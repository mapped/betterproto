import pickle
from copy import (
    copy,
    deepcopy,
)
from dataclasses import dataclass
from typing import (
    Dict,
    List,
)
from unittest.mock import ANY

import cachelib
import pytest

import betterproto
from betterproto.lib.google import protobuf as google


def unpickled(message):
    return pickle.loads(pickle.dumps(message))


@dataclass(eq=False, repr=False)
class Fe(betterproto.Message):
    abc: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class Fi(betterproto.Message):
    abc: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class Fo(betterproto.Message):
    abc: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class NestedData(betterproto.Message):
    struct_foo: Dict[str, "google.Struct"] = betterproto.map_field(
        1, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )
    map_str_any_bar: Dict[str, "google.Any"] = betterproto.map_field(
        2, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )


@dataclass(eq=False, repr=False)
class Complex(betterproto.Message):
    foo_str: str = betterproto.string_field(1)
    fe: "Fe" = betterproto.message_field(3, group="grp")
    fi: "Fi" = betterproto.message_field(4, group="grp")
    fo: "Fo" = betterproto.message_field(5, group="grp")
    nested_data: "NestedData" = betterproto.message_field(6)
    mapping: Dict[str, "google.Any"] = betterproto.map_field(
        7, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )


def complex_msg():
    return Complex(
        foo_str="yep",
        fe=Fe(abc="1"),
        nested_data=NestedData(
            struct_foo={
                "foo": google.Struct(
                    fields={
                        "hello": google.Value(
                            list_value=google.ListValue(
                                values=[google.Value(string_value="world")]
                            )
                        )
                    }
                ),
            },
            map_str_any_bar={
                "key": google.Any(value=b"value"),
            },
        ),
        mapping={
            "message": google.Any(value=bytes(Fi(abc="hi"))),
            "string": google.Any(value=b"howdy"),
        },
    )


def test_pickling_complex_message():
    msg = complex_msg()
    deser = unpickled(msg)
    assert msg == deser
    assert msg.fe.abc == "1"
    assert msg.is_set("fi") is not True
    assert msg.mapping["message"] == google.Any(value=bytes(Fi(abc="hi")))
    assert msg.mapping["string"].value.decode() == "howdy"
    assert (
        msg.nested_data.struct_foo["foo"]
        .fields["hello"]
        .list_value.values[0]
        .string_value
        == "world"
    )


def test_recursive_message():
    from tests.output_betterproto.recursivemessage import Test as RecursiveMessage

    msg = RecursiveMessage()
    msg = unpickled(msg)

    assert msg.child == RecursiveMessage()

    # Lazily-created zero-value children must not affect equality.
    assert msg == RecursiveMessage()

    # Lazily-created zero-value children must not affect serialization.
    assert bytes(msg) == b""


def test_recursive_message_defaults():
    from tests.output_betterproto.recursivemessage import (
        Intermediate,
        Test as RecursiveMessage,
    )

    msg = RecursiveMessage(name="bob", intermediate=Intermediate(42))
    msg = unpickled(msg)

    # set values are as expected
    assert msg == RecursiveMessage(name="bob", intermediate=Intermediate(42))

    # lazy initialized works modifies the message
    assert msg != RecursiveMessage(
        name="bob", intermediate=Intermediate(42), child=RecursiveMessage(name="jude")
    )
    msg.child.child.name = "jude"
    assert msg == RecursiveMessage(
        name="bob",
        intermediate=Intermediate(42),
        child=RecursiveMessage(child=RecursiveMessage(name="jude")),
    )

    # lazily initialization recurses as needed
    assert msg.child.child.child.child.child.child.child == RecursiveMessage()
    assert msg.intermediate.child.intermediate == Intermediate()


@dataclass
class PickledMessage(betterproto.Message):
    foo: bool = betterproto.bool_field(1)
    bar: int = betterproto.int32_field(2)
    baz: List[str] = betterproto.string_field(3)


def test_copyability():
    msg = PickledMessage(bar=12, baz=["hello"])
    msg = unpickled(msg)

    copied = copy(msg)
    assert msg == copied
    assert msg is not copied
    assert msg.baz is copied.baz

    deepcopied = deepcopy(msg)
    assert msg == deepcopied
    assert msg is not deepcopied
    assert msg.baz is not deepcopied.baz


