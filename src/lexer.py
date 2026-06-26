# src/lexer.py
# ============================================================
#  LEXER — Tokenizer BahasaFlores
#  Multi-kata keyword dikenali dengan greedy matching
# ============================================================

import re
from enum import Enum, auto
from typing import List, NamedTuple


# ════════════════════════════════════════════════════════════
#  TOKEN TYPES
# ════════════════════════════════════════════════════════════

class TT(Enum):
    # Literals
    NUMBER      = auto()
    STRING      = auto()
    BOOL_TRUE   = auto()   # beto
    BOOL_FALSE  = auto()   # sala
    NONE_VAL    = auto()   # abi le

    # Keywords — Control Flow
    IF          = auto()   # t ada le
    ELIF        = auto()   # kalo ne
    ELSE        = auto()   # yang lae

    # Keywords — Loop
    WHILE       = auto()   # puna pali
    FOR         = auto()   # unto
    BREAK       = auto()   # barenti
    CONTINUE    = auto()   # tero

    # Keywords — Function
    FUNC_DEF    = auto()   # bua
    RETURN      = auto()   # beri bale

    # Keywords — Built-in
    PRINT       = auto()   # bua jadi
    INPUT_KW    = auto()   # beri maso

    # Keywords — Logical
    AND         = auto()   # mo dia
    OR          = auto()   # atau
    NOT         = auto()   # trada

    # Keywords — Misc
    IN          = auto()   # dalam

    # Identifiers
    IDENT       = auto()

    # Operators — Arithmetic
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    PERCENT     = auto()   # %
    DOUBLESLASH = auto()   # //
    POWER       = auto()   # **

    # Operators — Comparison
    EQ          = auto()   # ==
    NEQ         = auto()   # !=
    LT          = auto()   # 
    GT          = auto()   # >
    LTE         = auto()   # <=
    GTE         = auto()   # >=

    # Operators — Assignment
    ASSIGN      = auto()   # =
    PLUS_EQ     = auto()   # +=
    MINUS_EQ    = auto()   # -=
    STAR_EQ     = auto()   # *=
    SLASH_EQ    = auto()   # /=

    # Delimiters
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACKET    = auto()   # [
    RBRACKET    = auto()   # ]
    COLON       = auto()   # :
    COMMA       = auto()   # ,
    DOT         = auto()   # .

    # Structure
    NEWLINE     = auto()
    INDENT      = auto()
    DEDENT      = auto()
    EOF         = auto()

    # Special
    COMMENT     = auto()


# ════════════════════════════════════════════════════════════
#  TOKEN
# ════════════════════════════════════════════════════════════

class Token(NamedTuple):
    type: TT
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"


# ════════════════════════════════════════════════════════════
#  KEYWORD TABLE
#  Urutan penting: keyword panjang dulu sebelum yang pendek
#  supaya greedy matching bekerja benar
# ════════════════════════════════════════════════════════════

MULTI_WORD_KEYWORDS = [
    # 3 kata dulu
    ("t ada le",   TT.IF),
    ("beri bale",  TT.RETURN),
    ("beri maso",  TT.INPUT_KW),
    ("bua jadi",   TT.PRINT),
    ("puna pali",  TT.WHILE),
    ("yang lae",   TT.ELSE),
    ("abi le",     TT.NONE_VAL),
    # 2 kata
    ("kalo ne",    TT.ELIF),
    ("mo dia",     TT.AND),
]

SINGLE_WORD_KEYWORDS = {
    "unto":    TT.FOR,
    "barenti": TT.BREAK,
    "tero":    TT.CONTINUE,
    "bua":     TT.FUNC_DEF,
    "atau":    TT.OR,
    "trada":   TT.NOT,
    "beto":    TT.BOOL_TRUE,
    "sala":    TT.BOOL_FALSE,
    "dalam":   TT.IN,
}


# ════════════════════════════════════════════════════════════
#  LEXER CLASS
# ════════════════════════════════════════════════════════════

