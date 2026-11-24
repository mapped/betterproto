from typing import (
    Dict,
    Iterable,
    List,
    Tuple,
)

from betterproto import casing


def pythonize_class_name(name: str) -> str:
    return casing.pascal_case(name)


def pythonize_field_name(name: str) -> str:
    return casing.safe_snake_case(name)


def pythonize_method_name(name: str) -> str:
    return casing.safe_snake_case(name)


def pythonize_enum_member_name(name: str, enum_name: str) -> str:
    enum_name = casing.snake_case(enum_name).upper()
    find = name.find(enum_name)
    if find != -1:
        stripped = name[find + len(enum_name) :].strip("_")
        if stripped:
            name = stripped
    return casing.sanitize_name(name)


def pythonize_enum_member_names(
    enum_name: str, members: Iterable[Tuple[str, int]]
) -> List[str]:
    """Python names for an enum's ``(proto name, number)`` members, in order.

    Raises ``ValueError`` if two members with different numbers get the same
    Python name, since the generated class would silently lose one of them.
    """
    names = []
    seen: Dict[str, Tuple[str, int]] = {}
    for proto_name, number in members:
        name = pythonize_enum_member_name(proto_name, enum_name)
        other = seen.setdefault(name, (proto_name, number))
        if other[1] != number:
            raise ValueError(
                f"enum {enum_name}: members {other[0]} = {other[1]} and "
                f"{proto_name} = {number} both map to the Python name {name!r}"
            )
        names.append(name)
    return names
