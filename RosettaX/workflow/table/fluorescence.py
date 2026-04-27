from typing import Any


DEFAULT_BEAD_ROWS = [
    {"col1": "", "col2": ""}
    for _ in range(3)
]

def build_default_bead_rows() -> list[dict[str, str]]:
    return [
        dict(row)
        for row in DEFAULT_BEAD_ROWS
    ]

def build_bead_rows_from_mesf_values(
    mesf_values: Any,
) -> list[dict[str, str]]:
    if mesf_values is None:
        return build_default_bead_rows()

    if isinstance(mesf_values, str):
        raw_parts = [
            part.strip()
            for part in mesf_values.split(",")
        ]
    elif isinstance(mesf_values, (list, tuple)):
        raw_parts = [
            str(part).strip()
            for part in mesf_values
        ]
    else:
        raw_parts = [
            str(mesf_values).strip()
        ]

    parsed_values: list[str] = []

    for raw_part in raw_parts:
        if not raw_part:
            continue

        parsed_value = casting.as_float(
            raw_part,
        )

        if parsed_value is None:
            continue

        parsed_values.append(
            f"{float(parsed_value):.6g}"
        )

    if not parsed_values:
        return build_default_bead_rows()

    return [
        {
            "col1": value,
            "col2": "",
        }
        for value in parsed_values
    ]