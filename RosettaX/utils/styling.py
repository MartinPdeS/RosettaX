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
    persisted_props=["data"],
    style_table={"overflowX": "auto"},
    style_cell={
        "textAlign": "left",
        "backgroundColor": "white",
        "color": "black",
    },
    style_data={
        "backgroundColor": "white",
        "color": "black",
    },
    style_data_conditional=[
        {
            "if": {"state": "active"},
            "backgroundColor": "white",
            "border": "1px solid #d9d9d9",
            "color": "black",
        },
        {
            "if": {"state": "selected"},
            "backgroundColor": "white",
            "border": "1px solid #d9d9d9",
            "color": "black",
        },
    ],
    css=[
        {
            "selector": ".dash-cell div",
            "rule": "text-align: left;",
        },
        {
            "selector": ".dash-cell input",
            "rule": "text-align: left; background-color: white !important; color: black !important;",
        },
    ],
)