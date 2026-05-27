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
| `-q`, `--quiet`   | Enable quiet mode (suppress output)          |

## Privilege Requirements

Migasfree v5 implements a zero-trust architecture. All communication with the server is authenticated using **mTLS certificates** and **JWS payload signatures**.

For security reasons, these cryptographic keys (located in `/var/migasfree-client/keys/` and `/var/migasfree-client/mtls/`) are strictly protected with `0600` permissions and are owned by `root`.

**As a result, any CLI command that interacts with the Migasfree Server API MUST be executed with administrative privileges (`root` or `sudo`).**

* **Requires `sudo`**: `sync`, `register`, `apps`, `traits`, `tags`, `info`, `upload`
* **Does NOT require `sudo`**: `search` (queries the local Package Management System without contacting the server)

If you attempt to run a command that requires server interaction without privileges, the CLI will safely abort and display a `Permission denied reading mTLS security keys` error.

## Commands

### sync

Synchronizes the computer with the migasfree server. This is the primary command for client-server communication.

```bash
migasfree sync [options]
```

**Options:**

| Option                  | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `-f`, `--force-upgrade` | Force package updates even if Auto_Update_Packages is False  |
| `-j`, `--json`          | Structured JSON stream output (ideal for GUI integration)   |
| `-dev`, `--devices`     | Synchronize devices only                                     |
| `-hard`, `--hardware`   | Synchronize hardware only                                    |
| `-soft`, `--software`   | Synchronize software only                                    |
| `-att`, `--attributes`  | Synchronize attributes only                                  |
| `-fau`, `--faults`      | Synchronize faults only                                      |

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

**Options:**

| Option         | Description                                                 |
| -------------- | ----------------------------------------------------------- |
| `-j`, `--json` | Structured JSON stream output (ideal for GUI integration)   |

**Examples:**

```bash
# Install a single package
sudo migasfree install htop

# Install multiple packages
sudo migasfree install vim git curl
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

**Options:**

| Option         | Description                                                 |
| -------------- | ----------------------------------------------------------- |
| `-j`, `--json` | Structured JSON stream output (ideal for GUI integration)   |

**Examples:**

```bash
# Purge a package
sudo migasfree purge apache2
```

---

### traits

Retrieves computer traits from the server.

```bash
migasfree traits [PREFIX] [KEY]
```

**Arguments:**

| Argument | Description                                                                      |
| -------- | -------------------------------------------------------------------------------- |
| `PREFIX` | (Optional) Filter traits by prefix                                               |
| `KEY`    | (Optional) Extract individual value (id, description, name, value, prefix, sort) |

**Examples:**

```bash
# List all traits
migasfree traits

# Filter traits by 'OS' prefix
migasfree traits OS

# Get value of 'OS' trait
migasfree traits OS value
```

---

### tags

Manages computer tags on the server.

```bash
migasfree tags {-g | -s TAG [TAG...] | -c TAG [TAG...]}
```

**Options:**

| Option               | Description                                |
| -------------------- | ------------------------------------------ |
| `-g`, `--get`        | Get current tags from server (JSON format) |
| `-s`, `--set`        | Set tags on server (replaces existing tags)|
| `-c`, `--communicate`| Communicate tags to server (add tags)      |

**Examples:**

```bash
# Get tags
migasfree tags -g

# Set specific tags
migasfree tags -s production webserver

# Add tags to existing ones
migasfree tags -c branch-office
```

---

### attributes

Retrieves the computer's currently assigned attribute from the server.

```bash
migasfree attributes [options]
```

**Options:**

| Option         | Description                                   |
| -------------- | --------------------------------------------- |
| `-j`, `--json` | Output information in JSON format             |
| `-c`, `--cid`  | Retrieve exclusively the computer CID attribute |

**Examples:**

```bash
# Show assigned attributes (tabular formatting)
migasfree attributes

# Get the CID attribute in JSON format (quiet mode for pure JSON)
migasfree -q attributes -c --json
```

---

### info

Retrieves comprehensive computer and telemetry information from the server registry.

```bash
migasfree info [options] [KEY]
```

**Options:**

| Option         | Description                                   |
| -------------- | --------------------------------------------- |
| `-j`, `--json` | Output information in JSON format             |

**Arguments:**

| Argument | Description                                   |
| -------- | --------------------------------------------- |
| `KEY`    | (Optional) Extract a specific value.          |

Supported keys:

* **Identification**: `id`, `uuid`, `name`, `search`, `fqdn`
* **System Telemetry**: `status`, `sync_end_date`, `ip_address`, `mac_address`
* **Hardware Specifications**: `cpu`, `architecture`, `ram`, `storage`, `disks`
* **Product Info**: `product`, `product_system`

**Examples:**

```bash
# Show all information (key-value formatting)
migasfree info

# Show only the CPU details
migasfree info cpu

# Show only the RAM size
migasfree info ram

# Show only server-side id
migasfree info id

# Get all info in JSON format (quiet mode for pure JSON)
migasfree -q info --json
```

---

### label

Displays the computer's identification label. Useful for asset management and troubleshooting.

```bash
migasfree label
```

**Output includes:**

* Computer UUID
* Computer name
* IP address
* Server name
* Project

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
| `-r`, `--dir`    | Directory with packages to upload |

**Examples:**

```bash
# Upload a package to default store
migasfree upload -f mypackage_1.0_all.deb

