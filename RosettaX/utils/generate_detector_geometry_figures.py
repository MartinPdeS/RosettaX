# -*- coding: utf-8 -*-

"""
Generate detector geometry preview images for documentation pages.

This script renders one 3D optical preview figure per detector preset and
writes PNG files to the documentation image folders used by RosettaX.

Examples
--------
python -m RosettaX.utils.generate_detector_geometry_figures
python -m RosettaX.utils.generate_detector_geometry_figures --dry-run
python -m RosettaX.utils.generate_detector_geometry_figures --skip-docs-static
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import re
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from RosettaX.pages.p03_scattering.sections.s03_model import optical_preview
from RosettaX.workflow import detector
from RosettaX.workflow.detector.loader import (
    CUSTOM_DETECTOR_PRESET_NAME,
    load_detector_configuration_presets,
)


matplotlib.use("Agg")


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSETS_OUTPUT_DIR = REPO_ROOT / "RosettaX" / "assets" / "detector_figures"
DEFAULT_DOCS_STATIC_OUTPUT_DIR = REPO_ROOT / "docs" / "source" / "_static" / "detector_figures"

# Keep exact legacy file names used by the in-app docs page and Sphinx page.
PRESET_FILENAME_OVERRIDES: dict[str, str] = {
    "Agilent NovoCyte FSC": "agilent_novocyte_fsc.png",
    "Agilent NovoCyte SSC": "agilent_novocyte_ssc.png",
    "Apogee - Forward": "apogee_a60_forward.png",
    "Apogee - Side": "apogee_a60_side.png",
    "BD FACSCanto II FSC": "bd_facscanto2_fsc.png",
    "BD FACSCanto II SSC": "bd_facscanto2_ssc.png",
    "Beckman Coulter CytoFLEX Fluorescence": "beckman_cyttofelx_flourescence.png",
    "Beckman Coulter CytoFLEX SSC": "beckman_cyttofelx_ssc.png",
    "Cytek Aurora FSC": "cytek_aurora_fsc.png",
    "Cytek Aurora SSC": "cytek_aurora_ssc.png",
    "nanoFCM NanoAnalyzer FSC": "nanofcm_nanoanalyzer_fsc.png",
    "nanoFCM NanoAnalyzer SSC": "nanofcm_nanoanalyzer_ssc.png",
    "Sony ID7000 FSC": "sony_id7000_fsc.png",
    "Sony ID7000 SSC": "sony_id7000_ssc.png",
    "Thermo Fisher Attune NxT FSC": "thermofisher_attune_fsc.png",
    "Thermo Fisher Attune NxT SSC": "thermofisher_attune_ssc.png",
}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return re.sub(r"_+", "_", slug)


def _resolve_default_filename(*, preset_name: str, preset: dict[str, Any]) -> str:
    override = PRESET_FILENAME_OVERRIDES.get(preset_name)

    if override:
        return override

    manufacturer = str(preset.get("manufacturer", "")).strip()
    instrument = str(preset.get("instrument", "")).strip()
    channel = str(preset.get("channel", "")).strip()

    if manufacturer or instrument or channel:
        stem = "_".join(
            value
            for value in (
                _slugify(manufacturer),
                _slugify(instrument),
                _slugify(channel),
            )
            if value
        )
        return f"{stem}.png"

    return f"{_slugify(preset_name)}.png"


def _build_figure_for_preset(
    *,
    preset_name: str,
) -> Any:
    (
        resolved_detector_numerical_aperture,
        resolved_detector_cache_numerical_aperture,
        resolved_blocker_bar_numerical_aperture,
        resolved_detector_sampling,
        resolved_detector_phi_angle_degree,
        resolved_detector_gamma_angle_degree,
    ) = detector.resolve_detector_configuration_values(
        preset_name=preset_name,
        current_detector_numerical_aperture=0.2,
        current_detector_cache_numerical_aperture=0.0,
        current_blocker_bar_numerical_aperture=0.0,
        current_detector_sampling=700,
        current_detector_phi_angle_degree=0.0,
        current_detector_gamma_angle_degree=0.0,
    )

    detector_angular_weights = detector.resolve_detector_angular_weights(
        preset_name=preset_name,
        detector_sampling=resolved_detector_sampling,
        current_detector_numerical_aperture=resolved_detector_numerical_aperture,
        current_detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
        current_blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
        current_detector_phi_angle_degree=resolved_detector_phi_angle_degree,
        current_detector_gamma_angle_degree=resolved_detector_gamma_angle_degree,
        current_medium_refractive_index=1.333,
    )

    _, effective_blocker_bar_numerical_aperture = detector.resolve_detector_modeling_geometry_values(
        preset_name=preset_name,
        current_detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
        current_blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
    )

    detector_visible_mask: tuple[bool, ...] | None = None

    if detector_angular_weights is not None:
        detector_visible_mask = tuple(
            bool(value != 0.0)
            for value in np.asarray(
                detector_angular_weights,
                dtype=np.complex128,
            ).reshape(-1)
        )

    scatter_coordinates = optical_preview.resolve_scatter_coordinates(
        scatter_coordinates=None,
        detector_numerical_aperture=float(resolved_detector_numerical_aperture),
        blocker_bar_numerical_aperture=float(effective_blocker_bar_numerical_aperture),
        medium_refractive_index=1.333,
        detector_phi_angle_degree=float(resolved_detector_phi_angle_degree),
        detector_gamma_angle_degree=float(resolved_detector_gamma_angle_degree),
        detector_sampling=int(resolved_detector_sampling),
        detector_visible_mask=detector_visible_mask,
    )

    return {
        "scatter_coordinates": scatter_coordinates,
        "camera": optical_preview.build_default_optical_preview_camera(),
    }


def _camera_to_view_angles(
    camera: dict[str, Any],
) -> tuple[float, float]:
    eye = camera.get("eye", {}) if isinstance(camera, dict) else {}
    eye_x = float(eye.get("x", 1.15))
    eye_y = float(eye.get("y", 1.05))
    eye_z = float(eye.get("z", 0.85))

    azimuth_degree = math.degrees(
        math.atan2(eye_y, eye_x)
    )

    horizontal_norm = math.sqrt(eye_x * eye_x + eye_y * eye_y)
    elevation_degree = math.degrees(
        math.atan2(eye_z, horizontal_norm)
    )

    return elevation_degree, azimuth_degree


def _export_figure(
    *,
    figure: dict[str, Any],
    output_path: Path,
    width: int,
    height: int,
    scale: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure_width_inch = max(width, 1) / 100.0
    figure_height_inch = max(height, 1) / 100.0
    render_dpi = max(1.0, float(scale)) * 100.0

    unit_sphere_x, unit_sphere_y, unit_sphere_z = optical_preview.get_unit_sphere_coordinates()
    center_sphere_x, center_sphere_y, center_sphere_z = optical_preview.get_center_sphere_coordinates()
    scatter_coordinates = np.asarray(
        figure.get("scatter_coordinates", np.empty((0, 3), dtype=float)),
        dtype=float,
    ).reshape(-1, 3)

    matplotlib_figure = plt.figure(
        figsize=(figure_width_inch, figure_height_inch),
        dpi=render_dpi,
    )
    axis = matplotlib_figure.add_subplot(
        111,
        projection="3d",
    )

    axis.plot_surface(
        unit_sphere_x,
        unit_sphere_y,
        unit_sphere_z,
        color="#9ecae1",
        alpha=0.08,
        linewidth=0,
        antialiased=True,
        shade=False,
    )
    axis.plot_surface(
        center_sphere_x,
        center_sphere_y,
        center_sphere_z,
        color="#111111",
        alpha=1.0,
        linewidth=0,
        antialiased=True,
        shade=False,
    )

    if scatter_coordinates.size > 0:
        axis.scatter(
            scatter_coordinates[:, 0],
            scatter_coordinates[:, 1],
            scatter_coordinates[:, 2],
            c="#111111",
            s=2,
            alpha=1.0,
            depthshade=False,
        )

    origin = np.asarray([-0.78, 0.0, 0.0], dtype=float)
    k_tip = np.asarray([-0.14, 0.0, 0.0], dtype=float)
    electric_field_tip = np.asarray([-0.78, 0.0, 0.52], dtype=float)

    axis.quiver(
        origin[0],
        origin[1],
        origin[2],
        *(k_tip - origin),
        color="#d62728",
        linewidth=2.0,
        arrow_length_ratio=0.18,
    )
    axis.quiver(
        origin[0],
        origin[1],
        origin[2],
        *(electric_field_tip - origin),
        color="#1f77b4",
        linewidth=2.0,
        arrow_length_ratio=0.18,
    )
    axis.text(
        -0.11,
        0.0,
        0.08,
        "k",
        color="#d62728",
        fontsize=12,
    )
    axis.text(
        -0.72,
        0.0,
        0.59,
        "E",
        color="#1f77b4",
        fontsize=12,
    )

    axis.set_xlim(-1.35, 1.35)
    axis.set_ylim(-1.35, 1.35)
    axis.set_zlim(-1.35, 1.35)
    axis.set_box_aspect((1.0, 1.0, 1.0))

    elevation_degree, azimuth_degree = _camera_to_view_angles(
        figure.get("camera", {}),
    )
    axis.view_init(
        elev=elevation_degree,
        azim=azimuth_degree,
    )

    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_zticks([])
    axis.set_axis_off()

    matplotlib_figure.patch.set_alpha(0.0)
    axis.patch.set_alpha(0.0)

    plt.tight_layout(pad=0.0)
    matplotlib_figure.savefig(
        output_path,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.01,
    )
    plt.close(matplotlib_figure)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate detector geometry PNG files used by documentation pages.",
    )
    parser.add_argument(
        "--assets-output-dir",
        type=Path,
        default=DEFAULT_ASSETS_OUTPUT_DIR,
        help="Output directory for in-app documentation images.",
    )
    parser.add_argument(
        "--docs-static-output-dir",
        type=Path,
        default=DEFAULT_DOCS_STATIC_OUTPUT_DIR,
        help="Output directory for Sphinx static documentation images.",
    )
    parser.add_argument(
        "--skip-docs-static",
        action="store_true",
        help="Do not write into docs/source/_static/detector_figures.",
    )
    parser.add_argument(
        "--preset",
        action="append",
        default=[],
        help="Optional preset name filter. Can be provided multiple times.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Export width in pixels.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=960,
        help="Export height in pixels.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Export scale factor.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve outputs and print actions without writing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_arguments()

    presets = load_detector_configuration_presets()

    target_output_dirs = [Path(args.assets_output_dir)]

    if not args.skip_docs_static:
        target_output_dirs.append(Path(args.docs_static_output_dir))

    requested_presets = {str(name).strip() for name in (args.preset or []) if str(name).strip()}

    generated_count = 0

    for preset_name in sorted(presets):
        if preset_name == CUSTOM_DETECTOR_PRESET_NAME:
            continue

        if requested_presets and preset_name not in requested_presets:
            continue

        preset = presets[preset_name]
        filename = _resolve_default_filename(
            preset_name=preset_name,
            preset=preset,
        )

        output_paths = [output_dir / filename for output_dir in target_output_dirs]

        if args.dry_run:
            for output_path in output_paths:
                print(f"[dry-run] {preset_name} -> {output_path}")
            generated_count += 1
            continue

        figure = _build_figure_for_preset(
            preset_name=preset_name,
        )

        for output_path in output_paths:
            _export_figure(
                figure=figure,
                output_path=output_path,
                width=args.width,
                height=args.height,
                scale=args.scale,
            )
            print(f"[saved] {preset_name} -> {output_path}")

        generated_count += 1

    print(f"Generated {generated_count} detector geometry figure(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
