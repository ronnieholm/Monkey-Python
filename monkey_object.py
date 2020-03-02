from enum import Enum, unique
from abc import ABC, abstractclassmethod
from typing import List, Dict, NewType, Callable
import hashlib
from collections import namedtuple
import ast
from environment import Environment


@unique
class ObjectType(Enum):
    # Within each Object derived class, we could use type() to get at its Python
    # type for comparison, thereby getting rid of type_ on each derived class.
    # Relying on type() would render this enum redundant. Monkey error messages,
    # however, include members of this enum in error messages. Relying on
    # type(), details of the underlying implementation would leak into user
    # error messages. Hence we keep the Monkey types and Python types types
    # separate.
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    RETURN_VALUE = "RETURN_VALUE"
    ERROR = "ERROR"
    FUNCTION = "FUNCTION"
    STRING = "STRING"
    BUILTIN = "BUILTIN"
    ARRAY = "ARRAY"
    HASH = "HASH"


# Classes in Python have reference semantics which makes any two HashKeys
# different. namedtyple on the other hand has value sematics.
# // TODO: type: ObjectType, value: int
HashKey = namedtuple("HashKey", ["type", "value"])

# TODO: How to force runtime error if method is not implemented? It's currently ignored


class Hashable:
    @abstractclassmethod
    def hash_key(cls) -> HashKey:
        raise NotImplementedError


class MonkeyObject:
    @abstractclassmethod
    def type_(cls) -> ObjectType:
        raise NotImplementedError

    @abstractclassmethod
    def inspect(cls) -> str:
        raise NotImplementedError


class Integer(MonkeyObject, Hashable):
    def __init__(self, value: int) -> None:
        self.value = value

    def type_(self) -> ObjectType:
        return ObjectType.INTEGER

    def inspect(self) -> str:
        return str(self.value)

    def hash_key(self) -> HashKey:
        return HashKey(self.type_(), self.value)


class String(MonkeyObject, Hashable):
    def __init__(self, value: str) -> None:
        self.value = value

    def type_(self) -> ObjectType:
        return ObjectType.STRING

    def inspect(self) -> str:
        return str(self.value)

    def hash_key(self) -> HashKey:
        return HashKey(self.type_(), int(hashlib.md5(self.value.encode("utf-8")).hexdigest(), 16))


class Boolean(MonkeyObject, Hashable):
    def __init__(self, value: bool) -> None:
        self.value = value

    def type_(self) -> ObjectType:
        return ObjectType.BOOLEAN

    def inspect(self) -> str:
        # Python's boolean literals are True and False where Monkey's are true
        # and false
        return "true" if self.value else "false"

    def hash_key(self) -> HashKey:
        value = 1 if self.value == 1 else 0
        return HashKey(self.type_(), value)


class Null(MonkeyObject):
    # Null is a type like Integer and Boolean except it doesn't wrap a value. It
    # represents the absence of a value.

    def type_(self) -> ObjectType:
        return ObjectType.NULL

    def inspect(self) -> str:
        return "null"


class ReturnValue(MonkeyObject):
    # ReturnValue is a wrapper around another Monkey object.

    def __init__(self, value: MonkeyObject) -> None:
        self.value = value

    def type_(self) -> ObjectType:
        return ObjectType.RETURN_VALUE

    def inspect(self) -> str:
        # Satisfies mypy that infinite recursion cannot happen. Passing
        # Return_value is possible type system wise given Object
        # constraint, and type hints doesn't support exclusing single type.
        assert not isinstance(self, ReturnValue)
        return self.value.inspect()


class Error(MonkeyObject):
    # Error wraps a string error message. In a production language, we'd want to
    # attach stack trace and line and column numbers to such error object.

    def __init__(self, message: str) -> None:
        self.message = message

    def type_(self) -> ObjectType:
        return ObjectType.ERROR

    def inspect(self) -> str:
        return f"ERROR: {self.message}"


class Function(MonkeyObject):
    def __init__(self, parameters: List[ast.Identifier], body: ast.BlockStatement, env: Environment) -> None:
        self.parameters = parameters
        self.body = body

        # Functions carry their own environment. This allows for
        # closures to "close over" the environment they're defined in and
        # allows the function to later access values within the closure.
        self.env = env

    def type_(self) -> ObjectType:
        return ObjectType.FUNCTION

    def inspect(self) -> str:
        params = map(lambda p: p.string(), self.parameters)
        return f"fn({', '.join(params)}) {{\n{self.body.string()}\n}}"


class Array(MonkeyObject):
    def __init__(self, elements: List[MonkeyObject]) -> None:
        self.elements = elements

    def type_(self) -> ObjectType:
        return ObjectType.ARRAY

    def inspect(self) -> str:
        elements = map(lambda e: e.inspect(), self.elements)
        return f"[{', '.join(elements)}]"


class HashPair:
    def __init__(self, key: MonkeyObject, value: MonkeyObject) -> None:
        self.key = key
        self.value = value


class Hash(MonkeyObject):
    def __init__(self, pairs: Dict[HashKey, HashPair]) -> None:
        self.pairs = pairs

    def type_(self) -> ObjectType:
        return ObjectType.HASH

    def inspect(self) -> str:
        pairs = []
        for _, pair in self.pairs.items():
            pairs.append(f"{pair.key.inspect()}: {pair.value.inspect()}")
        return f"{{{', '.join(pairs)}}}"


class Builtin(MonkeyObject):
    def __init__(self, function: Callable[[List[MonkeyObject]], MonkeyObject]) -> None:
        self.function = function

    def type_(self) -> ObjectType:
        return ObjectType.BUILTIN

    def inspect(self) -> str:
        return "builtin function"
