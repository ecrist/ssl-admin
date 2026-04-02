"""
Shared fixtures for ssl-admin test suite.

Both Perl and Python scripts require placeholder substitution
(~~~ETCDIR~~~, ~~~BUILD~~~, ~~~VERSION~~~) before they can run.
Each fixture builds a self-contained working environment in a temp dir.

LibreSSL 3.3 (macOS) does not support $ENV::VAR expansion in openssl.conf.
A thin openssl wrapper (tests/bin/openssl → openssl_wrapper.py) is prepended
to PATH in every test environment; it expands $ENV::VAR tokens before
invoking the real binary, so both scripts work transparently.
"""

import datetime
import os
import subprocess
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
WRAPPER_BIN = REPO_ROOT / "tests" / "bin"   # contains our openssl wrapper

# Environment used to build the test CA and sign certs.
# Must match policy_match in openssl.conf (country, state, org must equal CA).
TEST_ENV_VARS = {
    "KEY_SIZE":     "2048",
    "KEY_DAYS":     "3650",
    "KEY_CN":       "",
    "KEY_CRL_LOC":  "URI:http://localhost/crl.pem",
    "KEY_COUNTRY":  "US",
    "KEY_PROVINCE": "TestState",
    "KEY_CITY":     "TestCity",
    "KEY_ORG":      "TestOrg",
    "KEY_EMAIL":    "test@test.com",
}

PERL_CONF_TEMPLATE = (
    '$ENV{\'KEY_SIZE\'}     = "2048";\n'
    '$ENV{\'KEY_DAYS\'}     = "3650";\n'
    '$ENV{\'KEY_CN\'}       = "";\n'
    '$ENV{\'KEY_CRL_LOC\'}  = "URI:http://localhost/crl.pem";\n'
    '$ENV{\'KEY_COUNTRY\'}  = "US";\n'
    '$ENV{\'KEY_PROVINCE\'} = "TestState";\n'
    '$ENV{\'KEY_CITY\'}     = "TestCity";\n'
    '$ENV{\'KEY_ORG\'}      = "TestOrg";\n'
    '$ENV{\'KEY_EMAIL\'}    = "test\@test.com";\n'
)

PYTHON_CONF_TEMPLATE = """\
KEY_SIZE     = 2048
KEY_DAYS     = 3650
KEY_CN       =
KEY_CRL_LOC  = URI:http://localhost/crl.pem
KEY_COUNTRY  = US
KEY_PROVINCE = TestState
KEY_CITY     = TestCity
KEY_ORG      = TestOrg
KEY_EMAIL    = test@test.com
"""


def test_env(extra: dict = None) -> dict:
    """Return an env dict with the wrapper bin prepended to PATH."""
    env = os.environ.copy()
    env.update(TEST_ENV_VARS)
    env["PATH"] = f"{WRAPPER_BIN}:{env.get('PATH', '/usr/bin:/bin')}"
    if extra:
        env.update(extra)
    return env


def substitute(content: str, etcdir: str) -> str:
    return (content
            .replace("~~~ETCDIR~~~", etcdir)
            .replace("~~~BUILD~~~", "devel")
            .replace("~~~VERSION~~~", "test"))


def make_ca_env(etcdir: Path) -> Path:
    """
    Build a fully-initialized ssl-admin working directory under etcdir/ssl-admin/
    using real OpenSSL calls via the wrapper, bypassing the install wizard.
    """
    workdir = etcdir / "ssl-admin"
    for d in ("active", "revoked", "csr", "packages", "prog"):
        (workdir / d).mkdir(parents=True, mode=0o750, exist_ok=True)

    shutil.copy2(str(REPO_ROOT / "python" / "openssl.conf"),
                 str(workdir / "openssl.conf"))

    env = test_env({"KEY_DIR": str(workdir)})

    def ossl(cmd: str):
        r = subprocess.run(cmd, shell=True, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"OpenSSL failed:\n{r.stderr}")
        return r

    # CA key + self-signed cert
    ossl(f"openssl genrsa -out {workdir}/active/ca.key 2048")
    ossl(f"openssl req -new -x509 -extensions v3_ca "
         f"-key {workdir}/active/ca.key -out {workdir}/active/ca.crt "
         f"-days 3650 -config {workdir}/openssl.conf -batch")

    shutil.copy2(str(workdir / "active" / "ca.crt"),
                 str(workdir / "packages" / "ca.crt"))

    # Prog files
    (workdir / "prog" / "index.txt").touch()
    (workdir / "prog" / "index.txt.attr").write_text("unique_subject = no\n")
    (workdir / "prog" / "serial").write_text("01\n")
    (workdir / "prog" / "install").write_text(
        datetime.datetime.now().strftime("%c") + "\n")

    # Initial CRL
    ossl(f"cd {workdir}/active && openssl ca -gencrl -batch "
         f"-config {workdir}/openssl.conf -out {workdir}/prog/crl.pem")

    return workdir


@pytest.fixture()
def perl_env(tmp_path):
    """
    Returns (script_path, workdir, env) for a Perl script test run.
    """
    base = tmp_path / "perl"
    base.mkdir()
    etcdir = base / "etc"
    etcdir.mkdir()
    workdir = make_ca_env(etcdir)

    (workdir / "ssl-admin.conf").write_text(PERL_CONF_TEMPLATE)

    script_src = (REPO_ROOT / "perl" / "ssl-admin").read_text()
    script_path = base / "ssl-admin"
    script_path.write_text(substitute(script_src, str(etcdir)))
    script_path.chmod(0o755)

    return script_path, workdir, test_env({"KEY_DIR": str(workdir)})


@pytest.fixture()
def python_env(tmp_path):
    """
    Returns (script_path, workdir, env) for a Python script test run.
    """
    base = tmp_path / "python"
    base.mkdir()
    etcdir = base / "etc"
    etcdir.mkdir()
    workdir = make_ca_env(etcdir)

    (workdir / "ssl-admin.conf").write_text(PYTHON_CONF_TEMPLATE)

    script_src = (REPO_ROOT / "python" / "ssl-admin").read_text()
    script_path = base / "ssl-admin"
    script_path.write_text(substitute(script_src, str(etcdir)))
    script_path.chmod(0o755)

    return script_path, workdir, test_env()


def run_script(script_path: Path, stdin_input: str, env: dict,
               timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a script (Perl or Python) with piped stdin, detected via shebang."""
    shebang = script_path.read_text().split("\n")[0]
    interpreter = "perl" if "perl" in shebang else "python3"
    return subprocess.run(
        [interpreter, str(script_path)],
        input=stdin_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
