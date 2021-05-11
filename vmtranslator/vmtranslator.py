import os
import re
import sys

import generateasm

DEBUG = True

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
    output = ''
    for num, line in enumerate(code.split('\n'), 1):
        if statement := re.sub(r'\s*//.*', '', line):
            try:
                command = Command(statement, filename)
                asm_code = ASM_GENERATOR_MAP[command.type](command)
                asm_code = asm_code.replace('#', f'{filename}.{num}')
                comment = ('// ' + statement + '\n' if DEBUG else '')
                output += comment + asm_code
            except ValueError as error:
                raise ValueError(f'Syntax error in line {num}: {error}')
    return output

def main():
    # Get the target directory from the command line args.
    input_directory = sys.argv[1]

    # Get a list of all VM code files in the supplied directory.
    print(f'Looking for .vm files in {input_directory}')
    target_paths = [
        os.path.join(input_directory, f)
        for f in os.listdir(input_directory)
        if os.path.splitext(f)[1] == '.vm'
    ]

    # If there are no .vm files, raise an error
    if not target_paths:
        raise ValueError('No .vm files in specified directory')
    else:
        print(f'Compiling {len(target_paths)} files in {input_directory}')

    # Iterate through each target file and compile it separately.
    compiled_code = []
    for target_path in target_paths:
        print(f'Translating {target_path}')
        with open(target_path, 'r') as f:
            target_contents = f.read()
        
        # Perform the translation, extracting the filename before calling
        filename = os.path.splitext(os.path.basename(target_path))[0]
        output = translate(target_contents, filename)

        compiled_code.append(output)

    # Write the translated instructions to a .asm file
    output_filename = os.path.basename(input_directory) + '.asm'
    output_path = os.path.join(input_directory, output_filename)
    with open(output_path, 'w') as f:
        f.write(generateasm.bootstrap() + ''.join(compiled_code))

    print(f'Wrote translated program to {output_path}')

if __name__ == '__main__':
    main()
