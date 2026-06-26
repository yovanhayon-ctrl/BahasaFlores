# trace_compiler.py
# ============================================================
#  TRACE COMPILER — Debug Visual Semua Stage
#  Usage:
#    python trace_compiler.py tests/contoh.flores
#    python trace_compiler.py tests/contoh.flores --exe
# ============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.lexer     import tokenize, TT
from src.parser    import Parser
from src.semantic  import SemanticAnalyzer
from src.optimizer import Optimizer
from src.codegen   import CodeGenerator
from src.ast_nodes import *


# ════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ════════════════════════════════════════════════════════════

WIDTH = 65

def header(title: str):
    print("\n" + "═" * WIDTH)
    pad = (WIDTH - len(title) - 2) // 2
    print("═" * pad + f" {title} " + "═" * pad)
    print("═" * WIDTH)

def section(title: str):
    print(f"\n{'─' * WIDTH}")
    print(f"  {title}")
    print(f"{'─' * WIDTH}")

def ok(msg: str):
    print(f"  ✓  {msg}")

def info(msg: str):
    print(f"  │  {msg}")

def err(msg: str):
    print(f"  ✗  {msg}")


# ════════════════════════════════════════════════════════════
#  STAGE 1 — LEXER TRACE
# ════════════════════════════════════════════════════════════

def trace_lexer(source: str):
    header("STAGE 1 : L E X E R")

    tokens = tokenize(source)

    categories = {
        "KEYWORD"   : [TT.IF, TT.ELIF, TT.ELSE, TT.WHILE, TT.FOR,
                       TT.BREAK, TT.CONTINUE, TT.FUNC_DEF, TT.RETURN,
                       TT.PRINT, TT.INPUT_KW, TT.AND, TT.OR, TT.NOT, TT.IN],
        "LITERAL"   : [TT.NUMBER, TT.STRING, TT.BOOL_TRUE,
                       TT.BOOL_FALSE, TT.NONE_VAL],
        "IDENTIFIER": [TT.IDENT],
        "OPERATOR"  : [TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH,
                       TT.PERCENT, TT.DOUBLESLASH, TT.POWER,
                       TT.EQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE,
                       TT.ASSIGN, TT.PLUS_EQ, TT.MINUS_EQ,
                       TT.STAR_EQ, TT.SLASH_EQ],
        "DELIMITER" : [TT.LPAREN, TT.RPAREN, TT.LBRACKET,
                       TT.RBRACKET, TT.COLON, TT.COMMA, TT.DOT],
        "STRUCTURE" : [TT.NEWLINE, TT.INDENT, TT.DEDENT, TT.EOF],
    }

    counts = {k: 0 for k in categories}
    for tok in tokens:
        for cat, types in categories.items():
            if tok.type in types:
                counts[cat] += 1
                break

    section("Token Stream (filtered — tanpa NEWLINE/INDENT/DEDENT)")
    print(f"\n  {'NO':<5} {'TYPE':<18} {'VALUE':<22} {'LOC'}")
    print(f"  {'─'*5} {'─'*18} {'─'*22} {'─'*12}")

    filtered = [t for t in tokens
                if t.type not in (TT.NEWLINE, TT.INDENT,
                                  TT.DEDENT, TT.EOF)]
    for i, tok in enumerate(filtered, 1):
        loc = f"L{tok.line}:C{tok.col}"
        print(f"  {i:<5} {tok.type.name:<18} {tok.value!r:<22} {loc}")

    section("Statistik Token")
    total = len(tokens)
    for cat, count in counts.items():
        bar = "█" * count + "░" * max(0, 30 - count)
        print(f"  {cat:<12} {count:>4}  {bar[:30]}")
    print(f"\n  {'TOTAL':<12} {total:>4}  token")

    section("Keyword BahasaFlores yang Terdeteksi")
    kw_map = {
        TT.IF       : "t ada le",
        TT.ELIF     : "kalo ne",
        TT.ELSE     : "yang lae",
        TT.WHILE    : "puna pali",
        TT.FOR      : "unto",
        TT.BREAK    : "barenti",
        TT.CONTINUE : "tero",
        TT.FUNC_DEF : "bua",
        TT.RETURN   : "beri bale",
        TT.PRINT    : "bua jadi",
        TT.INPUT_KW : "beri maso",
        TT.AND      : "mo dia",
        TT.OR       : "atau",
        TT.NOT      : "trada",
        TT.IN       : "dalam",
        TT.BOOL_TRUE : "beto",
        TT.BOOL_FALSE: "sala",
        TT.NONE_VAL : "abi le",
    }
    found_kw = set()
    for tok in tokens:
        if tok.type in kw_map:
            found_kw.add(tok.type)

    for tt, kw in kw_map.items():
        status = "✓" if tt in found_kw else "·"
        print(f"  {status}  {kw:<15}")

    return tokens


