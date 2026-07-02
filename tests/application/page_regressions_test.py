# -*- coding: utf-8 -*-

import importlib
import logging
from types import SimpleNamespace

import dash
import numpy as np
import pytest

from RosettaX.application import layout as application_layout
from RosettaX.pages.p00_sidebar.main import Sidebar
from RosettaX.pages.p02_fluorescence.ids import Ids as FluorescenceIds
from RosettaX.pages.p02_fluorescence.sections.s04_calibration.main import Calibration
from RosettaX.pages.p03_scattering.ids import Ids as ScatteringIds
from RosettaX.pages.p03_scattering.sections.s03_model.main import Model as ScatteringModel
from RosettaX.pages.p03_scattering.sections.s05_calibration.main import Calibration as ScatteringCalibration
from RosettaX.pages.p03_scattering.sections.s05_calibration import services as scattering_services
from RosettaX.pages.p04_calibrate.sections.s04_apply import services as apply_services


def _collect_component_ids(component) -> set[str]:
    component_id = getattr(component, "id", None)
    collected_ids = {component_id} if isinstance(component_id, str) else set()
    children = getattr(component, "children", None)

    if children is None:
        return collected_ids

    if isinstance(children, (list, tuple)):
        for child in children:
            collected_ids.update(_collect_component_ids(child))
        return collected_ids

    collected_ids.update(_collect_component_ids(children))
    return collected_ids


def _collect_component_hrefs(component) -> set[str]:
    href = getattr(component, "href", None)
    collected_hrefs = {href} if isinstance(href, str) else set()
    children = getattr(component, "children", None)

    if children is None:
        return collected_hrefs

    if isinstance(children, (list, tuple)):
        for child in children:
            collected_hrefs.update(_collect_component_hrefs(child))
        return collected_hrefs

    collected_hrefs.update(_collect_component_hrefs(children))
    return collected_hrefs


def _find_component_by_id(component, target_id: str):
    component_id = getattr(component, "id", None)

    if component_id == target_id:
        return component

    children = getattr(component, "children", None)

    if children is None:
        return None

    if isinstance(children, (list, tuple)):
        for child in children:
            found_component = _find_component_by_id(child, target_id)

            if found_component is not None:
                return found_component

        return None

    return _find_component_by_id(children, target_id)


def _collect_text(component) -> list[str]:
    if component is None:
        return []

    if isinstance(component, str):
        return [component]

    children = getattr(component, "children", None)

    if children is None:
        return []

    if isinstance(children, (list, tuple)):
        collected: list[str] = []
        for child in children:
            collected.extend(_collect_text(child))
        return collected

    return _collect_text(children)


class Test_FluorescenceCalibrationLayout:
    def test_layout_includes_calibration_graph_component(self) -> None:
        section = Calibration(
            page=SimpleNamespace(ids=FluorescenceIds()),
            section_number=4,
        )

        layout = section.get_layout()

        assert section.ids.graph_calibration in _collect_component_ids(layout)


class Test_ScatteringCalibrationPreviewGraph:
    def test_preview_store_is_built_from_computed_solid_sphere_rows(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            scattering_services,
            "build_solid_sphere_dense_simulated_coupling_curve",
            lambda **_: (
                np.asarray([90.0, 210.0], dtype=float),
                np.asarray([0.9, 2.1], dtype=float),
            ),
        )

        figure_store = scattering_services.build_calibration_standard_mie_relation_figure_store(
            mie_model="Solid Sphere",
            current_table_rows=[
                {
                    "particle_diameter_nm": "100",
                    "expected_coupling": "1.0",
                },
                {
                    "particle_diameter_nm": "200",
                    "expected_coupling": "2.0",
                },
            ],
            medium_refractive_index=1.33,
            particle_refractive_index=1.59,
            core_refractive_index=None,
            shell_refractive_index=None,
            wavelength_nm=488.0,
            detector_numerical_aperture=0.4,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            detector_sampling=600,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            simulated_curve_point_count=200,
            logger=logging.getLogger(__name__),
        )

        assert figure_store["layout"]["title"]["text"] == "Calibration standard Mie relation"
        assert [trace["name"] for trace in figure_store["data"]] == [
            "Mie relation (200 points)",
            "Calibration standards",
        ]


class Test_ScatteringModelLayout:
    def test_layout_includes_detector_brand_model_and_type_controls(self) -> None:
        section = ScatteringModel(
            page=SimpleNamespace(ids=ScatteringIds()),
            section_number=3,
        )

        layout = section.get_layout()
        component_ids = _collect_component_ids(layout)

        assert section.ids.detector_configuration_brand in component_ids
        assert section.ids.detector_configuration_model in component_ids
        assert section.ids.detector_configuration_type in component_ids
        assert section.ids.detector_configuration_preset in component_ids

        custom_values_container = _find_component_by_id(
            layout,
            section.ids.detector_configuration_custom_values_container,
        )

        assert custom_values_container is not None
        assert section.ids.wavelength_nm in _collect_component_ids(custom_values_container)


