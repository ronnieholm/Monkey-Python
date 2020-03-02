from abc import ABC, abstractclassmethod
from typing import List, Optional, Dict, Union
from functools import reduce
from lexer import Token


class Node(ABC):
    @abstractclassmethod
    def token_literal(cls) -> Optional[str]:
        # For debugging and testing.
        raise NotImplementedError

    @abstractclassmethod
    def string(cls) -> str:
        # We don't override __str__ or __repr__ to make string calls explicit.
        raise NotImplementedError


class Statement(Node):
    def __init__(self, token: Token) -> None:
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return self.token.literal


class Expression(Node):
    def __init__(self, token: Token) -> None:
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return self.token.literal


class Program(Node):
    def __init__(self, statements: List[Union[Statement, Expression]]) -> None:
        self.statements = statements or []

    def token_literal(self) -> str:
        stmts = self.statements
        return stmts[0].token_literal() if len(stmts) > 0 else ""

    def string(self) -> str:
        return reduce(lambda a, b: a + b.string(), self.statements, "")


class Identifier(Expression):
    def __init__(self, token: Token, value: str) -> None:
        super(Identifier, self).__init__(token)
        self.value = value

    def string(self) -> str:
        return self.value


class LetStatement(Statement):
    def __init__(self, token: Token, name: Identifier, value: Expression) -> None:
        super(LetStatement, self).__init__(token)
        self.name = name
        self.value = value

    def string(self) -> str:
        out = f"{self.token_literal()} {self.name.string()} = "

        # LetStatement, ReturnStatement, and ExpressionStatement may contain a
        # None member. This happens when attempting to call Program.string() on
        # a program with parse errors. Program.string() isn't called by tests
        # nor main.py, but may be enabled during debugging.
        if self.value is not None:
            out += self.value.string()
        return out + ";"


class ReturnStatement(Statement):
    def __init__(self, token: Token, return_value: Expression) -> None:
        super(ReturnStatement, self).__init__(token)
        self.return_value = return_value

    def string(self) -> str:
        out = f"{self.token_literal()} "
        if self.return_value is not None:
            out += self.return_value.string()
        return out + ";"


class ExpressionStatement(Expression):
    def __init__(self, token: Token, expression: Expression) -> None:
        super(ExpressionStatement, self).__init__(token)
        self.expression = expression

    def string(self) -> str:
        expr = self.expression
        return expr.string() if expr is not None else ""


class IntegerLiteral(Expression):
    def __init__(self, token: Token, value: int) -> None:
        super(IntegerLiteral, self).__init__(token)
        self.value = value


class PrefixExpression(Expression):
    def __init__(self, token: Token, operator: str, right: Expression) -> None:
        super(PrefixExpression, self).__init__(token)
        self.operator = operator
        self.right = right

    def string(self) -> str:
        return f"({self.operator}{self.right.string()})"


class InfixExpression(Expression):
    def __init__(self, token: Token, left: Expression, operator: str, right: Expression) -> None:
        super(InfixExpression, self).__init__(token)

        # Object being accessed is an expression as it can be an identifier, an
        # array literal, or a function call.
        self.left = left
        self.operator = operator
        self.right = right

    def string(self) -> str:
        return f"({self.left.string()} {self.operator} {self.right.string()})"


class Boolean(Expression):
    def __init__(self, token: Token, value: bool) -> None:
        super(Boolean, self).__init__(token)
        self.value = value


class BlockStatement(Statement):
    def __init__(self, token: Token, statements: List[Union[Statement, Expression]]) -> None:
        super(BlockStatement, self).__init__(token)
        self.statements = statements or []

    def string(self) -> str:
        return reduce(lambda a, b: a + b.string(), self.statements, "")


class IfExpression(Expression):
    def __init__(self, token: Token, condition: Expression,
                 consequence: BlockStatement,
                 alternative: Optional[BlockStatement]) -> None:
        super(IfExpression, self).__init__(token)
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def string(self) -> str:
        out = f"if {self.condition.string()} {{ {self.consequence.string()} }}"
        if self.alternative is not None:
            out += f" else {{ {self.alternative.string()} }}"
        return out


class FunctionLiteral(Expression):
    def __init__(self, token: Token, parameters: List[Identifier], body: BlockStatement) -> None:
        super(FunctionLiteral, self).__init__(token)
        self.parameters = parameters
        self.body = body

    def string(self) -> str:
        params = map(lambda p: p.string(), self.parameters)
        return f"{self.token_literal()}({', '.join(params)}) {self.body.string()}"


class CallExpression(Expression):
    def __init__(self, token: Token, function: Expression, arguments: List[Expression]) -> None:
        super(CallExpression, self).__init__(token)
        self.function = function
        self.arguments = arguments or []

    def string(self) -> str:
        args = map(lambda a: a.string(), self.arguments)
        return f"{self.function.string()}({', '.join(args)})"


class StringLiteral(Expression):
    def __init__(self, token: Token, value: str) -> None:
        super(StringLiteral, self).__init__(token)
        self.value = value


class ArrayLiteral(Expression):
    def __init__(self, token: Token, elements: List[Expression]) -> None:
        super(ArrayLiteral, self).__init__(token)
        self.elements = elements

    def string(self) -> str:
        elements = map(lambda e: e.string(), self.elements)
        return f"[{', '.join(elements)}]"


class IndexExpression(Expression):
    def __init__(self, token: Token, left: Expression, index: Expression) -> None:
        super(IndexExpression, self).__init__(token)
        self.left = left
        self.index = index

    def string(self) -> str:
        return f"({self.left.string()}[{self.index.string()}])"


class HashLiteral(Expression):
    def __init__(self, token: Token, pairs: Dict[Expression, Expression]) -> None:
        super(HashLiteral, self).__init__(token)
        self.pairs = pairs

    def string(self) -> str:
        pairs = []
        for key, value in self.pairs.items():
            pairs.append(f"{key.string()}: {value.string()}")
        return f"{{{', '.join(pairs)}}}"
