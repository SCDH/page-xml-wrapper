from hypothesis import given
import hypothesis.strategies as st

from pygexml.strategies import st_images
from pygexml.image import Image


def test_image_example() -> None:
    image = Image(filename="a.jpg", width=800, height=600)
    assert image.filename == "a.jpg"
    assert image.width == 800
    assert image.height == 600


@given(
    st.text(),
    st.one_of(st.none(), st.integers(min_value=1)),
    st.one_of(st.none(), st.integers(min_value=1)),
)
def test_image_arbitrary(filename: str, width: int, height: int) -> None:
    image = Image(filename=filename, width=width, height=height)
    assert image.filename == filename
    assert image.width == width
    assert image.height == height


@given(st_images)
def test_image_serialization_roundtrip_arbitrary(image: Image) -> None:
    assert Image.from_dict(image.to_dict()) == image
