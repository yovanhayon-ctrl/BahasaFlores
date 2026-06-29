# main.py
# Taruh di: BahasaFlores/main.py
# ============================================================
#  MAIN — Jalankan compiler + tampilkan semua stage
# ============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.lexer    import tokenize, TT
from src.parser   import Parser
from src.semantic import SemanticAnalyzer
from src.optimizer import Optimizer
from src.codegen  import CodeGenerator
from src.ast_nodes import *

WIDTH = 60

def garis():
    print("=" * WIDTH)

def section(judul):
    print("\n" + "-" * WIDTH)
    print(f"  {judul}")
    print("-" * WIDTH)


# ════════════════════════════════════════════════════════════
#  STAGE 1 — LEXER
# ════════════════════════════════════════════════════════════

def tampil_lexer(source):
    garis()
    print("  STAGE 1 — LEXER : TOKENISASI")
    garis()

    tokens = tokenize(source)

    section("SOURCE CODE (.flores)")
    for i, line in enumerate(source.split('\n'), 1):
        print(f"  {i:>3} | {line}")

    section("TOKEN YANG DIHASILKAN")
    print(f"\n  {'NO':<5} {'TIPE TOKEN':<18} {'NILAI':<22} {'LOKASI'}")
    print(f"  {'─'*5} {'─'*18} {'─'*22} {'─'*10}")

    filtered = [t for t in tokens
                if t.type not in (TT.NEWLINE, TT.INDENT,
                                  TT.DEDENT, TT.EOF)]
    for i, tok in enumerate(filtered, 1):
        loc = f"L{tok.line}:C{tok.col}"
        print(f"  {i:<5} {tok.type.name:<18} {tok.value!r:<22} {loc}")

    section("STATISTIK TOKEN")
    kw_count   = sum(1 for t in filtered if t.type in [
                     TT.IF, TT.ELIF, TT.ELSE, TT.WHILE, TT.FOR,
                     TT.BREAK, TT.CONTINUE, TT.FUNC_DEF, TT.RETURN,
                     TT.PRINT, TT.INPUT_KW, TT.AND, TT.OR, TT.NOT, TT.IN,
                     TT.BOOL_TRUE, TT.BOOL_FALSE, TT.NONE_VAL])
    id_count   = sum(1 for t in filtered if t.type == TT.IDENT)
    lit_count  = sum(1 for t in filtered if t.type in [TT.NUMBER, TT.STRING])
    op_count   = sum(1 for t in filtered if t.type in [
                     TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH,
                     TT.EQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE,
                     TT.ASSIGN, TT.PLUS_EQ, TT.MINUS_EQ])
    del_count  = sum(1 for t in filtered if t.type in [
                     TT.LPAREN, TT.RPAREN, TT.COLON, TT.COMMA])

    print(f"  Keyword BahasaFlores : {kw_count}")
    print(f"  Identifier           : {id_count}")
    print(f"  Literal              : {lit_count}")
    print(f"  Operator             : {op_count}")
    print(f"  Delimiter            : {del_count}")
    print(f"  ─────────────────────────────")
    print(f"  TOTAL                : {len(filtered)}")

    section("KEYWORD BAHASA FLORES TERDETEKSI")
    kw_map = {
        TT.IF: "t ada le", TT.ELIF: "kalo ne",
        TT.ELSE: "yang lae", TT.WHILE: "puna pali",
        TT.FOR: "unto", TT.BREAK: "barenti",
        TT.CONTINUE: "tero", TT.FUNC_DEF: "bua",
        TT.RETURN: "beri bale", TT.PRINT: "bua jadi",
        TT.INPUT_KW: "beri maso", TT.AND: "mo dia",
        TT.OR: "atau", TT.NOT: "trada", TT.IN: "dalam",
        TT.BOOL_TRUE: "beto", TT.BOOL_FALSE: "sala",
        TT.NONE_VAL: "abi le",
    }
    found = set(t.type for t in tokens if t.type in kw_map)
    for tt, kw in kw_map.items():
        status = "✓  DITEMUKAN" if tt in found else "·  tidak dipakai"
        print(f"  {status:<18} {kw}")

    return tokens


# ════════════════════════════════════════════════════════════
#  STAGE 2 — PARSER + AST
# ════════════════════════════════════════════════════════════

