"""Regression tests for application citation page."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import importlib

import dash


def _collect_text(component) -> list[str]:
    """Collect text recursively from the test component tree."""
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


class Test_CitationPage:
    """Regression checks for citation page."""

    def test_layout_includes_requested_zenodo_record_and_bibtex(
        self,
        monkeypatch,
    ) -> None:
        """Check layout includes requested zenodo record and bibtex."""
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        citation_main = importlib.import_module("RosettaX.pages.p20_citation.main")
        citation_main = importlib.reload(citation_main)

        layout = citation_main.CitationPage().layout()
        text_nodes = _collect_text(layout)

        assert "Cite RosettaX" in text_nodes
        assert "View Zenodo record" in text_nodes
        assert any("10.5281/zenodo.21309433" in text for text in text_nodes)
        assert any("@software{poinsinet_de_sivry_houle_2026_21309433" in text for text in text_nodes)
