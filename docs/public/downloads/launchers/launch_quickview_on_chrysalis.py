#!/usr/bin/env python3
"""Launch QuickView on Chrysalis and open its UI on this Mac."""

import argparse
import re
import shlex
import socket
import subprocess
import sys
import tempfile

REMOTE_COMMAND = (
    "module load miniforge3/25.3.1"
    ' && eval "$(conda shell.bash hook)"'
    " && conda activate /lcrc/group/e3sm/share/quickview"
    " && printf '%s\\n' 'Starting QuickView, please wait. "
    "The UI will show up in a browser window.'"
    " && exec quickview --port 0 --timeout 0"
)


def add_tunnel(host, control_socket, remote_port):
    for _ in range(5):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            local_port = sock.getsockname()[1]
        result = subprocess.run(
            ["ssh", "-S", control_socket, "-O", "forward", "-L",
             f"127.0.0.1:{local_port}:localhost:{remote_port}", host],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return local_port
    raise RuntimeError(f"Could not create tunnel:\n{result.stderr.strip()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="username@chrysalis.lcrc.anl.gov or SSH alias")
    parser.add_argument("--command", default=REMOTE_COMMAND,
                        help="Override the remote setup and launch command")
    args = parser.parse_args()
    if args.host.startswith("-"):
        parser.error("The SSH destination cannot start with '-'.")
    # Initialize the HPC module environment in a Bash login shell.
    remote_command = "bash -lc " + shlex.quote(args.command)
    with tempfile.TemporaryDirectory(prefix="qv-", dir="/tmp") as directory:
        control_socket = f"{directory}/ssh"
        process = subprocess.Popen(
            ["ssh", "-tt", "-x", "-M", "-S", control_socket,
             "-o", "ControlPersist=no", "-o", "ExitOnForwardFailure=yes",
             "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
             args.host, remote_command],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        opened = False
        try:
            for line in process.stdout:
                print(line.rstrip("\r\n"), flush=True)
                match = re.search(r"tauri-server-port=(\d+)", line)
                if match and not opened:
                    remote_port = int(match.group(1))
                    if not 1 <= remote_port <= 65535:
                        raise RuntimeError("QuickView reported an invalid port.")
                    local_port = add_tunnel(args.host, control_socket, remote_port)
                    url = f"http://127.0.0.1:{local_port}/"
                    print(f"\nOpen: {url}", flush=True)
                    print("Press Ctrl+C here to stop QuickView.\n", flush=True)
                    subprocess.run(["open", url], check=True)
                    opened = True
            status = process.wait()
            if status:
                raise RuntimeError(f"SSH exited with status {status}.")
            if not opened:
                raise RuntimeError("QuickView exited without reporting a port.")
        except KeyboardInterrupt:
            print("\nStopping QuickView…", flush=True)
        finally:
            if process.poll() is None:
                try:
                    process.stdin.write("\x03")
                    process.stdin.flush()
                    process.wait(timeout=5)
                except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
                    pass
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            process.stdin.close()
            process.stdout.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"\nError: {error}", file=sys.stderr)
        sys.exit(1)

