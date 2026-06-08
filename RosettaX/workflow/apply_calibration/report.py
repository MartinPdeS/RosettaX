# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from datetime import datetime
import math
from pathlib import Path
import re
import textwrap
from typing import Any, Optional

from .services import ApplyCalibrationFilesResult, ApplyCalibrationRequest


PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0
PAGE_MARGIN = 42.0
CONTENT_WIDTH = PAGE_WIDTH - (2.0 * PAGE_MARGIN)
PAGE_BOTTOM = 44.0
RUNNING_HEADER_HEIGHT = 24.0

COLOR_INK = (0.11, 0.14, 0.18)
COLOR_MUTED = (0.39, 0.44, 0.51)
COLOR_LINE = (0.81, 0.85, 0.89)
COLOR_SURFACE = (0.98, 0.99, 1.00)
COLOR_ACCENT = (0.05, 0.43, 0.61)
COLOR_ACCENT_SOFT = (0.87, 0.94, 0.98)
COLOR_ACCENT_ALT = (0.88, 0.93, 0.90)
COLOR_WARNING = (0.72, 0.41, 0.12)
COLOR_POINT = (0.89, 0.34, 0.19)
COLOR_LINE_SERIES = (0.07, 0.47, 0.73)


def build_apply_report_payload(
    *,
    request: ApplyCalibrationRequest,
    result: ApplyCalibrationFilesResult,
    calibration_summary: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a serializable payload describing one successful apply/export run."""
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request_signature": build_apply_report_request_signature(request=request),
        "selected_calibration": str(request.selected_calibration),
        "calibration_summary": _build_calibration_summary_payload(
            calibration_summary=calibration_summary,
        ),
        "calibration_details": _build_calibration_details_payload(
            calibration_payload=request.calibration_payload,
        ),
        "uploaded_fcs_paths": [str(path) for path in request.uploaded_fcs_paths],
        "export_columns": [str(column) for column in request.export_columns],
        "scattering_target_model_parameters": _build_scattering_target_model_payload(
            request=request,
        ),
        "result": {
            "download_filename": str(result.download_filename),
            "source_channel": str(result.source_channel),
            "output_channels": [str(channel) for channel in result.output_channels],
            "file_count": int(result.file_count),
            "warnings": [str(warning) for warning in result.warnings],
            "status": str(result.status),
            "includes_embedded_report": str(result.download_filename).lower().endswith(".zip"),
        },
    }


def build_apply_report_request_signature(
    *,
    request: ApplyCalibrationRequest,
) -> dict[str, Any]:
    """Build a comparable signature for the current apply request."""
    return {
        "uploaded_fcs_paths": [str(path) for path in request.uploaded_fcs_paths],
        "selected_calibration": str(request.selected_calibration),
        "export_columns": [str(column) for column in request.export_columns],
        "scattering_target_model_parameters": _build_scattering_target_model_payload(
            request=request,
        ),
    }


def apply_report_matches_request(
    *,
    report_payload: Any,
    request: ApplyCalibrationRequest,
) -> bool:
    """Return whether report_payload still matches the current request."""
    if not isinstance(report_payload, dict):
        return False

    return report_payload.get("request_signature") == build_apply_report_request_signature(
        request=request,
    )


def build_apply_report_download_filename(
    *,
    report_payload: dict[str, Any],
) -> str:
    """Build a stable download filename for the PDF report."""
    calibration_summary = report_payload.get("calibration_summary", {})

    if isinstance(calibration_summary, dict):
        calibration_name = calibration_summary.get(
            "file_name",
            report_payload.get("selected_calibration", "calibration"),
        )
    else:
        calibration_name = report_payload.get("selected_calibration", "calibration")

    calibration_stem = Path(str(calibration_name or "calibration")).stem
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", calibration_stem).strip("._")

    if not safe_stem:
        safe_stem = "calibration"

    generated_at = str(report_payload.get("generated_at", ""))
    timestamp = re.sub(r"[^0-9]", "", generated_at)[:14]

    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    return f"rosettax_apply_report_{safe_stem}_{timestamp}.pdf"


def build_apply_report_pdf_bytes(
    *,
    report_payload: dict[str, Any],
) -> bytes:
    """Build a styled multi-page PDF report for one apply/export run."""
    composer = _PdfReportComposer(report_payload=report_payload)
    return composer.build_pdf_bytes()


def _build_calibration_summary_payload(
    *,
    calibration_summary: Optional[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(calibration_summary, dict):
        return {}

    return {
        "selected_calibration": str(calibration_summary.get("selected_calibration", "")),
        "file_name": str(calibration_summary.get("file_name", "")),
        "file_path": str(calibration_summary.get("file_path", "")),
        "calibration_type": str(calibration_summary.get("calibration_type", "")),
        "source_channel": str(calibration_summary.get("source_channel", "")),
        "output_quantity": str(calibration_summary.get("output_quantity", "")),
        "version": calibration_summary.get("version"),
        "requires_target_model": bool(calibration_summary.get("requires_target_model", False)),
    }


def _build_calibration_details_payload(
    *,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(calibration_payload, dict):
        return {}

    calibration_type = str(calibration_payload.get("calibration_type", "")).strip().lower()

    if calibration_type == "fluorescence":
        return _build_fluorescence_calibration_details(calibration_payload=calibration_payload)

    if calibration_type == "scattering":
        return _build_scattering_calibration_details(calibration_payload=calibration_payload)

    return {
        "calibration_type": calibration_type or "unknown",
        "payload_keys": sorted(calibration_payload.keys()),
    }


def _build_fluorescence_calibration_details(
    *,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    fit_metrics = calibration_payload.get("fit_metrics", {})
    parameters = calibration_payload.get("parameters", {})
    nested_payload = calibration_payload.get("payload", {})
    reference_points = calibration_payload.get("reference_points", [])

    return {
        "calibration_type": "fluorescence",
        "schema_version": str(calibration_payload.get("schema_version", "")),
        "source_file": str(calibration_payload.get("source_file") or ""),
        "source_channel": str(calibration_payload.get("source_channel") or ""),
        "gating_channel": str(calibration_payload.get("gating_channel") or ""),
        "gating_threshold": _as_float_or_none(calibration_payload.get("gating_threshold")),
        "fit_model": str(calibration_payload.get("fit_model") or ""),
        "fit_metrics": {
            "r_squared": _as_float_or_none(fit_metrics.get("r_squared")),
            "point_count": _as_int_or_none(fit_metrics.get("point_count")),
        },
        "parameters": {
            "slope": _as_float_or_none(parameters.get("slope")),
            "intercept": _as_float_or_none(parameters.get("intercept")),
            "prefactor": _as_float_or_none(parameters.get("prefactor")),
        },
        "axis_definitions": {
            "x_definition": str(nested_payload.get("x_definition") or ""),
            "y_definition": str(nested_payload.get("y_definition") or ""),
        },
        "reference_points": [
            {
                "reference_value": _as_float_or_none(point.get("reference_value")),
                "measured_value": _as_float_or_none(point.get("measured_value")),
            }
            for point in reference_points
            if isinstance(point, dict)
        ],
    }


def _build_scattering_calibration_details(
    *,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    instrument_response = calibration_payload.get("instrument_response", {})
    metadata = calibration_payload.get("metadata", {})
    reference_table = calibration_payload.get("reference_table", [])

    return {
        "calibration_type": "scattering",
        "version": _as_int_or_none(calibration_payload.get("version")),
        "source_channel": str(calibration_payload.get("source_channel") or ""),
        "output_quantity": str(calibration_payload.get("output_quantity") or ""),
        "instrument_response": {
            "measured_channel": str(instrument_response.get("measured_channel") or ""),
            "slope": _as_float_or_none(instrument_response.get("slope")),
            "intercept": _as_float_or_none(instrument_response.get("intercept")),
            "r_squared": _as_float_or_none(instrument_response.get("r_squared")),
            "force_zero_intercept": bool(instrument_response.get("force_zero_intercept", False)),
            "input_quantity": str(instrument_response.get("input_quantity") or ""),
            "output_quantity": str(instrument_response.get("output_quantity") or ""),
            "model_name": str(instrument_response.get("model_name") or ""),
        },
        "reference_table": [
            {str(key): _sanitize_payload_value(value) for key, value in row.items()}
            for row in reference_table
            if isinstance(row, dict)
        ],
        "metadata": {
            str(key): _sanitize_payload_value(value)
            for key, value in metadata.items()
            if _is_supported_payload_value(value)
        },
    }


def _build_scattering_target_model_payload(
    *,
    request: ApplyCalibrationRequest,
) -> Optional[dict[str, Any]]:
    parameters = request.scattering_target_model_parameters

    if parameters is None:
        return None

    return parameters.to_parameter_payload()


def _sanitize_payload_value(value: Any) -> Any:
    if isinstance(value, (str, bool, int)) or value is None:
        return value

    if isinstance(value, float):
        return float(value)

    if isinstance(value, list):
        return [
            _sanitize_payload_value(item)
            for item in value
            if _is_supported_payload_value(item)
        ]

    return str(value)


def _is_supported_payload_value(value: Any) -> bool:
    return isinstance(value, (str, bool, int, float, list)) or value is None


def _as_float_or_none(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int_or_none(value: Any) -> Optional[int]:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class _PdfPage:
    commands: list[str] = field(default_factory=list)


class _PdfReportComposer:
    def __init__(self, *, report_payload: dict[str, Any]) -> None:
        self.report_payload = report_payload
        self.pages: list[_PdfPage] = []
        self.current_page = _PdfPage()
        self.pages.append(self.current_page)
        self.cursor_y = PAGE_HEIGHT - 154.0
        self._draw_cover_header()

    def build_pdf_bytes(self) -> bytes:
        self._compose_document()

        for page_number, page in enumerate(self.pages, start=1):
            self._draw_page_footer(
                page=page,
                page_number=page_number,
                page_count=len(self.pages),
            )

        return _build_pdf_document(pages=self.pages)

    def _compose_document(self) -> None:
        self._draw_summary_cards(items=_build_cover_summary_items(report_payload=self.report_payload))
        self._draw_key_value_table(
            title="Apply overview",
            items=_build_apply_overview_items(report_payload=self.report_payload),
        )
        self._draw_key_value_table(
            title="Calibration metadata",
            items=_build_calibration_metadata_items(report_payload=self.report_payload),
        )

        chart_spec = _build_chart_spec(report_payload=self.report_payload)
        if chart_spec is not None:
            self._draw_chart(chart_spec=chart_spec)

        calibration_type = str(
            self.report_payload.get("calibration_summary", {}).get("calibration_type", ""),
        ).strip().lower()

        if calibration_type == "fluorescence":
            self._draw_key_value_table(
                title="Fit parameters",
                items=_build_fluorescence_fit_items(report_payload=self.report_payload),
            )

        if calibration_type == "scattering":
            self._draw_key_value_table(
                title="Instrument response",
                items=_build_scattering_fit_items(report_payload=self.report_payload),
            )

        target_model_items = _build_target_model_items(report_payload=self.report_payload)
        if target_model_items:
            self._draw_key_value_table(
                title="Scattering target model",
                items=target_model_items,
            )

        input_file_rows = [[file_path] for file_path in _normalize_string_list(self.report_payload.get("uploaded_fcs_paths"))]
        self._draw_table(
            title="Input files",
            headers=["Uploaded FCS file"],
            rows=input_file_rows or [["None"]],
            column_weights=[1.0],
        )

        reference_table_spec = _build_reference_table_spec(report_payload=self.report_payload)
        if reference_table_spec is not None:
            self._draw_table(
                title=reference_table_spec["title"],
                headers=reference_table_spec["headers"],
                rows=reference_table_spec["rows"],
                column_weights=reference_table_spec["column_weights"],
            )

        warning_items = _normalize_string_list(self.report_payload.get("result", {}).get("warnings"))
        self._draw_bullet_box(title="Warnings", items=warning_items or ["None"])

    def _draw_cover_header(self) -> None:
        summary = self.report_payload.get("calibration_summary", {})
        calibration_name = ""

        if isinstance(summary, dict):
            calibration_name = str(summary.get("file_name") or "")

        if not calibration_name:
            calibration_name = str(self.report_payload.get("selected_calibration") or "Calibration")

        self._fill_rect(
            x=0.0,
            y=PAGE_HEIGHT - 118.0,
            width=PAGE_WIDTH,
            height=118.0,
            fill_color=COLOR_ACCENT,
        )
        self._fill_rect(
            x=PAGE_WIDTH - 148.0,
            y=PAGE_HEIGHT - 118.0,
            width=148.0,
            height=118.0,
            fill_color=COLOR_ACCENT_ALT,
        )
        self._draw_text(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 52.0,
            text="RosettaX Apply Calibration Report",
            font="F2",
            size=22.0,
            color=(1.0, 1.0, 1.0),
        )
        self._draw_text_block(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 76.0,
            width=PAGE_WIDTH - (2.0 * PAGE_MARGIN) - 120.0,
            text=calibration_name,
            font="F1",
            size=11.0,
            color=(1.0, 1.0, 1.0),
            leading=13.0,
        )
        self._draw_text(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 99.0,
            text=f"Generated {self.report_payload.get('generated_at', '')}",
            font="F1",
            size=9.0,
            color=(0.92, 0.96, 0.99),
        )

    def _draw_running_header(self) -> None:
        self._fill_rect(
            x=0.0,
            y=PAGE_HEIGHT - RUNNING_HEADER_HEIGHT,
            width=PAGE_WIDTH,
            height=RUNNING_HEADER_HEIGHT,
            fill_color=COLOR_SURFACE,
        )
        self._draw_line(
            x1=0.0,
            y1=PAGE_HEIGHT - RUNNING_HEADER_HEIGHT,
            x2=PAGE_WIDTH,
            y2=PAGE_HEIGHT - RUNNING_HEADER_HEIGHT,
            color=COLOR_LINE,
            line_width=0.8,
        )
        self._draw_text(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 17.0,
            text="RosettaX Apply Calibration Report",
            font="F2",
            size=9.0,
            color=COLOR_MUTED,
        )

    def _draw_page_footer(self, *, page: _PdfPage, page_number: int, page_count: int) -> None:
        self._draw_text_on_page(
            page=page,
            x=PAGE_MARGIN,
            y=20.0,
            text=f"Page {page_number} of {page_count}",
            font="F1",
            size=8.0,
            color=COLOR_MUTED,
        )

    def _start_new_page(self) -> None:
        self.current_page = _PdfPage()
        self.pages.append(self.current_page)
        self.cursor_y = PAGE_HEIGHT - 56.0
        self._draw_running_header()

    def _ensure_space(self, height: float) -> None:
        if self.cursor_y - height < PAGE_BOTTOM:
            self._start_new_page()

    def _draw_summary_cards(self, *, items: list[tuple[str, str]]) -> None:
        if not items:
            return

        card_height = 58.0
        gap = 12.0
        card_width = (CONTENT_WIDTH - (gap * (len(items) - 1))) / float(len(items))
        self._ensure_space(card_height + 8.0)

        x_cursor = PAGE_MARGIN
        y = self.cursor_y - card_height

        for label, value in items:
            self._fill_rect(
                x=x_cursor,
                y=y,
                width=card_width,
                height=card_height,
                fill_color=COLOR_SURFACE,
                stroke_color=COLOR_LINE,
            )
            self._draw_text(
                x=x_cursor + 10.0,
                y=y + card_height - 16.0,
                text=label,
                font="F1",
                size=8.0,
                color=COLOR_MUTED,
            )
            self._draw_text_block(
                x=x_cursor + 10.0,
                y=y + card_height - 31.0,
                width=card_width - 20.0,
                text=value,
                font="F2",
                size=12.0,
                color=COLOR_INK,
                leading=13.0,
                max_lines=2,
            )
            x_cursor += card_width + gap

        self.cursor_y = y - 18.0

    def _draw_key_value_table(self, *, title: str, items: list[tuple[str, str]]) -> None:
        if not items:
            return

        self._draw_table(
            title=title,
            headers=["Field", "Value"],
            rows=[[label, value] for label, value in items],
            column_weights=[0.34, 0.66],
        )

    def _draw_table(
        self,
        *,
        title: str,
        headers: list[str],
        rows: list[list[Any]],
        column_weights: list[float],
    ) -> None:
        if not headers:
            return

        self._draw_section_title(title=title)

        weights_total = sum(column_weights) or float(len(headers))
        column_widths = [CONTENT_WIDTH * (weight / weights_total) for weight in column_weights]
        header_height = 22.0
        font_size = 9.0
        line_height = 11.0
        row_padding = 7.0
        row_index = 0

        while row_index < len(rows):
            self._ensure_space(header_height + 26.0)
            self._draw_table_header(headers=headers, column_widths=column_widths, height=header_height)

            while row_index < len(rows):
                cell_lines_by_column = []
                for value, column_width in zip(rows[row_index], column_widths, strict=False):
                    cell_lines_by_column.append(
                        self._wrap_text_to_width(
                            text=_format_display_value(value),
                            width=column_width - 12.0,
                            font_size=font_size,
                        ) or [""],
                    )

                row_height = (max(len(lines) for lines in cell_lines_by_column) * line_height) + (2.0 * row_padding)

                if self.cursor_y - row_height < PAGE_BOTTOM:
                    self._start_new_page()
                    self._draw_section_title(title=f"{title} (continued)")
                    break

                self._draw_table_row(
                    row_number=row_index,
                    cell_lines_by_column=cell_lines_by_column,
                    column_widths=column_widths,
                    row_height=row_height,
                    line_height=line_height,
                    font_size=font_size,
                    padding=row_padding,
                )
                row_index += 1

            if row_index >= len(rows):
                self.cursor_y -= 8.0

    def _draw_table_header(self, *, headers: list[str], column_widths: list[float], height: float) -> None:
        x_cursor = PAGE_MARGIN
        y = self.cursor_y - height

        for header, column_width in zip(headers, column_widths, strict=False):
            self._fill_rect(
                x=x_cursor,
                y=y,
                width=column_width,
                height=height,
                fill_color=COLOR_ACCENT_SOFT,
                stroke_color=COLOR_LINE,
            )
            self._draw_text_block(
                x=x_cursor + 6.0,
                y=y + height - 8.0,
                width=column_width - 12.0,
                text=header,
                font="F2",
                size=9.0,
                color=COLOR_INK,
                leading=10.0,
                max_lines=2,
            )
            x_cursor += column_width

        self.cursor_y = y

    def _draw_table_row(
        self,
        *,
        row_number: int,
        cell_lines_by_column: list[list[str]],
        column_widths: list[float],
        row_height: float,
        line_height: float,
        font_size: float,
        padding: float,
    ) -> None:
        x_cursor = PAGE_MARGIN
        y = self.cursor_y - row_height
        row_fill = COLOR_SURFACE if row_number % 2 == 0 else (1.0, 1.0, 1.0)

        for cell_lines, column_width in zip(cell_lines_by_column, column_widths, strict=False):
            self._fill_rect(
                x=x_cursor,
                y=y,
                width=column_width,
                height=row_height,
                fill_color=row_fill,
                stroke_color=COLOR_LINE,
            )

            text_y = y + row_height - padding - font_size
            for line in cell_lines:
                self._draw_text(
                    x=x_cursor + 6.0,
                    y=text_y,
                    text=line,
                    font="F1",
                    size=font_size,
                    color=COLOR_INK,
                )
                text_y -= line_height

            x_cursor += column_width

        self.cursor_y = y

    def _draw_chart(self, *, chart_spec: dict[str, Any]) -> None:
        self._draw_section_title(title=str(chart_spec.get("title") or "Calibration plot"))
        plot_height = 214.0
        self._ensure_space(plot_height + 18.0)

        plot_x = PAGE_MARGIN
        plot_y = self.cursor_y - plot_height
        plot_width = CONTENT_WIDTH
        inner_x = plot_x + 44.0
        inner_y = plot_y + 34.0
        inner_width = plot_width - 58.0
        inner_height = plot_height - 58.0

        self._fill_rect(
            x=plot_x,
            y=plot_y,
            width=plot_width,
            height=plot_height,
            fill_color=(1.0, 1.0, 1.0),
            stroke_color=COLOR_LINE,
        )
        self._draw_text(
            x=plot_x + 12.0,
            y=plot_y + plot_height - 18.0,
            text=str(chart_spec.get("subtitle") or ""),
            font="F1",
            size=8.5,
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
            self._draw_line(
                x1=inner_x,
                y1=y_value,
                x2=inner_x + inner_width,
                y2=y_value,
                color=COLOR_LINE,
                line_width=0.6,
            )
            self._draw_line(
                x1=x_value,
                y1=inner_y,
                x2=x_value,
                y2=inner_y + inner_height,
                color=COLOR_LINE,
                line_width=0.6,
            )

        self._draw_line(
            x1=inner_x,
            y1=inner_y,
            x2=inner_x + inner_width,
            y2=inner_y,
            color=COLOR_INK,
            line_width=1.1,
        )
        self._draw_line(
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
            self._draw_polyline(points=polyline_points, color=COLOR_LINE_SERIES, line_width=1.8)

        for point_x, point_y in transformed_points:
            marker_x = _project_value(point_x, x_min, x_max, inner_x, inner_width) - 2.2
            marker_y = _project_value(point_y, y_min, y_max, inner_y, inner_height) - 2.2
            self._fill_rect(x=marker_x, y=marker_y, width=4.4, height=4.4, fill_color=COLOR_POINT)

        log_x = bool(chart_spec.get("log_x", False))
        log_y = bool(chart_spec.get("log_y", False))
        self._draw_text(
            x=inner_x,
            y=plot_y + 10.0,
            text=str(chart_spec.get("x_label") or ""),
            font="F1",
            size=8.0,
            color=COLOR_MUTED,
        )
        self._draw_text(
            x=plot_x + 12.0,
            y=plot_y + plot_height - 31.0,
            text=f"Y: {chart_spec.get('y_label') or ''}",
            font="F1",
            size=8.0,
            color=COLOR_MUTED,
        )
        self._draw_text(
            x=inner_x,
            y=inner_y - 14.0,
            text=_format_display_value(_inverse_transform_value(x_min, log_x)),
            font="F1",
            size=7.5,
            color=COLOR_MUTED,
        )
        self._draw_text(
            x=inner_x + inner_width - 30.0,
            y=inner_y - 14.0,
            text=_format_display_value(_inverse_transform_value(x_max, log_x)),
            font="F1",
            size=7.5,
            color=COLOR_MUTED,
        )
        self._draw_text(
            x=plot_x + 4.0,
            y=inner_y - 2.0,
            text=_format_display_value(_inverse_transform_value(y_min, log_y)),
            font="F1",
            size=7.5,
            color=COLOR_MUTED,
        )
        self._draw_text(
            x=plot_x + 4.0,
            y=inner_y + inner_height - 2.0,
            text=_format_display_value(_inverse_transform_value(y_max, log_y)),
            font="F1",
            size=7.5,
            color=COLOR_MUTED,
        )

        self.cursor_y = plot_y - 16.0

    def _draw_bullet_box(self, *, title: str, items: list[str]) -> None:
        self._draw_section_title(title=title)

        wrapped_lines = [
            self._wrap_text_to_width(
                text=f"- {item}",
                width=CONTENT_WIDTH - 20.0,
                font_size=9.0,
            ) or ["-"]
            for item in items
        ]

        box_height = max(34.0, 14.0 + (sum(len(lines) for lines in wrapped_lines) * 11.0))
        self._ensure_space(box_height)

        y = self.cursor_y - box_height
        self._fill_rect(
            x=PAGE_MARGIN,
            y=y,
            width=CONTENT_WIDTH,
            height=box_height,
            fill_color=COLOR_SURFACE,
            stroke_color=COLOR_LINE,
        )

        text_y = y + box_height - 16.0
        for lines in wrapped_lines:
            for line in lines:
                self._draw_text(
                    x=PAGE_MARGIN + 10.0,
                    y=text_y,
                    text=line,
                    font="F1",
                    size=9.0,
                    color=COLOR_WARNING if line != "- None" else COLOR_MUTED,
                )
                text_y -= 11.0

        self.cursor_y = y - 10.0

    def _draw_section_title(self, *, title: str) -> None:
        self._ensure_space(28.0)
        self._draw_text(
            x=PAGE_MARGIN,
            y=self.cursor_y,
            text=title,
            font="F2",
            size=13.0,
            color=COLOR_INK,
        )
        self._draw_line(
            x1=PAGE_MARGIN,
            y1=self.cursor_y - 6.0,
            x2=PAGE_MARGIN + 120.0,
            y2=self.cursor_y - 6.0,
            color=COLOR_ACCENT,
            line_width=1.2,
        )
        self.cursor_y -= 20.0

    def _wrap_text_to_width(self, *, text: str, width: float, font_size: float) -> list[str]:
        approximate_character_width = max(font_size * 0.54, 1.0)
        character_limit = max(int(width / approximate_character_width), 1)
        wrapped_lines: list[str] = []

        for paragraph in _sanitize_text(text).splitlines() or [""]:
            if not paragraph:
                wrapped_lines.append("")
                continue

            wrapped_lines.extend(
                textwrap.wrap(
                    paragraph,
                    width=character_limit,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
            )

        return wrapped_lines or [""]

    def _draw_text(
        self,
        *,
        x: float,
        y: float,
        text: str,
        font: str,
        size: float,
        color: tuple[float, float, float],
    ) -> None:
        self._draw_text_on_page(
            page=self.current_page,
            x=x,
            y=y,
            text=text,
            font=font,
            size=size,
            color=color,
        )

    def _draw_text_on_page(
        self,
        *,
        page: _PdfPage,
        x: float,
        y: float,
        text: str,
        font: str,
        size: float,
        color: tuple[float, float, float],
    ) -> None:
        escaped = _escape_pdf_text(_sanitize_text(text))
        page.commands.append(
            "BT "
            f"/{font} {size:.2f} Tf "
            f"{_rgb(color)} rg "
            f"1 0 0 1 {x:.2f} {y:.2f} Tm "
            f"({escaped}) Tj ET"
        )

    def _draw_text_block(
        self,
        *,
        x: float,
        y: float,
        width: float,
        text: str,
        font: str,
        size: float,
        color: tuple[float, float, float],
        leading: float,
        max_lines: Optional[int] = None,
    ) -> None:
        lines = self._wrap_text_to_width(text=text, width=width, font_size=size)

        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = textwrap.shorten(lines[-1], width=max(len(lines[-1]) - 3, 3), placeholder="...")

        current_y = y
        for line in lines:
            self._draw_text(x=x, y=current_y, text=line, font=font, size=size, color=color)
            current_y -= leading

    def _fill_rect(
        self,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        fill_color: tuple[float, float, float],
        stroke_color: Optional[tuple[float, float, float]] = None,
    ) -> None:
        if stroke_color is None:
            self.current_page.commands.append(
                "q "
                f"{_rgb(fill_color)} rg "
                f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re f Q"
            )
            return

        self.current_page.commands.append(
            "q "
            f"{_rgb(fill_color)} rg "
            f"{_rgb(stroke_color)} RG "
            f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re B Q"
        )

    def _draw_line(
        self,
        *,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: tuple[float, float, float],
        line_width: float,
    ) -> None:
        self.current_page.commands.append(
            "q "
            f"{_rgb(color)} RG "
            f"{line_width:.2f} w "
            f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q"
        )

    def _draw_polyline(
        self,
        *,
        points: list[tuple[float, float]],
        color: tuple[float, float, float],
        line_width: float,
    ) -> None:
        if len(points) < 2:
            return

        commands = [f"{points[0][0]:.2f} {points[0][1]:.2f} m"]
        for point_x, point_y in points[1:]:
            commands.append(f"{point_x:.2f} {point_y:.2f} l")

        self.current_page.commands.append(
            "q "
            f"{_rgb(color)} RG "
            f"{line_width:.2f} w "
            f"{' '.join(commands)} S Q"
        )


def _build_cover_summary_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    summary = report_payload.get("calibration_summary", {})
    result_payload = report_payload.get("result", {})

    calibration_type = "unknown"
    if isinstance(summary, dict):
        calibration_type = str(summary.get("calibration_type") or "unknown").capitalize()

    file_count = 0
    if isinstance(result_payload, dict):
        file_count = int(result_payload.get("file_count") or 0)

    output_channels = _normalize_string_list(
        result_payload.get("output_channels") if isinstance(result_payload, dict) else None,
    )
    artifact_name = str(
        result_payload.get("download_filename") if isinstance(result_payload, dict) else "",
    ) or "n/a"

    return [
        ("Calibration type", calibration_type),
        ("Input files", str(file_count)),
        ("Output channels", ", ".join(output_channels) if output_channels else artifact_name),
    ]


def _build_apply_overview_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    result_payload = report_payload.get("result", {})

    if not isinstance(result_payload, dict):
        result_payload = {}

    return [
        ("Generated at", str(report_payload.get("generated_at") or "n/a")),
        ("Selected calibration", str(report_payload.get("selected_calibration") or "n/a")),
        ("Download artifact", str(result_payload.get("download_filename") or "n/a")),
        ("Output channels", ", ".join(_normalize_string_list(result_payload.get("output_channels"))) or "None"),
        ("Extra exported columns", ", ".join(_normalize_string_list(report_payload.get("export_columns"))) or "None"),
        ("ZIP includes PDF", "Yes" if bool(result_payload.get("includes_embedded_report")) else "No"),
        ("Status", str(result_payload.get("status") or "n/a")),
        ("Warnings", str(len(_normalize_string_list(result_payload.get("warnings"))))),
    ]


def _build_calibration_metadata_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    summary = report_payload.get("calibration_summary", {})
    details = report_payload.get("calibration_details", {})

    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(details, dict):
        details = {}

    items = [
        ("Calibration file", str(summary.get("file_name") or report_payload.get("selected_calibration") or "n/a")),
        ("Calibration type", str(summary.get("calibration_type") or "unknown")),
        ("Source channel", str(summary.get("source_channel") or details.get("source_channel") or "n/a")),
        ("Output quantity", str(summary.get("output_quantity") or details.get("output_quantity") or "n/a")),
        ("Version", _format_display_value(summary.get("version"))),
    ]

    if details.get("calibration_type") == "fluorescence":
        items.extend(
            [
                ("Source bead file", str(details.get("source_file") or "n/a")),
                ("Gating channel", str(details.get("gating_channel") or "n/a")),
                ("Gating threshold", _format_display_value(details.get("gating_threshold"))),
                ("Fit model", str(details.get("fit_model") or "n/a")),
            ]
        )
    elif details.get("calibration_type") == "scattering":
        metadata = details.get("metadata", {})
        if isinstance(metadata, dict):
            for key in (
                "measured_channel",
                "detector_configuration_preset_name",
                "mie_model",
                "wavelength_nm",
            ):
                if key in metadata:
                    items.append((_prettify_label(key), _format_display_value(metadata.get(key))))

    file_path = str(summary.get("file_path") or "").strip()
    if file_path:
        items.append(("Calibration path", file_path))

    return items


def _build_fluorescence_fit_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    details = report_payload.get("calibration_details", {})

    if not isinstance(details, dict):
        return []

    fit_metrics = details.get("fit_metrics", {})
    parameters = details.get("parameters", {})
    axis_definitions = details.get("axis_definitions", {})

    if not isinstance(fit_metrics, dict):
        fit_metrics = {}
    if not isinstance(parameters, dict):
        parameters = {}
    if not isinstance(axis_definitions, dict):
        axis_definitions = {}

    return [
        ("Slope", _format_display_value(parameters.get("slope"))),
        ("Intercept", _format_display_value(parameters.get("intercept"))),
        ("Prefactor", _format_display_value(parameters.get("prefactor"))),
        ("R squared", _format_display_value(fit_metrics.get("r_squared"))),
        ("Point count", _format_display_value(fit_metrics.get("point_count"))),
        ("X definition", str(axis_definitions.get("x_definition") or "n/a")),
        ("Y definition", str(axis_definitions.get("y_definition") or "n/a")),
    ]


def _build_scattering_fit_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    details = report_payload.get("calibration_details", {})

    if not isinstance(details, dict):
        return []

    instrument_response = details.get("instrument_response", {})

    if not isinstance(instrument_response, dict):
        return []

    return [
        ("Measured channel", _format_display_value(instrument_response.get("measured_channel"))),
        ("Slope", _format_display_value(instrument_response.get("slope"))),
        ("Intercept", _format_display_value(instrument_response.get("intercept"))),
        ("R squared", _format_display_value(instrument_response.get("r_squared"))),
        ("Input quantity", _format_display_value(instrument_response.get("input_quantity"))),
        ("Output quantity", _format_display_value(instrument_response.get("output_quantity"))),
        ("Model name", _format_display_value(instrument_response.get("model_name"))),
        ("Force zero intercept", "Yes" if bool(instrument_response.get("force_zero_intercept")) else "No"),
    ]


def _build_target_model_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    payload = report_payload.get("scattering_target_model_parameters", None)

    if not isinstance(payload, dict):
        return []

    return [(_prettify_label(key), _format_display_value(value)) for key, value in payload.items()]


def _build_reference_table_spec(
    *,
    report_payload: dict[str, Any],
) -> Optional[dict[str, Any]]:
    details = report_payload.get("calibration_details", {})

    if not isinstance(details, dict):
        return None

    calibration_type = str(details.get("calibration_type") or "").strip().lower()

    if calibration_type == "fluorescence":
        rows = []
        for index, point in enumerate(details.get("reference_points", []), start=1):
            if not isinstance(point, dict):
                continue
            rows.append([
                index,
                _format_display_value(point.get("reference_value")),
                _format_display_value(point.get("measured_value")),
            ])

        return {
            "title": "MESF and peak positions",
            "headers": ["Point", "Reference value", "Measured peak position"],
            "rows": rows or [["-", "None", "None"]],
            "column_weights": [0.14, 0.36, 0.50],
        }

    if calibration_type == "scattering":
        reference_table = details.get("reference_table", [])
        if not isinstance(reference_table, list):
            return None

        preferred_columns = [
            "measured_peak_position",
            "particle_diameter_nm",
            "core_diameter_nm",
            "shell_thickness_nm",
            "outer_diameter_nm",
        ]
        present_columns = [
            column_name
            for column_name in preferred_columns
            if any(
                isinstance(row, dict) and row.get(column_name) not in (None, "")
                for row in reference_table
            )
        ]

        if not present_columns and reference_table and isinstance(reference_table[0], dict):
            present_columns = list(reference_table[0].keys())[:5]

        if not present_columns:
            return None

        rows = []
        for row in reference_table:
            if not isinstance(row, dict):
                continue
            rows.append([_format_display_value(row.get(column_name)) for column_name in present_columns])

        return {
            "title": "Scattering reference standards",
            "headers": [_prettify_label(column_name) for column_name in present_columns],
            "rows": rows or [["None"] * len(present_columns)],
            "column_weights": [1.0] * len(present_columns),
        }

    return None


def _build_chart_spec(
    *,
    report_payload: dict[str, Any],
) -> Optional[dict[str, Any]]:
    details = report_payload.get("calibration_details", {})

    if not isinstance(details, dict):
        return None

    calibration_type = str(details.get("calibration_type") or "").strip().lower()

    if calibration_type == "fluorescence":
        points = [point for point in details.get("reference_points", []) if isinstance(point, dict)]
        x_values: list[float] = []
        y_values: list[float] = []

        for point in points:
            measured_value = _as_float_or_none(point.get("measured_value"))
            reference_value = _as_float_or_none(point.get("reference_value"))
            if measured_value is None or reference_value is None:
                continue
            if measured_value <= 0.0 or reference_value <= 0.0:
                continue
            x_values.append(measured_value)
            y_values.append(reference_value)

        if not x_values or not y_values:
            return None

        line_x_values: list[float] = []
        line_y_values: list[float] = []
        parameters = details.get("parameters", {})

        if isinstance(parameters, dict):
            slope = _as_float_or_none(parameters.get("slope"))
            intercept = _as_float_or_none(parameters.get("intercept"))

            if slope is not None and intercept is not None:
                log_x_min = math.log10(min(x_values))
                log_x_max = math.log10(max(x_values))
                for index in range(60):
                    fraction = index / 59.0
                    current_x = 10.0 ** (log_x_min + ((log_x_max - log_x_min) * fraction))
                    current_y = (10.0 ** intercept) * (current_x ** slope)
                    line_x_values.append(current_x)
                    line_y_values.append(current_y)

        return {
            "title": "Fluorescence calibration fit",
            "subtitle": "Measured peak positions against saved reference values.",
            "x_label": "Measured peak position",
            "y_label": "Reference value",
            "x_values": x_values,
            "y_values": y_values,
            "line_x_values": line_x_values,
            "line_y_values": line_y_values,
            "log_x": True,
            "log_y": True,
        }

    if calibration_type == "scattering":
        reference_table = details.get("reference_table", [])
        if not isinstance(reference_table, list):
            return None

        y_key = None
        for candidate in ("particle_diameter_nm", "outer_diameter_nm", "core_diameter_nm"):
            if any(isinstance(row, dict) and row.get(candidate) not in (None, "") for row in reference_table):
                y_key = candidate
                break

        x_values: list[float] = []
        y_values: list[float] = []
        for row in reference_table:
            if not isinstance(row, dict):
                continue
            x_value = _as_float_or_none(row.get("measured_peak_position"))
            y_value = _as_float_or_none(row.get(y_key)) if y_key is not None else None
            if x_value is None or y_value is None:
                continue
            x_values.append(x_value)
            y_values.append(y_value)

        if not x_values or not y_values:
            return None

        paired_points = sorted(zip(x_values, y_values, strict=False), key=lambda point: point[0])

        return {
            "title": "Scattering calibration standards",
            "subtitle": "Saved standard peaks used to fit the scattering calibration.",
            "x_label": "Measured peak position",
            "y_label": _prettify_label(y_key or "reference_value"),
            "x_values": [point[0] for point in paired_points],
            "y_values": [point[1] for point in paired_points],
            "line_x_values": [point[0] for point in paired_points],
            "line_y_values": [point[1] for point in paired_points],
            "log_x": False,
            "log_y": False,
        }

    return None


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

        transformed_points.append((math.log10(x_float) if log_x else x_float, math.log10(y_float) if log_y else y_float))

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


def _project_value(value: float, minimum: float, maximum: float, plot_origin: float, plot_size: float) -> float:
    if maximum == minimum:
        return plot_origin + (plot_size / 2.0)

    fraction = (value - minimum) / (maximum - minimum)
    return plot_origin + (fraction * plot_size)


def _inverse_transform_value(value: float, log_axis: bool) -> float:
    if log_axis:
        return 10.0 ** value

    return value


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item) for item in value]


def _format_display_value(value: Any) -> str:
    if value in (None, ""):
        return "n/a"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if value == 0.0:
            return "0"
        if abs(value) >= 1000.0 or abs(value) < 0.01:
            return f"{value:.4e}"
        return f"{value:.6g}"

    if isinstance(value, list):
        return ", ".join(_format_display_value(item) for item in value) or "n/a"

    return str(value)


def _prettify_label(value: str) -> str:
    label = str(value).replace("_", " ").strip()

    if not label:
        return "Value"

    return label.capitalize()


def _build_pdf_document(*, pages: list[_PdfPage]) -> bytes:
    catalog_object_id = 1
    pages_object_id = 2
    font_regular_object_id = 3
    font_bold_object_id = 4

    next_object_id = 5
    page_object_ids: list[int] = []
    content_object_ids: list[int] = []
    content_streams: list[bytes] = []

    for page in pages:
        page_object_ids.append(next_object_id)
        next_object_id += 1
        content_object_ids.append(next_object_id)
        next_object_id += 1
        content_streams.append(_build_page_content_stream(page=page))

    kids_text = " ".join(f"{page_object_id} 0 R" for page_object_id in page_object_ids)

    objects: list[bytes] = [
        _format_pdf_object(catalog_object_id, f"<< /Type /Catalog /Pages {pages_object_id} 0 R >>".encode("latin-1")),
        _format_pdf_object(pages_object_id, f"<< /Type /Pages /Count {len(page_object_ids)} /Kids [{kids_text}] >>".encode("latin-1")),
        _format_pdf_object(font_regular_object_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        _format_pdf_object(font_bold_object_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"),
    ]

    for page_object_id, content_object_id, content_stream in zip(page_object_ids, content_object_ids, content_streams, strict=False):
        page_body = (
            f"<< /Type /Page /Parent {pages_object_id} 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH:.0f} {PAGE_HEIGHT:.0f}] "
            f"/Resources << /Font << /F1 {font_regular_object_id} 0 R /F2 {font_bold_object_id} 0 R >> >> "
            f"/Contents {content_object_id} 0 R >>"
        ).encode("latin-1")
        content_body = b"<< /Length " + str(len(content_stream)).encode("ascii") + b" >>\nstream\n" + content_stream + b"\nendstream"
        objects.append(_format_pdf_object(page_object_id, page_body))
        objects.append(_format_pdf_object(content_object_id, content_body))

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    payload = bytearray(header)
    offsets = [0]

    for object_bytes in objects:
        offsets.append(len(payload))
        payload.extend(object_bytes)

    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    payload.extend((
        f"trailer\n<< /Size {len(offsets)} /Root {catalog_object_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii"))

    return bytes(payload)


def _build_page_content_stream(*, page: _PdfPage) -> bytes:
    return "\n".join(page.commands).encode("latin-1")


def _format_pdf_object(object_id: int, body: bytes) -> bytes:
    return str(object_id).encode("ascii") + b" 0 obj\n" + body + b"\nendobj\n"


def _rgb(color: tuple[float, float, float]) -> str:
    return " ".join(f"{channel:.3f}" for channel in color)


def _sanitize_text(value: str) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
