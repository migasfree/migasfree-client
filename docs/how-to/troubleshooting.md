# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with migasfree-client.

## Quick Diagnostics

Before troubleshooting, gather diagnostic information:

```bash
# Enable debug mode and run sync
sudo migasfree sync -d

# Check the log file
cat /var/log/migasfree.log | tail -100

# Verify configuration
cat /etc/migasfree.conf
```

## Common Issues

### Connection Problems

#### "Connection refused" or "Connection error"

**Symptoms:**

```text
Connection error: [Errno 111] Connection refused
```

**Causes and Solutions:**

| Cause                    | Solution                                |
| ------------------------ | --------------------------------------- |
| Server address incorrect | Check `Server` in `/etc/migasfree.conf` |
| Server is down           | Contact your administrator              |
| Wrong port               | Check `Port` setting or use default     |
| Firewall blocking        | Ensure port 80/443 is open              |

**Diagnosis:**

```bash
# Test connectivity
ping your-server.example.com

# Test HTTP/HTTPS port
curl -v http://your-server.example.com/api/v1/public/server/info/
```

#### "Name or service not known"

**Symptoms:**

```text
Connection error: [Errno -2] Name or service not known
```

**Solution:**

```bash
# Verify DNS resolution
nslookup your-server.example.com

# Or use IP address directly in config
Server = 192.168.1.100
```

---

### SSL/TLS Certificate Issues

#### "SSL certificate verify failed"

**Symptoms:**

```text
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**

1. **If using self-signed certificates:**

   ```bash
   # Install your CA certificate
   sudo cp your-ca.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates
   ```

2. **If using mTLS:**

   ```bash
   # Re-import mTLS certificates
   sudo migasfree import-mtls /path/to/certificate.tar
   ```

3. **Temporary workaround (not recommended for production):**

   ```ini
   # In migasfree.conf
   Protocol = http
   ```

#### "Certificate not yet valid" or "Certificate has expired"

**Symptoms:**

```text
certificate is not yet valid
# or
certificate has expired
```

**Solutions:**

1. **Check system time:**

   ```bash
   date
   # If incorrect:
   sudo timedatectl set-ntp true
   ```

2. **Re-register to get new certificates:**

   ```bash
   sudo migasfree remove-keys
   sudo migasfree register -u admin
   ```

---

### Authentication Issues

#### "401 Unauthorized"

**Symptoms:**

```text
HTTP error code: 401
```

**Causes:**

- Invalid or expired signing keys
- Computer not registered
- Wrong credentials

**Solutions:**

1. **Re-register the computer:**

   ```bash
   sudo migasfree remove-keys
   sudo migasfree register -u admin
   ```

2. **Verify keys exist:**

   ```bash
   ls -la /var/migasfree-client/keys/your-server/
   # Should contain: server.pub, Project.pri
   ```

#### "403 Forbidden"

**Symptoms:**

```text
HTTP error code: 403
```

**Cause:** User doesn't have permission for this operation.

**Solution:** Contact your migasfree administrator.

---

### Package Management Issues

#### "Package not found"

**Symptoms:**

```text
E: Unable to locate package xyz
```

**Solutions:**

1. **Refresh package lists:**

   ```bash
   sudo migasfree sync
   # This recreates repositories and refreshes cache
   ```

2. **Check repository configuration:**

   ```bash
   # Debian/Ubuntu
   ls -la /etc/apt/sources.list.d/migasfree*
   
   # Fedora/RHEL
   ls -la /etc/yum.repos.d/migasfree*
   ```

3. **Force repository recreation:**

   ```bash
   # Remove migasfree repos and sync again
   sudo rm /etc/apt/sources.list.d/migasfree*
   sudo migasfree sync
   ```

#### "Lock file exists" / "Could not get lock"

**Symptoms:**

```text
E: Could not get lock /var/lib/dpkg/lock
```

**Solutions:**

1. **Wait for other package manager to finish:**

   ```bash
   # Check for running package managers
   ps aux | grep -E 'apt|dpkg|yum|dnf'
   ```

2. **If no other process is running:**

   ```bash
   sudo rm /var/lib/dpkg/lock
   sudo rm /var/lib/apt/lists/lock
   sudo dpkg --configure -a
   ```

---

### Registration Issues

#### "Project not found" (404)

**Symptoms:**

```text
HTTP error code: 404
```

**Cause:** The project doesn't exist on the server.

**Solutions:**

1. **Check auto-detected project:**

   ```bash
   python3 -c "import distro; print(f'{distro.name()}-{distro.version()}')"
   ```

2. **Set project manually:**

   ```ini
   # In migasfree.conf
   Project = Ubuntu-22.04
   ```

3. **Contact administrator** to create the project on the server.

#### "Computer already registered with different UUID"

**Cause:** Hardware UUID changed (VM cloned, hardware replaced).

**Solution:** Contact your administrator to remove the old computer entry, then re-register.

---

### Synchronization Issues

#### "Another instance is running"

**Symptoms:**

```text
Another instance of migasfree is running: 12345
```

**Solutions:**

1. **Wait for the other process to finish**

2. **If the process is stuck:**

   ```bash
   # Check if process exists
   ps -p 12345
   
   # If not running, remove lock file
   sudo rm /var/tmp/migasfree.pid
   ```

#### "Server is saturated"

**Symptoms:**

```text
Server is saturated. Please try again later. (Retry after 30 seconds)
```

**Cause:** Too many computers syncing simultaneously. The server returns HTTP 429
to prevent overload.

**How it works:**

Before starting synchronization, migasfree-client checks server availability:

1. First, it checks if the `migasfree-agent` service is running locally
2. If running, it queries the server's availability endpoint
3. If the server responds with HTTP 429, sync is aborted with `EAGAIN`

**Solutions:**

1. **Wait and retry:**

   ```bash
   # The error message includes the retry delay
   sleep 30 && sudo migasfree sync
   ```

2. **Stagger sync times:** Configure randomized delays across your fleet
   to prevent thundering herd:

   ```bash
   # Add to cron jobs
   sleep $((RANDOM % 600)) && migasfree sync
   ```

3. **Check if migasfree-agent service is needed:**

   If you don't use the manager component, you can ignore availability
   checks. The client will skip the check if the service isn't running:

   ```bash
   # Check if service is running
   systemctl status migasfree-agent
   # or
   service migasfree-agent status
   ```

---

### mTLS Issues

#### "mTLS certificate not found"

**Symptoms:**
Sync works but doesn't use mTLS authentication.

**Solutions:**

1. **Check certificate files:**

   ```bash
   ls -la /var/migasfree-client/mtls/your-server/
   # Should contain: cert.pem, key.pem, ca.pem
   ```

2. **Import certificates manually:**

   ```bash
   sudo migasfree import-mtls /path/to/certificate.tar
   ```

3. **Re-register to fetch certificates:**

   ```bash
   sudo migasfree register -u admin
   ```

#### Certificate permission errors

**Symptoms:**

```text
Permission denied: '/var/migasfree-client/mtls/...'
```

**Solution:**

```bash
sudo chmod 600 /var/migasfree-client/mtls/your-server/key.pem
sudo chmod 644 /var/migasfree-client/mtls/your-server/cert.pem
sudo chmod 644 /var/migasfree-client/mtls/your-server/ca.pem
```

---

## Debug Mode

For detailed troubleshooting, enable debug mode:

```bash
# Command line
sudo migasfree sync -d

