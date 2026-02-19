# pygexml

A minimal Python wrapper around the [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) format for OCR output.

[![pygexml checks, tests and docs](https://github.com/SCDH/pygexml/actions/workflows/ci.yml/badge.svg)](https://github.com/SCDH/pygexml/actions/workflows/ci.yml) [![API docs online](https://img.shields.io/badge/API%20docs-online-blue?logo=gitbook&logoColor=lightgrey)](https://scdh.github.io/pygexml)

## Installation

```
pip install pygexml
```

Requires Python 3.12+.

## Usage

```python
from pygexml import Page

page = Page.from_xml_string(xml_string)

for line in page.all_text():
    print(line)
```

### Data model

| Class | Import from |
|---|---|
| `Page` | `pygexml` |
| `Page`, `TextRegion`, `TextLine`, `Coords` | `pygexml.page` |
| `Point`, `Box`, `Polygon` | `pygexml.geometry` |

`Page`, `TextRegion` and `TextLine` each expose `all_text()` and `all_words()` iterators.
Lookups by ID are available via `lookup_region()` and `lookup_textline()`.

Refer to the [online API docs](https://scdh.github.io/pygexml) for details.

## Development

```bash
pip install ".[dev,test,docs]"

black pygexml test test_util    # format
mypy pygexml test test_util     # type check
pyright pygexml test test_util  # type check
pytest -v                       # tests
pdoc -o .api_docs pygexml/*     # API docs
```

CI runs on Python 3.12, 3.13 and 3.14. API documentation is published to GitHub Pages on every push to `main`.

## Contributing

[Bug reports, feature requests](https://github.com/SCDH/pygexml/issues) and [pull requests](https://github.com/SCDH/pygexml/pulls) are welcome. Feel free to open draft pull requests early to invite discussion and collaboration.

Please note that this project has a [Code of Conduct](CODE_OF_CONDUCT.md).

## Copyright and License

Copyright (c) 2026 [Mirko Westermeier](https://github.com/memowe) (SCDH, University of Münster)

Released under the [MIT License](LICENSE).
