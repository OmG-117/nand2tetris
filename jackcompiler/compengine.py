from tokenizer import TokenList

# Set of all the native types in the Jack grammar.
TYPES = {'int', 'char', 'boolean'}

# Set of all the statement keywords in the Jack grammar.
STATEMENTS = {'let', 'if', 'while', 'do', 'return'}

# Set of all the operators in the Jack grammar.
OPS = {'+', '-', '*', '/', '&', '|', '<', '>', '='}

# Set of all the non-terminals in the XML output spec.
NON_TERMINALS = {
    'class', 'classVarDec', 'subroutineDec', 'parameterList', 'subroutineBody',
    'varDec', 'statements', 'whileStatement', 'ifStatement', 'returnStatement',
    'letStatement', 'doStatement', 'expression', 'term', 'expressionList'
}

# Recursive class to form a parse tree of the compiled tokens.
class ParseTree:
    def __init__(self):
        self.children = []

    def add_token(self, token):
        self.children.append((token.type, token.value))

    def add_subtree(self, tag, tree):
        self.children.append((tag, tree))

    def as_xml(self, indent_level = 2, to_spec = False):
        string = ''
        padding = ' ' * indent_level
        for tag, value in self.children:
            if type(value) is ParseTree:                    
                value = value.as_xml(indent_level, to_spec)
                if to_spec and tag not in NON_TERMINALS:
                    string += value
                else:
                    value = value.replace('\n', '\n' + padding)
                    string += f'\n<{tag}>{value}\n</{tag}>'
            else:
                if to_spec and type(value) is str:
                    value = value.replace('"', '&quot;')
                    value = value.replace('&', '&amp;')
                    value = value.replace('<', '&lt;')
                    value = value.replace('>', '&gt;')
                string += f'\n<{tag}> {value} </{tag}>'
        return string

    def __str__(self):
        return self.as_xml()


# Function to test the compilation engine, including error reporting.
def test(code: str):
    tokens = TokenList(code)
    try:
        output = compile_file(tokens)
    except ValueError as err:
        tokens.error(err)
    print(output)


# Helper function for eating an identifier.
def eat_identifier_helper(tokens: TokenList, tree: ParseTree):
    if (token := tokens.pop()).type == 'identifier':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid identifier "{token.value}"'))


# Helper function for eating an expected symbol.
def eat_symbol_helper(tokens: TokenList, tree: ParseTree, symbol: str):
    if (token := tokens.pop()).value == symbol:
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Expected "{symbol}"'))


# Helper function for compiling variable declarations.
def variable_declaration_helper(tokens: TokenList, tree: ParseTree):

    # Eat the keyword or identifier indicating the type of the variable.
    if (token := tokens.pop()).value in TYPES:
        tree.add_token(token)
    elif token.type == 'identifier':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid type "{token.value}"'))

    # Eat the identifier representing the name of the first variable.
    eat_identifier_helper(tokens, tree)

    # Until a ';' token is encountered, eat ',' token and identifier pairs
    # that indicate additional variables being declared.
    while (token := tokens.pop()).value != ';':
        if token.value == ',':
            tree.add_token(token)
        else:
            tokens.error(ValueError('Expected "," or ";"'))
        eat_identifier_helper(tokens, tree)

    # Add the ';' token indicating the end of the statement.
    tree.add_token(token)


# Helper function for compiling curly bracketed statements.
def bracketed_statements_helper(tokens: TokenList, tree: ParseTree):

    # Eat the '{' token indicating the start of the statement body.
    eat_symbol_helper(tokens, tree, '{')

    # Eat the statements.
    tree.add_subtree('statements', compile_statements(tokens))

    # Eat the '}' token indicating the end of the statement body.
    eat_symbol_helper(tokens, tree, '}')


# Entry function for converting a TokenList into a ParseTree.
def compile_file(tokens: TokenList):
    tree = ParseTree()

    # Look for class declarations.
    while tokens.get().value == 'class':
        tree.add_subtree('class', compile_class(tokens))

    # If anything but a class declaration is encountered before the end of the
    # file is reached, raise an error.
    if tokens.pop().type != 'eof':
        tokens.error(ValueError('All top level declarations must be classes'))

    return tree


