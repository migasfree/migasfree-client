# migasfree-client Packaging Guide

Project-specific packaging information for migasfree-client.

## Supported Platforms

| Platform | Package Format | Config Files |
|----------|---------------|--------------|
| Debian/Ubuntu | `.deb` | `stdeb.cfg`, `stdeb.cfg.d/` |
| Fedora/RHEL | `.rpm` | `setup.cfg.d/fedora.cfg` |
| Windows | `.exe` | PyInstaller |

## Packaging Files Structure

```
migasfree-client/
├── pyproject.toml      # Main project config
├── setup.py            # Legacy setup (still used by stdeb)
├── setup.cfg.d/        # Per-distro setup configs
│   ├── debian.cfg
│   ├── fedora.cfg
│   └── ...
├── stdeb.cfg           # Base Debian packaging config
├── stdeb.cfg.d/        # Per-distro stdeb configs
│   ├── bullseye.cfg
│   └── jammy.cfg
└── MANIFEST.in         # Source distribution inclusion
```

## Debian Packaging

### Build for Current Distribution

```bash
pip install stdeb
python setup.py --command-packages=stdeb.command sdist_dsc
cd deb_dist/migasfree-client-*/
dpkg-buildpackage -rfakeroot -uc -us
```

### Build for Specific Distribution

```bash
# Copy distro-specific config
cp stdeb.cfg.d/jammy.cfg stdeb.cfg

# Build
python setup.py --command-packages=stdeb.command sdist_dsc
```

## Dependencies

### Runtime Dependencies

- `python3-netifaces`
- `python3-requests`
- `python3-cryptography`
- `python3-rich`

### Platform-Specific Requirements

- **Linux**: lshw, dmidecode (for hardware inventory)
- **Windows**: WPT (Windows Package Tool) for package management

## Configuration Paths

| Platform | Config Path | Key Storage |
|----------|-------------|-------------|
| Linux | `/etc/migasfree.conf` | `/var/migasfree-client/mtls/` |
| Windows | `%PROGRAMDATA%\migasfree-client\migasfree.conf` | `%PROGRAMDATA%\migasfree-client\` |