class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[LexerError] Baris {line}, Kolom {col}: {msg}")
        self.line = line
        self.col  = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.col    = 1
        self.tokens: List[Token] = []

    # ── helpers ─────────────────────────────────────────────

    def peek(self, offset=0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else '\0'

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col   = 1
        else:
            self.col  += 1
        return ch

    def remaining(self) -> str:
        return self.source[self.pos:]

    def add(self, tt: TT, value: str, line: int, col: int):
        self.tokens.append(Token(tt, value, line, col))

    # ── indentation ─────────────────────────────────────────

    def tokenize_indentation(self) -> List[Token]:
        """
        Konversi raw token stream jadi stream dengan
        INDENT / DEDENT yang benar (gaya Python).
        """
        raw = self._tokenize_raw()
        return self._inject_indent_dedent(raw)

    def _tokenize_raw(self) -> List[Token]:
        """Scan semua token TANPA INDENT/DEDENT dulu."""
        tokens = []

        while self.pos < len(self.source):
            start_line = self.line
            start_col  = self.col
            ch         = self.peek()

            # ── skip spasi horizontal (bukan newline) ───────
            if ch in (' ', '\t'):
                self.advance()
                continue

            # ── komentar ────────────────────────────────────
            if ch == '#':
                while self.pos < len(self.source) and self.peek() != '\n':
                    self.advance()
                continue

            # ── newline ─────────────────────────────────────
            if ch == '\n':
                self.advance()
                tokens.append(Token(TT.NEWLINE, '\\n', start_line, start_col))
                # Hitung indentasi baris berikutnya
                indent = 0
                while self.pos < len(self.source) and self.peek() in (' ', '\t'):
                    indent += 1 if self.peek() == ' ' else 4
                    self.advance()
                # Simpan level indentasi sebagai metadata di value
                tokens.append(Token(TT.NEWLINE, f'INDENT_LEVEL:{indent}',
                                    self.line, 1))
                continue

            # ── string ──────────────────────────────────────
            if ch in ('"', "'"):
                tok = self._scan_string(start_line, start_col)
                tokens.append(tok)
                continue

            # ── angka ───────────────────────────────────────
            if ch.isdigit():
                tok = self._scan_number(start_line, start_col)
                tokens.append(tok)
                continue

            # ── identifier / keyword ─────────────────────────
            if ch.isalpha() or ch == '_':
                tok = self._scan_word(start_line, start_col)
                tokens.append(tok)
                continue

            # ── operator & delimiter ─────────────────────────
            tok = self._scan_operator(start_line, start_col)
            if tok:
                tokens.append(tok)
                continue

            raise LexerError(f"Karakter tidak dikenal: {ch!r}",
                             start_line, start_col)

        tokens.append(Token(TT.EOF, '', self.line, self.col))
        return tokens

    def _scan_string(self, line, col) -> Token:
        quote = self.advance()
        buf   = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch == '\\':
                self.advance()
                esc = self.advance()
                buf.append({'n': '\n', 't': '\t', '\\': '\\',
                            '"': '"', "'": "'"}.get(esc, esc))
            elif ch == quote:
                self.advance()
                break
            elif ch == '\n':
                raise LexerError("String tidak ditutup", line, col)
            else:
                buf.append(self.advance())
        return Token(TT.STRING, ''.join(buf), line, col)

    def _scan_number(self, line, col) -> Token:
        buf = []
        while self.pos < len(self.source) and self.peek().isdigit():
            buf.append(self.advance())
        if self.pos < len(self.source) and self.peek() == '.':
            buf.append(self.advance())
            while self.pos < len(self.source) and self.peek().isdigit():
                buf.append(self.advance())
        return Token(TT.NUMBER, ''.join(buf), line, col)

    def _scan_word(self, line, col) -> Token:
        """
        Greedy match: coba multi-word keyword dulu,
        fallback ke single-word, fallback ke identifier.
        """
        # Ambil semua kata (spasi + alfanumerik) dari posisi ini
        # untuk keperluan matching multi-kata
        rest = self.remaining()

        # Coba multi-word keyword
        for kw, tt in MULTI_WORD_KEYWORDS:
            if rest.startswith(kw):
                # Pastikan batas kata benar
                end_idx = len(kw)
                next_ch = rest[end_idx] if end_idx < len(rest) else '\0'
                if not (next_ch.isalnum() or next_ch == '_'):
                    # Consume semua karakter keyword
                    for _ in kw:
                        if self.peek() != ' ':
                            self.advance()
                        else:
                            self.advance()
                    # Koreksi: advance sudah dilakukan per karakter
                    # Reset dan re-advance dengan benar
                    # (kita lakukan via pos langsung)
                    self.pos  = self.pos - len(kw) + len(kw)
                    self.col += len(kw)
                    return Token(tt, kw, line, col)

        # Re-scan dengan cara aman: advance per karakter
        # Reset ke posisi awal kata
        buf = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch.isalnum() or ch == '_':
                buf.append(self.advance())
            else:
                break
        word = ''.join(buf)

        # Cek multi-word: setelah kata pertama mungkin ada spasi + kata lagi
        # Coba gabungkan dengan kata berikutnya
        result = self._try_extend_keyword(word, line, col)
        if result:
            return result

        # Single-word keyword?
        if word in SINGLE_WORD_KEYWORDS:
            return Token(SINGLE_WORD_KEYWORDS[word], word, line, col)

        # Identifier
        return Token(TT.IDENT, word, line, col)

    def _try_extend_keyword(self, first_word: str, line: int, col: int):
        """
        Setelah scan kata pertama, coba extend ke multi-word keyword.
        Contoh: scan 't', lalu coba 't ada le'.
        """
        saved_pos  = self.pos
        saved_col  = self.col
        saved_line = self.line

        # Kumpulkan kandidat dari sisa source
        candidate = first_word
        for kw, tt in MULTI_WORD_KEYWORDS:
            if kw.startswith(first_word) and kw != first_word:
                suffix = kw[len(first_word):]
                # suffix dimulai dengan spasi
                rest = self.source[self.pos:]
                if rest.startswith(suffix):
                    end_idx = len(suffix)
                    next_ch = rest[end_idx] if end_idx < len(rest) else '\0'
                    if not (next_ch.isalnum() or next_ch == '_'):
                        # Consume suffix
                        for ch in suffix:
                            self.advance()
                        return Token(tt, kw, line, col)

        # Tidak cocok, kembalikan None
        return None

    def _scan_operator(self, line, col) -> Token:
        ch = self.peek()

        two = self.source[self.pos:self.pos+2]
        op2 = {
            '**': TT.POWER,
            '//': TT.DOUBLESLASH,
            '==': TT.EQ,
            '!=': TT.NEQ,
            '<=': TT.LTE,
            '>=': TT.GTE,
            '+=': TT.PLUS_EQ,
            '-=': TT.MINUS_EQ,
            '*=': TT.STAR_EQ,
            '/=': TT.SLASH_EQ,
        }
        if two in op2:
            self.advance(); self.advance()
            return Token(op2[two], two, line, col)

        op1 = {
            '+': TT.PLUS,   '-': TT.MINUS,
            '*': TT.STAR,   '/': TT.SLASH,
            '%': TT.PERCENT,'=': TT.ASSIGN,
            '<': TT.LT,     '>': TT.GT,
            '(': TT.LPAREN, ')': TT.RPAREN,
            '[': TT.LBRACKET, ']': TT.RBRACKET,
            ':': TT.COLON,  ',': TT.COMMA,
            '.': TT.DOT,
        }
        if ch in op1:
            self.advance()
            return Token(op1[ch], ch, line, col)

        raise LexerError(f"Operator tidak dikenal: {ch!r}", line, col)

    # ── inject INDENT / DEDENT ──────────────────────────────

    def _inject_indent_dedent(self, raw: List[Token]) -> List[Token]:
        """
        Proses token NEWLINE + INDENT_LEVEL menjadi
        INDENT / DEDENT yang tepat.
        """
        result      = []
        indent_stack= [0]
        i           = 0
        pending_nl  = None

        while i < len(raw):
            tok = raw[i]

            if tok.type == TT.NEWLINE and tok.value == '\\n':
                pending_nl = tok
                i += 1
                # Lihat apakah ada INDENT_LEVEL token berikutnya
                if i < len(raw) and raw[i].type == TT.NEWLINE \
                        and raw[i].value.startswith('INDENT_LEVEL:'):
                    level = int(raw[i].value.split(':')[1])
                    i += 1

                    cur = indent_stack[-1]
                    if level > cur:
                        result.append(Token(TT.NEWLINE, '\\n',
                                            pending_nl.line, pending_nl.col))
                        result.append(Token(TT.INDENT, '',
                                            pending_nl.line, pending_nl.col))
                        indent_stack.append(level)
                    elif level < cur:
                        result.append(Token(TT.NEWLINE, '\\n',
                                            pending_nl.line, pending_nl.col))
                        while indent_stack[-1] > level:
                            indent_stack.pop()
                            result.append(Token(TT.DEDENT, '',
                                                pending_nl.line, pending_nl.col))
                        if indent_stack[-1] != level:
                            raise LexerError(
                                "Indentasi tidak konsisten",
                                pending_nl.line, pending_nl.col)
                    else:
                        result.append(Token(TT.NEWLINE, '\\n',
                                            pending_nl.line, pending_nl.col))
                else:
                    if pending_nl:
                        result.append(Token(TT.NEWLINE, '\\n',
                                            pending_nl.line, pending_nl.col))
                continue

            if tok.type == TT.EOF:
                # Tutup semua indent yang masih terbuka
                while len(indent_stack) > 1:
                    indent_stack.pop()
                    result.append(Token(TT.DEDENT, '', tok.line, tok.col))
                result.append(tok)
                i += 1
                continue

            result.append(tok)
            i += 1

        return result


# ════════════════════════════════════════════════════════════
#  PUBLIC API
# ════════════════════════════════════════════════════════════

def tokenize(source: str) -> List[Token]:
    lexer = Lexer(source)
    return lexer.tokenize_indentation()


def print_tokens(tokens: List[Token]):
    """Helper debug: cetak semua token dengan rapi."""
    print("=" * 55)
    print(f"{'TYPE':<20} {'VALUE':<20} {'LOC'}")
    print("=" * 55)
    for tok in tokens:
        loc = f"L{tok.line}:C{tok.col}"
        print(f"{tok.type.name:<20} {tok.value!r:<20} {loc}")
    print("=" * 55)