"""Apply report charts rendering."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from .report_document import (
    _escape_pdf_text,
    _measure_helvetica_text,
    _rgb,
    _sanitize_text,
)
from .report_helpers import (
    format_display_value as _format_display_value,
)
from .report_payload import (
    _as_float_or_none,
)
from .report_styles import (
    COLOR_INK,
    COLOR_LINE,
    COLOR_LINE_SERIES,
    COLOR_MUTED,
    COLOR_POINT,
    CONTENT_WIDTH,
    PAGE_MARGIN,
)

if TYPE_CHECKING:
    from .report_pdf import _PdfReportComposer


def draw_chart(composer, *, chart_spec: dict[str, Any]) -> None:
    plot_height = 248.0
    composer._ensure_space(plot_height + 52.0)
    composer._draw_section_title(
        title=str(chart_spec.get("title") or "Calibration plot")
    )

    plot_x = PAGE_MARGIN
    plot_y = composer.cursor_y - plot_height
    plot_width = CONTENT_WIDTH
    inner_x = plot_x + 78.0
    inner_y = plot_y + 48.0
    inner_width = plot_width - 94.0
    inner_height = plot_height - 88.0

    composer._fill_rect(
        x=plot_x,
        y=plot_y,
        width=plot_width,
        height=plot_height,
        fill_color=(1.0, 1.0, 1.0),
        stroke_color=COLOR_LINE,
    )
    composer._draw_text(
        x=plot_x + 12.0,
        y=plot_y + plot_height - 18.0,
        text=str(chart_spec.get("subtitle") or ""),
        font="F1",
        size=8.5,
        color=COLOR_MUTED,
    )
    legend_y = plot_y + plot_height - 18.0
    legend_x = plot_x + plot_width - 150.0
    if chart_spec.get("line_x_values"):
        composer._draw_line(
            x1=legend_x,
            y1=legend_y + 2.0,
            x2=legend_x + 14.0,
            y2=legend_y + 2.0,
            color=COLOR_LINE_SERIES,
            line_width=1.8,
        )
        composer._draw_text(
            x=legend_x + 19.0,
            y=legend_y - 1.0,
            text="Fit",
            font="F1",
            size=7.5,
            color=COLOR_MUTED,
        )
    composer._fill_circle(
        cx=legend_x + 65.0,
        cy=legend_y + 2.0,
        radius=2.6,
        fill_color=COLOR_POINT,
    )
    composer._draw_text(
        x=legend_x + 72.0,
        y=legend_y - 1.0,
        text="Observed",
        font="F1",
        size=7.5,
        color=COLOR_MUTED,
    )

    transformed_points = _build_transformed_points(
        x_values=chart_spec.get("x_values", []),
        y_values=chart_spec.get("y_values", []),
        log_x=bool(chart_spec.get("log_x", False)),
        log_y=bool(chart_spec.get("log_y", False)),
    )
    transformed_line = _build_transformed_points(
        x_values=chart_spec.get("line_x_values", []),
        y_values=chart_spec.get("line_y_values", []),
        log_x=bool(chart_spec.get("log_x", False)),
        log_y=bool(chart_spec.get("log_y", False)),
    )
    all_points = transformed_points + transformed_line
    x_min, x_max = _resolve_plot_range([point[0] for point in all_points])
    y_min, y_max = _resolve_plot_range([point[1] for point in all_points])

    for tick_index in range(5):
        y_value = inner_y + (inner_height * tick_index / 4.0)
        x_value = inner_x + (inner_width * tick_index / 4.0)
        composer._draw_line(
            x1=inner_x,
            y1=y_value,
            x2=inner_x + inner_width,
            y2=y_value,
            color=COLOR_LINE,
            line_width=0.6,
        )
        composer._draw_line(
            x1=x_value,
            y1=inner_y,
            x2=x_value,
            y2=inner_y + inner_height,
            color=COLOR_LINE,
            line_width=0.6,
        )

    composer._draw_line(
        x1=inner_x,
        y1=inner_y,
        x2=inner_x + inner_width,
        y2=inner_y,
        color=COLOR_INK,
        line_width=1.1,
    )
    composer._draw_line(
        x1=inner_x,
        y1=inner_y,
        x2=inner_x,
        y2=inner_y + inner_height,
        color=COLOR_INK,
        line_width=1.1,
    )

    if transformed_line:
        polyline_points = [
            (
                _project_value(point[0], x_min, x_max, inner_x, inner_width),
                _project_value(point[1], y_min, y_max, inner_y, inner_height),
            )
            for point in transformed_line
        ]
        composer._draw_polyline(
            points=polyline_points, color=COLOR_LINE_SERIES, line_width=1.8
        )

    for point_x, point_y in transformed_points:
        marker_x = _project_value(point_x, x_min, x_max, inner_x, inner_width)
        marker_y = _project_value(point_y, y_min, y_max, inner_y, inner_height)
        composer._fill_circle(
            cx=marker_x, cy=marker_y, radius=2.6, fill_color=COLOR_POINT
        )

    log_x = bool(chart_spec.get("log_x", False))
    log_y = bool(chart_spec.get("log_y", False))
    draw_axis_label(
        composer,
        center_x=inner_x + inner_width / 2.0,
        center_y=plot_y + 15.0,
        text=str(chart_spec.get("x_label") or ""),
    )
    draw_axis_label(
        composer,
        center_x=plot_x + 16.0,
        center_y=inner_y + inner_height / 2.0,
        text=str(chart_spec.get("y_label") or ""),
        vertical=True,
    )
    composer._draw_text(
        x=inner_x,
        y=inner_y - 14.0,
        text=_format_display_value(_inverse_transform_value(x_min, log_x)),
        font="F1",
        size=7.5,
        color=COLOR_MUTED,
    )
    x_max_label = _format_display_value(_inverse_transform_value(x_max, log_x))
    composer._draw_text(
        x=inner_x + inner_width - _measure_helvetica_text(x_max_label, size=7.5),
        y=inner_y - 14.0,
        text=x_max_label,
        font="F1",
        size=7.5,
        color=COLOR_MUTED,
    )
    y_min_label = _format_display_value(_inverse_transform_value(y_min, log_y))
    composer._draw_text(
        x=inner_x - 10.0 - _measure_helvetica_text(y_min_label, size=7.5),
        y=inner_y - 2.0,
        text=y_min_label,
        font="F1",
        size=7.5,
        color=COLOR_MUTED,
    )
    y_max_label = _format_display_value(_inverse_transform_value(y_max, log_y))
    composer._draw_text(
        x=inner_x - 10.0 - _measure_helvetica_text(y_max_label, size=7.5),
        y=inner_y + inner_height - 2.0,
        text=y_max_label,
        font="F1",
        size=7.5,
        color=COLOR_MUTED,
    )

    composer.cursor_y = plot_y - 16.0


def draw_axis_label(
    composer: _PdfReportComposer,
    *,
    center_x: float,
    center_y: float,
    text: str,
    vertical: bool = False,
) -> None:
    size = 8.5
    text_width = _measure_helvetica_text(text, size=size)
    if vertical:
        x = center_x + size * 0.3
        y = center_y - text_width / 2.0
        matrix = "0 1 -1 0"
    else:
        x = center_x - text_width / 2.0
        y = center_y - size * 0.3
        matrix = "1 0 0 1"
    composer.current_page.commands.append(
        f"BT /F1 {size:.2f} Tf {_rgb(COLOR_MUTED)} rg "
        f"{matrix} {x:.2f} {y:.2f} Tm "
        f"({_escape_pdf_text(_sanitize_text(text))}) Tj ET"
    )


def _build_transformed_points(
    *,
    x_values: Any,
    y_values: Any,
    log_x: bool,
    log_y: bool,
) -> list[tuple[float, float]]:
    if not isinstance(x_values, list) or not isinstance(y_values, list):
        return []

    transformed_points: list[tuple[float, float]] = []
    for x_value, y_value in zip(x_values, y_values, strict=False):
        x_float = _as_float_or_none(x_value)
        y_float = _as_float_or_none(y_value)
        if x_float is None or y_float is None:
            continue
        if log_x and x_float <= 0.0:
            continue
        if log_y and y_float <= 0.0:
            continue

        transformed_points.append(
            (
                math.log10(x_float) if log_x else x_float,
                math.log10(y_float) if log_y else y_float,
            )
        )

    return transformed_points


def _resolve_plot_range(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        return minimum - 0.5, maximum + 0.5

    padding = (maximum - minimum) * 0.08
    return minimum - padding, maximum + padding


def _project_value(
    value: float, minimum: float, maximum: float, plot_origin: float, plot_size: float
) -> float:
    if maximum == minimum:
        return plot_origin + (plot_size / 2.0)

    fraction = (value - minimum) / (maximum - minimum)
    return plot_origin + (fraction * plot_size)


def _inverse_transform_value(value: float, log_axis: bool) -> float:
    if log_axis:
        return 10.0**value

    return value
