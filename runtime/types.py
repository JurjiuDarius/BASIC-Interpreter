from runtime.interpreter import RuntimeResult, Interpreter
from runtime.context import Context, SymbolTable
import runtime.runner as runner
import os


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

        _, error = runner.run(fn, script)

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
