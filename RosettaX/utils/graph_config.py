# -*- coding: utf-8 -*-


PLOTLY_GRAPH_CONFIG = {
    "displayModeBar": True,
    "scrollZoom": False,
    "doubleClick": False,
    "responsive": True,
    "staticPlot": False,
    "editable": False,
    "edits": {
        "axisTitleText": False,
        "titleText": False,
        "legendText": False,
    },
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
    ],
}


PLOTLY_STATIC_GRAPH_CONFIG = {
    **PLOTLY_GRAPH_CONFIG,
    "displayModeBar": False,
    "staticPlot": True,
}


PLOTLY_GRAPH_STYLE = {
    "touchAction": "none",
    "width": "100%",
    "height": "60vh"
}