# ssl-admin

An interactive X.509 Certificate Authority (CA) management tool for issuing, revoking, and distributing SSL/TLS certificates. Originally designed for OpenVPN PKI management, ssl-admin simplifies complex OpenSSL operations through a menu-driven interface.

## Features

- Create and manage a self-signed root CA
- Issue client and server certificates
- Revoke certificates and maintain a Certificate Revocation List (CRL)
- Renew/re-sign previously issued certificates
- Package certificates for end-user distribution (ZIP, OpenVPN inline config)
- Generate Diffie-Hellman parameters
- Available in both Perl (original) and Python 3 (rewrite with bug fixes) implementations
- Full batch/non-interactive CLI mode for scripting and automation

## Requirements

- **OpenSSL** in your `PATH`
- **Perl 5** (for the Perl implementation)
- **Python 3** (for the Python implementation)
- Root/sudo access (required at runtime unless running in development mode)

## Installation

### Perl Version

```sh
cd perl
./configure          # Detects OS and sets installation paths
make install         # Installs to system directories
```

The `configure` script sets OS-appropriate paths automatically:

| OS | Config dir | Binary dir |
|----|-----------|------------|
| FreeBSD / NetBSD / OpenBSD | `/usr/local/etc` | `/usr/local/bin` |
| macOS | `/Library` | `/usr/local/bin` |
| Linux | `/etc` | `/usr/bin` |

For local development without installing:

```sh
cd perl
./configure
make build-devel
./ssl-admin          # Runs from the current directory
```

### Python Version

No installation required. Run directly:

```sh
python/ssl-admin
```

Or make it executable and add to your `PATH`:

```sh
chmod +x python/ssl-admin
cp python/ssl-admin /usr/local/bin/ssl-admin
```

## Configuration

Before first use, copy and edit the configuration file:

```sh
cp python/ssl-admin.conf /etc/ssl-admin/ssl-admin.conf   # or your OS config dir
```

**`ssl-admin.conf`** — key/value pairs:

```
KEY_SIZE = 2048                       # RSA key size in bits (max 4096)
KEY_DAYS = 3650                       # Certificate validity in days
KEY_CN =                              # Default Common Name
KEY_CRL_LOC = URI:http://example.com/crl.pem   # CRL distribution point

# These must match your root CA certificate exactly
KEY_COUNTRY = US                      # 2-letter country code
KEY_PROVINCE = Minnesota              # State or province
KEY_CITY = Minneapolis                # City
KEY_ORG = Example Org                 # Organization name
KEY_EMAIL = admin@example.com         # Contact email
```

The `openssl.conf` file controls OpenSSL behavior and is read from the same directory as `ssl-admin.conf`. The bundled `openssl.conf` uses modern defaults (SHA-256, UTF-8 string handling, critical key usage extensions).

## First Run

When run against a new working directory, ssl-admin walks you through initialization:

1. Prompts to review/edit the configuration file
2. Creates the required directory structure
3. Asks whether to create a new self-signed CA or import an existing one

The working directory (`KEY_DIR` from your config) will be structured as:

```
KEY_DIR/
├── active/       # Issued certificates and keys
├── revoked/      # Revoked certificates (moved here on revocation)
├── csr/          # Archived certificate signing requests
├── packages/     # Distribution packages (.zip, .ovpn)
└── prog/         # Internal state (index, serial, CRL) — do not edit
```

## Usage

```sh
ssl-admin            # Launch interactive menu
ssl-admin crl        # Non-interactive: regenerate CRL and exit (legacy)
ssl-admin <command> [options]   # Batch mode
```

### Main Menu

| Option | Action |
|--------|--------|
| `1` | Update runtime options (key size, validity days, intermediate CA signing) |
| `2` | Create a new Certificate Signing Request (CSR) |
| `3` | Sign an existing CSR |
| `4` | One-step: create and sign a certificate |
| `5` | Revoke a certificate |
| `6` | Renew/re-sign a previously issued certificate |
| `7` | View the Certificate Revocation List |
| `8` | Search the certificate index |
| `i` | Generate an OpenVPN inline config (embeds cert, key, and CA) |
| `z` | Package certificate files into a ZIP for end-user distribution |
| `dh` | Generate Diffie-Hellman parameters |
| `CA` | Create a new self-signed CA certificate |
| `S` | One-step: create and sign a server certificate |
| `C` | Regenerate the Certificate Revocation List |
| `q` | Quit |

