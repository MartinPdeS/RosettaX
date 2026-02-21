from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from RosettaX.backend import BackEnd


@dataclass(frozen=True)
class ChannelOptions:
    scatter_options: list[dict[str, str]]
    fluorescence_options: list[dict[str, str]]
    scatter_value: Optional[str]
    fluorescence_value: Optional[str]


class FileStateRefresher:
    def __init__(self, *, scatter_keywords: list[str], non_valid_keywords: list[str]) -> None:
        self.scatter_keywords = [str(k).lower() for k in scatter_keywords]
        self.non_valid_keywords = [str(k).lower() for k in non_valid_keywords]

    def options_from_file(
        self,
        file_path: str,
        *,
        preferred_scatter: Optional[str] = None,
        preferred_fluorescence: Optional[str] = None,
    ) -> ChannelOptions:
        backend = BackEnd(file_path)
        columns = list(getattr(backend.fcs_file, "data").columns)

        scatter_options: list[dict[str, str]] = []
        fluorescence_options: list[dict[str, str]] = []

        for column in columns:
            lower = str(column).strip().lower()
            is_scatter = any(keyword in lower for keyword in self.scatter_keywords)
            is_invalid = any(keyword in lower for keyword in self.non_valid_keywords)

            if is_scatter:
                scatter_options.append({"label": str(column), "value": str(column)})
            elif not is_invalid:
                fluorescence_options.append({"label": str(column), "value": str(column)})

        scatter_value = None
        fluorescence_value = None

        preferred_scatter = str(preferred_scatter or "").strip()
        preferred_fluorescence = str(preferred_fluorescence or "").strip()

        if preferred_scatter and any(o["value"] == preferred_scatter for o in scatter_options):
            scatter_value = preferred_scatter
        elif scatter_options:
            scatter_value = scatter_options[0]["value"]

        if preferred_fluorescence and any(o["value"] == preferred_fluorescence for o in fluorescence_options):
            fluorescence_value = preferred_fluorescence
        elif fluorescence_options:
            fluorescence_value = fluorescence_options[0]["value"]

        return ChannelOptions(
            scatter_options=scatter_options,
            fluorescence_options=fluorescence_options,
            scatter_value=scatter_value,
            fluorescence_value=fluorescence_value,
        )


class CalibrationSetupStore:
    @staticmethod
    def save_fluorescent_setup(sidebar_data: Optional[dict[str, Any]], *, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        next_sidebar = dict(sidebar_data or {})
        next_sidebar.setdefault("Fluorescent", [])
        next_sidebar.setdefault("Scatter", [])
        next_sidebar.setdefault("payloads", {})

        next_sidebar["Fluorescent"] = list(next_sidebar["Fluorescent"])
        if name not in next_sidebar["Fluorescent"]:
            next_sidebar["Fluorescent"].append(name)

        next_sidebar["payloads"][f"Fluorescent/{name}"] = dict(payload)
        return next_sidebar