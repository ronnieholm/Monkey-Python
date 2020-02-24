import unittest
from collections import namedtuple
from lexer import Lexer, TokenType


class LexerTest(unittest.TestCase):
    def test_next_token(self):
        source = """let five = 5;
                    let ten = 10;
                    
                    let add = fn(x, y) {
                      x + y;
                    };
                    
                    let result = add(five, ten);
                    !-/*5;
                    5 < 10 > 5;
                    
                    if (5 < 10) {
                    	return true;
                    } else {
                    	return false;
                    }
                    
                    10 == 10;
                    10 != 9;
                    "foobar"
                    "foo bar"
                    [1, 2];
                    {"foo": "bar"}"""
        Case = namedtuple(
            "Case", ["expected_token_type", "expected_token_literal"])
        tests = [
            Case(TokenType.LET, "let"),
            Case(TokenType.IDENT, "five"),
            Case(TokenType.ASSIGN, "="),
            Case(TokenType.INT, "5"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.LET, "let"),
            Case(TokenType.IDENT, "ten"),
            Case(TokenType.ASSIGN, "="),
            Case(TokenType.INT, "10"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.LET, "let"),
            Case(TokenType.IDENT, "add"),
            Case(TokenType.ASSIGN, "="),
            Case(TokenType.FUNCTION, "fn"),
            Case(TokenType.LPAREN, "("),
            Case(TokenType.IDENT, "x"),
            Case(TokenType.COMMA, ","),
            Case(TokenType.IDENT, "y"),
            Case(TokenType.RPAREN, ")"),
            Case(TokenType.LBRACE, "{"),
            Case(TokenType.IDENT, "x"),
            Case(TokenType.PLUS, "+"),
            Case(TokenType.IDENT, "y"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.RBRACE, "}"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.LET, "let"),
            Case(TokenType.IDENT, "result"),
            Case(TokenType.ASSIGN, "="),
            Case(TokenType.IDENT, "add"),
            Case(TokenType.LPAREN, "("),
            Case(TokenType.IDENT, "five"),
            Case(TokenType.COMMA, ","),
            Case(TokenType.IDENT, "ten"),
            Case(TokenType.RPAREN, ")"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.BANG, "!"),
            Case(TokenType.MINUS, "-"),
            Case(TokenType.SLASH, "/"),
            Case(TokenType.ASTERISK, "*"),
            Case(TokenType.INT, "5"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.INT, "5"),
            Case(TokenType.LT, "<"),
            Case(TokenType.INT, "10"),
            Case(TokenType.GT, ">"),
            Case(TokenType.INT, "5"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.IF, "if"),
            Case(TokenType.LPAREN, "("),
            Case(TokenType.INT, "5"),
            Case(TokenType.LT, "<"),
            Case(TokenType.INT, "10"),
            Case(TokenType.RPAREN, ")"),
            Case(TokenType.LBRACE, "{"),
            Case(TokenType.RETURN, "return"),
            Case(TokenType.TRUE, "true"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.RBRACE, "}"),
            Case(TokenType.ELSE, "else"),
            Case(TokenType.LBRACE, "{"),
            Case(TokenType.RETURN, "return"),
            Case(TokenType.FALSE, "false"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.RBRACE, "}"),
            Case(TokenType.INT, "10"),
            Case(TokenType.EQ, "=="),
            Case(TokenType.INT, "10"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.INT, "10"),
            Case(TokenType.NOT_EQ, "!="),
            Case(TokenType.INT, "9"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.STRING, "foobar"),
            Case(TokenType.STRING, "foo bar"),
            Case(TokenType.LBRACKET, "["),
            Case(TokenType.INT, "1"),
            Case(TokenType.COMMA, ","),
            Case(TokenType.INT, "2"),
            Case(TokenType.RBRACKET, "]"),
            Case(TokenType.SEMICOLON, ";"),
            Case(TokenType.LBRACE, "{"),
            Case(TokenType.STRING, "foo"),
            Case(TokenType.COLON, ":"),
            Case(TokenType.STRING, "bar"),
            Case(TokenType.RBRACE, "}"),
            Case(TokenType.EOF, "")]

        lexer = Lexer(source)
        for test in tests:
            token_ = lexer.next_token()
            self.assertEqual(token_.type_, test.expected_token_type)
            self.assertEqual(token_.literal, test.expected_token_literal)
