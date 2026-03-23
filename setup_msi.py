from cx_Freeze import Executable, setup

# Import version from the package
from migasfree_client import __version__

# Dependencies are automatically detected, but they might need fine tuning.
build_exe_options = {
    'packages': ['os', 'migasfree_client', 'psutil', 'requests', 'jwcrypto', 'cryptography', 'rich', 'win32com'],
    'excludes': ['tkinter', 'unittest', 'pydoc'],
    'include_files': [
        ('conf/migasfree.conf', 'conf/migasfree.conf'),
    ],
}

# bdist_msi options for the Windows Installer
bdist_msi_options = {
    'add_to_path': True,
    'initial_target_dir': r'[ProgramFilesFolder]\migasfree_client',
    # cx_Freeze automatically generates an UpgradeCode based on the project name.
}

# base="Console" is used for CLI applications
base = 'Console'

setup(
    name='migasfree-client',
    version=__version__,
    description='Migasfree Client for Windows',
    options={
        'build_exe': build_exe_options,
        'bdist_msi': bdist_msi_options,
    },
    executables=[
        Executable(
            'migasfree_client/__main__.py',
            target_name='migasfree.exe',
            base=base,
        )
    ],
)
