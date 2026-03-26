from pathlib import Path

import pytest
from hypothesis import given, assume
import hypothesis.strategies as st

from lxml import etree

from pygexml.strategies import *
from pygexml.geometry import Point, Box, Polygon
from pygexml.page import Coords, TextLine, TextRegion, Page

############## Tests for Coords ####################


def test_coords_example() -> None:
    polygon = Polygon(points=[Point(1, 2), Point(3, 4)])
    coords = Coords(polygon=polygon)
    assert coords.polygon == polygon


def test_coords_with_not_enough_points() -> None:
    with pytest.raises(Exception, match="At least 2 Points"):
        Coords(polygon=Polygon(points=[Point(17, 42)]))


def test_coords_stringification() -> None:
    coords = Coords(polygon=Polygon(points=[Point(1, 2), Point(17, 42)]))
    assert str(coords) == "1,2 17,42"


def test_coords_parse_example() -> None:
    coords = Coords.parse("1,2 17,42")
    assert coords.polygon.points == [Point(1, 2), Point(17, 42)]


def test_coords_parse_invalid_inputs() -> None:
    with pytest.raises(Exception, match="Invalid Coords XML string"):
        Coords.parse("17,42 666,42 SCDH, yay!")
    with pytest.raises(Exception, match="Invalid Coords XML string"):
        Coords.parse("")
    with pytest.raises(Exception, match="Invalid Coords XML string"):
        Coords.parse("17,42")


def test_coords_allow_for_simple_negative_coordinates() -> None:
    with pytest.warns(
        UserWarning, match=r".*does not match the PAGE XMl spec: 1,-2 -3,4"
    ):
        coords = Coords.parse("1,-2 -3,4")
        assert coords.polygon.points == [Point(1, -2), Point(-3, 4)]


@given(st_coords)
def test_coords_parse_arbitrary(coords: Coords) -> None:
    assert Coords.parse(str(coords)) == coords


def test_coords_from_box_example() -> None:
    box = Box(top_left=Point(17, 17), bottom_right=Point(42, 42))
    coords = Coords.from_box(box)
    assert coords.polygon.points == [
        Point(17, 17),
        Point(42, 17),
        Point(42, 42),
        Point(17, 42),
    ]


@given(st_boxes)
def test_coords_from_box(box: Box) -> None:
    coords = Coords.from_box(box)
    assert coords.polygon == Polygon.from_box(box)


@given(st_coords_strings)
def test_coords_stringify_arbitrary(coords_str: str) -> None:
    coords_object = Coords.parse(coords_str)
    assert str(coords_object) == coords_str


############## Tests for TextLines ####################


def test_textline_simple_parsing_example() -> None:
    tl = TextLine.from_xml(etree.fromstring("""
        <TextLine id="tl-id">
            <Coords points="17,42 1,2"/>
            <TextEquiv>
                <Unicode>tl-text</Unicode>
            </TextEquiv>
        </TextLine>
    """))
    assert tl.id == "tl-id"
    assert tl.coords == Coords.parse("17,42 1,2")
    assert tl.text == "tl-text"


def test_textline_wrong_element() -> None:
    with pytest.raises(Exception, match="Wrong element given"):
        TextLine.from_xml(etree.fromstring("<WRONG>!!!</WRONG>"))


def test_textline_no_id() -> None:
    xml = etree.fromstring("<TextLine></TextLine>")
    with pytest.raises(Exception, match="No id found"):
        TextLine.from_xml(xml)


def test_textline_no_coords() -> None:
    xml = etree.fromstring("""
        <TextLine id="tl-id">
            <TextEquiv>
                <Unicode>tl-text</Unicode>
            </TextEquiv>
        </TextLine>
    """)
    with pytest.raises(Exception, match="No Coords found"):
        TextLine.from_xml(xml)


def test_textline_no_text() -> None:
    xml = etree.fromstring("""
        <TextLine id="tl-id">
            <Coords points="0,0 10,0 10,10 0,10"/>
            <TextEquiv>
            </TextEquiv>
        </TextLine>
    """)
    with pytest.raises(Exception, match="No text found"):
        TextLine.from_xml(xml)


