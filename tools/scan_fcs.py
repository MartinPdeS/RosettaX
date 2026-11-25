"""Audit FCS recordings against the reviewed cross-device regression fixtures."""

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from RosettaX.workflow.validation_recordings import (  # noqa: E402
    SAMPLE_DIRECTORY,
    reviewed_recordings,
    supported_cytometers,
)


def readme_with_systems(*, source: str) -> str:
    """Replace the marked README table with the instrument list from reviewed recordings."""
    start = ".. supported-cytometers-start"
    end = ".. supported-cytometers-end"
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("Expected exactly one supported-cytometers marker pair in README.rst")
    before, section = source.split(start)
    _, after = section.split(end)
    rows = [".. list-table::", "   :header-rows: 1", "   :widths: 28 72", "",
            "   * - Manufacturer", "     - Cytometer models"]
    for brand, models in supported_cytometers().items():
        rows.extend([f"   * - {brand}", f"     - {', '.join(models)}"])
    return before + start + "\n\n" + "\n".join(rows) + "\n\n" + end + after


def acquisition_metadata(*, path: Path) -> tuple[str, list[str], dict | None]:
    """Read the FCS header and resolve suggested Rosetta channels with the installed app."""
    from RosettaX.utils.reader import FCSFile
    from RosettaX.workflow.detector.catalog import match_recording_instrument
    from RosettaX.workflow.detector.configuration import (
        extract_instrument_name_from_metadata,
    )

    with FCSFile(str(path)) as recording:
        metadata = recording.get_metadata()
    instrument = extract_instrument_name_from_metadata(metadata=metadata)
    columns = metadata.column_names
    match = match_recording_instrument(instrument_name=instrument, channel_names=columns)
    return instrument, columns, match


def describe_acquisition(*, path: Path) -> str:
    """Summarize an FCS header and the suggested catalog channels."""
    from RosettaX.workflow.peak.core.detectors import infer_rosetta_v1_channel

    instrument, columns, match = acquisition_metadata(path=path)
    roles = [
        infer_rosetta_v1_channel(column_names=columns, detector_role=role, matched_rule=match)
        for role in ("scattering", "green_fluorescence")
    ]
    return (f"FCS instrument={instrument!r}, catalog={match['model'] if match else 'unmatched'}, "
            f"scatter={roles[0]!r}, green={roles[1]!r}, available channels={columns}")


def audit_inventory(*, args: argparse.Namespace) -> int:
    """Check stored fingerprints, review coverage and README consistency."""
    if args.path and args.update_readme:
        raise ValueError("--update-readme requires a full checkout scan")
    records = reviewed_recordings()
    by_digest = {record["sha256"]: path for path, record in records.items()}
    expected = {SAMPLE_DIRECTORY / path: record for path, record in records.items()}
    if args.path:
        target = args.path.resolve()
        if not target.exists() or (target.is_file() and target.suffix.lower() != ".fcs"):
            raise ValueError(f"Expected an FCS file or directory: {target}")
        paths = {target} if target.is_file() else {
            path for path in target.rglob("*") if path.is_file() and path.suffix.lower() == ".fcs"
        }
        if target.is_dir():
            paths.update(path for path in expected if path.is_relative_to(target))
    else:
        tracked = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT)
        paths = {ROOT / path for path in os.fsdecode(tracked).split("\0") if path.lower().endswith(".fcs")}
        paths.update(expected)
        # Include incoming files in the review directory even when Git ignores their extension.
        paths.update(path for path in (SAMPLE_DIRECTORY / "cross_device").rglob("*") if path.is_file() and path.suffix.lower() == ".fcs")

    counts = Counter()
    failed = False
    for path in sorted(paths):
        location = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        digest = ""
        if not path.is_file():
            status = "MISSING"
        else:
            digest = file_digest(path=path)
            if path in expected and digest != expected[path]["sha256"]:
                status = "CHANGED"
            else:
                status = "REVIEWED" if digest in by_digest else "UNREVIEWED"
        record = records[by_digest[digest]] if digest in by_digest and status == "REVIEWED" else None
        detail = f"{record['manufacturer']} {record['model']}" if record else digest
        print(f"{status:10} {location}  {detail}")
        if args.inspect and path.is_file():
            try:
                print("           " + describe_acquisition(path=path))
            except (ValueError, OSError, RuntimeError, KeyError) as error:
                print(f"           Cannot inspect FCS header: {error}", file=sys.stderr)
                failed = True
        counts[status] += 1
        if status in {"MISSING", "CHANGED"} or (status == "UNREVIEWED" and (args.path or path.is_relative_to(SAMPLE_DIRECTORY / "cross_device"))):
            failed = True
        if path.is_relative_to(SAMPLE_DIRECTORY / "cross_device") and path not in expected:
            if record is not None:
                print(f"           Unregistered copy of {by_digest[digest]}")
            failed = True
    print(", ".join(f"{count} {status.lower()}" for status, count in sorted(counts.items())) or "No FCS files found.")
    if not args.path:
        readme = ROOT / "README.rst"
        source = readme.read_text(encoding="utf-8")
        updated = readme_with_systems(source=source)
        if args.update_readme and not failed and source != updated:
            readme.write_text(updated, encoding="utf-8")
        elif source != updated:
            print("README table is stale. Run tools/scan_fcs.py --update-readme.", file=sys.stderr)
            failed = True
    return int((args.check or args.update_readme) and (failed or not paths))



