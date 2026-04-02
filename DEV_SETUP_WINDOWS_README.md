# DEV_SETUP_WINDOWS_README

Windows development setup guide for **Mystic Siege** using **Python**, **PyGame**, **Git**, **GitHub**, **PowerShell**, **VS Code**, and a **repo-local virtual environment**.

This guide is intended to keep the development environment as contained and reproducible as possible.

---

## Goal

Set up a clean Windows development environment with:

- Python **3.12**
- a repo-local virtual environment at **`.venv`**
- VS Code using the correct project interpreter
- Git installed for cloning, pulling, and pushing
- GitHub access verified before starting work
- project dependencies installed only inside the virtual environment
- a repeatable setup that another developer can follow easily

---

## Why this setup

This project should use:

- **one Python version per project**
- **one virtual environment per repo**
- **VS Code pointed at that local environment**
- **Git for source control**
- **GitHub sign-in verified up front**
- **no global package installs for project dependencies**

This helps avoid:

- installing packages into the wrong Python
- version mismatch problems between developers
- VS Code using the wrong interpreter
- Git authentication issues later when trying to push
- “works on my machine” issues

---

## Before you start

You will need:

- a Windows machine
- internet access
- PowerShell
- Git
- VS Code
- access to the GitHub repo: `https://github.com/mdsmith-91/mystic_siege`

---

## Setup checklist

### 1) Confirm PowerShell is available

Press **Start**, type **PowerShell**, and open **Windows PowerShell** or **PowerShell**.

Then run:

```powershell
$PSVersionTable.PSVersion
```

#### What this does
Confirms PowerShell is installed and working.

#### Why this matters
This guide uses PowerShell commands for installing tools, creating the virtual environment, and running the project.

---

### 2) Confirm WinGet is available

In PowerShell, run:

```powershell
winget --version
```

#### What this does
Checks whether the Windows package manager is available.

#### Why this matters
We use WinGet to install Git, VS Code, and Python Manager in a clean, repeatable way.

#### If this fails
Install or update **App Installer** from the Microsoft Store, then reopen PowerShell and try again.

---

### 3) Install Git

Run:

    ```powershell
    winget install --id Git.Git -e --source winget
    ```

Then verify:

    ```powershell
    git --version
    ```

#### Configure Git identity

Run:

    ```powershell
    git config --global user.name "Your Name"

    ```

Then:

    ```powershell
    git config --global user.email "your-email@example.com"
    ```

Then verify:

    ```powershell
    git config --global user.name
    ```

And:

    ```powershell
    git config --global user.email
    ```

#### What this does

Sets the name and email that Git will attach to your future commits.

#### Why this matters

If this is not set correctly, commits may not be attributed properly on GitHub.

#### Privacy note

If you do not want to expose your personal email in public commits, use your GitHub `noreply` email instead of your real email.

---

### 4) Install VS Code

Run:

```powershell
winget install --id Microsoft.VisualStudioCode -e --source winget
```

Then verify:

```powershell
code --version
```

#### What this does
Installs Visual Studio Code and checks that the `code` command is available.

#### Why this matters
VS Code will be the main editor/debugger for the project.

#### If `code --version` fails
Open VS Code once from the Start menu, then try again. If needed, reinstall or add VS Code to PATH during installation.

---

### 5) Verify GitHub account access

Do both of the following:

#### In the browser
- Sign in to GitHub.
- Open: `https://github.com/mdsmith-91/mystic_siege`
- Confirm the repo loads.

#### In VS Code
- Open VS Code.
- Click the **Accounts** icon in the lower-left or upper-right area, depending on layout.
- Sign in to **GitHub** if you are not already signed in.

#### Why this matters
It is better to confirm GitHub access before cloning or trying to push changes. This avoids discovering authentication problems later.

---

### 6) Install Python Manager

Run:

```powershell
winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity
```

#### What this does
Installs Python’s official install manager.

#### Why this matters
This gives you the `py` command and makes it easier to install and manage the exact Python version the project expects.

---

### 7) Install Python 3.12

Run:

```powershell
py install 3.12
```

Then verify:

```powershell
py -V
```

#### Expected result
You should see a Python launcher/runtime available. The project target is **Python 3.12**.

#### Why this matters
`venv` does **not** install Python by itself. It creates an isolated environment from an already-installed Python interpreter.

---

### 8) Clone the repository

Run:

```powershell
mkdir C:\dev
```

Then:

```powershell
cd C:\dev
```

Run:

```powershell
git clone https://github.com/mdsmith-91/mystic_siege.git
```

Then:

```powershell
cd mystic_siege
```

#### What this does
Downloads the project and moves into the project folder.

#### Why this matters
All project commands should be run from the repo root so paths and scripts work correctly.

---

### 9) Create the project virtual environment

Run:

```powershell
py -3.12 -m venv .venv
```

#### What this does
Creates a virtual environment inside the repo folder.

#### Why this matters
This isolates all installed packages to this project only.

#### Important
Do **not** commit `.venv` to Git.

---

### 10) Activate the virtual environment

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

#### What this does
Activates the local environment for the current PowerShell session.

#### Why this matters
After activation, Python and pip commands will install and run against this project’s environment instead of the global system Python.

---

