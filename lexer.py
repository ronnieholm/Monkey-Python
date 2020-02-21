from enum import Enum, unique
from typing import Dict, Optional

@unique
class TokenType(Enum):
    ILLEGAL = "ILLEGAL" # Unknown token/character
    EOF = "EOF"         # Signals parser to stop requesting tokens

    # Identifiers and literals
    IDENT = "IDENT"   # add, foobar, x, y, ...
    INT = "INT"       # 123
    STRING = "STRING" # "foo"

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
    def __init__(self, type: TokenType, literal: str):
        self.type_ = type
        self.literal = literal

class Lexer:
    def __init__(self, input: str):
        self._input = input
        self._position = 0       # current character position in input
        self._read_position = 0  # next character position for lookahead
        self._char: str = ""
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
        elif self._char == "+": tok = Token(TokenType.PLUS, self._char)
        elif self._char == "-": tok = Token(TokenType.MINUS, self._char)
        elif self._char == "!": 
            if self._peek_char() == "=":
                char = self._char
                self._read_char()
                tok = Token(TokenType.NOT_EQ, char + self._char)
            else:
                tok = Token(TokenType.BANG, self._char)
        elif self._char == "*": tok = Token(TokenType.ASTERISK, self._char)
        elif self._char == "/": tok = Token(TokenType.SLASH, self._char)
        elif self._char == "<": tok = Token(TokenType.LT, self._char)
        elif self._char == ">": tok = Token(TokenType.GT, self._char)
        elif self._char == ",": tok = Token(TokenType.COMMA, self._char)
        elif self._char == ";": tok = Token(TokenType.SEMICOLON, self._char)
        elif self._char == "(": tok = Token(TokenType.LPAREN, self._char)
        elif self._char == ")": tok = Token(TokenType.RPAREN, self._char)
        elif self._char == "{": tok = Token(TokenType.LBRACE, self._char)
        elif self._char == "}": tok = Token(TokenType.RBRACE, self._char)
        elif self._char == "[": tok = Token(TokenType.LBRACKET, self._char)
        elif self._char == "]": tok = Token(TokenType.RBRACKET, self._char)
        elif self._char == ":": tok = Token(TokenType.COLON, self._char)
        elif self._char == '"':
            tok = Token(TokenType.STRING, self._read_string())
        elif self._char == "\0": tok = Token(TokenType.EOF, "")
        else:
            if self._is_letter(self._char):
                literal = self._read_identifier()
                type_ = Lexer._lookup_ident(literal)

                # Early return is necessary because when calling
                # _read_identifier() it calls _read_character() repeatedly,
                # advancing _read_position and _position past the last character
                # of the current identifier. So no need to call next_token again
                # after switching on character.
                return Token(type_, literal)
            elif self._is_digit(self._char):
                literal = self._read_number()
                return Token(TokenType.INT, literal)
            else:
                tok = Token(TokenType.ILLEGAL, self._char)

        self._read_char()
        return tok

    def _skip_whitespace(self) -> None:
        while self._char == " " or self._char == "\t" or self._char == "\n" or self._char == "\r":
            self._read_char()

    def _read_char(self) -> None:
        if self._read_position >= len(self._input):
            self._char = "\0"
        else:
            self._char = self._input[self._read_position]
        
        self._position = self._read_position
        self._read_position += 1

    def _read_string(self) -> str:
        position = self._position + 1
        while True:
            self._read_char()
            if self._char == '"':
                break
        return self._input[position:self._position]

    def _read_number(self) -> str:
        position = self._position
        while self._is_digit(self._char):
            self._read_char()
        return self._input[position:self._position]

    def _read_identifier(self) -> str:
        position = self._position
        while self._is_letter(self._char):
            self._read_char()
        return self._input[position:self._position]

    def _is_letter(self, char: str) -> bool:
        return "a" <= char and char <= "z" or "A" <= char and char <= "Z" or char == "_"

    def _is_digit(self, char: str) -> bool:
        return "0" <= char and char <= "9"

    def _peek_char(self) -> Optional[str]:
        if self._read_position >= len(self._input):
            return None
        else:
            return self._input[self._read_position]

    # TODO: Move keyeowds and _lookup_ident to token.py?
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
        else: 
            return TokenType.IDENT