# Or in configuration
# /etc/migasfree.conf
[client]
Debug = True
```

Debug logs are written to:

- **Linux**: `/var/log/migasfree.log`
- **Windows**: `C:\Windows\Temp\logs\migasfree.log`

## Log Analysis

### Key Log Messages

| Message                         | Meaning                       |
| ------------------------------- | ----------------------------- |
| `mTLS enabled, protocol: https` | mTLS is working               |
| `Response get_computer_id: ...` | Computer identified on server |
| `Error creating repositories`   | Repository config failed      |
| `connection error`              | Network/server issue          |

### Filtering Logs

```bash
# Show only errors
grep -i error /var/log/migasfree.log

# Show today's logs
grep "$(date +%Y-%m-%d)" /var/log/migasfree.log

# Show last sync attempt
grep -A 50 "in execution" /var/log/migasfree.log | tail -60
```

## Getting Help

If you can't resolve the issue:

1. **Collect diagnostics:**

   ```bash
   migasfree version > diagnostics.txt
   cat /etc/migasfree.conf >> diagnostics.txt
   tail -200 /var/log/migasfree.log >> diagnostics.txt
   ```

2. **Open an issue**: [GitHub Issues](https://github.com/migasfree/migasfree-client/issues)
   - Include the diagnostics file
   - Describe what you expected vs what happened
   - Include steps to reproduce

## See Also

- [Configuration Reference](../reference/configuration.md)
- [Environment Variables](../reference/environment-variables.md)
- [CLI Reference](../reference/cli.md)
