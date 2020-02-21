from abc import ABC, abstractclassmethod
from typing import List, Optional, Dict, Type
from lexer import Token

class Node(ABC):
    @abstractclassmethod
    def token_literal(self) -> Optional[str]:
        raise NotImplementedError

    @abstractclassmethod
    def string(self) -> str:
        raise NotImplementedError

class Statement(Node):
    def token_literal(self) -> Optional[str]:
        raise NotImplementedError

class Expression(Node):
    def token_literal(self) -> str:
        raise NotImplementedError

class Program(Statement):
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
            out += s.string() # TODO: how to avoid reallocing memory and write into a buffer?
        return out

class Identifier(Expression):
    def __init__(self, token: Token, value: str):
        self.token = token
        self.value = value

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return self.value

class LetStatement(Statement):    
    def __init__(self, token: Token, name: Identifier, value: Expression):
        self.token = token
        self.name = name
        self.value = value

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        out = f"{self.token_literal()} {self.name.string()} = "
        if self.value != None:
            out += self.value.string()
        return out + ";"

class ReturnStatement(Statement):
    def __init__(self, token: Token, return_value: Expression):
        self.token = token
        self.return_value = return_value

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        out = f"{self.token_literal()} "
        if self.return_value != None:
            out += self.return_value.string()
        return out + ";"

class ExpressionStatement(Expression):
    def __init__(self, token: Token, expression: Expression):
        self.token = token
        self.expression = expression

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        if self.expression != None:
            return self.expression.string()
        return ""

class IntegerLiteral(Expression):
    def __init__(self, token: Token, value: int):
        self.token = token
        self.value = value
    
    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return self.token.literal

class PrefixExpression(Expression):
    def __init__(self, token: Token, operator: str, right: Expression):
        self.token = token
        self.operator = operator
        self.right = right

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return f"({self.operator}{self.right.string()})"

class InfixExpression(Expression):
    def __init__(self, token:Token, left: Expression, operator: str, right: Expression):
        self.token = token
        self.left = left
        self.operator = operator
        self.right = right

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:        
        return f"({self.left.string()} {self.operator} {self.right.string()})"

class Boolean(Expression):
    def __init__(self, token: Token, value: bool):
        self.token = token
        self.value = value

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return self.token.literal

class BlockStatement(Statement):
    def __init__(self, token: Token, statements: List[Statement]):
        self.token = token
        self.statements = statements or []

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        out = ""
        for s in self.statements:
            out += s.string()
        return out

class IfExpression(Expression):
    def __init__(self, token: Token, condition: Expression, consequence: BlockStatement, alternative: BlockStatement):
        self.token = token
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        out = f"if {self.condition.string()} {{ {self.consequence.string()} }}"
        if self.alternative != None:
            out += f" else {{ {self.alternative.string()} }}"
        return out

class FunctionLiteral(Expression):
    def __init__(self, token: Token, parameters: List[Identifier], body: BlockStatement):
        self.token = token
        self.parameters = parameters
        self.body = body

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        params = []
        for p in self.parameters:
            params.append(p.string())
        return f"{self.token_literal}({', '.join(params)}) {self.body.string()}"

class CallExpression(Expression):
    def __init__(self, token: Token, function: Expression, arguments: List[Expression]):
        self.token = token
        self.function = function
        self.arguments = arguments or []

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        args = []
        for a in self.arguments:
            args.append(a.string())
        return f"{self.function.string()}({', '.join(args)})"
    
class StringLiteral(Expression):
    def __init__(self, token: Token, value: str):
        self.token = token
        self.value = value
    
    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return self.token.literal

class ArrayLiteral(Expression):
    def __init__(self, token: Token, elements: List[Expression]):
        self.token = token
        self.elements = elements

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        elements = []
        for e in self.elements:
            elements.append(e.string())
        return f"[{', '.join(elements)}]"

class IndexExpression(Expression):
    def __init__(self, token: Token, left: Expression, index: Expression):
        self.token = token
        self.left = left
        self.index = index

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        return f"({self.left.string()}[{self.index.string()}])"

class HashLiteral(Expression):
    from object import Object
    
    def __init__(self, token: Token, pairs: Dict[Object, Object]):
        self.token = token
        self.pairs = pairs

    def token_literal(self) -> str:
        return self.token.literal

    def string(self) -> str:
        pairs = []
        for k, v in self.pairs.items():
            pairs.append(f"{k.string()}: {v.string()}")
        return f"{{{', '.join(pairs)}}}"
