from parsing.nodes import *
from lexing.symbols import *
from errors.error import *


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