### 11) Upgrade pip inside the virtual environment

Run:

```powershell
python -m pip install --upgrade pip
```

#### What this does
Updates pip inside the active `.venv`.

#### Why this matters
Using `python -m pip` ensures pip is tied to the currently active interpreter, which avoids installing into the wrong Python.

---

### 12) Install project dependencies

Run:

```powershell
python -m pip install -r requirements.txt
```

```powershell
python -m pip install -r requirements-dev.txt
```

#### What this does
Installs runtime and development dependencies for the project.

#### Why this matters
This ensures the local environment matches the dependencies expected by the repo.

---

### 13) Run the project environment check

Run:

```powershell
python run_check.py
```

#### What this does
Runs the project’s built-in setup validation.

#### Why this matters
This is the fastest way to confirm Python, imports, and key dependencies are working before trying to run the game.

---

### 14) Generate placeholder assets

Run:

```powershell
python src/utils/placeholder_assets.py
```

#### What this does
Creates the placeholder assets needed for first-time setup.

#### Why this matters
The project expects these assets to exist before running normally.

---

### 15) Run the game

Run:

```powershell
python main.py
```

#### What this does
Starts Mystic Siege.

#### Why this matters
This confirms the environment is fully working end-to-end.

---

### 16) Open the project in VS Code

In VS Code:

- Open the `mystic_siege` folder
- Install the **Python** extension
- Click Quick Access (search bar) at the top, click **Show and Run Commands**
- Run **Python: Select Interpreter**
- Choose: Python 3.12.** (.venv) .venv\Scripts\python.exe


#### Why this matters
VS Code needs to use the project’s local interpreter for:

- running Python files
- debugging
- linting/intellisense
- terminal commands started from VS Code

If VS Code uses the wrong interpreter, the project may appear broken even when the terminal setup is correct.

---

### 17) Optional: install recommended VS Code extensions

Recommended extensions:

- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **GitHub Pull Requests and Issues** (GitHub)
- **Ruff** (Astral Software)
- **Git Lens** (GitKraken)
- **Error Lens** (Alexander)
- **Code Spell Checker** (Street Side Software)

#### Why this helps
These improve Python editing, type analysis, debugging, and GitHub workflow inside VS Code.

---

## Recommended daily workflow

Each time you start working on the project:

### 1) Open PowerShell in the repo folder

```powershell
cd C:\dev\mystic_siege
```

### 2) Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3) Pull the latest changes

```powershell
git pull
```

### 4) Run the game or project commands

```powershell
python main.py
```

---

## Optional VS Code debug setup

Create a file at:

```text
.vscode/launch.json
```

With this content:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Mystic Siege",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    }
  ]
}
```

### Why this helps
This gives a consistent one-click debug configuration for the project entry point.

---

## Verification checklist

Use this to confirm setup is complete:

- [ ] PowerShell opens and `$PSVersionTable.PSVersion` works
- [ ] `winget --version` works
- [ ] `git --version` works
- [ ] `code --version` works
- [ ] GitHub account is signed in and the repo is accessible in the browser
- [ ] `py install 3.12` completed successfully
- [ ] `.venv` exists in the repo folder
- [ ] virtual environment activates successfully
- [ ] dependencies installed without errors
- [ ] `python run_check.py` works
- [ ] `python src/utils/placeholder_assets.py` works
- [ ] `python main.py` launches the game
- [ ] VS Code is using `.venv\Scripts\python.exe`

---

## Troubleshooting

### PowerShell says scripts are disabled
Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then retry:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### `winget` is not recognized
Install or update **App Installer** from the Microsoft Store, then reopen PowerShell.

---

### `git` is not recognized
Reinstall Git with:

```powershell
winget install --id Git.Git -e --source winget
```

Then reopen PowerShell and run:

```powershell
git --version
```

---

### `code` is not recognized
Open VS Code once from the Start menu. If it still fails, reinstall VS Code or add it to PATH during installation.

---

### `py` is not recognized
Python Manager may not be installed correctly yet. Re-run:

```powershell
winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity
```

Then install Python again:

```powershell
py install 3.12
```

---

### VS Code is using the wrong Python
In VS Code:

- open the Command Palette
- run **Python: Select Interpreter**
- choose the interpreter inside `.venv`

---

### The game fails because packages are missing
Make sure the virtual environment is activated, then reinstall dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

---

### The environment got messy
Delete `.venv` and recreate it:

```powershell
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

---

## Team notes

For this project, each developer should:

- use the same Python major/minor version
- keep dependencies inside `.venv`
- avoid installing project dependencies globally
- run project commands from the repo root
- confirm VS Code is using the local interpreter
- verify GitHub sign-in before pushing changes

This keeps setup consistent across machines and reduces debugging time.

---

## Future Linux testing note

WSL 2 is **not required** for the Windows development setup above.

However, if Linux build/testing is needed later:

- keep Windows as the main development environment
- use WSL 2 as a separate Linux test/build environment
- keep a separate repo clone and separate `.venv` inside WSL
- do **not** share one `.venv` across Windows and Linux

---

## Setup complete

After finishing this guide, the normal startup flow should be:

```powershell
cd C:\dev\mystic_siege
.\.venv\Scripts\Activate.ps1
git pull
python main.py
```