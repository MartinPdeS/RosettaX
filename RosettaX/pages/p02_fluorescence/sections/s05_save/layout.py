
import dash_bootstrap_components as dbc


def get_layout(section) -> dbc.Card:
    """
    Create the fluorescence save section layout.
    """
    card = section.layout_builder.get_layout()

    return card