def test_textline_empty_text() -> None:
    xml = etree.fromstring("""
        <TextLine id="tl-id">
            <Coords points="1,2 3,4"/>
            <TextEquiv>
                <Unicode/>
            </TextEquiv>
        </TextLine>
    """)
    assert TextLine.from_xml(xml).text == ""


def test_textline_alto_example() -> None:
    tl = TextLine.from_alto(etree.fromstring("""
        <TextLine ID="tl-id" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
            <String CONTENT="foo"/>
            <SP/>
            <String CONTENT="bar"/>
        </TextLine>
    """))
    assert tl.id == "tl-id"
    assert tl.coords == Coords.from_box(
        Box(top_left=Point(1, 2), bottom_right=Point(4, 6))
    )
    assert tl.text == "foo bar"


def test_textline_alto_wrong_element() -> None:
    with pytest.raises(Exception, match="Wrong element given"):
        TextLine.from_alto(etree.fromstring("<WRONG>!!!</WRONG>"))


def test_textline_alto_no_id() -> None:
    xml = etree.fromstring(
        """<TextLine HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4"></TextLine>"""
    )
    with pytest.raises(Exception, match="No ID found"):
        TextLine.from_alto(xml)


def test_textline_alto_missing_box_attributes() -> None:
    xml = etree.fromstring(
        """<TextLine ID="tl-id" HPOS="1" VPOS="2" WIDTH="3"></TextLine>"""
    )
    with pytest.raises(Exception, match="Missing one of the box attributes"):
        TextLine.from_alto(xml)


def test_textline_alto_no_text_elements() -> None:
    xml = etree.fromstring("""
        <TextLine ID="tl-id" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
        </TextLine>
    """)
    with pytest.raises(Exception, match="No text elements found"):
        TextLine.from_alto(xml)


def test_textline_alto_empty_text() -> None:
    xml = etree.fromstring("""
        <TextLine ID="tl-id" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
            <String/>
            <SP/>
        </TextLine>
    """)
    assert TextLine.from_alto(xml).text == " "


def test_textline_simple_words() -> None:
    tl = TextLine("", Coords.parse("1,2 3,4"), "foo  bar baz ")
    assert tl.words() == ["foo", "bar", "baz"]


@given(st_text_lines)
def test_textline_words(tl: TextLine) -> None:
    assert tl.words() == tl.text.split()


def test_textline_serialization_roundtrip() -> None:
    tl = TextLine(id="tl-id", coords=Coords.parse("1,2 3,4"), text="foo bar")
    assert TextLine.from_dict(tl.to_dict()) == tl


####### Tests for TextRegion ###############


def test_textregion_simple_parsing_example() -> None:
    tr = TextRegion.from_xml(etree.fromstring("""
        <TextRegion id="tr-id">
            <Coords points="1,2 8,9"/>
            <TextLine id="tl-1">
                <Coords points="17,42 1,2"/>
                <TextEquiv>
                    <Unicode>bla</Unicode>
                </TextEquiv>
            </TextLine>

            <TextLine id="tl-2">
                <Coords points="20,38 2,2"/>
                <TextEquiv>
                    <Unicode>blub</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
        """))
    assert tr.id == "tr-id"
    assert tr.coords == Coords.parse("1,2 8,9")
    assert tr.textlines == {
        "tl-1": TextLine(
            id="tl-1",
            coords=Coords.parse("17,42 1,2"),
            text="bla",
        ),
        "tl-2": TextLine(
            id="tl-2",
            coords=Coords.parse("20,38 2,2"),
            text="blub",
        ),
    }


def test_textregion_wrong_element() -> None:
    with pytest.raises(Exception, match="Wrong element given"):
        TextRegion.from_xml(etree.fromstring("<WRONG>!!!</WRONG>"))


def test_textregion_no_id() -> None:
    xml = etree.fromstring("<TextRegion></TextRegion>")
    with pytest.raises(Exception, match="No id found"):
        TextRegion.from_xml(xml)


def test_textregion_no_coords() -> None:
    xml = etree.fromstring("""
        <TextRegion id="tr-id">
            <TextLine id="tl-1">
                <TextEquiv>
                    <Unicode>bla</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    """)
    with pytest.raises(Exception, match="No Coords element found"):
        TextRegion.from_xml(xml)


