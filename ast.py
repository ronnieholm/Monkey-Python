from abc import ABC, abstractclassmethod
from typing import List, Optional, Dict, Type
from lexer import Token

class Node(ABC):
    @abstractclassmethod
    def token_literal(self) -> Optional[str]:
        # For debugging and testing.
        raise NotImplementedError

    @abstractclassmethod
    def string(self) -> str:
        # We don't override __str__ or __repr__ to make string calls explicit.
        raise NotImplementedError

class Statement(Node):
    def __init__(self, token: Token):
        self.token = token

    def token_literal(self) -> Optional[str]:
        return self.token.literal

    def string(self):
        return self.token.literal

class Expression(Node):
    def __init__(self, token: Token):
        self.token = token

    def token_literal(self) -> Optional[str]:
        return self.token.literal

    def string(self):
        return self.token.literal

class Program(Node):
    def __init__(self, statements = None):
        self.statements = statements or []

    def token_literal(self) -> str:
        if len(self.statements) > 0:
            return self.statements[0].token_literal()
        else:
            return ""

    def string(self) -> str:
        out = ""
        for s in self.statements:
            out += s.string()
        return out

class Identifier(Expression):
    def __init__(self, token: Token, value: str):
        super(Identifier, self).__init__(token)
        self.value = value

    def string(self) -> str:
        return self.value

class LetStatement(Statement):    
    def __init__(self, token: Token, name: Identifier, value: Expression):
        super(LetStatement, self).__init__(token)
        self.name = name
        self.value = value

    def string(self) -> str:
        out = f"{self.token_literal()} {self.name.string()} = "
        if self.value != None:
            out += self.value.string()
        return out + ";"

class ReturnStatement(Statement):
    def __init__(self, token: Token, return_value: Expression):
        super(ReturnStatement, self).__init__(token)
        self.return_value = return_value

    def string(self) -> str:
        out = f"{self.token_literal()} "
        if self.return_value != None:
            out += self.return_value.string()
        return out + ";"

class ExpressionStatement(Expression):
    def __init__(self, token: Token, expression: Expression):
        super(ExpressionStatement, self).__init__(token)
        self.expression = expression

    def string(self) -> str:
        if self.expression != None:
            return self.expression.string()
        return ""

class IntegerLiteral(Expression):
    def __init__(self, token: Token, value: int):
        super(IntegerLiteral, self).__init__(token)
        self.value = value

class PrefixExpression(Expression):
    def __init__(self, token: Token, operator: str, right: Expression):
        super(PrefixExpression, self).__init__(token)
        self.operator = operator
        self.right = right

    def string(self) -> str:
        return f"({self.operator}{self.right.string()})"

class InfixExpression(Expression):
    def __init__(self, token:Token, left: Expression, operator: str, right: Expression):
        super(InfixExpression, self).__init__(token)

        # Object being accessed is an expression as it can be an identifier, an
        # array literal, or a function call.
        self.left = left
        self.operator = operator
        self.right = right

    def string(self) -> str:        
        return f"({self.left.string()} {self.operator} {self.right.string()})"

class Boolean(Expression):
    def __init__(self, token: Token, value: bool):
        super(Boolean, self).__init__(token)
        self.value = value

class BlockStatement(Statement):
    def __init__(self, token: Token, statements: List[Statement]):
        super(BlockStatement, self).__init__(token)
        self.statements = statements or []

    def string(self) -> str:
        out = ""
        for s in self.statements:
            out += s.string()
        return out

class IfExpression(Expression):
    def __init__(self, token: Token, condition: Expression, consequence: BlockStatement, alternative: BlockStatement):
        super(IfExpression, self).__init__(token)
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def string(self) -> str:
        out = f"if {self.condition.string()} {{ {self.consequence.string()} }}"
        if self.alternative != None:
            out += f" else {{ {self.alternative.string()} }}"
        return out

class FunctionLiteral(Expression):
    def __init__(self, token: Token, parameters: List[Identifier], body: BlockStatement):
        super(FunctionLiteral, self).__init__(token)
        self.parameters = parameters
        self.body = body

    def string(self) -> str:
        params = []
        for p in self.parameters:
            params.append(p.string())
        return f"{self.token_literal}({', '.join(params)}) {self.body.string()}"

class CallExpression(Expression):
    def __init__(self, token: Token, function: Expression, arguments: List[Expression]):
        super(CallExpression, self).__init__(token)
        self.function = function
        self.arguments = arguments or []

    def string(self) -> str:
        args = []
        for a in self.arguments:
            args.append(a.string())
        return f"{self.function.string()}({', '.join(args)})"
    
class StringLiteral(Expression):
    def __init__(self, token: Token, value: str):
        super(StringLiteral, self).__init__(token)
        self.value = value

class ArrayLiteral(Expression):
    def __init__(self, token: Token, elements: List[Expression]):
        super(ArrayLiteral, self).__init__(token)
        self.elements = elements

    def string(self) -> str:
        elements = []
        for e in self.elements:
            elements.append(e.string())
        return f"[{', '.join(elements)}]"

class IndexExpression(Expression):
    def __init__(self, token: Token, left: Expression, index: Expression):
        super(IndexExpression, self).__init__(token)
        self.left = left
        self.index = index

    def string(self) -> str:
        return f"({self.left.string()}[{self.index.string()}])"

class HashLiteral(Expression):
    from object import Object
    
    def __init__(self, token: Token, pairs: Dict[Object, Object]):
        super(HashLiteral, self).__init__(token)
        self.pairs = pairs

    def string(self) -> str:
        pairs = []
        for k, v in self.pairs.items():
            pairs.append(f"{k.string()}: {v.string()}")
        return f"{{{', '.join(pairs)}}}"
