"""Apply report tables rendering."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Any

from .report_helpers import (
    format_display_value as _format_display_value,
)
from .report_styles import (
    COLOR_ACCENT,
    COLOR_INK,
    COLOR_LINE,
    COLOR_SURFACE_ALT,
    CONTENT_WIDTH,
    PAGE_BOTTOM,
    PAGE_MARGIN,
)

if TYPE_CHECKING:
    from .report_pdf import _PdfReportComposer


def draw_table(
    composer: _PdfReportComposer,
    *,
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    column_weights: list[float],
) -> None:
    if not headers:
        return

    weights_total = sum(column_weights) or float(len(headers))
    column_widths = [
        CONTENT_WIDTH * (weight / weights_total) for weight in column_weights
    ]
    header_line_count = max(
        len(
            composer._wrap_text_to_width(text=header, width=width - 12.0, font_size=9.0)
        )
        for header, width in zip(headers, column_widths, strict=False)
    )
    header_height = max(22.0, header_line_count * 10.0 + 12.0)
    font_size = 9.0
    line_height = 11.0
    row_padding = 7.0
    row_index = 0

    if rows:
        first_row_layout = build_table_row_layout(
            composer,
            row_values=rows[0],
            column_widths=column_widths,
            font_size=font_size,
            line_height=line_height,
            row_padding=row_padding,
        )
        composer._ensure_space(28.0 + header_height + first_row_layout[1] + 10.0)
    else:
        composer._ensure_space(40.0)

    composer._draw_section_title(title=title)

    while row_index < len(rows):
        next_row_layout = build_table_row_layout(
            composer,
            row_values=rows[row_index],
            column_widths=column_widths,
            font_size=font_size,
            line_height=line_height,
            row_padding=row_padding,
        )
        composer._ensure_space(header_height + next_row_layout[1] + 10.0)
        draw_table_header(
            composer, headers=headers, column_widths=column_widths, height=header_height
        )

        while row_index < len(rows):
            cell_lines_by_column, row_height = build_table_row_layout(
                composer,
                row_values=rows[row_index],
                column_widths=column_widths,
                font_size=font_size,
                line_height=line_height,
                row_padding=row_padding,
            )

            available_height = composer.cursor_y - PAGE_BOTTOM
            if row_height > available_height:
                cell_lines_by_column, row_height = truncate_row_layout_to_fit_height(
                    composer,
                    cell_lines_by_column=cell_lines_by_column,
                    line_height=line_height,
                    row_padding=row_padding,
                    available_height=available_height,
                )

            if composer.cursor_y - row_height < PAGE_BOTTOM:
                composer._start_new_page()
                composer._draw_section_title(title=f"{title} (continued)")
                break

            draw_table_row(
                composer,
                row_number=row_index,
                cell_lines_by_column=cell_lines_by_column,
                column_widths=column_widths,
                row_height=row_height,
                line_height=line_height,
                font_size=font_size,
            )
            row_index += 1

        if row_index >= len(rows):
            composer.cursor_y -= 14.0


def build_table_row_layout(
    composer: _PdfReportComposer,
    *,
    row_values: list[Any],
    column_widths: list[float],
    font_size: float,
    line_height: float,
    row_padding: float,
) -> tuple[list[list[str]], float]:
    cell_lines_by_column: list[list[str]] = []

    for value, column_width in zip(row_values, column_widths, strict=False):
        cell_lines_by_column.append(
            composer._wrap_text_to_width(
                text=_format_display_value(value),
                width=column_width - 12.0,
                font_size=font_size,
            )
            or [""],
        )

    row_height = (max(len(lines) for lines in cell_lines_by_column) * line_height) + (
        2.0 * row_padding
    )
    return cell_lines_by_column, row_height


def truncate_row_layout_to_fit_height(
    composer: _PdfReportComposer,
    *,
    cell_lines_by_column: list[list[str]],
    line_height: float,
    row_padding: float,
    available_height: float,
) -> tuple[list[list[str]], float]:
    max_line_count = max(int((available_height - (2.0 * row_padding)) / line_height), 1)

    truncated_lines_by_column: list[list[str]] = []
    for lines in cell_lines_by_column:
        if len(lines) <= max_line_count:
            truncated_lines_by_column.append(lines)
            continue

        truncated = list(lines[:max_line_count])
        truncated[-1] = textwrap.shorten(
            truncated[-1],
            width=max(len(truncated[-1]) - 3, 3),
            placeholder="...",
        )
        truncated_lines_by_column.append(truncated)

    row_height = (max_line_count * line_height) + (2.0 * row_padding)
    return truncated_lines_by_column, row_height


def draw_table_header(
    composer, *, headers: list[str], column_widths: list[float], height: float
) -> None:
    x_cursor = PAGE_MARGIN
    y = composer.cursor_y - height

    for header, column_width in zip(headers, column_widths, strict=False):
        composer._fill_rect(
            x=x_cursor,
            y=y,
            width=column_width,
            height=height,
            fill_color=COLOR_ACCENT,
            stroke_color=COLOR_LINE,
        )
        lines = composer._wrap_text_to_width(
            text=header, width=column_width - 12.0, font_size=9.0
        )
        text_y = y + height / 2.0 + (len(lines) - 1) * 5.0 - 2.7
        for line in lines:
            composer._draw_text(
                x=x_cursor + 6.0,
                y=text_y,
                text=line,
                font="F2",
                size=9.0,
                color=(1.0, 1.0, 1.0),
            )
            text_y -= 10.0
        x_cursor += column_width

    composer.cursor_y = y


def draw_table_row(
    composer: _PdfReportComposer,
    *,
    row_number: int,
    cell_lines_by_column: list[list[str]],
    column_widths: list[float],
    row_height: float,
    line_height: float,
    font_size: float,
) -> None:
    x_cursor = PAGE_MARGIN
    y = composer.cursor_y - row_height
    row_fill = (1.0, 1.0, 1.0) if row_number % 2 == 0 else COLOR_SURFACE_ALT

    for cell_lines, column_width in zip(
        cell_lines_by_column, column_widths, strict=False
    ):
        composer._fill_rect(
            x=x_cursor,
            y=y,
            width=column_width,
            height=row_height,
            fill_color=row_fill,
            stroke_color=COLOR_LINE,
        )

        text_y = (
            y
            + row_height / 2.0
            + (len(cell_lines) - 1) * line_height / 2.0
            - font_size * 0.3
        )
        for line in cell_lines:
            composer._draw_text(
                x=x_cursor + 6.0,
                y=text_y,
                text=line,
                font="F1",
                size=font_size,
                color=COLOR_INK,
            )
            text_y -= line_height

        x_cursor += column_width

    composer.cursor_y = y
