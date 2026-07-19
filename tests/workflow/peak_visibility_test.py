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
        assert visibility.build_advanced_mode_control_style("") == {
            "display": "none",
        }
        assert visibility.build_data_filter_control_style(
            process_name="",
            advanced_mode_value=["enabled"],
        ) == {"display": "none"}
        assert visibility.build_graph_toggle_control_style("") == {
            "display": "none",
        }
        assert visibility.build_process_settings_container_style(
            process_name="",
            advanced_mode_value=["enabled"],
        ) == {
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
        assert visibility.build_advanced_mode_control_style("Automatic 1D") == {
            "display": "inline-flex",
        }
        assert visibility.build_data_filter_control_style(
            process_name="Automatic 1D",
            advanced_mode_value=[],
        ) == {"display": "none"}
        assert visibility.build_data_filter_control_style(
            process_name="Automatic 1D",
            advanced_mode_value=["enabled"],
        ) == {"display": "inline-flex"}
        assert visibility.build_graph_toggle_control_style("Automatic 1D") == {
            "display": "inline-flex",
        }
        assert visibility.build_process_settings_container_style(
            process_name="Automatic 1D",
            advanced_mode_value=["enabled"],
        ) == {
            "display": "flex",
            "alignItems": "end",
            "gap": "12px",
            "flexWrap": "wrap",
            "marginTop": "10px",
        }
        assert visibility.build_process_settings_container_style(
            process_name="Automatic 1D",
            advanced_mode_value=[],
        ) == {
            "display": "none",
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

    def test_rosetta_advanced_only_helpers_hide_without_advanced_mode(self) -> None:
        children, guide_style = visibility.build_graph_helper_panel(
            process_name="Rosetta Script",
            graph_toggle_value=["enabled"],
            advanced_mode_value=[],
        )
        assert children == []
        assert guide_style["display"] == "none"

        assert visibility.build_rosetta_advanced_only_style(
            process_name="Rosetta Script",
            graph_toggle_value=["enabled"],
            advanced_mode_value=[],
        ) == {
            "display": "none",
        }

        assert visibility.build_rosetta_advanced_only_style(
            process_name="Rosetta Script",
            graph_toggle_value=["enabled"],
            advanced_mode_value=["enabled"],
        ) == {
            "display": "block",
        }

        assert visibility.build_rosetta_advanced_only_style(
            process_name="Automatic 1D",
            graph_toggle_value=["enabled"],
            advanced_mode_value=[],
        ) == {
            "display": "block",
        }

    def test_rosetta_v1_advanced_only_helpers_match_rosetta_behavior(self) -> None:
        assert visibility.build_rosetta_advanced_only_style(
            process_name="Rosetta Script V1",
            graph_toggle_value=["enabled"],
            advanced_mode_value=[],
        ) == {
            "display": "none",
        }

        assert visibility.build_rosetta_advanced_only_style(
            process_name="Rosetta Script V1",
            graph_toggle_value=["enabled"],
            advanced_mode_value=["enabled"],
        ) == {
            "display": "block",
        }

    def test_graph_helper_panel_guides_user_before_process_selection(self) -> None:
        children, style = visibility.build_graph_helper_panel(
            process_name="",
            graph_toggle_value=[],
            advanced_mode_value=[],
        )

        assert children == []
        assert style["display"] == "none"

        children, style = visibility.build_graph_helper_panel(
            process_name="",
            graph_toggle_value=[],
            advanced_mode_value=["enabled"],
        )
        rendered_text = " ".join(str(getattr(child, "children", "")) for child in children)
        assert style["display"] == "block"
        assert "Select a peak process" in rendered_text
        assert "Choose the required detector channels" in rendered_text

    def test_graph_helper_panel_shows_manual_2d_instruction(self) -> None:
        children, _ = visibility.build_graph_helper_panel(
            process_name="Manual 2D",
            graph_toggle_value=["enabled"],
            advanced_mode_value=[],
        )

        assert children == []

        children, _ = visibility.build_graph_helper_panel(
            process_name="Manual 2D",
            graph_toggle_value=["enabled"],
            advanced_mode_value=["enabled"],
        )

        rendered_text = " ".join(
            str(getattr(child, "children", ""))
            for child in children
        )

        assert "Drag a selection box around a cluster" in rendered_text

    def test_graph_helper_panel_shows_rosetta_legend_in_advanced_mode(self) -> None:
        children, _ = visibility.build_graph_helper_panel(
            process_name="Rosetta Script V1",
            graph_toggle_value=["enabled"],
            advanced_mode_value=["enabled"],
        )

        rendered_text = " ".join(
            str(getattr(child, "children", ""))
            for child in children
        )

        assert "Rosetta graph legend" in rendered_text
        assert "Green dashed vertical lines" in rendered_text


class Test_PeakProcessFiltering:
    def test_filter_peak_processes_keeps_only_allowed_names(self) -> None:
        scripts = registry.get_peak_process_instances()

        filtered = registry.filter_peak_processes(
            scripts=scripts,
            allowed_process_names=[
                "Manual 1D",
                "Automatic 2D",
            ],
        )

        filtered_names = [
            getattr(script, "process_name", "")
            for script in filtered
        ]

        assert filtered_names
        assert set(filtered_names).issubset(
            {
                "Manual 1D",
                "Automatic 2D",
            }
        )
        assert "Automatic 2D" in filtered_names

    def test_filter_peak_processes_returns_all_when_allowed_is_empty(self) -> None:
        scripts = registry.get_peak_process_instances()

        filtered = registry.filter_peak_processes(
            scripts=scripts,
            allowed_process_names=[],
        )

        assert [getattr(script, "process_name", "") for script in filtered] == [
            getattr(script, "process_name", "")
            for script in scripts
        ]
