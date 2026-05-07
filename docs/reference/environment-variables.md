# Environment Variables Reference

migasfree-client supports environment variables to override configuration file settings. This is useful for containerized deployments, CI/CD pipelines, or temporary overrides.

## Configuration Override Variables

These variables override the corresponding settings in `migasfree.conf`:

### Client Section

| Variable                                | Config Option          | Description               | Example                           |
| --------------------------------------- | ---------------------- | ------------------------- | --------------------------------- |
| `MIGASFREE_CLIENT_SERVER`               | `Server`               | Server address (host, host:port, or full URL) | `migasfree.example.com` or `https://migasfree.example.com:8443` |
| `MIGASFREE_CLIENT_PROJECT`              | `Project`              | Project name              | `Ubuntu-22.04`                    |
| `MIGASFREE_CLIENT_COMPUTER_NAME`        | `Computer_Name`        | Override hostname         | `my-workstation`                  |
| `MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES` | `Auto_Update_Packages` | Auto-update packages      | `True` / `False`                  |
| `MIGASFREE_CLIENT_MANAGE_DEVICES`       | `Manage_Devices`       | Manage devices            | `True` / `False`                  |
| `MIGASFREE_CLIENT_UPLOAD_HARDWARE`      | `Upload_Hardware`      | Upload hardware info      | `True` / `False`                  |
| `MIGASFREE_CLIENT_PROXY`                | `Proxy`                | HTTP proxy                | `192.168.1.100:8080`              |
| `MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE`  | `Package_Proxy_Cache`  | Package cache proxy       | `apt-cache.local:3142`            |
| `MIGASFREE_CLIENT_DEBUG`                | `Debug`                | Enable debug mode         | `True` / `False`                  |

### Packager Section

| Variable                      | Config Option | Description               | Example        |
| ----------------------------- | ------------- | ------------------------- | -------------- |
| `MIGASFREE_PACKAGER_USER`     | `User`        | Package uploader username | `packager`     |
| `MIGASFREE_PACKAGER_PASSWORD` | `Password`    | Package uploader password | `secret`       |
| `MIGASFREE_PACKAGER_PROJECT`  | `Project`     | Default upload project    | `Ubuntu-22.04` |
| `MIGASFREE_PACKAGER_STORE`    | `Store`       | Default package store     | `main`         |

### Special Variables

| Variable         | Description                      | Example                         |
| ---------------- | -------------------------------- | ------------------------------- |
| `MIGASFREE_CONF` | Override configuration file path | `/custom/path/migasfree.conf`   |

## Usage Examples

### Basic Override

```bash
# Override server for a single command
MIGASFREE_CLIENT_SERVER=test-server.local sudo migasfree sync

# Non-standard port
MIGASFREE_CLIENT_SERVER=https://test-server.local:8443 sudo migasfree sync

# Enable debug mode temporarily
MIGASFREE_CLIENT_DEBUG=True sudo migasfree sync
```

### Docker/Container Usage

```dockerfile
FROM python:3.10-slim

RUN pip install migasfree-client

ENV MIGASFREE_CLIENT_SERVER=https://migasfree.example.com
ENV MIGASFREE_CLIENT_PROJECT=Docker-Container

CMD ["migasfree", "sync"]
```

```bash
# Run with environment variables
docker run -e MIGASFREE_CLIENT_SERVER=https://prod-server.example.com \
           -e MIGASFREE_CLIENT_DEBUG=True \
           migasfree-client
```

### Systemd Service Override

```ini
# /etc/systemd/system/migasfree-sync.service.d/override.conf
[Service]
Environment="MIGASFREE_CLIENT_SERVER=https://migasfree.example.com"
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      MIGASFREE_CLIENT_SERVER: ${{ secrets.MIGASFREE_SERVER }}
      MIGASFREE_PACKAGER_USER: ${{ secrets.PACKAGER_USER }}
      MIGASFREE_PACKAGER_PASSWORD: ${{ secrets.PACKAGER_PASSWORD }}
    steps:
      - name: Upload package
        run: migasfree upload -f mypackage.deb
```

### Shell Script

```bash
#!/bin/bash
# sync-with-custom-server.sh

export MIGASFREE_CLIENT_SERVER="https://custom-server.local"
export MIGASFREE_CLIENT_DEBUG="True"

migasfree sync
```

## Precedence Order

When the same setting is defined in multiple places, this precedence applies:

1. **Environment variables** (highest priority)
2. **Command-line arguments** (where applicable)
3. **Configuration file** (`migasfree.conf`)
4. **Default values** (lowest priority)

## Boolean Values

Boolean environment variables accept the following values:

| True                     | False                       |
| ------------------------ | --------------------------- |
| `True`, `true`, `TRUE`   | `False`, `false`, `FALSE`   |
| `Yes`, `yes`, `YES`      | `No`, `no`, `NO`            |
| `On`, `on`, `ON`         | `Off`, `off`, `OFF`         |
| `1`                      | `0`                         |
| `Y`, `y`                 | `N`, `n`                    |

## Debugging

To see which environment variables are being used:

```bash
# Enable debug and check logs
MIGASFREE_CLIENT_DEBUG=True migasfree sync 2>&1 | head -50

# The log will show:
# 2026-04-10T09:33:24+0200 - INFO - command - _show_config_options - Config client: {'server': 'example.com', ...}
```

## Security Considerations

> ⚠️ **Warning**: Environment variables containing passwords may be visible in:
>
> - Process listings (`ps aux`)
> - System logs
> - Shell history

**Best practices:**

- Use configuration files for passwords when possible
- Set `HISTCONTROL=ignorespace` and prefix commands with a space
- In CI/CD, use secrets management features

## See Also

- [Configuration Options](configuration.md)
- [Getting Started](../getting-started.md)
- [CLI Reference](cli.md)