def test_textregion_alto_example() -> None:
    tr = TextRegion.from_alto(etree.fromstring("""
        <TextBlock ID="tr-id" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
            <TextLine ID="tl-1" HPOS="2" VPOS="3" WIDTH="4" HEIGHT="5">
                <String CONTENT="foo"/>
            </TextLine>
        </TextBlock>
    """))
    assert tr.id == "tr-id"
    assert tr.coords == Coords.parse("1,2 4,2 4,6 1,6")
    assert tr.textlines == {
        "tl-1": TextLine(
            id="tl-1",
            coords=Coords.parse("2,3 6,3 6,8 2,8"),
            text="foo",
        )
    }


def test_textregion_alto_wrong_element() -> None:
    with pytest.raises(Exception, match="Wrong element given"):
        TextRegion.from_alto(etree.fromstring("<WRONG>!!!</WRONG>"))


def test_textregion_alto_no_id() -> None:
    xml = etree.fromstring(
        """<TextBlock HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4"></TextBlock>"""
    )
    with pytest.raises(Exception, match="No ID found"):
        TextRegion.from_alto(xml)


def test_textregion_alto_missing_box_attributes() -> None:
    xml = etree.fromstring(
        """<TextBlock ID="tr-id" HPOS="1" VPOS="2" WIDTH="3"></TextBlock>"""
    )
    with pytest.raises(Exception, match="Missing one of the box attributes"):
        TextRegion.from_alto(xml)


def test_textregion_alto_no_textlines() -> None:
    xml = etree.fromstring("""
        <TextBlock ID="tr-id" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
        </TextBlock>
    """)
    with pytest.raises(Exception, match="No TextLine elements found"):
        TextRegion.from_alto(xml)


@given(st_text_lines, st_text_regions)
def test_textregion_line_lookup(line: TextLine, region: TextRegion) -> None:
    assume(not line.id in region.textlines)
    region.textlines[line.id] = line
    assert region.lookup_textline(line.id) == line


@given(st.text(), st_text_regions)
def test_textregion_line_lookup_not_found(id: str, region: TextRegion) -> None:
    assume(not id in region.textlines)
    assert region.lookup_textline(id) is None


def test_textregion_all_text_and_words() -> None:
    tr = TextRegion(
        id="a",
        coords=Coords.parse("1,2 3,4"),
        textlines={
            "b": TextLine(id="b", coords=Coords.parse("2,3 4,5"), text="foo"),
            "c": TextLine(id="c", coords=Coords.parse("2,3 4,5"), text="bar  baz "),
        },
    )
    assert list(tr.all_text()) == ["foo", "bar  baz "]
    assert list(tr.all_words()) == ["foo", "bar", "baz"]


@given(st_text_regions)
def test_textregion_all_arbitrary_text_and_words(region: TextRegion) -> None:
    assert list(region.all_text()) == [tl.text for tl in region.textlines.values()]
    assert list(region.all_words()) == [
        w for tl in region.textlines.values() for w in tl.words()
    ]


def test_textregion_serialization_roundtrip() -> None:
    tr = TextRegion(
        id="tr-id",
        coords=Coords.parse("1,2 3,4"),
        textlines={
            "tl-1": TextLine(id="tl-1", coords=Coords.parse("1,2 3,4"), text="foo")
        },
    )
    assert TextRegion.from_dict(tr.to_dict()) == tr


############### Tests for Page ####################


