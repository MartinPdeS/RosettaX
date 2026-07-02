# -*- coding: utf-8 -*-

import importlib

import dash

from RosettaX.pages.p10_visualization import services


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


class Test_VisualizationPage:
    def test_layout_includes_core_visualization_controls(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        visualization_main = importlib.import_module(
            "RosettaX.pages.p10_visualization.main"
        )
        page = visualization_main.VisualizationPage()

        layout = page.layout()
        component_ids = _collect_component_ids(layout)

        assert page.ids.upload in component_ids
        assert page.ids.x_channel in component_ids
        assert page.ids.y_channel in component_ids
        assert page.ids.plot_type in component_ids
        assert page.ids.max_events in component_ids
        assert page.ids.colormap_log in component_ids
        assert page.ids.marker_size in component_ids
        assert page.ids.marker_opacity in component_ids
        assert page.ids.graph in component_ids

        graph_component = _find_component_by_id(layout, page.ids.graph)
        assert graph_component is not None
        assert getattr(graph_component, "style", {}) == services.resolve_visualization_control_defaults()["graph_style"]