# 'class' className '{' classVarDec* subroutineDec* '}'
def compile_class(tokens: TokenList):
    tree = ParseTree()

    # Eat the 'class' keyword at the top of the list.
    if (token := tokens.pop()).value == 'class':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid class declaration'))

    # Eat the identifier representing the name of the class.
    eat_identifier_helper(tokens, tree)

    # Eat the '{' token indicating the start of the class body.
    eat_symbol_helper(tokens, tree, '{')

    # Look for keywords indicating a class variable or subroutine declaration 
    # and call the appropriate compile function.
    while (token := tokens.get()).value != '}':
        if token.value in ('static', 'field'):
            tree.add_subtree('classVarDec', compile_class_var_dec(tokens))
        elif token.value in ('constructor', 'function', 'method'):
            tree.add_subtree('subroutineDec', compile_subroutine_dec(tokens))
        else:
            tokens.error(ValueError(f'Unexpected token "{tokens.pop().value}"'))

    # Eat the '}' token indicating the end of the class body.
    eat_symbol_helper(tokens, tree, '}')

    return tree


# ('static' | 'field') type varName (',' varName)* ';'
def compile_class_var_dec(tokens: TokenList):
    tree = ParseTree()

    # Eat the keyword indicating whether the variable is static or not.
    if (token := tokens.pop()).value in ('static', 'field'):
        tree.add_token(token)
    else:
        tokens.error(ValueError('Invalid class variable declaration'))

    # Eat the rest of the variable declaration in the helper function.
    variable_declaration_helper(tokens, tree)

    return tree


# ('constructor' | 'function' | 'method') ('void' | type) subroutineName
# '(' parameterList ')' subroutineBody
def compile_subroutine_dec(tokens: TokenList):
    tree = ParseTree()

    # Eat the keyword indicating the type of this subroutine.
    if (token := tokens.pop()).value in ('constructor', 'function', 'method'):
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid subroutine declaration'))

    # Eat the keyword or identifier indicating the return value type.
    if (token := tokens.pop()).value in ('void', *TYPES):
        tree.add_token(token)
    elif token.type == 'identifier':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid type "{token.value}"'))

    # Eat the identifier representing the name of this subroutine.
    eat_identifier_helper(tokens, tree)

    # Eat the '(' token indicating the start of the parameterList.
    eat_symbol_helper(tokens, tree, '(')

    # Eat the parameterList.
    tree.add_subtree('parameterList', compile_parameter_list(tokens))

    # Eat the ')' token indicating the end of the parameterList.
    eat_symbol_helper(tokens, tree, ')')

    # Eat the subroutineBody.
    tree.add_subtree('subroutineBody', compile_subroutine_body(tokens))

    return tree


# ((type varName) (',' type varName)*)?
def compile_parameter_list(tokens: TokenList):
    tree = ParseTree()

    # Check if the next token is a keyword or identifier indicating the type
    # of a parameter. If it is, eat it and then eat the identifier representing
    # the parameter's name. Else, only a ')' token is valid.
    token = tokens.get()
    if token.value in TYPES or token.type == 'identifier':
        tree.add_token(tokens.pop())
        eat_identifier_helper(tokens, tree)
    elif token.value != ')':
        tokens.error(ValueError(f'Invalid type "{tokens.pop().value}"'))

    # Look to see if the next token is ')'. If it is not, eat a ',' token,
    # a keyword or identifier, and a final identifier indicating a parameter.
    while tokens.get().value != ')':
        if (token := tokens.pop()).value == ',':
            tree.add_token(token)
        else:
            tokens.error(ValueError('Expected "," or ")"'))
        if (token := tokens.pop()).value in TYPES:
            tree.add_token(token)
        elif token.type == 'identifier':
            tree.add_token(token)
        else:
            tokens.error(ValueError(f'Invalid type "{token.value}"'))
        eat_identifier_helper(tokens, tree)

    return tree


# '{' varDec* statements '}'
def compile_subroutine_body(tokens: TokenList):
    tree = ParseTree()

    # Eat the '{' token indicating the start of the subroutine body.
    eat_symbol_helper(tokens, tree, '{')

    # While the next token is the 'var' keyword, we are still in the varDec
    # area of the body, so call the appropriate compile function.
    while tokens.get().value == 'var':
        tree.add_subtree('varDec', compile_var_dec(tokens))

    # Eat the statements.
    tree.add_subtree('statements', compile_statements(tokens))

    # Eat the '}' token indicating the end of the subroutine body.
    eat_symbol_helper(tokens, tree, '}')

    return tree


