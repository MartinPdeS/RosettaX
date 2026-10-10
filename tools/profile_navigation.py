"""Measure browser navigation against a running RosettaX server.

Requires optional Playwright tooling (pip install playwright; playwright install
chromium). Run with --url http://127.0.0.1:8050 and optionally --sample-file
path/to/beads.fcs. Times include a 500 ms network quiet period; they measure
settled page updates rather than human-perceived readiness or isolated rendering.
"""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8050")
    parser.add_argument("--sample-file", type=Path)
    parser.add_argument("--browser-executable", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.repeats < 1:
        parser.error("--repeats must be positive")
    if arguments.sample_file and not arguments.sample_file.is_file():
        parser.error("--sample-file must exist")

    results = []
    errors = []
    with sync_playwright() as playwright:
        options = {"headless": True}
        if arguments.browser_executable:
            options["executable_path"] = str(arguments.browser_executable)
        browser = playwright.chromium.launch(**options)
        page = browser.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        requests = []
        pending = set()
        last_activity = time.perf_counter()

        def request_started(request):
            nonlocal last_activity
            requests.append(request)
            pending.add(request)
            last_activity = time.perf_counter()

        def request_finished(request):
            nonlocal last_activity
            pending.discard(request)
            last_activity = time.perf_counter()

        page.on("request", request_started)
        page.on("requestfinished", request_finished)
        page.on("requestfailed", request_finished)

        def settle() -> None:
            deadline = time.perf_counter() + 60
            while pending or time.perf_counter() - last_activity < 0.5:
                if time.perf_counter() > deadline:
                    raise TimeoutError("Page did not settle within 60 seconds")
                page.wait_for_timeout(50)
            page.wait_for_function(
                """() => document.querySelector('#sidebar-content a[href="/scattering"]')
                && !document.title.startsWith('Updating')
                && !document.querySelector('[data-dash-is-loading="true"]')"""
            )
            # Let the browser paint the final callback results.
            page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")

        def measure(label: str, action) -> None:
            nonlocal last_activity
            requests.clear()
            start = time.perf_counter()
            last_activity = start
            action()
            settle()
            elapsed = time.perf_counter() - start
            callbacks = []
            for request in requests:
                if not request.url.endswith("/_dash-update-component"):
                    continue
                response = request.response()
                callbacks.append({
                    "output": request.post_data_json.get("output"),
                    "duration_ms": request.timing["responseEnd"],
                    "response_bytes": request.sizes()["responseBodySize"] if response else 0,
                    "status": response.status if response else None,
                    "failure": request.failure,
                })
            result = {
                "transition": label,
                "settled_ms": round(elapsed * 1000, 1),
                "callback_count": len(callbacks),
                "callback_response_bytes": sum(c["response_bytes"] for c in callbacks),
                "callbacks": callbacks,
            }
            results.append(result)
            arguments.output.write_text(json.dumps({"measurements": results, "browser_errors": errors}, indent=2) + "\n")
            print(json.dumps({k: v for k, v in result.items() if k != "callbacks"}), flush=True)

        def measure_navigation(label: str, path: str) -> None:
            link = page.locator(f'#sidebar-content a[href="{path}"]').first
            if not link.is_visible():
                page.locator("#sidebar-calibration-toggle-button").click()
                settle()
            measure(label, link.click)

        measure("initial home", lambda: page.goto(arguments.url))
        for repeat in range(arguments.repeats):
            for path in ["/fluorescence", "/scattering", "/"]:
                measure_navigation(f"empty {repeat + 1} {path}", path)

        if arguments.sample_file:
            for path in ["/fluorescence", "/scattering"]:
                measure_navigation(f"before upload {path}", path)
                measure(
                    f"upload {path}",
                    lambda: page.locator('input[type="file"][accept=".fcs"]').first.set_input_files(arguments.sample_file),
                )
                if f"Loaded file: {arguments.sample_file.name}" not in page.locator("#page-content").text_content():
                    raise RuntimeError(f"Uploaded filename missing on {path}")
            for repeat in range(arguments.repeats):
                for path in ["/", "/fluorescence", "/scattering"]:
                    measure_navigation(f"loaded {repeat + 1} {path}", path)
                    if path != "/" and f"Loaded file: {arguments.sample_file.name}" not in page.locator("#page-content").text_content():
                        raise RuntimeError(f"Uploaded filename not restored on {path}")
        browser.close()

    arguments.output.write_text(json.dumps({"measurements": results, "browser_errors": errors}, indent=2) + "\n")
    # Chromium can report ERR_ABORTED for a successful 204 (Dash PreventUpdate).
    if errors or any(c["status"] != 204 and (c["failure"] or c["status"] != 200) for r in results for c in r["callbacks"]):
        raise RuntimeError(f"Browser or callback errors encountered; inspect {arguments.output}")


if __name__ == "__main__":
    main()
