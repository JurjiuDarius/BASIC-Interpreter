from error import IllegalCharError, InvalidSyntaxError, RuntimeError
from nodes import *
import string
import os

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


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value=None):
        if value == None:
            return self.type == type_
        return self.type == type_ and self.value == value

    def __repr__(self) -> str:
        if self.value:
            return f"{self.type}:{self.value}"
        return f"{self.type}"


class Lexer:
    def __init__(self, file_name, text):
        self.file_name = file_name
        self.text = text
        self.pos = Position(-1, 0, -1, file_name, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = (
            self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
        )

    def make_tokens(self):
        tokens = []
        while self.current_char != None:
            if self.current_char in " \t":
                self.advance()

            elif self.current_char == "#":
                self.skip_line()

            elif self.current_char in ";\n":
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()

            elif self.current_char in DIGITS:
                tokens.append(self.make_number())

            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())

            elif self.current_char == '"':
                tokens.append(self.make_str())

            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()

            elif self.current_char == "-":
                tokens.append(self.make_minus_or_arrow())

            elif self.current_char == "*":
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()

            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()

            elif self.current_char == "^":
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()

            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == "[":
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()

            elif self.current_char == "]":
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()

            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == "=":
                tokens.append(self.make_equals())
                self.advance()

            elif self.current_char == "!":
                tokens.append(Token(TT_EQ, pos_start=self.pos))
                self.advance()

            elif self.current_char == "<":
                tokens.append(self.make_less_than())
                self.advance()

            elif self.current_char == ">":
                tokens.append(self.make_greater_than())
                self.advance()

            elif self.current_char == "=":
                tokens.append(Token(TT_EQ, pos_start=self.pos))
                self.advance()

            elif self.current_char == "=":
                tokens.append(Token(TT_EQ, pos_start=self.pos))
                self.advance()

            elif self.current_char == ",":
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()

            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, char)

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def skip_line(self):
        while self.current_char != "\n":
            self.advance()

        self.advance

    def make_str(self):
        string = ""
        pos_start = self.pos.copy()
        escape_character = False
        self.advance()

        while self.current_char != None and (
            self.current_char != '"' or escape_character
        ):
            if escape_character:
                string += self.current_char
            else:
                if self.current_char == "\\":
                    escape_character = True
                else:
                    string += self.current_char
            escape_character = False
            self.advance()

        self.advance()

        return Token(TT_STR, string, pos_start, self.pos)

    def make_minus_or_arrow(self):
        tok_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == ">":
            tok_type = TT_ARROW
            self.advance()

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, IllegalCharError(pos_start, self.pos, "'=' expected after '!'")

    def make_equals(self):
        pos_start = self.pos.copy()
        tok_type = TT_EQ
        self.advance()
        if self.current_char == "=":
            self.advance()
            tok_type = TT_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        pos_start = self.pos.copy()
        tok_type = TT_LT
        self.advance()
        if self.current_char == "=":
            self.advance()
            tok_type = TT_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        pos_start = self.pos.copy()
        tok_type = TT_GT
        self.advance()
        if self.current_char == "=":
            self.advance()
            tok_type = TT_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_identifier(self):
        id_str = ""
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + "_":
            id_str += self.current_char
            self.advance()
        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char

            self.advance()
        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)


class Position:
    def __init__(self, idx, ln, col, file_name, file_text):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.file_name, self.file_text)


class NumberNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f"{self.tok}"


class StringNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f"{self.tok}"


class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end


class BinaryOperationNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.op_tok}, {self.right_node})"


class UnaryOperationNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        self.pos_start = self.op_tok.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f"({self.op_tok}, {self.node})"


class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end


class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (
            self.else_case
            if self.else_case is not None
            else self.cases[len(self.cases) - 1]
        )[0].pos_end


class ForNode:
    def __init__(
        self,
        var_name_tok,
        start_var_node,
        end_val_node,
        step_val_node,
        body_node,
        should_return_null,
    ):
        self.var_name_tok = var_name_tok
        self.start_val_node = start_var_node
        self.end_val_node = end_val_node
        self.step_val_node = step_val_node
        self.body_node = body_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.body_node.pos_end

        self.should_return_null = should_return_null


