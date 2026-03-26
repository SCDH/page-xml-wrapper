from pathlib import Path
from re import Pattern, compile
from warnings import warn
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from typing import ClassVar
from collections.abc import Iterable
from lxml import etree
from lxml.etree import _Element as Element, QName

from .geometry import Point, Box, Polygon, GeometryError


def find_child(element: Element, name: str) -> Element | None:
    for child in element:
        if QName(child).localname == name:
            return child
    return None


def find_children(element: Element, name: str) -> Iterable[Element]:
    return (child for child in element if QName(child).localname == name)


class PageXMLError(Exception):
    pass


class ALTOXMLError(Exception):
    pass


@dataclass
class Coords(DataClassJsonMixin):
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

    def __post_init__(self) -> None:
        if len(self.polygon.points) < 2:
            raise PageXMLError("At least 2 Points are required")

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
            raise PageXMLError("At least 2 Points are required")

        return Coords(polygon=polygon)

    @classmethod
    def from_box(cls, box: Box) -> "Coords":
        return cls(polygon=Polygon.from_box(box))

    def __str__(self) -> str:
        return " ".join(str(p) for p in self.polygon.points)


@dataclass
class TextLine(DataClassJsonMixin):
    id: str
    coords: Coords
    text: str

    @classmethod
    def from_xml(cls, element: Element) -> "TextLine":
        if QName(element).localname != "TextLine":
            raise PageXMLError("Wrong element given")
        if "id" not in element.attrib:
            raise PageXMLError("No id found")
        coords_element = find_child(element, "Coords")
        if coords_element is None:
            raise PageXMLError("No Coords found")
        if "points" not in coords_element.attrib:
            raise PageXMLError("Coords has no points attribute")
        text_equiv = find_child(element, "TextEquiv")
        text_element = (
            find_child(text_equiv, "Unicode") if text_equiv is not None else None
        )
        if text_element is None:
            raise PageXMLError("No text found")
        return TextLine(
            id=str(element.attrib["id"]),
            coords=Coords.parse(str(coords_element.attrib["points"])),
            text=text_element.text if text_element.text is not None else "",
        )

    @classmethod
    def from_alto(cls, element: Element) -> "TextLine":
        if QName(element).localname != "TextLine":
            raise ALTOXMLError("Wrong element given")
        if "ID" not in element.attrib:
            raise ALTOXMLError("No ID found")

        box_attrs = ["HPOS", "VPOS", "WIDTH", "HEIGHT"]
        if not all(attr in element.attrib for attr in box_attrs):
            raise ALTOXMLError("Missing one of the box attributes")
        coords: Coords = Coords.from_box(
            Box.from_top_left_width_height(
                top_left=Point(
                    x=int(element.attrib["HPOS"]), y=int(element.attrib["VPOS"])
                ),
                width=int(element.attrib["WIDTH"]),
                height=int(element.attrib["HEIGHT"]),
            )
        )

        if len(element) == 0:
            raise ALTOXMLError("No text elements found")

        text: str = ""
        for child in element:
            match QName(child).localname:
                case "String":
                    if "CONTENT" in child.attrib:
                        text += str(child.attrib["CONTENT"])
                case "SP":
                    text += " "

        return TextLine(id=str(element.attrib["ID"]), coords=coords, text=text)

    def words(self) -> Iterable[str]:
        return self.text.split()


