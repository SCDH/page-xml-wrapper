import pkgutil
import pygexml


def test_all_submodules_in_init() -> None:
    discovered = {m.name for m in pkgutil.iter_modules(pygexml.__path__)}
    exported = {name for name in vars(pygexml) if not name.startswith("_")}
    missing = discovered - exported
    assert not missing, f"Missing in __init__.py: {missing}"
