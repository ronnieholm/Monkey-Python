import unittest
from collections import namedtuple
from typing import Dict
from parser import Parser
from lexer import Lexer
import monkey_object
import environment
from evaluator import Evaluator

Case = namedtuple("Case", ["input", "expected"])


class LexerTest(unittest.TestCase):
    def test_eval_integer_expression(self):
        tests = [
            Case("5", 5),
            Case("10", 10),
            Case("-5", -5),
            Case("-10", -10),
            Case("5 + 5 + 5 + 5 - 10", 10),
            Case("2 * 2 * 2 * 2 * 2", 32),
            Case("-50 + 100 + -50", 0),
            Case("5 * 2 + 10", 20),
            Case("5 + 2 * 10", 25),
            Case("20 + 2 * -10", 0),
            Case("50 / 2 * 2 + 10", 60),
            Case("2 * (5 + 10)", 30),
            Case("3 * 3 * 3 + 10", 37),
            Case("3 * (3 * 3) + 10", 37),
            Case("(5 + 10 * 2 + 15 / 3) * 2 + -10", 50)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            self._test_integer_object(evaluated, test.expected)

    def _test_eval(self, source: str) -> monkey_object.MonkeyObject:
        lexer = Lexer(source)
        parser = Parser(lexer)
        evaluator = Evaluator()
        program = parser.parse_program()
        env = environment.Environment()
        return evaluator.eval(program, env)

    def _test_integer_object(self, obj: monkey_object.MonkeyObject, expected: int) -> None:
        self.assertIsInstance(obj, monkey_object.Integer)
        self.assertEqual(obj.value, expected)

    def test_eval_boolean_expression(self):
        tests = [
            Case("true", True),
            Case("false", False),
            Case("1 < 2", True),
            Case("1 > 2", False),
            Case("1 < 1", False),
            Case("1 > 1", False),
            Case("1 == 1", True),
            Case("1 != 1", False),
            Case("1 == 2", False),
            Case("1 != 2", True),
            Case("true == true", True),
            Case("false == false", True),
            Case("true == false", False),
            Case("true != false", True),
            Case("false != true", True),
            Case("(1 < 2) == true", True),
            Case("(1 < 2) == false", False),
            Case("(1 > 2) == true", False),
            Case("(1 > 2) == false", True)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            self._test_boolean_object(evaluated, test.expected)

    def _test_boolean_object(self, obj: monkey_object.Boolean, expected: bool) -> None:
        self.assertIsInstance(obj, monkey_object.Boolean)
        self.assertEqual(obj.value, expected)

    def test_bang_operator(self):
        tests = [
            Case("!true", False),
            Case("!false", True),
            Case("!5", False),
            Case("!!true", True),
            Case("!!false", False),
            Case("!!5", True)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            self._test_boolean_object(evaluated, test.expected)

    def test_if_else_expression(self) -> None:
        tests = [
            Case("if (true) { 10 }", 10),
            Case("if (false) { 10 }", None),
            Case("if (1) { 10 }", 10),
            Case("if (1 < 2) { 10 }", 10),
            Case("if (1 > 2) { 10 }", None)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            if isinstance(evaluated, monkey_object.Integer):
                self._test_integer_object(evaluated, test.expected)
            else:
                self._test_null_object(evaluated)

    def _test_null_object(self, obj: monkey_object.MonkeyObject) -> None:
        self.assertEqual(obj, Evaluator.null)

    def test_return_statement(self) -> None:
        tests = [
            Case("return 10;", 10),
            Case("return 10; 9;", 10),
            Case("return 2 * 5; 9;", 10),
            Case("9; return 2 * 5; 9;", 10),
            Case("""if (10 > 1) {
                      if (10 > 1) {
                        return 10;
                      }
                      return 1;
                    }""", 10),
            Case("""if (10 > 1) {
                     if (10 > 1) {
                       return 10;
                     }
                     return 1;
                   }""", 10),
            Case("""let f = fn(x) {
                     return x;
                     x + 10;
                   };
                   f(10);""", 10),
            Case("""let f = fn(x) {
                     let result = x + 10;
                     return result;
                     return 10;
                   };
                   f(10);""", 20)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            self._test_integer_object(evaluated, test.expected)

    def test_error_handling(self) -> None:
        tests = [
            Case("5 + true;", "type mismatch: INTEGER + BOOLEAN"),
            Case("5 + true; 5;", "type mismatch: INTEGER + BOOLEAN"),
            Case("-true", "unknown operator: -BOOLEAN"),
            Case("true + false;", "unknown operator: BOOLEAN + BOOLEAN"),
            Case("5; true + false; 5", "unknown operator: BOOLEAN + BOOLEAN"),
            Case("if (10 > 1) { true + false; }",
                 "unknown operator: BOOLEAN + BOOLEAN"),
            Case("""if (10 > 1) {
                      if (10 > 1) {
                        return true + false;
                      }
                      return 1;
                    }""", "unknown operator: BOOLEAN + BOOLEAN"),
            Case("foobar", "identifier not found: foobar"),
            Case('"Hello" - "World"', "unknown operator: STRING - STRING"),
            Case('{"name": "Monkey"}[fn(x) { x }];', "unusable as hash key: FUNCTION")]
        for test in tests:
            evaluated = self._test_eval(test.input)
            self.assertIsInstance(evaluated, monkey_object.Error)
            self.assertEqual(evaluated.message, test.expected)

    def test_let_statements(self) -> None:
        tests = [
            Case("let a = 5; a;", 5),
            Case("let a = 5 * 5; a;", 25),
            Case("let a = 5; let b = a; b;", 5),
            Case("let a = 5; let b = a; let c = a + b + 5; c;", 15)]
        for test in tests:
            self._test_integer_object(
                self._test_eval(test.input), test.expected)

    def test_function_object(self) -> None:
        source = "fn(x) { x + 2; };"
        evaluated = self._test_eval(source)
        self.assertIsInstance(evaluated, monkey_object.Function)
        self.assertEqual(len(evaluated.parameters), 1)
        self.assertEqual(evaluated.parameters[0].string(), "x")
        expected_body = "(x + 2)"
        self.assertEqual(evaluated.body.string(), expected_body)

    def test_function_application(self) -> None:
        tests = [
            Case("let identity = fn(x) { x; }; identity(5);", 5),
            Case("let identity = fn(x) { return x; }; identity(5);", 5),
            Case("let double = fn(x) { x * 2; }; double(5);", 10),
            Case("let add = fn(x, y) { x + y; }; add(5, 5);", 10),
            Case("let add = fn(x, y) { x + y; }; add(5 + 5, add(5, 5));", 20),
            Case("fn(x) { x; }(5)", 5)]
        for test in tests:
            self._test_integer_object(
                self._test_eval(test.input), test.expected)

    def test_closures(self):
        source = """let newAdder = fn(x) {
                     fn(y) { x + y };
                    };
                    let addTwo = newAdder(2);
                    addTwo(2);"""
        self._test_integer_object(self._test_eval(source), 4)

    def test_string_literal(self):
        source = '"Hello world"'
        evaluated = self._test_eval(source)
        self.assertIsInstance(evaluated, monkey_object.String)
        self.assertEqual(evaluated.value, "Hello world")

    def test_string_concatenation(self):
        source = '"Hello" + " " + "World!"'
        evaluated = self._test_eval(source)
        self.assertIsInstance(evaluated, monkey_object.String)
        self.assertEqual(evaluated.value, "Hello World!")

    def test_builtin_functions(self):
        tests = [
            Case('len("")', 0),
            Case('len("four")', 4),
            Case('len("hello world")', 11),
            Case('len(1)', "argument to 'len' not supported. Got INTEGER"),
            Case('len("one", "two")', "wrong number of arguments. Got 2, want 1"),
            Case('len([1, 2, 3])', 3),
            Case('len([])', 0),
            # Don't print to stdout when running tests
            #Case('puts("hello", "world!")', None),
            Case('first([1, 2, 3])', 1),
            Case('first([])', None),
            Case('first(1)', "argument to 'first' must be ARRAY. Got INTEGER"),
            Case('last([1, 2, 3])', 3),
            Case('last([])', None),
            Case('last(1)', "argument to 'last' must be ARRAY. Got INTEGER"),
            Case('rest([1, 2, 3])', [2, 3]),
            Case('rest([])', None),
            Case('push([], 1)', [1]),
            Case('push(1, 1)', "argument to 'push' must be ARRAY. Got INTEGER")]
        for test in tests:
            evaluated = self._test_eval(test.input)
            if isinstance(test.expected, int):
                self._test_integer_object(evaluated, test.expected)
            elif isinstance(test.expected, str):
                self.assertIsInstance(evaluated, monkey_object.Error)
                self.assertEqual(evaluated.message, test.expected)
            elif isinstance(test.expected, list):
                self.assertIsInstance(evaluated, monkey_object.Array)
                self.assertEqual(len(evaluated.elements), len(test.expected))
                for i, expected_element in enumerate(test.expected):
                    self._test_integer_object(
                        evaluated.elements[i], expected_element)
            elif test.expected is None:
                self._test_null_object(evaluated)
            else:
                raise NotImplementedError

    def test_array_literals(self):
        source = "[1, 2 * 2, 3 + 3]"
        evaluated = self._test_eval(source)
        self.assertIsInstance(evaluated, monkey_object.Array)
        self.assertEqual(len(evaluated.elements), 3)
        self._test_integer_object(evaluated.elements[0], 1)
        self._test_integer_object(evaluated.elements[1], 4)
        self._test_integer_object(evaluated.elements[2], 6)

    def test_array_index_expressions(self):
        tests = [
            Case("[1, 2, 3][0]", 1),
            Case("[1, 2, 3][1]", 2),
            Case("[1, 2, 3][2]", 3),
            Case("let i = 0; [1][i];", 1),
            Case("[1, 2, 3][1 + 1];", 3),
            Case("let myArray = [1, 2, 3]; myArray[2];", 3),
            Case("let myArray = [1, 2, 3]; myArray[0] + myArray[1] + myArray[2];",
                 6),
            Case("let myArray = [1, 2, 3]; let i = myArray[0]; myArray[i]", 2),
            Case("[1, 2, 3][3]", None),
            Case("[1, 2, 3][-1]", None)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            if isinstance(test.expected, int):
                self._test_integer_object(evaluated, test.expected)
            else:
                self._test_null_object(evaluated)

    def test_hash_literals(self):
        source = """let two = "two";
                    {
                      "one": 10 - 9,
                      two: 1 + 1,
                      "thr" + "ee": 6 / 2,
                      4: 4,
                      true: 5,
                      false: 6
                    }"""
        evaluated = self._test_eval(source)
        self.assertIsInstance(evaluated, monkey_object.Hash)
        expected: Dict[monkey_object.HashKey, int] = {
            monkey_object.String("one").hash_key(): 1,
            monkey_object.String("two").hash_key(): 2,
            monkey_object.String("three").hash_key(): 3,
            monkey_object.Integer(4).hash_key(): 4,
            Evaluator.true.hash_key(): 5,
            Evaluator.false.hash_key(): 6
        }
        self.assertEqual(len(evaluated.pairs), len(expected))
        for key, value in expected.items():
            pair = evaluated.pairs[key]
            self._test_integer_object(pair.value, value)

    def test_hash_index_expressions(self):
        tests = [
            Case('{"foo": 5}["foo"]', 5),
            Case('{"foo": 5}["bar"]', None),
            Case('let key = "foo"; {"foo": 5}[key]', 5),
            Case('{}["foo"]', None),
            Case('{5: 5}[5]', 5),
            Case('{true: 5}[true]', 5),
            Case('{false: 5}[false]', 5)]
        for test in tests:
            evaluated = self._test_eval(test.input)
            if isinstance(test.expected, int):
                self._test_integer_object(evaluated, test.expected)
            else:
                self._test_null_object(evaluated)
