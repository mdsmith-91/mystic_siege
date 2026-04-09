# Android APK Build — Implementation Spec

> **Purpose:** Self-contained spec for adding an Android APK build to the Mystic Siege
> release pipeline. Hand this file to an AI agent (Claude or Codex) to implement.
> The agent should read each referenced file in full before editing it.

---

## Context

- **Project:** Mystic Siege — Python 3.12 / pygame-ce top-down survivor game
- **Current release pipeline:** `.github/workflows/release.yml` builds Linux and Windows
  standalone executables via PyInstaller, triggered after CI passes on `main`
- **Runtime deps:** `pygame-ce>=2.5.0`, `pytmx>=3.32`, `numpy>=1.26`
- **Build tool to add:** [Buildozer](https://buildozer.readthedocs.io/) + python-for-android (p4a)
- **Goal:** Add an Android APK artifact to each GitHub Release. Touch controls are
  **out of scope** — this targets "builds and launches" as the initial milestone.

---

## Critical First Step — Verify pygame-ce p4a Compatibility

Before touching any project files, the agent **must** check whether python-for-android
has a working recipe for pygame-ce:

```bash
# Check the p4a recipe index
pip show python-for-android
python -m pythonforandroid.recipes list | grep -i pygame
```

- If a `pygame-ce` recipe exists: use `requirements = pygame-ce,pytmx,numpy` in `buildozer.spec`
- If only a `pygame2` recipe exists: use `requirements = pygame2,pytmx,numpy` and document
  whether the pygame-ce wheel installs on top, or whether a custom recipe is needed
- Record the finding in a comment at the top of `buildozer.spec`

---

## Files to Create

### 1. `buildozer.spec` (project root)

Create this file. Read `version.txt` (currently `0.4`) to set the version field.

```ini
[app]
title = Mystic Siege
package.name = mysticsige
package.domain = org.mysticsige

# Keep in sync with version.txt — update manually on version bumps
version = 0.4

source.dir = .
source.include_exts = py,png,jpg,wav,ogg,ttf,json,tmx,tsx

# Exclude CI/dev files from the APK
source.exclude_dirs = .github,docs,dist,build,.buildozer,saves,__pycache__,.git
source.exclude_patterns = *.pyc,*.pyo,*.spec,requirements-dev.txt,run_check.py

# IMPORTANT: If pygame-ce p4a recipe exists use pygame-ce; otherwise use pygame2.
# See Critical First Step section above.
requirements = python3,pygame-ce,pytmx,numpy

orientation = landscape
fullscreen = 1

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True

# Icon — drop a 512x512 PNG at assets/sprites/ui/icon.png and uncomment:
# icon.filename = assets/sprites/ui/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
```

---

## Files to Modify

### 2. `src/utils/resource_loader.py`

**Read the file in full first.**

The `_get_base_path()` function currently handles two cases: PyInstaller bundle
(`sys._MEIPASS`) and development (walk up from `src/utils/`). Add a third case for
Android, where p4a sets the `ANDROID_ARGUMENT` env var and the app's writable data
directory is accessible via the `android` module.

Replace the existing `_get_base_path` function (lines 7–15) with:

```python
def _get_base_path() -> str:
    """Return the root directory for asset loading.

    Priority order:
    1. PyInstaller bundle — files are unpacked to sys._MEIPASS
    2. Android (python-for-android) — assets live alongside the APK entry point
    3. Development — resolve 2 levels up from src/utils/ to reach the project root
    """
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if os.environ.get('ANDROID_ARGUMENT'):
        # p4a sets ANDROID_ARGUMENT; assets are bundled relative to the entry point
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

No other changes to `resource_loader.py`.

---

### 3. `main.py`

**Read the file in full first.**

The current display setup (line 20–24) passes `vsync=1` and `display=_get_cursor_display_index()`.
Both can cause crashes on Android — vsync behavior is handled by the Android surface
and multi-display APIs don't exist there.

Add an Android guard around those arguments:

```python
    _is_android = os.environ.get('ANDROID_ARGUMENT') is not None
    if _is_android:
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED
        )
    else:
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED, vsync=1,
            display=_get_cursor_display_index(),
        )
