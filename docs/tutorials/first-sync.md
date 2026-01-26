# Your First Synchronization

This tutorial guides you through your first successful synchronization with a migasfree server. By the end, you'll understand the sync process and verify that your computer is properly managed.

## Learning Goals

After completing this tutorial, you will:

- ✅ Understand what happens during synchronization
- ✅ Know how to interpret sync output
- ✅ Verify your computer appears on the server
- ✅ Troubleshoot common first-sync issues

## Prerequisites

Before starting, ensure you have:

- [ ] migasfree-client installed
- [ ] Configuration file with server address
- [ ] Computer registered (completed `migasfree register`)

If you haven't done these steps, see [Getting Started](../getting-started.md) first.

## Step 1: Check Your Configuration

First, verify your configuration is correct:

```bash
# View current configuration
cat /etc/migasfree.conf
```

You should see at minimum:

```ini
[client]
Server = your-server.example.com
```

## Step 2: Verify Registration

Confirm your computer is registered:

```bash
# Check if signing keys exist
ls -la /var/migasfree-client/keys/*/
```

Expected output:

```text
-rw-r--r-- 1 root root 800 Jan 15 10:30 server.pub
-rw------- 1 root root 3243 Jan 15 10:30 MyProject.pri
```

If keys are missing, register first:

```bash
sudo migasfree register -u admin
```

## Step 3: Run Your First Sync

Now run the synchronization command:

```bash
sudo migasfree sync -d
```

> **Tip**: The `-d` flag enables debug output, which is helpful for understanding what's happening.

## Step 4: Understanding the Output

Let's break down what you'll see:

### Connection Phase

```text
─────────────────────── Connecting to migasfree server... ───────────────────────
                                                                              Ok
```

This confirms the client can reach the server and authenticate.

### Attributes Phase

```text
───────────────────────── Evaluating attributes... ──────────────────────────────
HST: mycomputer                                                               Ok
USR: admin                                                                    Ok
NET: 192.168.1.100                                                            Ok
PCI: 8086:1234 Intel Corporation Device                                       Ok
```

The client collects information about your computer:

- **HST** (Hostname): Your computer's name
- **USR** (User): Currently logged-in user
- **NET** (Network): IP addresses
- **PCI/USB**: Hardware devices

These "attributes" determine which software deployments apply to your computer.

### Faults Phase

```text
────────────────────────── Evaluating faults... ─────────────────────────────────
                                                                              Ok
```

The server can define "fault detection" scripts. Any issues found are reported here.

### Repository Phase

```text
───────────────────────── Creating repositories... ──────────────────────────────
base                                                                          Ok
updates                                                                       Ok
migasfree-deployment-1                                                        Ok
```

The client configures package repositories defined by the server. You can verify:

```bash
# Debian/Ubuntu
ls /etc/apt/sources.list.d/migasfree*

# Fedora/RHEL
ls /etc/yum.repos.d/migasfree*
```

### Package Phase

```text
───────────────────────── Installing packages... ─────────────────────────────────
htop                                                                          Ok
vim                                                                           Ok
───────────────────────── Removing packages... ──────────────────────────────────
nano                                                                          Ok
───────────────────────── Updating packages... ──────────────────────────────────
                                                                              Ok
```

The server can mandate:

- **Installing** specific packages (appear on all matching computers)
- **Removing** specific packages (security/policy compliance)
- **Updating** available package upgrades

### Inventory Phase

```text
───────────────────────── Uploading inventory... ─────────────────────────────────
                                                                              Ok
```

The client sends a list of all installed packages to the server.

### Hardware Phase

```text
───────────────────────── Uploading hardware... ─────────────────────────────────
                                                                              Ok
```

Detailed hardware information (CPU, RAM, disks, network) is uploaded.

### Devices Phase

```text
───────────────────────── Configuring devices... ─────────────────────────────────
HP LaserJet Pro M404                                                          Ok
```

Printers and other devices configured on the server are set up locally.

### Completion

```text
───────────────────────── Completed operations ──────────────────────────────────
```

Sync completed successfully!

## Step 5: Verify on the Server

Your administrator can now see your computer in the migasfree web interface:

1. Navigate to `https://your-server.example.com/`
2. Go to **Computers** section
3. Search for your hostname
4. View attributes, software inventory, and hardware details

## Step 6: Check the Label

Verify your computer's identification:

```bash
migasfree label
```

Example output:

```text
┌────────────────────────────────────────────────────────────────┐
│                         MIGASFREE                               │
├────────────────────────────────────────────────────────────────┤
│  UUID:     550e8400-e29b-41d4-a716-446655440000                │
│  Computer: mycomputer                                          │
│  IP:       192.168.1.100                                       │
│  Server:   migasfree.example.com                               │
│  Project:  Ubuntu-22.04                                        │
└────────────────────────────────────────────────────────────────┘
```

## Common First-Sync Issues

### "Connection error"

```bash
# Test connectivity
curl -v http://your-server.example.com/api/v1/public/server/info/
```

**Solutions:**

- Check server address in configuration
- Verify network connectivity
- Check firewall rules

### "401 Unauthorized"

**Solution:** Re-register your computer:

```bash
sudo migasfree remove-keys
sudo migasfree register -u admin
```

### "Project not found"

**Solution:** Set project explicitly in `/etc/migasfree.conf`:

```ini
Project = Ubuntu-22.04
```

Ask your administrator which projects exist on the server.

## What's Next?

Now that your first sync works:

- **Learn about mTLS**: [Setting Up mTLS Security](setup-mtls.md)
- **Automate syncs**: [How to Automate Synchronization](../how-to/automation.md)
- **Troubleshoot issues**: [Troubleshooting Guide](../how-to/troubleshooting.md)

## Summary

In this tutorial, you:

1. ✅ Verified your configuration and registration
2. ✅ Ran your first synchronization
3. ✅ Understood each phase of the sync process
4. ✅ Verified your computer is registered on the server
5. ✅ Learned how to troubleshoot common issues

Your computer is now part of the migasfree managed infrastructure!
