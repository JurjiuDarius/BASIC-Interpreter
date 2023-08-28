class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.error_name = error_name
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.details = details

    def as_string(self):
        result = f"{self.error_name}: {self.details}"
        result += f"File {self.pos_start.file_name}, line {self.pos_start.ln+1}"
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Invalid parsing error: ", details)
