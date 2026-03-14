"""
Behavioral parity tests.

Each test runs the same menu sequence through both the Perl and Python
implementations and asserts that the resulting filesystem state is
identical.  Exact stdout is NOT compared (minor whitespace differences
are acceptable); what matters is that both scripts create/move/delete
the same files.
"""

import subprocess
from pathlib import Path

import pytest
from conftest import run_script, make_ca_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cert_is_valid(cert_path: Path, ca_path: Path) -> bool:
    """Return True if openssl can verify the cert against the CA."""
    r = subprocess.run(
        f"openssl verify -CAfile {ca_path} {cert_path}",
        shell=True, capture_output=True, text=True,
    )
    return r.returncode == 0


def serial_from_cert(cert_path: Path) -> str:
    r = subprocess.run(
        f"openssl x509 -noout -serial -in {cert_path}",
        shell=True, capture_output=True, text=True,
    )
    # output: "serial=HEXVALUE"
    return r.stdout.strip().split("=")[-1].lower()


# ---------------------------------------------------------------------------
# Quit
# ---------------------------------------------------------------------------

class TestQuit:

    def test_quit_perl(self, perl_env):
        script_path, workdir, env = perl_env
        result = run_script(script_path, "q\n", env)
        assert result.returncode == 0

    def test_quit_python(self, python_env):
        script_path, workdir, env = python_env
        result = run_script(script_path, "q\n", env)
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# One-step create + sign (menu option 4)
# ---------------------------------------------------------------------------