def file_digest(*, path: Path) -> str:
    """Return the SHA-256 fingerprint of an FCS recording."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def replace_text(*, path: Path, text: str) -> None:
    """Publish a complete UTF-8 file with an atomic rename on the same filesystem."""
    with NamedTemporaryFile(dir=path.parent, delete=False) as staged:
        temporary_path = Path(staged.name)
        try:
            staged.write(text.encode("utf-8"))
            staged.close()
            temporary_path.chmod(path.stat().st_mode & 0o777)
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)


def register_recording(*, source: Path, record: dict, columns: list[str]) -> None:
    """Register a reviewed file, its expectations and the README inventory together."""
    registry = SAMPLE_DIRECTORY / "sample_file_metadata.json"
    destination = SAMPLE_DIRECTORY / "cross_device" / source.name
    key = destination.relative_to(SAMPLE_DIRECTORY).as_posix()
    readme = ROOT / "README.rst"
    lock = registry.with_suffix(".lock")
    try:
        handle = lock.open("x")
    except FileExistsError as error:
        raise ValueError(f"Registration is locked by {lock}. Check for an active add command before removing a stale lock.") from error
    try:
        copied = False
        published = False
        try:
            original = registry.read_text(encoding="utf-8")
            metadata = json.loads(original)
            if any(entry.get("validation", {}).get("sha256") == record["sha256"] for entry in metadata.values()):
                raise ValueError("These contents are already registered.")
            if key in metadata:
                raise ValueError(f"A sample is already registered at {key}. Choose a distinct filename.")
            if not destination.exists():
                with source.open("rb") as incoming, destination.open("xb") as outgoing:
                    copied = True
                    shutil.copyfileobj(incoming, outgoing)
            if file_digest(path=destination) != record["sha256"]:
                raise ValueError(f"{destination.name} differs from the tested contents.")
            metadata[key] = {"detectors": columns, "size_bytes": destination.stat().st_size, "validation": record}
            original_readme = readme.read_text(encoding="utf-8")
            replace_text(path=registry, text=json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
            published = True
            updated = readme_with_systems(source=original_readme)
            if original_readme != updated:
                replace_text(path=readme, text=updated)
        except BaseException:
            if published:
                replace_text(path=registry, text=original)
            if copied:
                destination.unlink(missing_ok=True)
            raise
    finally:
        handle.close()
        lock.unlink()
    print(f"Added {key}")


def assignment_failure(*, diameters: list) -> str:
    """Return the validation failure reason for a recording with too few assigned sizes."""
    return "fewer than 2 assigned peaks" if sum(bool(size) for size in diameters) < 2 else ""


def check_file(*, args: argparse.Namespace) -> int:
    """Exercise automatic channel selection and sizing, then compare or review the outcome."""
    from RosettaX.workflow.peak.core.detectors import (
        populate_peak_script_detector_dropdowns,
    )
    from RosettaX.workflow.recording_validation import check_outcome, run_real_sample

    path = args.file.resolve()
    if not path.is_file() or path.suffix.casefold() != ".fcs":
        raise ValueError(f"Expected a single FCS file: {path}")
    digest = file_digest(path=path)
    records = reviewed_recordings()
    registered_key = next((key for key, value in records.items() if value["sha256"] == digest), None)
    if path.is_relative_to(SAMPLE_DIRECTORY) and path.relative_to(SAMPLE_DIRECTORY).as_posix() in records:
        if registered_key != path.relative_to(SAMPLE_DIRECTORY).as_posix():
            raise ValueError(f"Registered fixture has changed: {path}")
    instrument, columns, match = acquisition_metadata(path=path)
    _, selected = populate_peak_script_detector_dropdowns(
        uploaded_fcs_path=str(path), detector_dropdown_ids=[
            {"process": "Rosetta Script V1", "channel": role} for role in ("scattering", "green_fluorescence")
        ], current_detector_values=[None, None], auto_select_rosetta_v1=True, logger=logging.getLogger(__name__),
    )
    if len(selected) != 2 or not all(selected):
        raise ValueError(f"Configure Rosetta channel recommendations for {instrument!r} in instrument_catalog.toml. Available channels: {columns}")
    if file_digest(path=path) != digest:
        raise ValueError(f"{path.name} changed during channel detection.")
    record = records.get(registered_key, {})
    scatter, fluorescence = selected
    if record and selected != [record["scatter"], record["fluorescence"]]:
        raise ValueError(f"Observed {selected}, expected {[record['scatter'], record['fluorescence']]}.")
    result = run_real_sample(
        path=path, scatter=scatter, fluorescence=record.get("sizing_fluorescence", fluorescence),
        fit_calibration=record.get("fit_calibration", True),
    )
    if file_digest(path=path) != digest:
        raise ValueError(f"{path.name} changed during validation.")
    diameters = [row["particle_diameter_nm"] for row in result["rows"]]
    print(f"{path.name} ({instrument})\nChannels: {scatter}, {fluorescence}\nDiameters (nm): {diameters}\n{result['status']}")
    print(f"Calibration R²: {result['r_squared']}" if result["r_squared"] is not None else f"Calibration R²: {result['fit_note']}.")
    failure = assignment_failure(diameters=diameters)
    if failure:
        print(f"FAIL: {failure}")
        return 1
    if not record:
        brand = (match or {}).get("manufacturer", "")
        model = (match or {}).get("model", instrument)
        brand = {"Sony Biosciences": "Sony", "BD Biosciences": "BD", "Cytek Biosciences": "Cytek",
                 "Beckman Coulter Life Sciences": "Beckman Coulter"}.get(brand, brand)
        model = {"A50-Micro Standard": "A50 Micro", "A60-Micro Standard": "A60 Micro", "MicroPLUS Standard": "MicroPLUS"}.get(model, model)
        record = dict(sha256=digest, scatter=scatter, fluorescence=fluorescence, fit_calibration=True,
                      expected_diameters_nm=diameters, expected_warning=result["status"] if result["warning"] else "",
                      manufacturer=brand, model=model, title=f"{brand} {model} ({path.stem})")
    check_outcome(result=result, record=record, fixture_name=Path(registered_key or path.name).name)
    if registered_key:
        print(f"PASS: matches reviewed recording {registered_key}.")
        return 0
    if args.command == "check":
        print("New recording. Workflow completed; no reviewed baseline exists yet.")
        return 0
    for field in ("manufacturer", "model", "title"):
        if getattr(args, field):
            record[field] = getattr(args, field)
    if not record["manufacturer"] or not record["model"]:
        raise ValueError("Supply --manufacturer and --model for this acquisition.")
    print(json.dumps(record, indent=2, ensure_ascii=False))
    if not args.accept and input("Add these reviewed expectations? [y/N] ").strip().lower() not in {"y", "yes"}:
        print("Registration cancelled.")
        return 1
    register_recording(source=path, record=record, columns=columns)
    return 0


def run_all_checks(*, markdown: Path | None = None) -> int:
    """Run the reference suite once and report observed results per recording."""
    with TemporaryDirectory() as directory:
        report = Path(directory) / "results.xml"
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:cacheprovider", "-q",
             f"--junitxml={report}", "tests/reference/cross_device_rosetta_calibration_test.py"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        if not report.is_file():
            print(process.stdout, file=sys.stderr)
            return process.returncode or 1
        cases = ElementTree.parse(report).findall(".//testcase")

    results = {}
    for case in cases:
        properties = {item.get("name"): item.get("value") for item in case.findall("properties/property")}
        filename = properties.get("recording")
        if not filename:
            print(process.stdout, file=sys.stderr)
            return process.returncode or 1
        result = results.setdefault(filename, {"sizes": "unavailable", "fit": "—", "fit_note": "fit unavailable", "issues": []})
        for field in ("model", "scatter", "fluorescence"):
            if field in properties:
                result[field] = properties[field]
        if "diameters_nm" in properties:
            diameters = json.loads(properties["diameters_nm"])
            failure = assignment_failure(diameters=diameters)
            if failure:
                result["issues"].append(failure)
            size_labels = []
            for diameter in diameters:
                if isinstance(diameter, float) and diameter.is_integer():
                    diameter = int(diameter)
                size_labels.append("?" if diameter == "" else str(diameter))
            result["sizes"] = ", ".join(size_labels) or "none"
            r_squared = json.loads(properties["r_squared"])
            result["fit"] = "—" if r_squared is None else f"{r_squared:.6f}"
            result["fit_note"] = (properties.get("fit_note") or "no fit") if r_squared is None else ""
        for issue in case:
            if issue.tag in {"failure", "error", "skipped"}:
                message = issue.get("message") or issue.tag
                result["issues"].append(" ".join(message.split())[:180])

    headers = ("Status", "Recording", "Model", "Scatter", "Fluorescence", "Sizes (nm)", "R²", "Notes")
    rows = []
    failures = 0
    for filename, result in results.items():
        issues = result["issues"]
        failures += bool(issues)
        notes = "; ".join(dict.fromkeys(filter(None, [result["fit_note"], *issues])))
        rows.append(("FAIL" if issues else "PASS", filename, result.get("model", "—"),
                     result.get("scatter", "—"), result.get("fluorescence", "—"),
                     result["sizes"], result["fit"], notes))

    widths = [max(map(len, column)) for column in zip(headers, *rows)]
    for row in [headers, *rows]:
        cells = [cell.rjust(width) if header == "R²" else cell.ljust(width)
                 for header, cell, width in zip(headers, row, widths)]
        print("  ".join(cells).rstrip())
    footer = []
    if any("?" in result["sizes"] for result in results.values()):
        footer.append("? = detected peak with no assigned diameter")
    footer.append(f"{len(results) - failures}/{len(results)} recordings passed ({len(cases)} checks).")
    print("\n".join(footer))

    if markdown is not None:
        table = [headers, ["---"] * len(headers), *rows]
        lines = ["# Cross-device FCS validation", "",
                 "Scatter and fluorescence are the FCS channels used for bead sizing. "
                 "R² is the scattering calibration-curve fit for the assigned bead sizes.", ""]
        size_column = headers.index("Sizes (nm)")
        notes_column = headers.index("Notes")
        for row in table:
            cells = [cell.replace("\\", "\\\\").replace("|", "\\|") for cell in row]
            cells[size_column] = cells[size_column].replace(" ", "&nbsp;")
            # Keep short reasons together so Markdown renderers give Notes enough room.
            if len(row[notes_column]) <= 32:
                cells[notes_column] = cells[notes_column].replace(" ", "&nbsp;")
            lines.append("| " + " | ".join(cells) + " |")
        lines.extend(["", "\n\n".join(footer), ""])
        markdown.write_text("\n".join(lines), encoding="utf-8")
    return process.returncode or int(bool(failures))


def main() -> int:
    """Dispatch a workflow check, reviewed-fixture registration, or inventory audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check_all = commands.add_parser("check-all", help="Run the real workflow tests for every registered recording.")
    check_all.add_argument("--markdown", type=Path, metavar="PATH", help="Write the same results as a Markdown report.")
    single = commands.add_parser("check", help="Run one FCS and compare with its reviewed expectations when available.")
    single.add_argument("file", type=Path)
    add = commands.add_parser("add", help="Run one FCS and register its reviewed outcome.")
    add.add_argument("file", type=Path)
    add.add_argument("--manufacturer", help="Override the displayed manufacturer.")
    add.add_argument("--model", help="Override the displayed model.")
    add.add_argument("--title", help="Set the recording title shown on the downloads page.")
    add.add_argument("--accept", action="store_true", help="Accept the printed expectations without prompting.")
    audit = commands.add_parser("audit", help="Inspect file fingerprints and README consistency.")
    audit.add_argument("path", nargs="?", type=Path, help="Scan a file or directory recursively (default: source checkout).")
    audit.add_argument("--inspect", action="store_true", help="Read FCS headers and show instrument and channel suggestions (requires RosettaX dependencies).")
    audit.add_argument("--check", action="store_true", help="Fail on fixture drift, missing reviews in cross_device, or a stale README. For an explicit path, require every input to be reviewed.")
    audit.add_argument("--update-readme", action="store_true", help="Refresh only the supported cytometers table after checking the source fixtures.")
    arguments = sys.argv[1:]
    if not arguments or arguments[0] not in {"check-all", "check", "add", "audit", "-h", "--help"}:
        arguments = ["audit", *arguments]
    args = parser.parse_args(arguments)
    try:
        if args.command == "audit":
            return audit_inventory(args=args)
        if args.command == "check-all":
            return run_all_checks(markdown=args.markdown)
        return check_file(args=args)
    except (ValueError, RuntimeError, OSError, EOFError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
