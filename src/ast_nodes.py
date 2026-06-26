# src/ast_nodes.py
# ============================================================
#  AST NODE DEFINITIONS — BahasaFlores Compiler
# ============================================================
from dataclasses import dataclass, field
from typing import List, Optional, Any


class ASTNode:
    """Base class semua node AST."""
    pass


# ── Program Root ────────────────────────────────────────────
@dataclass
class Program(ASTNode):
    body: List[ASTNode]

    def __repr__(self):
        return f"Program({len(self.body)} statements)"


# ════════════════════════════════════════════════════════════
#  STATEMENTS
# ════════════════════════════════════════════════════════════

@dataclass
class AssignStmt(ASTNode):
    name: str
    op: str          # '=' | '+=' | '-=' | '*=' | '/='
    value: ASTNode
    line: int = 0

    def __repr__(self):
        return f"Assign({self.name} {self.op} {self.value})"


@dataclass
class PrintStmt(ASTNode):
    args: List[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"Print({self.args})"


@dataclass
class InputStmt(ASTNode):
    prompt: Optional[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"Input({self.prompt})"


@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    elif_clauses: List       # [(condition, block), ...]
    else_block: Optional[List[ASTNode]]
    line: int = 0

    def __repr__(self):
        return f"If({self.condition})"


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"While({self.condition})"


@dataclass
class ForStmt(ASTNode):
    var: str
    iterable: ASTNode
    body: List[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"For({self.var} dalam {self.iterable})"


@dataclass
class FuncDef(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"FuncDef({self.name})"


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"Return({self.value})"


@dataclass
class BreakStmt(ASTNode):
    line: int = 0

    def __repr__(self):
        return "Break()"


@dataclass
class ContinueStmt(ASTNode):
    line: int = 0

    def __repr__(self):
        return "Continue()"


@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode
    line: int = 0

    def __repr__(self):
        return f"ExprStmt({self.expr})"


# ════════════════════════════════════════════════════════════
#  EXPRESSIONS
# ════════════════════════════════════════════════════════════

@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode
    line: int = 0

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode
    line: int = 0

    def __repr__(self):
        return f"UnaryOp({self.op}{self.operand})"


@dataclass
class NumberLiteral(ASTNode):
    value: Any        # int atau float
    line: int = 0

    def __repr__(self):
        return f"Num({self.value})"


@dataclass
class StringLiteral(ASTNode):
    value: str
    line: int = 0

    def __repr__(self):
        return f"Str({self.value!r})"


@dataclass
class BoolLiteral(ASTNode):
    value: bool
    line: int = 0

    def __repr__(self):
        return f"Bool({self.value})"


@dataclass
class NoneLiteral(ASTNode):
    line: int = 0

    def __repr__(self):
        return "NoneVal()"


@dataclass
class Identifier(ASTNode):
    name: str
    line: int = 0

    def __repr__(self):
        return f"ID({self.name})"


@dataclass
class FuncCall(ASTNode):
    name: str
    args: List[ASTNode]
    line: int = 0

    def __repr__(self):
        return f"Call({self.name}, {self.args})"


@dataclass
class SubscriptExpr(ASTNode):
    obj: ASTNode
    index: ASTNode
    line: int = 0

    def __repr__(self):
        return f"Subscript({self.obj}[{self.index}])"