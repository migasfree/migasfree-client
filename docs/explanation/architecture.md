# Architecture Overview

This document explains the internal architecture of migasfree-client and how it interacts with the migasfree server.

## System Overview

migasfree is a systems management solution consisting of two main components:

```mermaid
graph TD
    subgraph Client System
        C[migasfree-client] --> PM[Package Manager<br/>apt/dnf/pacman/...]
    end
    
    subgraph Server Infrastructure
        S[migasfree-server] --> DB[(PostgreSQL<br/>+ Storage)]
    end
    
    C <-->|HTTPS/mTLS<br/>REST API| S
```

### Client Responsibilities

- Execute synchronization commands
- Collect and report computer attributes
- Manage local package repositories
- Install/remove packages via the local package manager
- Upload hardware and software inventories
- Configure devices (printers, etc.)
- Manage authentication certificates

### Server Responsibilities

- Store computer inventory and status
- Define deployments (packages to install/remove)
- Manage package repositories
- Define computer attributes and formulas
- Generate reports and statistics

## Client Architecture

```text
migasfree_client/
├── __main__.py          # Entry point & arg parser
├── command.py           # MigasFreeCommand orchestration
├── sync.py              # Synchronization logic
├── upload.py            # Package upload logic
├── info.py              # Computer information retrieval
├── tags.py              # Tag management
├── label.py             # Computer identification (ASCII art)
├── availability.py      # Server availability check
├── url_request.py       # HTTP requests with JWS/JWE + mTLS
├── secure.py            # Cryptographic operations (JWS/JWE)
├── mtls.py              # mTLS certificate management
├── utils.py             # Utility functions
├── settings.py          # Configuration management
├── mixins/
│   ├── config.py        # ConfigMixin (init, SSL, PMS selection)
│   ├── renderer.py      # RendererMixin (console output)
│   ├── evaluator.py     # CodeEvaluatorMixin (traits, faults)
│   ├── hardware.py      # HardwareCollectorMixin (lshw)
│   └── software.py      # SoftwareManagerMixin (PMS ops)
├── devices/             # Device management (Printers, CUPS)
└── pms/                 # Package Management Systems
    ├── __init__.py      # PMS factory + plugin discovery
    ├── pms.py           # Abstract base class
    ├── apt.py           # Debian/Ubuntu
    ├── dnf.py           # Fedora
    ├── yum.py           # RHEL/CentOS
    ├── zypper.py        # openSUSE
    ├── pacman.py        # Arch Linux
    ├── apk.py           # Alpine Linux
    └── wpt.py           # Windows
```

### Component Diagram

```mermaid
graph TD
    CLI[CLI Entry Point<br/>__main__.py] --> CMD[MigasFreeCommand<br/>command.py]

    CMD --> URL[UrlRequest<br/>url_request.py]
    CMD --> PMS[Pms Factory<br/>pms/*.py]
    CMD --> DEV[Devices Factory<br/>devices/*.py]
    CMD --> MTLS[mTLS<br/>mtls.py]

    URL --> SEC[secure.py<br/>JWS / JWE]
    URL --> SESSION[requests Session<br/>+ mTLS]

    PMS --> APT[Apt]
    PMS --> DNF[Dnf]
    PMS --> YUM[Yum]
    PMS --> ZYP[Zypper]
    PMS --> PAC[Pacman]
    PMS --> APK[Apk]
    PMS --> WPT[Wpt]

    DEV --> CUPS[Cupswrapper]
    DEV --> PLG[Plugins]

    MTLS --> CACERT[CA Certificate Mgmt]
    MTLS --> CERTFETCH[mTLS Certificate<br/>Fetch & Install]

    subgraph Mixins
        M1[HardwareCollectorMixin]
        M2[SoftwareManagerMixin]
        M3[CodeEvaluatorMixin]
        M4[ConfigMixin]
        M5[RendererMixin]
    end

    CMD --- M1
    CMD --- M2
    CMD --- M3
    CMD --- M4
    CMD --- M5
```

## Synchronization Flow

The `sync` command performs a series of operations in a strict, sequential order. Unlike old graphical representations that implied parallel execution, the actual logic executes step-by-step to guarantee integrity.

### High-level Flowchart

```mermaid
flowchart TD
    Start([Start Sync]) --> Avail{Server Available?}
    Avail -- No --> EndQueue([Queue for later])
    Avail -- Yes --> Attr[1. Upload Attributes & Faults]
    Attr --> PMS[2. Package Manager<br>Update Repos & Sync Packages]
    PMS --> SoftInv[3. Upload Software Inventory]
    SoftInv --> HwCheck{Hardware Capture<br>Required?}
    HwCheck -- Yes --> HwInv[4. Upload Hardware Inventory]
    HwCheck -- No --> Devices[5. Configure Logical Devices<br>e.g. Printers]
    HwInv --> Devices
    Devices --> Post[6. Traits, Events & Execution Errors]
    Post --> EndSync[7. End Synchronization]
    EndSync --> Finish([Sync Successful])
```

### Detailed Sequence Diagram

