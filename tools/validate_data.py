"""Validate the JSON data files using the current content loader."""

from budgetwars.loaders import load_all_content, validate_content_bundle


def main() -> None:
    bundle = load_all_content()
    validate_content_bundle(bundle)
    print("Data validation passed for the daily market overhaul.")


if __name__ == "__main__":
    main()
