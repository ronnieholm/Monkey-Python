import unittest
import object

class ObjectTests(unittest.TestCase):
    def test_string_hash_key(self):
        hello1 = object.String("Hello World")
        hello2 = object.String("Hello World")
        diff1 = object.String("My name is johnny")
        diff2 = object.String("My name is johnny")
        self.assertEqual(hello1.hash_key(), hello2.hash_key())
        self.assertEqual(diff1.hash_key(), diff2.hash_key())
    
    def test_boolean_hash_key(self):
        hello1 = object.Boolean(True)
        hello2 = object.Boolean(True)
        diff1 = object.Boolean(False)
        diff2 = object.Boolean(False)
        self.assertEqual(hello1.hash_key(), hello2.hash_key())
        self.assertEqual(diff1.hash_key(), diff2.hash_key())

    def test_integer_hash_key(self):
        hello1 = object.Integer(1)
        hello2 = object.Integer(1)
        diff1 = object.Integer(2)
        diff2 = object.Integer(2)
        self.assertEqual(hello1.hash_key(), hello2.hash_key())
        self.assertEqual(diff1.hash_key(), diff2.hash_key())
        
        
