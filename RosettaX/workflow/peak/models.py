# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class PeakConfig:
    """
    Static configuration for one reusable peak-detection section.

    This config describes how a page section wraps the generic peak workflow.

    Attributes
    ----------
    header_title : Any
        Title displayed at the top of the peak section card.
    process_dropdown_label : str
        Label shown above the process-selection dropdown.
    graph_title : Any
        Title displayed above the histogram or scatter graph.
    table_id : Any
        Dash component id of the peak table that receives detected peaks.
    page_state_store_id : Any
        Dash store id that holds the serialised page state.
    max_events_input_id : Any
        Dash component id for the maximum-events numeric input.
    runtime_config_store_id : str
        Dash store id for the runtime configuration.
    mie_model_input_id : Any
        Dash component id for the Mie model selector (scattering page only).
    default_process_runtime_config_path : Optional[str]
        Dotted runtime-config path used to persist the selected process name.
    number_of_bins_runtime_config_path : str
        Dotted runtime-config path for the histogram bin count.
    xscale_runtime_config_path : str
        Dotted runtime-config path for the x-axis scale (``"linear"`` or
        ``"log"``).
    xscale_fallback_runtime_config_path : str
        Fallback path used when *xscale_runtime_config_path* returns no value.
    yscale_runtime_config_path : str
        Dotted runtime-config path for the y-axis scale.
    yscale_fallback_runtime_config_path : str
        Fallback path used when *yscale_runtime_config_path* returns no value.
    default_number_of_bins : int
        Default histogram bin count when no runtime value is found.
    default_xscale : str
        Default x-axis scale when no runtime value is found.
    default_yscale : str
        Default y-axis scale when no runtime value is found.
    """

    header_title: Any
    process_dropdown_label: str
    graph_title: Any

    table_id: Any = None
    page_state_store_id: Any = None
    max_events_input_id: Any = None
    runtime_config_store_id: str = "runtime-config-store"
    mie_model_input_id: Any = None

    default_process_runtime_config_path: Optional[str] = None

    number_of_bins_runtime_config_path: str = "visualization.n_bins"
    xscale_runtime_config_path: str = "calibration.histogram_xscale"
    xscale_fallback_runtime_config_path: str = "calibration.xscale"
    yscale_runtime_config_path: str = "calibration.histogram_yscale"
    yscale_fallback_runtime_config_path: str = "calibration.histogram_scale"

    default_number_of_bins: int = 100
    default_xscale: str = "linear"
    default_yscale: str = "log"