def tampil_parser(tokens):
    garis()
    print("  STAGE 2 — PARSER : PARSE TREE + AST")
    garis()

    parser = Parser(tokens)
    ast    = parser.parse()

    section("PARSE TREE")
    _cetak_tree(ast, 0)

    section("AST NODE SUMMARY")
    summary = {}
    _hitung_node(ast, summary)
    for nama, jumlah in sorted(summary.items()):
        print(f"  {nama:<25} {jumlah:>3} node")
    print(f"\n  Total: {sum(summary.values())} node")

    return ast


def _cetak_tree(node, indent):
    if node is None:
        return
    prefix = "  " * indent
    conn   = "├─" if indent > 0 else "┌─"
    print(f"  {prefix}{conn} {_label(node)}")
    for child in _anak(node):
        if isinstance(child, ASTNode):
            _cetak_tree(child, indent + 1)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, ASTNode):
                    _cetak_tree(item, indent + 1)


def _label(node):
    if isinstance(node, Program):      return f"[PROGRAM] {len(node.body)} stmt"
    if isinstance(node, FuncDef):      return f"[bua] {node.name}({', '.join(node.params)})"
    if isinstance(node, AssignStmt):   return f"[ASSIGN] {node.name} {node.op}"
    if isinstance(node, PrintStmt):    return f"[bua jadi] {len(node.args)} arg"
    if isinstance(node, IfStmt):       return f"[t ada le]"
    if isinstance(node, WhileStmt):    return f"[puna pali]"
    if isinstance(node, ForStmt):      return f"[unto] {node.var} dalam"
    if isinstance(node, ReturnStmt):   return f"[beri bale]"
    if isinstance(node, BreakStmt):    return f"[barenti]"
    if isinstance(node, ContinueStmt): return f"[tero]"
    if isinstance(node, ExprStmt):     return f"[EXPR]"
    if isinstance(node, BinOp):        return f"[BINOP] {node.op}"
    if isinstance(node, UnaryOp):      return f"[UNARY] {node.op}"
    if isinstance(node, FuncCall):     return f"[CALL] {node.name}()"
    if isinstance(node, Identifier):   return f"[ID] {node.name}"
    if isinstance(node, NumberLiteral):return f"[NUM] {node.value}"
    if isinstance(node, StringLiteral):return f"[STR] {node.value!r}"
    if isinstance(node, BoolLiteral):  return f"[beto/sala] {node.value}"
    if isinstance(node, NoneLiteral):  return f"[abi le]"
    if isinstance(node, InputStmt):    return f"[beri maso]"
    return f"[{type(node).__name__}]"


def _anak(node):
    if isinstance(node, Program):      return node.body
    if isinstance(node, FuncDef):      return node.body
    if isinstance(node, AssignStmt):   return [node.value]
    if isinstance(node, PrintStmt):    return node.args
    if isinstance(node, ExprStmt):     return [node.expr]
    if isinstance(node, ReturnStmt):   return [node.value] if node.value else []
    if isinstance(node, BinOp):        return [node.left, node.right]
    if isinstance(node, UnaryOp):      return [node.operand]
    if isinstance(node, FuncCall):     return node.args
    if isinstance(node, InputStmt):    return [node.prompt] if node.prompt else []
    if isinstance(node, IfStmt):
        result = [node.condition] + node.then_block
        for c, b in node.elif_clauses:
            result += [c] + b
        if node.else_block:
            result += node.else_block
        return result
    if isinstance(node, WhileStmt):    return [node.condition] + node.body
    if isinstance(node, ForStmt):      return [node.iterable] + node.body
    return []


def _hitung_node(node, summary):
    if node is None:
        return
    name = type(node).__name__
    summary[name] = summary.get(name, 0) + 1
    for child in _anak(node):
        if isinstance(child, ASTNode):
            _hitung_node(child, summary)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, ASTNode):
                    _hitung_node(item, summary)


# ════════════════════════════════════════════════════════════
#  STAGE 3 — SEMANTIC
# ════════════════════════════════════════════════════════════

