"""Run navigation and upload smoke checks against an isolated local app server."""

import argparse
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("build/browser-navigation.json")
    )
    parser.add_argument("--browser-executable", type=Path)
    arguments = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    output_path = arguments.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="rosettax-browser-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        environment = dict(os.environ)
        environment.update(
            MPLCONFIGDIR=str(temporary_path / "matplotlib"),
            ROSETTAX_USAGE_METRICS_PATH=str(temporary_path / "metrics.json"),
            ROSETTAX_VISIT_LOG_PATH=str(temporary_path / "visits.jsonl"),
        )
        log_path = output_path.with_suffix(".server.log")
        with log_path.open("w") as server_log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "RosettaX",
                    "--no-browser",
                    "--no-debug",
                    "--port",
                    str(port),
                    "--log-level",
                    "WARNING",
                ],
                cwd=repository,
                env=environment,
                stdout=server_log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 60
                while True:
                    if server.poll() is not None:
                        raise RuntimeError(f"Application exited; inspect {log_path}")
                    try:
                        with urlopen(url + "/_dash-layout", timeout=1) as response:
                            if response.status == 200:
                                break
                    except (URLError, TimeoutError):
                        pass
                    if time.monotonic() > deadline:
                        raise TimeoutError(
                            f"Application did not start; inspect {log_path}"
                        )
                    time.sleep(0.2)
                command = [
                    sys.executable,
                    str(repository / "tools/profile_navigation.py"),
                    "--url",
                    url,
                    "--repeats",
                    "2",
                    "--output",
                    str(output_path),
                    "--sample-file",
                    str(
                        repository
                        / "RosettaX/assets/sample-files/apogee_rainbow_beads.fcs"
                    ),
                    "--budgets",
                    str(repository / "tools/navigation_budgets.json"),
                ]
                if arguments.browser_executable:
                    command.extend(
                        ["--browser-executable", str(arguments.browser_executable)]
                    )
                subprocess.run(
                    command, cwd=repository, env=environment, check=True, timeout=180
                )
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == "__main__":
    main()
