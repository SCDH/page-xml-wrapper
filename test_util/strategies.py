# mypy: disallow_untyped_defs=False

import string

import hypothesis.strategies as st

from page_xml.geometry import Point, Box, Polygon
from page_xml import Coords, Page, TextLine, TextRegion

st_points = st.builds(Point, x=st.integers(min_value=0), y=st.integers(min_value=0))


@st.composite
def st_box_points(draw):
    tl = draw(st_points)
    br_x = draw(st.integers(min_value=tl.x + 1))
    br_y = draw(st.integers(min_value=tl.y + 1))
    br = Point(x=br_x, y=br_y)
    return tl, br


st_boxes = st.builds(
    lambda pp: Box(top_left=pp[0], bottom_right=pp[1]), st_box_points()
)

st_polygons = st.builds(Polygon, st.lists(st_points, min_size=1))
st_polygons2 = st.builds(Polygon, st.lists(st_points, min_size=2))

st_coords = st.builds(Coords, polygon=st_polygons2)

st_coords_strings = st.builds(str, st_coords)

st_text_lines = st.builds(
    TextLine, id=st.text(alphabet=string.printable), coords=st_coords, text=st.text()
)

st_text_regions = st.builds(
    TextRegion,
    id=st.text(alphabet=string.printable),
    coords=st_coords,
    textlines=st.builds(
        lambda lines: {l.id: l for l in lines}, st.lists(st_text_lines)
    ),
)


@st.composite
def st_pages(draw):
    image_filename = draw(st.text(alphabet=string.printable))
    regions = {tr.id: tr for tr in draw(st.lists(st_text_regions))}
    page = Page(image_filename=image_filename, regions=regions)
    return page
