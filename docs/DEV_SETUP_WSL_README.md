# DEV_SETUP_WSL_README

WSL 2 development and Linux build/test setup guide for **Mystic Siege**.

> Current project-state note (2026-04-05): `python run_check.py` validates the
> Linux environment and imports, but it does not verify gameplay correctness. The
> current multiplayer implementation is partial and still requires manual runtime testing.

Use this guide if you want to:

- test the project in a real Linux userspace from your Windows machine
- validate Linux-specific behavior earlier
- build Linux release artifacts separately from Windows
- keep your Windows and Linux environments cleanly separated

---

## Important recommendation

For this project:

- use **Windows** as the main day-to-day development environment
- use **WSL 2** as a **secondary Linux build/test environment**

Do **not** replace your Windows setup with WSL unless you specifically want a Linux-first workflow.

---

## Why use WSL 2 here

WSL 2 is useful because it lets you:

- run Linux tools locally on Windows
- keep a separate Linux Python environment
- test Linux-specific dependency behavior
- prepare Linux-side builds in a Linux environment

This is especially helpful for projects that may need separate Linux release testing.

---

## Important rule

Keep Windows and WSL environments separate.

That means:

- separate repo clone on Windows
- separate repo clone inside WSL
- separate `.venv` for Windows
- separate `.venv` for Linux

Do **not** share one `.venv` across both environments.

---

## Recommended folder layout

### Windows copy
Used for:

- normal development
- Windows testing
- Windows packaging

Example:

```text
C:\dev\mystic_siege
```

### WSL copy
Used for:

- Linux testing
- Linux-specific debugging
- Linux packaging/build validation

Example:

```text
~/dev/mystic_siege
```

---

## Best practice for WSL file location

Keep the Linux repo clone **inside the Linux filesystem**, not under `/mnt/c/...`.

### Good

```bash
~/dev/mystic_siege
```

### Avoid

```bash
/mnt/c/dev/mystic_siege
```

### Why this matters
Linux tools in WSL generally work best when the project files live in the Linux filesystem.

---

## Setup checklist

### 1) Install WSL 2

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

Then reboot if Windows asks you to.

### What this does
Installs WSL and a default Linux distribution, usually Ubuntu.

### Why this matters
This gives you a real Linux environment for running and testing the project.

---

### 2) Confirm WSL is installed

Run:

```powershell
wsl --status
```

Optional:

```powershell
wsl --list --verbose
```

### Why this matters
Confirms WSL is available and shows whether your distro is installed and running under WSL 2.

---

### 3) Open your Linux distribution

Launch **Ubuntu** from the Start menu, or run:

```powershell
wsl
```

### What this does
Drops you into the Linux shell.

---

### 4) Update the package list and installed packages

Inside WSL, run:

```bash
sudo apt update
```

Then run:

```bash
sudo apt upgrade -y
```

### Why this matters
Gets the Linux environment current before installing dependencies.

---

### 5) Install core development tools

Inside WSL, run:

```bash
sudo apt install -y git build-essential python3.12 python3.12-venv python3-pip
```

### What this does
Installs Git, compiler/build tools, Python, venv support, and pip.

### Why this matters
You need Python plus venv support to create an isolated Linux environment for the project.

### Note
Depending on the Ubuntu version, `python3.12` may already exist or may need a slightly different package flow. If it is unavailable from apt on your distro version, install the distro’s default Python 3 and confirm it is a compatible 3.12.x release.

---

### 6) Install common libraries often needed by PyGame apps

Inside WSL, run:

```bash
sudo apt install -y python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev
```

### Why this matters
PyGame-based projects may need Linux-side SDL and related development libraries for reliable installation and runtime behavior.

---

### 7) Create a Linux-side development folder

Inside WSL, run:

```bash
mkdir -p ~/dev
```
Then:

```bash
cd ~/dev
```

### Why this matters
Keeps the Linux copy of the project cleanly separated from the Windows copy.

---

### 8) Clone the repo inside WSL

Run:

```bash
git clone https://github.com/mdsmith-91/mystic_siege.git
```

Then:

```bash
cd mystic_siege
```

### Why this matters
This gives you a true Linux-side copy of the project for Linux testing and packaging.

---

### 9) Create a Linux virtual environment

Run:

```bash
python3.12 -m venv .venv
```

If `python3.12` is not the command name on your distro but the installed Python is still compatible, use that interpreter instead.

### Why this matters
This keeps Linux Python packages isolated to the WSL project copy.

---

### 10) Activate the Linux virtual environment

Run:

```bash
source .venv/bin/activate
```

