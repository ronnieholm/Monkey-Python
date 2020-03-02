# pylint: disable=import-outside-toplevel
from typing import List, Dict, cast
import monkey_object


def _len(args: List[monkey_object.MonkeyObject]) -> monkey_object.MonkeyObject:
    if len(args) != 1:
        return monkey_object.Error(
            f"wrong number of arguments. Got {len(args)}, want 1")
    if isinstance(args[0], monkey_object.String):
        return monkey_object.Integer(len(args[0].value))
    if isinstance(args[0], monkey_object.Array):
        return monkey_object.Integer(len(args[0].elements))
    return monkey_object.Error(
        f"argument to 'len' not supported. Got {args[0].type_().value}")


def _first(args: List[monkey_object.MonkeyObject]) -> monkey_object.MonkeyObject:
    from evaluator import Evaluator
    if len(args) != 1:
        return monkey_object.Error(
            f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != monkey_object.ObjectType.ARRAY:
        return monkey_object.Error(
            f"argument to 'first' must be ARRAY. Got {args[0].type_().value}")
    array = cast(monkey_object.Array, args[0])
    if len(array.elements) > 0:
        return array.elements[0]
    return Evaluator.null


def _last(args: List[monkey_object.MonkeyObject]) -> monkey_object.MonkeyObject:
    from evaluator import Evaluator
    if len(args) != 1:
        return monkey_object.Error(
            f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != monkey_object.ObjectType.ARRAY:
        return monkey_object.Error(
            f"argument to 'last' must be ARRAY. Got {args[0].type_().value}")
    array = cast(monkey_object.Array, args[0])
    length = len(array.elements)
    if length > 0:
        return array.elements[length - 1]
    return Evaluator.null


def _rest(args: List[monkey_object.MonkeyObject]) -> monkey_object.MonkeyObject:
    from evaluator import Evaluator
    if len(args) != 1:
        return monkey_object.Error(
            f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != monkey_object.ObjectType.ARRAY:
        return monkey_object.Error(
            f"argument to 'rest' must be ARRAY. Got {args[0].type_().value}")
    array = cast(monkey_object.Array, args[0])
    length = len(array.elements)
    if length > 0:
        new_elements = array.elements[1:].copy()
        return monkey_object.Array(new_elements)
    return Evaluator.null


def _push(args: List[monkey_object.MonkeyObject]) -> monkey_object.MonkeyObject:
    if len(args) != 2:
        return monkey_object.Error(
            f"wrong number of arguments. Got {len(args)}, want 2")
    if args[0].type_() != monkey_object.ObjectType.ARRAY:
        return monkey_object.Error(
            f"argument to 'push' must be ARRAY. Got {args[0].type_().value}")
    array = cast(monkey_object.Array, args[0])
    # Monkey arrays are immutable so we must clone the underlying Python type
    new_elements = array.elements.copy()
    new_elements.append(args[1])
    return monkey_object.Array(new_elements)


def _puts(args: List[monkey_object.MonkeyObject]) -> monkey_object.MonkeyObject:
    from evaluator import Evaluator
    for arg in args:
        print(arg.inspect())
    return Evaluator.null


builtins: Dict[str, monkey_object.Builtin] = {
    "len": monkey_object.Builtin(_len),
    "first": monkey_object.Builtin(_first),
    "last": monkey_object.Builtin(_last),
    "rest": monkey_object.Builtin(_rest),
    "push": monkey_object.Builtin(_push),
    "puts": monkey_object.Builtin(_puts)
}
