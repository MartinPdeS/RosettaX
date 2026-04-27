UPLOAD = {
    "width": "100%",
    "height": "60px",
    "lineHeight": "60px",
    "borderWidth": "1px",
    "borderStyle": "dashed",
    "borderRadius": "5px",
    "textAlign": "center",
    "margin": "10px",
}

CARD = {
    "display": "flex",
    "gap": "12px",
    "alignItems": "center"
}

SIDEBAR = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": f"500px",
    "padding": "16px",
    "overflowY": "auto",
    "zIndex": 1000,
    "boxSizing": "border-box",
}

PAGE = {
    "body_scroll": {"maxHeight": "80vh", "overflowY": "auto"},
    "row": {"display": "flex", "alignItems": "center", "gap": "10px"},
    "label": {"minWidth": "160px"},
    "card_body_scroll": {"maxHeight": "60vh", "overflowY": "auto"},
}

CONTENT = {
    "marginLeft": f"460px",
    "padding": "16px",
    "minHeight": "100vh",
    "boxSizing": "border-box",
}


DATATABLE = dict(
    editable=True,
    row_deletable=True,
    cell_selectable=True,
    persistence=True,
    persistence_type="session",
    persisted_props=[
        "data",
    ],
    style_table={
        "overflowX": "auto",
    },
    style_cell={
        "textAlign": "left",
        "backgroundColor": "white",
        "color": "black",
        "minWidth": "120px",
        "width": "160px",
        "maxWidth": "260px",
        "whiteSpace": "normal",
        "border": "1px solid #d9d9d9",
    },
    style_header={
        "backgroundColor": "#f8f9fa",
        "color": "black",
        "fontWeight": "600",
        "border": "1px solid #bdbdbd",
    },
    style_data={
        "backgroundColor": "white",
        "color": "black",
    },
    style_data_conditional=[
        {
            "if": {
                "state": "active",
            },
            "backgroundColor": "white",
            "border": "1px solid #d9d9d9",
            "color": "black",
        },
        {
            "if": {
                "state": "selected",
            },
            "backgroundColor": "#eef4ff",
            "border": "1px solid #b8cff8",
            "color": "black",
        },
    ],
    css=[
        {
            "selector": ".dash-cell div",
            "rule": "text-align: left !important;",
        },
        {
            "selector": ".dash-cell.focused div",
            "rule": "text-align: left !important;",
        },
        {
            "selector": ".dash-cell.cell--selected div",
            "rule": "text-align: left !important;",
        },
        {
            "selector": ".dash-cell input",
            "rule": (
                "text-align: left !important; "
                "background-color: white !important; "
                "color: black !important;"
            ),
        },
    ],
)

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