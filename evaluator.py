from typing import List, Optional, Dict, cast
import ast
import environment
import monkey_object
import builtin


class Evaluator:
    # As there's only ever a need for a single instance of each of these values,
    # we optimize by pre-creating instances to return during evaluation.
    null = monkey_object.Null()
    true = monkey_object.Boolean(True)
    false = monkey_object.Boolean(False)

    def eval(self, node: ast.Node,
             env: environment.Environment) -> Optional[monkey_object.MonkeyObject]:
        # statements
        if isinstance(node, ast.Program):
            return self._eval_program(cast(List[ast.BlockStatement], node.statements), env)
        if isinstance(node, ast.ExpressionStatement):
            return self.eval(node.expression, env)
        if isinstance(node, ast.BlockStatement):
            return self._eval_block_statement(cast(List[ast.Statement], node.statements), env)
        if isinstance(node, ast.ReturnStatement):
            value = self.eval(node.return_value, env)

            # We want to assert rather than "if value is None: return None".
            # While the latter also satisfies mypy, we'd lose track of where the
            # None originated. eval would end up returning None with no hint as
            # to which downstream method it originated from, making debugging
            # difficult. The type checker understands assert statement.
            assert value is not None

            # Check for errors whenever Eval is called inside Eval in order to
            # stop errors from being passed around and bubbling up far from
            # their origin.
            if self._is_error(value):
                return value
            return monkey_object.ReturnValue(value)
        if isinstance(node, ast.LetStatement):
            value = self.eval(node.value, env)
            assert value is not None
            if self._is_error(value):
                return value
            return env.set(node.name.value, value)

        # expressions
        if isinstance(node, ast.IntegerLiteral):
            return monkey_object.Integer(node.value)
        if isinstance(node, ast.StringLiteral):
            return monkey_object.String(node.value)
        if isinstance(node, ast.Boolean):
            return self._native_bool_to_boolean_object(node.value)
        if isinstance(node, ast.PrefixExpression):
            right = self.eval(node.right, env)
            assert right is not None
            if self._is_error(right):
                return right
            return self._eval_prefix_expression(node.operator, right)
        if isinstance(node, ast.InfixExpression):
            left = self.eval(node.left, env)
            assert left is not None
            if self._is_error(left):
                return left
            right = self.eval(node.right, env)
            assert right is not None
            if self._is_error(right):
                return right
            return self._eval_infix_expression(node.operator, left, right)
        if isinstance(node, ast.IfExpression):
            return self._eval_if_expression(node, env)
        if isinstance(node, ast.Identifier):
            return self._eval_identifier(node, env)
        if isinstance(node, ast.FunctionLiteral):
            params = node.parameters
            body = node.body
            return monkey_object.Function(params, body, env)
        if isinstance(node, ast.CallExpression):
            function = self.eval(node.function, env)
            assert function is not None
            if self._is_error(function):
                return function
            args = self._eval_expressions(node.arguments, env)
            assert args is not None
            if len(args) == 1 and self._is_error(args[0]):
                return args[0]
            return self._apply_function(function, args)
        if isinstance(node, ast.ArrayLiteral):
            elements = self._eval_expressions(node.elements, env)
            assert elements is not None
            if len(elements) == 1 and self._is_error(elements[0]):
                return elements[0]
            return monkey_object.Array(elements)
        if isinstance(node, ast.IndexExpression):
            left = self.eval(node.left, env)
            assert left is not None
            if self._is_error(left):
                return left
            index = self.eval(node.index, env)
            assert index is not None
            if self._is_error(index):
                return index
            return self._eval_index_expression(left, index)
        if isinstance(node, ast.HashLiteral):
            return self._eval_hash_literal(node, env)

        raise NotImplementedError

    def _apply_function(self, function: monkey_object.MonkeyObject,
                        args: List[monkey_object.MonkeyObject]) -> \
                        Optional[monkey_object.MonkeyObject]:
        if isinstance(function, monkey_object.Function):
            extended_env = self._extend_function_environment(function, args)
            evaluated = self.eval(function.body, extended_env)
            assert evaluated is not None
            return self._unwrap_return_value(evaluated)
        if isinstance(function, monkey_object.Builtin):
            return function.function(args)
        return monkey_object.Error(f"not a function: {function.type_().value}")

    def _extend_function_environment(self, function: monkey_object.Function,
                                     args: List[monkey_object.MonkeyObject]) -> \
                                     environment.Environment:
        env = environment.Environment.new_enclosed_environment(function.env)
        for param_idx, param in enumerate(function.parameters):
            env.set(param.value, args[param_idx])
        return env

    def _unwrap_return_value(self, obj: monkey_object.MonkeyObject) -> monkey_object.MonkeyObject:
        # Unwrapping prevents a return statement from bubbling up through
        # several functions and stopping evaluation in all of them. We only want
        # to stop the evaluation of the last called function's body. Otherwise,
        # _eval_block_statement would stop evaluating statements in outer
        # functions.
        return obj.value if isinstance(obj, monkey_object.ReturnValue) else obj

    def _eval_program(self, stmts: List[ast.BlockStatement],
                      env: environment.Environment) -> \
                      Optional[monkey_object.MonkeyObject]:
        result = None
        for stmt in stmts:
            result = self.eval(stmt, env)

            # Prevents further evaluation if the result of the evaluation is a
            # return statement. Note how we don't return ReturnValue directly,
            # but unwrap its value. ReturnValue is an internal detail to allow
            # Eval() to signal to its caller that it encountered and evaluated a
            # return statement.
            if isinstance(result, monkey_object.ReturnValue):
                return result.value
            if isinstance(result, monkey_object.Error):
                return result
        return result

    def _eval_block_statement(self, stmts: List[ast.Statement],
                              env: environment.Environment) -> \
                              Optional[monkey_object.MonkeyObject]:
        result = None
        for stmt in stmts:
            result = self.eval(stmt, env)
            if result is not None:
                if isinstance(result, (monkey_object.ReturnValue, monkey_object.Error)):
                    # Compared to _eval_program(), we don't unwrap the return
                    # value. Instead when an ReturnValue is encountered as the
                    # result of evaluating a statement, we return it to
                    # _eval_program() for unwrapping. This halts outer block
                    # evaluation and bubbles up the result.
                    return result
        return result

    def _native_bool_to_boolean_object(self, value: bool) -> monkey_object.Boolean:
        return Evaluator.true if value else Evaluator.false

    def _eval_prefix_expression(self, operator: str,
                                right: monkey_object.MonkeyObject) -> \
                                monkey_object.MonkeyObject:
        if operator == "!":
            return self._eval_bang_operator_expression(right)
        if operator == "-":
            return self._eval_minus_prefix_operator_expression(right)
        return monkey_object.Error(f"unknown operator: {operator}{right.type_().value}")

    def _eval_bang_operator_expression(self, right: monkey_object.MonkeyObject) -> \
                                       monkey_object.MonkeyObject:
        if right == Evaluator.true:
            return Evaluator.false
        if right == Evaluator.false:
            return Evaluator.true
        if right == Evaluator.null:
            return Evaluator.true
        return Evaluator.false

    def _eval_minus_prefix_operator_expression(self, right: monkey_object.MonkeyObject) -> \
                                               monkey_object.MonkeyObject:
        if right.type_() != monkey_object.ObjectType.INTEGER:
            return monkey_object.Error(f"unknown operator: -{right.type_().value}")
        value = cast(monkey_object.Integer, right).value
        return monkey_object.Integer(-value)

    def _eval_infix_expression(self, operator: str, left: monkey_object.MonkeyObject,
                               right: monkey_object.MonkeyObject) -> monkey_object.MonkeyObject:
        if left.type_() == monkey_object.ObjectType.INTEGER and \
           right.type_() == monkey_object.ObjectType.INTEGER:
            return self._eval_integer_infix_expression(operator, left, right)
        if left.type_() == monkey_object.ObjectType.STRING and \
           right.type_() == monkey_object.ObjectType.STRING:
            return self._eval_string_infix_expression(operator, left, right)
        # For booleans we can use reference comparison to check for equality. It
        # works because of our singleton True and False instances but wouldn't
        # work for integers since they aren't singletons. 5 == 5 would be false
        # when comparing references. To compare integer we must unwrap the
        # integer stored inside each Integer object and compare their values.
        if operator == "==":
            return self._native_bool_to_boolean_object(left == right)
        if operator == "!=":
            return self._native_bool_to_boolean_object(left != right)
        if left.type_() != right.type_():
            return monkey_object.Error(
                f"type mismatch: {left.type_().value} {operator} {right.type_().value}")
        return monkey_object.Error(
            f"unknown operator: {left.type_().value} {operator} {right.type_().value}")

    def _eval_integer_infix_expression(self, operator: str, left: monkey_object.MonkeyObject,
                                       right: monkey_object.MonkeyObject) -> \
                                       monkey_object.MonkeyObject:
        # Called from _eval_infix_expression which type type assertion. mypy
        # cannot infer, so we have to explicitly guard with asserts.
        assert isinstance(left, monkey_object.Integer)
        assert isinstance(right, monkey_object.Integer)
        left_val = left.value
        right_val = right.value
        if operator == "+":
            return monkey_object.Integer(left_val + right_val)
        if operator == "-":
            return monkey_object.Integer(left_val - right_val)
        if operator == "*":
            return monkey_object.Integer(left_val * right_val)
        if operator == "/":
            return monkey_object.Integer(left_val // right_val)
        if operator == "<":
            return self._native_bool_to_boolean_object(left_val < right_val)
        if operator == ">":
            return self._native_bool_to_boolean_object(left_val > right_val)
        if operator == "==":
            return self._native_bool_to_boolean_object(left_val == right_val)
        if operator == "!=":
            return self._native_bool_to_boolean_object(left_val != right_val)
        return monkey_object.Error(
            f"unknown operator: {left.type_().value} {operator} {right.type_().value}")

    def _eval_string_infix_expression(self, operator: str,
                                      left: monkey_object.MonkeyObject,
                                      right: monkey_object.MonkeyObject) -> \
                                      monkey_object.MonkeyObject:
        assert isinstance(left, monkey_object.String)
        assert isinstance(right, monkey_object.String)
        if operator != "+":
            return monkey_object.Error(
                f"unknown operator: {left.type_().value} {operator} {right.type_().value}")
        left_val = left.value
        right_val = right.value
        return monkey_object.String(left_val + right_val)

    def _eval_if_expression(self, expr: ast.IfExpression,
                            env: environment.Environment) -> \
                            Optional[monkey_object.MonkeyObject]:
        condition = self.eval(expr.condition, env)
        assert condition is not None
        if self._is_error(condition):
            return condition
        if self._is_truthy(condition):
            return self.eval(expr.consequence, env)
        if expr.alternative is not None:
            return self.eval(expr.alternative, env)
        return Evaluator.null

    def _eval_identifier(self, node: ast.Identifier, env: environment.Environment) -> \
                         monkey_object.MonkeyObject:
        value = env.get(node.value)
        if value is not None:
            return value
        if node.value in builtin.builtins:
            return builtin.builtins[node.value]
        return monkey_object.Error(f"identifier not found: {node.value}")

    def _eval_expressions(self, exprs: List[ast.Expression],
                          env: environment.Environment) -> \
                          Optional[List[monkey_object.MonkeyObject]]:
        result = []

        # By definition arguments are evaluated left to right. Since the side
        # effect of evaluating one argument might be relied on during evaluation
        # of the next, defining an explicit evaluation order is important.
        for expr in exprs:
            evaluated = self.eval(expr, env)
            assert evaluated is not None
            if self._is_error(evaluated):
                return [evaluated]
            result.append(evaluated)
        return result

    def _eval_index_expression(self, left: monkey_object.MonkeyObject,
                               index: monkey_object.MonkeyObject) -> \
                               monkey_object.MonkeyObject:
        if left.type_() == monkey_object.ObjectType.ARRAY and \
           index.type_() == monkey_object.ObjectType.INTEGER:
            return self._eval_array_index_expression(left, index)
        if left.type_() == monkey_object.ObjectType.HASH:
            return self._eval_hash_index_expression(left, index)
        return monkey_object.Error(f"index operator not supported: {left.type_().value}")

    def _eval_array_index_expression(self, array: monkey_object.MonkeyObject,
                                     index: monkey_object.MonkeyObject) -> \
                                     monkey_object.MonkeyObject:
        assert isinstance(array, monkey_object.Array)
        assert isinstance(index, monkey_object.Integer)
        idx = index.value
        max_index = len(array.elements) - 1
        if idx < 0 or idx > max_index:
            # Some languages throw an exception when the index is out of bounds.
            # In Monkey by definition we return null as the result.
            return Evaluator.null
        return array.elements[idx]

    def _eval_hash_index_expression(self, expr: monkey_object.MonkeyObject,
                                    index: monkey_object.MonkeyObject) -> \
                                    monkey_object.MonkeyObject:
        if not isinstance(index, monkey_object.Hashable):
            return monkey_object.Error(f"unusable as hash key: {index.type_().value}")
        if not index.hash_key() in expr.pairs:
            return Evaluator.null
        return expr.pairs[index.hash_key()].value

    def _eval_hash_literal(self, node: ast.HashLiteral,
                           env: environment.Environment) -> Optional[monkey_object.MonkeyObject]:
        pairs: Dict[monkey_object.HashKey, monkey_object.HashPair] = {}
        for key_node, value_node in node.pairs.items():
            key = self.eval(key_node, env)
            assert key is not None
            if self._is_error(key):
                return key
            if not isinstance(key, monkey_object.Hashable):
                return monkey_object.Error(f"unusable as hash key: {key.type_().value}")
            value = self.eval(value_node, env)
            if self._is_error(value):
                return value
            hashed = key.hash_key()
            pairs[hashed] = monkey_object.HashPair(key, value)
        return monkey_object.Hash(pairs)

    def _is_truthy(self, obj: monkey_object.MonkeyObject) -> bool:
        if obj == Evaluator.null:
            return False
        if obj == Evaluator.true:
            return True
        if obj == Evaluator.false:
            return False
        return True

    def _is_error(self, obj: monkey_object.MonkeyObject) -> bool:
        if obj is not None:
            return isinstance(obj, monkey_object.Error)
        return False
