# return a list of all the individual tokens in a string.
def tokenize(line):
    tokens = []
    buff = ''

    for ch in line:
        if ch in '=,{}[]():"\'+-*<>%\\/':
            if len(buff) > 0:
                tokens.append(buff)
            tokens.append(ch)
            buff = ''
        elif ch in ' 0123456789':
            buff += ch
            if len(buff) > 0:
                tokens.append(buff)
            buff = ''
        else:
            buff += ch

    if len(buff) > 0:
        tokens.append(buff)
    return tokens


# returns a list of the separate arguments in a string
def broad_tokenize(line):
    stack = []
    tokens = line.split(' ')

    for token in tokens:
        if len(token) > 0:
            stack.append(token)

    return stack


# return the level of indentation of the line
def tab_depth(line):
    t, s = 0, 0
    for ch in line:
        if ch == '\t':
            t += 1
        elif ch == ' ':
            s += 1
        else:
            break

    if s % 4 != 0:
        raise Exception('Invalid indentation.')
    return t + s / 4


# returns whether this is a valid name for a funcname or parameter
def valid_name(expression):
    for c in expression:
        if c not in 'qwertyuiopasdfghjklzxcvbnm#_':
            return False
    return True
