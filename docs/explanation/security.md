# Security Model

This document explains the security architecture of migasfree-client and how it protects communications between clients and the server.

## Security Overview

migasfree-client implements a defense-in-depth security model with multiple layers of protection:

| Layer           | Technology | Purpose                  |
| --------------- | ---------- | ------------------------ |
| Transport       | TLS/HTTPS  | Encrypt network traffic  |
| Authentication  | mTLS       | Verify client identity   |
| Integrity       | JWS (RSA)  | Prevent message tampering|
| Confidentiality | JWE (RSA)  | Protect sensitive data   |

## Transport Security (TLS)

All communications use HTTPS when configured:

```ini
[client]
Protocol = https
```

### Certificate Validation

By default, the client validates server certificates:

- Certificate must be signed by a trusted CA
- Certificate hostname must match server
- Certificate must not be expired

### Self-Signed Certificates

For self-signed server certificates:

```bash
# Install your CA certificate (Linux)
sudo cp your-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

## Mutual TLS (mTLS)

mTLS provides strong client authentication using X.509 certificates.

### How It Works

```text
┌────────────┐                       ┌────────────┐
│   Client   │                       │   Server   │
│            │───── Hello ──────────►│            │
│            │◄──── Server Cert ─────│            │
│            │───── Client Cert ────►│            │  ◄── Server verifies
│            │◄──── Encrypted ───────│            │      client identity
│            │───── Data ───────────►│            │
└────────────┘                       └────────────┘
```

### Certificate Files

```text
/var/migasfree-client/mtls/server.example.com/
├── cert.pem    # Client certificate
├── key.pem     # Client private key (mode 600)
└── ca.pem      # CA certificate
```

### Importing Certificates

Administrators provide certificates as a tar archive:

```bash
sudo migasfree import-mtls /path/to/certs.tar
```

The archive can contain:

- PEM files: `cert.pem`, `key.pem`, `ca.pem`
- PKCS#12: `.p12` or `.pfx` file

### Key Security

Private keys are protected:

```bash
# Correct permissions
$ ls -la /var/migasfree-client/mtls/*/key.pem
-rw------- 1 root root 1704 Jan 15 10:30 key.pem
```

The client enforces 0600 permissions on private keys.

## Message Signing (JWS)

All API requests are signed using JSON Web Signature (JWS).

### Purpose

- **Integrity**: Detect message tampering
- **Authentication**: Verify message origin
- **Non-repudiation**: Prove who sent the message

### Key Pairs

```text
/var/migasfree-client/keys/server.example.com/
├── server.pub      # Server's public key (verifies server responses)
└── MyProject.pri   # Project's private key (signs client requests)
```

### Flow

**Request (Client → Server):**

```text
1. Client creates JSON payload
2. Signs with project private key
3. Sends signed JWS token to server
4. Server verifies signature with project public key
```

**Response (Server → Client):**

```text
1. Server creates JSON response
2. Signs with server private key
3. Sends signed JWS token to client
4. Client verifies signature with server public key
```

## Message Encryption (JWE)

Sensitive data is encrypted using JSON Web Encryption (JWE).

### When Used

- User passwords during registration
- Sensitive attribute values
- Certificate data

### Algorithms

| Purpose            | Algorithm     |
| ------------------ | ------------- |
| Key Exchange       | RSA-OAEP      |
| Content Encryption | A256CBC-HS512 |

## Code Execution Security

The server can send code for clients to execute (for attribute evaluation and fault detection). This is a powerful feature with security implications.

### Trust Model

> ⚠️ **Important**: Clients execute code from the server with the privileges of the migasfree process (typically root).

This means:

- Only trusted servers should be configured
- Server security is critical
- Network security prevents MITM attacks

### Input Sanitization

The client sanitizes certain inputs:

```python
# Path traversal prevention
def sanitize_path(path):
    """Prevent directory traversal attacks"""
    return os.path.abspath(path).startswith(allowed_base)
```

## Best Practices

### For Administrators

1. **Always use HTTPS** in production:

   ```ini
   Protocol = https
   ```

2. **Enable mTLS** for strong client authentication

3. **Secure the server** - it controls all clients

4. **Monitor certificates** - renew before expiration

5. **Use strong passwords** for the packager account

### For Packagers

1. **Protect packager credentials**:
   - Use environment variables instead of config file
   - Never commit credentials to version control

2. **Sign packages** before upload (if your PMS supports it)

### For Security Auditors

Key areas to review:

| Area        | Files             | Concern                    |
| ----------- | ----------------- | -------------------------- |
| mTLS        | `mtls.py`         | Certificate handling       |
| Crypto      | `secure.py`       | Algorithm selection        |
| HTTP        | `url_request.py`  | Certificate validation     |
| Code exec   | `sync.py`         | `_eval_code` function      |
| Permissions | Various           | File permission handling   |

## Known Considerations

### CA Certificate Bootstrap

During initial registration, the CA certificate is downloaded without verification (chicken-and-egg problem):

```python
# In mtls.py - intentional for bootstrapping
response = requests.get(url, verify=False)
```

**Mitigation**: Use the `import-mtls` command to import trusted certificates instead.

### Privilege Level

migasfree-client typically runs as root to:

- Install/remove packages
- Modify system configuration
- Configure devices

This is necessary for its function but increases the impact of any vulnerability.

## Incident Response

If you suspect a security issue:

1. **Disconnect** affected computers from network
2. **Revoke** mTLS certificates on the server
3. **Check** server logs for unauthorized access
4. **Re-register** computers after investigation
5. **Report** vulnerabilities to maintainers

## See Also

- [Architecture Overview](architecture.md)
- [Configuration Reference](../reference/configuration.md)
- [Troubleshooting mTLS Issues](../how-to/troubleshooting.md#mtls-issues)
