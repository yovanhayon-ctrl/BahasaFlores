# flores.py
# ============================================================
#  ENTRY POINT — BahasaFlores Compiler CLI
#  Usage:
#    python flores.py program.flores
#    python flores.py program.flores --exe
#    python flores.py program.flores --verbose
#    python flores.py program.flores --exe --verbose
# ============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.compiler import CompilerPipeline


def main():
    args    = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    exe     = "--exe" in args or "-e" in args
    files   = [a for a in args if not a.startswith("-")]

    if not files:
        print("BahasaFlores Compiler v1.0")
        print("")
        print("Usage:")
        print("  python flores.py <file.flores>")
        print("  python flores.py <file.flores> --exe")
        print("  python flores.py <file.flores> --verbose")
        print("  python flores.py <file.flores> --exe --verbose")
        print("")
        print("Contoh:")
        print("  python flores.py program.flores --exe --verbose")
        sys.exit(0)

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"✗ File tidak ditemukan: {filepath}")
            sys.exit(1)

        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        basename = os.path.splitext(os.path.basename(filepath))[0]
        pipeline = CompilerPipeline(source, filename=basename, verbose=verbose)
        success  = pipeline.run(build_exe=exe)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()