# 'var' type varName (',' varName)* ';'
def compile_var_dec(tokens: TokenList):
    tree = ParseTree()

    # Eat the 'var' keyword at the top of the list.
    if (token := tokens.pop()).value == 'var':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid variable declaration'))

    # Eat the rest of the variable declaration in the helper function.
    variable_declaration_helper(tokens, tree)

    return tree


# statement*
def compile_statements(tokens: TokenList):
    tree = ParseTree()

    # Until the next token is '}', look for keywords indicating a statement and
    # call the appropriate compile function.
    while (token := tokens.get()).value in STATEMENTS:
        if token.value == 'let':
            tree.add_subtree('letStatement', compile_let_statement(tokens))
        elif token.value == 'if':
            tree.add_subtree('ifStatement', compile_if_statement(tokens))
        elif token.value == 'while':
            tree.add_subtree('whileStatement', compile_while_statement(tokens))
        elif token.value == 'do':
            tree.add_subtree('doStatement', compile_do_statement(tokens))
        elif token.value == 'return':
            tree.add_subtree('returnStatement', compile_return_statement(tokens))
        else:
            tokens.error(ValueError(f'Unexpected token "{tokens.pop().value}"'))

    return tree


# 'let' varName ('[' expression ']')? '=' expression ';'
def compile_let_statement(tokens: TokenList):
    tree = ParseTree()
    
    # Eat the 'let' keyword at the top of the list.
    if (token := tokens.pop()).value == 'let':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid let statement'))

    # Eat the identifier representing the variable being assigned to.
    eat_identifier_helper(tokens, tree)

    # Check for a '[' token indicating an array access.
    if tokens.get().value == '[':
        tree.add_token(tokens.pop())
        tree.add_subtree('expression', compile_expression(tokens))
        eat_symbol_helper(tokens, tree, ']')

    # Eat the '=' token that is part of the syntax.
    eat_symbol_helper(tokens, tree, '=')

    # Eat the expression being assigned.
    tree.add_subtree('expression', compile_expression(tokens))

    # Eat the ';' token indicating the end of the statement.
    eat_symbol_helper(tokens, tree, ';')

    return tree


# 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
def compile_if_statement(tokens: TokenList):
    tree = ParseTree()

    # Eat the 'if' keyword at the top of the list.
    if (token := tokens.pop()).value == 'if':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid if statement'))

    # Eat the '(' token indicating the start of the condition.
    eat_symbol_helper(tokens, tree, '(')

    # Eat the expression representing the condition.
    tree.add_subtree('expression', compile_expression(tokens))

    # Eat the ')' token indicating the end of the condition.
    eat_symbol_helper(tokens, tree, ')')

    # Eat the bracketed statements.
    bracketed_statements_helper(tokens, tree)

    # Check next token to see if there is an else condition.
    if tokens.get().value == 'else':
        tree.add_token(tokens.pop())
        bracketed_statements_helper(tokens, tree)

    return tree


# 'while' '(' expression ')' '{' statements '}'
def compile_while_statement(tokens: TokenList):
    tree = ParseTree()

    # Eat the 'while' keyword at the top of the list.
    if (token := tokens.pop()).value == 'while':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid while statement'))

    # Eat the '(' token indicating the start of the condition.
    eat_symbol_helper(tokens, tree, '(')

    # Eat the expression representing the condition.
    tree.add_subtree('expression', compile_expression(tokens))

    # Eat the ')' token indicating the end of the condition.
    eat_symbol_helper(tokens, tree, ')')

    # Eat the bracketed statements.
    bracketed_statements_helper(tokens, tree)

    return tree


# 'do' subroutineCall ';'
def compile_do_statement(tokens: TokenList):
    tree = ParseTree()

    # Eat the 'do' keyword at the top of the list.
    if (token := tokens.pop()).value == 'do':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid do statement'))

    # Eat the subroutine call.
    tree.add_subtree('subroutineCall', compile_subroutine_call(tokens))

    # Eat the ';' token indicating the end of the statement.
    eat_symbol_helper(tokens, tree, ';')

    return tree