def test_page_from_element_example() -> None:
    pa = Page.from_xml(etree.fromstring("""
        <Page imageFilename="7895328.jpg" imageWidth="4279" imageHeight="5315">
            <TextRegion id="tr-1">
                <Coords points="1,2 8,9"/>
                <TextLine id="tl-1">
                    <Coords points="17,42 1,2"/>
                    <TextEquiv>
                        <Unicode>bla</Unicode>
                    </TextEquiv>
                </TextLine>
                <TextLine id="tl-2">
                    <Coords points="20,38 2,2"/>
                    <TextEquiv>
                        <Unicode>blub</Unicode>
                    </TextEquiv>
                </TextLine>
            </TextRegion>

            <TextRegion id="tr-2">
                <Coords points="1,2 8,9"/>
                <TextLine id="tl-1">
                    <Coords points="17,42 1,2"/>
                    <TextEquiv>
                        <Unicode>bla</Unicode>
                    </TextEquiv>
                </TextLine>
                <TextLine id="tl-2">
                    <Coords points="20,38 2,2"/>
                    <TextEquiv>
                        <Unicode>blub</Unicode>
                    </TextEquiv>
                </TextLine>
            </TextRegion>
        </Page>
    """))

    assert pa.image_filename == "7895328.jpg"
    assert pa.regions == {
        "tr-1": TextRegion(
            id="tr-1",
            coords=Coords.parse("1,2 8,9"),
            textlines={
                "tl-1": TextLine(
                    id="tl-1",
                    coords=Coords.parse("17,42 1,2"),
                    text="bla",
                ),
                "tl-2": TextLine(
                    id="tl-2",
                    coords=Coords.parse("20,38 2,2"),
                    text="blub",
                ),
            },
        ),
        "tr-2": TextRegion(
            id="tr-2",
            coords=Coords.parse("1,2 8,9"),
            textlines={
                "tl-1": TextLine(
                    id="tl-1",
                    coords=Coords.parse("17,42 1,2"),
                    text="bla",
                ),
                "tl-2": TextLine(
                    id="tl-2",
                    coords=Coords.parse("20,38 2,2"),
                    text="blub",
                ),
            },
        ),
    }


def test_page_wrong_element() -> None:
    with pytest.raises(Exception, match="Wrong element given"):
        Page.from_xml(etree.fromstring("<WRONG>!!!</WRONG>"))


def test_page_no_filename() -> None:
    xml = "<Page></Page>"
    with pytest.raises(Exception, match="No filename found"):
        Page.from_xml(etree.fromstring(xml))


def test_page_from_string() -> None:
    pa = Page.from_xml_string("""<?xml version='1.0' encoding='utf-8'?>
        <PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd">
            <Metadata>
                <Creator>God</Creator>
                <Created>Sonntag</Created>
            </Metadata>
            <Page imageFilename="a.jpg" imageWidth="4217" imageHeight="1742">
                <TextRegion id="b">
                    <Coords points="1,2 3,4"/>
                    <TextLine id="c" index="0" custom="heights_v2:[91.0,32.1]">
                        <Coords points="5,6 7,8"/>
                        <Baseline points="2008,360 2208,352"/>
                        <TextEquiv conf="0.932">
                        <Unicode>d</Unicode>
                        </TextEquiv>
                    </TextLine>
                </TextRegion>
            </Page>
        </PcGts>
    """)  # use default PageXML namespace
    assert pa.image_filename == "a.jpg"
    assert pa.regions == {
        "b": TextRegion(
            id="b",
            coords=Coords.parse("1,2 3,4"),
            textlines={"c": TextLine(id="c", coords=Coords.parse("5,6 7,8"), text="d")},
        )
    }


def test_from_xml_file_example(tmp_path: Path) -> None:
    content = """<?xml version='1.0' encoding='utf-8'?>
            <PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd">
                <Metadata>
                    <Creator>God</Creator>
                    <Created>Sonntag</Created>
                </Metadata>
                <Page imageFilename="a.jpg" imageWidth="4217" imageHeight="1742">
                    <TextRegion id="b">
                        <Coords points="1,2 3,4"/>
                        <TextLine id="c" index="0" custom="heights_v2:[91.0,32.1]">
                            <Coords points="5,6 7,8"/>
                            <Baseline points="2008,360 2208,352"/>
                            <TextEquiv conf="0.932">
                            <Unicode>d</Unicode>
                            </TextEquiv>
                        </TextLine>
                    </TextRegion>
                </Page>
            </PcGts>
        """

    xml_filepath = tmp_path / "test.xml"
    xml_filepath.write_text(content, encoding="utf-8")

    result = Page.from_xml_file(xml_filepath)
    assert result.image_filename == "a.jpg"
    assert result.regions == {
        "b": TextRegion(
            id="b",
            coords=Coords.parse("1,2 3,4"),
            textlines={"c": TextLine(id="c", coords=Coords.parse("5,6 7,8"), text="d")},
        )
    }
    assert result == Page.from_xml_string(content)


def test_from_missing_xml_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "does_not_exist.xml"
    assert not missing_file.exists()
    with pytest.raises(FileNotFoundError):
        Page.from_xml_file(missing_file)


