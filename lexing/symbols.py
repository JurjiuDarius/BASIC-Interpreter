import string

TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_POW = "POW"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_LSQUARE = "["
TT_RSQUARE = "]"
TT_STR = "STR"
TT_EOF = "EOF"
TT_EQ = "EQ"
TT_EE = "EE"
TT_NE = "NE"
TT_LT = "LT"
TT_GT = "GT"
TT_LTE = "LTE"
TT_GTE = "GTE"
TT_COMMA = "COMMA"
TT_ARROW = "ARROW"
TT_IDENTIFIER = "IDENTIFIER"
TT_NEWLINE = "NEWLINE"
TT_KEYWORD = "KEYWORD"

escape_characters = {"n": "\n", "t": "t"}

KEYWORDS = [
    "VAR",
    "AND",
    "OR",
    "NOT",
    "IF",
    "THEN",
    "ELSE",
    "ELIF",
    "FOR",
    "TO",
    "STEP",
    "WHILE",
    "FUN",
    "END",
    "RETURN",
    "CONTINUE",
    "BREAK",
]


DIGITS = "1234567890"
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS
