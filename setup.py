import os

# Daftar folder yang ingin dibuat
folders = ['src', 'tests', 'dist', 'docs']

# Daftar file yang ingin dibuat beserta path-nya
files = [
    'src/__init__.py', 
    'src/lexer.py', 
    'src/ast_nodes.py', 
    'src/parser.py', 
    'src/semantic.py', 
    'src/optimizer.py', 
    'src/codegen.py',
    'tests/contoh.flores', 
    'tests/test_lexer.py', 
    'tests/ujian_akhir.flores',
    'docs/dokumentasi.md',
    'flores.py', 
    'trace_compiler.py', 
    'REFERENSI_BAHASA.md'
]

# Eksekusi pembuatan folder
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Eksekusi pembuatan file (hanya dibuat jika belum ada)
for file in files:
    if not os.path.exists(file):
        open(file, 'w').close()

print("✅ Semua struktur folder dan file berhasil dibuat!")