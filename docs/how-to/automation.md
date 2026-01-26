# Automate Synchronization

This guide shows how to set up automatic synchronization so your computers stay up-to-date without manual intervention.

## Quick Setup

### Linux (systemd timer)

```bash
# The service file
sudo tee /etc/systemd/system/migasfree-sync.service << 'EOF'
[Unit]
Description=migasfree client synchronization
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/migasfree sync
EOF

# The timer (runs every 2 hours)
sudo tee /etc/systemd/system/migasfree-sync.timer << 'EOF'
[Unit]
Description=Run migasfree sync periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
RandomizedDelaySec=10min

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now migasfree-sync.timer
```

### Windows (Task Scheduler)

```powershell
# Run as Administrator
$action = New-ScheduledTaskAction -Execute "migasfree" -Argument "sync"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 2) -Once -At (Get-Date)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "migasfree-sync" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

## Detailed Options

### Sync Frequency Recommendations

| Environment      | Frequency         | Rationale                            |
| ---------------- | ----------------- | ------------------------------------ |
| Workstations     | Every 2-4 hours   | Balance updates with user experience |
| Servers          | Daily (off-hours) | Minimize disruption                  |
| Kiosks/Labs      | On boot + hourly  | Ensure consistent state              |
| Critical systems | Manual only       | Full control over changes            |

### Randomized Delay

Avoid all computers syncing simultaneously (thundering herd):

**systemd:**

```ini
# In migasfree-sync.timer
RandomizedDelaySec=30min
```

**cron:**

```bash
# Sleep random 0-1800 seconds before sync
RANDOM_DELAY=$(shuf -i 0-1800 -n 1)
sleep $RANDOM_DELAY && migasfree sync
```

### On-Boot Synchronization

Ensure computers sync after startup:

**systemd:**

```ini
# In migasfree-sync.timer
OnBootSec=5min
```

**cron (Linux):**

```bash
@reboot sleep 300 && /usr/bin/migasfree sync
```

### Network Dependency

Wait for network before syncing:

**systemd:**

```ini
# In migasfree-sync.service
After=network-online.target
Wants=network-online.target
```

### Logging

Redirect output for troubleshooting:

**systemd:**

```ini
# Logs go to journald automatically
# View with: journalctl -u migasfree-sync.service
```

**cron:**

```bash
0 */2 * * * /usr/bin/migasfree sync >> /var/log/migasfree-cron.log 2>&1
```

## Monitoring

### Check timer status (systemd)

```bash
# List all timers
systemctl list-timers

# Check specific timer
systemctl status migasfree-sync.timer

# View logs
journalctl -u migasfree-sync.service -f
```

### Check scheduled task (Windows)

```powershell
Get-ScheduledTask -TaskName "migasfree-sync" | Get-ScheduledTaskInfo
```

## Disable/Enable

### Temporarily disable

```bash
# Linux
sudo systemctl stop migasfree-sync.timer

# Windows
Disable-ScheduledTask -TaskName "migasfree-sync"
```

### Re-enable

```bash
# Linux
sudo systemctl start migasfree-sync.timer

# Windows
Enable-ScheduledTask -TaskName "migasfree-sync"
```

## Troubleshooting

### Timer not running

```bash
# Check timer status
systemctl status migasfree-sync.timer

# Check for errors
journalctl -u migasfree-sync.service --since "1 hour ago"
```

### Overlapping runs

If sync takes longer than the interval, prevent overlap:

```ini
# In migasfree-sync.service
[Service]
Type=oneshot
# Prevent multiple instances
ExecStartPre=/bin/sh -c '! pgrep -x migasfree'
```

## See Also

- [CLI Reference](../reference/cli.md)
- [Troubleshooting](troubleshooting.md)
- [Configuration](../reference/configuration.md)
