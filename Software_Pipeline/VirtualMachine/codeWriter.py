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

    def close(self):
        self.output_file.close()