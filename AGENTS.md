# Project Guidelines

## Scope
These instructions apply to the whole RosettaX repository. Keep changes narrow, preserve existing public APIs unless the task requires otherwise, and prefer extending existing modules over adding parallel abstractions.

## What This Repo Is
- RosettaX is a local Dash application for flow-cytometry fluorescence and scattering calibration workflows.
- The main package lives under `RosettaX/`; the CLI entry point is `rosettax`, implemented in `RosettaX.__main__`.
- Follow the repo's existing build commands with Python 3.13, while keeping code compatible with the declared minimum Python 3.10.

## Repo Map
- `RosettaX/application/`: app shell, top-level layout, and route wiring.
- `RosettaX/pages/`: page composition. Pages and sections mostly wire layout, ids, and callbacks together.
- `RosettaX/workflow/`: reusable workflow logic. Prefer changing code here when behavior is shared or stateful.
- `RosettaX/workflow/detector/`: detector presets, geometry resolution, and angular-weight behavior.
- `RosettaX/profiles/`, `RosettaX/calibrations/`, `RosettaX/data/`: packaged JSON/data assets. Do not break relative resource loading.
- `tests/`: behavior-first regression coverage for workflows, runtime config, application routing, and scattering modeling.

## How To Route Changes
- If a page section only assembles UI pieces, keep it thin and move reusable logic into `RosettaX.workflow` or that section's `services.py`.
- In page sections, follow the existing split: `main.py` owns assembly, `layout.py` builds components, `callbacks.py` wires Dash callbacks, `services.py` holds local behavior, `ids.py` centralizes ids, and `models.py` or `adapters.py` hold structured data or translation logic.
- If the same behavior exists in both fluorescence and scattering flows, look for a workflow module before duplicating page-local logic.
- Preserve the fluorescence and scattering separation unless the task explicitly requires shared behavior.
- Keep runtime-config key paths stable unless the task is specifically about migrating config structure.
- When working on detector presets, cache geometry, blocker bar geometry, or angular weights, use the detector workflow abstractions that already encode those rules instead of reintroducing compatibility wrappers.

## Implementation Conventions
- Match surrounding style: explicit names, small methods, concise docstrings where the module already uses them.
- Keep domain names explicit. Do not shorten calibration, detector, runtime-config, upload, coupling, or refractive-index terminology.
- Prefer `pathlib.Path` semantics in code and tests; do not assert hard-coded `/` suffixes.
- Avoid embedding one-off scientific rules inside callbacks when a workflow or service module can own them.
- Keep ids centralized in `ids.py` rather than reconstructing string literals across callbacks and layouts.

## Build And Test
- Install development dependencies with `pip install -e .[testing,dev]`.
- Use `make editable` for editable local installs and `make quick` when compiled/build-system behavior matters.
- Run the smallest relevant test slice first:
	- upload workflow: `pytest tests/upload/services_test.py tests/upload/services_guardrails_test.py`
	- runtime config or profiles: `pytest tests/runtime/config_test.py tests/runtime/profile_contract_test.py`
	- application shell, routes, or page composition: `pytest tests/application/main_test.py tests/application/routes_test.py tests/application/page_regressions_test.py`
	- scattering modeling or detector behavior: `pytest tests/scattering/calibration_services_test.py tests/scattering/model_configuration_test.py tests/scattering/backend_cache_test.py tests/apply_calibration/scattering_mie_relation_builder_test.py`
- Use full `pytest` only when a change crosses multiple workflows or shared infrastructure.

## Documentation
- Update `README.rst` or docs only when behavior, workflow steps, or user-visible commands change.
- Keep documentation concrete and workflow-oriented. Avoid generic product language.