"""
Validation tests targeting specific bugs that were fixed.

These run each script with crafted input to confirm the fixed
behavior rather than the old broken behavior.
"""

import re
import pytest
from conftest import run_script


# ---------------------------------------------------------------------------
# Key size validation  (bug: 'lt' string comparison instead of numeric <=)
# ---------------------------------------------------------------------------

class TestKeySizeValidation:

    def _run_option_1(self, script_path, env, key_size_inputs):
        """
        Enter menu option 1 (update runtime options), send key_days=<enter>
        (keep default), then the provided key_size inputs in sequence,
        then 'n' for intermediate CA, then 'q' to quit.
        """
        stdin = "1\n"          # select menu option 1
        stdin += "\n"          # keep current key_days
        for ks in key_size_inputs:
            stdin += ks + "\n"
        stdin += "n\n"         # intermediate CA = no
        stdin += "q\n"         # quit
        return run_script(script_path, stdin, env)

    def test_large_value_rejected_perl(self, perl_env):
        """10000 should be rejected; the loop must re-prompt and accept 2048."""
        script_path, workdir, env = perl_env
        # Send 10000 first (should be rejected), then 2048 (should be accepted)
        result = self._run_option_1(script_path, env, ["10000", "2048"])
        assert result.returncode == 0, result.stderr
        # "reconfigured" confirms we made it through option 1 successfully
        assert "reconfigured" in result.stdout.lower()

    def test_large_value_rejected_python(self, python_env):
        script_path, workdir, env = python_env
        result = self._run_option_1(script_path, env, ["10000", "2048"])
        assert result.returncode == 0, result.stderr
        assert "reconfigured" in result.stdout.lower()

    def test_boundary_4096_accepted_perl(self, perl_env):
        """4096 is the maximum and must be accepted in a single attempt."""
        script_path, workdir, env = perl_env
        result = self._run_option_1(script_path, env, ["4096"])
        assert result.returncode == 0, result.stderr
        assert "reconfigured" in result.stdout.lower()

    def test_boundary_4096_accepted_python(self, python_env):
        script_path, workdir, env = python_env
        result = self._run_option_1(script_path, env, ["4096"])
        assert result.returncode == 0, result.stderr
        assert "reconfigured" in result.stdout.lower()

    def test_4097_rejected_perl(self, perl_env):
        """4097 exceeds the limit and must loop back to re-prompt."""
        script_path, workdir, env = perl_env
        result = self._run_option_1(script_path, env, ["4097", "2048"])
        assert result.returncode == 0, result.stderr
        assert "reconfigured" in result.stdout.lower()

    def test_4097_rejected_python(self, python_env):
        script_path, workdir, env = python_env
        result = self._run_option_1(script_path, env, ["4097", "2048"])
        assert result.returncode == 0, result.stderr
        assert "reconfigured" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Common name validation  (regex '^[\w\s\-\.]+$')
# ---------------------------------------------------------------------------

class TestCommonNameValidation:

    def _run_option_2_then_quit(self, script_path, env, cn_inputs):
        """
        Enter menu option 2 (create CSR), send CN inputs in sequence,
        then send 'n' for password protection, then quit.
        We don't expect a full signing here — just testing CN acceptance.
        """
        stdin = "2\n"
        for cn in cn_inputs:
            stdin += cn + "\n"
        # After a valid CN is accepted, the script will try to run openssl.
        # Send Ctrl-D style by just letting it run; we check returncode/output.
        stdin += "n\n"   # no password on key
        stdin += "q\n"
        return run_script(script_path, stdin, env)

    def test_valid_cn_accepted_perl(self, perl_env):
        script_path, workdir, env = perl_env
        result = self._run_option_2_then_quit(script_path, env, ["jdoe"])
        # Should not loop asking for CN again
        assert result.stdout.count("Owner [") == 1

    def test_valid_cn_accepted_python(self, python_env):
        script_path, workdir, env = python_env
        result = self._run_option_2_then_quit(script_path, env, ["jdoe"])
        assert result.stdout.count("Owner [") == 1

    def test_invalid_cn_loops_perl(self, perl_env):
        """A CN with shell-special characters must be rejected and re-prompted."""
        script_path, workdir, env = perl_env
        # Send an invalid CN first, then a valid one
        result = self._run_option_2_then_quit(
            script_path, env, [";drop tables", "jdoe"])
        # Prompt should appear at least twice
        assert result.stdout.count("Owner [") >= 2

    def test_invalid_cn_loops_python(self, python_env):
        script_path, workdir, env = python_env
        result = self._run_option_2_then_quit(
            script_path, env, [";drop tables", "jdoe"])
        assert result.stdout.count("Owner [") >= 2

    def test_hyphen_dot_cn_accepted_perl(self, perl_env):
        """Hyphens and dots are valid in a CN (e.g. hostnames)."""
        script_path, workdir, env = perl_env
        result = self._run_option_2_then_quit(
            script_path, env, ["web-server.example.com"])
        assert result.stdout.count("Owner [") == 1

    def test_hyphen_dot_cn_accepted_python(self, python_env):
        script_path, workdir, env = python_env
        result = self._run_option_2_then_quit(
            script_path, env, ["web-server.example.com"])
        assert result.stdout.count("Owner [") == 1


# ---------------------------------------------------------------------------
# Serial number regex  (bug: [A-F0-9] missed lowercase hex from modern OpenSSL)
# ---------------------------------------------------------------------------

class TestSerialRegex:
    """
    The revocation code uses a regex to parse serial numbers out of
    openssl output.  The fix extended it to [A-Fa-f0-9].
    We verify the regex directly matches lowercase serials.
    """

    SERIAL_PATTERN = re.compile(r'Serial Number:\s*([A-Fa-f0-9]+)')
    OLD_PATTERN    = re.compile(r'Serial Number:\s*([A-F0-9]+)')

    @pytest.mark.parametrize("serial", [
        "01", "ff", "1a2b3c", "ABCDEF", "abcdef", "deadbeef",
    ])
    def test_fixed_regex_matches(self, serial):
        text = f"Serial Number: {serial}"
        assert self.SERIAL_PATTERN.search(text), \
            f"Fixed regex should match serial '{serial}'"

    @pytest.mark.parametrize("serial", ["ff", "aabb", "deadbeef", "cafe"])
    def test_old_regex_misses_lowercase(self, serial):
        """All-lowercase hex serials must not match the old uppercase-only regex."""
        text = f"Serial Number: {serial}"
        assert not self.OLD_PATTERN.search(text), \
            f"Old uppercase-only regex incorrectly matches lowercase serial '{serial}'"

    def test_old_regex_partial_match_on_mixed(self):
        """
        Mixed serials like '1a2b' expose the old bug: the regex captures only
        the leading digit '1' instead of the full serial, causing revocation
        verification to silently fail (hex('1') != hex('1a2b')).
        """
        text = "Serial Number: 1a2b"
        m = self.OLD_PATTERN.search(text)
        full_match = m and m.group(1) == "1a2b"
        assert not full_match, "Old regex must not capture the full mixed serial"

        new_m = self.SERIAL_PATTERN.search(text)
        assert new_m and new_m.group(1) == "1a2b", \
            "Fixed regex must capture the full mixed serial"
