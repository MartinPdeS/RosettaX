# -*- coding: utf-8 -*-

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any


_SELLMEIER_DIRECTORY_PATH = Path(__file__).resolve().parents[2] / "assets" / "sellmeier"


@lru_cache(maxsize=1)
def _load_sellmeier_bank() -> dict[str, Any]:
    materials: dict[str, Any] = {}

    for json_path in sorted(_SELLMEIER_DIRECTORY_PATH.glob("*.json")):
        with json_path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)

        if not isinstance(payload, dict):
            raise ValueError(
                f"Sellmeier material file must contain a JSON object: {json_path.name}."
            )

        material_id = str(payload.get("id") or json_path.stem).strip().lower()

        if not material_id:
            raise ValueError(
                f"Sellmeier material file must define a material id: {json_path.name}."
            )

        materials[material_id] = {
            key: value
            for key, value in payload.items()
            if key != "id"
        }

    return {
        "schema_version": 1,
        "wavelength_unit": "um",
        "formula": "n^2 = a + sum(B_i * lambda^2 / (lambda^2 - C_i))",
        "materials": materials,
    }


def calculate_sellmeier_refractive_index(
    material_id: Any,
    *,
    wavelength_nm: Any,
) -> float:
    """
    Resolve one material refractive index from the Sellmeier bank.
    """
    material_key = str(material_id or "").strip().lower()

    if not material_key:
        raise ValueError("material_id is required.")

    wavelength_um = float(wavelength_nm) / 1000.0

    if wavelength_um <= 0.0:
        raise ValueError("wavelength_nm must be positive.")

    bank = _load_sellmeier_bank()
    material_spec = bank.get("materials", {}).get(material_key)

    if not isinstance(material_spec, dict):
        raise KeyError(f"Unknown Sellmeier material: {material_key}.")

    coefficient_spec = material_spec.get("coefficients", {})
    offset = float(coefficient_spec.get("a", 1.0))
    b_coefficients = coefficient_spec.get("b", [])
    c_coefficients = coefficient_spec.get("c", [])

    if len(b_coefficients) != len(c_coefficients):
        raise ValueError(
            f"Sellmeier coefficients are misconfigured for {material_key}."
        )

    wavelength_squared = wavelength_um * wavelength_um
    refractive_index_squared = offset

    for b_coefficient, c_coefficient in zip(b_coefficients, c_coefficients):
        refractive_index_squared += float(b_coefficient) * wavelength_squared / (
            wavelength_squared - float(c_coefficient)
        )

    if refractive_index_squared <= 0.0:
        raise ValueError(
            f"Sellmeier resolution produced a non-positive refractive index for {material_key}."
        )

    return math.sqrt(refractive_index_squared)


def resolve_refractive_index_value(
    preset_value: Any,
    *,
    wavelength_nm: Any,
) -> float:
    """
    Resolve either one numeric value or one Sellmeier material identifier.
    """
    if preset_value is None:
        raise ValueError("preset_value is required.")

    if isinstance(preset_value, bool):
        raise ValueError("preset_value must not be boolean.")

    if isinstance(preset_value, (int, float)):
        return float(preset_value)

    preset_value_text = str(preset_value).strip()

    if not preset_value_text:
        raise ValueError("preset_value is required.")

    try:
        return float(preset_value_text)
    except ValueError:
        return calculate_sellmeier_refractive_index(
            preset_value_text,
            wavelength_nm=wavelength_nm,
        )


def resolve_refractive_index_source_value(
    source_value: Any,
    *,
    wavelength_nm: Any,
    fallback_value: Any,
) -> float:
    """
    Resolve a preset source to one numeric refractive index, falling back to an
    explicit numeric value when the source is empty or unknown.
    """
    if source_value not in (None, ""):
        try:
            return resolve_refractive_index_value(
                source_value,
                wavelength_nm=wavelength_nm,
            )
        except Exception:
            pass

    return float(fallback_value)


def format_refractive_index_display(
    value: Any,
    *,
    source_value: Any = None,
) -> str:
    """Format a resolved index, including its Sellmeier material when known."""
    formatted_value = f"{float(value):.6g}"
    material_key = str(source_value or "").strip().lower()

    if material_key and material_key in _load_sellmeier_bank().get("materials", {}):
        material_label = material_key.replace("_", " ").replace("-", " ").title()
        return f"{material_label}({formatted_value})"

    return formatted_value
