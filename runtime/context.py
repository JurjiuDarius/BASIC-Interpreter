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