```mermaid
sequenceDiagram
    participant Client as MigasFreeSync
    participant Server as Migasfree Server
    participant PMS as Package Manager

    Client->>Server: Check Availability
    Client->>Client: Execute Pre-Sync Scripts
    Client->>Server: Upload Attributes & Faults
    Client->>PMS: Query Installed Software (BEFORE)
    Client->>Client: Create Repositories & Clean Cache
    Client->>PMS: Sync Packages (Mandatory & Updates)
    Client->>PMS: Query Installed Software (AFTER)
    Client->>Server: Upload Software Inventory (Diff)
    alt Hardware Capture Required
        Client->>Client: lshw (JSON)
        Client->>Server: Upload Hardware
    end
    Client->>Server: Sync Logical Devices (Printers)
    Client->>Server: Execute Traits & Events
    Client->>Client: Execute Post-Sync Scripts
    Client->>Server: Upload Execution Errors
    Client->>Server: End Synchronization
```

### Server Availability Check

Before starting synchronization, the client checks if the server can accept
new sync requests. This prevents overwhelming the server during peak loads.

**Flow:**

1. **Check migasfree-agent service**: First, the client checks if the
   `migasfree-agent` service is running locally using cross-platform detection:
   - Linux: `service`, `systemctl`, or `rc-service` (OpenRC)
   - Windows: `sc query`

2. **If service is NOT running**: Skip the availability endpoint call and
   proceed directly with synchronization. This is useful for:
   - Development environments without the full stack
   - Deployments without the manager component
   - Legacy setups

3. **If service IS running**: Query the server's availability endpoint:
   - **HTTP 200**: Server is available, proceed with sync
   - **HTTP 429 (Too Many Requests)**: Server is saturated, exit with
     `EAGAIN` and display retry time
   - **Connection error**: Assume available, let sync fail later if needed

## Security Architecture

### Authentication Layers

migasfree-client uses multiple security layers:

```mermaid
graph TD
    L1[Layer 1: Transport Security<br/>HTTPS Encryption] --> L2[Layer 2: Mutual TLS<br/>mTLS Certs]
    L2 --> L3[Layer 3: Message Signing<br/>JWS Integrity]
    L3 --> L4[Layer 4: Message Encryption<br/>JWE Sensitive Data]
    
    subgraph Protection
        L1 --- P1[Server Validation]
        L2 --- P2[Client Auth]
        L3 --- P3[Anti-Tampering]
        L4 --- P4[Privacy]
    end
```

### Key Storage

```text
/var/migasfree-client/
├── keys/
│   └── server.example.com/
│       ├── server.pub          # Server's public key (signing)
│       └── MyProject.pri       # Project's private key
└── mtls/
    └── server.example.com/
        ├── cert.pem            # Client certificate
        ├── key.pem             # Client private key (mode 600)
        └── ca.pem              # CA certificate
```

## Package Management Abstraction

The PMS (Package Management System) layer provides a unified interface across different Linux distributions and Windows:

```python
class PMS:
    """Abstract base class for package managers"""
    
    def install(packages: list) -> bool: ...
    def remove(packages: list) -> bool: ...
    def purge(packages: list) -> bool: ...
    def upgrade_all() -> bool: ...
    def search(pattern: str) -> list: ...
    def create_repos(repos: dict) -> bool: ...
    def clean_repos() -> bool: ...
    def get_installed() -> list: ...
```

### Supported Package Managers

| Class    | Distribution   | Package Format |
| -------- | -------------- | -------------- |
| `Apt`    | Debian, Ubuntu | .deb           |
| `Dnf`    | Fedora 22+     | .rpm           |
| `Yum`    | RHEL, CentOS   | .rpm           |
| `Zypper` | openSUSE       | .rpm           |
| `Pacman` | Arch Linux     | .pkg.tar.zst   |
| `Apk`    | Alpine Linux   | .apk           |
| `Wpt`    | Windows 10+    | .msi, .exe     |

## Data Flow

### Request Flow (Client → Server)

```text
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Python     │    │    Sign      │    │   HTTPS      │    │   Server     │
│   Dict       │───►│   (JWS)      │───►│   + mTLS     │───►│   API        │
│              │    │              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
     JSON               Signed              mTLS cert
     payload            token               included
```

### Response Flow (Server → Client)

```text
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Server     │    │   Server     │    │    Client    │    │   Python     │
│   Response   │───►│   Signs      │───►│   Verifies   │───►│   Dict       │
│              │    │   (JWS)      │    │   Signature  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
     JSON               Signed              Verified,
     response           response            decrypted
```

## Configuration Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION PRECEDENCE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Environment Variables        (Highest Priority)             │
│     └→ MIGASFREE_CLIENT_SERVER, etc.                            │
│                                                                 │
│  2. Command Line Arguments                                      │
│     └→ --debug, --pms, etc.                                     │
│                                                                 │
│  3. Configuration File                                          │
│     └→ /etc/migasfree.conf                                      │
│                                                                 │
│  4. Default Values               (Lowest Priority)              │
│     └→ Hardcoded in settings.py                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

The client implements a hierarchical error handling strategy:

| Error Type        | Handling           | User Impact              |
| ----------------- | ------------------ | ------------------------ |
| Network errors    | Retry with backoff | Temporary interruption   |
| Auth errors       | Stop and report    | Requires re-registration |
| Package errors    | Continue sync      | Partial completion       |
| Server saturation | Wait and retry     | Delayed execution        |

## See Also

- [Security Model](security.md)
- [CLI Reference](../reference/cli.md)
- [Configuration Reference](../reference/configuration.md)
- [Troubleshooting](../how-to/troubleshooting.md)
