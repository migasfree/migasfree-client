import os
import shutil
import sys

# Windows HKLM App Paths key location
APP_PATHS_BASE = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths'
EXE_NAME = 'migasfree.exe'
SHIM_NAME = 'migasfree.cmd'


def register_in_app_paths(exe_path: str, install_dir: str) -> bool:
    """Registers the executable in Windows App Paths for global shell execution.

    Args:
        exe_path: The absolute path to the executable file.
        install_dir: The directory containing the executable.

    Returns:
        True if the registration succeeded, False otherwise.
    """
    if sys.platform != 'win32':
        return True

    import winreg

    app_paths_key = f'{APP_PATHS_BASE}\\{EXE_NAME}'
    try:
        # HKLM App Paths enables global execution without polluting %PATH%
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, app_paths_key) as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_SZ, install_dir)
        print(f"Successfully registered '{EXE_NAME}' in Windows App Paths.")
    except PermissionError:
        print(
            f"Permission denied: Unable to register '{EXE_NAME}' in App Paths. Run as Administrator.",
            file=sys.stderr,
        )
        return False
    except Exception as e:
        print(f'Error writing Registry App Paths: {e}', file=sys.stderr)
        return False

    return True


def get_wpt_bin_dir() -> str:
    """Finds the directory where wpt is installed."""
    # Try finding it in the PATH environment variable
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for d in path_dirs:
        if os.path.exists(os.path.join(d, 'wpt.exe')):
            return d

    # Fallback to standard Program Files location
    program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
    wpt_default = os.path.join(program_files, 'wpt')
    if os.path.isdir(wpt_default):
        return wpt_default

    return ''


def create_shim(exe_path: str) -> bool:
    """Creates a .cmd shim in the wpt bin directory if possible."""
    wpt_dir = get_wpt_bin_dir()
    if not wpt_dir:
        print('Warning: Could not locate wpt installation directory. Shim was not created.')
        return True

    shim_path = os.path.join(wpt_dir, SHIM_NAME)
    try:
        shim_content = f'@echo off\n"{exe_path}" %*\n'
        with open(shim_path, 'w', encoding='utf-8') as f:
            f.write(shim_content)
        print(f"Successfully created shim '{SHIM_NAME}' at {shim_path}.")
        return True
    except Exception as e:
        print(f'Warning: Failed to create shim at {shim_path}: {e}', file=sys.stderr)
        return False


def main():
    # 1. Paths resolution
    wpt_install_dir = os.environ.get('WPT_INSTALL_DIR')
    if not wpt_install_dir:
        print('Error: WPT_INSTALL_DIR is not set.', file=sys.stderr)
        sys.exit(1)

    program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
    target_install_dir = os.path.join(program_files, 'migasfree-client')
    target_exe_path = os.path.join(target_install_dir, EXE_NAME)

    print(f"[*] Relocating migasfree-client files to '{target_install_dir}'...")

    try:
        # Create target directory if it doesn't exist
        if os.path.exists(target_install_dir):
            shutil.rmtree(target_install_dir)

        # Copy from wpt_install_dir to target_install_dir
        shutil.copytree(wpt_install_dir, target_install_dir)

        # Clean up wpt_install_dir to keep it empty and avoid duplication
        for item in os.listdir(wpt_install_dir):
            item_path = os.path.join(wpt_install_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        print('[+] Files successfully relocated and managed cache cleared.')
    except Exception as e:
        print(f'Error relocating files: {e}', file=sys.stderr)
        sys.exit(1)

    # 2. Register in App Paths
    success = register_in_app_paths(target_exe_path, target_install_dir)
    if not success:
        sys.exit(1)

    # 3. Create CLI shim
    create_shim(target_exe_path)

    print('migasfree-client installation completed successfully.')
    sys.exit(0)


if __name__ == '__main__':
    main()
