#!/usr/bin/env python3
"""
Thin wrapper around the system openssl binary that expands $ENV::VAR
references in config files before invocation.

LibreSSL 3.3 (macOS default) does not support $ENV::VAR substitution
in openssl.conf files.  This wrapper intercepts the -config argument,
expands all $ENV::VAR tokens using the current process environment,
writes a temp file, and calls the real openssl with the patched config.

Installed on PATH ahead of the system openssl only during tests.
"""

import os
import re
import sys
import tempfile
import subprocess
from pathlib import Path

REAL_OPENSSL = "/usr/bin/openssl"


def expand_env_refs(content: str) -> str:
    def replace(m):
        return os.environ.get(m.group(1), "")
    return re.sub(r'\$ENV::(\w+)', replace, content)


def main():
    args = list(sys.argv[1:])
    tmp_path = None
    try:
        for i, arg in enumerate(args):
            if arg == "-config" and i + 1 < len(args):
                config_file = Path(args[i + 1])
                if config_file.exists():
                    content = config_file.read_text()
                    expanded = expand_env_refs(content)
                    if expanded != content:
                        fd, tmp_path = tempfile.mkstemp(suffix=".conf")
                        os.write(fd, expanded.encode())
                        os.close(fd)
                        args[i + 1] = tmp_path
                break
        result = subprocess.run([REAL_OPENSSL] + args)
        sys.exit(result.returncode)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    main()