# ════════════════════════════════════════════════════════════
#  STAGE 2 — PARSER + AST TRACE
# ════════════════════════════════════════════════════════════

def trace_parser(tokens):
    header("STAGE 2 : P A R S E R  +  A S T")

    parser = Parser(tokens)
    ast    = parser.parse()

    section("Parse Tree (Call Stack Simulation)")
    _print_parse_tree(ast, indent=0)

    section("AST Node Summary")
    summary = {}
    _count_nodes(ast, summary)
    for node_type, count in sorted(summary.items()):
        print(f"  ─ {node_type:<25} {count:>3} node")

    ok(f"Total: {sum(summary.values())} node dalam AST")
    return ast


def _print_parse_tree(node, indent=0):
    if node is None:
        return
    prefix    = "  " * indent
    connector = "├─" if indent > 0 else "┌─"
    node_str  = _node_label(node)
    print(f"  {prefix}{connector} {node_str}")
    children = _get_children(node)
    for child in children:
        if isinstance(child, ASTNode):
            _print_parse_tree(child, indent + 1)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, ASTNode):
                    _print_parse_tree(item, indent + 1)


def _node_label(node) -> str:
    if isinstance(node, Program):
        return f"[PROGRAM] {len(node.body)} statements"
    if isinstance(node, FuncDef):
        return f"[FUNC_DEF] bua {node.name}({', '.join(node.params)})"
    if isinstance(node, AssignStmt):
        return f"[ASSIGN] {node.name} {node.op} ..."
    if isinstance(node, PrintStmt):
        return f"[PRINT] bua jadi ({len(node.args)} arg)"
    if isinstance(node, IfStmt):
        return f"[IF] t ada le ..."
    if isinstance(node, WhileStmt):
        return f"[WHILE] puna pali ..."
    if isinstance(node, ForStmt):
        return f"[FOR] unto {node.var} dalam ..."
    if isinstance(node, ReturnStmt):
        return f"[RETURN] beri bale"
    if isinstance(node, BreakStmt):
        return f"[BREAK] barenti"
    if isinstance(node, ContinueStmt):
        return f"[CONTINUE] tero"
    if isinstance(node, ExprStmt):
        return f"[EXPR_STMT]"
    if isinstance(node, BinOp):
        return f"[BINOP] {node.op}"
    if isinstance(node, UnaryOp):
        return f"[UNARY] {node.op}"
    if isinstance(node, FuncCall):
        return f"[CALL] {node.name}({len(node.args)} arg)"
    if isinstance(node, Identifier):
        return f"[ID] {node.name}"
    if isinstance(node, NumberLiteral):
        return f"[NUM] {node.value}"
    if isinstance(node, StringLiteral):
        return f"[STR] {node.value!r}"
    if isinstance(node, BoolLiteral):
        return f"[BOOL] {'beto' if node.value else 'sala'}"
    if isinstance(node, NoneLiteral):
        return f"[NONE] abi le"
    if isinstance(node, InputStmt):
        return f"[INPUT] beri maso"
    if isinstance(node, SubscriptExpr):
        return f"[SUBSCRIPT]"
    return f"[{type(node).__name__}]"


