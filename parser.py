from enum import Enum, unique
from typing import List, Callable, Dict, Optional, Union
import mast
from lexer import Lexer, Token, TokenType

# TIP: Setting a breakpoint in one of the parsing methods and inspecting the
# call stack when it's hit, effectively show the Abstract Syntax Tree at that
# point during parsing.


@unique
class PrecedenceLevel(Enum):
    # It's the relative and not absolute values of levels that matter. During
    # parsing we want to answer questions such as whether product has higher
    # precedence than equals.
    LOWEST = 0
    EQUALS = 1       # ==
    LESSGREATER = 2  # < or >
    SUM = 3          # +
    PRODUCT = 4      # *
    PREFIX = 5       # -x or !x
    CALL = 6         # myFunction(x)
    INDEX = 7        # array[index]


# Table of precedence to map token type to precedence level. Not every
# precedence level is present (Lowest and Prefix) and some precedence levels
# appear more than once (LessGreater, Sum, Product). Lowest serves as starting
# precedence for the Pratt parser while Prefix isn't associated with any token
# but an expression as a whole. On the other hand some operators such as
# multiplication and division share precedence level.
Precedence: dict = {
    TokenType.EQ: PrecedenceLevel.EQUALS,
    TokenType.NOT_EQ: PrecedenceLevel.EQUALS,
    TokenType.LT: PrecedenceLevel.LESSGREATER,
    TokenType.GT: PrecedenceLevel.LESSGREATER,
    TokenType.PLUS: PrecedenceLevel.SUM,
    TokenType.MINUS: PrecedenceLevel.SUM,
    TokenType.SLASH: PrecedenceLevel.PRODUCT,
    TokenType.ASTERISK: PrecedenceLevel.PRODUCT,
    TokenType.LPAREN: PrecedenceLevel.CALL,
    TokenType.LBRACKET: PrecedenceLevel.INDEX
}

