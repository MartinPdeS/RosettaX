"""RosettaX documentation configuration."""

from pathlib import Path
import sys

from martinpdes_docs import configure

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

project = "RosettaX"
package = "RosettaX"
repository = "MartinPdeS/RosettaX"
globals().update(
    configure(
        project=project,
        package=package,
        repository=repository,
        logo="_static/logo.svg",
        favicon="_static/favicon.svg",
        gallery_options={"abort_on_example_error": True},
        logo_text="",
        html_css_files=["layout.css"],
    )
)
