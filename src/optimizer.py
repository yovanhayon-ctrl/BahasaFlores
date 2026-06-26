# src/optimizer.py
# ============================================================
#  CODE OPTIMIZER — Constant Folding + Dead Code Elimination
# ============================================================

from .ast_nodes import *
from typing import List


class Optimizer:
    """
    Optimasi AST sebelum code generation.
    Teknik yang dipakai:
    1. Constant Folding   — 2 + 3  →  5
    2. Constant Propagation — x = 5; y = x + 1  →  y = 6
    3. Dead Code Elimination — t ada le (sala): ...  → dihapus
    4. Algebraic Simplification — x * 1 → x, x + 0 → x
    """

    def __init__(self):
        self.const_env = {}   # nama variabel → nilai konstan
        self.changes   = 0    # hitung berapa optimasi dilakukan

    def optimize(self, node: ASTNode) -> ASTNode:
        method = f"opt_{type(node).__name__}"
        visitor = getattr(self, method, self.generic_opt)
        return visitor(node)

    def generic_opt(self, node: ASTNode) -> ASTNode:
        return node

    def optimize_block(self, stmts: List[ASTNode]) -> List[ASTNode]:
        result = []
        for stmt in stmts:
            optimized = self.optimize(stmt)
            if optimized is not None:
                result.append(optimized)
        return result

    # ── Statements ──────────────────────────────────────────

    def opt_Program(self, node: Program) -> Program:
        node.body = self.optimize_block(node.body)
        return node

    def opt_AssignStmt(self, node: AssignStmt) -> AssignStmt:
        node.value = self.optimize(node.value)
        # Constant Propagation: simpan nilai jika konstan
        if isinstance(node.value, (NumberLiteral, StringLiteral,
                                   BoolLiteral, NoneLiteral)):
            if node.op == '=':
                self.const_env[node.name] = node.value
        else:
            # Nilai tidak lagi konstan jika di-reassign
            self.const_env.pop(node.name, None)
        return node

    def opt_PrintStmt(self, node: PrintStmt) -> PrintStmt:
        node.args = [self.optimize(a) for a in node.args]
        return node

    def opt_ExprStmt(self, node: ExprStmt) -> ExprStmt:
        node.expr = self.optimize(node.expr)
        return node

    def opt_IfStmt(self, node: IfStmt) -> Optional[ASTNode]:
        node.condition = self.optimize(node.condition)

        # Dead Code Elimination: kondisi selalu False → hapus
        if isinstance(node.condition, BoolLiteral) and not node.condition.value:
            self.changes += 1
            # Periksa else_block
            if node.else_block:
                return Program(self.optimize_block(node.else_block))
            return None   # Hapus seluruh if

        # Kondisi selalu True → ambil then_block saja
        if isinstance(node.condition, BoolLiteral) and node.condition.value:
            self.changes += 1
            return Program(self.optimize_block(node.then_block))

        node.then_block    = self.optimize_block(node.then_block)
        node.elif_clauses  = [(self.optimize(c), self.optimize_block(b))
                               for c, b in node.elif_clauses]
        if node.else_block:
            node.else_block = self.optimize_block(node.else_block)
        return node

    def opt_WhileStmt(self, node: WhileStmt) -> Optional[WhileStmt]:
        node.condition = self.optimize(node.condition)
        # Dead code: while (sala): → hapus
        if isinstance(node.condition, BoolLiteral) and not node.condition.value:
            self.changes += 1
            return None
        node.body = self.optimize_block(node.body)
        return node

    def opt_ForStmt(self, node: ForStmt) -> ForStmt:
        node.iterable = self.optimize(node.iterable)
        node.body     = self.optimize_block(node.body)
        return node

    def opt_FuncDef(self, node: FuncDef) -> FuncDef:
        node.body = self.optimize_block(node.body)
        return node

    def opt_ReturnStmt(self, node: ReturnStmt) -> ReturnStmt:
        if node.value:
            node.value = self.optimize(node.value)
        return node

    # ── Expressions ─────────────────────────────────────────

    def opt_Identifier(self, node: Identifier) -> ASTNode:
        # Constant Propagation
        if node.name in self.const_env:
            self.changes += 1
            return self.const_env[node.name]
        return node

    def opt_BinOp(self, node: BinOp) -> ASTNode:
        node.left  = self.optimize(node.left)
        node.right = self.optimize(node.right)

        L = node.left
        R = node.right

        # Constant Folding — keduanya angka
        if isinstance(L, NumberLiteral) and isinstance(R, NumberLiteral):
            result = self._fold_number(L.value, node.op, R.value)
            if result is not None:
                self.changes += 1
                return NumberLiteral(result, node.line)

        # Constant Folding — string concatenation
        if (isinstance(L, StringLiteral) and isinstance(R, StringLiteral)
                and node.op == '+'):
            self.changes += 1
            return StringLiteral(L.value + R.value, node.line)

        # Algebraic Simplification
        simp = self._simplify(L, node.op, R, node.line)
        if simp is not None:
            self.changes += 1
            return simp

        return node

    def _fold_number(self, a, op, b):
        try:
            ops = {'+': a+b, '-': a-b, '*': a*b,
                   '/': a/b  if b != 0 else None,
                   '//': a//b if b != 0 else None,
                   '%': a%b   if b != 0 else None,
                   '**': a**b,
                   '==': a==b, '!=': a!=b,
                   '<': a<b,   '>': a>b,
                   '<=': a<=b, '>=': a>=b}
            return ops.get(op)
        except Exception:
            return None

    def _simplify(self, L, op, R, line):
        zero  = NumberLiteral(0, line)
        one   = NumberLiteral(1, line)

        def is_zero(n): return isinstance(n, NumberLiteral) and n.value == 0
        def is_one(n):  return isinstance(n, NumberLiteral) and n.value == 1

        if op == '+' and is_zero(R): return L
        if op == '+' and is_zero(L): return R
        if op == '-' and is_zero(R): return L
        if op == '*' and is_one(R):  return L
        if op == '*' and is_one(L):  return R
        if op == '*' and is_zero(R): return zero
        if op == '*' and is_zero(L): return zero
        if op == '/' and is_one(R):  return L
        return None

    def opt_UnaryOp(self, node: UnaryOp) -> ASTNode:
        node.operand = self.optimize(node.operand)
        if node.op == '-' and isinstance(node.operand, NumberLiteral):
            self.changes += 1
            return NumberLiteral(-node.operand.value, node.line)
        return node

    def opt_FuncCall(self, node: FuncCall) -> FuncCall:
        node.args = [self.optimize(a) for a in node.args]
        return node

    def opt_InputStmt(self, node: InputStmt) -> InputStmt:
        if node.prompt:
            node.prompt = self.optimize(node.prompt)
        return node

    def opt_NumberLiteral(self, n): return n
    def opt_StringLiteral(self, n): return n
    def opt_BoolLiteral(self, n):   return n
    def opt_NoneLiteral(self, n):   return n
    def opt_SubscriptExpr(self, node: SubscriptExpr) -> SubscriptExpr:
        node.obj   = self.optimize(node.obj)
        node.index = self.optimize(node.index)
        return node