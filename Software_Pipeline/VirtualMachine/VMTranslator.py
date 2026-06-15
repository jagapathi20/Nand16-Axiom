import sys
import os

from parser import Parser
from codeWriter import CodeWriter

def main():
    if len(sys.argv) < 2:
        print("Usage: python vm_translator.py <path-to-file.vm>")
        return
    
    vm_file_path = sys.argv[1]

    base_path, _ = os.path.splitext(vm_file_path)
    asm_file_path = base_path + ".asm"

    print(f"Translating {vm_file_path} -> {asm_file_path}...")

    try:
        parser = Parser(vm_file_path)
        code_writer = CodeWriter(asm_file_path)

        while parser.has_more_commands():
            parser.advance()

            cmd_type = parser.command_type()

            if cmd_type == "C_ARITHMETIC":
                command = parser.arg1()
                code_writer.write_arithmetic(command)
            elif cmd_type in ["C_PUSH", "C_POP"]:
                segment = parser.arg1()
                index = parser.arg2()
                code_writer.write_push_pop(cmd_type,segment, index)
        
        code_writer.close()
        print("Translation completed successfully!")
    except FileNotFoundError:
        print(f"Error: Could not find or open the file '{vm_file_path}'")
    except Exception as e:
        print(f"An unexpected error occurred during translation: {e}")
        print(f"Failed while processing command: '{parser.current_command}'")


if __name__ == "__main__":
    main()
