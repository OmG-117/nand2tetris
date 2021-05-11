def bootstrap():
    return f'''\
    @256
    D=A
    @SP
    M=D
    @Sys.init
    0;JMP
'''

###############################################################################

ARITHMETIC_UNARY_SETUP = '''\
    @SP
    A=M-1
'''

ARITHMETIC_BINARY_SETUP = '''\
    @SP
    AM=M-1
    D=M
    A=A-1
'''

OP_SYMBOL = {
    'neg': '-',
    'not': '!',
    'add': '+',
    'sub': '-',
    'and': '&',
    'or' : '|',
}

def arithmetic_unary_op(op):
    return ARITHMETIC_UNARY_SETUP + f'''\
    M={OP_SYMBOL[op]}M
'''

def arithmetic_binary_op(op):
    return ARITHMETIC_BINARY_SETUP + f'''\
    M=M{OP_SYMBOL[op]}D
'''

def arithmetic_comparison(op):
    return ARITHMETIC_BINARY_SETUP + f'''\
    D=M-D
    M=-1
    @#.T{op.upper()}
    D;J{op.upper()}
    @SP
    A=M-1
    M=0
(#.T{op.upper()})
'''

def c_arithmetic(command):
    if command.arg1 in ('eq', 'gt', 'lt'):
        return arithmetic_comparison(command.arg1)
    elif command.arg1 in ('neg', 'not'):
        return arithmetic_unary_op(command.arg1)
    elif command.arg1 in ('add', 'sub', 'and', 'or'):
        return arithmetic_binary_op(command.arg1)
    else:
        raise ValueError(f'Invalid arithmetic operation "{command.arg1}"')

###############################################################################

SEG_CODE = {
    'local'   : 'LCL',
    'argument': 'ARG',
    'this'    : 'THIS',
    'that'    : 'THAT',
    'pointer' : '3',
    'temp'    : '5',
}

def get_const(value):
    return f'''\
    @{value}
    D=A
'''

def get_std(segment, address):
    return get_const(address) + f'''\
    @{SEG_CODE[segment]}
    A={'A' if segment in ('pointer', 'temp') else 'M'}+D
    D=M
'''

def get_static(filename, address):
    return f'''\
    @{filename}.{address}
    D=M
'''

def c_push(command):
    try:
        int(command.arg2)
    except ValueError:
        raise ValueError(f'Invalid memory segment address "{command.arg2}"')
    if command.arg1 == 'constant':
        getter = get_const(command.arg2)
    elif command.arg1 == 'static':
        getter = get_static(command.filename, command.arg2)
    else:
        try:
            getter = get_std(command.arg1, command.arg2)
        except KeyError:
            raise ValueError(f'Invalid memory segment "{command.arg1}"')
    return getter + f'''\
    @SP
    AM=M+1
    A=A-1
    M=D
'''

def put_addr_std(segment, address):
    return get_const(address) + f'''\
    @{SEG_CODE[segment]}
    D=D+{'A' if segment in ('pointer', 'temp') else 'M'}
    @R15
    M=D
'''

def put_addr_static(filename, address):
    return f'''\
    @{filename}.{address}
    D=A
    @R15
    M=D
'''

def c_pop(command):
    try:
        int(command.arg2)
    except ValueError:
        raise ValueError(f'Invalid memory segment address "{command.arg2}"')
    if command.arg1 == 'static':
        addr_putter = put_addr_static(command.filename, command.arg2)
    else:
        try:
            addr_putter = put_addr_std(command.arg1, command.arg2)
        except KeyError:
            raise ValueError(f'Invalid memory segment "{command.arg1}"')
    return addr_putter + f'''\
    @SP
    AM=M-1
    D=M
    @R15
    A=M
    M=D
'''

###############################################################################

def c_label(command):
    return f'''\
({command.arg1})
'''

def c_goto(command):
    return f'''\
    @{command.arg1}
    0;JMP
'''

def c_if_goto(command):
    return f'''\
    @SP
    AM=M-1
    D=M
    @{command.arg1}
    D;JNE
'''
###############################################################################

def c_function(command):
    try:
        num_lcl_vars = int(command.arg2)
    except ValueError:
        raise ValueError(f'Invalid number of local variables "{command.arg2}"')
    return f'''\
({command.arg1})
    @SP
    A=M\
{("""
    M=0
    A=A+1""" * num_lcl_vars)[ :-10]}
    @{num_lcl_vars}
    D=A
    @SP
    M=M+D
'''

def c_return(command):
    return f'''\
    @LCL    // FRAME = LCL
    D=M
    @R14
    M=D
    @5      // RETURN_ADDRESS = *(FRAME - 5)
    D=-A
    @R14
    A=M+D
    D=M
    @R13
    M=D
    @SP     // D = *(SP - 1)
    A=M-1
    D=M
    @ARG    // *ARG = D
    A=M
    M=D
    D=A+1   // SP = ARG + 1
    @SP
    M=D
    @R14     // THAT = *(--FRAME)
    AM=M-1
    D=M
    @THAT
    M=D
    @R14     // THIS = *(--FRAME)
    AM=M-1
    D=M
    @THIS
    M=D
    @R14     // ARG = *(--FRAME)
    AM=M-1
    D=M
    @ARG
    M=D
    @R14     // LCL = *(--FRAME)
    AM=M-1
    D=M
    @LCL
    M=D
    @R13     // JMP RETURN_ADDRESS
    A=M
    0;JMP    
'''

def c_call(command):
    return f'''\
    @#.RETURN_ADDRESS   // *(++SP) = #.RETURN_ADDRESS
    D=A
    @SP
    A=M
    M=D
    @LCL    // *(++SP) = LCL
    D=M
    @SP
    AM=M+1
    M=D
    @ARG    // *(++SP) = ARG
    D=M
    @SP
    AM=M+1
    M=D
    @THIS   // *(++SP) = THIS
    D=M
    @SP
    AM=M+1
    M=D
    @THAT   // *(++SP) = THAT
    D=M
    @SP
    AM=M+1
    M=D
    @SP     // SP++
    M=M+1
    @{5 + int(command.arg2)}     // ARG = SP - n - 5
    D=-A
    @SP
    D=D+M
    @ARG
    M=D
    @SP     // LCL = SP
    D=M
    @LCL
    M=D
    @{command.arg1}     // JMP TGT_FUNCTION
    0;JMP
(#.RETURN_ADDRESS)
'''