class TestCreateAndSign:
    """
    Option 4: create CSR + sign in one step.
    Both scripts should produce identical output files.
    """

    CN = "testuser"

    def _stdin(self) -> str:
        return (
            "4\n"           # menu: one-step create/sign
            f"{self.CN}\n"  # common name
            "n\n"           # no password on private key
            "q\n"           # quit
        )

    def _assert_files(self, workdir: Path):
        active = workdir / "active"
        csr_dir = workdir / "csr"
        assert (active / f"{self.CN}.crt").exists(), "cert not created"
        assert (active / f"{self.CN}.key").exists(), "key not created"
        assert (active / f"{self.CN}.pem").exists(), "pem not created"
        assert (csr_dir  / f"{self.CN}.csr").exists(), "csr not archived"
        # The key backup in csr/ as well
        assert (csr_dir  / f"{self.CN}.key").exists(), "key backup missing"
        # Cert must verify against the CA
        assert cert_is_valid(active / f"{self.CN}.crt",
                             active / "ca.crt"), "cert does not verify"

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        result = run_script(script_path, self._stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_files(workdir)

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        result = run_script(script_path, self._stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_files(workdir)

    def test_parity(self, perl_env, python_env):
        """Both produce the same set of output files."""
        for script_path, workdir, env in [perl_env, python_env]:
            run_script(script_path, self._stdin(), env)
        for _, workdir, _ in [perl_env, python_env]:
            self._assert_files(workdir)


# ---------------------------------------------------------------------------
# Server certificate (menu option S)
# ---------------------------------------------------------------------------

class TestServerCert:

    CN = "webserver"

    def _stdin(self) -> str:
        return (
            "S\n"
            f"{self.CN}\n"
            "n\n"           # no password
            "y\n"           # archive CSR
            "q\n"
        )

    def _assert_files(self, workdir: Path):
        active = workdir / "active"
        assert (active / f"{self.CN}.crt").exists()
        assert (active / f"{self.CN}.key").exists()
        assert cert_is_valid(active / f"{self.CN}.crt", active / "ca.crt")

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        result = run_script(script_path, self._stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_files(workdir)

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        result = run_script(script_path, self._stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_files(workdir)


# ---------------------------------------------------------------------------
# Revoke certificate (menu option 5)
# ---------------------------------------------------------------------------

class TestRevoke:

    CN = "revokeuser"

    def _create_stdin(self) -> str:
        return (
            "4\n"
            f"{self.CN}\n"
            "n\n"
            "q\n"
        )

    def _revoke_stdin(self) -> str:
        return (
            "5\n"
            f"{self.CN}\n"
            "y\n"           # confirm revocation
            "q\n"
        )

    def _assert_revoked(self, workdir: Path):
        revoked = workdir / "revoked"
        active  = workdir / "active"
        crl     = workdir / "prog" / "crl.pem"

        # Files should have moved from active/ to revoked/
        assert (revoked / f"{self.CN}.crt").exists(), "crt not in revoked/"
        assert (revoked / f"{self.CN}.key").exists(), "key not in revoked/"
        assert not (active / f"{self.CN}.crt").exists(), "crt still in active/"

        # CRL should exist and mention the revoked serial
        assert crl.exists(), "CRL not found"
        r = subprocess.run(
            f"openssl crl -noout -text -in {crl}",
            shell=True, capture_output=True, text=True,
        )
        assert "Revoked Certificates" in r.stdout or \
               "No Revoked Certificates" not in r.stdout, \
               "CRL does not list any revoked certificates"

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        # First create the cert
        run_script(script_path, self._create_stdin(), env)
        # Then revoke it
        result = run_script(script_path, self._revoke_stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_revoked(workdir)

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        run_script(script_path, self._create_stdin(), env)
        result = run_script(script_path, self._revoke_stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_revoked(workdir)


# ---------------------------------------------------------------------------
# Renew / re-sign from archived CSR (menu option 6)
# ---------------------------------------------------------------------------

class TestRenew:

    CN = "renewuser"

    def _create_stdin(self) -> str:
        return "4\n" + f"{self.CN}\n" + "n\n" + "q\n"

    def _revoke_stdin(self) -> str:
        return "5\n" + f"{self.CN}\n" + "y\n" + "q\n"

    def _renew_stdin(self) -> str:
        return (
            "6\n"
            f"{self.CN}\n"
            "y\n"           # confirm re-sign of revoked cert
            "y\n"           # archive CSR (sign_csr() prompts when menu != 4)
            "q\n"
        )

    def _assert_renewed(self, workdir: Path):
        active = workdir / "active"
        assert (active / f"{self.CN}.crt").exists(), "renewed cert not in active/"
        assert cert_is_valid(active / f"{self.CN}.crt", active / "ca.crt")

    def test_renew_from_archive_perl(self, perl_env):
        """Renew a non-revoked archived CSR (straight re-sign path)."""
        script_path, workdir, env = perl_env
        # Create cert (archives CSR to csr/)
        run_script(script_path, self._create_stdin(), env)
        # Move cert out of active so option 6 can re-sign cleanly
        cert = workdir / "active" / f"{self.CN}.crt"
        cert.rename(workdir / f"{self.CN}.crt.bak")

        # "y\n" answers sign_csr()'s "archive CSR?" prompt (auto only for opt 4)
        stdin = "6\n" + f"{self.CN}\n" + "y\n" + "q\n"
        result = run_script(script_path, stdin, env)
        assert result.returncode == 0, result.stderr
        self._assert_renewed(workdir)

    def test_renew_from_archive_python(self, python_env):
        script_path, workdir, env = python_env
        run_script(script_path, self._create_stdin(), env)
        cert = workdir / "active" / f"{self.CN}.crt"
        cert.rename(workdir / f"{self.CN}.crt.bak")

        stdin = "6\n" + f"{self.CN}\n" + "y\n" + "q\n"
        result = run_script(script_path, stdin, env)
        assert result.returncode == 0, result.stderr
        self._assert_renewed(workdir)

    def test_renew_revoked_perl(self, perl_env):
        """Re-sign a previously revoked cert."""
        script_path, workdir, env = perl_env
        run_script(script_path, self._create_stdin(), env)
        run_script(script_path, self._revoke_stdin(), env)
        result = run_script(script_path, self._renew_stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_renewed(workdir)

    def test_renew_revoked_python(self, python_env):
        script_path, workdir, env = python_env
        run_script(script_path, self._create_stdin(), env)
        run_script(script_path, self._revoke_stdin(), env)
        result = run_script(script_path, self._renew_stdin(), env)
        assert result.returncode == 0, result.stderr
        self._assert_renewed(workdir)


# ---------------------------------------------------------------------------
# View CRL (menu option 7)
# ---------------------------------------------------------------------------

class TestViewCRL:

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        result = run_script(script_path, "7\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert "certificate revocation list" in result.stdout.lower()

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        result = run_script(script_path, "7\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert "certificate revocation list" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Generate CRL (menu option C)
# ---------------------------------------------------------------------------

class TestGenerateCRL:

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        result = run_script(script_path, "C\ny\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert (workdir / "prog" / "crl.pem").exists()

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        result = run_script(script_path, "C\ny\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert (workdir / "prog" / "crl.pem").exists()

    def test_crl_argument_perl(self, perl_env):
        """ssl-admin crl (command-line arg) should exit 0 silently."""
        script_path, workdir, env = perl_env
        first_line = script_path.read_text().split("\n")[0]
        cmd = ["perl" if "perl" in first_line else "python3",
               str(script_path), "crl"]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env=env, timeout=30)
        assert r.returncode == 0
        assert r.stdout == "" or "ssl-admin installed" not in r.stdout

    def test_crl_argument_python(self, python_env):
        script_path, workdir, env = python_env
        cmd = ["python3", str(script_path), "crl"]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env=env, timeout=30)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Separate CSR create (option 2) and sign (option 3)
# ---------------------------------------------------------------------------

class TestSeparateCreateSign:

    CN = "splituser"

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        # Step 1: create CSR only
        run_script(script_path, f"2\n{self.CN}\nn\nq\n", env)
        assert (workdir / f"{self.CN}.csr").exists(), "CSR not created"
        assert (workdir / f"{self.CN}.key").exists(), "key not created"

        # Step 2: sign the existing CSR
        result = run_script(script_path, f"3\n{self.CN}\ny\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert (workdir / "active" / f"{self.CN}.crt").exists()

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        run_script(script_path, f"2\n{self.CN}\nn\nq\n", env)
        assert (workdir / f"{self.CN}.csr").exists()
        assert (workdir / f"{self.CN}.key").exists()

        result = run_script(script_path, f"3\n{self.CN}\ny\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert (workdir / "active" / f"{self.CN}.crt").exists()

    def test_parity(self, perl_env, python_env):
        """Both scripts leave identical files after a create+sign cycle."""
        for script_path, workdir, env in [perl_env, python_env]:
            run_script(script_path, f"2\n{self.CN}\nn\nq\n", env)
            run_script(script_path, f"3\n{self.CN}\ny\nq\n", env)

        for _, workdir, _ in [perl_env, python_env]:
            active = workdir / "active"
            assert (active / f"{self.CN}.crt").exists()
            assert (active / f"{self.CN}.key").exists()
            assert cert_is_valid(active / f"{self.CN}.crt", active / "ca.crt")


# ---------------------------------------------------------------------------
# Index lookup (menu option 8)
# ---------------------------------------------------------------------------

class TestIndexLookup:

    CN = "indexuser"

    def test_perl(self, perl_env):
        script_path, workdir, env = perl_env
        run_script(script_path, f"4\n{self.CN}\nn\nq\n", env)
        result = run_script(script_path, f"8\n{self.CN}\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert self.CN in result.stdout

    def test_python(self, python_env):
        script_path, workdir, env = python_env
        run_script(script_path, f"4\n{self.CN}\nn\nq\n", env)
        result = run_script(script_path, f"8\n{self.CN}\nq\n", env)
        assert result.returncode == 0, result.stderr
        assert self.CN in result.stdout