def test_page_from_alto_example() -> None:
    pa = Page.from_alto(etree.fromstring("""
        <alto>
            <Description>
                <sourceImageInformation>
                    <fileName>a.jpg</fileName>
                </sourceImageInformation>
            </Description>

            <Layout>
                <Page>
                    <PrintSpace>
                        <TextBlock ID="tr-1" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
                            <TextLine ID="tl-1" HPOS="2" VPOS="3" WIDTH="4" HEIGHT="5">
                                <String CONTENT="foo"/>
                                <SP/>
                                <String CONTENT="bar"/>
                            </TextLine>
                        </TextBlock>
                        <TextBlock ID="tr-2" HPOS="3" VPOS="4" WIDTH="5" HEIGHT="6">
                            <TextLine ID="tl-2" HPOS="4" VPOS="5" WIDTH="6" HEIGHT="7">
                                <String CONTENT="baz"/>
                            </TextLine>
                        </TextBlock>
                    </PrintSpace>
                </Page>
            </Layout>
        </alto>
    """))
    assert pa.image_filename == "a.jpg"
    assert pa.regions == {
        "tr-1": TextRegion(
            id="tr-1",
            coords=Coords.parse("1,2 4,2 4,6 1,6"),
            textlines={
                "tl-1": TextLine(
                    id="tl-1",
                    coords=Coords.parse("2,3 6,3 6,8 2,8"),
                    text="foo bar",
                )
            },
        ),
        "tr-2": TextRegion(
            id="tr-2",
            coords=Coords.parse("3,4 8,4 8,10 3,10"),
            textlines={
                "tl-2": TextLine(
                    id="tl-2",
                    coords=Coords.parse("4,5 10,5 10,12 4,12"),
                    text="baz",
                )
            },
        ),
    }


def test_page_alto_wrong_element() -> None:
    with pytest.raises(Exception, match="Wrong element given"):
        Page.from_alto(etree.fromstring("<WRONG>!!!</WRONG>"))


def test_page_alto_no_description() -> None:
    xml = etree.fromstring("<alto></alto>")
    with pytest.raises(Exception, match="No Description element found"):
        Page.from_alto(xml)


def test_page_alto_no_source_image_information() -> None:
    xml = etree.fromstring("<alto><Description></Description></alto>")
    with pytest.raises(Exception, match="No sourceImageInformation element found"):
        Page.from_alto(xml)


def test_page_alto_no_filename() -> None:
    xml = etree.fromstring("""
        <alto>
            <Description>
                <sourceImageInformation></sourceImageInformation>
            </Description>
        </alto>
    """)
    with pytest.raises(Exception, match="No fileName element found"):
        Page.from_alto(xml)


def test_page_alto_no_layout() -> None:
    xml = etree.fromstring("""
        <alto>
            <Description>
                <sourceImageInformation>
                    <fileName>a.jpg</fileName>
                </sourceImageInformation>
            </Description>
        </alto>
    """)
    with pytest.raises(Exception, match="No Layout element found"):
        Page.from_alto(xml)


def test_page_alto_no_page() -> None:
    xml = etree.fromstring("""
        <alto>
            <Description>
                <sourceImageInformation>
                    <fileName>a.jpg</fileName>
                </sourceImageInformation>
            </Description>
            <Layout></Layout>
        </alto>
    """)
    with pytest.raises(Exception, match="No Page element found"):
        Page.from_alto(xml)


def test_page_alto_no_print_space() -> None:
    xml = etree.fromstring("""
        <alto>
            <Description>
                <sourceImageInformation>
                    <fileName>a.jpg</fileName>
                </sourceImageInformation>
            </Description>
            <Layout>
                <Page></Page>
            </Layout>
        </alto>
    """)
    with pytest.raises(Exception, match="No PrintSpace element found"):
        Page.from_alto(xml)