def _get_children(node) -> list:
    result = []
    if isinstance(node, Program):
        result = node.body
    elif isinstance(node, FuncDef):
        result = node.body
    elif isinstance(node, AssignStmt):
        result = [node.value]
    elif isinstance(node, PrintStmt):
        result = node.args
    elif isinstance(node, ExprStmt):
        result = [node.expr]
    elif isinstance(node, IfStmt):
        result = [node.condition] + node.then_block
        for cond, block in node.elif_clauses:
            result += [cond] + block
        if node.else_block:
            result += node.else_block
    elif isinstance(node, WhileStmt):
        result = [node.condition] + node.body
    elif isinstance(node, ForStmt):
        result = [node.iterable] + node.body
    elif isinstance(node, ReturnStmt):
        if node.value:
            result = [node.value]
    elif isinstance(node, BinOp):
        result = [node.left, node.right]
    elif isinstance(node, UnaryOp):
        result = [node.operand]
    elif isinstance(node, FuncCall):
        result = node.args
    elif isinstance(node, InputStmt):
        if node.prompt:
            result = [node.prompt]
    elif isinstance(node, SubscriptExpr):
        result = [node.obj, node.index]
    return result


def _count_nodes(node, summary: dict):
    if node is None:
        return
    name = type(node).__name__
    summary[name] = summary.get(name, 0) + 1
    for child in _get_children(node):
        if isinstance(child, ASTNode):
            _count_nodes(child, summary)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, ASTNode):
                    _count_nodes(item, summary)


# ════════════════════════════════════════════════════════════
#  STAGE 3 — SEMANTIC ANALYZER TRACE
# ════════════════════════════════════════════════════════════

def trace_semantic(ast):
    header("STAGE 3 : S E M A N T I C  A N A L Y Z E R")

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    section("Symbol Table — Global Scope")
    _print_scope(analyzer.global_scope)

    section("Hasil Analisis")
    if analyzer.errors:
        err(f"Ditemukan {len(analyzer.errors)} error:")
        for e in analyzer.errors:
            print(f"     {e}")
        return None
    else:
        ok("Tidak ada error semantik")
        ok("Semua variabel terdefinisi dengan benar")
        ok("Semua fungsi terdefinisi dengan benar")
        ok("break/continue hanya dalam loop")
        ok("return hanya dalam fungsi")

    return analyzer


def _print_scope(scope, depth=0):
    pad = "  " * depth
    print(f"\n  {pad}Scope: [{scope.scope_name}]")
    print(f"  {pad}{'─'*40}")
    if not scope.symbols:
        print(f"  {pad}  (kosong)")
    for name, info_data in scope.symbols.items():
        kind = info_data.get('type', '?')
        line = info_data.get('line', '-')
        if kind == 'function':
            params = info_data.get('params', [])
            print(f"  {pad}  f  {name:<20} params={params}")
        elif kind == 'builtin':
            print(f"  {pad}  *  {name:<20} [built-in]")
        else:
            print(f"  {pad}  -  {name:<20} baris {line}")


# ════════════════════════════════════════════════════════════
#  STAGE 4 — OPTIMIZER TRACE
# ════════════════════════════════════════════════════════════

def trace_optimizer(ast):
    header("STAGE 4 : O P T I M I Z E R")

    optimizer = Optimizer()

    section("Sebelum Optimasi — AST Node Count")
    before = {}
    _count_nodes(ast, before)
    for k, v in sorted(before.items()):
        print(f"  ─ {k:<25} {v:>3}")
    total_before = sum(before.values())

    opt_ast = optimizer.optimize(ast)

    section("Setelah Optimasi — AST Node Count")
    after = {}
    _count_nodes(opt_ast, after)
    for k, v in sorted(after.items()):
        print(f"  ─ {k:<25} {v:>3}")
    total_after = sum(after.values())

    section("Ringkasan Optimasi")
    ok(f"Jumlah optimasi dilakukan : {optimizer.changes}")
    ok(f"Node sebelum optimasi     : {total_before}")
    ok(f"Node setelah optimasi     : {total_after}")
    ok(f"Node direduksi            : {total_before - total_after}")

    section("Teknik Optimasi yang Dipakai")
    info("1. Constant Folding       — 2 + 3  ->  5")
    info("2. Constant Propagation   — x=5; y=x+1  ->  y=6")
    info("3. Dead Code Elimination  — t ada le (sala): ... -> dihapus")
    info("4. Algebraic Simplify     — x*1 -> x,  x+0 -> x")

    return opt_ast


