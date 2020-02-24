import ast
import unittest
from collections import namedtuple
from parser import Parser
from lexer import Lexer


class ParserTests(unittest.TestCase):
    def test_let_statements(self):
        Case = namedtuple(
            "Case", ["input", "expected_identifier", "expected_value"])
        tests = [
            Case("let x = 5;", "x", 5),
            Case("let y = true;", "y", True),
            Case("let foobar = y", "foobar", "y")]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            self.assertEqual(len(program.statements), 1)
            stmt = program.statements[0]
            self._test_let_statement(stmt, test.expected_identifier)
            self.assertIsInstance(stmt, ast.LetStatement)
            value = stmt.value
            self._test_literal_expression(value, test.expected_value)

    def _test_let_statement(self, stmt: ast.Statement, name: str):
        self.assertEqual(stmt.token_literal(), "let")
        self.assertIsInstance(stmt, ast.LetStatement)
        self.assertEqual(stmt.name.value, name)
        self.assertEqual(stmt.name.token_literal(), name)

    def _check_parser_errors(self, parser: Parser):
        if len(parser.errors) == 0:
            return
        for message in parser.errors:
            print(message)
        self.fail("See stdout")

    def test_return_statements(self):
        Case = namedtuple("Case", ["input", "expected_value"])
        tests = [
            Case("return 5;", 5),
            Case("return true;", True),
            Case("return foobar;", "foobar")]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            self.assertEqual(len(program.statements), 1)
            return_stmt = program.statements[0]
            self.assertIsInstance(return_stmt, ast.ReturnStatement)
            self.assertEqual(return_stmt.token_literal(), "return")
            self._test_literal_expression(
                return_stmt.return_value, test.expected_value)

    def test_identifier_expression(self):
        source = "foobar"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        self.assertIsInstance(stmt.expression, ast.Identifier)
        ident = stmt.expression
        self.assertEqual(ident.value, "foobar")
        self.assertEqual(ident.token.literal, "foobar")

    def test_integer_literal_expression(self):
        source = "5"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        self.assertIsInstance(stmt.expression, ast.IntegerLiteral)
        literal = stmt.expression
        self.assertEqual(literal.value, 5)
        self.assertEqual(literal.token.literal, "5")

    def test_parsing_prefix_expressions(self):
        Case = namedtuple("Case", ["input", "operator", "value"])
        tests = [
            Case("!5;", "!", 5),
            Case("-15;", "-", 15),
            Case("!true", "!", True),
            Case("!false;", "!", False)]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            self.assertEqual(len(program.statements), 1)
            stmt = program.statements[0]
            self.assertIsInstance(stmt, ast.ExpressionStatement)
            self.assertIsInstance(stmt.expression, ast.PrefixExpression)
            expr = stmt.expression
            self.assertEqual(expr.operator, test.operator)
            if not self._test_integer_literal(expr.right, test.value):
                return

    def _test_integer_literal(self, expr: ast.Expression, value: int) -> None:
        self.assertIsInstance(expr, ast.IntegerLiteral)
        integer = expr
        self.assertEqual(integer.value, value)
        self.assertEqual(integer.token.literal, str(value))

    def _test_identifier(self, expr: ast.Expression, value: str) -> None:
        self.assertIsInstance(expr, ast.Identifier)
        self.assertEqual(expr.value, value)
        self.assertEqual(expr.token.literal, value)

    def _test_boolean_literal(self, expr: ast.Expression, value: str) -> None:
        self.assertIsInstance(expr, ast.Boolean)
        self.assertEqual(expr.value, value)

        # Monkey and Python boolean literals differ
        if value:
            self.assertEqual(expr.token_literal(), "true")
        else:
            self.assertEqual(expr.token_literal(), "false")

    def _test_literal_expression(self, expr: ast.Expression, expected: any) -> None:
        # TODO: Why does converting to isinstance fail comparisons?
        if type(expected) == int:
            self._test_integer_literal(expr, expected)
        elif type(expected) == str:
            self._test_identifier(expr, expected)
        elif type(expected) == bool:
            self._test_boolean_literal(expr, expected)
        else:
            self.fail(f"type of expr not handled. Got {type(expected)}")

    def _test_infix_expression(self, expr: ast.Expression, left: any, operator: str, right: any) -> None:
        self.assertIsInstance(expr, ast.InfixExpression)
        self._test_literal_expression(expr.left, left)
        self.assertEqual(expr.operator, operator)
        self._test_literal_expression(expr.right, right)

    def test_parsing_infix_expressions(self):
        Case = namedtuple(
            "Case", ["input", "left_value", "operator", "right_value"])
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
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            self.assertEqual(len(program.statements), 1)
            stmt = program.statements[0].expression
            self._test_infix_expression(
                stmt, test.left_value, test.operator, test.right_value)

    def test_operator_precedence_parsing(self):
        Case = namedtuple("Case", ["input", "expected"])
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
            Case("add(a * b[2], b[1], 2 * [1, 2][1])", "add((a * (b[2])), (b[1]), (2 * ([1, 2][1])))")]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            # not self.assertEqual(len(program.statements), 1) as one test
            # consists of two statements.
            self._check_parser_errors(parser)
            actual = program.string()
            self.assertEqual(actual, test.expected)

    def test_bool_expressions(self):
        Case = namedtuple("Case", ["input", "expected"])
        tests = [
            Case("true", "true"),
            Case("false", "false")]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            actual = program.string()
            self.assertEqual(actual, test.expected)

    def test_if_expression(self):
        source = "if (x < y) { x }"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        self.assertEqual(len(program.statements), 1)
        expr = program.statements[0].expression
        self.assertIsInstance(expr, ast.IfExpression)
        self._test_infix_expression(expr.condition, "x", "<", "y")
        self.assertEqual(len(expr.consequence.statements), 1)
        consequence = expr.consequence.statements[0]
        self.assertIsInstance(consequence, ast.ExpressionStatement)
        self._test_identifier(consequence.expression, "x")
        self.assertEqual(expr.alternative, None)

    def test_if_else_expression(self):
        source = "if (x < y) { x } else { y }"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        self.assertEqual(len(program.statements), 1)
        expr = program.statements[0].expression
        self.assertIsInstance(expr, ast.IfExpression)
        self._test_infix_expression(expr.condition, "x", "<", "y")
        self.assertEqual(len(expr.consequence.statements), 1)
        consequence = expr.consequence.statements[0]
        self.assertIsInstance(consequence, ast.ExpressionStatement)
        self._test_identifier(consequence.expression, "x")
        self.assertEqual(len(expr.alternative.statements), 1)
        alternative = expr.alternative.statements[0]
        self.assertIsInstance(alternative, ast.ExpressionStatement)
        self._test_identifier(alternative.expression, "y")

    def test_function_literal_parsing(self):
        source = "fn(x, y) { x + y; }"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        function = stmt.expression
        self.assertIsInstance(function, ast.FunctionLiteral)
        self.assertEqual(len(function.parameters), 2)
        self._test_literal_expression(function.parameters[0], "x")
        self._test_literal_expression(function.parameters[1], "y")
        self.assertEqual(len(function.body.statements), 1)
        body_stmt = function.body.statements[0]
        self.assertIsInstance(body_stmt, ast.ExpressionStatement)
        self._test_infix_expression(body_stmt.expression, "x", "+", "y")

    def test_function_parameter_parsing(self):
        Case = namedtuple("Case", ["input", "expected_params"])
        tests = [
            Case("fn() {};", []),
            Case("fn(x) {};", ["x"]),
            Case("fn(x, y, z) {};", ["x", "y", "z"])]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            stmt = program.statements[0]
            self.assertIsInstance(stmt, ast.ExpressionStatement)
            function = stmt.expression
            self.assertIsInstance(function, ast.FunctionLiteral)
            self.assertEqual(len(test.expected_params),
                             len(function.parameters))
            for i, ident in enumerate(test.expected_params):
                self._test_literal_expression(function.parameters[i], ident)

    def test_call_expression_parsing(self):
        source = "add(1, 2 * 3, 4 + 5);"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        expr = stmt.expression
        self.assertIsInstance(expr, ast.CallExpression)
        self._test_identifier(expr.function, "add")
        self.assertEqual(len(expr.arguments), 3)
        self._test_literal_expression(expr.arguments[0], 1)
        self._test_infix_expression(expr.arguments[1], 2, "*", 3)
        self._test_infix_expression(expr.arguments[2], 4, "+", 5)

    def test_call_expression_parameter_parsing(self):
        Case = namedtuple("Case", ["input", "expected_ident", "expected_args"])
        tests = [
            Case("add();", "add", []),
            Case("add(1);", "add", [1]),
            Case("add(1, 2 * 3, 4 + 5);", "add", ["1", "(2 * 3)", "(4 + 5)"])]

        for test in tests:
            lexer = Lexer(test.input)
            parser = Parser(lexer)
            program = parser.parse_program()
            self._check_parser_errors(parser)
            self.assertEqual(len(program.statements), 1)
            stmt = program.statements[0]
            self.assertIsInstance(stmt, ast.ExpressionStatement)
            expr = stmt.expression
            self.assertIsInstance(expr, ast.CallExpression)
            self._test_identifier(expr.function, test.expected_ident)
            self.assertEqual(len(expr.arguments), len(test.expected_args))
            for i, arg in enumerate(test.expected_args):
                self.assertEqual(arg, test.expected_args[i])

    def test_string_literal_expression(self):
        source = '"Hello world"'
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        literal = stmt.expression
        self.assertIsInstance(literal, ast.StringLiteral)
        self.assertEqual(literal.value, "Hello world")

    def test_parsing_array_literals(self):
        source = "[1, 2 * 2, 3 + 3]"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        array = stmt.expression
        self.assertIsInstance(array, ast.ArrayLiteral)
        self.assertEqual(len(array.elements), 3)
        self._test_integer_literal(array.elements[0], 1)
        self._test_infix_expression(array.elements[1], 2, "*", 2)
        self._test_infix_expression(array.elements[2], 3, "+", 3)

    def test_parsing_index_expression(self):
        source = "myArray[1 + 1]"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        index_expr = stmt.expression
        self.assertIsInstance(index_expr, ast.IndexExpression)
        self._test_identifier(index_expr.left, "myArray")
        self._test_infix_expression(index_expr.index, 1, "+", 1)

    def test_parsing_hash_literals_string_keys(self):
        source = '{"one": 1, "two": 2, "three": 3}'
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        hash_literal = stmt.expression
        self.assertIsInstance(hash_literal, ast.HashLiteral)
        self.assertEqual(len(hash_literal.pairs), 3)
        expected = {
            "one": 1,
            "two": 2,
            "three": 3
        }
        for key, value in hash_literal.pairs.items():
            self.assertIsInstance(key, ast.StringLiteral)
            expected_value = expected[key.string()]
            self._test_integer_literal(value, expected_value)

    def test_parsing_empty_hash_literal(self):
        source = "{}"
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        hash_literal = stmt.expression
        self.assertIsInstance(hash_literal, ast.HashLiteral)
        self.assertEqual(len(hash_literal.pairs), 0)

    # TODO: verify with parser_test.go that we include all TestParserHash tests

    def test_parsing_hash_literals_with_expressions(self):
        source = '{"one": 0 + 1, "two": 10 - 8, "three": 15 / 5}'
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        self._check_parser_errors(parser)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.ExpressionStatement)
        hash_literal = stmt.expression
        self.assertIsInstance(hash_literal, ast.HashLiteral)
        self.assertEqual(len(hash_literal.pairs), 3)
        expected = {
            "one": lambda e: self._test_infix_expression(e, 0, "+", 1),
            "two": lambda e: self._test_infix_expression(e, 10, "-", 8),
            "three": lambda e: self._test_infix_expression(e, 15, "/", 5)
        }
        for key, value in hash_literal.pairs.items():
            self.assertIsInstance(key, ast.StringLiteral)
            expected[key.string()](value)
