from typing import List, Union, NewType, Callable, Dict
import object

def _len_built_in(args: List[object.Object]) -> Union[object.Integer, object.Error]:
    if len(args) != 1:
        return object.Error(f"wrong number of arguments. Got {len(args)}, want 1")
    if isinstance(args[0], object.String):
        return object.Integer(len(args[0].value))
    elif isinstance(args[0], object.Array):
        return object.Integer(len(args[0].elements))
    else:
        return object.Error(f"argument to 'len' not supported. Got {args[0].type_().value}")

def _first_built_in(args: List[object.Object]) -> object.Object:
    from evaluator import Evaluator
    if len(args) != 1:
        return object.Error(f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != object.ObjectType.ARRAY:
        return object.Error(f"argument to 'first' must be ARRAY. Got {args[0].type_().value}")
    array = args[0]
    if len(array.elements) > 0:
        return array.elements[0]
    return Evaluator.null

def _last_built_in(args: List[object.Array]) -> object.Object:
    from evaluator import Evaluator
    if len(args) != 1:
        return object.Error(f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != object.ObjectType.ARRAY:
        return object.Error(f"argument to 'last' must be ARRAY. Got {args[0].type_().value}")
    array = args[0]
    length = len(array.elements)
    if length > 0:
        return array.elements[length - 1]
    return Evaluator.null

def _rest_built_in(args: List[object.Array]) -> object.Object:
    from evaluator import Evaluator
    if len(args) != 1:
        return object.Error(f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != object.ObjectType.ARRAY:
        return object.Error(f"argument to 'rest' must be ARRAY. Got {args[0].type_().value}")
    array = args[0]
    length = len(array.elements)
    if length > 0:
        new_elements = array.elements[1:].copy()
        return object.Array(new_elements)
    return Evaluator.null

def _push_built_in(args: List[object.Array]) -> object.Object:
    if len(args) != 2:
        return object.Error(f"wrong number of arguments. Got {len(args)}, want 2")
    if args[0].type_() != object.ObjectType.ARRAY:
        return object.Error(f"argument to 'push' must be ARRAY. Got {args[0].type_().value}")
    array = args[0]
    # Monkey arrays are immutable so we must clone the underlying Python type
    new_elements = array.elements.copy()
    new_elements.append(args[1])
    return object.Array(new_elements)

def _puts_built_in(args: List[object.Object]) -> object.Object: # TODO: why not object.Null?
    from evaluator import Evaluator    
    for arg in args:
        print(arg.inspect())
    return Evaluator.null

BuiltinFunction = NewType("BuiltinFunction", Callable[[object.Object], object.Object])
builtins: Dict[str, BuiltinFunction] = {
    "len": object.Builtin(_len_built_in),
    "first": object.Builtin(_first_built_in),
    "last": object.Builtin(_last_built_in),
    "rest": object.Builtin(_rest_built_in),
    "push": object.Builtin(_push_built_in),
    "puts": object.Builtin(_puts_built_in)
}