@dataclass
class TextRegion(DataClassJsonMixin):
    id: str
    coords: Coords
    textlines: dict[str, TextLine]

    @classmethod
    def from_xml(cls, element: Element) -> "TextRegion":
        if QName(element).localname != "TextRegion":
            raise PageXMLError("Wrong element given")
        if "id" not in element.attrib:
            raise PageXMLError("No id found")
        coords_element = find_child(element, "Coords")
        if coords_element is None:
            raise PageXMLError("No Coords element found")
        if "points" not in coords_element.attrib:
            raise PageXMLError("Coords has no points attribute")
        text_lines = find_children(element, "TextLine")

        return TextRegion(
            id=str(element.attrib["id"]),
            coords=Coords.parse(str(coords_element.attrib["points"])),
            textlines={
                tl.id: tl for tl in (TextLine.from_xml(tl) for tl in text_lines)
            },
        )

    @classmethod
    def from_alto(cls, element: Element) -> "TextRegion":
        if QName(element).localname != "TextBlock":
            raise ALTOXMLError("Wrong element given")
        if "ID" not in element.attrib:
            raise ALTOXMLError("No ID found")

        box_attrs = ["HPOS", "VPOS", "WIDTH", "HEIGHT"]
        if not all(attr in element.attrib for attr in box_attrs):
            raise ALTOXMLError("Missing one of the box attributes")
        coords: Coords = Coords.from_box(
            Box.from_top_left_width_height(
                top_left=Point(
                    x=int(element.attrib["HPOS"]), y=int(element.attrib["VPOS"])
                ),
                width=int(element.attrib["WIDTH"]),
                height=int(element.attrib["HEIGHT"]),
            )
        )

        textlines: dict[str, TextLine] = {}
        for child in element:
            if QName(child).localname == "TextLine":
                tl = TextLine.from_alto(child)
                textlines[tl.id] = tl

        if not textlines:
            raise ALTOXMLError("No TextLine elements found")

        return TextRegion(
            id=str(element.attrib["ID"]), coords=coords, textlines=textlines
        )

    def lookup_textline(self, id: str) -> TextLine | None:
        return self.textlines.get(id)

    def all_text(self) -> Iterable[str]:
        return (tl.text for tl in self.textlines.values())

    def all_words(self) -> Iterable[str]:
        return (w for tl in self.textlines.values() for w in tl.words())


@dataclass
class Page(DataClassJsonMixin):
    image_filename: str
    regions: dict[str, TextRegion]

    @classmethod
    def from_xml(cls, element: Element) -> "Page":
        if QName(element).localname != "Page":
            raise PageXMLError("Wrong element given")

        if "imageFilename" not in element.attrib:
            raise PageXMLError("No filename found")

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
            raise PageXMLError("No page element found")
        return cls.from_xml(page_element)

    @classmethod
    def from_xml_file(cls, file: Path | str, encoding: str = "utf-8") -> "Page":
        path = Path(file)
        xml_string = path.read_text(encoding=encoding)
        return Page.from_xml_string(xml_string)

    @classmethod
    def from_alto(cls, element: Element) -> "Page":
        if QName(element).localname != "alto":
            raise ALTOXMLError("Wrong element given")

        image_element = find_child(element, "Description")
        if image_element is None:
            raise ALTOXMLError("No Description element found")
        image_element = find_child(image_element, "sourceImageInformation")
        if image_element is None:
            raise ALTOXMLError("No sourceImageInformation element found")
        filename_element = find_child(image_element, "fileName")
        if filename_element is None:
            raise ALTOXMLError("No fileName element found")
        image_filename = (
            filename_element.text if filename_element.text is not None else ""
        )

        layout = find_child(element, "Layout")
        if layout is None:
            raise ALTOXMLError("No Layout element found")
        page_element = find_child(layout, "Page")
        if page_element is None:
            raise ALTOXMLError("No Page element found")
        printspace_element = find_child(page_element, "PrintSpace")
        if printspace_element is None:
            raise ALTOXMLError("No PrintSpace element found")

        text_blocks = find_children(printspace_element, "TextBlock")

        return Page(
            image_filename=image_filename,
            regions={
                tb.id: tb for tb in (TextRegion.from_alto(tb) for tb in text_blocks)
            },
        )

    @classmethod
    def from_alto_string(cls, xml_str: str) -> "Page":
        root = etree.fromstring(xml_str.encode("utf-8"))
        return cls.from_alto(root)

    @classmethod
    def from_alto_file(cls, file: Path | str, encoding: str = "utf-8") -> "Page":
        path = Path(file)
        xml_string = path.read_text(encoding=encoding)
        return Page.from_alto_string(xml_string)

    def lookup_region(self, id: str) -> TextRegion | None:
        return self.regions.get(id)

    def all_text(self) -> Iterable[str]:
        return (line for region in self.regions.values() for line in region.all_text())

    def all_words(self) -> Iterable[str]:
        return (word for region in self.regions.values() for word in region.all_words())
