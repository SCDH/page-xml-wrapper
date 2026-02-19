import pytest
from hypothesis import given, strategies as st

from test_util.strategies import *
from pygexml.geometry import *

############## Tests for Point #####################


@given(st.integers(min_value=0), st.integers(min_value=0))
def test_point_construction(x: int, y: int) -> None:
    point = Point(x=x, y=y)
    assert point.x == x
    assert point.y == y


@given(st.integers(min_value=0), st.integers(min_value=0))
def test_point_stringification(x: int, y: int) -> None:
    point = Point(x=x, y=y)
    assert str(point) == f"{x},{y}"


############## Tests for Box ####################


def test_box_simple_example() -> None:
    p17 = Point(17, 17)
    p42 = Point(42, 42)
    box = Box(top_left=p17, bottom_right=p42)
    assert box.top_left == p17
    assert box.bottom_right == p42
    assert box.width() == 25
    assert box.height() == 25


@given(st_box_points())
def test_box_construction(pp: tuple[Point, Point]) -> None:
    tl, br = pp
    box = Box(top_left=tl, bottom_right=br)
    assert box.top_left == tl
    assert box.bottom_right == br


@given(st_box_points())
def test_box_construction_exception(pp: tuple[Point, Point]) -> None:
    tl, br = pp
    with pytest.raises(Exception, match="top left is not top left"):
        Box(top_left=br, bottom_right=tl)  # flipped points!


@given(st_boxes)
def test_box_width(box: Box) -> None:
    assert box.width() == abs(box.bottom_right.x - box.top_left.x)


@given(st_boxes)
def test_box_height(box: Box) -> None:
    assert box.height() == abs(box.bottom_right.y - box.top_left.y)


def test_box_simple_contains() -> None:
    box = Box(Point(17, 17), Point(42, 42))
    assert box.contains(Point(23, 37))
    assert not box.contains(Point(23, 666))


@given(st_points, st_boxes)
def test_box_containment(point: Point, box: Box) -> None:
    assert box.contains(point) == (
        box.top_left.x <= point.x <= box.bottom_right.x
        and box.top_left.y <= point.y <= box.bottom_right.y
    )


############## Tests for Polygon ####################


def test_polygon_simple_example() -> None:
    p17 = Point(17, 17)
    p42 = Point(42, 42)
    polygon = Polygon(points=[p17, p42])
    assert polygon.points == [p17, p42]
    assert polygon.bounding_box().top_left == p17
    assert polygon.bounding_box().bottom_right == p42


@given(st.lists(st_points, min_size=1))
def test_polygon_construction(points: list[Point]) -> None:
    polygon = Polygon(points=points)
    assert polygon.points == points


def test_polygon_construction_without_points() -> None:
    with pytest.raises(GeometryError, match="Polygon: points must not be empty"):
        Polygon(points=[])


@given(st_polygons)
def test_polygon_bounding_box_corners(polygon: Polygon) -> None:
    points = polygon.points
    min_x = min(point.x for point in points)
    max_x = max(point.x for point in points)
    min_y = min(point.y for point in points)
    max_y = max(point.y for point in points)
    bounding_box = polygon.bounding_box()
    assert bounding_box.top_left == Point(x=min_x, y=min_y)
    assert bounding_box.bottom_right == Point(x=max_x, y=max_y)


@given(st_polygons)
def test_polygon_bounding_box_contains(polygon: Polygon) -> None:
    bounding_box = polygon.bounding_box()
    for point in polygon.points:
        assert bounding_box.contains(point)
