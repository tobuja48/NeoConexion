def display(value: str) -> str:
    return value.strip()


def key(value: str) -> str:
    return display(value).lower()


def unique_names(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Keep the first display name for each normalized key."""
    names: dict[str, str] = {}
    for value in values:
        if key(value):
            names.setdefault(key(value), display(value))
    return tuple(names.values())
