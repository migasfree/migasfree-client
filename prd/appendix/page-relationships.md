# Command Flow & State Transitions

This document maps out the high-level operational lifecycle, dependency graph, and state transitions of `migasfree-client` sessions.

---

## 1. High-Level Lifecycle & Dependency Graph

`migasfree-client` execution follows a structured, sequential security and configuration validation flow. It verifies identities and states before initiating active workloads.

```mermaid
graph TD
    Start([Execute migasfree CLI]) --> Init[Initialize Logging & Environment]
    Init --> ReadConf[Load Configuration File]
    ReadConf --> CheckPrivs{Is User Root/Admin?}
    
    CheckPrivs -- No --> FailPrivs[Exit with EPERM]
    CheckPrivs -- Yes --> CheckKeys{Do Project Keys Exist?}
    
    CheckKeys -- No --> AutoReg[Initiate Auto-Registration]
    AutoReg --> SaveKeys[Save server.pub & project.pri]
    SaveKeys --> GetCert[Fetch mTLS Certificate]
    GetCert --> CheckKeys
    
    CheckKeys -- Yes --> CheckSaturate{Is Server Saturated?}
    
    CheckSaturate -- Yes --> Saturated[Exit with EAGAIN]
    CheckSaturate -- No --> MainDispatch{Dispatch Subcommand}
    
    MainDispatch -- sync --> ExecSync[Execute Full Synchronization]
    MainDispatch -- register --> ExecReg[Re-Register Computer]
    MainDispatch -- tags --> ExecTags[Set/Get Tags]
    MainDispatch -- upload --> ExecUpload[Upload Package Files]
    MainDispatch -- conf --> ExecConf[Update Local Configuration]
    
    ExecSync --> Finish([Exit with ALL_OK])
    ExecReg --> Finish
    ExecTags --> Finish
    ExecUpload --> Finish
    ExecConf --> Finish
```

---

## 2. Cross-Command State Coupling

CLI commands do not run in a continuous UI state machine but share persistent files and database configurations that couple their behaviors.

| Origin Command | Destination Command | Shared Resource | Shared State / Description |
| :--- | :--- | :--- | :--- |
| `register` | `sync` | Cryptographic Keys & Certificates | `register` downloads the asymmetric keys (`server.pub` and `<project>.pri`) and mTLS certificate. Without these, `sync` cannot run and exits with `EPERM`. |
| `sync` | `traits` | `computer_traits.json` | `sync` downloads and updates the global traits profile, caching it locally in JSON format. `traits` reads this cache to display current configuration values. |
| `sync` | Event Hooks | `events.json` & `.env` | `sync` calculates a diff between historical and newly retrieved traits. It writes this difference into `.env` and `.json` in the `events.d` folder and invokes local event scripts. |
| `conf` | All Commands | `migasfree.conf` | Modifying settings (such as proxy, cache, or update flags) via the `conf` command immediately alters the communication and package updates of subsequent runs of `sync`, `register`, or `upload`. |
| `sync` | `info` | Computer ID Cache | `sync` automatically requests and caches the server-assigned internal integer ID. `info` retrieves this cached ID directly to display metadata without making redundant network queries. |
