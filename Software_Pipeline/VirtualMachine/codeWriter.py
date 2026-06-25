import os 

SEGMENT_POINTERS = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT"
}

class CodeWriter:
    def __init__(self, file_path):
        self.output_file = open(file_path, 'w')
        base_name = os.path.basename(file_path)
        self.file_name, _ = os.path.splitext(base_name)
        self.label_counter = 0
        self.current_function = "none"

    def write_arithmetic(self, command: str):
        assembly_code = []
        assembly_code.append(f"//{command}")

        if command in ("add", "sub", "and", "or"):
            assembly_code.extend([
                "@SP", 
                "M=M-1", 
                "A=M", 
                "D=M", 
                "A=A-1"])
            if command == "add":
                assembly_code.append("M=D+M")
            elif command == "sub":
                assembly_code.append("M=M-D")
            elif command == "and":
                assembly_code.append("M=D&M")
            elif command == "or":
                assembly_code.append("M=D|M")

        elif command in ("not", "neg"):
            assembly_code.extend([
                "@SP", 
                "A=M-1"
                ])
            if command == "not":
                assembly_code.append("M=!M")
            elif command == "neg":
                assembly_code.append("M=-M")

        elif command in ("eq", "lt", "gt"):
            label_true = f"COMP_TRUE_{self.label_counter}"
            label_end = f"COMP_END_{self.label_counter}"
            self.label_counter += 1

            if command == "eq": jump_mnemonic = "JEQ"  
            elif command == "lt": jump_mnemonic = "JLT"
            elif command == "gt": jump_mnemonic = "JGT"

            assembly_code.extend([
                "@SP", 
                "M=M-1", 
                "A=M", 
                "D=M", 
                "A=A-1", 
                "D=M-D",             
                f"@{label_true}",
                f"D;{jump_mnemonic}",         
                "@SP", 
                "A=M-1",
                "M=0",        
                f"@{label_end}", 
                "0;JMP",     
                f"({label_true})",
                "@SP", 
                "A=M-1", 
                "M=-1",       
                f"({label_end})"
            ])

        for line in assembly_code:
            self.output_file.write(line + "\n")

    def write_push_pop(self, command_type: str, segment: str, index: int):
        assembly_code = []
        cmd_str = "push" if command_type == "C_PUSH" else "pop"
        assembly_code.append(f"// {cmd_str} {segment} {index}")

        if segment in ("local", "argument", "this", "that"):
            pointer = SEGMENT_POINTERS[segment]

            if command_type == "C_PUSH":
                assembly_code.extend([
                    f"@{pointer}", 
                    "D=M",
                    f"@{index}", 
                    "A=D+A", 
                    "D=M",
                    "@SP", 
                    "A=M", ""
                    "M=D",
                    "@SP", 
                    "M=M+1"
                ])

            elif command_type == "C_POP":
                assembly_code.extend([
                    f"@{pointer}", 
                    "D=M",
                    f"@{index}", 
                    "D=D+A",
                    "@R13", 
                    "M=D",
                    "@SP", 
                    "M=M-1", 
                    "A=M", 
                    "D=M",
                    "@R13", 
                    "A=M", 
                    "M=D"
                ])

        elif segment == "temp":
            target_address = 5 + index
            if command_type == "C_PUSH":
                assembly_code.extend([
                    f"@{target_address}",
                    "D=M",
                    "@SP", 
                    "A=M", 
                    "M=D", 
                    "@SP", 
                    "M=M+1"
                    ])
            elif command_type == "C_POP":
                assembly_code.extend([
                    "@SP", 
                    "M=M-1", 
                    "A=M", 
                    "D=M", 
                    f"@{target_address}", 
                    "M=D"
                    ])
        
        elif segment == "pointer":
            target_pointer = "THIS" if index == 0 else "THAT"
            if command_type == "C_PUSH":
                assembly_code.extend([
                    f"@{target_pointer}", 
                    "D=M", 
                    "@SP",
                    "A=M", 
                    "M=D", 
                    "@SP", 
                    "M=M+1"
                    ])
            elif command_type == "C_POP":
                assembly_code.extend([
                    "@SP",
                    "M=M-1",
                    "A=M",
                    "D=M",
                    f"@{target_pointer}", 
                    "M=D"])

        elif segment == "static":
            static_label = f"{self.file_name}.{index}" 
            if command_type == "C_PUSH":
                assembly_code.extend([
                    f"@{static_label}", 
                    "D=M", 
                    "@SP", 
                    "A=M", 
                    "M=D", 
                    "@SP", 
                    "M=M+1"
                    ])
            elif command_type == "C_POP":
                assembly_code.extend([
                    "@SP", 
                    "M=M-1", 
                    "A=M",
                    "D=M", 
                    f"@{static_label}", 
                    "M=D"
                    ])
        elif segment == "constant":
            if command_type == "C_PUSH":
                assembly_code.extend([
                    f"@{index}", 
                    "D=A",
                    "@SP", 
                    "A=M", 
                    "M=D",
                    "@SP", 
                    "M=M+1"
                 ])

        for line in assembly_code:
            self.output_file.write(line + "\n")

    def write_label(self, label: str):
        full_label = f"{self.current_function}${label}"
        self.output_file.write(f"// label {label}\n ({full_label})\n")

    def write_goto(self, label: str):
        full_label = f"{self.current_function}${label}"
        assembly_code = [
            f"// goto {label}",
            f"@{full_label}",
            "0;JMP"
        ]

        for line in assembly_code:
            self.output_file.write(line + "\n")

    def write_if(self, label: str):
        full_label = f"{self.current_function}${label}"
        assembly_code = [
            f"// if-goto {label}",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            f"@{full_label}",
            "D;JNE"
        ]
        for line in assembly_code:
            self.output_file.write(line + "\n")


    def write_function(self, function_name: str, num_locals: int):
        self.current_function = function_name
        assembly_code = [f"// function {function_name} {num_locals}", f"({function_name})"]

        for _ in range(num_locals):
            assembly_code.extend([
                "@SP",
                "A=M",
                "M=0",
                "@SP",
                "M=M+1"
            ])
        for line in assembly_code:
            self.output_file.write(line + "\n")

    def write_call(self, function_name: str, num_args: int):
        return_label = f"{function_name}$ret.{self.label_counter}"
        self.label_counter += 1

        assembly_code = [f"// call {function_name} {num_args}"]

        # push return address
        assembly_code.extend([f"@{return_label}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"])

        # push LCL, ARG, THIS, THAT
        for segment in ["LCL", "ARG", "THIS", "THAT"]:
            assembly_code.extend([f"@{segment}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])

        # ARG = SP - 5 - num_args
        assembly_code.extend([
            "@SP", "D=M", "@5", "D=D-A",
            f"@{num_args}", "D=D-A",
            "@ARG", "M=D"
        ])

        # LCL = SP
        assembly_code.extend(["@SP", "D=M", "@LCL", "M=D"])

        # goto function
        assembly_code.extend([f"@{function_name}", "0;JMP", f"({return_label})"])

        for line in assembly_code:
            self.output_file.write(line + "\n")

    def write_return(self):
        assembly_code = [
                "// return",
                "@LCL",
                "D=M",
                "@R14",
                "M=D",

                "@5",
                "A=D-A",
                "D=M",
                "@R15",
                "M=D",

                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "@ARG",
                "A=M",
                "M=D",

                "@ARG",
                "D=M+1",
                "@SP",
                "M=D"
        ]

        for i, pointer in enumerate(["THAT", "THIS", "ARG", "LCL"], start=1):
            assembly_code.extend([
                    "@R14",
                    "D=M",
                    f"@{i}",
                    "A=D-A",
                    "D=M",
                    f"@{pointer}",
                    "M=D"
            ])

        assembly_code.extend([
                "@R15",
                "A=M",
                "0;JMP"
        ])

        for line in assembly_code:
            self.output_file.write(line + "\n")

    def set_file_name(self, file_name: str):
        self.file_name = file_name

    def write_bootstrap(self):
        assembly_code = [
            "// Bootstrap Intialization",
            "@256",
            "D=A",
            "@SP",
            "M=D"
        ]

        for line in assembly_code:
            self.output_file.write(line + "\n")

        self.write_call("Sys.init", 0)

    def close(self):
        self.output_file.close()