class WhileNode:
    def __init__(self, condition_node, body_node, should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end


class FunctionDefinitionNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        self.pos_start = pos_start
        self.pos_end = pos_end


class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0
        self.last_registered_advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def parse(self):
        res = self.statements()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected operator token",
                )
            )
        return res

    def statements(self):
        res = ParseResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            self.register_advance(res)

        statement = res.register(self.statement())
        if res.error:
            return res
        statements.append(statement)
        has_more_statements = True
        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                self.register_advance(res)
                newline_count += 1
                if newline_count == 0:
                    has_more_statements = False

            if not has_more_statements:
                break

            statement = res.try_register(self.statement())
            if not statement:
                self.reverse(res.to_reverse_count)
                has_more_statements = False
                continue
            statements.append(statement)

        return res.success(
            ListNode(statements, pos_start, self.current_tok.pos_end.copy())
        )

    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, "RETURN"):
            self.register_advance(res)
            expr = res.try_register(self.expression())

            if not expr:
                self.reverse(res.to_reverse_count)

            return res.success(
                ReturnNode(expr, pos_start, self.current_tok.pos_end.copy())
            )

        if self.current_tok.matches(TT_KEYWORD, "CONTINUE"):
            self.register_advance(res)

            return res.success(ContinueNode(pos_start, self.current_tok.pos_end.copy()))

        if self.current_tok.matches(TT_KEYWORD, "BREAK"):
            self.register_advance(res)

            return res.success(BreakNode(pos_start, self.current_tok.pos_end.copy()))

        expr = res.register(self.expression())
        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "int, float, identifier +, - or ), ], VAR, IF, FOR, WHILE, FUN, RETURN, CONTINUE, BREAK OR NOT",
                )
            )
        return res.success(expr)

    def advance(self):
        self.tok_idx += 1
        self.update_current_tok()
        return self.current_tok

    def reverse(self, amount=1):
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self):
        if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    def comparison_expression(self):
        res = ParseResult()
        if self.current_tok.matches(TT_KEYWORD, "NOT"):
            op_tok = self.current_tok
            self.register_advance(res)

            node = res.register(self.comparison_expression())
            if res.error:
                return res
            return res.success(UnaryOperationNode(op_tok, node))
        node = res.register(
            self.bin_op(
                self.arithmetic_expression, (TT_EE, TT_NE, TT_LT, TT_LTE, TT_GT, TT_GTE)
            )
        )

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected int, float, identifier, '[' '+', '-','(' 'NOT'",
                )
            )
        return res.success(node)

    def arithmetic_expression(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res
        if self.current_tok.type == TT_LPAREN:
            self.register_advance(res)
            arg_nodes = []

            if self.current_tok.type == TT_RPAREN:
                self.register_advance(res)
            else:
                arg_nodes.append(res.register(self.expression()))
                if res.error:
                    return res
                while self.current_tok.type == TT_COMMA:
                    self.register_advance(res)
                    arg_nodes.append(res.register(self.expression()))
                    if res.error:
                        return res

                if self.current_tok.type != TT_RPAREN:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected ',' or ')'",
                        )
                    )

                self.register_advance(res)

            return res.success(CallNode(atom, arg_nodes))

        return res.success(atom)

    def atom(self):
        res = ParseResult()
        tok = self.current_tok
        if tok.type in (TT_INT, TT_FLOAT):
            self.register_advance(res)
            return res.success(NumberNode(tok))

        elif tok.type == TT_IDENTIFIER:
            self.register_advance(res)
            return res.success(VarAccessNode(tok))

        elif tok.type == TT_LSQUARE:
            list_expr = res.register(self.list_expression())
            if res.error:
                return res
            return res.success(list_expr)

        elif tok.type == TT_STR:
            self.register_advance(res)
            return res.success(StringNode(tok))

        elif tok.type == TT_LPAREN:
            self.register_advance(res)
            expression = res.register(self.expression())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                self.register_advance(res)
                return res.success(expression)
            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "int, float, identifier , '+', '-' or ')'",
                    )
                )

        elif tok.matches(TT_KEYWORD, "IF"):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)

        elif tok.matches(TT_KEYWORD, "FOR"):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)

        elif tok.matches(TT_KEYWORD, "WHILE"):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)

        elif tok.matches(TT_KEYWORD, "WHILE"):
            while_expr = res.register(self.func_def())
            if res.error:
                return res
            return res.success(while_expr)

        elif tok.matches(TT_KEYWORD, "FUN"):
            func_def = res.register(self.func_def())
            if res.error:
                return res
            return res.success(func_def)

        return res.failure(
            InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected int or float")
        )

    def list_expression(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected '['",
                )
            )

        self.register_advance(res)

        if self.current_tok.type == TT_RSQUARE:
            self.register_advance(res)
        else:
            element_nodes.append(res.register(self.expression()))
            if res.error:
                return res
            while self.current_tok.type == TT_COMMA:
                self.register_advance(res)
                element_nodes.append(res.register(self.expression()))
                if res.error:
                    return res

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ',' or ']'",
                    )
                )

            self.register_advance(res)

        return res.success(
            ListNode(element_nodes, pos_start, self.current_tok.pos_end.copy())
        )

    def match_value_advance(self, result, token_type, value):
        if not self.current_tok.matches(token_type, value):
            return result.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    f"Expected '{value}'",
                )
            )

        result.register_advancement()
        self.advance()

    def register_advance(self, result):
        result.register_advancement()
        self.advance()

    def func_def(self):
        res = ParseResult()
        failure = self.match_value_advance(res, TT_KEYWORD, "FUN")
        if failure:
            return failure

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            self.register_advance(res)
            if self.current_tok.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected '('",
                    )
                )

        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier or '('",
                    )
                )

        self.register_advance(res)
        arg_name_toks = []
        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            self.register_advance(res)

            while self.current_tok.type == TT_COMMA:
                self.register_advance(res)
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected identifier",
                        )
                    )
                arg_name_toks.append(self.current_tok)
                self.register_advance(res)

            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ',' or ')'",
                    )
                )
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier or ')'",
                    )
                )
        self.register_advance(res)
        if self.current_tok.type == TT_ARROW:
            self.register_advance(res)

            node_to_return = res.register(self.expression())
            if res.error:
                return res
            return res.success(
                FunctionDefinitionNode(
                    var_name_tok, arg_name_toks, node_to_return, True
                )
            )

        if self.current_tok.type != TT_NEWLINE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected '->' or new line",
                )
            )

        self.register_advance(res)

        body = res.register(self.statements())
        if res.error:
            return res
        self.match_value_advance(res, TT_KEYWORD, "END")

        return res.success(
            FunctionDefinitionNode(var_name_tok, arg_name_toks, body, False)
        )

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.parse_if_cases("IF"))
        if res.error:
            return res
        cases, else_cases = all_cases
        return res.success(IfNode(cases, else_cases))

    def if_expr_b(self):
        return self.parse_if_cases("ELIF")

    def if_expr_c(self):
        res = ParseResult()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, "ELSE"):
            self.register_advance(res)
            if self.current_tok.type == TT_NEWLINE:
                self.register_advance(res)
                statements = res.register(self.statements())

                if res.error:
                    return res
                else_case = (statements, True)

                if self.current_tok.matches(TT_KEYWORD, "END"):
                    self.register_advance(res)

                else:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_ned,
                            "Expected 'END",
                        )
                    )

            else:
                expr = res.register(self.statement())
                if res.error:
                    return res
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None

        if self.current_tok.matches(TT_KEYWORD, "ELIF"):
            all_cases = res.register(self.if_expr_b())
            if res.error:
                return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error:
                return res

        return res.success((cases, else_case))

    def parse_if_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None

        failure = self.match_value_advance(res, TT_KEYWORD, case_keyword)
        if failure:
            return failure

        condition = res.register(self.expression())
        if res.error:
            return res

        failure = self.match_value_advance(res, TT_KEYWORD, "THEN")
        if failure:
            return failure

        if self.current_tok.type == TT_NEWLINE:
            self.register_advance(res)

            statements = res.register(self.statements())
            if res.error:
                return res

            cases.append((condition, statements, True))

            if self.current_tok.matches(TT_KEYWORD, "END"):
                self.register_advance(res)
            else:
                all_cases = res.register(self.if_expr_b_or_c())
                if res.error:
                    return res
                new_cases, else_case = all_cases
                cases.extend(new_cases)

        else:
            expr = res.register(self.statement())
            if res.error:
                return res
            cases.append((condition, expr, False))
            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        return res.success((cases, else_case))

    def for_expr(self):
        res = ParseResult()

        failure = self.match_value_advance(res, TT_KEYWORD, "FOR")
        if failure:
            return failure

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected identifier",
                )
            )

        var_name = self.current_tok
        self.register_advance(res)

        if self.current_tok.type != TT_EQ:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='"
                )
            )

        self.register_advance(res)

        start_value = res.register(self.statement())
        if res.error:
            return res

        failure = self.match_value_advance(res, TT_KEYWORD, "TO")
        if failure:
            return failure

        end_value = res.register(self.expression())
        if res.error:
            return res

        if self.current_tok.matches(TT_KEYWORD, "STEP"):
            self.register_advance(res)

            step_value = res.register(self.expression())
            if res.error:
                return res
        else:
            step_value = None

        failure = self.match_value_advance(res, TT_KEYWORD, "THEN")
        if failure:
            return failure

        if self.current_tok.type == TT_NEWLINE:
            self.register_advance(res)
            body = res.register(self.statements())
            if res.error:
                return res

            self.match_value_advance(res, TT_KEYWORD, "END")

            return res.success(
                ForNode(var_name, start_value, end_value, step_value, body, True)
            )

        body = res.register(self.expression())

        if res.error:
            return res

        return res.success(
            ForNode(var_name, start_value, end_value, step_value, body, False)
        )

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "WHILE"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'WHILE'",
                )
            )

        self.register_advance(res)
        condition = res.register(self.expression())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, "THEN"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'THEN'",
                )
            )
        if self.current_tok.type == TT_NEWLINE:
            self.register_advance(res)
            body = res.register(self.statements())
            if res.error:
                return res

            self.match_value_advance(res, TT_KEYWORD, "END")

            return res.success(WhileNode(condition, body, True))

        self.register_advance(res)
        body = res.register(self.statement())
        if res.error:
            return res

        return res.success(WhileNode(condition, body, False))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def power(self):
        return self.bin_op(self.call, (TT_POW,), self.factor)

    def factor(self):
        res = ParseResult()
        tok = self.current_tok
        if tok.type in (TT_PLUS, TT_MINUS):
            self.register_advance(res)
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOperationNode(tok, factor))
        return self.power()

    def expression(self):
        res = ParseResult()
        if self.current_tok.matches(TT_KEYWORD, "VAR"):
            self.register_advance(res)
            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Identifier expected",
                    )
                )

            var_name = self.current_tok
            self.register_advance(res)

            if self.current_tok.type != TT_EQ:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "'=' expected",
                    )
                )
            self.register_advance(res)
            expr = res.register(self.expression())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr))

        node = res.register(
            self.bin_op(
                self.comparison_expression, ((TT_KEYWORD, "AND"), (TT_KEYWORD, "OR"))
            )
        )
        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected int, float, identifier, '[' '+', '-','(' 'NOT'",
                )
            )
        return res.success(node)

    def bin_op(self, func_left, ops, func_right=None):
        res = ParseResult()
        if func_right == None:
            func_right = func_left

        left = res.register(func_left())
        if res.error:
            return res

        while (
            self.current_tok.type in ops
            or (self.current_tok.type, self.current_tok.value) in ops
        ):
            op_tok = self.current_tok
            self.register_advance(res)
            right = res.register(func_right())
            if res.error:
                return res
            left = BinaryOperationNode(left, op_tok, right)

        return res.success(left)


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def illegal_operation(self, other=None):
        if not other:
            other = self
        return RuntimeError(
            self.pos_start,
            other.pos_end if other else self.pos_end,
            "Illegal operation",
            self.context,
        )

    def added_to(self, other):
        return None, self.illegal_operation(other)

    def subbed_by(self, other):
        return None, self.illegal_operation(other)

    def multiplied_by(self, other):
        return None, self.illegal_operation(other)

    def divided_by(self, other):
        return None, self.illegal_operation(other)

    def powered_by(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)

    def anded_by(self, other):
        return None, self.illegal_operation(other)

    def ored_by(self, other):
        return None, self.illegal_operation(other)

    def notted(self):
        return None, self.illegal_operation()

    def execute(self, args):
        return RuntimeResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception("No copy method defined")

    def is_true(self):
        return False


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        elif isinstance(other, int) or isinstance(other, float):
            return Number(self.value + other).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        elif isinstance(other, int) or isinstance(other, float):
            return Number(self.value - other).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multiplied_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        elif isinstance(other, int) or isinstance(other, float):
            return Number(self.value * other).set_context(self.context), None
        elif isinstance(other, String):
            return String(other.value * self.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def powered_by(self, other):
        if isinstance(other, Number):
            return Number(self.value**other.value).set_context(self.context), None
        elif isinstance(other, int) or isinstance(other, float):
            return Number(self.value**other).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def divided_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(
                    other.pos_start, other.pos_end, "Divison by 0", self.context
                )
            return (Number(self.value / other.value).set_context(self.context), None)
        elif isinstance(other, int) or isinstance(other, float):
            if other == 0:
                return None, RuntimeError(
                    other.pos_start, other.pos_end, "Divison by 0", self.context
                )
            return (Number(self.value / other).set_context(self.context), None)
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def ok(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value <= other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value >= other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def anded_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value and other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def ored_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value or other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def is_true(self):
        return self.value != 0

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        elif isinstance(other, str):
            return String(self.value + other).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multiplied_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        elif isinstance(other, int):
            return String(self.value * other).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def added_to(self, other):
        if isinstance(other, List):
            return List(self.elements + other.elements), None

        if isinstance(other, list):
            return List(self.elements + other), None

        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def subbed_by(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)
                return new_list, None
            except:
                return RuntimeError(
                    other.pos_start,
                    other.pos_end,
                    f"Incorrect index when trying to remove from list:{other.value}",
                    self.context,
                )
        else:
            return None, Value.illegal_operation(self, other)

    def divided_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return RuntimeError(
                    other.pos_start,
                    other.pos_end,
                    f"Incorrect index when trying to access element at index:{other.value}",
                    self.context,
                )
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]'


class BaseFunction(Value):
    def __init__(self, name=None):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        res = RuntimeResult()
        if len(args) > len(arg_names):
            return res.failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    f"{len(args) - len(arg_names)} too many args passed into '{self.name}'",
                    self.context,
                )
            )

        if len(args) < len(arg_names):
            return res.failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    f"{len(arg_names) - len(args)} too few args passed into '{self.name}'",
                    self.context,
                )
            )
        return res.success(None)

    def populate_args(self, arg_names, args, context):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(context)
            context.symbol_table.set(arg_name, arg_value)

    def check_populate_args(self, arg_names, args, context):
        res = RuntimeResult()
        res.register(self.check_args(arg_names, args))
        if res.error:
            return res
        self.populate_args(arg_names, args, context)
        return res.success(None)


