# Command-Line Interface Reference

Complete reference for all migasfree-client commands and options.

## Synopsis

```bash
migasfree <command> [options]
```

## Global Options

These options are available for most commands:

| Option            | Description                                  |
| ----------------- | -------------------------------------------- |
| `-d`, `--debug`   | Enable debug output                          |
| `-e`, `--pms`     | Select package management system             |
| `-g`, `--graphic` | Enable graphical mode (show notifications)   |

## Commands

### sync

Synchronizes the computer with the migasfree server. This is the primary command for client-server communication.

```bash
migasfree sync [options]
```

**Options:**

| Option            | Description                                                  |
| ----------------- | ------------------------------------------------------------ |
| `-f`, `--force`   | Force package updates even if Auto_Update_Packages is False  |
| `-d`, `--debug`   | Enable debug output                                          |
| `-g`, `--graphic` | Show graphical notifications                                 |

**Actions performed:**

1. Upload computer attributes to server
2. Evaluate and report faults
3. Configure package repositories
4. Install mandatory packages
5. Remove unwanted packages
6. Upgrade available packages (if enabled)
7. Upload software inventory
8. Upload hardware information
9. Configure devices

**Examples:**

```bash
# Basic synchronization
sudo migasfree sync

# Force package updates
sudo migasfree sync -f

# Debug mode with graphical notifications
sudo migasfree sync -d -g
```

---

### register

Registers the computer with the migasfree server. Must be run once before synchronization.

```bash
migasfree register [options]
```

**Options:**

| Option             | Description                              |
| ------------------ | ---------------------------------------- |
| `-u`, `--user`     | Username for authentication              |
| `-p`, `--password` | Password (will prompt if not provided)   |

**Examples:**

```bash
# Register with username prompt for password
sudo migasfree register -u admin

# Register with password (not recommended - visible in history)
sudo migasfree register -u admin -p secret
```

---

### search

Searches for packages in configured repositories.

```bash
migasfree search <pattern>
```

**Arguments:**

| Argument  | Description                    |
| --------- | ------------------------------ |
| `pattern` | Package name pattern to search |

**Examples:**

```bash
# Search for vim packages
migasfree search vim

# Search with wildcard
migasfree search "python3-*"
```

---

### install

Installs packages via the package management system.

```bash
migasfree install <package> [package...]
```

**Arguments:**

| Argument  | Description                         |
| --------- | ----------------------------------- |
| `package` | One or more package names to install|

**Examples:**

```bash
# Install a single package
sudo migasfree install htop

# Install multiple packages
sudo migasfree install vim git curl
```

---

### remove

Removes packages via the package management system.

```bash
migasfree remove <package> [package...]
```

**Arguments:**

| Argument  | Description                        |
| --------- | ---------------------------------- |
| `package` | One or more package names to remove|

**Examples:**

```bash
# Remove a package
sudo migasfree remove nano

# Remove multiple packages
sudo migasfree remove nano telnet ftp
```

---

### purge

Removes packages and their configuration files.

```bash
migasfree purge <package> [package...]
```

**Arguments:**

| Argument  | Description                        |
| --------- | ---------------------------------- |
| `package` | One or more package names to purge |

**Examples:**

```bash
# Purge a package
sudo migasfree purge apache2
```

---

### label

Displays the computer's identification label. Useful for asset management and troubleshooting.

```bash
migasfree label
```

**Output includes:**

- Computer UUID
- Computer name
- IP address
- Server name
- Project

**Example:**

```bash
migasfree label
```

---

### version

Displays version information for the client and its components.

```bash
migasfree version
```

**Example output:**

```text
migasfree client version: 5.0.0
Python: 3.10.6
Platform: Linux-5.15.0-generic-x86_64
PMS: apt
```

---

### upload

Uploads a package to the migasfree server (for packagers).

```bash
migasfree upload [options]
```

**Options:**

| Option           | Description                |
| ---------------- | -------------------------- |
| `-f`, `--file`   | Package file to upload     |
| `-s`, `--store`  | Target store on server     |
| `-S`, `--source` | Upload as source package   |

**Examples:**

```bash
# Upload a package to default store
migasfree upload -f mypackage_1.0_all.deb

# Upload to specific store
migasfree upload -f mypackage_1.0.rpm -s custom-store
```

---

### import-mtls

Imports mTLS client certificates from a tar archive.

```bash
migasfree import-mtls <file>
```

**Arguments:**

| Argument | Description                                        |
| -------- | -------------------------------------------------- |
| `file`   | Path to the certificate tar archive (.tar, .tar.gz)|

**Certificate formats supported:**

- PEM files (cert.pem, key.pem, ca.pem)
- PKCS#12 files (.p12, .pfx)

**Example:**

```bash
sudo migasfree import-mtls /path/to/certificates.tar
```

---

### remove-keys

Removes all signing keys and certificates for a server.

```bash
migasfree remove-keys [options]
```

**Options:**

| Option  | Description                  |
| ------- | ---------------------------- |
| `--all` | Remove keys for all servers  |

**Examples:**

```bash
# Remove keys for configured server
sudo migasfree remove-keys

# Remove all keys
sudo migasfree remove-keys --all
```

---

## Exit Codes

| Code | Meaning                  |
| ---- | ------------------------ |
| 0    | Success                  |
| 1    | General error            |
| 2    | Command-line usage error |
| 3    | Connection error         |
| 4    | Authentication error     |
| 5    | Server error             |
| 6    | Package manager error    |

## Environment Variables

Command behavior can be modified using environment variables. See [Environment Variables Reference](environment-variables.md) for details.

## Configuration

Commands read settings from the configuration file. See [Configuration Reference](configuration.md) for all options.

## Files

| Path (Linux)                    | Description             |
| ------------------------------- | ----------------------- |
| `/etc/migasfree.conf`           | Main configuration file |
| `/var/migasfree-client/keys/`   | Signing keys            |
| `/var/migasfree-client/mtls/`   | mTLS certificates       |
| `/var/log/migasfree.log`        | Log file                |
| `/var/tmp/migasfree.pid`        | PID lock file           |

| Path (Windows)                                   | Description       |
| ------------------------------------------------ | ----------------- |
| `%PROGRAMDATA%\migasfree-client\migasfree.conf`  | Configuration     |
| `%PROGRAMDATA%\migasfree-client\keys\`           | Signing keys      |
| `%PROGRAMDATA%\migasfree-client\mtls\`           | mTLS certificates |

## See Also

- [Getting Started](../getting-started.md)
- [Configuration Reference](configuration.md)
- [Environment Variables](environment-variables.md)
- [Troubleshooting](../how-to/troubleshooting.md)