## Batch Mode

ssl-admin supports non-interactive operation for use in scripts, cron jobs, and automation pipelines. Pass a subcommand and options directly on the command line; the tool runs that one operation and exits.

```sh
ssl-admin <command> [options]
```

The CA must already be initialized (run interactively at least once) before using batch mode.

### Subcommands

| Subcommand | Description |
|-----------|-------------|
| `create-csr` | Create a new Certificate Signing Request |
| `sign` | Sign an existing CSR |
| `create-sign` | One-step: create and sign a certificate |
| `revoke` | Revoke a certificate |
| `renew` | Renew/re-sign a previously issued certificate |
| `view-crl` | Display the Certificate Revocation List |
| `index` | Show the index entry for a certificate |
| `inline` | Generate an OpenVPN inline config |
| `zip` | Package certificate files into a ZIP |
| `dh` | Generate Diffie-Hellman parameters |
| `new-ca` | Create a new self-signed CA certificate |
| `server` | One-step: create and sign a server certificate |
| `options` | Set runtime options (days, key size, intermediate CA) |
| `gen-crl` | Regenerate the Certificate Revocation List |
| `crl` | Alias for `gen-crl` (legacy compatibility) |

### Common Options

| Option | Applies to | Description |
|--------|-----------|-------------|
| `--cn NAME` | most commands | Certificate Common Name (required for cert operations) |
| `--password` | `create-csr`, `create-sign`, `server`, `new-ca` | Password-protect the private key |
| `--overwrite` | `create-csr`, `create-sign`, `server` | Overwrite an existing certificate (default: error) |
| `--archive-csr` / `--no-archive-csr` | `sign`, `create-sign`, `renew`, `server` | Control CSR archiving after signing |
| `--openvpn` / `--no-openvpn` | `zip` | Include OpenVPN client config in ZIP |
| `--days N` | `options`, `new-ca` | Certificate validity in days |
| `--size N` | `options`, `new-ca` | RSA key size in bits (max 4096) |
| `--intermediate` | `options` | Enable intermediate CA certificate signing |

Run `ssl-admin --help` or `ssl-admin <command> --help` for full option details.

### Examples

```sh
# Issue a client certificate
ssl-admin create-sign --cn jdoe

# Issue a server certificate
ssl-admin server --cn webserver.example.com

# Revoke a certificate and update the CRL
ssl-admin revoke --cn jdoe

# Renew a certificate
ssl-admin renew --cn jdoe

# Regenerate the CRL (e.g. from cron)
ssl-admin gen-crl

# Package a certificate for distribution
ssl-admin zip --cn jdoe --openvpn

# Overwrite an existing certificate
ssl-admin create-sign --cn jdoe --overwrite

# Create a CA cert with custom validity and key size
ssl-admin new-ca --cn "My Root CA" --days 3650 --size 4096
```

### Cron Example

```cron
# Regenerate CRL weekly
0 3 * * 0 /usr/local/bin/ssl-admin gen-crl
```

## Running Tests

The test suite uses `pytest` and validates both the Python implementation and behavioral parity between the Perl and Python versions.

```sh
cd tests
pip install pytest
pytest -v
```

Tests cover:

- Input validation (key size, common name format, serial number parsing)
- One-step certificate creation and signing
- Server certificate creation
- Certificate revocation and renewal
- CRL generation and display
- Certificate index search
- Parity between Perl and Python implementations

> **Note:** On macOS with LibreSSL, the test suite uses a thin OpenSSL wrapper (`tests/openssl_wrapper.py`) to handle `$ENV::VAR` expansion differences between OpenSSL and LibreSSL.

## License

BSD 3-Clause License. Copyright 2017–2023, Eric Crist. See [LICENSE](LICENSE) for details.
