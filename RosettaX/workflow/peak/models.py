# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PeakConfig:
    """
    Static configuration for one reusable peak section.

    This config describes how a page section wraps the existing generic peak
    workflow.
    """

    header_title: str
    process_dropdown_label: str
    graph_title: str

    table_id: Any = None
    page_state_store_id: Any = None
    max_events_input_id: Any = None
    runtime_config_store_id: str = "runtime-config-store"
    mie_model_input_id: Any = None

    number_of_bins_runtime_config_path: str = "calibration.n_bins_for_plots"
    xscale_runtime_config_path: str = "calibration.histogram_xscale"
    xscale_fallback_runtime_config_path: str = "calibration.xscale"
    yscale_runtime_config_path: str = "calibration.histogram_yscale"
    yscale_fallback_runtime_config_path: str = "calibration.histogram_scale"

    default_number_of_bins: int = 100
    default_xscale: str = "linear"
    default_yscale: str = "log"