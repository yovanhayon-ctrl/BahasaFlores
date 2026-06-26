# src/parser.py
# ============================================================
#  PARSER — Recursive Descent, menghasilkan AST langsung
#  (Parse Tree implisit di dalam call stack rekursi)
# ============================================================

from typing import List, Optional
from .lexer import Token, TT, tokenize
from .ast_nodes import *


class ParseError(Exception):
    def __init__(self, msg, line=0, col=0):
        super().__init__(f"[ParseError] Baris {line}, Kolom {col}: {msg}")
        self.line = line
        self.col  = col


class Parser:
    def __init__(self, tokens: List[Token]):
        # Hapus NEWLINE ganda dan INDENT_LEVEL artifacts
        self.tokens = [t for t in tokens
                       if not (t.type == TT.NEWLINE
                               and t.value.startswith('INDENT_LEVEL:'))]
        self.pos    = 0

    # ── navigation ──────────────────────────────────────────

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, tt: TT, msg: str = "") -> Token:
        tok = self.current()
        if tok.type != tt:
            raise ParseError(
                msg or f"Diharapkan {tt.name}, didapat {tok.type.name} ({tok.value!r})",
                tok.line, tok.col)
        return self.advance()

    def match(self, *types: TT) -> bool:
        return self.current().type in types

    def skip_newlines(self):
        while self.match(TT.NEWLINE):
            self.advance()

    # ════════════════════════════════════════════════════════
    #  ENTRY POINT
    # ════════════════════════════════════════════════════════

    def parse(self) -> Program:
        self.skip_newlines()
        body = []
        while not self.match(TT.EOF):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()
        return Program(body)

    # ════════════════════════════════════════════════════════
    #  STATEMENTS
    # ════════════════════════════════════════════════════════

    def parse_statement(self) -> ASTNode:
        tok = self.current()

        if tok.type == TT.IF:
            return self.parse_if()
        if tok.type == TT.WHILE:
            return self.parse_while()
        if tok.type == TT.FOR:
            return self.parse_for()
        if tok.type == TT.FUNC_DEF:
            return self.parse_funcdef()
        if tok.type == TT.RETURN:
            return self.parse_return()
        if tok.type == TT.PRINT:
            return self.parse_print()
        if tok.type == TT.BREAK:
            self.advance()
            return BreakStmt(line=tok.line)
        if tok.type == TT.CONTINUE:
            self.advance()
            return ContinueStmt(line=tok.line)

        # Assignment atau Expression
        return self.parse_assign_or_expr()

    # ── if / kalo ne / yang lae ─────────────────────────────

    def parse_if(self) -> IfStmt:
        tok = self.current()
        self.expect(TT.IF)
        self.expect(TT.LPAREN,  "Setelah 't ada le' harus ada '('")
        cond = self.parse_expr()
        self.expect(TT.RPAREN,  "Harus ditutup ')'")
        self.expect(TT.COLON,   "Harus ada ':' setelah kondisi")
        then_block = self.parse_block()

        elif_clauses = []
        while self.match(TT.ELIF):
            self.advance()
            self.expect(TT.LPAREN, "Setelah 'kalo ne' harus ada '('")
            ec = self.parse_expr()
            self.expect(TT.RPAREN, "Harus ditutup ')'")
            self.expect(TT.COLON,  "Harus ada ':' setelah kondisi")
            eb = self.parse_block()
            elif_clauses.append((ec, eb))

        else_block = None
        if self.match(TT.ELSE):
            self.advance()
            self.expect(TT.COLON, "Harus ada ':' setelah 'yang lae'")
            else_block = self.parse_block()

        return IfStmt(cond, then_block, elif_clauses, else_block, tok.line)

    # ── puna pali ───────────────────────────────────────────

    def parse_while(self) -> WhileStmt:
        tok = self.current()
        self.expect(TT.WHILE)
        self.expect(TT.LPAREN,  "Setelah 'puna pali' harus ada '('")
        cond = self.parse_expr()
        self.expect(TT.RPAREN,  "Harus ditutup ')'")
        self.expect(TT.COLON,   "Harus ada ':' setelah kondisi")
        body = self.parse_block()
        return WhileStmt(cond, body, tok.line)

    # ── unto ────────────────────────────────────────────────

    def parse_for(self) -> ForStmt:
        tok = self.current()
        self.expect(TT.FOR)
        var_tok = self.expect(TT.IDENT, "Harus ada nama variabel setelah 'unto'")
        self.expect(TT.IN,    "Harus ada 'dalam' setelah variabel")
        iterable = self.parse_expr()
        self.expect(TT.COLON, "Harus ada ':' setelah iterable")
        body = self.parse_block()
        return ForStmt(var_tok.value, iterable, body, tok.line)

    # ── bua (fungsi) ────────────────────────────────────────

    def parse_funcdef(self) -> FuncDef:
        tok = self.current()
        self.expect(TT.FUNC_DEF)
        # Cek apakah ini "bua jadi" (print) — sudah ditangani di tokenizer
        name_tok = self.expect(TT.IDENT, "Harus ada nama fungsi setelah 'bua'")
        self.expect(TT.LPAREN,  "Harus ada '(' setelah nama fungsi")
        params = []
        if not self.match(TT.RPAREN):
            params.append(self.expect(TT.IDENT).value)
            while self.match(TT.COMMA):
                self.advance()
                params.append(self.expect(TT.IDENT).value)
        self.expect(TT.RPAREN,  "Harus ada ')' setelah parameter")
        self.expect(TT.COLON,   "Harus ada ':' setelah definisi fungsi")
        body = self.parse_block()
        return FuncDef(name_tok.value, params, body, tok.line)

    # ── beri bale ───────────────────────────────────────────

    def parse_return(self) -> ReturnStmt:
        tok = self.current()
        self.expect(TT.RETURN)
        value = None
        if not self.match(TT.NEWLINE, TT.EOF, TT.DEDENT):
            value = self.parse_expr()
        return ReturnStmt(value, tok.line)

    # ── bua jadi ────────────────────────────────────────────

    def parse_print(self) -> PrintStmt:
        tok = self.current()
        self.expect(TT.PRINT)
        self.expect(TT.LPAREN,  "Harus ada '(' setelah 'bua jadi'")
        args = []
        if not self.match(TT.RPAREN):
            args.append(self.parse_expr())
            while self.match(TT.COMMA):
                self.advance()
                args.append(self.parse_expr())
        self.expect(TT.RPAREN,  "Harus ada ')' penutup")
        return PrintStmt(args, tok.line)

    # ── assignment atau expression ───────────────────────────

    def parse_assign_or_expr(self) -> ASTNode:
        tok  = self.current()
        expr = self.parse_expr()

        ASSIGN_OPS = {
            TT.ASSIGN:   '=',
            TT.PLUS_EQ:  '+=',
            TT.MINUS_EQ: '-=',
            TT.STAR_EQ:  '*=',
            TT.SLASH_EQ: '/=',
        }
        if self.current().type in ASSIGN_OPS:
            if not isinstance(expr, Identifier):
                raise ParseError("Sisi kiri assignment harus identifier",
                                 tok.line, tok.col)
            op_tok = self.advance()
            value  = self.parse_expr()
            return AssignStmt(expr.name, ASSIGN_OPS[op_tok.type],
                              value, tok.line)

        return ExprStmt(expr, tok.line)

    # ── block ────────────────────────────────────────────────

    def parse_block(self) -> List[ASTNode]:
        self.skip_newlines()
        self.expect(TT.INDENT, "Harus ada indentasi (INDENT) untuk block")
        self.skip_newlines()
        stmts = []
        while not self.match(TT.DEDENT, TT.EOF):
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        if self.match(TT.DEDENT):
            self.advance()
        return stmts

    # ════════════════════════════════════════════════════════
    #  EXPRESSIONS — Recursive Descent
    # ════════════════════════════════════════════════════════

    def parse_expr(self) -> ASTNode:
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.match(TT.OR):
            op = self.advance()
            right = self.parse_and()
            left = BinOp(left, 'atau', right, op.line)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_not()
        while self.match(TT.AND):
            op = self.advance()
            right = self.parse_not()
            left = BinOp(left, 'mo dia', right, op.line)
        return left

    def parse_not(self) -> ASTNode:
        if self.match(TT.NOT):
            op = self.advance()
            return UnaryOp('trada', self.parse_not(), op.line)
        return self.parse_compare()

    def parse_compare(self) -> ASTNode:
        left = self.parse_add()
        CMP  = {TT.EQ:'==', TT.NEQ:'!=', TT.LT:'<',
                TT.GT:'>', TT.LTE:'<=', TT.GTE:'>='}
        while self.current().type in CMP:
            op  = self.advance()
            right = self.parse_add()
            left  = BinOp(left, CMP[op.type], right, op.line)
        return left

    def parse_add(self) -> ASTNode:
        left = self.parse_mul()
        while self.match(TT.PLUS, TT.MINUS):
            op    = self.advance()
            right = self.parse_mul()
            left  = BinOp(left, op.value, right, op.line)
        return left

    def parse_mul(self) -> ASTNode:
        left = self.parse_unary()
        while self.match(TT.STAR, TT.SLASH, TT.PERCENT, TT.DOUBLESLASH):
            op    = self.advance()
            right = self.parse_unary()
            left  = BinOp(left, op.value, right, op.line)
        return left

    def parse_unary(self) -> ASTNode:
        if self.match(TT.MINUS):
            op = self.advance()
            return UnaryOp('-', self.parse_unary(), op.line)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        tok = self.current()

        if tok.type == TT.NUMBER:
            self.advance()
            val = int(tok.value) if '.' not in tok.value else float(tok.value)
            return NumberLiteral(val, tok.line)

        if tok.type == TT.STRING:
            self.advance()
            return StringLiteral(tok.value, tok.line)

        if tok.type == TT.BOOL_TRUE:
            self.advance()
            return BoolLiteral(True, tok.line)

        if tok.type == TT.BOOL_FALSE:
            self.advance()
            return BoolLiteral(False, tok.line)

        if tok.type == TT.NONE_VAL:
            self.advance()
            return NoneLiteral(tok.line)

        if tok.type == TT.INPUT_KW:
            self.advance()
            self.expect(TT.LPAREN, "Harus ada '(' setelah 'beri maso'")
            prompt = None
            if not self.match(TT.RPAREN):
                prompt = self.parse_expr()
            self.expect(TT.RPAREN)
            return InputStmt(prompt, tok.line)

        if tok.type == TT.IDENT:
            self.advance()
            # Function call?
            if self.match(TT.LPAREN):
                self.advance()
                args = []
                if not self.match(TT.RPAREN):
                    args.append(self.parse_expr())
                    while self.match(TT.COMMA):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect(TT.RPAREN)
                return FuncCall(tok.value, args, tok.line)
            # Subscript?
            if self.match(TT.LBRACKET):
                self.advance()
                idx = self.parse_expr()
                self.expect(TT.RBRACKET)
                return SubscriptExpr(Identifier(tok.value, tok.line),
                                     idx, tok.line)
            return Identifier(tok.value, tok.line)

        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT.RPAREN, "Harus ada ')' penutup")
            return expr

        raise ParseError(
            f"Token tidak terduga: {tok.type.name} ({tok.value!r})",
            tok.line, tok.col)


# ════════════════════════════════════════════════════════════
#  PUBLIC API
# ════════════════════════════════════════════════════════════

def parse(source: str) -> Program:
    from .lexer import tokenize
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse()