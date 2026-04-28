from typing import Any

import pytest
from hypothesis import given
from lxml import etree
from lxml.etree import _Element as Element

from pygexml.strategies import st_pages_with_dimensions
from pygexml.image import Image
from pygexml.page import Coords, TextLine, TextRegion, Page
from pygexml.svg import SVGError, page_to_svg, page_to_svg_string

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def make_page(**kwargs: Any) -> Page:
    defaults: dict[str, Any] = dict(
        image=Image(filename="a.jpg", width=800, height=600),
        regions={},
    )
    return Page(**(defaults | kwargs))


############## Tests for page_to_svg ####################


def test_page_to_svg_raises_without_image_width() -> None:
    page = make_page(image=Image(filename="a.jpg", width=None, height=600))
    with pytest.raises(SVGError, match="width"):
        page_to_svg(page)


def test_page_to_svg_raises_without_image_height() -> None:
    page = make_page(image=Image(filename="a.jpg", width=800, height=None))
    with pytest.raises(SVGError, match="height"):
        page_to_svg(page)


def test_page_to_svg_returns_svg_element() -> None:
    svg = page_to_svg(make_page())
    assert isinstance(svg, Element)
    assert svg.tag == f"{{{SVG_NS}}}svg"


def test_page_to_svg_dimensions() -> None:
    svg = page_to_svg(make_page(image=Image(filename="a.jpg", width=800, height=600)))
    assert svg.attrib["width"] == "800"
    assert svg.attrib["height"] == "600"
    assert svg.attrib["viewBox"] == "0 0 800 600"


def test_page_to_svg_image_element() -> None:
    svg = page_to_svg(make_page(image=Image(filename="a.jpg", width=800, height=600)))
    images = svg.findall(f"{{{SVG_NS}}}image")
    assert len(images) == 1
    img = images[0]
    assert img.attrib[f"{{{XLINK_NS}}}href"] == "a.jpg"
    assert img.attrib["width"] == "800"
    assert img.attrib["height"] == "600"


def test_page_to_svg_text_regions() -> None:
    page = make_page(
        regions={
            "r1": TextRegion(
                id="r1",
                coords=Coords.parse("0,0 10,0 10,10 0,10"),
                textlines={
                    "l1": TextLine(
                        id="l1", coords=Coords.parse("1,1 9,1 9,9 1,9"), text="foo"
                    ),
                },
            ),
        }
    )
    svg = page_to_svg(page)
    groups = svg.findall(f"{{{SVG_NS}}}g")
    assert len(groups) == 1
    region_g = groups[0]
    assert region_g.attrib["id"] == "r1"
    assert region_g.attrib["class"] == "TextRegion"
    line_groups = region_g.findall(f"{{{SVG_NS}}}g")
    assert len(line_groups) == 1
    assert line_groups[0].attrib["id"] == "l1"
    assert line_groups[0].attrib["class"] == "TextLine"


def test_page_to_svg_coords_path() -> None:
    page = make_page(
        regions={
            "r1": TextRegion(
                id="r1",
                coords=Coords.parse("0,0 10,0 10,10 0,10"),
                textlines={},
            ),
        }
    )
    svg = page_to_svg(page)
    region_g = svg.find(f"{{{SVG_NS}}}g")
    assert region_g is not None
    path = region_g.find(f"{{{SVG_NS}}}path")
    assert path is not None
    assert path.attrib["d"] == "M 0,0 10,0 10,10 0,10"
    assert path.attrib["class"] == "Coords"


############## Tests for page_to_svg_string ####################


def test_page_to_svg_string_example() -> None:
    result = page_to_svg_string(
        make_page(image=Image(filename="a.jpg", width=800, height=600))
    )
    assert isinstance(result, str)
    assert 'xmlns="http://www.w3.org/2000/svg"' in result
    assert 'xlink:href="a.jpg"' in result
    assert 'viewBox="0 0 800 600"' in result


