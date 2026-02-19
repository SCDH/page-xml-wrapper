# page-xml-wrapper

A minimal Python wrapper around the [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) format for OCR output.

## Installation

```
pip install page-xml-wrapper
```

Requires Python 3.12+.

## Usage

```python
from page_xml import Page

page = Page.from_xml_string(xml_string)

for line in page.all_text():
    print(line)
```

### Data model

| Class | Import from |
|---|---|
| `Page`, `TextRegion`, `TextLine`, `Coords` | `page_xml` |
| `Point`, `Box`, `Polygon` | `page_xml.geometry` |

`Page`, `TextRegion` and `TextLine` each expose `all_text()` and `all_words()` iterators.
Lookups by ID are available via `lookup_region()` and `lookup_textline()`.

Refer to the [online API docs](https://scdh.github.io/page-xml-wrapper) for details.

## Development

```bash
pip install ".[dev,test,docs]"

black page_xml test test_util    # format
mypy page_xml test test_util     # type check
pyright page_xml test test_util  # type check
pytest -v                        # tests
pdoc -o .api_docs page_xml/*     # API docs
```

CI runs on Python 3.12, 3.13 and 3.14. API documentation is published to GitHub Pages on every push to `main`.

## Contributing

[Bug reports, feature requests](https://github.com/SCDH/page-xml-wrapper/issues) and [pull requests](https://github.com/SCDH/page-xml-wrapper/pulls) are welcome. Feel free to open draft pull requests early to invite discussion and collaboration.

Please note that this project has a [Code of Conduct](CODE_OF_CONDUCT.md).

## Copyright and License

Copyright (c) 2026 [Mirko Westermeier](https://github.com/memowe) (SCDH, University of Münster)

Released under the [MIT License](LICENSE).
