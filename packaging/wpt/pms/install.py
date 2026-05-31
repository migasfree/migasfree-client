import os
import sys

# Windows HKLM App Paths key location
APP_PATHS_BASE = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths'
EXE_NAME = 'migasfree.exe'


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


def main():
    install_dir = os.environ.get('WPT_INSTALL_DIR')
    if not install_dir:
        print('Error: WPT_INSTALL_DIR is not set.', file=sys.stderr)
        sys.exit(1)

    exe_path = os.path.join(install_dir, EXE_NAME)
    if not os.path.isfile(exe_path):
        print(f"Error: '{EXE_NAME}' not found at {exe_path}", file=sys.stderr)
        sys.exit(1)

    success = register_in_app_paths(exe_path, install_dir)
    if not success:
        sys.exit(1)

    print('migasfree-client installation completed successfully.')
    sys.exit(0)


if __name__ == '__main__':
    main()
