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
    "doubleClick": "reset",
    "responsive": True,
    "staticPlot": False,
    "editable": False,
    "edits": {
        "axisTitleText": False,
        "titleText": False,
        "legendText": False,
    },
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d",
    ],
}


PLOTLY_STATIC_GRAPH_CONFIG = {
    **PLOTLY_GRAPH_CONFIG,
    "staticPlot": True,
}


PLOTLY_GRAPH_STYLE = {
    "touchAction": "none",
    "width": "100%",
    "height": "60vh"
}


WORKFLOW_SECTION = {
    "card": {
        "borderRadius": "15px",
        "borderLeft": "5px solid rgba(13, 110, 253, 0.75)",
        "boxShadow": "0 0.35rem 0.9rem rgba(0, 0, 0, 0.08)",
        "overflow": "visible",
    },
    "header": {
        "background": "rgba(13, 110, 253, 0.10)",
        "borderBottom": "1px solid rgba(13, 110, 253, 0.20)",
        "padding": "13px 18px",
        "borderTopLeftRadius": "15px",
        "borderTopRightRadius": "15px",
        "fontWeight": "750",
        "fontSize": "1.02rem",
    },
    "body": {
        "padding": "18px",
        "overflow": "visible",
    },
    "subtitle": {
        "fontSize": "0.86rem",
        "opacity": 0.76,
        "marginTop": "3px",
    },
    "subcard": {
        "borderRadius": "12px",
        "border": "1px solid rgba(13, 110, 253, 0.16)",
        "overflow": "visible",
    },
    "subcard_header": {
        "background": "rgba(13, 110, 253, 0.06)",
        "borderBottom": "1px solid rgba(13, 110, 253, 0.16)",
        "padding": "12px 16px",
        "borderTopLeftRadius": "12px",
        "borderTopRightRadius": "12px",
    },
    "subcard_body": {
        "padding": "16px",
        "overflow": "visible",
    },
    "action_panel": {
        "borderRadius": "12px",
        "border": "1px solid rgba(13, 110, 253, 0.16)",
        "background": "rgba(13, 110, 253, 0.04)",
        "overflow": "visible",
    },
    "compact_control_box": {
        "display": "inline-flex",
        "gap": "18px",
        "alignItems": "center",
        "flexWrap": "wrap",
        "padding": "8px 10px",
        "border": "1px solid rgba(128, 128, 128, 0.18)",
        "borderRadius": "9px",
        "background": "rgba(128, 128, 128, 0.06)",
    },
    "info_badge": {
        "width": "19px",
        "height": "19px",
        "borderRadius": "50%",
        "display": "inline-flex",
        "alignItems": "center",
        "justifyContent": "center",
        "fontSize": "0.72rem",
        "fontWeight": "800",
        "marginLeft": "8px",
        "cursor": "help",
        "opacity": 0.72,
        "border": "1px solid currentColor",
        "lineHeight": "1",
        "flex": "0 0 auto",
    },
    "title_with_info": {
        "display": "flex",
        "alignItems": "center",
        "fontWeight": "750",
        "fontSize": "1.02rem",
    },
}


def merge_style(
    *styles,
) -> dict:
    """
    Merge style dictionaries while ignoring non dictionary values.
    """
    merged_style = {}

    for style in styles:
        if isinstance(style, dict):
            merged_style.update(style)

    return merged_style


def copy_style(
    style,
) -> dict:
    """
    Return a mutable copy of a style dictionary.
    """
    if isinstance(style, dict):
        return dict(style)

    return {}