# src/compiler.py
# ============================================================
#  COMPILER PIPELINE — Orchestrator semua stage
# ============================================================

import os
import subprocess
import sys
from .lexer    import tokenize, print_tokens
from .parser   import Parser
from .semantic import SemanticAnalyzer
from .optimizer import Optimizer
from .codegen  import CodeGenerator
from .ast_nodes import ASTNode 

class CompilerPipeline:
    def __init__(self, source: str, filename: str = "output",
                 verbose: bool = False):
        self.source   = source
        self.filename = filename
        self.verbose  = verbose
        self.tokens   = None
        self.ast      = None
        self.opt_ast  = None
        self.py_code  = None

    def run(self, build_exe: bool = False) -> bool:
        print("\n" + "═"*55)
        print("   BahasaFlores Compiler v1.0")
        print("═"*55)

        try:
            # ── Stage 1: LEXER ──────────────────────────────
            print("\n[1/5] LEXER — Tokenisasi...")
            self.tokens = tokenize(self.source)
            if self.verbose:
                print_tokens(self.tokens)
            print(f"      ✓ {len(self.tokens)} token dihasilkan")

            # ── Stage 2: PARSER ─────────────────────────────
            print("\n[2/5] PARSER — Membangun AST...")
            parser   = Parser(self.tokens)
            self.ast = parser.parse()
            if self.verbose:
                self._print_ast(self.ast)
            print(f"      ✓ {len(self.ast.body)} statement di-parse")

            # ── Stage 3: SEMANTIC ───────────────────────────
            print("\n[3/5] SEMANTIC ANALYZER...")
            analyzer = SemanticAnalyzer()
            analyzer.analyze(self.ast)
            if analyzer.errors:
                print("\n  ✗ Ditemukan error semantik:")
                for err in analyzer.errors:
                    print(f"    {err}")
                return False
            print("      ✓ Tidak ada error semantik")
            if self.verbose:
                self._print_symbol_table(analyzer.global_scope)

            # ── Stage 4: OPTIMIZER ──────────────────────────
            print("\n[4/5] CODE OPTIMIZER...")
            optimizer    = Optimizer()
            self.opt_ast = optimizer.optimize(self.ast)
            print(f"      ✓ {optimizer.changes} optimasi dilakukan")

            # ── Stage 5: CODE GENERATION ────────────────────
            print("\n[5/5] CODE GENERATION...")
            codegen       = CodeGenerator()
            self.py_code  = codegen.generate(self.opt_ast)
            py_file       = f"{self.filename}.py"
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(self.py_code)
            print(f"      ✓ File Python: {py_file}")
            if self.verbose:
                print("\n--- Generated Python ---")
                print(self.py_code)
                print("------------------------")

            # ── Stage 6 (opsional): PACKAGING ──────────────
            if build_exe:
                self._package_exe(py_file)

            print("\n" + "═"*55)
            print("   KOMPILASI SELESAI! ✓")
            print("═"*55 + "\n")
            return True

        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def _package_exe(self, py_file: str):
        print("\n[+] PACKAGING → .exe (PyInstaller)...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller",
                 "--onefile",
                 "--name", self.filename,
                 "--distpath", "dist",
                 "--workpath", "build",
                 "--specpath", "build",
                 "--clean",
                 py_file],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"    ✓ Executable: dist/{self.filename}.exe")
            else:
                print("    ✗ PyInstaller error:")
                print(result.stderr[-500:])
        except FileNotFoundError:
            print("    ✗ PyInstaller tidak ditemukan.")
            print("      Jalankan: pip install pyinstaller")

    def _print_ast(self, node, indent=0):
        prefix = "  " * indent + "├─ "
        print(f"{prefix}{node}")
        for attr in ['body', 'then_block', 'else_block',
                     'body', 'args', 'params']:
            children = getattr(node, attr, None)
            if children and isinstance(children, list):
                for child in children:
                    if isinstance(child, ASTNode):
                        self._print_ast(child, indent+1)

    def _print_symbol_table(self, scope, depth=0):
        pad = "  " * depth
        print(f"\n{pad}Scope: [{scope.scope_name}]")
        for name, info in scope.symbols.items():
            print(f"{pad}  {name}: {info}")