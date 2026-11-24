from tests.output_betterproto.enum import (
    ArithmeticOperator,
    Choice,
    PropertyKey,
    PurgeData,
    Test,
)
from tests.output_betterproto_pydantic.enum import (
    Choice as ChoicePyd,
    PropertyKey as PropertyKeyPyd,
    PurgeData as PurgeDataPyd,
    Test as TestPyd,
)


def test_enum_set_and_get():
    assert Test(choice=Choice.ZERO).choice == Choice.ZERO
    assert Test(choice=Choice.ONE).choice == Choice.ONE
    assert Test(choice=Choice.THREE).choice == Choice.THREE
    assert Test(choice=Choice.FOUR).choice == Choice.FOUR


def test_enum_set_with_int():
    assert Test(choice=0).choice == Choice.ZERO
    assert Test(choice=1).choice == Choice.ONE
    assert Test(choice=3).choice == Choice.THREE
    assert Test(choice=4).choice == Choice.FOUR


def test_enum_is_comparable_with_int():
    assert Test(choice=Choice.ZERO).choice == 0
    assert Test(choice=Choice.ONE).choice == 1
    assert Test(choice=Choice.THREE).choice == 3
    assert Test(choice=Choice.FOUR).choice == 4


def test_enum_to_dict():
    assert "choice" not in Test(choice=Choice.ZERO).to_dict(), (
        "Default enum value is not serialized"
    )
    assert (
        Test(choice=Choice.ZERO).to_dict(include_default_values=True)["choice"]
        == "ZERO"
    )
    assert Test(choice=Choice.ONE).to_dict()["choice"] == "ONE"
    assert Test(choice=Choice.THREE).to_dict()["choice"] == "THREE"
    assert Test(choice=Choice.FOUR).to_dict()["choice"] == "FOUR"


def test_repeated_enum_is_comparable_with_int():
    assert Test(choices=[Choice.ZERO]).choices == [0]
    assert Test(choices=[Choice.ONE]).choices == [1]
    assert Test(choices=[Choice.THREE]).choices == [3]
    assert Test(choices=[Choice.FOUR]).choices == [4]


def test_repeated_enum_set_and_get():
    assert Test(choices=[Choice.ZERO]).choices == [Choice.ZERO]
    assert Test(choices=[Choice.ONE]).choices == [Choice.ONE]
    assert Test(choices=[Choice.THREE]).choices == [Choice.THREE]
    assert Test(choices=[Choice.FOUR]).choices == [Choice.FOUR]


def test_repeated_enum_to_dict():
    assert Test(choices=[Choice.ZERO]).to_dict()["choices"] == ["ZERO"]
    assert Test(choices=[Choice.ONE]).to_dict()["choices"] == ["ONE"]
    assert Test(choices=[Choice.THREE]).to_dict()["choices"] == ["THREE"]
    assert Test(choices=[Choice.FOUR]).to_dict()["choices"] == ["FOUR"]

    all_enums_dict = Test(
        choices=[Choice.ZERO, Choice.ONE, Choice.THREE, Choice.FOUR]
    ).to_dict()
    assert (all_enums_dict["choices"]) == ["ZERO", "ONE", "THREE", "FOUR"]


def test_repeated_enum_with_single_value_to_dict():
    assert Test(choices=Choice.ONE).to_dict()["choices"] == ["ONE"]
    assert Test(choices=1).to_dict()["choices"] == ["ONE"]


def test_repeated_enum_with_non_list_iterables_to_dict():
    assert Test(choices=(1, 3)).to_dict()["choices"] == ["ONE", "THREE"]
    assert Test(choices=(1, 3)).to_dict()["choices"] == ["ONE", "THREE"]
    assert Test(choices=(Choice.ONE, Choice.THREE)).to_dict()["choices"] == [
        "ONE",
        "THREE",
    ]

    def enum_generator():
        yield Choice.ONE
        yield Choice.THREE

    assert Test(choices=enum_generator()).to_dict()["choices"] == ["ONE", "THREE"]


def test_enum_mapped_on_parse():
    # test default value
    b = Test().parse(bytes(Test()))
    assert b.choice.name == Choice.ZERO.name
    assert b.choices == []

    # test non default value
    a = Test().parse(bytes(Test(choice=Choice.ONE)))
    assert a.choice.name == Choice.ONE.name
    assert b.choices == []

    # test repeated
    c = Test().parse(bytes(Test(choices=[Choice.THREE, Choice.FOUR])))
    assert c.choices[0].name == Choice.THREE.name
    assert c.choices[1].name == Choice.FOUR.name

    # bonus: defaults after empty init are also mapped
    assert Test().choice.name == Choice.ZERO.name


def test_renamed_enum_members():
    assert set(ArithmeticOperator.__members__) == {
        "NONE",
        "PLUS",
        "MINUS",
        "_0_PREFIXED",
    }


def test_pydantic_enum_preserve_type():
    test = TestPyd(choice=ChoicePyd.ZERO)
    assert isinstance(test.choice, ChoicePyd)


def test_members_named_like_their_enum_keep_their_full_name():
    for purge_data in (PurgeData, PurgeDataPyd):
        assert [(member.name, member.value) for member in purge_data] == [
            ("UNSPECIFIED", 0),
            ("PURGE_DATA", 1),
            ("DO_NOT_PURGE_DATA", 2),
        ]
        assert purge_data(1).name == "PURGE_DATA"
        assert purge_data(2).name == "DO_NOT_PURGE_DATA"

    for property_key in (PropertyKey, PropertyKeyPyd):
        assert property_key(131) is property_key.EXTENDED_PROPERTY_KEY
        assert property_key(1) is property_key.NAME
        assert property_key(0) is property_key.UNSPECIFIED
