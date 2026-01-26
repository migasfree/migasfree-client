# migasfree-client Security Guidelines

Project-specific security guidelines for migasfree-client development.

## Security-Critical Components

### 1. mTLS Authentication (`mtls.py`)

The client uses mutual TLS for server authentication:

- **Certificate storage**: `/var/migasfree-client/mtls/<server>/`
- **Required files**: `cert.pem`, `key.pem`, `ca.pem`
- **Permissions**: Private key MUST be 600

**Review checklist for mTLS changes:**
- [ ] Private key permissions are enforced
- [ ] Certificate validation is enabled
- [ ] No hardcoded bypass options in production

### 2. Code Execution (`sync.py`)

The `_eval_code()` method executes server-provided code for:
- Property evaluation (dynamic attribute collection)
- Fault definition execution

**Review checklist for code execution:**
- [ ] Code comes from authenticated, verified server
- [ ] Execution is properly sandboxed/limited
- [ ] Errors don't expose system information

### 3. Subprocess Execution (`command.py`)

**Review checklist for subprocess calls:**
- [ ] Uses list arguments, not shell strings
- [ ] No `shell=True` without explicit justification
- [ ] User input is not interpolated into commands

### 4. Credential Management

Sensitive data locations:

| Location | Contains | Risk |
|----------|----------|------|
| `/etc/migasfree.conf` | Server URL, packager credentials | Unauthorized access |
| `/var/migasfree-client/mtls/` | TLS certificates and private keys | Identity theft |
| `[packager]` section | Upload credentials | Package tampering |

## Secure Coding Patterns

### Logging

```python
# WRONG: Logs credentials
logger.error(f'Auth failed: user={user}, password={password}')

# CORRECT: No sensitive data
logger.error('Authentication failed for user: %s', user)
```

### Subprocess Calls

```python
# WRONG: Shell injection risk
os.system(f'apt install {package_name}')

# CORRECT: Safe argument passing
subprocess.run(['apt', 'install', package_name], check=True)
```

### File Permissions

```python
# Set restrictive permissions on private keys
import os
import stat
os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
```

## Security Testing

```bash
# Run Bandit security scanner
pip install bandit
bandit -r migasfree_client/

# Check for known vulnerabilities in dependencies
pip install pip-audit
pip-audit
```
