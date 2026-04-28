import pytest
from hypothesis import given
from lxml import etree
from lxml.etree import _Element as Element

from pygexml.strategies import st_pages_with_dimensions
from pygexml.image import Image
from pygexml.page import Coords, TextLine, TextRegion, Page
from pygexml.svg import SVGError, page_to_svg, page_to_svg_string

SVG_NS = "http://www.w3.org/2000/svg"


def make_page(**kwargs) -> Page:
    defaults: dict = dict(
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
    assert img.attrib["href"] == "a.jpg"
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
    assert 'href="a.jpg"' in result
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
