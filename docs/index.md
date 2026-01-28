# migasfree-client Documentation

Welcome to the migasfree-client documentation. This guide will help you install, configure, and use the migasfree systems management client.

## Quick Navigation

| Section                               | Description                    |
| ------------------------------------- | ------------------------------ |
| [Getting Started](getting-started.md) | Installation and first steps   |
| [Tutorials](tutorials/)               | Step-by-step learning guides   |
| [How-To Guides](how-to/)              | Task-oriented instructions     |
| [Reference](reference/)               | Technical specifications       |
| [Explanation](explanation/)           | Background and concepts        |

## What is migasfree-client?

migasfree-client is a systems management client that synchronizes computers with a [migasfree server](https://github.com/migasfree/migasfree). It enables centralized management of:

- **Software deployment** - Install, update, and remove packages
- **Hardware inventory** - Automatic hardware information capture
- **Software inventory** - Track installed packages
- **Device management** - Configure printers and peripherals
- **Fault monitoring** - Centralized error and fault reporting

## Supported Platforms

| Platform      | Package Manager | Status           |
| ------------- | --------------- | ---------------- |
| Debian/Ubuntu | apt             | ✅ Full support  |
| Fedora        | dnf             | ✅ Full support  |
| RHEL/CentOS   | yum             | ✅ Full support  |
| openSUSE      | zypper          | ✅ Full support  |
| Arch Linux    | pacman          | ✅ Full support  |
| Alpine Linux  | apk             | ✅ Full support  |
| Windows 10+   | wpt             | ✅ Full support  |

## Quick Start

```bash
# Install (example for Debian/Ubuntu)
sudo apt install migasfree-client

# Configure
sudo nano /etc/migasfree.conf
# Set: Server = your-migasfree-server.example.com

# Register the computer
sudo migasfree register -u admin

# Synchronize
sudo migasfree sync
```

For detailed instructions, see [Getting Started](getting-started.md).

## Documentation Structure

This documentation follows the [Diátaxis framework](https://diataxis.fr/):

### 📚 [Tutorials](tutorials/)

*Learning-oriented* - Step-by-step guides for beginners

- [Your First Synchronization](tutorials/first-sync.md)
- [Setting Up mTLS Security](tutorials/setup-mtls.md)

### 🔧 [How-To Guides](how-to/)

*Task-oriented* - Solve specific problems

- [Troubleshooting Common Issues](how-to/troubleshooting.md)
- [Configure Proxy Settings](how-to/proxy-setup.md)
- [Automate Synchronization](how-to/automation.md)

### 📖 [Reference](reference/)

*Information-oriented* - Technical specifications

- [Command-Line Interface](reference/cli.md)
- [Configuration Options](reference/configuration.md)
- [Environment Variables](reference/environment-variables.md)

### 💡 [Explanation](explanation/)

*Understanding-oriented* - Background concepts

- [Architecture Overview](explanation/architecture.md)
- [Security Model](explanation/security.md)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/migasfree/migasfree-client/issues)
- **Documentation**: [Fun with migasfree](https://fun-with-migasfree.readthedocs.org/) (Spanish)
- **Source Code**: [GitHub Repository](https://github.com/migasfree/migasfree-client)

## Contributing

We welcome contributions! Please see:

- [Development Guidelines](../CONTRIBUTING.md)
- [Documentation Guidelines](contributing_docs.md)

## License

migasfree-client is free software released under the [GNU GPL v3](../LICENSE).
