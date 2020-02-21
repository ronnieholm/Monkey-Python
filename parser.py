from enum import Enum, unique
import ast
from lexer import Lexer, Token, TokenType
from typing import List, Callable, NewType, Dict, Union, Optional, Type

PrefixParseFn = NewType("PrefixParseFn", Callable[[], ast.Expression])
InfixParseFn = NewType("InfixParseFn", Callable[[ast.Expression], ast.Expression])

@unique
class Precedence_level(Enum):
    LOWEST = 0
    EQUALS = 1      # ==
    LESSGREATER = 2 # < or >
    SUM = 3         # +
    PRODUCT = 4     # *
    PREFIX = 5      # -x or !x
    CALL = 6        # myFunction(x)
    INDEX = 7       # array[index]

# TODO: probably should be lower cased
Precedence: dict = {
    TokenType.EQ: Precedence_level.EQUALS,
    TokenType.NOT_EQ: Precedence_level.EQUALS,
    TokenType.LT: Precedence_level.LESSGREATER,
    TokenType.GT: Precedence_level.LESSGREATER,
    TokenType.PLUS: Precedence_level.SUM,
    TokenType.MINUS: Precedence_level.SUM,
    TokenType.SLASH: Precedence_level.PRODUCT,
    TokenType.ASTERISK: Precedence_level.PRODUCT,
    TokenType.LPAREN: Precedence_level.CALL,
    TokenType.LBRACKET: Precedence_level.INDEX
}

