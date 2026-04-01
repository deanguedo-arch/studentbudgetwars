"""Validate the JSON content bundle for After Grad: The First 10 Years."""

from budgetwars.loaders import load_all_content, validate_content_bundle


def main() -> None:
    bundle = load_all_content()
    validate_content_bundle(bundle)
    print("Data validation passed for the After Grad V2 life-sim build.")


if __name__ == "__main__":
    main()
