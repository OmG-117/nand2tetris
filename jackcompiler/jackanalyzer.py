import glob
import sys


def main():
    # Get the target directory from the command line args.
    input_directory = sys.argv[1]

    # Get a list of all Jack files in the supplied directory. If no Jack files
    # exist or if the path is invalid, raise an error.
    target_files = [f for f in glob.glob(input_directory + '*.jack')]
    if not target_files:
        raise ValueError('Invalid directory name')

    # Iterate through each target file and compile it separately.
    for target_file in target_files:
        output_file = target_file[ :-5] + '.xml'
        print(target_file, output_file)


if __name__ == '__main__':
    main()