# 'return' expression? ';'
def compile_return_statement(tokens: TokenList):
    tree = ParseTree()

    # Eat the 'return' keyword at the top of the list.
    if (token := tokens.pop()).value == 'return':
        tree.add_token(token)
    else:
        tokens.error(ValueError(f'Invalid return statement'))

    # Eat the optional expression.
    if tokens.get().value != ';':
        tree.add_subtree('expression', compile_expression(tokens))

    # Eat the ';' token indicating the end of the statement.
    eat_symbol_helper(tokens, tree, ';')

    return tree


# term (op term)*
def compile_expression(tokens: TokenList):
    tree = ParseTree()

    # Eat the first term.
    tree.add_subtree('term', compile_term(tokens))

    # While the next token is an operator, eat it and the following term.
    while tokens.get().value in OPS:
        tree.add_token(tokens.pop())
        tree.add_subtree('term', compile_term(tokens))

    return tree


# integerConstant | stringConstant | keywordConstant | varName | varName 
# '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
def compile_term(tokens: TokenList):
    tree = ParseTree()

    # If the next token is a literal, it can be eaten as is.
    if (token := tokens.get()).type in ('integerConstant', 'stringConstant'):
        tree.add_token(tokens.pop())

    # If the next token is a keyword constant, it can be eaten as is.
    elif token.value in ('true', 'false', 'null', 'this'):
        tree.add_token(tokens.pop())

    # If the next token is an identifier, it may be a variable name, an array
    # access, or a subroutine call to one which may be in another class. Look
    # ahead to the next to next token to determine what it is.
    elif token.type == 'identifier':
        if (n2n_token := tokens.get(1)).value == '[':
            tree.add_token(tokens.pop())
            tree.add_token(tokens.pop())
            tree.add_subtree('expression', compile_expression(tokens))
            eat_symbol_helper(tokens, tree, ']')
        elif n2n_token.value in ('(', '.'):
            tree.add_subtree('subroutineCall', compile_subroutine_call(tokens))
        else:
            tree.add_token(tokens.pop())

    # If the next token is '(', it must indicate a paranthesized expression.
    elif token.value == '(':
        tree.add_token(tokens.pop())
        tree.add_subtree('expression', compile_expression(tokens))
        eat_symbol_helper(tokens, tree, ')')

    # If the next token is a unary operator, it must be followed by a term.
    elif token.value in ('-', '~'):
        tree.add_token(tokens.pop())
        tree.add_subtree('term', compile_term(tokens))

    # If the next token is none of these, raise an error.
    else:
        tokens.error(ValueError(f'Unexpected token "{tokens.pop().value}"'))

    return tree


# subroutineName '(' expressionList ')' | 
# (className | varName) '.' subroutineName '(' expressionList ')'
def compile_subroutine_call(tokens: TokenList):
    tree = ParseTree()

    # Eat the identifier representing the name of the subroutine/class/object.
    eat_identifier_helper(tokens, tree)

    # If the next token is '.', the last identifier represented a class/object.
    # Eat it and the identifier representing the name of the subroutine.
    if tokens.get().value == '.':
        tree.add_token(tokens.pop())
        eat_identifier_helper(tokens, tree)

    # Eat the '(' token indicating the start of the expressionList.
    eat_symbol_helper(tokens, tree, '(')

    # Eat the expressionList.
    tree.add_subtree('expressionList', compile_expression_list(tokens))

    # Eat the ')' token indicating the end of the expressionList.
    eat_symbol_helper(tokens, tree, ')')

    return tree


# (expression (',' expression)* )?
def compile_expression_list(tokens: TokenList):
    tree = ParseTree()

    # If the next token is not ')', eat the first expression.
    if tokens.get().value != ')':
        tree.add_subtree('expression', compile_expression(tokens))

    # Look to see if the next token is ')'. If it is not, eat a ',' token,
    # and the following expression. Repeat.
    while tokens.get().value != ')':
        if (token := tokens.pop()).value == ',':
            tree.add_token(token)
        else:
            tokens.error(ValueError('Expected "," or ")"'))
        tree.add_subtree('expression', compile_expression(tokens))

    return tree