PrefixParseFn = Callable[[], Optional[mast.Expression]]
InfixParseFn = Callable[[mast.Expression], Optional[mast.Expression]]


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.errors: List[str] = []
        self._lexer = lexer

        # Acts like _position and _peek_char within the lexer, but instead of
        # pointing to characters in the source they point to current and next
        # tokens. We need _current_token, the current token under examination,
        # to decide what to do next, and we need _peekToken to guide the
        # decision in case _current_token doesn't provide us with enough
        # information, e.g., with source "5;", _current_token is Int and we
        # require _peek_token to decide if we're at the end of the line or at
        # the start of an arithmetic expression. This implements a parser with
        # one token lookahead.
        #
        # We initialize both with a dummy token rather than define their type as
        # Optional[Token] which would cause lots of unnecessary changes to
        # satisfy the type checker. In practice, these tokens would only be None
        # between declaration and until the calls to _next_token().
        self._current_token: Token = Token(TokenType.ILLEGAL, "")
        self._peek_token: Token = Token(TokenType.ILLEGAL, "")

        # Functions based on token type called as part of Pratt parsing.
        self._prefix_parse_fns: Dict[TokenType, PrefixParseFn] = {}
        self._infix_parse_fns: Dict[TokenType, InfixParseFn] = {}

        # Read two tokens so _current_token and _peekToken tokens are both set.
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

    def _register_prefix(self, type_: TokenType, function: PrefixParseFn) -> None:
        self._prefix_parse_fns[type_] = function

    def _register_infix(self, type_: TokenType, function: InfixParseFn) -> None:
        self._infix_parse_fns[type_] = function

    def _next_token(self) -> None:
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def parse_program(self) -> mast.Program:
        stmts = []
        while not self._current_token_is(TokenType.EOF):
            stmt = self._parse_statement()

            # Many _parse_x() return null which bubbles up the call stack to
            # here where null enables continued parsing on error. The
            # alternative would be for _parse_x() to immediately stop parsing
            # and signal a parser error. But that wouldn't allow collecting
            # multiple errors to improve the user experience. Instead parsing
            # would halt on the first error. As an example, _expect_peek()
            # returns null if the expected token isn't found _and_ adds an error
            # message to the _errors list. That null bubbles up to
            # _parse_statement() which skips adding the statement to the AST and
            # moves on the next statement. Evaluation of the AST shouldn't be
            # attempted in case of parser errors as the faulting parts of the
            # program is missing from the AST, likely resulting in evaluation
            # errors.
            if stmt is not None:
                stmts.append(stmt)
            self._next_token()
        return mast.Program(stmts)

    def _parse_statement(self) -> Optional[Union[mast.Statement, mast.Expression]]:
        if self._current_token.type_ == TokenType.LET:
            return self._parse_let_statement()
        if self._current_token.type_ == TokenType.RETURN:
            return self._parse_return_statement()

        # The only two real statement types in Monkey are let and return. If
        # none of those got matched, try to parse source as a pseudo
        # ExpressionStatement.
        return self._parse_expression_statement()

    def _parse_let_statement(self) -> Optional[mast.LetStatement]:
        token = self._current_token
        if not self._expect_peek(TokenType.IDENT):
            return None
        name = mast.Identifier(self._current_token, self._current_token.literal)
        if not self._expect_peek(TokenType.ASSIGN):
            return None
        self._next_token()
        value = self._parse_expression(PrecedenceLevel.LOWEST)

        # Type checker would be satisfied if we added "assert value is not None"
        # following a call to a parser retuning Optional. assert, however,
        # terminates the program on None when what we want, whenever a
        # sub-parser such as _parse_expression() returns None, is to bubble up
        # None to _parse_program() so it can skip adding the statement to the
        # mast.
        if value is None:
            return None
        if self._peek_token_is(TokenType.SEMICOLON):
            self._next_token()
        return mast.LetStatement(token, name, value)

    def _parse_expression_statement(self) -> Optional[mast.ExpressionStatement]:
        token = self._current_token

        # Pass in lowest precedence level since we haven't parsed anything yet.
        expression = self._parse_expression(PrecedenceLevel.LOWEST)
        if expression is None:
            return None

        # Expression statements end with optional semicolon.
        if self._peek_token_is(TokenType.SEMICOLON):
            self._next_token()
        return mast.ExpressionStatement(token, expression)

    def _parse_expression(self, precedence: PrecedenceLevel) -> Optional[mast.Expression]:
        type_ = self._current_token.type_
        if not type_ in self._prefix_parse_fns:
            self._no_prefix_parse_fn_error(self._current_token.type_)
            return None
        left_expr = self._prefix_parse_fns[type_]()
        if left_expr is None:
            return None

        # precedence.value is what the Pratt paper refers to as right-binding
        # power and _peek_precedence is what it refers to as left-binding power.
        # For as long as left-binding power > right-binding power, add another
        # level to the Abstract Syntax Three, signifying operations which need
        # to be carried out first when the expression is evaluated.
        while not self._peek_token_is(TokenType.SEMICOLON) \
              and precedence.value < self._peek_precedence().value:
            peek = self._peek_token.type_
            if not peek in self._infix_parse_fns:
                return left_expr
            self._next_token()
            left_expr = self._infix_parse_fns[peek](left_expr)
            if left_expr is None:
                return None
        return left_expr

    def _parse_identifier(self) -> Optional[mast.Identifier]:
        return mast.Identifier(self._current_token, self._current_token.literal)

    def _parse_integer_literal(self) -> Optional[mast.IntegerLiteral]:
        token = self._current_token
        try:
            value = int(token.literal)
        except ValueError:
            message = f"could not parse {token.literal} as integer"
            self.errors.append(message)
            return None
        return mast.IntegerLiteral(token, value)

    def _parse_string_literal(self) -> mast.StringLiteral:
        return mast.StringLiteral(self._current_token, self._current_token.literal)

    def _parse_function_parameters(self) -> Optional[List[mast.Identifier]]:
        identifiers: List[mast.Identifier] = []
        if self._peek_token_is(TokenType.RPAREN):
            self._next_token()
            return identifiers
        self._next_token()
        ident = mast.Identifier(self._current_token,
                               self._current_token.literal)
        identifiers.append(ident)
        while self._peek_token_is(TokenType.COMMA):
            self._next_token()
            self._next_token()
            ident = mast.Identifier(self._current_token,
                                   self._current_token.literal)
            identifiers.append(ident)
        if not self._expect_peek(TokenType.RPAREN):
            return None
        return identifiers

    # Similar to _parse_function_parameters() except it's more general and
    # returns a list of expression rather than a list of identifiers.
    def _parse_expression_list(self, end: TokenType) -> Optional[List[mast.Expression]]:
        list_: List[mast.Expression] = []
        if self._peek_token_is(end):
            self._next_token()
            return list_
        self._next_token()
        expr = self._parse_expression(PrecedenceLevel.LOWEST)
        if expr is None:
            return None
        list_.append(expr)
        while self._peek_token_is(TokenType.COMMA):
            self._next_token()
            self._next_token()
            expr = self._parse_expression(PrecedenceLevel.LOWEST)
            if expr is None:
                return None
            list_.append(expr)
        if not self._expect_peek(end):
            return None
        return list_

    def _parse_array_literal(self) -> Optional[mast.ArrayLiteral]:
        token = self._current_token
        elements = self._parse_expression_list(TokenType.RBRACKET)
        if elements is None:
            return None
        return mast.ArrayLiteral(token, elements)

    def _parse_hash_literal(self) -> Optional[mast.HashLiteral]:
        token = self._current_token
        pairs: Dict[mast.Expression, mast.Expression] = {}
        while not self._peek_token_is(TokenType.RBRACE):
            self._next_token()
            key = self._parse_expression(PrecedenceLevel.LOWEST)
            if key is None:
                return None
            if not self._expect_peek(TokenType.COLON):
                return None
            self._next_token()
            value = self._parse_expression(PrecedenceLevel.LOWEST)
            if value is None:
                return None
            pairs[key] = value
            if not self._peek_token_is(TokenType.RBRACE) and not self._expect_peek(TokenType.COMMA):
                return None
        if not self._expect_peek(TokenType.RBRACE):
            return None
        return mast.HashLiteral(token, pairs)

    def _parse_group_expression(self) -> Optional[mast.Expression]:
        self._next_token()
        expr = self._parse_expression(PrecedenceLevel.LOWEST)
        if not self._expect_peek(TokenType.RPAREN):
            return None
        return expr

    def _parse_if_expression(self) -> Optional[mast.IfExpression]:
        token = self._current_token
        if not self._expect_peek(TokenType.LPAREN):
            return None
        self._next_token()
        condition = self._parse_expression(PrecedenceLevel.LOWEST)
        if condition is None:
            return None
        if not self._expect_peek(TokenType.RPAREN):
            return None
        if not self._expect_peek(TokenType.LBRACE):
            return None
        consequence = self._parse_block_statement()
        alternative = None
        if self._peek_token_is(TokenType.ELSE):
            self._next_token()
            if not self._expect_peek(TokenType.LBRACE):
                return None
            alternative = self._parse_block_statement()
        return mast.IfExpression(token, condition, consequence, alternative)

    def _parse_block_statement(self) -> mast.BlockStatement:
        token = self._current_token
        statements = []
        self._next_token()
        while not self._current_token_is(TokenType.RBRACE):
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._next_token()
        return mast.BlockStatement(token, statements)

    def _parse_function_literal(self) -> Optional[mast.FunctionLiteral]:
        token = self._current_token
        if not self._expect_peek(TokenType.LPAREN):
            return None
        parameters = self._parse_function_parameters()
        if parameters is None:
            return None
        if not self._expect_peek(TokenType.LBRACE):
            return None
        body = self._parse_block_statement()
        return mast.FunctionLiteral(token, parameters, body)

    def _parse_call_expression(self, function: mast.Expression) -> Optional[mast.CallExpression]:
        token = self._current_token
        arguments = self._parse_expression_list(TokenType.RPAREN)
        if arguments is None:
            return None
        return mast.CallExpression(token, function, arguments)

    def _parse_index_expression(self, left: mast.Expression) -> Optional[mast.IndexExpression]:
        token = self._current_token
        self._next_token()
        index = self._parse_expression(PrecedenceLevel.LOWEST)
        if index is None:
            return None
        if not self._expect_peek(TokenType.RBRACKET):
            return None
        return mast.IndexExpression(token, left, index)

    def _parse_call_arguments(self) -> Optional[List[mast.Expression]]:
        args: List[mast.Expression] = []
        if self._peek_token_is(TokenType.RPAREN):
            self._next_token()
            return args
        self._next_token()
        expr = self._parse_expression(PrecedenceLevel.LOWEST)
        if expr is None:
            return None
        args.append(expr)
        while self._peek_token_is(TokenType.COMMA):
            self._next_token()
            self._next_token()
            expr = self._parse_expression(PrecedenceLevel.LOWEST)
            if expr is None:
                return None
            args.append(expr)
        if not self._expect_peek(TokenType.RPAREN):
            return None
        return args

    def _parse_prefix_expression(self) -> Optional[mast.PrefixExpression]:
        token = self._current_token
        self._next_token()
        right = self._parse_expression(PrecedenceLevel.PREFIX)
        if right is None:
            return None
        return mast.PrefixExpression(token, token.literal, right)

    def _parse_infix_expression(self, left: mast.Expression) -> Optional[mast.InfixExpression]:
        token = self._current_token
        precedence = self._current_precedence()
        self._next_token()
        right = self._parse_expression(precedence)
        if right is None:
            return None
        return mast.InfixExpression(token, left, token.literal, right)

    def _parse_boolean(self) -> Optional[mast.Boolean]:
        if self._current_token is None:
            return None
        return mast.Boolean(self._current_token, self._current_token_is(TokenType.TRUE))

    def _parse_return_statement(self) -> Optional[mast.ReturnStatement]:
        token = self._current_token
        self._next_token()
        return_value = self._parse_expression(PrecedenceLevel.LOWEST)
        if return_value is None:
            return None
        if self._peek_token_is(TokenType.SEMICOLON):
            self._next_token()
        return mast.ReturnStatement(token, return_value)

    def _current_token_is(self, type_: TokenType) -> bool:
        if self._current_token is None:
            return False
        return self._current_token.type_ == type_

    def _peek_token_is(self, type_: TokenType) -> bool:
        if self._peek_token is None:
            return False
        return self._peek_token.type_ == type_

    def _expect_peek(self, type_: TokenType) -> bool:
        if self._peek_token_is(type_):
            self._next_token()
            return True
        self._peek_error(type_)
        return False

    def _peek_error(self, type_: TokenType) -> None:
        assert self._peek_token is not None
        message = f"expected next token to be {type_.value}. " + \
                  f"Got {self._peek_token.type_.value} instead"
        self.errors.append(message)

    def _no_prefix_parse_fn_error(self, type_: TokenType) -> None:
        message = f"no prefix parse function for {type_.value} found"
        self.errors.append(message)

    def _peek_precedence(self) -> PrecedenceLevel:
        assert self._peek_token is not None
        type_ = self._peek_token.type_

        # Returning LOWEST when precedence level could not be determined enables
        # us to parse grouped expression. The RParen token doesn't have an
        # associated precedence, and returning LOWEST is what causes the parser
        # to finish evaluating a subexpression as a whole.
        if type_ in Precedence:
            return Precedence[type_]
        return PrecedenceLevel.LOWEST

    def _current_precedence(self) -> PrecedenceLevel:
        type_ = self._current_token.type_
        if type_ in Precedence:
            return Precedence[type_]
        return PrecedenceLevel.LOWEST
