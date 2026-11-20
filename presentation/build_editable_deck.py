"""Build the RosettaX talk with editable text, geometry, and shared arrow styling."""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Pt

DIRECTORY = Path(__file__).resolve().parent
FONT = "Avenir Next"
NAVY = "17313F"
SLATE = "4D6573"
TEAL = "218D87"
BLUE = "4F89A8"
GOLD = "BB8724"
CORAL = "C9654C"
GREEN = "32866B"
PALE = "F5F8F9"
LINE = "DCE5E9"
WHITE = "FFFFFF"
ARROW_STYLE = json.loads((DIRECTORY / "arrow-style.json").read_text())
ARROWS: dict[str, list[list[float]]] = {}


def color(*, value: str) -> RGBColor:
    """Return an RGB color from a six digit hexadecimal value."""
    return RGBColor.from_string(value)


def textbox(*, slide, value: str, x: float, y: float, width: float, height: float,
            size: float = 17, bold: bool = False, ink: str = NAVY,
            align=PP_ALIGN.LEFT, name: str | None = None):
    """Add editable text using slide coordinates in points."""
    shape = slide.shapes.add_textbox(Pt(x), Pt(y), Pt(width), Pt(height))
    shape.name = name or value.split("\n")[0][:70]
    frame = shape.text_frame
    frame.clear()
    frame.margin_left = frame.margin_right = Pt(0)
    frame.margin_top = frame.margin_bottom = Pt(0)
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.TOP
    for index, line in enumerate(value.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = align
        paragraph.space_after = Pt(0)
        paragraph.space_before = Pt(0)
        paragraph.line_spacing = 1.13
        run = paragraph.add_run()
        run.text = line
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color(value=ink)
    return shape


def geometry(*, slide, x: float, y: float, width: float, height: float,
             fill: str = WHITE, border: str | None = None,
             kind=MSO_SHAPE.ROUNDED_RECTANGLE, name: str = "Panel"):
    """Add a native shape without an empty text container or effects."""
    shape = slide.shapes.add_shape(kind, Pt(x), Pt(y), Pt(width), Pt(height))
    shape.name = name
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        shape.adjustments[0] = 0.07
    shape.fill.solid()
    shape.fill.fore_color.rgb = color(value=fill)
    if border:
        shape.line.color.rgb = color(value=border)
        shape.line.width = Pt(0.8)
    else:
        shape.line.fill.background()
    body = shape._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}txBody")
    if body is not None:
        shape._element.remove(body)
    shape._element.spPr.append(OxmlElement("a:effectLst"))
    return shape


def rule(*, slide, x: float, y: float, width: float, ink: str = LINE, weight: float = 1):
    """Add a native horizontal rule in points."""
    shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Pt(x), Pt(y), Pt(x + width), Pt(y))
    shape.line.color.rgb = color(value=ink)
    shape.line.width = Pt(weight)
    shape._element.spPr.append(OxmlElement("a:effectLst"))
    return shape


def brand_logo(*, slide, x: float, y: float, width: float):
    """Place the existing logo with its embedded tagline cropped natively."""
    picture = slide.shapes.add_picture(str(DIRECTORY / "assets/rosettax-logo.png"),
                                       Pt(x), Pt(y), width=Pt(width), height=Pt(width / 4.56))
    picture.crop_left = 0.05
    picture.crop_right = 0.02
    picture.crop_top = 0.18
    picture.crop_bottom = 0.30
    return picture


def arrow(*, slide, number: int, x: float, y: float):
    """Add a pure triangle, centered in a workflow gap, with no text body."""
    width = ARROW_STYLE["width"]
    height = ARROW_STYLE["height"]
    shape = geometry(slide=slide, x=x - width / 2, y=y - height / 2,
                     width=width, height=height, fill=ARROW_STYLE["color_hex"],
                     kind=MSO_SHAPE.ISOSCELES_TRIANGLE,
                     name=f"RosettaX Process Arrowhead {number}-{len(ARROWS.get(str(number), [])) + 1}")
    shape.rotation = 90
    shape._element.nvSpPr.cNvPr.set("descr", "RosettaX shared process arrowhead")
    ARROWS.setdefault(str(number), []).append([x, y])


