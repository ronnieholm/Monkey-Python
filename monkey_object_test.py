import unittest
import monkey_object


class MonkeyObjectTests(unittest.TestCase):
    def test_string_hash_key(self) -> None:
        hello1 = monkey_object.String("Hello World")
        hello2 = monkey_object.String("Hello World")
        diff1 = monkey_object.String("My name is johnny")
        diff2 = monkey_object.String("My name is johnny")
        self.assertEqual(hello1.hash_key(), hello2.hash_key())
        self.assertEqual(diff1.hash_key(), diff2.hash_key())

    def test_boolean_hash_key(self) -> None:
        hello1 = monkey_object.Boolean(True)
        hello2 = monkey_object.Boolean(True)
        diff1 = monkey_object.Boolean(False)
        diff2 = monkey_object.Boolean(False)
        self.assertEqual(hello1.hash_key(), hello2.hash_key())
        self.assertEqual(diff1.hash_key(), diff2.hash_key())

    def test_integer_hash_key(self) -> None:
        hello1 = monkey_object.Integer(1)
        hello2 = monkey_object.Integer(1)
        diff1 = monkey_object.Integer(2)
        diff2 = monkey_object.Integer(2)
        self.assertEqual(hello1.hash_key(), hello2.hash_key())
        self.assertEqual(diff1.hash_key(), diff2.hash_key())
