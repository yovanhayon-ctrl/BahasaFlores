# src/semantic.py
# ============================================================
#  SEMANTIC ANALYZER — Symbol Table + Type Checking
# ============================================================

from .ast_nodes import *
from typing import Dict, List, Optional


class SemanticError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(f"[SemanticError] Baris {line}: {msg}")
        self.line = line


# ── Symbol Table ─────────────────────────────────────────────

class SymbolTable:
    def __init__(self, parent=None, scope_name="global"):
        self.symbols: Dict[str, dict] = {}
        self.parent = parent
        self.scope_name = scope_name

    def define(self, name: str, info: dict):
        self.symbols[name] = info

    def lookup(self, name: str) -> Optional[dict]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def __repr__(self):
        return f"SymbolTable({self.scope_name}): {list(self.symbols.keys())}"


# ── Analyzer ─────────────────────────────────────────────────

class SemanticAnalyzer:
    def __init__(self):
        self.global_scope = SymbolTable(scope_name="global")
        self.current_scope = self.global_scope
        self.errors: List[str] = []
        self.in_function = False
        self.in_loop = False

        # Built-in functions yang masih boleh dipakai
        for builtin in ['range', 'int', 'float', 'str', 'len',
                        'list', 'dict', 'abs', 'max', 'min', 'sum']:
            self.global_scope.define(builtin, {'type': 'builtin'})

    def error(self, msg, line=0):
        self.errors.append(f"[SemanticError] Baris {line}: {msg}")

    def analyze(self, node: ASTNode):
        method = f"visit_{type(node).__name__}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        return None

    # ── Program ─────────────────────────────────────────────

    def visit_Program(self, node: Program):
        for stmt in node.body:
            self.analyze(stmt)
        return self.global_scope

    # ── Statements ──────────────────────────────────────────

    def visit_AssignStmt(self, node: AssignStmt):
        self.analyze(node.value)
        self.current_scope.define(node.name, {
            'type': 'variable',
            'line': node.line
        })

    def visit_PrintStmt(self, node: PrintStmt):
        for arg in node.args:
            self.analyze(arg)

    def visit_InputStmt(self, node: InputStmt):
        if node.prompt:
            self.analyze(node.prompt)

    def visit_IfStmt(self, node: IfStmt):
        self.analyze(node.condition)
        for stmt in node.then_block:
            self.analyze(stmt)
        for cond, block in node.elif_clauses:
            self.analyze(cond)
            for stmt in block:
                self.analyze(stmt)
        if node.else_block:
            for stmt in node.else_block:
                self.analyze(stmt)

    def visit_WhileStmt(self, node: WhileStmt):
        prev = self.in_loop
        self.in_loop = True
        self.analyze(node.condition)
        for stmt in node.body:
            self.analyze(stmt)
        self.in_loop = prev

    def visit_ForStmt(self, node: ForStmt):
        prev = self.in_loop
        self.in_loop = True
        self.analyze(node.iterable)
        self.current_scope.define(node.var, {'type': 'variable', 'line': node.line})
        for stmt in node.body:
            self.analyze(stmt)
        self.in_loop = prev

    def visit_FuncDef(self, node: FuncDef):
        self.current_scope.define(node.name, {
            'type': 'function',
            'params': node.params,
            'line': node.line
        })
        prev_scope    = self.current_scope
        prev_in_func  = self.in_function
        self.current_scope = SymbolTable(parent=self.current_scope,
                                          scope_name=node.name)
        self.in_function = True
        for param in node.params:
            self.current_scope.define(param, {'type': 'parameter'})
        for stmt in node.body:
            self.analyze(stmt)
        self.current_scope = prev_scope
        self.in_function   = prev_in_func

    def visit_ReturnStmt(self, node: ReturnStmt):
        if not self.in_function:
            self.error("'beri bale' digunakan di luar fungsi", node.line)
        if node.value:
            self.analyze(node.value)

    def visit_BreakStmt(self, node: BreakStmt):
        if not self.in_loop:
            self.error("'barenti' digunakan di luar loop", node.line)

    def visit_ContinueStmt(self, node: ContinueStmt):
        if not self.in_loop:
            self.error("'tero' digunakan di luar loop", node.line)

    def visit_ExprStmt(self, node: ExprStmt):
        self.analyze(node.expr)

    # ── Expressions ─────────────────────────────────────────

    def visit_Identifier(self, node: Identifier):
        if not self.current_scope.lookup(node.name):
            self.error(f"Variabel '{node.name}' belum didefinisikan", node.line)

    def visit_BinOp(self, node: BinOp):
        self.analyze(node.left)
        self.analyze(node.right)

    def visit_UnaryOp(self, node: UnaryOp):
        self.analyze(node.operand)

    def visit_FuncCall(self, node: FuncCall):
        sym = self.current_scope.lookup(node.name)
        if not sym:
            self.error(f"Fungsi '{node.name}' belum didefinisikan", node.line)
        for arg in node.args:
            self.analyze(arg)

    def visit_NumberLiteral(self, node): pass
    def visit_StringLiteral(self, node): pass
    def visit_BoolLiteral(self, node):   pass
    def visit_NoneLiteral(self, node):   pass
    def visit_SubscriptExpr(self, node: SubscriptExpr):
        self.analyze(node.obj)
        self.analyze(node.index)

    def report(self):
        if self.errors:
            print("\n=== SEMANTIC ERRORS ===")
            for e in self.errors:
                print(" ", e)
            return False
        print("[Semantic] OK — tidak ada error.")
        return True