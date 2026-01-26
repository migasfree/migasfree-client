# Getting Started with migasfree-client

This guide will walk you through installing migasfree-client, configuring it to connect to your server, and performing your first synchronization.

## Prerequisites

Before you begin, ensure you have:

- A running migasfree server (ask your administrator for the server address)
- Administrator/root privileges on your computer
- Python 3.6 or higher (usually pre-installed on modern systems)

## Installation

### Debian/Ubuntu

```bash
# From the official repository (if available)
sudo apt update
sudo apt install migasfree-client

# Or using pip
sudo pip3 install migasfree-client
```

### Fedora

```bash
# Using pip
sudo pip3 install migasfree-client

# Or from RPM (if available)
sudo dnf install migasfree-client
```

### Arch Linux

```bash
# Using pip
sudo pip3 install migasfree-client

# Or from AUR
yay -S migasfree-client
```

### Windows 10+

```powershell
# Open PowerShell as Administrator
pip install migasfree-client

# Install additional Windows dependencies
pip install python-magic-bin pywin32 psutil
```

### Verify Installation

```bash
migasfree version
```

Expected output:

```text
migasfree client version: 5.0.x
```

## Configuration

### Step 1: Locate the Configuration File

| Platform | Configuration File Path                         |
| -------- | ----------------------------------------------- |
| Linux    | `/etc/migasfree.conf`                           |
| Windows  | `%PROGRAMDATA%\migasfree-client\migasfree.conf` |

### Step 2: Edit the Configuration

```bash
# Linux
sudo nano /etc/migasfree.conf

# Windows (PowerShell as Admin)
notepad $env:PROGRAMDATA\migasfree-client\migasfree.conf
```

### Step 3: Set Required Options

```ini
[client]
# Your migasfree server address (required)
Server = migasfree.example.com

# Protocol: http or https (default: http)
Protocol = https

# Project name (optional - auto-detected from OS)
# Project = Ubuntu-22.04
```

### Minimal Configuration Example

```ini
[client]
Server = migasfree.example.com
Protocol = https
```

## Registration

Before synchronizing, you must register your computer with the server.

```bash
sudo migasfree register -u admin
```

You will be prompted for:

1. **User**: Your migasfree server username
2. **Password**: Your migasfree server password

Expected output:

```text
Key /var/migasfree-client/keys/migasfree.example.com/server.pub created!
Key /var/migasfree-client/keys/migasfree.example.com/Ubuntu-22.04.pri created!
Computer registered at server
mTLS certificates downloaded
```

> **Note**: If your server supports mTLS, certificates will be automatically downloaded during registration.

## Your First Synchronization

Now you can synchronize your computer with the server:

```bash
sudo migasfree sync
```

This command will:

1. ✅ Upload computer attributes (hostname, IP, user, etc.)
2. ✅ Check for fault conditions
3. ✅ Configure package repositories
4. ✅ Install/remove mandatory packages
5. ✅ Update packages (if enabled)
6. ✅ Upload software inventory
7. ✅ Upload hardware information (if requested)
8. ✅ Configure devices (printers, etc.)

### Synchronization Output

```text
─────────────────────── Connecting to migasfree server... ───────────────────────
                                                                              Ok
───────────────────────── Evaluating attributes... ──────────────────────────────
HST: mycomputer                                                               Ok
USR: admin                                                                    Ok
NET: 192.168.1.100                                                            Ok
───────────────────────── Creating repositories... ──────────────────────────────
                                                                              Ok
───────────────────────── Updating packages... ──────────────────────────────────
                                                                              Ok
───────────────────────── Completed operations ──────────────────────────────────
```

## Next Steps

Now that you have migasfree-client running, you can:

### Learn More

- 📚 [Tutorial: Advanced Synchronization Options](tutorials/first-sync.md)
- 🔐 [Tutorial: Setting Up mTLS Security](tutorials/setup-mtls.md)

### Common Tasks

- 🔧 [How to troubleshoot sync issues](how-to/troubleshooting.md)
- 🔧 [How to configure proxy settings](how-to/proxy-setup.md)
- 🔧 [How to automate synchronization](how-to/automation.md)

### Reference

- 📖 [All CLI commands](reference/cli.md)
- 📖 [All configuration options](reference/configuration.md)
- 📖 [Environment variables](reference/environment-variables.md)

## Quick Command Reference

| Command                     | Description                  |
| --------------------------- | ---------------------------- |
| `migasfree sync`            | Synchronize with server      |
| `migasfree sync -f`         | Force package updates        |
| `migasfree search PATTERN`  | Search for packages          |
| `migasfree install PACKAGE` | Install a package            |
| `migasfree label`           | Show computer identification |
| `migasfree version`         | Show version info            |

## Getting Help

If you encounter issues:

1. **Enable debug mode**: `sudo migasfree sync -d`
2. **Check logs**: `/var/log/migasfree.log` (Linux) or Windows Event Viewer
3. **See troubleshooting**: [Troubleshooting Guide](how-to/troubleshooting.md)
4. **Report issues**: [GitHub Issues](https://github.com/migasfree/migasfree-client/issues)
