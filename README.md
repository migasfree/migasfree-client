# Description

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![GitHub issues](https://img.shields.io/github/issues/migasfree/migasfree-client)](https://github.com/migasfree/migasfree-client/issues)

'migasfree' is a very simple, but effective, systems management system. Actually, it is used in `Ayuntamiento de Zaragoza` (Spain) by initial authors in the project **migration to open source software for desktops**. They use [AZLinux distribution](http://zaragozaciudad.net/azlinux), which is based on [Debian](https://www.debian.org/).

You can learn about systems management systems at:

- [Systems management](http://en.wikipedia.org/wiki/Systems_management)
- [List of systems management systems](http://en.wikipedia.org/wiki/List_of_systems_management_systems)

# License

migasfree is free software, released under GNU GPL v3 (see LICENSE file for details).

# Authors

See AUTHORS file.

# Requirements

- a Linux distribution (Fedora, openSUSE, Ubuntu, ...) or Windows >= 10
- Python >= 3.6 (see requirements.txt file)
- lshw >= B.02.15 (or [LsHw Windows Emulator](https://github.com/migasfree/lshw-windows-emulator) in Windows platform)
- dmidecode
- Extra requirements in Windows platform:
  - python-magic-bin
  - pysam-win
  - pywin32
  - psutil

# Features (migasfree suite)

- Web administration
- Multiuser
- Multiversion (you can have desktops with differents versions and/or distributions of GNU/Linux)
- Automated Data Capture (you do not worry about adding hostnames, users, IPs, devices, etc. to server)
- Centralized system errors
- Centralized system faults
- Hardware inventory
- Software inventory
- System queries from the admin site

# Commands

The `migasfree` command provides several subcommands:

| Command                          | Description                                     |
| -------------------------------- | ----------------------------------------------- |
| `migasfree register -u USER`     | Register computer at server with specified user |
| `migasfree sync`                 | Synchronize computer with server                |
| `migasfree sync -f`              | Synchronize and force package upgrades          |
| `migasfree sync -dev`            | Synchronize computer devices                    |
| `migasfree sync -hard`           | Synchronize hardware information                |
| `migasfree sync -soft`           | Upload software inventory                       |
| `migasfree sync -att`            | Upload attributes information                   |
| `migasfree sync -fau`            | Upload faults information                       |
| `migasfree search PATTERN`       | Search package in repositories                  |
| `migasfree install PACKAGE`      | Install package                                 |
| `migasfree purge PACKAGE`        | Purge (completely remove) package               |
| `migasfree traits [PREFIX]`      | Get computer traits at server                   |
| `migasfree label`                | Show computer identification label              |
| `migasfree version`              | Show version info                               |
| `migasfree tags -g`              | Get tags from server (JSON format)              |
| `migasfree tags -s TAG [TAG...]` | Set tags in server                              |
| `migasfree tags -c TAG [TAG...]` | Communicate tags to server                      |
| `migasfree upload -f FILE`       | Upload file to server                           |
| `migasfree upload -r DIR`        | Upload directory to server                      |
| `migasfree info [KEY]`           | Retrieve computer info at server                |
| `migasfree remove-keys`          | Remove client keys                              |
| `migasfree remove-keys -a`       | Remove client keys from all servers             |
| `migasfree import-mtls FILE`     | Import mTLS certificate from tar file           |

**Global options:**

- `-d, --debug`: Enable debug mode
- `-q, --quiet`: Enable silent mode (no verbose output)

# Configuration

The configuration file is located at:

- **Linux**: `/etc/migasfree.conf`
- **Windows**: `%PROGRAMDATA%\migasfree-client\migasfree.conf`

You can override the configuration file path using the `MIGASFREE_CONF` environment variable.

**[client] section:**

| Option                 | Default         | Description                                      |
| ---------------------- | --------------- | ------------------------------------------------ |
| `Server`               | localhost       | migasfree server hostname or IP                  |
| `Protocol`             | http            | Protocol to use: `http` or `https`               |
| `Port`                 | (empty)         | Server port (uses default for protocol if empty) |
| `Project`              | (auto-detected) | Project name (e.g., Ubuntu-20.04)                |
| `Auto_Update_Packages` | True            | Auto update packages during sync                 |
| `Manage_Devices`       | True            | Manage devices (printers, etc.)                  |
| `Upload_Hardware`      | True            | Upload hardware information to server            |
| `Computer_Name`        | (hostname)      | Override computer name                           |
| `Debug`                | False           | Enable debug logging                             |
| `Proxy`                | (empty)         | System proxy (e.g., 192.168.1.100:8080)          |
| `Package_Proxy_Cache`  | (empty)         | Package proxy cache (e.g., apt-cacher)           |

**[packager] section:**

| Option     | Description                     |
| ---------- | ------------------------------- |
| `User`     | Username for uploading packages |
| `Password` | Password for uploading packages |
| `Project`  | Default project for uploads     |
| `Store`    | Default store for uploads       |

# mTLS Authentication

migasfree-client supports mutual TLS (mTLS) authentication for secure client-server communication.

**Importing certificates manually:**

```bash
migasfree import-mtls /path/to/certificate.tar
```

**Certificate paths:**

| Platform | Path                                   |
| -------- | -------------------------------------- |
| Linux    | `/var/migasfree-client/mtls/`          |
| Windows  | `%PROGRAMDATA%\migasfree-client\mtls\` |

The mTLS certificates are automatically fetched during computer registration if the server supports mTLS.

# Behaviour

How can you change the software configuration of machines with migasfree?

When an user opens a graphic session in the machine, migasfree client queries the migasfree Server and it responds with a code survey to execute in the client, created _ad hoc_ for this client after consulting the database.

This code survey is executed in the client and basically configures the repositories of packages (rpm or deb). Previously, these repositories have been created for the server when the migasfree's administrator configures a repository.

A repository in migasfree server defines the packages that should be installed, updated or removed in the clients in function of attributes of client computer: **HOSTNAME**, **USER**, **LDAP CONTEXT**, **VIDEO CARD**, ... (the administrator defines the properties that he wants to use in his organization).

All changes of configuration in the clients are made through packages. Therefore it is necessary that you know how create packages in order to change the configuration of the machines that you want administrate. You can consider hiring a professional, this is the hard work, you were warned!

# Use

For example: You want change the Firefox homepage in all PCs in a range of IPs.

1. You must create a package (for example `myorg-firefox-1-0.rpm` or `myorg-firefox_1-0.deb`). You must investigate which files need to be modified and allow the package to perform the task of changing the configuration. This is hard work!

2. You must upload your package to the server. This is simple!

3. You must create a repository in migasfree server. Add your package `myorg-firefox` and define the range of IPs. This is easy!

4. _Voilà!_ When a user opens a graphic session and his IP is in range, migasfree client install the package.

# Documentation

[Fun with migasfree](http://fun-with-migasfree.readthedocs.org/) (spanish)

_That's all folks!!!_
