import glob
import re
import sys

import generateasm

DEBUG = False

TYPE_MAP = {
    'add'     : 'C_ARITHMETIC',
    'sub'     : 'C_ARITHMETIC',
    'neg'     : 'C_ARITHMETIC',
    'eq'      : 'C_ARITHMETIC',
    'gt'      : 'C_ARITHMETIC',
    'lt'      : 'C_ARITHMETIC',
    'and'     : 'C_ARITHMETIC',
    'or'      : 'C_ARITHMETIC',
    'not'     : 'C_ARITHMETIC',
    'push'    : 'C_PUSH',
    'pop'     : 'C_POP',
    'label'   : 'C_LABEL',
    'goto'    : 'C_GOTO',
    'if-goto' : 'C_IF',
    'function': 'C_FUNCTION',
    'return'  : 'C_RETURN',
    'call'    : 'C_CALL',
}

ASM_GENERATOR_MAP = {
    'C_ARITHMETIC': generateasm.c_arithmetic,
    'C_PUSH'      : generateasm.c_push,
    'C_POP'       : generateasm.c_pop,
    'C_LABEL'     : generateasm.c_label,
    'C_GOTO'      : generateasm.c_goto,
    'C_IF'        : generateasm.c_if_goto,
    'C_FUNCTION'  : generateasm.c_function,
    'C_RETURN'    : generateasm.c_return,
    'C_CALL'      : generateasm.c_call,
}

class Command:
    def __init__(self, command, filename):
        self.filename = filename
        self.arg1 = None
        self.arg2 = None
        terms = command.split()
        try:
            self.type = TYPE_MAP[terms[0]]
        except KeyError:
            raise ValueError(f'Invalid command "{terms[0]}"')
        try:
            if self.type == 'C_ARITHMETIC':
                self.arg1 = terms[0]
            elif self.type != 'C_RETURN':
                self.arg1 = terms[1]
            if self.type in ('C_PUSH', 'C_POP', 'C_FUNCTION', 'C_CALL'):
                self.arg2 = terms[2]
        except IndexError:
            raise ValueError(f'Missing argument for "{terms[0]}"')

def translate(code, filename):
    for num, line in enumerate(code, 1):
        if statement := re.sub(r'\s*//.*', '', line):
            try:
                command = Command(statement, filename)
                asm_code = ASM_GENERATOR_MAP[command.type](command)
                asm_code = asm_code.replace('#', f'{filename[ :-3]}.{num}')
                comment = ('// ' + statement + '\n' if DEBUG else '')
                yield comment + asm_code
            except ValueError as error:
                raise ValueError(f'Syntax error in line {num}: {error}')

def main():
    input_directory = sys.argv[1]
    target_files = [f for f in glob.glob(input_directory + '*.vm')]
    output_file = input_directory + input_directory.split('\\')[-2] + '.asm'
    with open(output_file, 'w') as f_out:
        f_out.write(generateasm.bootstrap())
        for input_file in target_files:
            with open(input_file, 'r') as f_in:
                vm_code = (line.strip() for line in f_in)
                for asm_code in translate(vm_code, input_file.split('\\')[-1]):
                    if not DEBUG:
                        asm_code = re.sub(r'\s*//.*', '', asm_code)
                    f_out.write(asm_code)

    print(f'Wrote translated program into {output_file}')

if __name__ == '__main__':
    main()
