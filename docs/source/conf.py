"""RosettaX documentation configuration."""

import os
from pathlib import Path
import sys

from sphinx_gallery.sorting import FileNameSortKey
from martinpdes_docs import configure

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

project = "RosettaX"
package = "RosettaX"
repository = "MartinPdeS/RosettaX"
version = os.getenv("tag", "latest")


globals().update(
    configure(
        project=project,
        package=package,
        repository=repository,
        version=version,
        logo="_static/logo.svg",
        favicon="_static/favicon.svg",
        sphinx_gallery_conf={
            "examples_dirs": "../examples/",
            "gallery_dirs": "gallery/",
            "within_subsection_order": FileNameSortKey,
            "abort_on_example_error": True,
        },
        html_theme_options={
            "logo": {"text": "", "image": "_static/logo.svg"},
        },
    )
)

extensions += ["sphinx.ext.mathjax", "sphinx.ext.autosectionlabel"]
html_css_files += ["layout.css"]
html_context["doc_path"] = "docs/source"
html_context["default_mode"] = "dark"