def footer(*, slide, number: int):
    """Add the consistent author, page number, and RosettaX branding."""
    rule(slide=slide, x=48, y=508, width=864, weight=0.7)
    textbox(slide=slide, value="Martin Poinsinet de Sivry-Houle · Amsterdam Vesicle Center",
            x=48, y=518, width=540, height=15, size=9, ink=SLATE)
    textbox(slide=slide, value=str(number), x=466, y=517, width=28, height=15,
            size=10, bold=True, ink=TEAL, align=PP_ALIGN.CENTER)
    brand_logo(slide=slide, x=826, y=516, width=86)


def slide_base(*, presentation, number: int, title: str | None = None,
               subtitle: str | None = None, accent: str = TEAL):
    """Create a clean slide with consistent title and subtitle placement."""
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color(value=WHITE)
    footer(slide=slide, number=number)
    if title:
        geometry(slide=slide, x=28, y=31, width=4, height=65,
                 fill=accent, kind=MSO_SHAPE.RECTANGLE, name="Title accent")
        textbox(slide=slide, value=title, x=48, y=27, width=864, height=47,
                size=33, bold=True)
        textbox(slide=slide, value=subtitle or "", x=48, y=82, width=864,
                height=44, size=18, ink=SLATE)
    return slide


def section(*, presentation, number: int, index: str, label: str, title: str,
            subtitle: str, accent: str = TEAL):
    """Create an editable section divider without a surrounding card."""
    slide = slide_base(presentation=presentation, number=number)
    slide.background.fill.fore_color.rgb = color(value=PALE)
    geometry(slide=slide, x=48, y=174, width=66, height=4, fill=accent,
             kind=MSO_SHAPE.RECTANGLE, name="Section accent")
    textbox(slide=slide, value=f"{index} · {label.upper()}", x=48, y=198,
            width=800, height=25, size=13, bold=True, ink=accent)
    textbox(slide=slide, value=title, x=48, y=238, width=850, height=63,
            size=40, bold=True)
    textbox(slide=slide, value=subtitle, x=48, y=315, width=795, height=66,
            size=22, ink=SLATE)
    return slide


def step(*, slide, x: float, y: float, width: float, height: float,
         number: str, title: str, body: str, accent: str, fill: str = PALE,
         title_size: float = 17, body_size: float = 15):
    """Add a compact native workflow step with a clear reading order."""
    geometry(slide=slide, x=x, y=y, width=width, height=height, fill=fill, border=LINE)
    textbox(slide=slide, value=number, x=x + 16, y=y + 13, width=width - 32,
            height=19, size=11, bold=True, ink=accent)
    textbox(slide=slide, value=title, x=x + 16, y=y + 40, width=width - 32,
            height=48, size=title_size, bold=True)
    textbox(slide=slide, value=body, x=x + 16, y=y + 92, width=width - 32,
            height=height - 100, size=body_size, ink=SLATE)


