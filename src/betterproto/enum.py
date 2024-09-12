from __future__ import annotations

import sys
from enum import (
    EnumMeta,
    IntEnum,
)
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    Tuple,
    Type,
)

if TYPE_CHECKING:
    from collections.abc import (
        Generator,
        Mapping,
    )

    from typing_extensions import (
        Never,
        Self,
    )


def _is_descriptor(obj: object) -> bool:
    return (
        hasattr(obj, "__get__") or hasattr(obj, "__set__") or hasattr(obj, "__delete__")
    )
if TYPE_CHECKING:
    BaseMetaType = EnumMeta
    BaseType = IntEnum
else:
    BaseMetaType = type
    BaseType = int

class EnumType(BaseMetaType):
    _value_map_: Mapping[int, Enum]
    _member_map_: Mapping[str, Enum]  # type: ignore[assignment]

    def __new__(
        mcs, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]
    ) -> Type[Enum]:
        value_map: dict[str, Enum] = {}
        member_map: dict[str, Enum] = {}

        new_mcs = type(
            f"{name}Type",
            tuple(
                dict.fromkeys(
                    [base.__class__ for base in bases if base.__class__ is not type]
                    + [EnumType, type]
                )
            ),  # reorder the bases so EnumType and type are last to avoid conflicts
            {"_value_map_": value_map, "_member_map_": member_map},
        )

        members = {
            name: value
            for name, value in namespace.items()
            if not _is_descriptor(value) and not name.startswith("__")
        }

        cls: Type[Enum] = type.__new__(
            new_mcs,
            name,
            bases,
            {key: value for key, value in namespace.items() if key not in members},
        )
        # this allows us to disallow member access from other members as
        # members become proper class variables

        for name, value in members.items():
            member = value_map.get(value)
            if member is None:
                member = cls.__new__(cls, name=name, value=value)
                value_map[value] = member
            member_map[name] = member
            type.__setattr__(new_mcs, name, member)

        return cls

    if not TYPE_CHECKING:

        @classmethod
        def __call__(cls, value: int) -> Enum:
            try:
                return cls._value_map_[value]
            except (KeyError, TypeError):
                raise ValueError(f"{value!r} is not a valid {cls.__name__}") from None

        @classmethod
        def __iter__(cls) -> Generator[Enum, None, None]:
            yield from cls._member_map_.values()

        if sys.version_info >= (3, 8):

            @classmethod
            def __reversed__(cls) -> Generator[Enum, None, None]:
                yield from reversed(cls._member_map_.values())

        else:

            @classmethod
            def __reversed__(cls) -> Generator[Enum, None, None]:
                yield from reversed(tuple(cls._member_map_.values()))

        @classmethod
        def __getitem__(cls, key: str) -> Enum:
            return cls._member_map_[key]

        @classmethod
        def __members__(cls) -> MappingProxyType[str, Enum]:
            return MappingProxyType(cls._member_map_)

    @classmethod
    def __repr__(cls) -> str:
        return f"<enum {cls.__name__!r}>"

    @classmethod
    def __len__(cls) -> int: 
        return len(cls._member_map_)

    @classmethod
    def __setattr__(cls, name: str, value: Any) -> Never: 
        raise AttributeError(f"{cls.__name__}: cannot reassign Enum classes.")

    @classmethod
    def __delattr__(cls, name: str) -> Never:
        raise AttributeError(f"{cls.__name__}: cannot delete Enum classes.")

    @classmethod
    def __contains__(cls, member: object) -> bool:
        return isinstance(member, cls) and isinstance(member, Enum) and member.name in cls._member_map_

class Enum(BaseType, metaclass=EnumType):
    """
    The base class for protobuf enumerations, all generated enumerations will
    inherit from this. Emulates `enum.IntEnum`.
    """

    name: str
    value: int  # type: ignore[misc]

    if not TYPE_CHECKING:

        def __new__(cls, *, name: Optional[str], value: int) -> Self:
            self = super().__new__(cls, value)
            super().__setattr__(self, "name", name)
            super().__setattr__(self, "value", value)
            return self

    def __str__(self) -> str:
        return self.name or "None"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __setattr__(self, key: str, value: Any) -> Never:
        raise AttributeError(
            f"{self.__class__.__name__} Cannot reassign a member's attributes."
        )

    def __delattr__(self, item: Any) -> Never:
        raise AttributeError(
            f"{self.__class__.__name__} Cannot delete a member's attributes."
        )

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: Any) -> Self:
        return self

    @classmethod
    def try_value(cls, value: int = 0) -> Self:
        """Return the value which corresponds to the value.

        Parameters
        -----------
        value: :class:`int`
            The value of the enum member to get.

        Returns
        -------
        :class:`Enum`
            The corresponding member or a new instance of the enum if
            ``value`` isn't actually a member.
        """
        try:
            value = cls._value_map_[value]
            if not isinstance(value, type(cls)):
                raise TypeError(f'{value} should be of same type as {cls.__name__}')
            return value
        except (KeyError, TypeError):
            return cls.__new__(cls, name=None, value=value)

    @classmethod
    def from_string(cls, name: str) -> Self:
        """Return the value which corresponds to the string name.

        Parameters
        -----------
        name: :class:`str`
            The name of the enum member to get.

        Raises
        -------
        :exc:`ValueError`
            The member was not found in the Enum.
        """
        try:
            member  = cls._member_map_[name]
            if not isinstance(member, type(cls)):
                raise TypeError(f'{member} should be of the same type as {cls.__name__}')
            return member 
        except KeyError as e:
            raise ValueError(f"Unknown value {name} for enum {cls.__name__}") from e
