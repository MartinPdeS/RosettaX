"""Update the named native arrowhead shapes while preserving slide edits."""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Pt

DIRECTORY = Path(__file__).resolve().parent
DECK = DIRECTORY / "RosettaX_colleague_overview.key"
SHAPE_PREFIX = "RosettaX Process Arrowhead"


def quote(*, value: str) -> str:
    """Escape text for an AppleScript string literal."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def applescript(*, source: str) -> str:
    """Execute AppleScript and return its textual result."""
    result = subprocess.run(["osascript"], input=source, text=True, check=True, capture_output=True)
    return result.stdout.rstrip("\n")


def main() -> None:
    """Update arrow geometry and color, then refresh the native deck and exports."""
    style = json.loads((DIRECTORY / "arrow-style.json").read_text())
    with tempfile.TemporaryDirectory(prefix="rosettax-arrow-style-") as temporary_directory:
        working = Path(temporary_directory).resolve()
        exported = working / "current.pptx"
        notes_text = applescript(source=f'''
tell application "Keynote"
 set d to open (POSIX file {quote(value=str(DECK))} as alias)
 save d
 export d to POSIX file {quote(value=str(exported))} as Microsoft PowerPoint
 tell d
  set notesList to {{}}
  repeat with slideNumber from 1 to count of slides
   set end of notesList to (presenter notes of slide slideNumber as text)
  end repeat
  set AppleScript's text item delimiters to character id 30
  return notesList as text
 end tell
end tell
''')
        notes = notes_text.split(chr(30))
        presentation = Presentation(exported)
        changed = 0
        for slide in presentation.slides:
            for shape in slide.shapes:
                if not shape.name.startswith(SHAPE_PREFIX):
                    continue
                center_x = shape.left + shape.width / 2
                center_y = shape.top + shape.height / 2
                shape.width = Pt(style["width"])
                shape.height = Pt(style["height"])
                shape.left = int(center_x - shape.width / 2)
                shape.top = int(center_y - shape.height / 2)
                shape.rotation = 90
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor.from_string(style["color_hex"])
                shape.line.fill.background()
                text_body = shape._element.find(qn("p:txBody"))
                if text_body is not None:
                    shape._element.remove(text_body)
                changed += 1
            # Restore notes natively after import: Keynote rejects the notes
            # parts emitted by python-pptx when saving an edited presentation.
            for relationship in list(slide.part.rels.values()):
                if relationship.reltype.endswith("/notesSlide"):
                    slide.part.drop_rel(relationship.rId)
        if changed == 0:
            raise RuntimeError("No named RosettaX arrowhead shapes were found; the deck was left unchanged.")
        if len(notes) != len(presentation.slides):
            raise RuntimeError("Presenter notes did not match the slide count; the deck was left unchanged.")
        edited = working / "RosettaX_arrow_style_updated.pptx"
        native = working / "RosettaX_arrow_style_updated.key"
        preview = working / "RosettaX_arrow_style_updated.pdf"
        roundtrip = working / "RosettaX_arrow_style_export.pptx"
        presentation.save(edited)
        commands = [
            'tell application "Keynote"',
            f'set d to open (POSIX file {quote(value=str(edited))} as alias)',
            'tell d',
        ]
        for number, note in enumerate(notes, start=1):
            commands.append(f"set presenter notes of slide {number} to {quote(value=note)}")
        commands.extend([
            "end tell",
            f"save d in POSIX file {quote(value=str(native))}",
            f"export d to POSIX file {quote(value=str(preview))} as PDF",
            f"export d to POSIX file {quote(value=str(roundtrip))} as Microsoft PowerPoint",
            f"close document {quote(value=DECK.name)} saving no",
            "close d saving no",
            "end tell",
        ])
        applescript(source="\n".join(commands))
        shutil.copy2(native, DECK)
        shutil.copy2(preview, DIRECTORY / "RosettaX_colleague_overview.pdf")
        shutil.copy2(preview, DIRECTORY / "RosettaX_colleague_overview_current.pdf")
        shutil.copy2(roundtrip, DIRECTORY / "RosettaX_colleague_overview.pptx")
        applescript(source=f'tell application "Keynote" to open (POSIX file {quote(value=str(DECK))} as alias)')
        print(f"Updated {changed} native arrowheads and preserved all {len(notes)} presenter note sections.")


if __name__ == "__main__":
    main()
