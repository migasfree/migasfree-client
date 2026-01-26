# migasfree-client Stakeholder Context

Business context for understanding migasfree-client requirements and users.

## What is migasfree?

**migasfree** is an open-source systems management platform for managing fleets of computers. The **client** component runs on managed computers and:

- Synchronizes with the central server
- Installs/removes packages as directed
- Reports hardware and software inventory
- Configures devices (printers)
- Executes server-defined checks (faults)

## Primary Users

| Role | Needs | Pain Points |
|------|-------|-------------|
| **System Administrator** | Reliable sync, clear errors, automation | Unclear failures, manual intervention |
| **IT Manager** | Inventory reports, compliance tracking | Missing data, incomplete views |
| **End User** | Minimal disruption, fast sync | Slow syncs, popup interruptions |
| **Security Team** | Audit logs, secure communication | Gaps in logging, cert management |
| **Package Maintainer** | Easy upload workflow, clear docs | Complex workflow, missing docs |

## Deployment Context

- **Primary organization**: Ayuntamiento de Zaragoza
- **Scale**: Hundreds to thousands of managed desktops
- **Platforms**: 
  - Debian-based Linux (AZLinux - custom distribution)
  - Windows 10+
- **Network**: May include proxies, restricted connectivity

## Feature Priorities

When prioritizing features, consider:

1. **Reliability**: Sync failures directly impact IT operations
2. **Security**: mTLS and secure credential handling are critical
3. **Cross-platform**: Features must work on both Linux and Windows
4. **Visibility**: Admins need clear status and error reporting
5. **Minimal disruption**: End users shouldn't be interrupted during work

## Key Metrics

- Sync success rate
- Time to apply package changes
- Device auto-configuration success
- Error clarity (can admins diagnose without logs?)
