# -*- coding: utf-8 -*-

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import dash


def register_setting_spinner_callbacks(
    *,
    ids: Any,
) -> None:
    """
    Register callbacks for custom process setting spinner buttons.

    These buttons support a separate spinner increment without forcing the
    typed input value to align to the same browser-level ``step`` validity
    constraint.
    """

    @dash.callback(
        dash.Output(
            ids.process_setting_match(),
            "value",
        ),
        dash.Input(
            ids.process_setting_spinner_button_match(),
            "n_clicks",
        ),
        dash.State(
            ids.process_setting_match(),
            "value",
        ),
        dash.State(
            ids.process_setting_match(),
            "id",
        ),
        dash.State(
            ids.process_setting_spinner_button_match(),
            "id",
        ),
        prevent_initial_call=True,
    )
    def update_process_setting_from_spinner(
        button_clicks: list[Any],
        current_value: Any,
        setting_id: dict[str, Any],
        button_ids: list[dict[str, Any]],
    ) -> Any:
        del button_clicks
        del setting_id

        triggered_id = dash.ctx.triggered_id

        if not isinstance(triggered_id, dict):
            return dash.no_update

        if not isinstance(button_ids, list):
            return dash.no_update

        direction = str(
            triggered_id.get("direction", ""),
        ).strip().lower()

        if direction not in {
            "up",
            "down",
        }:
            return dash.no_update

        step_value = Decimal("0.001")
        minimum_value = Decimal("0.000001")
        maximum_value = Decimal("0.08")

        resolved_value = _coerce_decimal(
            value=current_value,
            default=minimum_value,
        )

        if direction == "up":
            resolved_value += step_value
        else:
            resolved_value -= step_value

        resolved_value = max(
            minimum_value,
            min(
                maximum_value,
                resolved_value,
            ),
        )

        return _format_decimal(
            resolved_value,
        )


def _coerce_decimal(
    *,
    value: Any,
    default: Decimal,
) -> Decimal:
    """
    Parse a Decimal from UI input and fall back to ``default`` when needed.
    """
    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError, TypeError, ValueError):
        return Decimal(default)


def _format_decimal(
    value: Decimal,
) -> str:
    """
    Format a Decimal for a text input without scientific notation.
    """
    normalized = format(
        value,
        "f",
    )

    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")

    if not normalized:
        return "0"

    return normalized
