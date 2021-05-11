# Set of all keywords in the Jack grammar.
KEYWORDS = {
    'class',
    'constructor',
    'function',
    'method',
    'field',
    'static',
    'var',
    'int',
    'char',
    'boolean',
    'void',
    'true',
    'false',
    'null',
    'this',
    'let',
    'do',
    'if',
    'else',
    'while',
    'return',
}

# Set of all the symbols in the Jack grammar.
SYMBOLS = {
    '{', '}', '(', ')', '[', ']',
    '.', ',', ';', '+', '-', '*', '/',
    '&', '|', '<', '>', '=', '~',
}

# Simple class that takes a token string as input and classifies it into the
# correct type and correctly formats its value.
class Token:
    def __init__(self, token: str):
        if token == '':
            self.type = 'eof'
            self.value = token
        elif token in KEYWORDS:
            self.type = 'keyword'
            self.value = token
        elif token in SYMBOLS:
            self.type = 'symbol'
            self.value = token
        elif token[0].isdigit():
            self.type = 'integerConstant'
            self.value = int(token)
        elif token[0] == '"':
            self.type = 'stringConstant'
            self.value = token[1:-1]
        else:
            self.type = 'identifier'
            self.value = token

    def __repr__(self):
        return f'{self.type}: {self.value}'


# Class to generate and store a list of Tokens from the given code, along with 
# metadata to be able to generate descriptive error messages later.
class TokenList:
    def __init__(self, code: str):
        self.original = code
        self.tokens = []
        self.map = []
        self.pos = 0
        i = 0

        # Add a newline at the end of the code if there isn't one there
        if not code.endswith('\n'):
            code += '\n'

        # Try block to catch the iteration reaching the end of the code while
        # still scanning a identifier or literal.
        try:
            while i < len(code):
                char = code[i]

                # If the character is a forward slash, check if we're dealing
                # with a comment, and if so, skip till the end of the comment.
                if char == '/':
                    # If the next character is also a slash, then this is a
                    # one line comment, so skip up to the next newline char.
                    if code[i + 1] == '/':
                        i += 2
                        while code[i] != '\n':
                            i += 1
                        i += 1
                        continue
                    # If the next character is an asterix, then this is a block
                    # comment, so skip until a block comment close is found.
                    elif code[i + 1] == '*':
                        i += 2
                        while code[i:i + 2] != '*/':
                            i += 1
                        i += 2
                        continue

                # If the character is a symbol, generate a Token from it as is.
                if char in SYMBOLS:
                    self.map.append(i)
                    self.tokens.append(Token(char))
                    i += 1

                # If the character is a digit, check if subsequent characters
                # are also digits. If they are, append them to the Token.
                elif char.isdigit():
                    self.map.append(i)
                    token = char
                    while code[(i := i + 1)].isdigit():
                        token += code[i]
                    if code[i] in SYMBOLS or code[i].isspace():
                        self.tokens.append(Token(token))
                    else:
                        self.error(ValueError('Invalid integer'), True)

                # If the character is a double quote, then this must be the
                # start of a string. Append characters until the next quote.
                elif char == '"':
                    self.map.append(i)
                    token = char
                    while code[(i := i + 1)] != '"':
                        token += code[i]
                    token += code[i]
                    self.tokens.append(Token(token))
                    i += 1

                # If the character is an alphabet or underscore, then it may
                # either be the start of an identifier or keyword.
                elif char.isalpha() or char == '_':
                    self.map.append(i)
                    token = char
                    while code[(i := i + 1)].isalnum() or code[i] == '_':
                        token += code[i]
                    if code[i] in SYMBOLS or code[i].isspace():
                        self.tokens.append(Token(token))
                    else:
                        self.error(ValueError(
                            f'Invalid character in identifier "{code[i]}"'
                        ), True)

                # If the character is whitespace, just continue.
                elif char.isspace():
                    i += 1

                # If it's none of the above, raise an error.
                else:
                    self.error(ValueError('Invalid character'), True)
            
            # Add an extra EOF token.
            self.tokens.append(Token(''))

        except IndexError:
            raise ValueError('Unexpected EOF')

    # Function to add line and column metadata to a syntax error.
    def error(self, error: Exception, incomplete: bool = False):
        if incomplete:
            pos = self.map[-1]
        else:
            pos = self.map[self.pos - 1]

        code = self.original

        last_newline = pos - 1
        while code[last_newline] != '\n' and last_newline > 0:
            last_newline -= 1

        next_newline = pos + 1
        while code[next_newline] != '\n' and next_newline < len(code):
            next_newline += 1

        col_num = pos - last_newline
        line_num = 1 + code[ :last_newline + 1].count('\n')

        lines = ''
        if line_num > 1:
            l2l_newline = last_newline - 1
            while code[l2l_newline] != '\n' and l2l_newline > 0:
                l2l_newline -= 1
            lines += str(line_num - 1) + ' '
            lines += ' ' * (len(str(line_num)) - len(str(line_num - 1)))
            lines += code[l2l_newline + 1 : last_newline] + '\n'
        lines += str(line_num) + ' '
        lines += code[last_newline + 1 : next_newline] + '\n'
        lines += ' ' * len(str(line_num)) + ' ' + ''.join(
            char if char.isspace() else ' '
            for char in code[last_newline + 1 : pos]
        ) + '^'

        message = f'Error in line {line_num}, col {col_num}\n\n'
        message += lines + '\n\nSyntax error: ' + str(error)

        raise ValueError(message)

    # Function to return the current token and prime the next token.
    def pop(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    # Function to return a token "skip" positions from the current one.
    def get(self, skip: int = 0):
        return self.tokens[self.pos + skip]

    # Function to neatly display all the parsed tokens.
    def __str__(self):
        return str([str(token) for token in self.tokens])
