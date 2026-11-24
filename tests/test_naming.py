import pytest

from betterproto.compile.naming import (
    pythonize_enum_member_name,
    pythonize_enum_member_names,
)


@pytest.mark.parametrize(
    ["name", "enum_name", "expected"],
    [
        ("CLAIM_UNSPECIFIED", "Claim", "UNSPECIFIED"),
        ("ARITHMETIC_OPERATOR_PLUS", "ArithmeticOperator", "PLUS"),
        ("ARITHMETIC_OPERATOR_0_PREFIXED", "ArithmeticOperator", "_0_PREFIXED"),
        ("CONNECTOR_STATE_UNSPECIFIED", "State", "UNSPECIFIED"),
        ("RED", "Colour", "RED"),
        ("PURGE_DATA", "PurgeData", "PURGE_DATA"),
        ("DO_NOT_PURGE_DATA", "PurgeData", "DO_NOT_PURGE_DATA"),
        ("EXTENDED_PROPERTY_KEY", "PropertyKey", "EXTENDED_PROPERTY_KEY"),
    ],
)
def test_pythonize_enum_member_name(name, enum_name, expected):
    assert pythonize_enum_member_name(name, enum_name) == expected


def test_pythonize_enum_member_names():
    members = [
        ("PURGE_DATA_UNSPECIFIED", 0),
        ("PURGE_DATA", 1),
        ("DO_NOT_PURGE_DATA", 2),
    ]

    assert pythonize_enum_member_names("PurgeData", members) == [
        "UNSPECIFIED",
        "PURGE_DATA",
        "DO_NOT_PURGE_DATA",
    ]


def test_pythonize_enum_member_names_allows_aliases():
    members = [("COLOUR_RED", 1), ("COLOUR_ALSO_RED", 1), ("RED", 1)]

    assert pythonize_enum_member_names("Colour", members) == ["RED", "ALSO_RED", "RED"]


def test_pythonize_enum_member_names_rejects_lossy_collisions():
    members = [("COLOUR_RED", 1), ("RED", 2)]

    with pytest.raises(ValueError, match="COLOUR_RED = 1 and RED = 2"):
        pythonize_enum_member_names("Colour", members)
