from lxml import etree
from lxml.etree import _Element as Element

from .page import Page, TextRegion, TextLine

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


class SVGError(Exception):
    pass


def _coords_path(coords_str: str) -> str:
    return f"M {coords_str}"


def _baseline_path_d(line: TextLine) -> str:
    box = line.coords.polygon.bounding_box()
    y_baseline = box.top_left.y + (box.bottom_right.y - box.top_left.y) * 2 // 3
    return f"M {box.top_left.x},{y_baseline} {box.bottom_right.x},{y_baseline}"


def _line_to_svg(line: TextLine) -> Element:
    g = etree.Element(f"{{{SVG_NS}}}g", attrib={"id": line.id, "class": "TextLine"})
    etree.SubElement(
        g,
        f"{{{SVG_NS}}}path",
        attrib={
            "d": _coords_path(str(line.coords)),
            "class": "Coords",
        },
    )
    etree.SubElement(
        g,
        f"{{{SVG_NS}}}path",
        attrib={
            "id": f"bl-{line.id}",
            "d": _baseline_path_d(line),
            "class": "Baseline",
        },
    )
    if line.text:
        text = etree.SubElement(g, f"{{{SVG_NS}}}text")
        text_path = etree.SubElement(
            text,
            f"{{{SVG_NS}}}textPath",
            attrib={f"{{{XLINK_NS}}}href": f"#bl-{line.id}", "textLength": "100%"},
        )
        tspan = etree.SubElement(
            text_path, f"{{{SVG_NS}}}tspan", attrib={"class": "Text"}
        )
        tspan.text = line.text
    return g


def _region_to_svg(region: TextRegion) -> Element:
    g = etree.Element(f"{{{SVG_NS}}}g", attrib={"id": region.id, "class": "TextRegion"})
    etree.SubElement(
        g,
        f"{{{SVG_NS}}}path",
        attrib={
            "d": _coords_path(str(region.coords)),
            "class": "Coords",
        },
    )
    for line in region.textlines.values():
        g.append(_line_to_svg(line))
    return g


def page_to_svg(page: Page) -> Element:
    if page.image.width is None:
        raise SVGError("Image width is required for SVG generation")
    if page.image.height is None:
        raise SVGError("Image height is required for SVG generation")

    width = page.image.width
    height = page.image.height

    svg = etree.Element(
        f"{{{SVG_NS}}}svg",
        # the official way to do it although stubs are wrong:
        nsmap={None: SVG_NS, "xlink": XLINK_NS},  # type: ignore
        attrib={
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    etree.SubElement(
        svg,
        f"{{{SVG_NS}}}image",
        attrib={
            "x": "0",
            "y": "0",
            "width": str(width),
            "height": str(height),
            f"{{{XLINK_NS}}}href": page.image.filename,
            "preserveAspectRatio": "none",
        },
    )

    for region in page.regions.values():
        svg.append(_region_to_svg(region))

    return svg


def page_to_svg_string(page: Page) -> str:
    return etree.tostring(page_to_svg(page), encoding="unicode", pretty_print=True)