def tampil_semantic(ast):
    garis()
    print("  STAGE 3 — SEMANTIC ANALYZER")
    garis()

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    section("SYMBOL TABLE")
    scope = analyzer.global_scope
    print(f"\n  Scope: [{scope.scope_name}]")
    print(f"  {'NAMA':<20} {'TIPE':<15} {'INFO'}")
    print(f"  {'─'*20} {'─'*15} {'─'*15}")
    for nama, info in scope.symbols.items():
        tipe   = info.get('type', '?')
        detail = str(info.get('params', info.get('line', '-')))
        print(f"  {nama:<20} {tipe:<15} {detail}")

    section("HASIL ANALISIS")
    if analyzer.errors:
        for e in analyzer.errors:
            print(f"  ✗ {e}")
        return None

    print("  ✓ Tidak ada error semantik")
    print("  ✓ Semua variabel terdefinisi")
    print("  ✓ Semua fungsi terdefinisi")
    print("  ✓ Scope function/loop valid")
    return analyzer


# ════════════════════════════════════════════════════════════
#  STAGE 4 — OPTIMIZER
# ════════════════════════════════════════════════════════════

def tampil_optimizer(ast):
    garis()
    print("  STAGE 4 — CODE OPTIMIZER")
    garis()

    optimizer = Optimizer()

    before = {}
    _hitung_node(ast, before)

    opt_ast = optimizer.optimize(ast)

    after = {}
    _hitung_node(opt_ast, after)

    section("HASIL OPTIMASI")
    print(f"  Node sebelum : {sum(before.values())}")
    print(f"  Node sesudah : {sum(after.values())}")
    print(f"  Direduksi    : {sum(before.values()) - sum(after.values())}")
    print(f"  Optimasi     : {optimizer.changes}x")

    section("TEKNIK YANG DIPAKAI")
    print("  1. Constant Folding      — 2+3 -> 5")
    print("  2. Constant Propagation  — x=5; y=x -> y=5")
    print("  3. Dead Code Elimination — t ada le(sala) -> hapus")
    print("  4. Algebraic Simplify    — x*1 -> x")

    return opt_ast


# ════════════════════════════════════════════════════════════
#  STAGE 5 — CODE GENERATION
# ════════════════════════════════════════════════════════════

def tampil_codegen(opt_ast, filename):
    garis()
    print("  STAGE 5 — CODE GENERATION")
    garis()

    codegen = CodeGenerator()
    py_code = codegen.generate(opt_ast)
    py_file = f"{filename}.py"

    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(py_code)

    section("GENERATED PYTHON CODE")
    lines = py_code.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"  {i:>4} | {line}")

    section("INFO FILE")
    print(f"  File   : {py_file}")
    print(f"  Ukuran : {os.path.getsize(py_file)} bytes")
    print(f"  Baris  : {len(lines)}")

    return py_code, py_file


# ════════════════════════════════════════════════════════════
#  STAGE 6 — PACKAGING
# ════════════════════════════════════════════════════════════

def tampil_packaging(py_file, filename):
    import subprocess
    garis()
    print("  STAGE 6 — PACKAGING -> .exe")
    garis()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", filename,
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--clean",
        py_file
    ]

    section("BUILD PROCESS")
    print("  Sedang build .exe, harap tunggu...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        exe  = f"dist/{filename}.exe"
        size = os.path.getsize(exe) // 1024 if os.path.exists(exe) else 0
        print(f"  ✓ Build BERHASIL!")
        print(f"  ✓ File  : {exe}")
        print(f"  ✓ Ukuran: {size} KB")
    else:
        print("  ✗ Build GAGAL!")
        print(result.stderr[-500:])


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    args   = sys.argv[1:]
    exe    = "--exe" in args
    files  = [a for a in args if not a.startswith("--")]
    target = files[0] if files else "tests/ujian_akhir.flores"

    if not os.path.exists(target):
        print(f"File tidak ditemukan: {target}")
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        source = f.read()

    filename = os.path.splitext(os.path.basename(target))[0]

    garis()
    print("  BAHASAFLORES COMPILER v1.0 — MAIN")
    print(f"  File  : {target}")
    print(f"  Output: {filename}.py + dist/{filename}.exe")
    garis()

    tokens          = tampil_lexer(source)
    ast             = tampil_parser(tokens)
    sem             = tampil_semantic(ast)

    if sem is None:
        print("\n  Kompilasi dihentikan — ada error semantik!")
        sys.exit(1)

    opt_ast         = tampil_optimizer(ast)
    py_code, py_file= tampil_codegen(opt_ast, filename)

    if exe:
        tampil_packaging(py_file, filename)

    garis()
    print("  SEMUA STAGE SELESAI!")
    print(f"  Jalankan: python {filename}.py")
    if exe:
        print(f"  Atau    : dist\\{filename}.exe")
    garis()


if __name__ == "__main__":
    main()