# ════════════════════════════════════════════════════════════
#  STAGE 5 — CODE GENERATION TRACE
# ════════════════════════════════════════════════════════════

def trace_codegen(opt_ast, filename: str):
    header("STAGE 5 : C O D E  G E N E R A T I O N")

    codegen = CodeGenerator()
    py_code = codegen.generate(opt_ast)
    py_file = f"{filename}.py"

    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(py_code)

    section("Generated Python Code")
    lines = py_code.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"  {i:>4} | {line}")

    section("File Output")
    ok(f"Python source : {py_file}")
    ok(f"Ukuran file   : {os.path.getsize(py_file)} bytes")
    ok(f"Jumlah baris  : {len(lines)} baris")

    return py_code, py_file


# ════════════════════════════════════════════════════════════
#  STAGE 6 — PACKAGING TRACE
# ════════════════════════════════════════════════════════════

def trace_packaging(py_file: str, filename: str):
    header("STAGE 6 : P A C K A G I N G  ->  .exe")

    import subprocess

    section("PyInstaller Command")
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
    info("Command: " + " ".join(cmd))

    section("Build Log")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        exe_path = f"dist/{filename}.exe"
        size_kb  = os.path.getsize(exe_path) // 1024 \
                   if os.path.exists(exe_path) else 0
        ok("Build BERHASIL!")
        ok(f"Executable : {exe_path}")
        ok(f"Ukuran     : {size_kb} KB")
        ok(f"Cara run   : dist\\{filename}.exe")
    else:
        err("Build GAGAL!")
        print(result.stderr[-800:])


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    args  = sys.argv[1:]
    exe   = "--exe" in args
    files = [a for a in args if not a.startswith("--")]

    if not files:
        print("\nUsage:")
        print("  python trace_compiler.py <file.flores>")
        print("  python trace_compiler.py <file.flores> --exe")
        print("\nContoh:")
        print("  python trace_compiler.py tests/contoh.flores --exe")
        sys.exit(0)

    filepath = files[0]
    if not os.path.exists(filepath):
        print(f"  File tidak ditemukan: {filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    filename = os.path.splitext(os.path.basename(filepath))[0]

    print("\n" + "=" * WIDTH)
    print("   BahasaFlores Compiler — TRACE MODE")
    print(f"   File   : {filepath}")
    print(f"   Output : {filename}.py  +  dist/{filename}.exe")
    print("=" * WIDTH)

    # Jalankan semua stage
    tokens           = trace_lexer(source)
    ast              = trace_parser(tokens)
    sem              = trace_semantic(ast)

    if sem is None:
        print("\n  Kompilasi dihentikan karena error semantik.")
        sys.exit(1)

    opt_ast          = trace_optimizer(ast)
    py_code, py_file = trace_codegen(opt_ast, filename)

    if exe:
        trace_packaging(py_file, filename)

    # Final summary
    header("S E L E S A I")

    pkg_status = f"✓  dist/{filename}.exe" if exe else "─  (skip, tambahkan --exe)"
    run_exe    = f"dist\\{filename}.exe"    if exe else "(jalankan dengan --exe untuk build)"

    print("")
    print("  Pipeline BahasaFlores Compiler:")
    print("")
    print("  [1] LEXER          ✓  Token teridentifikasi")
    print("  [2] PARSER         ✓  AST terbangun")
    print("  [3] SEMANTIC       ✓  Tidak ada error")
    print("  [4] OPTIMIZER      ✓  Optimasi selesai")
    print(f"  [5] CODE GEN       ✓  {filename}.py digenerate")
    print(f"  [6] PACKAGING      {pkg_status}")
    print("")
    print("  Untuk menjalankan hasil kompilasi:")
    print(f"    python {filename}.py")
    print(f"    {run_exe}")
    print("")


if __name__ == "__main__":
    main()