import sys

# HKLM App Paths key location
APP_PATHS_KEY = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths'


def remove_from_registry(exe_name: str) -> bool:
    """Removes the specified executable from the Windows App Paths registry.

    Args:
        exe_name: The name of the executable (e.g., 'migasfree.exe').

    Returns:
        True if the key was deleted or did not exist, False otherwise.
    """
    if sys.platform != 'win32':
        return True

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, APP_PATHS_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                winreg.DeleteKey(key, exe_name)
                print(f"Successfully removed '{exe_name}' from Windows App Paths.")
            except FileNotFoundError:
                # Key already deleted or never existed
                print(f"'{exe_name}' was not found in App Paths (or already removed).")
            except PermissionError:
                print(
                    f"Permission denied: Unable to delete '{exe_name}' from App Paths. Run as Administrator.",
                    file=sys.stderr,
                )
                return False
    except Exception as e:
        print(f'Error opening Registry App Paths: {e}', file=sys.stderr)
        return False

    return True


def main():
    success = remove_from_registry('migasfree.exe')
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
