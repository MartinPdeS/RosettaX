# -*- coding: utf-8 -*-

import importlib
import logging
from types import SimpleNamespace

import dash
import numpy as np
import pytest

from RosettaX.application import layout as application_layout
from RosettaX.pages.p00_sidebar.ids import SidebarIds
from RosettaX.pages.p00_sidebar.main import Sidebar
from RosettaX.pages.p02_fluorescence.ids import Ids as FluorescenceIds
from RosettaX.pages.p02_fluorescence.sections.s04_calibration.main import Calibration
from RosettaX.pages.p03_scattering.ids import Ids as ScatteringIds
from RosettaX.pages.p03_scattering.sections.s03_model.main import Model as ScatteringModel
from RosettaX.pages.p03_scattering.sections.s05_calibration.main import Calibration as ScatteringCalibration
from RosettaX.pages.p03_scattering.sections.s05_calibration import services as scattering_services
from RosettaX.pages.p04_calibrate.sections.s04_apply import services as apply_services
from RosettaX.workflow.parameters.refractive_index import (
    calculate_sellmeier_refractive_index,
)


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

    def test_calibration_json_upload_has_no_component_size_cap(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        apply_main = importlib.import_module("RosettaX.pages.p04_calibrate.main")
        page = apply_main.ApplyCalibrationPage()

        layout = page.layout()
        upload_component = _find_component_by_id(
            layout,
            page.ids.CalibrationPicker.upload,
        )

        assert upload_component is not None
        assert getattr(upload_component, "max_size", None) is None

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
                advanced_monotonic_mode_enabled=[],
                use_monotonic_smoothing_kernel=[],
                monotonic_smoothing_sigma_points=2.0,
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

    def test_build_apply_calibration_request_resolves_polystyrene_preset_from_calibration_wavelength(
        self,
    ) -> None:
        request = apply_services.build_apply_calibration_request(
            uploaded_fcs_path=["/tmp/input.fcs"],
            export_columns=[],
            selected_calibration_summary={
                "requires_target_model": True,
                "file_name": "scattering.json",
                "calibration_payload": {
                    "calibration_type": "scattering",
                    "metadata": {
                        "calibration_standard_parameters": {
                            "wavelength_nm": 405.0,
                            "detector_numerical_aperture": 0.2,
                        }
                    },
                },
            },
            target_model_preset="Polystyrene Beads",
            advanced_monotonic_mode_enabled=[],
            use_monotonic_smoothing_kernel=[],
            monotonic_smoothing_sigma_points=2.0,
            target_mie_model="Solid Sphere",
            target_medium_refractive_index=1.333,
            target_particle_refractive_index=1.59,
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

        parameters = request.calibrations[0].scattering_target_model_parameters

        assert parameters is not None
        assert parameters.target_model.medium_refractive_index == calculate_sellmeier_refractive_index(
            "water",
            wavelength_nm=405.0,
        )
        assert parameters.target_model.particle_refractive_index == calculate_sellmeier_refractive_index(
            "polystyrene",
            wavelength_nm=405.0,
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
        assert page._id("workflow-map") not in component_ids
        assert page._id("refractive-index") not in component_ids
        assert page._id("calibration-files") not in component_ids
        assert page._id("apply-checks") not in component_ids
        assert page._id("system-model") not in component_ids
        assert page._id("supported-cytometers") not in component_ids
        assert page._id("regression-models") not in component_ids
        assert page._id("peak-identification") not in component_ids
        assert page._id("reports") not in component_ids
        assert "How detector support works" not in text_nodes

    def test_layout_links_to_documentation_deep_dive_pages(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        documentation_main = importlib.import_module(
            "RosettaX.pages.p07_documentation.main"
        )
        page = documentation_main.DocumentationPage()

        layout = page.layout()
        hrefs = _collect_component_hrefs(layout)

        assert "/documentation/system-model" in hrefs
        assert "/documentation/peak-scripts" in hrefs
        assert "/documentation/supported-cytometers" in hrefs
        assert "/documentation/refractive-index" in hrefs
        assert "/documentation/calibration-payload" in hrefs
        assert "/documentation/apply-checks" in hrefs
        assert "/documentation/regression-models" in hrefs
        assert "/documentation/reports" in hrefs


class Test_DocumentationDeepDivePages:
    def test_peak_scripts_page_layout_contains_related_navigation(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        peak_docs_main = importlib.import_module(
            "RosettaX.pages.p11_docs_peak_scripts.main"
        )
        page = peak_docs_main.PeakScriptsDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Peak Process Scripts" in text_nodes
        assert "Rosetta script" in text_nodes
        assert "/documentation" in hrefs
        assert "/documentation/regression-models" in hrefs

    def test_system_model_page_layout_contains_instrument_assumptions(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        system_docs_main = importlib.import_module(
            "RosettaX.pages.p15_docs_system_model.main"
        )
        page = system_docs_main.SystemModelDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "System Model and Optics" in text_nodes
        assert "What kind of system RosettaX assumes" in text_nodes
        assert "Scattering optical model" in text_nodes
        assert "/documentation" in hrefs
        assert "/documentation/supported-cytometers" in hrefs

    def test_supported_cytometers_page_layout_contains_catalog_and_contact(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        cytometer_docs_main = importlib.import_module(
            "RosettaX.pages.p12_docs_supported_cytometers.main"
        )
        page = cytometer_docs_main.SupportedCytometersDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Supported Flow Cytometers" in text_nodes
        assert "Packaged detector preset catalog" in text_nodes
        assert "Cytek Biosciences" in text_nodes
        assert f"mailto:{page.contact_email}" in hrefs

    def test_regression_models_page_layout_contains_fit_descriptions(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        regression_docs_main = importlib.import_module(
            "RosettaX.pages.p13_docs_regression_models.main"
        )
        page = regression_docs_main.RegressionModelsDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Regression Models" in text_nodes
        assert "Fluorescence fit model" in text_nodes
        assert "Scattering fit model" in text_nodes
        assert "/documentation/peak-scripts" in hrefs

    def test_reports_page_layout_contains_provenance_descriptions(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        reports_docs_main = importlib.import_module(
            "RosettaX.pages.p14_docs_reports.main"
        )
        page = reports_docs_main.ReportsDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Reports and Provenance" in text_nodes
        assert "What the PDF report records" in text_nodes
        assert "How the report differs from calibration JSON" in text_nodes
        assert "/documentation" in hrefs
        assert "/documentation/regression-models" in hrefs

    def test_refractive_index_page_layout_contains_resolution_details(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        refractive_docs_main = importlib.import_module(
            "RosettaX.pages.p16_docs_refractive_index.main"
        )
        page = refractive_docs_main.RefractiveIndexDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Material Refractive Index Resolution" in text_nodes
        assert "How RosettaX resolves refractive indices" in text_nodes
        assert "/documentation" in hrefs
        assert "/documentation/system-model" in hrefs

    def test_calibration_payload_page_layout_contains_wrapper_and_payload_sections(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        payload_docs_main = importlib.import_module(
            "RosettaX.pages.p17_docs_calibration_payload.main"
        )
        page = payload_docs_main.CalibrationPayloadDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Calibration File Wrapper and Payload" in text_nodes
        assert "Calibration file wrapper" in text_nodes
        assert "What the inner payload contains" in text_nodes
        assert "/documentation" in hrefs
        assert "/documentation/apply-checks" in hrefs

    def test_apply_checks_page_layout_contains_validation_rules(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        apply_checks_docs_main = importlib.import_module(
            "RosettaX.pages.p18_docs_apply_checks.main"
        )
        page = apply_checks_docs_main.ApplyChecksDocumentationPage()

        layout = page.layout()
        text_nodes = _collect_text(layout)
        hrefs = _collect_component_hrefs(layout)

        assert "Checks Performed While Applying a Calibration" in text_nodes
        assert "Apply-time checks" in text_nodes
        assert "/documentation" in hrefs
        assert "/documentation/calibration-payload" in hrefs


class Test_CrossCalibrationPage:
    def test_layout_includes_upload_build_review_and_export_controls(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        cross_main = importlib.import_module("RosettaX.pages.p08_cross_calibration.main")
        page = cross_main.CrossCalibrationPage()

        layout = page.layout()
        component_ids = _collect_component_ids(layout)
        text_nodes = _collect_text(layout)

        assert page.ids.primary_upload in component_ids
        assert page.ids.secondary_upload in component_ids
        assert page.ids.build_button in component_ids
        assert page.ids.graph in component_ids
        assert page.ids.table in component_ids
        assert page.ids.export_name in component_ids
        assert page.ids.export_button in component_ids
        assert "Create transfer calibration" in text_nodes
        assert "Download transfer calibration JSON" in text_nodes


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
        text_nodes = _collect_text(navigation)
        component_ids = _collect_component_ids(navigation)

        assert "Calibration" in text_nodes
        assert "Tools" in text_nodes
        assert ">" in text_nodes
        assert "Fluorescence" in text_nodes
        assert "Scattering" in text_nodes
        assert "Apply" in text_nodes
        assert SidebarIds.calibration_toggle_button in component_ids
        assert SidebarIds.calibration_collapse in component_ids
        assert SidebarIds.tools_toggle_button in component_ids
        assert SidebarIds.tools_collapse in component_ids
        assert "/documentation" in _collect_component_hrefs(navigation)
        assert "/cross-calibration" in _collect_component_hrefs(navigation)
        assert "/visualization" in _collect_component_hrefs(navigation)
        assert "/sample-files" in _collect_component_hrefs(navigation)

    def test_logo_links_to_home_page(self) -> None:
        sidebar = Sidebar()

        logo_section = sidebar._build_logo_section()

        assert "/" in _collect_component_hrefs(logo_section)
