#!/usr/bin/env python3
"""Import checker and pygame version verifier for Mystic Siege."""

import sys
import pygame
import importlib
import os

def check_module_import(module_path):
    """Try to import a module and return success or failure."""
    try:
        # Convert path to module name (e.g., src/ui/main_menu.py -> src.ui.main_menu)
        module_name = module_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        if module_name.startswith('.'):
            module_name = module_name[1:]

        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """Run all checks."""
    print("Running import checks...")

    # Get all Python files in the project
    project_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                project_files.append(os.path.join(root, file))

    # Add main project files
    main_files = ['main.py', 'settings.py']
    for file in main_files:
        if os.path.exists(file):
            project_files.append(file)

    # Check each module
    failures = []

    for file_path in project_files:
        # Skip the run_check.py file itself
        if file_path == 'run_check.py':
            continue

        success, error = check_module_import(file_path)
        if success:
            print(f"OK: {file_path}")
        else:
            print(f"FAIL: {file_path} — {error}")
            failures.append(f"{file_path} — {error}")

    # Print pygame and Python version info
    print("\nChecking system information...")
    print(f"Pygame version: {pygame.version.ver}")
    print(f"Python version: {sys.version}")

    # Check Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor == 12:
        print("✓ Python version is 3.12.x")
    else:
        print(f"⚠ Warning: Python version is {python_version.major}.{python_version.minor}.{python_version.micro}, not 3.12.x")

    # Final result
    if not failures:
        print("\nAll checks passed!")
    else:
        print(f"\n{len(failures)} import failures detected:")
        for failure in failures:
            print(f"  {failure}")
        sys.exit(1)

if __name__ == "__main__":
    main()