# Configuration Reference

Complete reference for all migasfree-client configuration options.

## Configuration File Location

| Platform | Path                                            |
| -------- | ----------------------------------------------- |
| Linux    | `/etc/migasfree.conf`                           |
| Windows  | `%PROGRAMDATA%\migasfree-client\migasfree.conf` |

You can override the location with the `MIGASFREE_CONF` environment variable.

## File Format

The configuration file uses INI format with two sections: `[client]` and `[packager]`.

```ini
[client]
Server = migasfree.example.com
Protocol = https

[packager]
User = packager
```

## Client Section

### Connection Settings

#### Server

**Required**. The hostname or IP address of the migasfree server.

```ini
Server = migasfree.example.com
```

| Property    | Value                       |
| ----------- | --------------------------- |
| Type        | String                      |
| Default     | (none)                      |
| Environment | `MIGASFREE_CLIENT_SERVER`   |

---

#### Protocol

The connection protocol to use.

```ini
Protocol = https
```

| Property     | Value                       |
| ------------ | --------------------------- |
| Type         | String                      |
| Default      | `http`                      |
| Valid values | `http`, `https`             |
| Environment  | `MIGASFREE_CLIENT_PROTOCOL` |

---

#### Port

Server port number. Optional if using default ports.

```ini
Port = 8443
```

| Property    | Value                         |
| ----------- | ----------------------------- |
| Type        | Integer                       |
| Default     | `80` (http) or `443` (https)  |
| Environment | `MIGASFREE_CLIENT_PORT`       |

---

### Project Settings

#### Project

The project name that identifies this computer's OS/distribution on the server.

```ini
Project = Ubuntu-22.04
```

| Property    | Value                        |
| ----------- | ---------------------------- |
| Type        | String                       |
| Default     | Auto-detected from OS        |
| Environment | `MIGASFREE_CLIENT_PROJECT`   |

**Auto-detection logic:**

- Linux: `{distribution}-{version}` (e.g., `Ubuntu-22.04`, `Fedora-38`)
- Windows: `Windows-{version}` (e.g., `Windows-10`)

---

#### Computer_Name

Override the computer's hostname for identification.

```ini
Computer_Name = workstation-042
```

| Property    | Value                              |
| ----------- | ---------------------------------- |
| Type        | String                             |
| Default     | System hostname                    |
| Environment | `MIGASFREE_CLIENT_COMPUTER_NAME`   |

---

### Behavior Settings

#### Auto_Update_Packages

Automatically upgrade available packages during sync.

```ini
Auto_Update_Packages = False
```

| Property    | Value                                     |
| ----------- | ----------------------------------------- |
| Type        | Boolean                                   |
| Default     | `True`                                    |
| Environment | `MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES`   |

**Note:** Use `migasfree sync -f` to force updates when this is `False`.

---

#### Manage_Devices

Enable device management (printers, etc.) during sync.

```ini
Manage_Devices = True
```

| Property    | Value                               |
| ----------- | ----------------------------------- |
| Type        | Boolean                             |
| Default     | `True`                              |
| Environment | `MIGASFREE_CLIENT_MANAGE_DEVICES`   |

---

#### Upload_Hardware

Upload hardware inventory information to the server.

```ini
Upload_Hardware = True
```

| Property    | Value                                |
| ----------- | ------------------------------------ |
| Type        | Boolean                              |
| Default     | `True`                               |
| Environment | `MIGASFREE_CLIENT_UPLOAD_HARDWARE`   |

---

### Proxy Settings

#### Proxy

HTTP proxy for connecting to the migasfree server.

```ini
Proxy = 192.168.1.100:8080
```

| Property    | Value                      |
| ----------- | -------------------------- |
| Type        | String (host:port)         |
| Default     | (none)                     |
| Environment | `MIGASFREE_CLIENT_PROXY`   |

**Format:** `host:port` or `http://host:port`

---

#### Package_Proxy_Cache

Proxy/cache server for package downloads (e.g., apt-cacher-ng).

```ini
Package_Proxy_Cache = apt-cacher.local:3142
```

| Property    | Value                                    |
| ----------- | ---------------------------------------- |
| Type        | String (host:port)                       |
| Default     | (none)                                   |
| Environment | `MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE`   |

This is applied to repository URLs, not to the migasfree API.

---

### Debugging

#### Debug

Enable debug logging and verbose output.

```ini
Debug = True
```

| Property    | Value                      |
| ----------- | -------------------------- |
| Type        | Boolean                    |
| Default     | `False`                    |
| Environment | `MIGASFREE_CLIENT_DEBUG`   |

Logs are written to `/var/log/migasfree.log` (Linux) or `C:\Windows\Temp\logs\migasfree.log` (Windows).

---

## Packager Section

Settings for package uploading functionality.

### User

Username for package upload authentication.

```ini
[packager]
User = packager
```

| Property    | Value                       |
| ----------- | --------------------------- |
| Type        | String                      |
| Default     | (none)                      |
| Environment | `MIGASFREE_PACKAGER_USER`   |

---

### Password

Password for package upload authentication.

```ini
Password = secret
```

| Property    | Value                           |
| ----------- | ------------------------------- |
| Type        | String                          |
| Default     | (none)                          |
| Environment | `MIGASFREE_PACKAGER_PASSWORD`   |

> ⚠️ **Security**: Consider using environment variables instead of storing passwords in configuration files.

---

### Packager-Project

Default project for package uploads.

```ini
Project = Ubuntu-22.04
```

| Property    | Value                          |
| ----------- | ------------------------------ |
| Type        | String                         |
| Default     | Value from `[client]` section  |
| Environment | `MIGASFREE_PACKAGER_PROJECT`   |

---

### Store

Default store for package uploads.

```ini
Store = production
```

| Property    | Value                        |
| ----------- | ---------------------------- |
| Type        | String                       |
| Default     | `org`                        |
| Environment | `MIGASFREE_PACKAGER_STORE`   |

---

## Complete Example

```ini
#
# migasfree-client configuration
#

[client]
# Server connection
Server = migasfree.example.com
Protocol = https
Port = 443

# Project (auto-detected if not specified)
# Project = Ubuntu-22.04

# Optional: Override hostname
# Computer_Name = custom-name

# Behavior
Auto_Update_Packages = True
Manage_Devices = True
Upload_Hardware = True

# Proxy (if needed)
# Proxy = proxy.example.com:8080
# Package_Proxy_Cache = apt-cacher.local:3142

# Debugging
Debug = False

[packager]
# Package upload credentials (optional)
# User = packager
# Password = secret
# Store = main
```

## Boolean Values

Boolean options accept the following values:

| True                     | False                       |
| ------------------------ | --------------------------- |
| `True`, `true`, `TRUE`   | `False`, `false`, `FALSE`   |
| `Yes`, `yes`, `YES`      | `No`, `no`, `NO`            |
| `On`, `on`, `ON`         | `Off`, `off`, `OFF`         |
| `1`                      | `0`                         |

## Permissions

The configuration file should be readable by the user running migasfree commands:

```bash
# Typical permissions
sudo chmod 644 /etc/migasfree.conf

# If file contains passwords, restrict access
sudo chmod 600 /etc/migasfree.conf
```

## See Also

- [Environment Variables](environment-variables.md)
- [CLI Reference](cli.md)
- [Getting Started](../getting-started.md)
