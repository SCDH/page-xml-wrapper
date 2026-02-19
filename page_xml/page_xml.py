from re import Pattern, compile
from warnings import warn
from dataclasses import dataclass
from typing import ClassVar
from collections.abc import Iterable
from lxml import etree
from lxml.etree import _Element as Element, QName

from .geometry import Point, Polygon, GeometryError


def find_child(element: Element, name: str) -> Element | None:
    for child in element:
        if QName(child).localname == name:
            return child
    return None


def find_children(element: Element, name: str) -> Iterable[Element]:
    return (child for child in element if QName(child).localname == name)


class PageXMLError(Exception):
    pass


@dataclass
class Coords:
    polygon: Polygon

    # Loose regex that allows for negative values that can be handled by
    # our code. Context: PeroOCR sometimes produces PageXML with negative
    # coordinate values.
    # https://github.com/DCGM/pero-ocr/issues/84#issuecomment-3745059403
    LOOSE_PATTERN: ClassVar[Pattern[str]] = compile(
        r"^(-?[0-9]+,-?[0-9]+ )+(-?[0-9]+,-?[0-9]+)$"
    )

    # Regex from official Page-XML spec
    STRICT_PATTERN: ClassVar[Pattern[str]] = compile(
        r"^([0-9]+,[0-9]+ )+([0-9]+,[0-9]+)$"
    )

    _NOT_ENOUGH_POINTS: ClassVar[str] = "Coords: at least 2 Points are required"

    def __post_init__(self) -> None:
        if len(self.polygon.points) < 2:
            raise PageXMLError(Coords._NOT_ENOUGH_POINTS)

    def __str__(self) -> str:
        return " ".join(str(p) for p in self.polygon.points)

    @classmethod
    def parse(cls, points_str: str) -> "Coords":

        if not cls.LOOSE_PATTERN.match(points_str):
            raise PageXMLError("Invalid Coords XML string")

        if not cls.STRICT_PATTERN.match(points_str):
            warn(
                "Warning: Coords XML string does not match the PAGE XMl spec: "
                + points_str
            )

        points: list[Point] = []
        for pair_str in points_str.split(" "):
            [x, y] = pair_str.split(",")
            points.append(Point(x=int(x), y=int(y)))

        try:
            polygon = Polygon(points=points)
        except GeometryError:
            raise PageXMLError(cls._NOT_ENOUGH_POINTS)

        return Coords(polygon=polygon)


type ID = str


@dataclass
class TextLine:
    id: ID
    coords: Coords
    text: str

    def words(self) -> Iterable[str]:
        return self.text.split()

    @classmethod
    def from_xml(cls, element: Element) -> "TextLine":
        if QName(element).localname != "TextLine":
            raise PageXMLError("TextLine: wrong element given")
        if "id" not in element.attrib:
            raise PageXMLError("TextLine: no id found")
        coords_element = find_child(element, "Coords")
        if coords_element is None:
            raise PageXMLError("TextLine: no Coords found")
        if "points" not in coords_element.attrib:
            raise PageXMLError("TextLine: Coords has no points attribute")
        text_equiv = find_child(element, "TextEquiv")
        text_element = (
            find_child(text_equiv, "Unicode") if text_equiv is not None else None
        )
        if text_element is None:
            raise PageXMLError("TextLine: no text found")
        return TextLine(
            id=str(element.attrib["id"]),
            coords=Coords.parse(str(coords_element.attrib["points"])),
            text=text_element.text if text_element.text is not None else "",
        )


@dataclass
class TextRegion:
    id: ID
    coords: Coords
    textlines: dict[ID, TextLine]

    @classmethod
    def from_xml(cls, element: Element) -> "TextRegion":
        if QName(element).localname != "TextRegion":
            raise PageXMLError("TextRegion: wrong element given")
        if "id" not in element.attrib:
            raise PageXMLError("TextRegion: no id found")
        coords_element = find_child(element, "Coords")
        if coords_element is None:
            raise PageXMLError("TextRegion: no Coords element found")
        if "points" not in coords_element.attrib:
            raise PageXMLError("TextRegion: Coords has no points attribute")
        text_lines = find_children(element, "TextLine")

        return TextRegion(
            id=str(element.attrib["id"]),
            coords=Coords.parse(str(coords_element.attrib["points"])),
            textlines={
                tl.id: tl for tl in (TextLine.from_xml(tl) for tl in text_lines)
            },
        )

    def lookup_textline(self, id: ID) -> TextLine | None:
        return self.textlines.get(id)

    def all_text(self) -> Iterable[str]:
        return (tl.text for tl in self.textlines.values())

    def all_words(self) -> Iterable[str]:
        return (w for tl in self.textlines.values() for w in tl.words())


@dataclass
class Page:
    image_filename: str
    regions: dict[ID, TextRegion]

    @classmethod
    def from_xml(cls, element: Element) -> "Page":
        if QName(element).localname != "Page":
            raise PageXMLError("Page: wrong element given")

        if "imageFilename" not in element.attrib:
            raise PageXMLError("Page: no filename found")

        regions = find_children(element, "TextRegion")

        return Page(
            image_filename=str(element.attrib["imageFilename"]),
            regions={
                tr.id: tr for tr in (TextRegion.from_xml(region) for region in regions)
            },
        )

    @classmethod
    def from_xml_string(cls, xml_str: str) -> "Page":
        root = etree.fromstring(xml_str.encode("utf-8"))
        page_element = find_child(root, "Page")
        if page_element is None:
            raise PageXMLError("Page: no page element found")
        return cls.from_xml(page_element)

    def lookup_region(self, id: ID) -> TextRegion | None:
        return self.regions.get(id)

    def all_text(self) -> Iterable[str]:
        return (line for region in self.regions.values() for line in region.all_text())

    def all_words(self) -> Iterable[str]:
        return (word for region in self.regions.values() for word in region.all_words())
