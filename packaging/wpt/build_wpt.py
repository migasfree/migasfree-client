import os
import shutil
import subprocess
import sys


def build_pms_package():
    # 1. Paths Setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

    wpt_source_dir = os.path.join(script_dir, 'migasfree-client-source')
    data_dir = os.path.join(wpt_source_dir, 'data')

    print(f'[*] Project root identified: {project_root}')

    # 2. Compile standalone binaries via cx_Freeze
    print('[*] Compiling migasfree-client via cx_Freeze...')
    try:
        subprocess.run([sys.executable, 'setup_msi.py', 'build_exe'], cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print(f'[!] cx_Freeze compilation failed: {e}', file=sys.stderr)
        sys.exit(1)

    # Locate compilation output
    build_dir = os.path.join(project_root, 'build')
    compiled_folder = None
    for entry in os.listdir(build_dir):
        if entry.startswith('exe.win'):
            compiled_folder = os.path.join(build_dir, entry)
            break

    if not compiled_folder:
        print('[!] Failed to locate cx_Freeze compilation directory.', file=sys.stderr)
        sys.exit(1)

    print(f'[*] Found compiled binary directory: {compiled_folder}')

    # 3. Structure the WPT package folder
    if os.path.exists(wpt_source_dir):
        shutil.rmtree(wpt_source_dir)

    os.makedirs(wpt_source_dir)

    # Copy pms files (metadata, install, remove)
    shutil.copytree(os.path.join(script_dir, 'pms'), os.path.join(wpt_source_dir, 'pms'))

    # Copy cx_Freeze output to data/
    shutil.copytree(compiled_folder, data_dir)
    print('[*] Structured WPT package directory.')

    # 4. Invoke WPT Build
    print('[*] Invoking WPT to build the final package...')
    try:
        # Assumes 'wpt' CLI is installed and available in the environment
        subprocess.run(['wpt', 'build', wpt_source_dir], check=True)
        print('[+] WPT package built successfully.')
    except Exception as e:
        print(f'[!] Error building WPT package: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    build_pms_package()