# Upload to specific store
migasfree upload -f mypackage_1.0.rpm -s custom-store
```

---

### conf

Inspects or modifies configuration parameters in the `migasfree.conf` file. If invoked without write options, it lists all active options, their values, and their origin (`(ENV)`, `(FILE)`, or `(DEFAULT)`).

```bash
migasfree conf [options]
```

**Options:**

| Option                                      | Description                                                 |
| ------------------------------------------- | ----------------------------------------------------------- |
| `-s`, `--server VALUE`                      | Set the migasfree server hostname/IP or complete URL.       |
| `-p`, `--project VALUE`                     | Set the active project name.                                |
| `-a`, `--auto-update-packages {true,false}` | Enable or disable automatic package updates during sync.    |
| `-m`, `--manage-devices {true,false}`       | Enable or disable peripheral device management.             |
| `-u`, `--upload-hardware {true,false}`      | Enable or disable automatic hardware inventory uploads.     |
| `-c`, `--computer-name VALUE`               | Set the custom computer name override.                      |
| `--debug-mode {true,false}`                 | Enable or disable debug logging mode.                       |
| `-x`, `--proxy VALUE`                       | Set system proxy (`host:port`). Empty to disable.           |
| `-k`, `--package-proxy-cache VALUE`         | Set package proxy cache (`host:port`). Empty to disable.    |

**Examples:**

```bash
# View all current active configuration values and their sources
migasfree conf

# Update the Server and set Auto Update Packages to false
sudo migasfree conf -s https://migasfree.example.com -a false

# Configure proxy server
sudo migasfree conf -x 192.168.1.100:8080
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

* PEM files (cert.pem, key.pem, ca.pem)
* PKCS#12 files (.p12, .pfx)

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

### packages

Retrieves available or installed packages, or checks if specific packages are installed.

```bash
migasfree packages {-a | -i | -c JSON_ARRAY}
```

**Options:**

| Option               | Description                                                        |
| -------------------- | ------------------------------------------------------------------ |
| `-a`, `--available`  | Get available packages in repositories (JSON format if quiet).     |
| `-i`, `--installed`  | Get all installed packages on the system (JSON format if quiet).   |
| `-c`, `--check`      | Check which of the given packages are installed (takes JSON array).|

**Examples:**

```bash
# Get available packages (verbose)
migasfree packages -a

# Get installed packages (JSON format)
migasfree -q packages -i

# Check package installation status
migasfree packages -c '["firefox-esr", "vlc"]'
```

---

### apps

Retrieves available applications from the software catalog for the computer.

```bash
migasfree apps [options]
```

**Options:**

| Option           | Description                        |
| ---------------- | ---------------------------------- |
| `-c`, `--category` | Filter applications by category ID |
| `-j`, `--json`     | Output information in JSON format  |

**Examples:**

```bash
# List all available apps
migasfree apps

# List apps in category 3 in JSON format
migasfree -q apps -c 3 --json
```

---

### categories

Retrieves the list of software catalog categories.

```bash
migasfree categories [options]
```

**Options:**

| Option         | Description                       |
| -------------- | --------------------------------- |
| `-j`, `--json` | Output information in JSON format |

**Examples:**

```bash
# List all categories
migasfree categories

# Get categories in JSON format
migasfree -q categories --json
```

---

### devices

Retrieves physical and logical device assignments and capabilities.

migasfree devices [options]

```txt

**Options:**

| Option               | Description                                           |
| -------------------- | ----------------------------------------------------- |
| `-a`, `--available`  | Get available (unassigned) physical devices           |
| `-l`, `--logical`    | Get logical device relations                          |
| `-c`, `--capabilities` | Get capabilities info by specific capability ID     |
| `--device-id`        | Filter logical relations by a specific device ID      |
| `--assign ID`        | Assign logical device to the computer by ID           |
| `--unassign ID`      | Unassign logical device from the computer by ID       |
| `--set-default ID`   | Set default logical device for the computer by ID     |
| `-j`, `--json`       | Output information in JSON format                     |

**Examples:**

```bash
# List currently assigned devices
migasfree devices

# List available unassigned physical devices in JSON format
migasfree -q devices -a --json

# List logical device relations for device ID 5
migasfree devices -l --device-id 5

# Get capabilities info for ID 10
migasfree -q devices -c 10 --json

# Assign logical device 4 to the computer
sudo migasfree devices --assign 4

# Unassign logical device 4 from the computer
sudo migasfree devices --unassign 4

# Set logical device 4 as default for this computer
sudo migasfree devices --set-default 4

# Clear default logical device
sudo migasfree devices --set-default 0
```

---

### user-check

Verifies user credentials and checks if they have administrative privileges.

```bash
migasfree user-check -u USER -p PASSWORD
```

**Options:**

| Option            | Description                 |
| ----------------- | --------------------------- |
| `-u`, `--user`    | Username to verify          |
| `-p`, `--pwd`     | Password to verify          |

**Examples:**

```bash
# Check user auth and privilege (verbose)
migasfree user-check -u tux -p secret

# Quiet check returning JSON for machine integration
migasfree -q user-check -u tux -p secret
```

---

### network

Retrieves system network telemetry and configurations.

```bash
migasfree network [options]
```

**Options:**

| Option         | Description                                                 |
| -------------- | ----------------------------------------------------------- |
| `-j`, `--json` | Output network information as structured JSON               |

**Examples:**

```bash
# Get network details (text format)
migasfree network

# Get network details in JSON format
migasfree network --json
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

* [Getting Started](../getting-started.md)
* [Configuration Reference](configuration.md)
* [Environment Variables](environment-variables.md)
* [Troubleshooting](../how-to/troubleshooting.md)
