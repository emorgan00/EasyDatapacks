# return a list of all the individual tokens in a string.
def tokenize(line):
    tokens = []
    buff = ''
    squote, dquote = False, False

    for ch in line:
        if ch == '"' and not squote:
            if len(buff) > 0:
                tokens.append(buff)
            tokens.append(ch)
            buff = ''
            dquote = not dquote
        elif ch == '\'' and not dquote:
            if len(buff) > 0:
                tokens.append(buff)
            tokens.append(ch)
            buff = ''
            squote = not squote
        elif squote or dquote:
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

    stack, token, depth, squote, dquote = [], '', 0, False, False

    for subtoken in tokens:
        token += subtoken

        if subtoken == '"' and not squote:
            dquote = not dquote
        if subtoken == '\'' and not dquote:
            squote = not squote
        elif subtoken in '[{':
            depth += 1
        elif subtoken in ']}':
            depth -= 1

        if depth == 0 and not quote and token[-1] == ' ':
        if depth == 0 and not squote and not dquote and token[-1] == ' ':
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
        if not (c.isalpha() or c in '#_'):
            return False
    return True

def valid_function(expression):
    for c in expression:
        if not (c.isalpha() or c in '_'):
            return False
    return True

def valid_int(expression):
    if len(expression) > 1:
        return expression[1:].isdigit() and expression[0] in '-0123456789'
    else:
        return expression.isdigit()