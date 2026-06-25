import sys
import os

from parser import Parser
from codeWriter import CodeWriter

def main():
    if len(sys.argv) < 2:
        print("Usage: python VMTranslator.py <path-to-file-or-directory>")
        return
    
    target_path = sys.argv[1]
    vm_files = []

    if os.path.isdir(target_path):
        # Target is a directory: gather all .vm files
        for file in os.listdir(target_path):
            if file.endswith(".vm"):
                vm_files.append(os.path.join(target_path, file))
        # Name output file after the directory name
        dir_name = os.path.basename(os.path.normpath(target_path))
        asm_file_path = os.path.join(target_path, dir_name + ".asm")
        # Multi-file programs are bootstrapped (SP=256, call Sys.init 0)
        should_bootstrap = True
    else:
        # Target is a single file
        vm_files.append(target_path)
        base_path, _ = os.path.splitext(target_path)
        asm_file_path = base_path + ".asm"
        # Single-file tests are NOT bootstrapped: the .tst script sets
        # SP/ARG/LCL manually, and there is no Sys.init to call into.
        should_bootstrap = False

    if not vm_files:
        print("No .vm files found to translate.")
        return

    print(f"Translating to -> {asm_file_path}...")

    try:
        code_writer = CodeWriter(asm_file_path)

        if should_bootstrap:
            code_writer.write_bootstrap()

        for vm_file_path in vm_files:
            print(f" Processing: {vm_file_path}")
            
            # Alert code_writer of the current file context for static variables
            current_file_base = os.path.splitext(os.path.basename(vm_file_path))[0]
            code_writer.set_file_name(current_file_base)

            parser = Parser(vm_file_path)

            while parser.has_more_commands():
                parser.advance()
                cmd_type = parser.command_type()

                if cmd_type == "C_ARITHMETIC":
                    code_writer.write_arithmetic(parser.arg1())
                elif cmd_type in ["C_PUSH", "C_POP"]:
                    code_writer.write_push_pop(cmd_type, parser.arg1(), parser.arg2())
                elif cmd_type == "C_LABEL":
                    code_writer.write_label(parser.arg1())
                elif cmd_type == "C_GOTO":
                    code_writer.write_goto(parser.arg1())
                elif cmd_type == "C_IF":
                    code_writer.write_if(parser.arg1())
                elif cmd_type == "C_FUNCTION":
                    code_writer.write_function(parser.arg1(), parser.arg2())
                elif cmd_type == "C_CALL":
                    code_writer.write_call(parser.arg1(), parser.arg2())
                elif cmd_type == "C_RETURN":
                    code_writer.write_return()
        
        code_writer.close()
        print("Translation completed successfully!")
    except Exception as e:
        print(f"An unexpected error occurred during translation: {e}")

if __name__ == "__main__":
    main()