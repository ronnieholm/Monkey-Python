from enum import Enum, unique
from typing import Dict, Optional


@unique
class TokenType(Enum):
    ILLEGAL = "ILLEGAL"  # Unknown token/character
    EOF = "EOF"          # End of File stops parsing

    # Identifiers and literals
    IDENT = "IDENT"      # add, foobar, x, y
    INT = "INT"          # 123
    STRING = "STRING"    # "foo"

    # Operators
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    BANG = "!"
    ASTERISK = "*"
    SLASH = "/"
    LT = "<"
    GT = ">"
    EQ = "=="
    NOT_EQ = "!="

    # Delimiters
    COMMA = ","
    SEMICOLON = ";"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    COLON = ":"

    # Keywords
    FUNCTION = "FUNCTION"
    LET = "LET"
    TRUE = "TRUE"
    FALSE = "FALSE"
    IF = "IF"
    ELSE = "ELSE"
    RETURN = "RETURN"


class Token:
    def __init__(self, type_: TokenType, literal: str) -> None:
        self.type_ = type_
        self.literal = literal


class Lexer:
    def __init__(self, source: str) -> None:
        self._source = source
        self._position = 0       # Where last character was read
        self._read_position = 0  # Where next character is read
        self._char: str = ""     # Character under examination
        self._read_char()

    def next_token(self) -> Token:
        self._skip_whitespace()

        if self._char == "=":
            if self._peek_char() == "=":
                char = self._char
                self._read_char()
                tok = Token(TokenType.EQ, char + self._char)
            else:
                tok = Token(TokenType.ASSIGN, self._char)
        elif self._char == "+":
            tok = Token(TokenType.PLUS, self._char)
        elif self._char == "-":
            tok = Token(TokenType.MINUS, self._char)
        elif self._char == "!":
            if self._peek_char() == "=":
                char = self._char
                self._read_char()
                tok = Token(TokenType.NOT_EQ, char + self._char)
            else:
                tok = Token(TokenType.BANG, self._char)
        elif self._char == "*":
            tok = Token(TokenType.ASTERISK, self._char)
        elif self._char == "/":
            tok = Token(TokenType.SLASH, self._char)
        elif self._char == "<":
            tok = Token(TokenType.LT, self._char)
        elif self._char == ">":
            tok = Token(TokenType.GT, self._char)
        elif self._char == ",":
            tok = Token(TokenType.COMMA, self._char)
        elif self._char == ";":
            tok = Token(TokenType.SEMICOLON, self._char)
        elif self._char == "(":
            tok = Token(TokenType.LPAREN, self._char)
        elif self._char == ")":
            tok = Token(TokenType.RPAREN, self._char)
        elif self._char == "{":
            tok = Token(TokenType.LBRACE, self._char)
        elif self._char == "}":
            tok = Token(TokenType.RBRACE, self._char)
        elif self._char == "[":
            tok = Token(TokenType.LBRACKET, self._char)
        elif self._char == "]":
            tok = Token(TokenType.RBRACKET, self._char)
        elif self._char == ":":
            tok = Token(TokenType.COLON, self._char)
        elif self._char == '"':
            tok = Token(TokenType.STRING, self._read_string())
        elif self._char == "\0":
            tok = Token(TokenType.EOF, "")
        else:
            if self._is_letter(self._char):
                literal = self._read_identifier()
                type_ = Lexer._lookup_ident(literal)
                return Token(type_, literal)
            if self._is_digit(self._char):
                literal = self._read_number()
                return Token(TokenType.INT, literal)
            tok = Token(TokenType.ILLEGAL, self._char)

        self._read_char()
        return tok

    def _skip_whitespace(self) -> None:
        while self._char in (' ', '\t', '\n', '\r'):
            self._read_char()

    def _read_char(self) -> None:
        if self._read_position >= len(self._source):
            self._char = "\0"
        else:
            self._char = self._source[self._read_position]

        self._position = self._read_position
        self._read_position += 1

    def _read_string(self) -> str:
        position = self._position + 1

        # BUG: Passing a string which isn't " terminated causes an infinite loop
        # because even though we reached the end of source, the " characters
        # hasn't been reached.
        while True:
            self._read_char()
            if self._char == '"':
                break
        return self._source[position:self._position]

    def _read_number(self) -> str:
        position = self._position
        while self._is_digit(self._char):
            self._read_char()
        return self._source[position:self._position]

    def _read_identifier(self) -> str:
        position = self._position
        while self._is_letter(self._char):
            self._read_char()
        return self._source[position:self._position]

    def _is_letter(self, char: str) -> bool:
        return "a" <= char <= "z" or "A" <= char <= "Z" or char == "_"

    def _is_digit(self, char: str) -> bool:
        return "0" <= char <= "9"

    def _peek_char(self) -> Optional[str]:
        if self._read_position >= len(self._source):
            return None
        return self._source[self._read_position]

    keywords: Dict[str, TokenType] = {
        "fn": TokenType.FUNCTION,
        "let": TokenType.LET,
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "return": TokenType.RETURN
    }

    @staticmethod
    def _lookup_ident(ident: str) -> TokenType:
        if ident in Lexer.keywords:
            return Lexer.keywords[ident]
        return TokenType.IDENT