def main() -> None:
    """Build all sixteen slides while preserving the existing talk content."""
    presentation = Presentation()
    presentation.slide_width = Pt(960)
    presentation.slide_height = Pt(540)

    slide = slide_base(presentation=presentation, number=1)
    textbox(slide=slide, value="SOFTWARE OVERVIEW", x=48, y=81, width=700,
            height=24, size=12, bold=True, ink=TEAL)
    geometry(slide=slide, x=48, y=164, width=5, height=155, fill=TEAL,
             kind=MSO_SHAPE.RECTANGLE, name="Cover accent")
    brand_logo(slide=slide, x=76, y=185, width=365)
    textbox(slide=slide, value="Flow cytometry, calibrated.", x=76, y=291,
            width=760, height=52, size=28, bold=True)
    textbox(slide=slide, value="Martin Poinsinet de Sivry-Houle", x=76, y=397,
            width=800, height=29, size=19)
    textbox(slide=slide, value="Amsterdam Vesicle Center · Amsterdam UMC", x=76,
            y=432, width=800, height=25, size=15, ink=SLATE)

    section(presentation=presentation, number=2, index="01", label="Overview",
            title="Introduction", subtitle="Core ideas behind RosettaX calibration")

    slide = slide_base(presentation=presentation, number=3, title="What is RosettaX?",
                       subtitle="The goals behind RosettaX")
    columns = [("Broad calibration", "Fluorescence, scattering,\nand cross-calibration.", BLUE, "EDF4F8"),
               ("Open-source", "Open tools that can be\nshared and reused.", TEAL, "EDF6F3"),
               ("Intuitive", "Flexible workflows for\ndifferent needs.", GOLD, "FFF7E7"),
               ("Fast", "Efficient steps from\ndata to results.", GREEN, "F0F6F2")]
    for index, (title, body, accent, fill) in enumerate(columns):
        x = 48 + index * 225
        geometry(slide=slide, x=x, y=170, width=189, height=169, fill=fill, border=LINE)
        geometry(slide=slide, x=x + 18, y=192, width=8, height=8, fill=accent,
                 kind=MSO_SHAPE.OVAL, name="Capability marker")
        textbox(slide=slide, value=title, x=x + 18, y=217, width=159,
                height=28, size=18, bold=True)
        textbox(slide=slide, value=body, x=x + 18, y=259, width=159,
                height=64, size=15, ink=SLATE)
        if index < 3:
            arrow(slide=slide, number=3, x=x + 207, y=254)
    rule(slide=slide, x=48, y=382, width=864)
    textbox(slide=slide, value="Reproducible: save a fit with its context, then reuse it on new data.",
            x=48, y=401, width=864, height=30, size=19, bold=True)
    textbox(slide=slide, value="Available online and locally · rosettax.vesiclecenter.com",
            x=48, y=441, width=864, height=26, size=16, ink=SLATE)

    slide = slide_base(presentation=presentation, number=4, title="The idea behind calibration",
                       subtitle="Calibration connects measured signals to known reference values")
    slide.shapes.add_picture(str(DIRECTORY / "assets/calibration-fit.png"),
                             Pt(48), Pt(150), width=Pt(560), height=Pt(245))
    textbox(slide=slide, value="How to read this fit", x=632, y=153, width=280,
            height=28, size=17, bold=True, ink=SLATE)
    textbox(slide=slide,
            value=("PAIR · Each dot links a measured bead peak (x) to its known MESF reference (y).\n\n"
                   "FIT · RosettaX fits a power law to convert B2-A peak position into fluorescence units.\n\n"
                   "RESULT · This six-population example has R² = 0.998 in log₁₀ space. Save the fit and apply it to new files."),
            x=632, y=190, width=280, height=266, size=14, ink=SLATE)
    textbox(slide=slide, value="Cytek Aurora · B2-A · Rainbow 6 MESF beads",
            x=48, y=402, width=560, height=22, size=11, bold=True, ink=SLATE)

    slide = slide_base(presentation=presentation, number=5, title="From data to calibrated results",
                       subtitle="Load the data, identify bead peaks, fit the calibration, and reuse it")
    steps = [("Load", "Choose an\nFCS file.", BLUE), ("Inspect", "Channels +\nmetadata.", TEAL),
             ("Identify", "Locate bead\npopulations.", GOLD), ("Fit", "Pair peaks;\nreview fit.", CORAL),
             ("Save", "Keep fit and\nsettings.", BLUE), ("Apply", "Transform\nnew events.", GREEN)]
    for index, (title, body, accent) in enumerate(steps):
        x = 48 + index * 148
        step(slide=slide, x=x, y=158, width=124, height=159, number=f"0{index + 1}",
             title=title, body=body, accent=accent, title_size=17, body_size=14)
        if index < 5:
            arrow(slide=slide, number=5, x=x + 136, y=237)
    for x, title, body, accent in [(48, "Fluorescence", "Reference beads relate the measured signal\nto fluorescence units.", BLUE),
                                    (492, "Scattering", "A particle optics model predicts the reference\nresponse from bead and detector settings.", GOLD)]:
        rule(slide=slide, x=x, y=362, width=420, ink=accent, weight=2)
        textbox(slide=slide, value=title, x=x, y=378, width=420, height=28,
                size=20, bold=True, ink=accent)
        textbox(slide=slide, value=body, x=x, y=420, width=420, height=58, size=16, ink=SLATE)

    section(presentation=presentation, number=6, index="02", label="Fluorescence",
            title="Fluorescence calibration", subtitle="Follow one bead sample from peaks to calibration", accent=BLUE)

    slide = slide_base(presentation=presentation, number=7, title="Follow one calibration",
                       subtitle="Load bead data, select a channel, and pair the detected peaks", accent=BLUE)
    items = [("01 · DATA", "Load bead FCS", "Cytek Rainbow\nbead sample.", BLUE),
             ("02 · CHANNEL", "Select B2-A", "Automatic 1D\npeak detection.", TEAL),
             ("03 · REFERENCES", "Pair six peaks", "Match each peak to\na bead reference value.", GOLD),
             ("04 · CALIBRATE", "Fit and save", "Review the fit, then\nsave the calibration.", CORAL)]
    for index, (number, title, body, accent) in enumerate(items):
        x = 48 + index * 225
        geometry(slide=slide, x=x, y=141, width=189, height=126, fill=PALE, border=LINE)
        textbox(slide=slide, value=number, x=x + 14, y=155, width=161, height=20,
                size=11, bold=True, ink=accent)
        textbox(slide=slide, value=title, x=x + 14, y=184, width=161, height=28,
                size=18, bold=True)
        textbox(slide=slide, value=body, x=x + 14, y=219, width=161, height=42,
                size=14, ink=SLATE)
        if index < 3:
            arrow(slide=slide, number=7, x=x + 207, y=204)
    slide.shapes.add_picture(str(DIRECTORY / "slide7-rosettax-peak-graph.png"),
                             Pt(80), Pt(292), width=Pt(800), height=Pt(167))
    textbox(slide=slide, value="RosettaX output · B2-A signal · dashed lines mark the six detected peaks",
            x=80, y=474, width=800, height=23, size=12, ink=SLATE)

    slide = slide_base(presentation=presentation, number=8, title="Review the fit",
                       subtitle="Check the fit quality, sample range, and reference inputs", accent=BLUE)
    geometry(slide=slide, x=48, y=152, width=500, height=328, fill=PALE, border=LINE)
    textbox(slide=slide, value="Reference values (log scale)", x=75, y=168,
            width=320, height=20, size=12, ink=SLATE)
    textbox(slide=slide, value="SCHEMATIC", x=423, y=169, width=104, height=20,
            size=10, bold=True, ink=SLATE, align=PP_ALIGN.RIGHT)
    for y in (246, 302, 358):
        rule(slide=slide, x=84, y=y, width=428, weight=0.7)
    rule(slide=slide, x=84, y=424, width=428, ink=SLATE)
    axis = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Pt(84), Pt(207), Pt(84), Pt(424))
    axis.line.color.rgb = color(value=SLATE)
    axis.line.width = Pt(1)
    axis._element.spPr.append(OxmlElement("a:effectLst"))
    fit = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Pt(104), Pt(410), Pt(493), Pt(220))
    fit.line.color.rgb = color(value=TEAL)
    fit.line.width = Pt(2)
    fit._element.spPr.append(OxmlElement("a:effectLst"))
    for x, y in [(136, 393), (185, 366), (237, 349), (288, 317), (341, 299), (396, 264), (452, 245)]:
        geometry(slide=slide, x=x - 4, y=y - 4, width=8, height=8, fill=TEAL,
                 kind=MSO_SHAPE.OVAL, name="Illustrative bead point")
    textbox(slide=slide, value="Measured detector signal (log scale)", x=84, y=444,
            width=428, height=21, size=12, ink=SLATE, align=PP_ALIGN.CENTER)
    for index, (heading, body, accent) in enumerate([
        ("Check signal coverage", "Do bead signals span\nthe sample range?", BLUE),
        ("Inspect fit quality", "Do points follow the line\nwithout a clear pattern?", CORAL),
        ("Confirm reference inputs", "Do values match the bead\nlot and selected channel?", GOLD),
    ]):
        y = 168 + index * 104
        textbox(slide=slide, value=f"0{index + 1}", x=582, y=y, width=30,
                height=25, size=14, bold=True, ink=accent)
        textbox(slide=slide, value=heading, x=622, y=y - 2, width=290,
                height=28, size=19, bold=True)
        textbox(slide=slide, value=body, x=622, y=y + 34, width=290,
                height=57, size=17, ink=SLATE)

    slide = slide_base(presentation=presentation, number=9, title="Apply the calibration",
                       subtitle="Select the saved fit, match the channel, and export calibrated data", accent=BLUE)
    items = [("Saved calibration", "Load the fit,\nunits, and\nsource channel.", BLUE, "EDF4F8"),
             ("Load sample FCS", "Choose the new sample\nfiles to calibrate.", TEAL, "EDF6F3"),
             ("Match the channel", "Map the source channel,\nthen transform each event.", GOLD, "FFF7E7"),
             ("Calibrated FCS", "Export calibrated values\nfor further analysis.", GREEN, "F0F6F2")]
    for index, (title, body, accent, fill) in enumerate(items):
        x = 48 + index * 225
        step(slide=slide, x=x, y=177, width=189, height=168, number=f"0{index + 1}",
             title=title, body=body, accent=accent, fill=fill, title_size=17, body_size=14)
        if index < 3:
            arrow(slide=slide, number=9, x=x + 207, y=260)
    rule(slide=slide, x=48, y=394, width=864)
    textbox(slide=slide, value="Optional calibration report", x=48, y=414,
            width=864, height=30, size=21, bold=True)
    textbox(slide=slide, value="Export a PDF with calibration details to support MIFlowCyt-EV reporting.",
            x=48, y=455, width=864, height=27, size=17, ink=SLATE)

    section(presentation=presentation, number=10, index="03", label="Scattering",
            title="Scattering calibration", subtitle="Model the reference response before fitting", accent=GOLD)

    slide = slide_base(presentation=presentation, number=11, title="Model the scattering response",
                       subtitle="Enter particle and detector settings, calculate the response, then fit", accent=GOLD)
    for x in (48, 345, 642):
        geometry(slide=slide, x=x, y=153, width=270, height=283, fill=PALE, border=LINE)
    textbox(slide=slide, value="01 · MODEL INPUTS", x=68, y=174, width=230,
            height=23, size=12, bold=True, ink=GOLD)
    for index, value in enumerate(["Laser wavelength + medium", "Bead size + material",
                                   "Bead + medium refractive indices", "Detector geometry + collection angle"]):
        y = 215 + index * 49
        geometry(slide=slide, x=68, y=y + 7, width=5, height=5, fill=GOLD,
                 kind=MSO_SHAPE.OVAL, name="Input marker")
        textbox(slide=slide, value=value, x=84, y=y, width=215, height=45, size=15, ink=SLATE)
    textbox(slide=slide, value="02 · MIE MODEL", x=365, y=174, width=230,
            height=23, size=12, bold=True, ink=GOLD)
    textbox(slide=slide, value="Predict collected\nlight for each\nbead population", x=365, y=226,
            width=230, height=106, size=23, bold=True)
    textbox(slide=slide, value="Particle optics + detector geometry", x=365, y=380,
            width=230, height=43, size=15, ink=SLATE)
    textbox(slide=slide, value="03 · CALIBRATION FIT", x=662, y=174, width=230,
            height=23, size=12, bold=True, ink=GOLD)
    textbox(slide=slide, value="Pair peaks with\npredicted scatter", x=662, y=226,
            width=230, height=75, size=23, bold=True)
    textbox(slide=slide, value="Fit the relationship and save\nthe calibration with its settings.", x=662, y=344,
            width=230, height=67, size=16, ink=SLATE)
    arrow(slide=slide, number=11, x=331.5, y=294)
    arrow(slide=slide, number=11, x=628.5, y=294)
    textbox(slide=slide, value="The fitted result depends on the particle and detector assumptions.",
            x=48, y=464, width=864, height=27, size=17, bold=True, ink=SLATE)

    section(presentation=presentation, number=12, index="04", label="Tools and validation",
            title="Tools and validation", subtitle="Prepare the data and evaluate calibration across instruments")

    slide = slide_base(presentation=presentation, number=13, title="Supporting tools",
                       subtitle="Prepare files, inspect signals, and explore cross calibration", accent=GOLD)
    textbox(slide=slide, value="PREPARE & INSPECT", x=48, y=145, width=864,
            height=23, size=12, bold=True, ink=TEAL)
    tools = [(48, 183, "FCS Inspector", "Check channels and\nacquisition metadata.", BLUE),
             (345, 183, "Slicing", "Export selected channels\nwhile keeping all events.", TEAL),
             (642, 183, "FCS Merge", "Combine compatible\nFCS acquisitions.", GOLD),
             (196, 359, "FCS Visualization", "Explore distributions and\nchannel relationships.", CORAL),
             (493, 359, "Cross calibration", "Transfer to routine beads.\nExperimental workflow.", BLUE)]
    for x, y, title, body, accent in tools:
        geometry(slide=slide, x=x, y=y, width=270, height=120, fill=PALE, border=LINE)
        geometry(slide=slide, x=x + 17, y=y + 21, width=7, height=7, fill=accent,
                 kind=MSO_SHAPE.OVAL, name="Tool marker")
        textbox(slide=slide, value=title, x=x + 35, y=y + 14, width=218,
                height=30, size=18, bold=True)
        textbox(slide=slide, value=body, x=x + 17, y=y + 58, width=236,
                height=51, size=16, ink=SLATE)
    textbox(slide=slide, value="EXPLORE & TRANSFER", x=48, y=324, width=864,
            height=23, size=12, bold=True, ink=TEAL)

    slide = slide_base(presentation=presentation, number=14, title="Cross-device validation plan",
                       subtitle="Calibrate with Rosetta beads, then evaluate independent reference beads")
    workflow = [("01 · CALIBRATE", "Rosetta beads", "Fit the measured peaks\nto establish the calibration.", BLUE, "EDF4F8"),
                ("02 · APPLY", "Reference beads", "Apply the fit to independent\nbeads with a known diameter.", TEAL, "EDF6F3"),
                ("03 · COMPARE", "Recovered vs known size", "Compare the recovered size\nwith the reference diameter.", GOLD, "FFF7E7")]
    for index, (number, title, body, accent, fill) in enumerate(workflow):
        x = 48 + index * 297
        step(slide=slide, x=x, y=142, width=270, height=151, number=number,
             title=title, body=body, accent=accent, fill=fill, title_size=19, body_size=16)
        if index < 2:
            arrow(slide=slide, number=14, x=x + 283.5, y=217)
    textbox(slide=slide, value="10 INSTRUMENTS IN THE VALIDATION PLAN", x=48, y=325,
            width=864, height=25, size=13, bold=True, ink=TEAL)
    instruments = [("Apogee", "BD FACSCalibur"), ("Northern Lights", "BD FACSymphony A1"),
                   ("BD FACSLyric", "Beckman Coulter CytoFLEX S"),
                   ("BD FACSCanto I", "Miltenyi MACSQuant Analyzer 16"),
                   ("BD LSR II", "Stratedigm S1313EX")]
    for index, (left, right) in enumerate(instruments):
        y = 360 + index * 26
        textbox(slide=slide, value=left, x=48, y=y, width=405, height=24, size=17)
        textbox(slide=slide, value=right, x=492, y=y, width=420, height=24, size=17)

    section(presentation=presentation, number=15, index="05", label="Discussion",
            title="Conclusion and discussion", subtitle="Calibrate, apply, then validate")

    slide = slide_base(presentation=presentation, number=16, title="Try RosettaX",
                       subtitle="Start with a sample file and share the next validation question")
    textbox(slide=slide, value="rosettax.vesiclecenter.com", x=48, y=157,
            width=864, height=45, size=30, bold=True, ink=TEAL)
    textbox(slide=slide, value="Explore one workflow, then compare results across instruments.",
            x=48, y=216, width=864, height=54, size=21, ink=SLATE)
    for index, (title, body, accent) in enumerate([
        ("Explore", "Try the packaged\nsample FCS files.", BLUE),
        ("Compare", "Explore Rosetta bead examples\nacross ten instruments.", TEAL),
        ("Shape validation", "Suggest the next instrument\nor workflow to test.", GOLD),
    ]):
        x = 48 + index * 297
        geometry(slide=slide, x=x, y=319, width=270, height=140, fill=PALE, border=LINE)
        textbox(slide=slide, value=f"0{index + 1}", x=x + 18, y=337, width=32,
                height=22, size=12, bold=True, ink=accent)
        textbox(slide=slide, value=title, x=x + 18, y=367, width=234,
                height=28, size=20, bold=True)
        textbox(slide=slide, value=body, x=x + 18, y=407, width=234,
                height=46, size=15, ink=SLATE)
        if index < 2:
            arrow(slide=slide, number=16, x=x + 283.5, y=389)

    # Populate presenter notes through Keynote after import. Its PowerPoint
    # importer rejects the notes parts produced by python-pptx.
    output = DIRECTORY / "RosettaX_colleague_overview.pptx"
    presentation.save(output)
    style = dict(ARROW_STYLE)
    style["positions"] = ARROWS
    (DIRECTORY / "arrow-style.json").write_text(json.dumps(style, indent=2) + "\n")
    print(f"Saved {len(presentation.slides)} editable slides to {output}")


if __name__ == "__main__":
    main()
