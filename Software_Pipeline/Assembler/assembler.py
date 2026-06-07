"""
Hack Assembler — nand2tetris Project 6
Translates Hack assembly language (.asm) into Hack binary machine code (.hack)

Architecture follows the nand2tetris course specification:
  - Parser   : reads and parses each instruction
  - Code      : translates mnemonics to binary
  - SymbolTable: manages the symbol table
  - Main      : orchestrates two-pass assembly
"""

import sys
import os


# ---------------------------------------------------------------------------
# Symbol Table
# ---------------------------------------------------------------------------

class SymbolTable:
    """Manages the symbol table with pre-defined Hack symbols."""

    PREDEFINED = {
        "SP":     0,
        "LCL":    1,
        "ARG":    2,
        "THIS":   3,
        "THAT":   4,
        "R0":     0,  "R1":  1,  "R2":  2,  "R3":  3,
        "R4":     4,  "R5":  5,  "R6":  6,  "R7":  7,
        "R8":     8,  "R9":  9,  "R10": 10, "R11": 11,
        "R12":    12, "R13": 13, "R14": 14, "R15": 15,
        "SCREEN": 16384,
        "KBD":    24576,
    }

    def __init__(self):
        self._table: dict[str, int] = dict(self.PREDEFINED)
        self._next_var_address = 16  # Variables start at RAM[16]

    def add_entry(self, symbol: str, address: int) -> None:
        self._table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self._table

    def get_address(self, symbol: str) -> int:
        return self._table[symbol]

    def add_variable(self, symbol: str) -> int:
        """Add a new variable symbol at the next available RAM address."""
        self._table[symbol] = self._next_var_address
        self._next_var_address += 1
        return self._table[symbol]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    """
    Reads a .asm file and exposes each meaningful instruction one at a time.
    Strips whitespace and comments; classifies each line as A, C, or L.
    """

    A_INSTRUCTION = "A_INSTRUCTION"  # @value
    C_INSTRUCTION = "C_INSTRUCTION"  # dest=comp;jump
    L_INSTRUCTION = "L_INSTRUCTION"  # (LABEL)

    def __init__(self, filepath: str):
        with open(filepath, "r") as f:
            raw_lines = f.readlines()

        self._instructions: list[str] = []
        for line in raw_lines:
            # Strip inline comments and surrounding whitespace
            stripped = line.split("//")[0].strip()
            if stripped:
                self._instructions.append(stripped)

        self._index = -1
        self.current_instruction: str = ""

    def has_more_lines(self) -> bool:
        return self._index < len(self._instructions) - 1

    def advance(self) -> None:
        self._index += 1
        self.current_instruction = self._instructions[self._index]

    def reset(self) -> None:
        self._index = -1
        self.current_instruction = ""

    @property
    def instruction_type(self) -> str:
        if self.current_instruction.startswith("@"):
            return self.A_INSTRUCTION
        if self.current_instruction.startswith("("):
            return self.L_INSTRUCTION
        return self.C_INSTRUCTION

    @property
    def symbol(self) -> str:
        """Return the symbol/decimal for A or L instructions."""
        inst = self.current_instruction
        if inst.startswith("@"):
            return inst[1:]
        if inst.startswith("("):
            return inst[1:-1]
        raise ValueError(f"symbol() called on C-instruction: {inst}")

    @property
    def dest(self) -> str:
        """Return the dest mnemonic (before '='), or empty string."""
        inst = self.current_instruction
        if "=" in inst:
            return inst.split("=")[0]
        return ""

    @property
    def comp(self) -> str:
        """Return the comp mnemonic (between '=' and ';')."""
        inst = self.current_instruction
        if "=" in inst:
            inst = inst.split("=")[1]
        if ";" in inst:
            inst = inst.split(";")[0]
        return inst

    @property
    def jump(self) -> str:
        """Return the jump mnemonic (after ';'), or empty string."""
        inst = self.current_instruction
        if ";" in inst:
            return inst.split(";")[1]
        return ""


# ---------------------------------------------------------------------------
# Code
# ---------------------------------------------------------------------------