class Parser:
    def __init__(self, lexer: Lexer):       
        self.errors: List[str] = []
        self._lexer = lexer
        self._current_token: Token # TODO: Do we need to create those here?
        self._peek_token: Token = None
        self._prefix_parse_fns: Dict[TokenType, PrefixParseFn] = {}
        self._infix_parse_fns: Dict[TokenType, InfixParseFn] = {}
        self._next_token()
        self._next_token()

        self._register_prefix(TokenType.IDENT, self._parse_identifier)
        self._register_prefix(TokenType.INT, self._parse_integer_literal)
        self._register_prefix(TokenType.BANG, self._parse_prefix_expression)
        self._register_prefix(TokenType.MINUS, self._parse_prefix_expression)
        self._register_prefix(TokenType.TRUE, self._parse_boolean)
        self._register_prefix(TokenType.FALSE, self._parse_boolean)
        self._register_prefix(TokenType.LPAREN, self._parse_group_expression)
        self._register_prefix(TokenType.IF, self._parse_if_expression)
        self._register_prefix(TokenType.FUNCTION, self._parse_function_literal)
        self._register_prefix(TokenType.STRING, self._parse_string_literal)
        self._register_prefix(TokenType.LBRACKET, self._parse_array_literal)
        self._register_prefix(TokenType.LBRACE, self._parse_hash_literal)

        self._register_infix(TokenType.PLUS, self._parse_infix_expression)
        self._register_infix(TokenType.MINUS, self._parse_infix_expression)
        self._register_infix(TokenType.SLASH, self._parse_infix_expression)
        self._register_infix(TokenType.ASTERISK, self._parse_infix_expression)
        self._register_infix(TokenType.EQ, self._parse_infix_expression)
        self._register_infix(TokenType.NOT_EQ, self._parse_infix_expression)
        self._register_infix(TokenType.LT, self._parse_infix_expression)
        self._register_infix(TokenType.GT, self._parse_infix_expression)
        self._register_infix(TokenType.LPAREN, self._parse_call_expression)
        self._register_infix(TokenType.LBRACKET, self._parse_index_expression)

    # TODO: Do we really need this function?
    def _register_prefix(self, type: TokenType, fn: PrefixParseFn) -> None:
        self._prefix_parse_fns[type] = fn

    # TODO: Do we really need this function?
    def _register_infix(self, type: TokenType, fn: InfixParseFn) -> None:
        self._infix_parse_fns[type] = fn

    def _next_token(self) -> None:
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def parse_program(self) -> ast.Program:
        program = ast.Program()

        while not self._current_token_is(TokenType.EOF):
            stmt = self._parse_statement()
            if stmt != None:
                program.statements.append(stmt)            
            self._next_token()
        
        return program

    def _parse_statement(self) -> Optional[Type[ast.Node]]:
        if self._current_token.type_ == TokenType.LET:
            return self._parse_let_statement()
        elif self._current_token.type_ == TokenType.RETURN:
            return self._parse_return_statement()
        else:
            return self._parse_expression_statement()

    def _parse_expression_statement(self) -> ast.ExpressionStatement:
        token = self._current_token
        expression = self._parse_expression(Precedence_level.LOWEST)
        if self._peek_token_is(TokenType.SEMICOLON):
            self._next_token()
        return ast.ExpressionStatement(token, expression)

    def _parse_expression(self, precedence: Precedence_level) -> Optional[ast.Expression]:
        t = self._current_token.type_
        if not t in self._prefix_parse_fns:
            self._no_prefix_parse_fn_error(self._current_token.type_)
            return None          
        leftExpr = self._prefix_parse_fns[t]()

        while not self._peek_token_is(TokenType.SEMICOLON) and precedence.value < self._peek_precedence().value:
            peek = self._peek_token.type_
            if not peek in self._infix_parse_fns:
                return leftExpr
            self._next_token()
            leftExpr = self._infix_parse_fns[peek](leftExpr)

        return leftExpr

    def _parse_identifier(self) -> ast.Identifier:
        return ast.Identifier(token = self._current_token, value = self._current_token.literal)

    def _parse_integer_literal(self) -> Optional[ast.Expression]:
        token = self._current_token
        try:
            value = int(token.literal)
        except ValueError:
            message = f"could not parse {token.literal} as integer"
            self.errors.append(message)
            return None
            
        return ast.IntegerLiteral(token, value)

    def _parse_string_literal(self) -> ast.Expression:
        return ast.StringLiteral(self._current_token, self._current_token.literal)

    def _parse_expression_list(self, end: TokenType) -> Optional[List[ast.Expression]]:
        list_ = []
        if self._peek_token_is(end):
            self._next_token()
            return list_
        self._next_token()
        list_.append(self._parse_expression(Precedence_level.LOWEST))

        while self._peek_token_is(TokenType.COMMA):
            self._next_token()
            self._next_token()
            list_.append(self._parse_expression(Precedence_level.LOWEST))

        if not self._expect_peek(end):
            return None

        return list_

    def _parse_array_literal(self) -> ast.Expression:
        token = self._current_token
        elements = self._parse_expression_list(TokenType.RBRACKET)
        return ast.ArrayLiteral(token, elements)

    def _parse_hash_literal(self) -> ast.Expression:
        token = self._current_token
        pairs: Dict[Type[ast.Expression], Type[ast.Expression]] = {}
        while not self._peek_token_is(TokenType.RBRACE):
            self._next_token()
            key = self._parse_expression(Precedence_level.LOWEST)
            if not self._expect_peek(TokenType.COLON):
                return None
            self._next_token()
            value = self._parse_expression(Precedence_level.LOWEST)
            pairs[key] = value
            if not self._peek_token_is(TokenType.RBRACE) and not self._expect_peek(TokenType.COMMA):
                return None
        if not self._expect_peek(TokenType.RBRACE):
            return None
        return ast.HashLiteral(token, pairs)

    def _parse_group_expression(self) -> Optional[ast.Expression]:
        self._next_token()
        expr = self._parse_expression(Precedence_level.LOWEST)
        if not self._expect_peek(TokenType.RPAREN):
            return None
        return expr

    def _parse_if_expression(self) -> Optional[ast.Expression]: # TODO: why not return If_expression?
        token = self._current_token
        if not self._expect_peek(TokenType.LPAREN):
            return None
        self._next_token()
        condition = self._parse_expression(Precedence_level.LOWEST)
        if not self._expect_peek(TokenType.RPAREN):
            return None
        if not self._expect_peek(TokenType.LBRACE):
            return None
        consequence = self._parse_block_statement()
        if self._peek_token_is(TokenType.ELSE):
            self._next_token()
            if not self._expect_peek(TokenType.LBRACE):
                return None
            alternative = self._parse_block_statement()
        else:
            alternative = None
        return ast.IfExpression(token, condition, consequence, alternative)        

    def _parse_block_statement(self) -> ast.BlockStatement:        
        token = self._current_token
        statements = []
        self._next_token()
        while not self._current_token_is(TokenType.RBRACE):
            stmt = self._parse_statement()
            if stmt != None:
                statements.append(stmt)
            self._next_token()
        return ast.BlockStatement(token, statements)

    def _parse_function_literal(self) -> Optional[ast.Expression]: # TODO: Why not Function_literal?
        token = self._current_token
        if not self._expect_peek(TokenType.LPAREN):
            return None
        parameters = self._parse_function_parameters()
        if not self._expect_peek(TokenType.LBRACE):
            return None
        body = self._parse_block_statement()
        return ast.FunctionLiteral(token, parameters, body)

    def _parse_function_parameters(self) -> Optional[List[ast.Identifier]]:
        identifiers = []
        if self._peek_token_is(TokenType.RPAREN):
            self._next_token()
            return identifiers
        self._next_token()
        ident = ast.Identifier(token = self._current_token, value = self._current_token.literal)
        identifiers.append(ident)
        while self._peek_token_is(TokenType.COMMA):
            self._next_token()
            self._next_token()
            ident = ast.Identifier(token = self._current_token, value = self._current_token.literal)
            identifiers.append(ident)       
        if not self._expect_peek(TokenType.RPAREN):
            return None
        return identifiers

    def _parse_call_expression(self, function: ast.Expression) -> ast.Expression:
        token = self._current_token
        arguments = self._parse_expression_list(TokenType.RPAREN)
        return ast.CallExpression(token, function, arguments)

    def _parse_index_expression(self, left: ast.Expression) -> ast.Expression:
        token = self._current_token
        self._next_token()
        index = self._parse_expression(Precedence_level.LOWEST)
        if not self._expect_peek(TokenType.RBRACKET):
            return None
        return ast.IndexExpression(token, left, index)

    def _parse_call_arguments(self) -> Optional[List[ast.Expression]]:
        args: List[ast.Expression] = []
        if self._peek_token_is(TokenType.RPAREN):
            self._next_token()
            return args
        self._next_token()
        args.append(self._parse_expression(Precedence_level.LOWEST))
        while self._peek_token_is(TokenType.COMMA):
            self._next_token()
            self._next_token()
            args.append(self._parse_expression(Precedence_level.LOWEST))
        if not self._expect_peek(TokenType.RPAREN):
            return None
        return args

    def _parse_prefix_expression(self) -> ast.Expression:
        token = self._current_token
        self._next_token()
        right = self._parse_expression(Precedence_level.PREFIX)        
        return ast.PrefixExpression(token, token.literal, right)

    def _parse_infix_expression(self, left: ast.Expression = None) -> ast.Expression:    
        token = self._current_token
        precedence = self._current_precedence()
        self._next_token()
        right = self._parse_expression(precedence)
        return ast.InfixExpression(token, left, token.literal, right)

    def _parse_let_statement(self) -> Optional[ast.LetStatement]:
        token = self._current_token
        if not self._expect_peek(TokenType.IDENT):
            return None        
        name = ast.Identifier(self._current_token, self._current_token.literal)
        if not self._expect_peek(TokenType.ASSIGN):
            return None
        self._next_token()
        value = self._parse_expression(Precedence_level.LOWEST)
        if self._peek_token_is(TokenType.SEMICOLON):
            self._next_token()
        return ast.LetStatement(token, name, value)

    def _parse_boolean(self) -> ast.Boolean:
        return ast.Boolean(self._current_token, value = self._current_token_is(TokenType.TRUE))

    def _parse_return_statement(self) -> ast.ReturnStatement:
        token = self._current_token
        self._next_token()
        return_value = self._parse_expression(Precedence_level.LOWEST)
        if self._peek_token_is(TokenType.SEMICOLON):
            self._next_token()
        return ast.ReturnStatement(token, return_value)

    def _current_token_is(self, t: TokenType) -> bool:
        return self._current_token.type_ == t

    def _peek_token_is(self, t: TokenType) -> bool:
        return self._peek_token.type_ == t

    def _expect_peek(self, t: TokenType) -> bool:
        if self._peek_token_is(t):
            self._next_token()
            return True
        else:
            self._peek_error(t)
            return False

    def _peek_error(self, t: TokenType) -> None:
        message = f"expected next token to be {t.value}. Got {self._peek_token.type_.value} instead"
        self.errors.append(message)
   
    def _no_prefix_parse_fn_error(self, t: TokenType) -> None:
        message = f"no prefix parse function for {t.value} found"
        self.errors.append(message)

    def _peek_precedence(self) -> Precedence_level:
        t = self._peek_token.type_
        if t in Precedence:
            return Precedence[t]
        return Precedence_level.LOWEST

    def _current_precedence(self) -> Precedence_level:
        t = self._current_token.type_
        if t in Precedence:
            return Precedence[t]
        return Precedence_level.LOWEST
  