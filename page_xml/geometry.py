from dataclasses import dataclass


class GeometryError(Exception):
    pass


@dataclass
class Point:
    x: int
    y: int

    def __str__(self) -> str:
        return f"{self.x},{self.y}"


@dataclass
class Box:
    top_left: Point
    bottom_right: Point

    def __post_init__(self) -> None:
        if (
            self.top_left.x > self.bottom_right.x
            or self.top_left.y > self.bottom_right.y
        ):
            raise GeometryError("Box: top left is not top left")

    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x

    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y

    def contains(self, point: Point) -> bool:
        return (
            self.top_left.x <= point.x <= self.bottom_right.x
            and self.top_left.y <= point.y <= self.bottom_right.y
        )


@dataclass
class Polygon:
    points: list[Point]

    def __post_init__(self) -> None:
        if len(self.points) < 1:
            raise GeometryError("Polygon: points must not be empty")

    def bounding_box(self) -> Box:
        min_x = min(point.x for point in self.points)
        max_x = max(point.x for point in self.points)
        min_y = min(point.y for point in self.points)
        max_y = max(point.y for point in self.points)
        return Box(
            top_left=Point(x=min_x, y=min_y), bottom_right=Point(x=max_x, y=max_y)
        )
