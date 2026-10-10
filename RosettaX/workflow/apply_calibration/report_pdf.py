"""Composition of the apply report PDF from prepared evidence sections."""

import textwrap
from typing import Any

from . import report_charts, report_tables
from .report_document import (
    _build_pdf_document,
    _escape_pdf_text,
    _PdfPage,
    _rgb,
    _sanitize_text,
)
from .report_helpers import (
    build_fit_evidence_items,
)
from .report_payload import (
    _build_calibration_entries,
    _normalize_string_list,
)
from .report_sections import (
    _build_apply_overview_items,
    _build_calibration_metadata_items,
    _build_chart_spec,
    _build_cover_summary_items,
    _build_fluorescence_fit_items,
    _build_reference_table_spec,
    _build_saved_payload_section_specs,
    _build_scattering_fit_items,
    _build_selected_calibration_rows,
    _build_target_model_items,
)
from .report_styles import (
    COLOR_ACCENT,
    COLOR_ACCENT_ALT,
    COLOR_INK,
    COLOR_LINE,
    COLOR_MUTED,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_WARNING,
    COLOR_WARNING_SOFT,
    CONTENT_WIDTH,
    PAGE_BOTTOM,
    PAGE_HEIGHT,
    PAGE_MARGIN,
    PAGE_WIDTH,
    RUNNING_HEADER_HEIGHT,
)


def build_apply_report_pdf_bytes(
    *,
    report_payload: dict[str, Any],
) -> bytes:
    """Build a styled multi-page PDF report for one apply/export run."""
    composer = _PdfReportComposer(report_payload=report_payload)
    return composer.build_pdf_bytes()


