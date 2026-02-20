# pygexml

A minimal Python wrapper around the [PAGE-XML][page-xml] format for OCR output.

[![pygexml checks, tests and docs][workflows-badge]][workflows] [![API docs online][api-docs-badge]][api-docs]

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

Refer to the [online API docs][api-docs] for details.

### Hypothesis strategies

The `pygexml.strategies` module provides [Hypothesis][hypothesis] strategies for all pygexml types, ready to use in property-based tests - including downstream projects:

```python
from hypothesis import given
from pygexml.strategies import st_pages

@given(st_pages())
def test_my_page_processing(page):
    assert process(page) is not None
```

Refer to the [`pygexml.strategies` API docs][api-docs-strategies] for details.

## Development

```bash
pip install ".[dev,test,docs]"

black pygexml test          # format
mypy pygexml test           # type check
pyright pygexml test        # type check
pytest -v                   # tests
pdoc -o .api_docs pygexml/* # API docs
```

CI runs on Python 3.12, 3.13 and 3.14. [API documentation][api-docs] is published to GitHub Pages on every push to `main`.

## Contributing

[Bug reports, feature requests][gh-issues] and [pull requests][gh-prs] are welcome. Feel free to open draft pull requests early to invite discussion and collaboration.

Please note that this project has a [Code of Conduct](CODE_OF_CONDUCT.md).

## Copyright and License

Copyright (c) 2026 [Mirko Westermeier][gh-memowe] (SCDH, University of Münster)

Released under the [MIT License](LICENSE).

[page-xml]: https://github.com/PRImA-Research-Lab/PAGE-XML
[workflows]: https://github.com/SCDH/pygexml/actions/workflows/checks_tests_docs.yml
[workflows-badge]: https://github.com/SCDH/pygexml/actions/workflows/checks_tests_docs.yml/badge.svg
[hypothesis]: https://hypothesis.readthedocs.io
[api-docs]: https://scdh.github.io/pygexml
[api-docs-strategies]: https://scdh.github.io/pygexml/pygexml/strategies.html
[api-docs-badge]: https://img.shields.io/badge/API%20docs-online-blue?logo=gitbook&logoColor=lightgrey
[gh-issues]: https://github.com/SCDH/pygexml/issues
[gh-prs]: https://github.com/SCDH/pygexml/pulls
[gh-memowe]: https://github.com/memowe