### Why this matters
This ensures all package installs happen inside the Linux `.venv`.

---

### 11) Upgrade pip inside the WSL environment

Run:

```bash
python -m pip install --upgrade pip
```

### Why this matters
Keeps the package installer current and tied to the active interpreter.

---

### 12) Install project dependencies

Run:

```bash
python -m pip install -r requirements.txt
```

Then:

```bash
python -m pip install -r requirements-dev.txt
```

### Why this matters
Installs the project dependencies into the Linux virtual environment.

---

### 13) Run the project environment check

Run:

```bash
python run_check.py
```

### Why this matters
Confirms imports and the basic environment are working before full testing.

### Important limitation
Passing `run_check.py` does not prove the solo or multiplayer gameplay paths are working.

---

### 14) Generate placeholder assets

Run:

```bash
python src/utils/placeholder_assets.py
```

### Why this matters
Matches the same first-time setup flow used on Windows.

---

### 15) Try running the game in WSL

Run:

```bash
python main.py
```

### Why this matters
This is the simplest Linux-side validation step.

### Current verification recommendation
If graphics/display support is available, use the current flow `Main Menu -> Lobby -> Class Select -> Game` for a basic manual smoke test.

### Important note
Graphical behavior in WSL depends on your Windows version, WSLg support, and graphics/audio setup. If the game does not display correctly, that does not necessarily mean the Python environment is wrong.

---

## VS Code with WSL

### Recommended approach
Use the **Remote - WSL** extension in VS Code.

### Steps

- Open VS Code on Windows
- Install **Remote - WSL** if prompted
- Open the WSL repo folder through the WSL extension
- Open the Command Palette
- Run **Python: Select Interpreter**
- Choose the Linux interpreter at:

```text
/home/your-linux-user/dev/mystic_siege/.venv/bin/python
```

### Why this matters
This makes VS Code behave like it is attached directly to the Linux environment and Linux interpreter.

---

## Daily WSL workflow

Each time you want to test or build from Linux:

```bash
cd ~/dev/mystic_siege
source .venv/bin/activate
python main.py
```

---

## One-time setup summary

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git build-essential python3.12 python3.12-venv python3-pip
sudo apt install -y python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev

mkdir -p ~/dev
cd ~/dev
git clone https://github.com/mdsmith-91/mystic_siege.git
cd mystic_siege

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

python run_check.py
python src/utils/placeholder_assets.py
python main.py
```

---

## Linux packaging/build notes

Use WSL if you want a Linux-side environment for build validation.

Recommended approach:

- build Windows artifacts on Windows
- build Linux artifacts in WSL/Linux
- keep those environments separate

If you package later, keep in mind that Linux compatibility can depend on the distro and system libraries used during the build.

---

## Verification checklist

- [ ] `wsl --install` completed successfully
- [ ] Ubuntu or another distro opens successfully
- [ ] repo is cloned inside the Linux filesystem
- [ ] `.venv` exists in the WSL repo folder
- [ ] dependencies installed without errors
- [ ] `python run_check.py` works
- [ ] `python src/utils/placeholder_assets.py` works
- [ ] `python main.py` runs or at least gets far enough to validate the environment
- [ ] VS Code is using the Linux `.venv` interpreter when connected through WSL

---

## Troubleshooting

### `python3.12` is not found
Check what Python versions are available:

```bash
python3 --version
which python3
```

If your distro provides a compatible Python 3.12.x as `python3`, use that interpreter instead when creating the venv.

---

### The repo was cloned under `/mnt/c/...`
Move to a Linux-native folder instead:

```bash
mkdir -p ~/dev
cd ~/dev
git clone https://github.com/mdsmith-91/mystic_siege.git
```

---

### PyGame or display behavior seems broken in WSL
That may be a graphics/display integration issue rather than a Python setup issue.

Verify these first:

- the virtual environment is activated
- dependencies installed successfully
- `python run_check.py` passes

---

### VS Code is using the Windows interpreter instead of the Linux one
Make sure you opened the folder through **Remote - WSL** and then re-select the interpreter inside `.venv/bin/python`.

---

### The Linux environment got messy
Delete and recreate the Linux virtual environment:

```bash
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

---

## Team notes

For this project, each developer can safely use:

- Windows setup for primary development
- WSL setup for Linux testing/build validation

Just keep these separate:

- repo clones
- virtual environments
- package installs
- interpreter selection in VS Code

---

## Setup complete

After finishing this guide, the normal WSL startup flow should be:

```bash
cd ~/dev/mystic_siege
source .venv/bin/activate
python main.py
```