```

Add `import os` at the top of `main.py` if it is not already imported.

Also guard the audio pre-init: Android treats `linux` as False (platform is `android`),
so the existing `sys.platform == "linux"` check is already safe — no change needed there.

---

### 4. `.github/workflows/release.yml`

**Read the file in full first.**

Add a `build-android` job to the existing workflow. It runs in parallel with the
existing `build` matrix job and is added as a dependency of the `release` job.

#### 4a. Add the job (insert after the closing `---` of the `build` job, before `release:`):

```yaml
  build-android:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_sha }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Buildozer and dependencies
        run: |
          pip install buildozer cython
          sudo apt-get update -qq
          sudo apt-get install -y --no-install-recommends \
            git zip unzip openjdk-17-jdk build-essential \
            libssl-dev libffi-dev libsqlite3-dev

      - name: Cache Buildozer global state
        uses: actions/cache@v4
        with:
          path: ~/.buildozer
          key: buildozer-global-${{ runner.os }}-${{ hashFiles('buildozer.spec') }}
          restore-keys: buildozer-global-${{ runner.os }}-

      - name: Cache project .buildozer directory
        uses: actions/cache@v4
        with:
          path: .buildozer
          key: buildozer-project-${{ runner.os }}-${{ hashFiles('buildozer.spec', 'requirements.txt') }}
          restore-keys: buildozer-project-${{ runner.os }}-

      - name: Generate placeholder assets
        env:
          SDL_VIDEODRIVER: dummy
          SDL_AUDIODRIVER: dummy
        run: |
          pip install -r requirements.txt
          python src/utils/placeholder_assets.py

      - name: Build APK
        env:
          ANDROID_SDK_ROOT: /usr/local/lib/android/sdk
        run: buildozer android debug

      - name: Locate APK
        run: |
          APK=$(find bin -name "*.apk" | head -1)
          echo "APK_PATH=$APK" >> $GITHUB_ENV

      - uses: actions/upload-artifact@v4
        with:
          name: MysticSiege-android.apk
          path: ${{ env.APK_PATH }}
          retention-days: 1
```

#### 4b. Update `release` job dependencies and release body:

Change:
```yaml
  release:
    needs: [build]
```
To:
```yaml
  release:
    needs: [build, build-android]
```

Append the APK to the `files:` block in the `softprops/action-gh-release@v2` step:
```yaml
          files: |
            artifacts/MysticSiege-linux/MysticSiege-linux
            artifacts/MysticSiege-windows.exe/MysticSiege-windows.exe
            artifacts/MysticSiege-android.apk/MysticSiege-android.apk
```

Update the `body:` to add Android instructions:
```yaml
          body: |
            **To play on Linux:** `chmod +x MysticSiege-linux && ./MysticSiege-linux`
            **To play on Windows:** double-click `MysticSiege-windows.exe`
            **To play on Android:** sideload `MysticSiege-android.apk` (enable "Install unknown apps" in Settings). Note: touch controls are not yet implemented — a gamepad is required.
```

---

## Verification Steps

Run these in order. Do not claim a step works without actually running it.

1. **Import check (always first):**
   ```bash
   python run_check.py
   ```
   Must pass with no errors after any change that touches imports.

2. **Local desktop still works:**
   ```bash
   python main.py
   ```
   Game must launch and reach the main menu. Verify the Android guard does not break
   the desktop path (`ANDROID_ARGUMENT` env var must not be set in your shell).

3. **Local APK build (if Buildozer is installed locally):**
   ```bash
   buildozer android debug
   ```
   Expect a long first build (20–60 min). A `.apk` appears in `bin/`.

4. **APK launch on emulator:**
   - Install via `adb install bin/*.apk`
   - Launch on Android API 30+ emulator (x86_64)
   - Confirm: game reaches main menu, no crash on first frame
   - Confirm: `assets/` loads (sprites visible, not magenta placeholders if real assets are present)
   - Confirm: audio initializes or fails silently (no crash)

5. **CI verification:**
   - Push to a branch, open a PR, verify the `build-android` job runs and produces an artifact
   - Merge to `main` only after the job succeeds

---

## Known Risks and Edge Cases

| Risk | Mitigation |
|---|---|
| pygame-ce has no p4a recipe | Try `pygame2` recipe; file an issue with the pygame-ce maintainers; or write a custom recipe pointing at the pygame-ce wheel |
| `pytmx` not in p4a recipe index | It's pure Python — add it to `requirements` in `buildozer.spec` and p4a will pip-install it |
| First CI build times out (60 min limit) | Increase GitHub Actions timeout on the job; cache `~/.buildozer` aggressively |
| `_get_cursor_display_index()` imported at module level | The guard in `main.py` wraps the call, not the import — verify the import itself doesn't crash on Android |
| `detect_refresh_rate()` fails on Android | `detect_refresh_rate` is in `src/utils/fps_cap.py` — check whether its pygame display calls are safe on Android; wrap in a try/except returning 60 if needed |
| Screen resolution mismatch | `SCREEN_WIDTH`/`SCREEN_HEIGHT` in `settings.py` are fixed values; Android will letterbox/pillarbox via `pygame.SCALED` — acceptable for now |

---

## Out of Scope (Future Work)

- Touch / on-screen controls (separate task — requires significant input system changes)
- Dynamic resolution detection for Android
- Google Play Store signing and submission (`buildozer android release`)
- `minibat` or enemy split behavior on low-end Android devices
