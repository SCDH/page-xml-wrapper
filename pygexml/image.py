from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class Image(DataClassJsonMixin):
    filename: str
    width: int | None
    height: int | None