class Test_ScatteringCalibrationCallbackOutputs:
    def test_missing_table_update_keeps_existing_rows(self) -> None:
        assert ScatteringCalibration._resolve_bead_table_output(None) is dash.no_update

    def test_explicit_table_update_is_forwarded(self) -> None:
        rows = [{"particle_diameter_nm": "100"}]

        assert ScatteringCalibration._resolve_bead_table_output(rows) == rows


class Test_ApplyCalibrationPage:
    def test_layout_uses_model_panels_without_target_particle_model_wrapper(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        apply_main = importlib.import_module("RosettaX.pages.p04_calibrate.main")
        page = apply_main.ApplyCalibrationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)

        assert "Target particle model" not in text_nodes
        assert "Model parameters" in text_nodes
        assert "Target Mie relation preview" in text_nodes

    def test_layout_starts_with_select_placeholder_and_hidden_target_model_boxes(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        apply_main = importlib.import_module("RosettaX.pages.p04_calibrate.main")
        page = apply_main.ApplyCalibrationPage()

        layout = page.layout()

        preset_dropdown = _find_component_by_id(
            layout,
            page.ids.CalibrationPicker.target_model_preset,
        )
        details_container = _find_component_by_id(
            layout,
            page.ids.CalibrationPicker.target_model_details_container,
        )
        preview_container = _find_component_by_id(
            layout,
            page.ids.CalibrationPicker.target_mie_relation_preview_container,
        )

        assert preset_dropdown is not None
        assert preset_dropdown.value == ""
        assert preset_dropdown.options[0] == {
            "label": "Select",
            "value": "",
        }
        assert details_container is not None
        assert details_container.style["display"] == "none"
        assert preview_container is not None
        assert preview_container.style["display"] == "none"

    def test_build_apply_calibration_request_requires_target_model_selection_for_scattering(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="Select a target model preset first."):
            apply_services.build_apply_calibration_request(
                uploaded_fcs_path=["/tmp/input.fcs"],
                export_columns=[],
                selected_calibration_summary={
                    "requires_target_model": True,
                    "file_name": "scattering.json",
                    "calibration_payload": {
                        "calibration_type": "scattering",
                    },
                },
                target_model_preset="",
                target_mie_model="Solid Sphere",
                target_medium_refractive_index=1.333,
                target_particle_refractive_index=1.39,
                target_solid_sphere_diameter_min_nm=30,
                target_solid_sphere_diameter_max_nm=1000,
                target_solid_sphere_diameter_count=500,
                target_core_refractive_index=1.37,
                target_shell_refractive_index=1.46,
                target_shell_thickness_nm=5,
                target_core_shell_core_diameter_min_nm=30,
                target_core_shell_core_diameter_max_nm=1000,
                target_core_shell_core_diameter_count=500,
            )


class Test_DocumentationPage:
    def test_layout_includes_core_documentation_sections(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        documentation_main = importlib.import_module(
            "RosettaX.pages.p07_documentation.main"
        )
        page = documentation_main.DocumentationPage()

        layout = page.layout()
        component_ids = _collect_component_ids(layout)
        text_nodes = _collect_text(layout)

        assert page._id("hero") in component_ids
        assert page._id("workflow-map") in component_ids
        assert page._id("system-model") in component_ids
        assert page._id("supported-cytometers") in component_ids
        assert page._id("refractive-index") in component_ids
        assert page._id("regression-models") in component_ids
        assert page._id("calibration-files") in component_ids
        assert page._id("apply-checks") in component_ids
        assert page._id("reports") in component_ids
        assert "How detector support works" in text_nodes
        assert "Cytek Biosciences" in text_nodes


class Test_ApplicationLayout:
    def test_layout_includes_global_maintainer_footer(self) -> None:
        layout = application_layout.build_application_layout()

        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "RosettaX is developed and maintained by " in text_nodes
        assert "Martin Poinsinet de Sivry-Houle" in text_nodes
        assert "mailto:martin.poinsinet.de.sivry@gmail.com" in hrefs


class Test_HelpPage:
    def test_layout_includes_horizontal_project_resources_card(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        help_main = importlib.import_module("RosettaX.pages.p06_help.main")
        page = help_main.HelpPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Project resources" in text_nodes
        assert "Technical docs" in text_nodes
        assert "Support Developer" in text_nodes
        assert "Open sample files page" in text_nodes
        assert "/documentation" in hrefs
        assert "/sample-files" in hrefs
        assert "https://github.com/MartinPdeS/RosettaX" in hrefs


class Test_SidebarNavigation:
    def test_navigation_includes_documentation_link(self) -> None:
        sidebar = Sidebar()

        navigation = sidebar._build_navigation_section()

        assert "/documentation" in _collect_component_hrefs(navigation)
        assert "/cross-calibration" in _collect_component_hrefs(navigation)
        assert "/visualization" in _collect_component_hrefs(navigation)
        assert "/sample-files" in _collect_component_hrefs(navigation)

    def test_logo_links_to_home_page(self) -> None:
        sidebar = Sidebar()

        logo_section = sidebar._build_logo_section()

        assert "/" in _collect_component_hrefs(logo_section)
