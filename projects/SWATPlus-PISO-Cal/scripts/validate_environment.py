from __future__ import annotations

import importlib
import platform
import sys

REQUIRED = {
    "numpy": None,
    "pandas": None,
    "scipy": None,
    "sklearn": None,
    "torch": None,
    "yaml": None,
}
OPTIONAL = {"sbi": "0.27.0"}


def version_of(module_name: str) -> str:
    module = importlib.import_module(module_name)
    return str(getattr(module, "__version__", "unknown"))


def main() -> None:
    print("python", sys.version.replace("\n", " "))
    print("platform", platform.platform())
    if not ((3, 11) <= sys.version_info[:2] < (3, 13)):
        raise SystemExit("FAIL: reference environment requires Python 3.11 or 3.12")
    for module_name in REQUIRED:
        print(module_name, version_of(module_name))
    for module_name, expected in OPTIONAL.items():
        try:
            actual = version_of(module_name)
        except ImportError:
            raise SystemExit(f'FAIL: install optional stack with pip install -e ".[sbi]"')
        print(module_name, actual)
        if expected and actual != expected:
            raise SystemExit(f"FAIL: expected {module_name}=={expected}, found {actual}")
    print("ENVIRONMENT_STATUS=PASS")


if __name__ == "__main__":
    main()
