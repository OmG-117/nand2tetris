import os
import sys

from compengine import compile_file
from tokenizer import TokenList


def main():
    # Get the target directory from the command line args.
    input_path = sys.argv[1]

    if os.path.isdir(input_path):
        # Get a list of all Jack files in the supplied directory.
        print(f'Looking for .jack files in {input_path}')
        target_paths = [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if os.path.splitext(f)[1] == '.jack'
        ]
        # If there are no .jack files, raise an error
        if not target_paths:
            raise ValueError('No .jack files in specified directory')
        else:
            print(f'Compiling {len(target_paths)} file(s) at {input_path}')
    else:
        # Store the path of the provided file in a list
        print(f'Compiling file at {input_path}')
        target_paths = [input_path]

    # Iterate through each target file and compile it separately.
    for target_path in target_paths:
        print(f'Analyzing {target_path}')
        with open(target_path, 'r') as f:
            target_contents = f.read()
        
        # Tokenize the code and generate the parse tree
        try:
            token_list = TokenList(target_contents)
            parse_tree = compile_file(token_list)
        except ValueError as exc:
            raise SystemExit(exc)

        # Write the parse tree to a .xml file
        output_path = os.path.splitext(target_path)[0] + '.xml'
        with open(output_path, 'w') as f:
            f.write(parse_tree.as_xml(2, True)[1: ] + '\n')

        print(f'Wrote parsed output to {output_path}')

if __name__ == '__main__':
    main()
