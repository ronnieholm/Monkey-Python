from typing import List, Optional, Type, Dict, Callable, NewType, Union
import ast
import environment
import object

# TODO: Move to statics inside Builtin?
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
    if len(args) != 1:
        return object.Error(f"wrong number of arguments. Got {len(args)}, want 1")
    if args[0].type_() != object.ObjectType.ARRAY:
        return object.Error(f"argument to 'first' must be ARRAY. Got {args[0].type_().value}")
    array = args[0]
    if len(array.elements) > 0:
        return array.elements[0]
    return Evaluator.null

def _last_built_in(args: List[object.Array]) -> object.Object:
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

class Evaluator:
    # As there's only ever a need for a single instance of each of these values,
    # we optimize by pre-creating instances to return during evaluation.    
    null = object.Null()
    true = object.Boolean(True)
    false = object.Boolean(False)

    def __init__(self):
        pass

    def eval(self, node: ast.Node, env: environment.Environment) -> object.Object:
        # statements
        if isinstance(node, ast.Program):
            return self._eval_program(node.statements, env)
        elif isinstance(node, ast.ExpressionStatement):
            return self.eval(node.expression, env)
        elif isinstance(node, ast.BlockStatement):
            return self._eval_block_statement(node.statements, env)
        elif isinstance(node, ast.ReturnStatement):
            value = self.eval(node.return_value, env)

            # Check for errors whenever Eval is called inside Eval in order to
            # stop errors from being passed around and bubbling up far from
            # their origin.            
            if self._is_error(value):
                return value
            return object.ReturnValue(value)
        elif isinstance(node, ast.LetStatement):
            value = self.eval(node.value, env)
            if self._is_error(value):
                return value
            return env.set(node.name.value, value)            
        
        # expressions
        elif isinstance(node, ast.IntegerLiteral):
            return object.Integer(node.value)
        elif isinstance(node, ast.StringLiteral):
            return object.String(node.value)
        elif isinstance(node, ast.Boolean):
            return self._native_bool_to_boolean_object(node.value)
        elif isinstance(node, ast.PrefixExpression):
            right = self.eval(node.right, env)            
            if self._is_error(node.right):
                return right
            return self._eval_prefix_expression(node.operator, right)
        elif isinstance(node, ast.InfixExpression):
            left = self.eval(node.left, env)
            if self._is_error(left):
                return left
            right = self.eval(node.right, env)
            if self._is_error(right):
                return right
            return self._eval_infix_expression(node.operator, left, right)
        elif isinstance(node, ast.IfExpression):
            return self._eval_if_expression(node, env)
        elif isinstance(node, ast.Identifier):
            return self._eval_identifier(node, env)
        elif isinstance(node, ast.FunctionLiteral):
            params = node.parameters
            body = node.body
            return object.Function(params, body, env)
        elif isinstance(node, ast.CallExpression):
            function = self.eval(node.function, env)
            if self._is_error(function):
                return function
            args = self._eval_expressions(node.arguments, env)
            if len(args) == 1 and self._is_error(args[0]):
                return args[0]
            return self._apply_function(function, args)
        elif isinstance(node, ast.ArrayLiteral):
            elements = self._eval_expressions(node.elements, env)
            if len(elements) == 1 and self._is_error(elements[0]):
                return elements[0]
            return object.Array(elements)
        elif isinstance(node, ast.IndexExpression):
            left = self.eval(node.left, env)
            if self._is_error(left):
                return left
            index = self.eval(node.index, env)
            if self._is_error(index):
                return index
            return self._eval_index_expression(left, index)
        elif isinstance(node, ast.HashLiteral):
            return self._eval_hash_literal(node, env)

        raise NotImplementedError

    def _apply_function(self, fn: object.Object, args: List[object.Object]) -> object.Object:
        if isinstance(fn, object.Function):
            extended_env = self._extend_function_environment(fn, args)
            evaluated = self.eval(fn.body, extended_env)
            return self._unwrap_return_value(evaluated)
        elif isinstance(fn, object.Builtin):
            return fn.fn(args)
        else:
            return object.Error(f"not a function: {fn.type_().value}")

    def _extend_function_environment(self, fn: object.Function, args: List[object.Object]) -> environment.Environment:
        env = environment.Environment.new_enclosed_environment(fn.env)
        for param_idx, param in enumerate(fn.parameters):
            env.set(param.value, args[param_idx])
        return env

    def _unwrap_return_value(self, obj: object.Object) -> object.Object:
        # Unwrapping prevents a return statement from bubbling up through
        # several functions and stopping evaluation in all of them. We only want
        # to stop the evaluation of the last called function's body. Otherwise,
        # _eval_block_statement would stop evaluating statements in outer
        # functions.        
        if isinstance(obj, object.ReturnValue):
            return obj.value
        return obj

    def _eval_program(self, stmts: List[ast.BlockStatement], env: environment.Environment) -> Optional[object.Object]:
        result = None
        for s in stmts:
            result = self.eval(s, env)

            # Prevents further evaluation if the result of the evaluation is a
            # return statement. Note how we don't return ReturnValue directly,
            # but unwrap its value. ReturnValue is an internal detail to allow
            # Eval() to signal to its caller that it encountered and evaluated a
            # return statement.            
            if isinstance(result, object.ReturnValue):
                return result.value
            elif isinstance(result, object.Error):
                return result
        return result

    def _eval_block_statement(self, stmts: List[ast.Statement], env: environment.Environment) -> Optional[object.Object]:
        result = None
        for s in stmts:
            result = self.eval(s, env)
            if result != None:
                if isinstance(result, object.ReturnValue) or isinstance(result, object.Error):
                    # Compared to _eval_program(), we don't unwrap the return
                    # value. Instead when an ReturnValue is encountered as the
                    # result of evaluating a statement, we return it to
                    # _eval_program() for unwrapping. This halts outer block
                    # evaluation and bubbles up the result.
                    return result
        return result

    def _native_bool_to_boolean_object(self, input: bool) -> object.Boolean:
        if input:
            return Evaluator.true
        else:
            return Evaluator.false

    def _eval_prefix_expression(self, operator: str, right: object.Object) -> object.Object:
        if operator == "!":
            return self._eval_bang_operator_expression(right)
        elif operator == "-":
            return self._eval_minus_prefix_operator_expression(right)
        else:
            return object.Error(f"unknown operator: {operator}{right.type_().value}")


    def _eval_bang_operator_expression(self, right: object.Object) -> object.Object:
        if right == Evaluator.true:
            return Evaluator.false
        elif right == Evaluator.false:
            return Evaluator.true
        elif right == Evaluator.null:
            return Evaluator.true
        else:
            return Evaluator.false

    def _eval_minus_prefix_operator_expression(self, right: object.Object) -> object.Object:
        if right.type_() != object.ObjectType.INTEGER:
            return object.Error(f"unknown operator: -{right.type_().value}")
        value = right.value
        return object.Integer(value = -value)

    def _eval_infix_expression(self, operator: str, left: object.Object, right: object.Object) -> object.Object:
        if left.type_() == object.ObjectType.INTEGER and right.type_() == object.ObjectType.INTEGER:
            return self._eval_integer_infix_expression(operator, left, right)
        elif left.type_() == object.ObjectType.STRING and right.type_() == object.ObjectType.STRING:
            return self._eval_string_infix_expression(operator, left, right)        
        # For booleans we can use reference comparison to check for equality. It
        # works because of our singleton True and False instances but wouldn't
        # work for integers since they aren't singletons. 5 == 5 would be false
        # when comparing references. To compare integer we must unwrap the
        # integer stored inside each Integer object and compare their values.
        elif operator == "==":
            return self._native_bool_to_boolean_object(left == right)
        elif operator == "!=":
            return self._native_bool_to_boolean_object(left != right)
        elif left.type_() != right.type_():
            return object.Error(f"type mismatch: {left.type_().value} {operator} {right.type_().value}")
        else:
            return object.Error(f"unknown operator: {left.type_().value} {operator} {right.type_().value}")

    def _eval_integer_infix_expression(self, operator: str, left: object.Object, right: object.Object) -> object.Object:
        left_val = left.value # TODO: type assert with mypy or leave lines out
        right_val = right.value
        if operator == "+":
            return object.Integer(value = left_val + right_val)
        elif operator == "-":
            return object.Integer(value = left_val - right_val)
        elif operator == "*":
            return object.Integer(value = left_val * right_val)
        elif operator == "/":
            return object.Integer(value = left_val / right_val)
        elif operator == "<":
            return self._native_bool_to_boolean_object(left_val < right_val)
        elif operator == ">":
            return self._native_bool_to_boolean_object(left_val > right_val)
        elif operator == "==":
            return self._native_bool_to_boolean_object(left_val == right_val)            
        elif operator == "!=":
            return self._native_bool_to_boolean_object(left_val != right_val)            
        else:
            return object.Error(f"unknown operator: {left.type_().value} {operator} {right.type_().value}")

    def _eval_string_infix_expression(self, operator: str, left: object.Object, right: object.Object) -> object.Object:
        if operator != "+":
            return object.Error(f"unknown operator: {left.type_().value} {operator} {right.type_().value}")
        left_val = left.value
        right_val = right.value
        return object.String(left_val + right_val)

    def _eval_if_expression(self, ie: ast.IfExpression, env: environment.Environment) -> object.Object:
        condition = self.eval(ie.condition, env)
        if self._is_error(condition):
            return condition
        if self._is_truthy(condition):
            return self.eval(ie.consequence, env)
        elif ie.alternative != None:
            return self.eval(ie.alternative, env)
        else:
            return Evaluator.null

    def _eval_identifier(self, node: ast.Identifier, env: environment.Environment) -> object.Object:
        value, ok = env.get(node.value)
        if ok:
            return value       
        if node.value in builtins:
            return builtins[node.value]
        return object.Error(f"identifier not found: {node.value}")

    def _eval_expressions(self, exprs: List[ast.Expression], env: environment.Environment) -> List[object.Object]:
        result = []

        # By definition arguments are evaluated left to right. Since the side
        # effect of evaluating one argument might be relied on during evaluation
        # of the next, defining an explicit evaluation order is important.
        for e in exprs:
            evaluated = self.eval(e, env)
            if self._is_error(evaluated):
                return [evaluated]
            result.append(evaluated)
        return result

    def _eval_index_expression(self, left: object.Object, index: object.Object) -> object.Object:
        if left.type_() == object.ObjectType.ARRAY and index.type_() == object.ObjectType.INTEGER:
            return self._eval_array_index_expression(left, index)
        elif left.type_() == object.ObjectType.HASH:
            return self._eval_hash_index_expression(left, index)
        return object.Error(f"index operator not supported: {left.type_().value}")

    def _eval_array_index_expression(self, array: object.Object, index: object.Object) -> object.Object:
        idx = index.value
        max = len(array.elements) - 1
        if idx < 0 or idx > max:
            # Some languages throw an exception when the index is out of bounds.
            # In Monkey by definition we return null as the result.
            return Evaluator.null
        return array.elements[idx]

    def _eval_hash_index_expression(self, hash: object.Object, index: object.Object) -> object.Object:
        if not isinstance(index, object.Hashable):
            return object.Error(f"unusable as hash key: {index.type_().value}")
        if not index.hash_key() in hash.pairs:
            return Evaluator.null
        return hash.pairs[index.hash_key()].value

    def _eval_hash_literal(self, node: ast.HashLiteral, env: environment.Environment) -> object.Object:
        pairs: Dict[object.HashKey, object.HashPair] = {}
        for key_node, value_node in node.pairs.items():
            key = self.eval(key_node, env)
            if self._is_error(key):
                return key
            if not isinstance(key, object.Hashable):
                return object.Error(f"unusable as hash key: {key.type_().value}")
            value = self.eval(value_node, env)
            if self._is_error(value):
                return value
            hashed = key.hash_key()
            pairs[hashed] = object.HashPair(key, value)
        return object.Hash(pairs)

    def _is_truthy(self, obj: object.Object) -> bool:
        if obj == Evaluator.null:
            return False
        elif obj == Evaluator.true:
            return True
        elif obj == Evaluator.false:
            return False
        else:
            return True

    def _is_error(self, obj: object.Object) -> bool:
        if obj != None:
            return isinstance(obj, object.Error)
        return False
