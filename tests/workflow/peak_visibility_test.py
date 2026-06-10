# -*- coding: utf-8 -*-

from RosettaX.workflow.peak import registry
from RosettaX.workflow.peak.callbacks import visibility


class Test_PeakProcessSelectionVisibility:
    def test_build_peak_process_options_starts_with_select_option(self) -> None:
        options = registry.build_peak_process_options(
            include_empty_option=True,
        )

        assert options[0] == {
            "label": "Select",
            "value": "",
        }

    def test_empty_selection_hides_graph_toggle_and_graph_container(self) -> None:
        assert visibility.build_graph_toggle_control_style("") == {
            "display": "none",
        }
        assert visibility.build_graph_container_style(
            process_name="",
            graph_toggle_value=["enabled"],
        ) == {
            "display": "none",
        }

    def test_selected_process_shows_graph_toggle_and_respects_toggle_value(self) -> None:
        assert visibility.build_graph_toggle_control_style("Automatic 1D") == {
            "display": "inline-flex",
        }
        assert visibility.build_graph_container_style(
            process_name="Automatic 1D",
            graph_toggle_value=["enabled"],
        ) == {
            "display": "block",
        }
        assert visibility.build_graph_container_style(
            process_name="Automatic 1D",
            graph_toggle_value=[],
        ) == {
            "display": "none",
        }