# ADR 001: Mutual TLS (mTLS) for Client Authentication

## Status

Accepted

## Context

The migasfree-server needs a secure way to verify the identity of thousands of clients connecting over the internet. Standard username/password authentication is prone to credential leak and replay attacks. We need a more robust, hardware-linked authentication mechanism.

## Decision

We incorporate Mutual TLS (mTLS) as the primary authentication layer.

1. **Client Identity**: Every registered computer will have a unique X.509 certificate.
2. **CA Management**: The migasfree server acts as its own Certificate Authority (CA) or integrates with an existing PKI.
3. **Automated Provisioning**: The client automatically downloads its mTLS certificates during the initial registration phase (mediated by JWS signing).
4. **Transport**: All subsequent API calls use these certificates for mutual identification.

## Consequences

### Positive

- **Strong Identity**: Servers can trust that a request comes from a specific, registered hardware node.
- **Revocation**: Compromised clients can be revoked at the server by invalidating their certificates.
- **Encryption**: Inherits all benefits of TLS 1.2+ encryption for data in transit.

### Negative

- **Management Overhead**: Requires PKI infrastructure on the server side.
- **Complexity**: Client must handle certificate rotation and storage securely.
- **Bootstrap Risk**: The initial certificate fetch must be secured (currently done via JWS and admin credentials).
