ARITHMETIC_COMMANDS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}

class Parser:
    def __init__(self, file_path: str):
        with open(file_path, 'r') as file:
            raw_lines = file.readlines()

        self.commands = []
        for line in raw_lines:
            clean_line = self._clean_line(line)
            if clean_line:
                self.commands.append(clean_line)

        self.commands.reverse()
        self.current_command = None

    def _clean_line(self, line:str) -> str:
        line_without_comment = line.split("//")[0]
        return line_without_comment.strip()

    def has_more_commands(self) -> bool:
        return len(self.commands) > 0

    def advance(self):
        if self.has_more_commands():
            self.current_command = self.commands.pop()

    def command_type(self) -> str:
        parts = self.current_command.split()
        first_word = parts[0]

        if first_word in ARITHMETIC_COMMANDS:
            return "C_ARITHMETIC"
        elif first_word == "push":
            return "C_PUSH"
        elif first_word == "pop":
            return "C_POP"
        elif first_word == "label":
            return "C_LABEL"
        elif first_word == "goto":
            return "C_GOTO"
        elif first_word == "if-goto":
            return "C_IF"
        elif first_word == "function":
            return "C_FUNCTION"
        elif first_word == "call":
            return "C_CALL"
        elif first_word == "return":
            return "C_RETURN"
        
        raise ValueError(f"Unknown command type encountered: {self.current_command}")
    
    def arg1(self) -> str:
        parts = self.current_command.split()
        if self.command_type() == "C_ARITHMETIC":
            return parts[0]
        return parts[1]
    
    def arg2(self) -> int:
        parts = self.current_command.split()
        return int(parts[2])