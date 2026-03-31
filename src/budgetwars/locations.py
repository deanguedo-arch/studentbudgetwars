"""Location utilities placeholder."""

from __future__ import annotations

from .models import LocationDefinition


def location_map(locations: list[LocationDefinition]) -> dict[str, LocationDefinition]:
    return {location.id: location for location in locations}
