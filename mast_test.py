import unittest
from mast import Program, LetStatement, Identifier
from lexer import Token, TokenType


class AstTest(unittest.TestCase):
    def test_string(self) -> None:
        program = Program([
            LetStatement(
                Token(TokenType.LET, "let"),
                Identifier(Token(TokenType.IDENT, "myVar"), "myVar"),
                Identifier(Token(TokenType.IDENT, "anotherVar"), "anotherVar"))])
        self.assertEqual(program.string(), "let myVar = anotherVar;")