class Code:
    """Translates Hack assembly mnemonics into their binary representations."""

    _DEST = {
        "":    "000",
        "M":   "001",
        "D":   "010",
        "DM":  "011", "MD": "011",
        "A":   "100",
        "AM":  "101", "MA": "101",
        "AD":  "110", "DA": "110",
        "ADM": "111", "AMD": "111", "DAM": "111",
        "DMA": "111", "MDA": "111", "MAD": "111",
    }

    _JUMP = {
        "":    "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111",
    }

    # comp table: key → (a-bit, cccccc)
    _COMP = {
        "0":   "0101010",
        "1":   "0111111",
        "-1":  "0111010",
        "D":   "0001100",
        "A":   "0110000",  "M":   "1110000",
        "!D":  "0001101",
        "!A":  "0110001",  "!M":  "1110001",
        "-D":  "0001111",
        "-A":  "0110011",  "-M":  "1110011",
        "D+1": "0011111",
        "A+1": "0110111",  "M+1": "1110111",
        "D-1": "0001110",
        "A-1": "0110010",  "M-1": "1110010",
        "D+A": "0000010",  "D+M": "1000010",
        "D-A": "0010011",  "D-M": "1010011",
        "A-D": "0000111",  "M-D": "1000111",
        "D&A": "0000000",  "D&M": "1000000",
        "D|A": "0010101",  "D|M": "1010101",
    }

    @classmethod
    def dest(cls, mnemonic: str) -> str:
        if mnemonic not in cls._DEST:
            raise ValueError(f"Unknown dest mnemonic: '{mnemonic}'")
        return cls._DEST[mnemonic]

    @classmethod
    def comp(cls, mnemonic: str) -> str:
        if mnemonic not in cls._COMP:
            raise ValueError(f"Unknown comp mnemonic: '{mnemonic}'")
        return cls._COMP[mnemonic]

    @classmethod
    def jump(cls, mnemonic: str) -> str:
        if mnemonic not in cls._JUMP:
            raise ValueError(f"Unknown jump mnemonic: '{mnemonic}'")
        return cls._JUMP[mnemonic]


# ---------------------------------------------------------------------------
# Assembler (two-pass)
# ---------------------------------------------------------------------------

class Assembler:
    """
    Two-pass Hack assembler.

    Pass 1: scan for label declarations (L-instructions) and record their
            ROM addresses in the symbol table.
    Pass 2: translate every A and C instruction to 16-bit binary, resolving
            variable symbols on the fly.
    """

    def __init__(self, filepath: str):
        if not filepath.endswith(".asm"):
            raise ValueError("Input file must have a .asm extension")
        self._filepath = filepath
        self._parser = Parser(filepath)
        self._symbols = SymbolTable()
        self._output: list[str] = []

    def assemble(self) -> list[str]:
        self._first_pass()
        self._second_pass()
        return self._output

    # ------------------------------------------------------------------
    # Pass 1 — build the label → ROM-address entries
    # ------------------------------------------------------------------

    def _first_pass(self) -> None:
        rom_address = 0
        while self._parser.has_more_lines():
            self._parser.advance()
            itype = self._parser.instruction_type

            if itype == Parser.L_INSTRUCTION:
                label = self._parser.symbol
                self._symbols.add_entry(label, rom_address)
            else:
                # A and C instructions each occupy one ROM word
                rom_address += 1

    # ------------------------------------------------------------------
    # Pass 2 — generate binary
    # ------------------------------------------------------------------

    def _second_pass(self) -> None:
        self._parser.reset()
        while self._parser.has_more_lines():
            self._parser.advance()
            itype = self._parser.instruction_type

            if itype == Parser.L_INSTRUCTION:
                continue  # Labels generate no code

            if itype == Parser.A_INSTRUCTION:
                self._output.append(self._translate_a())
            else:
                self._output.append(self._translate_c())

    def _translate_a(self) -> str:
        sym = self._parser.symbol

        if sym.isdigit():
            value = int(sym)
        elif self._symbols.contains(sym):
            value = self._symbols.get_address(sym)
        else:
            value = self._symbols.add_variable(sym)

        if value < 0 or value > 32767:
            raise ValueError(f"A-instruction value out of range: {value}")

        return "0" + format(value, "015b")

    def _translate_c(self) -> str:
        comp_bits = Code.comp(self._parser.comp)
        dest_bits = Code.dest(self._parser.dest)
        jump_bits = Code.jump(self._parser.jump)
        return "111" + comp_bits + dest_bits + jump_bits

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------

    def write(self) -> str:
        """Write the assembled binary to a .hack file; return the output path."""
        out_path = self._filepath.replace(".asm", ".hack")
        with open(out_path, "w") as f:
            f.write("\n".join(self._output) + "\n")
        return out_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <file.asm>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"Error: file not found — {filepath}")
        sys.exit(1)

    assembler = Assembler(filepath)
    assembler.assemble()
    out = assembler.write()
    print(f"✓ Assembled → {out}")


if __name__ == "__main__":
    main()