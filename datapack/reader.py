# return a list of all the individual tokens in a string.
def tokenize(line):
    tokens = []
    buff = ''
    inquote = False

    for ch in line:
        if ch in '"\'':
            if len(buff) > 0:
                tokens.append(buff)
            tokens.append(ch)
            buff = ''
            inquote = not inquote
        elif inquote:
            buff += ch
            continue
        elif ch in '=,{}[]():+-*<>%\\/':
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
    tokens = tokenize(line)

    stack, token, depth, quote = [], '', 0, False

    for subtoken in tokens:
        token += subtoken

        if subtoken in '"\'':
            quote = not quote
        elif subtoken in '[{':
            depth += 1
        elif subtoken in ']}':
            depth -= 1

        if depth == 0 and not quote and token[-1] == ' ':
            if len(token.strip()) > 0:
                stack.append(token.strip())
                token = ''

    if len(token) > 0:
        stack.append(token)
    return stack


# return the level of indentation of the line
def tab_depth(line, tab_width):
    t, s = 0, 0
    for ch in line:
        if ch == '\t':
            t += 1
        elif ch == ' ':
            s += 1
        else:
            break

    if s % tab_width != 0:
        return None
    return t + s / tab_width


# returns whether this is a valid name for a funcname or parameter
def valid_name(expression):
    for c in expression:
        if c not in 'qwertyuiopasdfghjklzxcvbnm#_':
            return False
    return True

print(tokenize('"Hello world!"'))