def test_message_can_be_cached():
    """Cachelib uses pickling to cache values"""

    cache = cachelib.SimpleCache()

    def use_cache():
        calls = getattr(use_cache, "calls", 0)
        result = cache.get("message")
        if result is not None:
            return result
        else:
            setattr(use_cache, "calls", calls + 1)
            result = complex_msg()
            cache.set("message", result)
            return result

    for n in range(10):
        if n == 0:
            assert not cache.has("message")
        else:
            assert cache.has("message")

        msg = use_cache()
        assert use_cache.calls == 1  # The message is only ever built once
        assert msg.fe.abc == "1"
        assert msg.is_set("fi") is not True
        assert msg.mapping["message"] == google.Any(value=bytes(Fi(abc="hi")))
        assert msg.mapping["string"].value.decode() == "howdy"
        assert (
            msg.nested_data.struct_foo["foo"]
            .fields["hello"]
            .list_value.values[0]
            .string_value
            == "world"
        )


class _LegacyPickled:
    """Pickles like betterproto 2.0.0b6 and earlier, which had no ``__reduce__``.

    The message class is created without ``__init__`` and its ``__dict__`` is
    passed to ``__setstate__``. Unset fields hold the ``PLACEHOLDER`` sentinel,
    which was a bare ``object()``.
    """

    def __init__(self, cls, fields, group_current=None, unknown_fields=b""):
        self.cls = cls
        self.state = {
            **{name: object() for name in cls._betterproto.meta_by_field_name},
            **fields,
            "_serialized_on_wire": True,
            "_unknown_fields": unknown_fields,
            "_group_current": group_current or {},
        }

    def __reduce__(self):
        return (_new_without_init, (self.cls,), self.state)


def _new_without_init(cls):
    return cls.__new__(cls)


def test_unpickle_legacy_dict_state():
    legacy = _LegacyPickled(
        Complex,
        {"foo_str": "yep", "fe": _LegacyPickled(Fe, {"abc": "1"})},
        group_current={"grp": "fe"},
    )

    msg = pickle.loads(pickle.dumps(legacy))

    assert type(msg) is Complex
    assert msg == Complex(foo_str="yep", fe=Fe(abc="1"))
    assert bytes(msg) == bytes(Complex(foo_str="yep", fe=Fe(abc="1")))
    assert betterproto.which_one_of(msg, "grp") == ("fe", Fe(abc="1"))
    assert msg.nested_data == NestedData()
    assert unpickled(msg) == msg


def test_unpickle_legacy_dict_state_ignores_unselected_oneof_members():
    legacy = _LegacyPickled(
        Complex,
        {
            "fe": _LegacyPickled(Fe, {"abc": "1"}),
            "fi": _LegacyPickled(Fi, {"abc": "stale"}),
        },
        group_current={"grp": "fe"},
    )

    msg = pickle.loads(pickle.dumps(legacy))

    assert betterproto.which_one_of(msg, "grp") == ("fe", Fe(abc="1"))
    assert not msg.is_set("fi")


def test_unpickle_legacy_dict_state_keeps_unknown_fields():
    unknown = bytes([0x50, 0x01])  # field 10, varint 1
    legacy = _LegacyPickled(PickledMessage, {"bar": 12}, unknown_fields=unknown)

    msg = pickle.loads(pickle.dumps(legacy))

    assert msg.bar == 12
    assert bytes(msg) == bytes(PickledMessage(bar=12)) + unknown


class LegacyColour(betterproto.Enum):
    RED = 1
    GREEN = 2


def _legacy_enum_pickle(enum_cls, value, pickled_name):
    """Opcodes betterproto 2.0.0b7 wrote for an enum member: NEWOBJ(cls, (value,)) then BUILD(__dict__)."""

    def text(s):
        b = s.encode()
        return pickle.SHORT_BINUNICODE + bytes([len(b)]) + b

    return b"".join(
        [
            pickle.PROTO + b"\x04",
            text(enum_cls.__module__),
            text(enum_cls.__qualname__),
            pickle.STACK_GLOBAL,
            pickle.BININT1 + bytes([value]),
            pickle.TUPLE1,
            pickle.NEWOBJ,
            pickle.EMPTY_DICT,
            pickle.MARK,
            text("name"),
            text(pickled_name),
            text("value"),
            pickle.BININT1 + bytes([value]),
            pickle.SETITEMS,
            pickle.BUILD,
            pickle.STOP,
        ]
    )


def test_unpickle_legacy_enum_member():
    member = pickle.loads(_legacy_enum_pickle(LegacyColour, 2, "GREEN"))

    assert member is LegacyColour.GREEN


def test_unpickle_legacy_enum_member_keeps_current_name():
    member = pickle.loads(_legacy_enum_pickle(LegacyColour, 1, "COLOUR_RED"))

    assert member is LegacyColour.RED
    assert member.name == "RED"


def test_unpickle_legacy_enum_unknown_value_raises():
    with pytest.raises(ValueError):
        pickle.loads(_legacy_enum_pickle(LegacyColour, 9, "GONE"))
