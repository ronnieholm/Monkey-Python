from enum import Enum, unique
from abc import ABC, abstractclassmethod
import ast
from typing import List, Dict, Optional, Type, NewType, Callable, Any
import hashlib
from collections import namedtuple

# TODO: Move environment to seperate file

# Environment is inside object or it would resulting in a circular dependency
# with Object referencing Environment and Environment refering Object modules.
# We still have a typing issue in that Object and Environment reference each
# other inside a single module. Before Python 3.7, the only way to forward
# declare a type is by quoting it. MyPy will remove the quotes during type
# checking as per
# https://stackoverflow.com/questions/55320236/does-python-evaluate-type-hinting-of-a-forward-reference
class Environment:
    def __init__(self):
        self._store: Dict[str, "Object"] = {}
        self.outer: Environment = None

    @staticmethod
    def new_enclosed_environment(outer: "Environment") -> "Environment":
        env = Environment()
        env.outer = outer
        return env

    def get(self, name: str) -> "Optional[(Object, bool)]":
        ok = name in self._store.keys()
        obj = None
        if ok:
            obj = self._store[name]
        elif self.outer != None:
            # If current environment doesn't have a value associated with a
            # name, we recursively call get on enclosing environment (which the
            # current environment is extending) until either name is found or
            # caller can issue a "unknown identifier" error.
            obj, ok = self.outer.get(name)
        return obj, ok

    def set(self, name: str, value: "Object") -> "Object":
        self._store[name] = value
        return value

ObjectType = str

@unique
class Type_(Enum): # TODO: Rename to ObjectType and remove the _OBJ ending. Could probably use auto to assign value as its redundant anyway
    # Within each Object derived class, we could use type() to get at its Python
    # type for comparison, thereby getting rid of type_ on each derived class.
    # Relying on type() would render this enum redundant. Monkey error messages,
    # however, include members of this enum in error messages. Relying on
    # type(), details of the underlying implementation would leak into user
    # error messages. Hence we keep the Monkey types and Python types types
    # separate.
    INTEGER_OBJ = "INTEGER"
    BOOLEAN_OBJ = "BOOLEAN"
    NULL_OBJ = "NULL"
    RETURN_VALUE_OBJ = "RETURN_VALUE"
    ERROR_OBJ = "ERROR"
    FUNCTION_OBJ = "FUNCTION"
    STRING_OBJ = "STRING"
    BUILTIN_OBJ = "BUILTIN"
    ARRAY_OBJ = "ARRAY"
    HASH_OBJ = "HASH"

# Classes in Python have reference semantics which makes any two HashKeys
# different. namedtyple on the other hand has value sematics. 
HashKey = namedtuple("HashKey", ["type", "value"]) # // TODO: type: Type_, value: int

# TODO: How to force runtime error if method is not implemented? It currently ignored
class Hashable:
    @abstractclassmethod
    def hash_key(self) -> HashKey:
        raise NotImplementedError

class Object:   
    @abstractclassmethod
    def type_(self) -> Type_:
        raise NotImplementedError

    @abstractclassmethod
    def inspect(self) -> str:
        raise NotImplementedError

class Integer(Object, Hashable):    
    def __init__(self, value: int):
        self.value = value

    # TODO: why do we even have type_ when we ask isinstance?
    def type_(self) -> Type_:
        return Type_.INTEGER_OBJ

    def inspect(self) -> str:
        return str(self.value)

    def hash_key(self) -> HashKey:
        return HashKey(self.type_(), self.value)

class String(Object, Hashable):    
    def __init__(self, value: str):
        self.value = value

    def type_(self) -> Type_:
        return Type_.STRING_OBJ

    def inspect(self) -> str:
        return str(self.value)

    def hash_key(self) -> HashKey:
        return HashKey(self.type_(), int(hashlib.md5(self.value.encode("utf-8")).hexdigest(), 16))

class Boolean(Object, Hashable):
    def __init__(self, value: bool):
        self.value = value

    def type_(self) -> Type_:
        return Type_.BOOLEAN_OBJ

    def inspect(self) -> str:
        # Python's boolean literals are True and False
        # where Monkey's are true and false
        if self.value:
            return "true"
        else:
            return "false"

    def hash_key(self) -> HashKey:
        if self.value == 1:
            value = 1
        else:
            value = 0
        return HashKey(self.type_(), value)


# Null is a type like Integer and Boolean except it doesn't wrap a value. It
# represents the absence of a value.
class Null(Object):
    def type_(self) -> Type_:
        return Type_.NULL_OBJ

    def inspect(self) -> str:
        return "null"

# TODO: Rename to ReturnValue
# ReturnValue is a wrapper around another Monkey object.
class Return_value(Object):
    def __init__(self, value: Object):     
        self.value = value

    def type_(self) -> Type_:
        return Type_.RETURN_VALUE_OBJ

    def inspect(self) -> str:
        # Satisfies mypy that infinite recursion cannot happen. Passing
        # Return_value is possible type system wise given Object
        # constraint, and type hints doesn't support exclusing single type.
        assert(not isinstance(self, Return_value))
        return self.value.inspect()

# Error wraps a string error message. In a production language, we'd want to
# attach stack trace and line and column numbers to such error object.
class Error(Object):
    def __init__(self, message: str):
        self.message = message

    def type_(self) -> Type_:
        return Type_.ERROR_OBJ

    def inspect(self) -> str:
        return f"ERROR: {self.message}"
    
class Function(Object):
    def __init__(self, parameters: List[ast.Identifier], body: ast.BlockStatement, env: Environment):
        self.parameters = parameters
        self.body = body

        # Functions carry their own environment. This allows for
        # closures to "close over" the environment they're defined in and
        # allows the function to later access values within the closure.        
        self.env = env

    def type_(self) -> Type_:
        return Type_.FUNCTION_OBJ

    def inspect(self) -> str:
        params = []
        for p in self.parameters:
            params.append(p.string())        
        return f"fn({', '.join(params)}) {{\n{self.body.string()}\n}}"

class Array(Object):
    def __init__(self, elements: List[Object]):
        self.elements = elements

    def type_(self) -> Type_:
        return Type_.ARRAY_OBJ

    def inspect(self) -> str:
        elements = []
        for e in self.elements:
            elements.append(e.inspect())
        return f"[{', '.join(elements)}]"

class HashPair:
    def __init__(self, key: Object, value: Object) -> None:
        self.key = key
        self.value = value

class Hash(Object):
    def __init__(self, pairs: Dict[HashKey, HashPair]) -> None:
        self.pairs = pairs

    def type_(self) -> Type_:
        return Type_.HASH_OBJ

    def inspect(self) -> str:
        pairs = []
        for _, pair in self.pairs.items():
            pairs.append(f"{pair.key.inspect()}: {pair.value.inspect()}")
        return f"{{{', '.join(pairs)}}}"

BuiltinFunction = NewType("BuiltinFunction", Callable[[Object], Object])

class Builtin(Object):
    def __init__(self, fn: BuiltinFunction):
        self.fn = fn

    def type_(self) -> Type_:
        return Type_.BUILTIN_OBJ

    def inspect(self) -> str:
        return "builtin function"
