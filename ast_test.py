import unittest
from lexer import Token, TokenType
from ast import Program, LetStatement, Identifier

class AstTest(unittest.TestCase):
    def test_string(self):
        program = Program(statements = [
            LetStatement(
                token = Token(type = TokenType.LET, literal = "let"),
                name = Identifier(
                    token = Token(type = TokenType.IDENT, literal = "myVar"),
                    value = "myVar"
                ),
                value = Identifier(
                    token = Token(type = TokenType.IDENT, literal = "anotherVar"),
                    value = "anotherVar" 
                )
            )
        ] )

        self.assertEqual(program.string(), "let myVar = anotherVar;")