def test_page_alto_from_string() -> None:
    alto_string = """
        <alto>
            <Description>
                <sourceImageInformation>
                    <fileName>a.jpg</fileName>
                </sourceImageInformation>
            </Description>

            <Layout>
                <Page>
                    <PrintSpace>
                        <TextBlock ID="tr-1" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
                            <TextLine ID="tl-1" HPOS="2" VPOS="3" WIDTH="4" HEIGHT="5">
                                <String CONTENT="foo"/>
                            </TextLine>
                        </TextBlock>
                    </PrintSpace>
                </Page>
            </Layout>
        </alto>
    """
    page = Page.from_alto_string(alto_string)
    assert page.image_filename == "a.jpg"
    assert page.regions == {
        "tr-1": TextRegion(
            id="tr-1",
            coords=Coords.parse("1,2 4,2 4,6 1,6"),
            textlines={
                "tl-1": TextLine(
                    id="tl-1",
                    coords=Coords.parse("2,3 6,3 6,8 2,8"),
                    text="foo",
                )
            },
        )
    }


def test_page_alto_from_file_example(tmp_path: Path) -> None:
    alto_string = """
        <alto>
            <Description>
                <sourceImageInformation>
                    <fileName>a.jpg</fileName>
                </sourceImageInformation>
            </Description>

            <Layout>
                <Page>
                    <PrintSpace>
                        <TextBlock ID="tr-1" HPOS="1" VPOS="2" WIDTH="3" HEIGHT="4">
                            <TextLine ID="tl-1" HPOS="2" VPOS="3" WIDTH="4" HEIGHT="5">
                                <String CONTENT="foo"/>
                            </TextLine>
                        </TextBlock>
                    </PrintSpace>
                </Page>
            </Layout>
        </alto>
    """

    filepath = tmp_path / "test_alto.xml"
    filepath.write_text(alto_string, encoding="utf-8")

    result = Page.from_alto_file(filepath)
    assert result.image_filename == "a.jpg"
    assert result.regions == {
        "tr-1": TextRegion(
            id="tr-1",
            coords=Coords.parse("1,2 4,2 4,6 1,6"),
            textlines={
                "tl-1": TextLine(
                    id="tl-1",
                    coords=Coords.parse("2,3 6,3 6,8 2,8"),
                    text="foo",
                )
            },
        )
    }
    assert result == Page.from_alto_string(alto_string)


def test_page_alto_from_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "does_not_exist.xml"
    assert not missing_file.exists()
    with pytest.raises(FileNotFoundError):
        Page.from_alto_file(missing_file)


@given(st_text_regions, st_pages())
def test_page_region_lookup(region: TextRegion, page: Page) -> None:
    assume(region.id not in page.regions)
    page.regions[region.id] = region
    assert page.lookup_region(region.id) == region


@given(st.text(), st_pages())
def test_page_region_lookup_not_found(id: str, page: Page) -> None:
    assume(id not in page.regions)
    assert page.lookup_region(id) is None


def test_page_all_text_and_words() -> None:
    pa = Page(
        image_filename="a",
        regions={
            "a": TextRegion(
                id="a",
                coords=Coords.parse("1,2 3,4"),
                textlines={
                    "b": TextLine(id="b", coords=Coords.parse("2,3 4,5"), text="foo"),
                    "c": TextLine(id="c", coords=Coords.parse("2,3 4,5"), text="bar"),
                },
            ),
            "c": TextRegion(
                id="c",
                coords=Coords.parse("1,2 3,4"),
                textlines={
                    "b": TextLine(id="b", coords=Coords.parse("2,3 4,5"), text="bla"),
                    "c": TextLine(
                        id="c", coords=Coords.parse("2,3 4,5"), text="blub 42"
                    ),
                },
            ),
        },
    )
    assert list(pa.all_text()) == ["foo", "bar", "bla", "blub 42"]
    assert list(pa.all_words()) == ["foo", "bar", "bla", "blub", "42"]


@given(st_pages())
def test_page_all_arbitrary_text_and_words(page: Page) -> None:
    assert list(page.all_text()) == [
        t for r in page.regions.values() for t in r.all_text()
    ]
    assert list(page.all_words()) == [
        w for r in page.regions.values() for w in r.all_words()
    ]


def test_page_serialization_roundtrip() -> None:
    pa = Page(
        image_filename="a.jpg",
        regions={
            "tr-1": TextRegion(
                id="tr-1",
                coords=Coords.parse("1,2 3,4"),
                textlines={
                    "tl-1": TextLine(
                        id="tl-1", coords=Coords.parse("1,2 3,4"), text="foo"
                    )
                },
            )
        },
    )
    assert Page.from_dict(pa.to_dict()) == pa
