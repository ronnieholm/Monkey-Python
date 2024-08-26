from typing import cast, Union, Any
from collections import namedtuple
import unittest
import mast
from mparser import Parser
from lexer import Lexer


class ParserTests(unittest.TestCase):
    def _setup_program(self, source: str) -> mast.Program:
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        return program

    def test_let_statements(self) -> None:
        Case = namedtuple(
            "Case", ["source", "expected_identifier", "expected_value"])
        tests = [
            Case("let x = 5;", "x", 5),
            Case("let y = true;", "y", True),
            Case("let foobar = y", "foobar", "y")]

        for test in tests:
            program = self._setup_program(test.source)
            self.assertEqual(len(program.statements), 1)
            stmt = cast(mast.LetStatement, program.statements[0])
            self._test_let_statement(stmt, test.expected_identifier)
            self.assertIsInstance(stmt, mast.LetStatement)
            value = stmt.value
            self._test_literal_expression(value, test.expected_value)

    def _test_let_statement(self, stmt: mast.Statement, name: str) -> None:
        self.assertEqual(stmt.token_literal(), "let")
        # Downside of type checking being done by a seperate program is that we
        # must assert the same thing twice: first to satisfy the runtime unit
        # test and second to satisfy mypy.
        self.assertIsInstance(stmt, mast.LetStatement)
        let_stmt = cast(mast.LetStatement, stmt)
        self.assertEqual(let_stmt.name.value, name)
        self.assertEqual(let_stmt.name.token_literal(), name)

    def _check_parser_errors(self, parser: Parser) -> None:
        if len(parser.errors) == 0:
            return
        for message in parser.errors:
            print(message)
        self.fail("See stdout")

    def test_return_statements(self) -> None:
        Case = namedtuple("Case", ["source", "expected_value"])
        tests = [
            Case("return 5;", 5),
            Case("return true;", True),
            Case("return foobar;", "foobar")]

        for test in tests:
            program = self._setup_program(test.source)
            self.assertEqual(len(program.statements), 1)
            return_stmt = cast(mast.ReturnStatement, program.statements[0])
            self.assertIsInstance(return_stmt, mast.ReturnStatement)
            self.assertEqual(return_stmt.token_literal(), "return")
            self._test_literal_expression(
                return_stmt.return_value, test.expected_value)

    def test_identifier_expression(self) -> None:
        source = "foobar"
        program = self._setup_program(source)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        expr_stmt = cast(mast.ExpressionStatement, stmt)
        self.assertIsInstance(expr_stmt.expression, mast.Identifier)
        ident = cast(mast.Identifier, expr_stmt.expression)
        self.assertEqual(ident.value, "foobar")
        self.assertEqual(ident.token.literal, "foobar")

    def test_integer_literal_expression(self) -> None:
        source = "5"
        program = self._setup_program(source)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        expr_stmt = cast(mast.ExpressionStatement, stmt)
        self.assertIsInstance(expr_stmt.expression, mast.IntegerLiteral)
        literal = cast(mast.IntegerLiteral, expr_stmt.expression)
        self.assertEqual(literal.value, 5)
        self.assertEqual(literal.token.literal, "5")

    def test_parsing_prefix_expressions(self) -> None:
        Case = namedtuple("Case", ["source", "operator", "value"])
        tests = [Case("!5;", "!", 5),
                 Case("-15;", "-", 15),
                 Case("!true", "!", True),
                 Case("!false;", "!", False)]

        for test in tests:
            program = self._setup_program(test.source)
            self.assertEqual(len(program.statements), 1)
            stmt = program.statements[0]
            self.assertIsInstance(stmt, mast.ExpressionStatement)
            expr_stmt = cast(mast.ExpressionStatement, stmt)
            self.assertIsInstance(expr_stmt.expression, mast.PrefixExpression)
            expr = cast(mast.PrefixExpression, expr_stmt.expression)
            self.assertEqual(expr.operator, test.operator)
            self._test_literal_expression(expr.right, test.value)

    def _test_integer_literal(self, expr: mast.Expression, value: int) -> None:
        self.assertIsInstance(expr, mast.IntegerLiteral)
        integer = cast(mast.IntegerLiteral, expr)
        self.assertEqual(integer.value, value)
        self.assertEqual(integer.token.literal, str(value))

    def _test_identifier(self, expr: mast.Expression, value: str) -> None:
        self.assertIsInstance(expr, mast.Identifier)
        identifier = cast(mast.Identifier, expr)
        self.assertEqual(identifier.value, value)
        self.assertEqual(identifier.token.literal, value)

    def _test_boolean_literal(self, expr: mast.Expression, value: bool) -> None:
        self.assertIsInstance(expr, mast.Boolean)
        boolean = cast(mast.Boolean, expr)
        self.assertEqual(boolean.value, value)

        # Monkey and Python boolean literals differ
        if value:
            self.assertEqual(expr.token_literal(), "true")
        else:
            self.assertEqual(expr.token_literal(), "false")

    def _test_literal_expression(self, expr: mast.Expression,
                                 expected: Union[int, str, bool]) -> None:
        # bool check must preceed int check or bool is matched as int.
        if isinstance(expected, bool):
            self._test_boolean_literal(expr, cast(bool, expected))
        elif isinstance(expected, int):
            self._test_integer_literal(expr, cast(int, expected))
        elif isinstance(expected, str):
            self._test_identifier(expr, cast(str, expected))
        else:
            self.fail(f"type of expr not handled. Got {type(expected)}")

    def _test_infix_expression(self, expr: mast.Expression, left: Any,
                               operator: str, right: Any) -> None:
        self.assertIsInstance(expr, mast.InfixExpression)
        self._test_literal_expression(
            cast(mast.InfixExpression, expr).left, left)
        self.assertEqual(cast(mast.InfixExpression, expr).operator, operator)
        self._test_literal_expression(
            cast(mast.InfixExpression, expr).right, right)

    def test_parsing_infix_expressions(self) -> None:
        Case = namedtuple(
            "Case", ["source", "left_value", "operator", "right_value"])
        tests = [
            Case("5 + 5;", 5, "+", 5),
            Case("5 - 5;", 5, "-", 5),
            Case("5 * 5;", 5, "*", 5),
            Case("5 / 5;", 5, "/", 5),
            Case("5 > 5;", 5, ">", 5),
            Case("5 < 5;", 5, "<", 5),
            Case("5 == 5;", 5, "==", 5),
            Case("5 != 5;", 5, "!=", 5),
            Case("true == true", True, "==", True),
            Case("true != false", True, "!=", False),
            Case("false == false", False, "==", False)]

        for test in tests:
            program = self._setup_program(test.source)
            self.assertEqual(len(program.statements), 1)
            expr_stmt = cast(mast.ExpressionStatement, program.statements[0])
            expr = expr_stmt.expression
            self._test_infix_expression(
                expr, test.left_value, test.operator, test.right_value)

    def test_operator_precedence_parsing(self) -> None:
        Case = namedtuple("Case", ["source", "expected"])
        tests = [
            Case("-a * b", "((-a) * b)"),
            Case("!-a", "(!(-a))"),
            Case("a + b + c", "((a + b) + c)"),
            Case("a + b - c", "((a + b) - c)"),
            Case("a * b * c", "((a * b) * c)"),
            Case("a * b / c", "((a * b) / c)"),
            Case("a + b / c", "(a + (b / c))"),
            Case("a + b * c + d / e - f", "(((a + (b * c)) + (d / e)) - f)"),
            Case("3 + 4; -5 * 5", "(3 + 4)((-5) * 5)"),
            Case("5 > 4 == 3 < 4", "((5 > 4) == (3 < 4))"),
            Case("5 < 4 != 3 > 4", "((5 < 4) != (3 > 4))"),
            Case("3 + 4 * 5 == 3 * 1 + 4 * 5",
                 "((3 + (4 * 5)) == ((3 * 1) + (4 * 5)))"),
            Case("3 + 4 * 5 == 3 * 1 + 4 * 5",
                 "((3 + (4 * 5)) == ((3 * 1) + (4 * 5)))"),
            Case("true", "true"),
            Case("false", "false"),
            Case("3 > 5 == false", "((3 > 5) == false)"),
            Case("3 < 5 == true", "((3 < 5) == true)"),
            Case("1 + (2 + 3) + 4", "((1 + (2 + 3)) + 4)"),
            Case("(5 + 5) * 2", "((5 + 5) * 2)"),
            Case("2 / (5 + 5)", "(2 / (5 + 5))"),
            Case("-(5 + 5)", "(-(5 + 5))"),
            Case("!(true == true)", "(!(true == true))"),
            Case("a + add(b * c) + d", "((a + add((b * c))) + d)"),
            Case("add(a, b, 1, 2 * 3, 4 + 5, add(6, 7 * 8))",
                 "add(a, b, 1, (2 * 3), (4 + 5), add(6, (7 * 8)))"),
            Case("add(a + b + c * d / f + g)",
                 "add((((a + b) + ((c * d) / f)) + g))"),
            Case("a * [1, 2, 3, 4][b * c] * d",
                 "((a * ([1, 2, 3, 4][(b * c)])) * d)"),
            Case("add(a * b[2], b[1], 2 * [1, 2][1])",
                 "add((a * (b[2])), (b[1]), (2 * ([1, 2][1])))")]

        for test in tests:
            program = self._setup_program(test.source)
            # not self.assertEqual(len(program.statements), 1) as one test
            # consists of two statements.
            actual = program.string()
            self.assertEqual(actual, test.expected)

    def test_boolean_expressions(self) -> None:
        Case = namedtuple("Case", ["source", "expected"])
        tests = [Case("true", "true"),
                 Case("false", "false")]

        for test in tests:
            program = self._setup_program(test.source)
            actual = program.string()
            self.assertEqual(actual, test.expected)

    def test_if_expression(self) -> None:
        source = "if (x < y) { x }"
        program = self._setup_program(source)
        self.assertEqual(len(program.statements), 1)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt.expression, mast.IfExpression)
        expr = cast(mast.IfExpression, stmt.expression)
        self._test_infix_expression(expr.condition, "x", "<", "y")
        self.assertEqual(len(expr.consequence.statements), 1)
        consequence = cast(mast.ExpressionStatement,
                           expr.consequence.statements[0])
        self.assertIsInstance(consequence, mast.ExpressionStatement)
        self._test_identifier(consequence.expression, "x")
        self.assertEqual(expr.alternative, None)

    def test_if_else_expression(self) -> None:
        source = "if (x < y) { x } else { y }"
        program = self._setup_program(source)
        self.assertEqual(len(program.statements), 1)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt.expression, mast.IfExpression)
        expr = cast(mast.IfExpression, stmt.expression)
        self._test_infix_expression(expr.condition, "x", "<", "y")
        self.assertEqual(len(expr.consequence.statements), 1)
        consequence = cast(mast.ExpressionStatement,
                           expr.consequence.statements[0])
        self.assertIsInstance(consequence, mast.ExpressionStatement)
        self._test_identifier(consequence.expression, "x")
        assert expr.alternative is not None
        self.assertEqual(len(expr.alternative.statements), 1)
        alternative = cast(mast.ExpressionStatement,
                           expr.alternative.statements[0])
        self.assertIsInstance(alternative, mast.ExpressionStatement)
        self._test_identifier(alternative.expression, "y")

    def test_function_literal_parsing(self) -> None:
        source = "fn(x, y) { x + y; }"
        program = self._setup_program(source)
        self.assertEqual(len(program.statements), 1)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        function = stmt.expression
        self.assertIsInstance(function, mast.FunctionLiteral)
        literal = cast(mast.FunctionLiteral, function)
        self.assertEqual(len(literal.parameters), 2)
        self._test_literal_expression(literal.parameters[0], "x")
        self._test_literal_expression(literal.parameters[1], "y")
        self.assertEqual(len(literal.body.statements), 1)
        body_stmt = cast(mast.ExpressionStatement, literal.body.statements[0])
        self.assertIsInstance(body_stmt, mast.ExpressionStatement)
        self._test_infix_expression(body_stmt.expression, "x", "+", "y")

    def test_function_parameter_parsing(self) -> None:
        Case = namedtuple("Case", ["source", "expected_params"])
        tests = [Case("fn() {};", []),
                 Case("fn(x) {};", ["x"]),
                 Case("fn(x, y, z) {};", ["x", "y", "z"])]

        for test in tests:
            program = self._setup_program(test.source)
            stmt = cast(mast.ExpressionStatement, program.statements[0])
            self.assertIsInstance(stmt, mast.ExpressionStatement)
            function = cast(mast.FunctionLiteral, stmt.expression)
            self.assertIsInstance(function, mast.FunctionLiteral)
            self.assertEqual(len(test.expected_params),
                             len(function.parameters))
            for i, ident in enumerate(test.expected_params):
                self._test_literal_expression(function.parameters[i], ident)

    def test_call_expression_parsing(self) -> None:
        source = "add(1, 2 * 3, 4 + 5);"
        program = self._setup_program(source)
        self.assertEqual(len(program.statements), 1)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        expr = cast(mast.Expression, stmt.expression)
        self.assertIsInstance(expr, mast.CallExpression)
        call_expr = cast(mast.CallExpression, expr)
        self._test_identifier(call_expr.function, "add")
        self.assertEqual(len(call_expr.arguments), 3)
        self._test_literal_expression(call_expr.arguments[0], 1)
        self._test_infix_expression(call_expr.arguments[1], 2, "*", 3)
        self._test_infix_expression(call_expr.arguments[2], 4, "+", 5)

    def test_call_expression_parameter_parsing(self) -> None:
        Case = namedtuple(
            "Case", ["source", "expected_ident", "expected_args"])
        tests = [Case("add();", "add", []),
                 Case("add(1);", "add", [1]),
                 Case("add(1, 2 * 3, 4 + 5);", "add", ["1", "(2 * 3)", "(4 + 5)"])]

        for test in tests:
            program = self._setup_program(test.source)
            self.assertEqual(len(program.statements), 1)
            stmt = cast(mast.ExpressionStatement, program.statements[0])
            self.assertIsInstance(stmt, mast.ExpressionStatement)
            expr = cast(mast.CallExpression, stmt.expression)
            self.assertIsInstance(expr, mast.CallExpression)
            self._test_identifier(expr.function, test.expected_ident)
            self.assertEqual(len(expr.arguments), len(test.expected_args))
            for i, arg in enumerate(test.expected_args):
                self.assertEqual(arg, test.expected_args[i])

    def test_string_literal_expression(self) -> None:
        source = '"Hello world"'
        program = self._setup_program(source)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        literal = cast(mast.StringLiteral, stmt.expression)
        self.assertIsInstance(literal, mast.StringLiteral)
        self.assertEqual(literal.value, "Hello world")

    def test_parsing_array_literals(self) -> None:
        source = "[1, 2 * 2, 3 + 3]"
        program = self._setup_program(source)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        array = cast(mast.ArrayLiteral, stmt.expression)
        self.assertIsInstance(array, mast.ArrayLiteral)
        self.assertEqual(len(array.elements), 3)
        self._test_integer_literal(array.elements[0], 1)
        self._test_infix_expression(array.elements[1], 2, "*", 2)
        self._test_infix_expression(array.elements[2], 3, "+", 3)

    def test_parsing_index_expression(self) -> None:
        source = "myArray[1 + 1]"
        program = self._setup_program(source)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        index_expr = cast(mast.IndexExpression, stmt.expression)
        self.assertIsInstance(index_expr, mast.IndexExpression)
        self._test_identifier(index_expr.left, "myArray")
        self._test_infix_expression(index_expr.index, 1, "+", 1)

    def test_parsing_hash_literals_string_keys(self) -> None:
        source = '{"one": 1, "two": 2, "three": 3}'
        program = self._setup_program(source)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        hash_literal = cast(mast.HashLiteral, stmt.expression)
        self.assertIsInstance(hash_literal, mast.HashLiteral)
        self.assertEqual(len(hash_literal.pairs), 3)
        expected = {
            "one": 1,
            "two": 2,
            "three": 3
        }
        for key, value in hash_literal.pairs.items():
            self.assertIsInstance(key, mast.StringLiteral)
            expected_value = expected[key.string()]
            self._test_integer_literal(value, expected_value)

    def test_parsing_empty_hash_literal(self) -> None:
        source = "{}"
        program = self._setup_program(source)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        hash_literal = cast(mast.HashLiteral, stmt.expression)
        self.assertIsInstance(hash_literal, mast.HashLiteral)
        self.assertEqual(len(hash_literal.pairs), 0)

    def test_parsing_hash_literals_with_expressions(self) -> None:
        source = '{"one": 0 + 1, "two": 10 - 8, "three": 15 / 5}'
        program = self._setup_program(source)
        stmt = cast(mast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt, mast.ExpressionStatement)
        hash_literal = cast(mast.HashLiteral, stmt.expression)
        self.assertIsInstance(hash_literal, mast.HashLiteral)
        self.assertEqual(len(hash_literal.pairs), 3)
        expected = {
            "one": lambda e: self._test_infix_expression(e, 0, "+", 1),
            "two": lambda e: self._test_infix_expression(e, 10, "-", 8),
            "three": lambda e: self._test_infix_expression(e, 15, "/", 5)
        }
        for key, value in hash_literal.pairs.items():
            self.assertIsInstance(key, mast.StringLiteral)
            expected[key.string()](value)