class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return

    def execute(self, args):
        res = RuntimeResult()
        interpreter = Interpreter()
        context = self.generate_new_context()

        res.register(self.check_populate_args(self.arg_names, args, context))

        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, context))
        if res.should_return() and res.func_return_value == None:
            return res

        ret_value = (
            (value if self.should_auto_return else None)
            or res.func_return_value
            or Number.null
        )
        return res.success(ret_value)

    def copy(self):
        copy = Function(
            self.name, self.body_node, self.arg_names, self.should_auto_return
        )
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        res = RuntimeResult()
        context = self.generate_new_context()
        method_name = f"execute_{self.name}"
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_populate_args(method.arg_names, args, context))

        if res.should_return():
            return res

        return_value = res.register(method(context))
        if res.should_return():
            return res

        return res.success(return_value)

    def no_visit_method(self, node, context):
        raise Exception(f"No execute {self.name} method defined")

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start)
        return copy

    def __repr__(self):
        return f"<built-in function {self.name}"

    def execute_print(self, context):
        print(str(context.symbol_table.get("value")))
        return RuntimeResult().success(Number.null)

    execute_print.arg_names = ["value"]

    def execute_print_return(self, context):
        return RuntimeResult().success(String(str(context.symbol_table.get("value"))))

    execute_print_return.arg_names = ["value"]

    def execute_input(self, context):
        text = input()
        return RuntimeResult().success(String(text))

    execute_input.arg_names = []

    def execute_input_int(self, context):
        while True:
            text = input()

            try:
                number = int(text)
                break
            except ValueError:
                print("Must input an integer")
        return RuntimeResult().success(Number(number))

    execute_input_int.arg_names = []

    def execute_clear(self, context):
        os.system("cls" if os.name == "nt" else "clear")
        return RuntimeResult().success(Number.null)

    execute_clear.arg_names = []

    def execute_is_number(self, context):
        is_number = isinstance(context.symbol_table.get("value"), Number)
        return RuntimeResult().success(Number.true if is_number else Number.false)

    execute_is_number.arg_names = ["value"]

    def execute_is_string(self, context):
        is_number = isinstance(context.symbol_table.get("value"), String)
        return RuntimeResult().success(Number.true if is_number else Number.false)

    execute_is_string.arg_names = ["value"]

    def execute_is_list(self, context):
        is_number = isinstance(context.symbol_table.get("value"), List)
        return RuntimeResult().success(Number.true if is_number else Number.false)

    execute_is_list.arg_names = ["value"]

    def execute_is_function(self, context):
        is_number = isinstance(context.symbol_table.get("value"), BaseFunction)
        return RuntimeResult().success(Number.true if is_number else Number.false)

    execute_is_function.arg_names = ["value"]

    def execute_append(self, context):
        list_ = context.symbol_table.get("list")
        value = context.symbol_table.get("value")

        if not isinstance(list_, List):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    "First argument must be a list",
                    context,
                )
            )

        list_.elements.append(value)
        return RuntimeResult().success(Number.null)

    execute_append.arg_names = ["list", "value"]

    def execute_pop(self, context):
        list_ = context.symbol_table.get("list")
        index = context.symbol_table.get("index")

        if not isinstance(list_, List):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    "First argument must be a list",
                    context,
                )
            )
        if not isinstance(index, Number):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    "Second argument must be a number",
                    context,
                )
            )

        try:
            element = list_.elements.pop(index.value)
        except:
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    f"Element at index {index} could not be removed because the index is out of bounds",
                    context,
                )
            )
        return RuntimeResult().success(element)

    execute_pop.arg_names = ["list", "index"]

    def execute_extend(self, context):
        listA = context.symbol_table.get("listA")
        listB = context.symbol_table.get("listB")

        if not isinstance(listA, List):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    "First argument must be a list",
                    context,
                )
            )
        if not isinstance(listB, List):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    "Second argument must be a list",
                    context,
                )
            )

        listA.elements.extend(listB.elements)
        return RuntimeResult().success(Number.null)

    execute_extend.arg_names = ["listA", "listB"]

    def execute_len(self, context):
        list_ = context.symbol_table.get("list")
        if not isinstance(list_, list):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    "Second argument must be a list",
                    context,
                )
            )
        return RuntimeResult().success(Number(len(list_.elements)))

    execute_len.arg_names = ["list"]

    def execute_run(self, context):
        fn = context.symbol_table.get("fn")

        if not isinstance(fn, String):
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start, self.pos_end, "Argument must be string", context
                )
            )

        fn = fn.value

        try:
            with open(fn, "r") as f:
                script = f.read()

        except Exception as e:
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    f"Failed to load script from file '{fn}'",
                    context,
                )
            )

        _, error = run(fn, script)

        if error:
            return RuntimeResult().failure(
                RuntimeError(
                    self.pos_start,
                    self.pos_end,
                    f"Could not finish executing script '{fn}' \n Error message: "
                    + error.as_string(),
                    context,
                )
            )
        return RuntimeResult().success(Number.null)

    execute_run.arg_names = ["fn"]


BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
BuiltInFunction.is_number = BuiltInFunction("is_number")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_list = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append = BuiltInFunction("append")
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend")
BuiltInFunction.len = BuiltInFunction("len")
BuiltInFunction.run = BuiltInFunction("run")


class RuntimeResult:
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False

    def register(self, res):
        self.error = res.should_return()
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        return res.value

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self

    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self

    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_return(self):
        return (
            self.error
            or self.func_return_value
            or self.loop_should_continue
            or self.loop_should_break
        )


class Context:
    def __init__(
        self,
        display_name,
        parent=None,
        parent_entry_pos=None,
    ):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, variable_name):
        value = self.symbols.get(variable_name, None)
        if value == None and self.parent:
            return self.parent.get(variable_name)

        return value

    def set(self, variable_name, value):
        self.symbols[variable_name] = value

    def remove(self, name):
        del self.symbols[name]


class Interpreter:
    def visit(self, node, context):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_NumberNode(self, node, context):
        return RuntimeResult().success(
            Number(node.tok.value)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_UnaryOperationNode(self, node, context):
        res = RuntimeResult()

        number = res.register(self.visit(node.node, context))
        if res.should_return():
            return res
        error = None
        if node.op_tok.type == TT_MINUS:
            number, error = number.multiplied_by(-1)
        elif node.op_tok.matches(TT_KEYWORD, "NOT"):
            number, error = number.notted()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_BinaryOperationNode(self, node, context):
        res = RuntimeResult()
        left = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        right = res.register(self.visit(node.right_node, context))
        if res.should_return():
            return res

        if node.op_tok.type == TT_PLUS:
            result, error = left.added_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.multiplied_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.divided_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.powered_by(right)
        elif node.op_tok.type == TT_EE:
            result, error = left.get_comparison_eq(right)
        elif node.op_tok.type == TT_NE:
            result, error = left.get_comparison_ne(right)
        elif node.op_tok.type == TT_LT:
            result, error = left.get_comparison_lt(right)
        elif node.op_tok.type == TT_GT:
            result, error = left.get_comparison_gt(right)
        elif node.op_tok.type == TT_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.op_tok.type == TT_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.op_tok.matches(TT_KEYWORD, "AND"):
            result, error = left.anded_by(right)
        elif node.op_tok.matches(TT_KEYWORD, "OR"):
            result, error = left.ored_by(right)
        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node, context):
        res = RuntimeResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(
                RuntimeError(
                    node.pos_start,
                    node.pos_end,
                    f"'{var_name}' is not defined",
                    context,
                )
            )

        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)

    def visit_VarAssignNode(self, node, context):
        res = RuntimeResult()

        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res
        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_IfNode(self, node, context):
        res = RuntimeResult()

        for condition, expr, should_return_null in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res
            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))
                if res.should_return():
                    return res
                return res.success(Number.null if should_return_null else expr_value)

        if node.else_case:
            expr, should_return_null = node.else_case
            else_value = res.register(self.visit(expr, context))
            if res.should_return():
                return res
            return res.success(Number.null if should_return_null else else_value)

        return res.success(Number.null)

    def visit_StringNode(self, node, context):
        return RuntimeResult().success(
            String(node.tok.value)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListNode(self, node, context):
        res = RuntimeResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res
        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ForNode(self, node, context):
        res = RuntimeResult()
        elements = []

        start_value = res.register(self.visit(node.start_val_node, context))
        if res.should_return():
            return res

        end_value = res.register(self.visit(node.end_val_node, context))
        if res.should_return():
            return res

        if node.step_val_node:
            step_value = res.register(self.visit(node.step_val_node, context))
            if res.should_return():
                return res
        else:
            step_value = Number(1)

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value

        while condition():
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value
            value = res.register(self.visit(node.body_node, context))

            if (
                res.should_return()
                and res.loop_should_break == False
                and res.loop_should_continue == False
            ):
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)
        return res.success(
            Number.null
            if node.should_return_null
            else List(elements)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_WhileNode(self, node, context):
        res = RuntimeResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res
            if not condition.is_true():
                break
            value = res.register(self.visit(node.body_node, context))
            if (
                res.should_return()
                and res.loop_should_break == False
                and res.loop_should_continue == False
            ):
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break
            elements.append(value)

        return res.success(
            Number.null
            if node.should_return_null
            else List(elements)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_FunctionDefinitionNode(self, node, context):
        res = RuntimeResult()
        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func = (
            Function(func_name, body_node, arg_names, node.should_auto_return)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )
        if node.var_name_tok:
            context.symbol_table.set(func_name, func)

        return res.success(func)

    def visit_CallNode(self, node, context):
        res = RuntimeResult()
        args = []
        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res

        return_value = res.register(value_to_call.execute(args))
        if res.should_return():
            return res
        return_value = (
            return_value.copy()
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )
        return res.success(return_value)

    def visit_ReturnNode(self, node, context):
        res = RuntimeResult()
        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res

        return res.success_return(value)

    def visit_ContinueNode(self, node, context):
        return RuntimeResult().success_continue()

    def visit_BreakNode(self, node, context):
        return RuntimeResult().success_continue()


global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)
global_symbol_table.set("IS_STR", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)
global_symbol_table.set("LEN", BuiltInFunction.len)
global_symbol_table.set("RUN", BuiltInFunction.run)


def run(file_name, text):
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()

    if error:
        return None, None

    parser = Parser(tokens)
    ast = parser.parse()

    if ast.error:
        return None, ast.error

    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    return result.value, result.error