class _PdfReportComposer:
    def __init__(self, *, report_payload: dict[str, Any]) -> None:
        self.report_payload = report_payload
        self.pages: list[_PdfPage] = []
        self.current_page = _PdfPage()
        self.pages.append(self.current_page)
        self.cursor_y = PAGE_HEIGHT - 154.0
        self._draw_cover_header()
        self._draw_status_banner()

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
        self._draw_summary_cards(
            items=_build_cover_summary_items(report_payload=self.report_payload)
        )
        warning_items = _normalize_string_list(
            self.report_payload.get("result", {}).get("warnings")
        )
        self._draw_bullet_box(title="Warnings", items=warning_items or ["None"])
        self._draw_key_value_table(
            title="Run summary",
            items=_build_apply_overview_items(report_payload=self.report_payload),
        )
        calibration_rows = _build_selected_calibration_rows(
            report_payload=self.report_payload,
        )
        if calibration_rows:
            report_tables.draw_table(
                self,
                title="Selected calibrations",
                headers=["File", "Type", "Source channel", "Output quantity"],
                rows=calibration_rows,
                column_weights=[0.34, 0.14, 0.24, 0.28],
            )
        calibration_entries = _build_calibration_entries(
            report_payload=self.report_payload,
        )

        if not calibration_entries:
            calibration_entries = [
                {
                    "display_name": "Calibration",
                    "calibration_type": "",
                }
            ]

        for calibration_index, calibration_entry in enumerate(calibration_entries):
            display_name = str(
                calibration_entry.get("display_name")
                or f"Calibration {calibration_index + 1}"
            )
            calibration_title_suffix = (
                f" ({display_name})" if len(calibration_entries) > 1 else ""
            )

            self._draw_key_value_table(
                title=f"Calibration details{calibration_title_suffix}",
                items=_build_calibration_metadata_items(
                    report_payload=self.report_payload,
                    calibration_index=calibration_index,
                ),
            )

            chart_spec = _build_chart_spec(
                report_payload=self.report_payload,
                calibration_index=calibration_index,
            )
            evidence_items = build_fit_evidence_items(
                details=calibration_entry.get("details", {})
            )
            if evidence_items:
                self._draw_key_value_table(
                    title=f"Calibration evidence{calibration_title_suffix}",
                    items=evidence_items,
                )
            if chart_spec is not None:
                if len(calibration_entries) > 1:
                    chart_spec = dict(chart_spec)
                    chart_spec["title"] = (
                        f"{chart_spec.get('title', 'Calibration chart')} ({display_name})"
                    )
                report_charts.draw_chart(self, chart_spec=chart_spec)

            calibration_type = (
                str(
                    calibration_entry.get("calibration_type") or "",
                )
                .strip()
                .lower()
            )

            if calibration_type == "fluorescence":
                self._draw_key_value_table(
                    title=f"Fit parameters{calibration_title_suffix}",
                    items=_build_fluorescence_fit_items(
                        report_payload=self.report_payload,
                        calibration_index=calibration_index,
                    ),
                )

            if calibration_type == "scattering":
                self._draw_key_value_table(
                    title=f"Instrument response{calibration_title_suffix}",
                    items=_build_scattering_fit_items(
                        report_payload=self.report_payload,
                        calibration_index=calibration_index,
                    ),
                )

            reference_table_spec = _build_reference_table_spec(
                report_payload=self.report_payload,
                calibration_index=calibration_index,
            )
            if reference_table_spec is not None:
                if len(calibration_entries) > 1:
                    reference_table_spec = dict(reference_table_spec)
                    reference_table_spec["title"] = (
                        f"{reference_table_spec.get('title', 'Reference table')} ({display_name})"
                    )
                report_tables.draw_table(
                    self,
                    title=reference_table_spec["title"],
                    headers=reference_table_spec["headers"],
                    rows=reference_table_spec["rows"],
                    column_weights=reference_table_spec["column_weights"],
                )

            for section_spec in _build_saved_payload_section_specs(
                report_payload=self.report_payload,
                calibration_index=calibration_index,
            ):
                section_title = str(section_spec["title"])
                if len(calibration_entries) > 1:
                    section_title = f"{section_title} ({display_name})"
                self._draw_key_value_table(
                    title=section_title,
                    items=section_spec["items"],
                )

        input_file_rows = [
            [file_path]
            for file_path in _normalize_string_list(
                self.report_payload.get("uploaded_fcs_paths")
            )
        ]
        report_tables.draw_table(
            self,
            title="Input FCS files",
            headers=["Uploaded FCS file"],
            rows=input_file_rows or [["None"]],
            column_weights=[1.0],
        )

        target_model_items = _build_target_model_items(
            report_payload=self.report_payload
        )
        if target_model_items:
            self._draw_key_value_table(
                title="Scattering target model",
                items=target_model_items,
            )

    def _draw_cover_header(self) -> None:
        summary = self.report_payload.get("calibration_summary", {})
        calibration_name = ""

        if isinstance(summary, dict):
            calibration_name = str(summary.get("file_name") or "")

        if not calibration_name:
            calibration_name = str(
                self.report_payload.get("selected_calibration") or "Calibration"
            )

        self._fill_rect(
            x=0.0,
            y=PAGE_HEIGHT - 126.0,
            width=PAGE_WIDTH,
            height=126.0,
            fill_color=COLOR_ACCENT,
        )
        self._fill_rect(
            x=0.0,
            y=PAGE_HEIGHT - 126.0,
            width=PAGE_WIDTH,
            height=1.0,
            fill_color=(0.89, 0.94, 0.98),
        )
        self._draw_text(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 44.0,
            text="Apply Calibration Report",
            font="F2",
            size=21.0,
            color=(1.0, 1.0, 1.0),
        )
        self._draw_text_block(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 64.0,
            width=PAGE_WIDTH - (2.0 * PAGE_MARGIN),
            text=calibration_name,
            font="F1",
            size=11.0,
            color=(1.0, 1.0, 1.0),
            leading=13.0,
        )
        self._draw_text(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 101.0,
            text="RosettaX  |  Calibration application summary",
            font="F1",
            size=8.5,
            color=(0.92, 0.96, 0.99),
        )
        self._draw_text(
            x=PAGE_MARGIN,
            y=PAGE_HEIGHT - 116.0,
            text=f"Generated {self.report_payload.get('generated_at', '')}",
            font="F1",
            size=9.0,
            color=(0.92, 0.96, 0.99),
        )

    def _draw_status_banner(self) -> None:
        """Draw a prominent completion state below the report cover."""
        result_payload = self.report_payload.get("result", {})
        if not isinstance(result_payload, dict):
            result_payload = {}

        warnings = _normalize_string_list(result_payload.get("warnings"))
        status = str(result_payload.get("status") or "Run completed.")
        has_warnings = bool(warnings)
        label = "COMPLETED WITH WARNINGS" if has_warnings else "COMPLETED"
        accent = COLOR_WARNING if has_warnings else COLOR_SUCCESS
        fill = COLOR_WARNING_SOFT if has_warnings else COLOR_ACCENT_ALT

        height = 42.0
        self._ensure_space(height + 12.0)
        y = self.cursor_y - height
        self._fill_rect(
            x=PAGE_MARGIN,
            y=y,
            width=CONTENT_WIDTH,
            height=height,
            fill_color=fill,
            stroke_color=accent,
        )
        self._fill_rect(
            x=PAGE_MARGIN,
            y=y,
            width=5.0,
            height=height,
            fill_color=accent,
        )
        self._draw_text(
            x=PAGE_MARGIN + 16.0,
            y=y + height - 16.0,
            text=label,
            font="F2",
            size=9.0,
            color=accent,
        )
        self._draw_text_block(
            x=PAGE_MARGIN + 16.0,
            y=y + height - 30.0,
            width=CONTENT_WIDTH - 28.0,
            text=status,
            font="F1",
            size=8.5,
            color=COLOR_INK,
            leading=10.0,
            max_lines=1,
        )
        self.cursor_y = y - 16.0

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
            text="Apply Calibration Report",
            font="F2",
            size=9.0,
            color=COLOR_MUTED,
        )
        self._draw_text(
            x=PAGE_WIDTH - PAGE_MARGIN - 150.0,
            y=PAGE_HEIGHT - 17.0,
            text=str(self.report_payload.get("generated_at") or ""),
            font="F1",
            size=8.0,
            color=COLOR_MUTED,
        )

    def _draw_page_footer(
        self, *, page: _PdfPage, page_number: int, page_count: int
    ) -> None:
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

    def _draw_key_value_table(
        self, *, title: str, items: list[tuple[str, str]]
    ) -> None:
        if not items:
            return

        report_tables.draw_table(
            self,
            title=title,
            headers=["Field", "Value"],
            rows=[[label, value] for label, value in items],
            column_weights=[0.34, 0.66],
        )

    def _draw_bullet_box(self, *, title: str, items: list[str]) -> None:
        self._draw_section_title(title=title)

        wrapped_lines = [
            self._wrap_text_to_width(
                text=f"- {item}",
                width=CONTENT_WIDTH - 20.0,
                font_size=9.0,
            )
            or ["-"]
            for item in items
        ]

        flat_lines = [line for lines in wrapped_lines for line in lines]
        line_height = 11.0
        line_index = 0

        while line_index < len(flat_lines):
            available_height = self.cursor_y - PAGE_BOTTOM - 8.0
            max_lines_on_page = max(int((available_height - 14.0) / line_height), 1)

            if max_lines_on_page <= 0:
                self._start_new_page()
                self._draw_section_title(title=f"{title} (continued)")
                continue

            next_index = min(line_index + max_lines_on_page, len(flat_lines))
            chunk = flat_lines[line_index:next_index]
            box_height = max(34.0, 14.0 + (len(chunk) * line_height))

            if self.cursor_y - box_height < PAGE_BOTTOM:
                self._start_new_page()
                self._draw_section_title(title=f"{title} (continued)")
                continue

            y = self.cursor_y - box_height
            self._fill_rect(
                x=PAGE_MARGIN,
                y=y,
                width=CONTENT_WIDTH,
                height=box_height,
                fill_color=COLOR_WARNING_SOFT
                if title.lower() == "warnings"
                else COLOR_SURFACE,
                stroke_color=COLOR_LINE,
            )

            text_y = y + box_height - 16.0
            for line in chunk:
                self._draw_text(
                    x=PAGE_MARGIN + 10.0,
                    y=text_y,
                    text=line,
                    font="F1",
                    size=9.0,
                    color=COLOR_WARNING if line != "- None" else COLOR_MUTED,
                )
                text_y -= line_height

            self.cursor_y = y - 10.0
            line_index = next_index

    def _draw_section_title(self, *, title: str) -> None:
        self._ensure_space(34.0)
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
        self.cursor_y -= 24.0

    def _wrap_text_to_width(
        self, *, text: str, width: float, font_size: float
    ) -> list[str]:
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
        max_lines: int | None = None,
    ) -> None:
        lines = self._wrap_text_to_width(text=text, width=width, font_size=size)

        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = textwrap.shorten(
                lines[-1], width=max(len(lines[-1]) - 3, 3), placeholder="..."
            )

        current_y = y
        for line in lines:
            self._draw_text(
                x=x, y=current_y, text=line, font=font, size=size, color=color
            )
            current_y -= leading

    def _fill_rect(
        self,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        fill_color: tuple[float, float, float],
        stroke_color: tuple[float, float, float] | None = None,
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
            f"q {_rgb(color)} RG {line_width:.2f} w {' '.join(commands)} S Q"
        )

    def _fill_circle(
        self,
        *,
        cx: float,
        cy: float,
        radius: float,
        fill_color: tuple[float, float, float],
    ) -> None:
        # Cubic Bezier approximation for a circle.
        kappa = 0.5522847498
        control = radius * kappa

        self.current_page.commands.append(
            "q "
            f"{_rgb(fill_color)} rg "
            f"{cx + radius:.2f} {cy:.2f} m "
            f"{cx + radius:.2f} {cy + control:.2f} {cx + control:.2f} {cy + radius:.2f} {cx:.2f} {cy + radius:.2f} c "
            f"{cx - control:.2f} {cy + radius:.2f} {cx - radius:.2f} {cy + control:.2f} {cx - radius:.2f} {cy:.2f} c "
            f"{cx - radius:.2f} {cy - control:.2f} {cx - control:.2f} {cy - radius:.2f} {cx:.2f} {cy - radius:.2f} c "
            f"{cx + control:.2f} {cy - radius:.2f} {cx + radius:.2f} {cy - control:.2f} {cx + radius:.2f} {cy:.2f} c f Q"
        )
