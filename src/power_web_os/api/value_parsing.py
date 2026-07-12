"""Small type-safe parsing helpers shared by API projectors."""


def optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