def test_page_to_svg_string_is_valid_xml() -> None:
    result = page_to_svg_string(make_page())
    root = etree.fromstring(result.encode("utf-8"))
    assert root.tag == f"{{{SVG_NS}}}svg"


def test_page_to_svg_string_raises_without_dimensions() -> None:
    page = make_page(image=Image(filename="a.jpg", width=None, height=None))
    with pytest.raises(SVGError):
        page_to_svg_string(page)


@given(st_pages_with_dimensions())
def test_page_to_svg_string_arbitrary_with_dimensions(page: Page) -> None:
    result = page_to_svg_string(page)
    root = etree.fromstring(result.encode("utf-8"))
    assert root.tag == f"{{{SVG_NS}}}svg"


def test_page_to_svg_includes_style_by_default() -> None:
    svg = page_to_svg(make_page())
    assert svg.find(f"{{{SVG_NS}}}style") is not None


def test_page_to_svg_style_contains_hover_rule() -> None:
    svg = page_to_svg(make_page())
    style = svg.find(f"{{{SVG_NS}}}style")
    assert style is not None
    assert ".TextLine:hover" in (style.text or "")


def test_page_to_svg_no_style_when_disabled() -> None:
    svg = page_to_svg(make_page(), include_style=False)
    assert svg.find(f"{{{SVG_NS}}}style") is None


def test_page_to_svg_string_no_style_when_disabled() -> None:
    result = page_to_svg_string(make_page(), include_style=False)
    assert "<style" not in result


############## Tests for text rendering ####################


def make_page_with_line(text: str = "foo") -> Page:
    return make_page(
        regions={
            "r1": TextRegion(
                id="r1",
                coords=Coords.parse("0,0 10,0 10,10 0,10"),
                textlines={
                    "l1": TextLine(
                        id="l1", coords=Coords.parse("1,1 9,1 9,9 1,9"), text=text
                    ),
                },
            ),
        }
    )


def get_line_g(page: Page) -> Element:
    svg = page_to_svg(page)
    region_g = svg.find(f"{{{SVG_NS}}}g")
    assert region_g is not None
    line_g = region_g.find(f"{{{SVG_NS}}}g")
    assert line_g is not None
    return line_g


def test_page_to_svg_line_has_baseline_path() -> None:
    line_g = get_line_g(make_page_with_line())
    paths = line_g.findall(f"{{{SVG_NS}}}path")
    assert len(paths) == 2
    baseline = next(p for p in paths if p.attrib.get("class") == "Baseline")
    assert baseline.attrib["id"] == "bl-l1"


def test_page_to_svg_line_baseline_from_bounding_box() -> None:
    # coords "1,1 9,1 9,9 1,9": x=[1,9], y=[1,9], height=8, y_baseline=1+8*2//3=6
    line_g = get_line_g(make_page_with_line())
    paths = line_g.findall(f"{{{SVG_NS}}}path")
    baseline = next(p for p in paths if p.attrib.get("class") == "Baseline")
    assert baseline.attrib["d"] == "M 1,6 9,6"


def test_page_to_svg_line_text_content() -> None:
    line_g = get_line_g(make_page_with_line("Hallo Welt"))
    text = line_g.find(f"{{{SVG_NS}}}text")
    assert text is not None
    text_path = text.find(f"{{{SVG_NS}}}textPath")
    assert text_path is not None
    assert text_path.attrib[f"{{{XLINK_NS}}}href"] == "#bl-l1"
    tspan = text_path.find(f"{{{SVG_NS}}}tspan")
    assert tspan is not None
    assert tspan.text == "Hallo Welt"
    assert tspan.attrib["class"] == "Text"


def test_page_to_svg_line_no_text_element_when_empty() -> None:
    line_g = get_line_g(make_page_with_line(""))
    assert line_g.find(f"{{{SVG_NS}}}text") is None
