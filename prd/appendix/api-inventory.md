# API Inventory

This document maps all the API endpoints utilized by `migasfree-client` to communicate with the Migasfree Server, detailed by their respective modules and functionality.

---

## 1. Authentication & Security

All communications with endpoints located under the `/api/v1/safe/` namespace require mutual TLS (**mTLS**) authentication and JSON Web Signatures (**JWS**) to verify payload integrity.

| Path | Method | Access Type | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/public/server/info/` | `GET` | Public | Retrieves server version, supported encryption standards, and status information. |
| `/api/v1/public/keys/project/` | `POST` | Public | Initiates registration and fetches cryptographic keys (`server.pub` and `<project>.pri`) for a project. |
| `/api/v1/public/keys/repositories/` | `GET` | Public | Obtains the public keys of active package repositories to verify signature integrity. |
| `/api/v1/public/keys/packager/` | `GET` | Public | Retrieves authorized packager public keys. |

---

## 2. Core Computer Management

| Path | Method | Access Type | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/safe/computers/id/` | `POST` | mTLS + JWS | Returns the unique server-assigned computer ID matching the client's UUID and Name. |
| `/api/v1/safe/computers/` | `POST` | Public | Enrolls a new computer into the system with its hardware UUID, computer name, and IP address. |
| `/api/v1/safe/computers/label/` | `GET` | mTLS + JWS | Retrieves support desk identification info (label layout) for terminal printing. |
| `/api/v1/safe/computers/info/` | `GET` | mTLS + JWS | Retrieves comprehensive computer metadata and system telemetry (CPU, RAM, status, network). |
| `/api/v1/safe/eot/` | `POST` | mTLS + JWS | Signals "End of Transmission" to release locks and finalize CLI session. |

---

## 3. Synchronization & Inventory Uploads

| Path | Method | Access Type | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/safe/computers/properties/` | `GET` | mTLS + JWS | Fetches dynamic properties and attribute evaluation rules for the system. |
| `/api/v1/safe/computers/faults/definitions/` | `GET` | mTLS + JWS | Fetches definitions of system faults to check against local parameters. |
| `/api/v1/safe/computers/repositories/` | `GET` | mTLS + JWS | Fetches lists of package repositories assigned to the computer's profile. |
| `/api/v1/safe/computers/packages/mandatory/` | `GET` | mTLS + JWS | Fetches packages defined as mandatory for installation/upgrade. |
| `/api/v1/safe/computers/devices/` | `GET` | mTLS + JWS | Fetches logical peripheral allocations (assigned printers and drivers). |
| `/api/v1/safe/computers/hardware/required/` | `GET` | mTLS + JWS | Queries whether a hardware inventory upload is required from the client. |
| `/api/v1/safe/computers/traits/` | `GET` | mTLS + JWS | Downloads system traits (configuration states, tags, and custom groups). |
| `/api/v1/safe/computers/errors/` | `POST` | mTLS + JWS | Uploads local execution errors and stderr dumps from previous runs. |
| `/api/v1/safe/computers/hardware/` | `POST` | mTLS + JWS | Uploads detailed local hardware inventory gathered by `lshw` / WMI. |
| `/api/v1/safe/computers/attributes/` | `POST` | mTLS + JWS | Uploads evaluated key-value system attributes. |
| `/api/v1/safe/computers/faults/` | `POST` | mTLS + JWS | Uploads evaluated system faults. |
| `/api/v1/safe/computers/software/` | `POST` | mTLS + JWS | Uploads a comprehensive list of installed packages on the machine. |
| `/api/v1/safe/computers/devices/changes/` | `POST` | mTLS + JWS | Uploads status changes or installation failures of printers. |
| `/api/v1/safe/synchronizations/` | `POST` | mTLS + JWS | Logs start and end timestamps, consumer version, and PMS success status of a sync. |
| `/manager/v1/public/synchronizations/availability/` | `GET` | Public | Check if the synchronization queue is full to prevent server saturation. |

---

## 4. Tags & Custom Packaging

| Path | Method | Access Type | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/safe/computers/tags/assigned/` | `GET` | mTLS + JWS | Fetches list of tags currently assigned to the computer. |
| `/api/v1/safe/computers/tags/available/` | `GET` | mTLS + JWS | Fetches list of tags available for self-assignment. |
| `/api/v1/safe/computers/tags/` | `POST` | mTLS + JWS | Submits custom self-assigned tags to the server. |
| `/api/v1/safe/packages/` | `POST` | Packager Auth | Uploads a package file (.deb, .rpm, .exe) to a project. |
| `/api/v1/safe/packages/set/` | `POST` | Packager Auth | Registers and uploads a complete package set. |
| `/api/v1/safe/packages/repos/` | `POST` | Packager Auth | Instructs server to rebuild the repository indexes. |
