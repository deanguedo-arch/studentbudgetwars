"""Validate the JSON data files using the package loaders and validators."""

from budgetwars.loaders import load_all_content
from budgetwars.validators import validate_content_bundle


def main() -> None:
    bundle = load_all_content()
    validate_content_bundle(bundle)
    print("Data validation passed.")


if __name__ == "__main__":
    main()
