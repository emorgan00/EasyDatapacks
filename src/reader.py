class Token:

	def __init__(this, tstr, ttype):
		this.str = tstr
		this.type = ttype

	def __str__(this):
		return this.str

# return a list of all the individual tokens in a string.
def tokenize(line):
	tokens = []
	buff = ''

	for ch in line:
		if ch in '=,{}[]():"\'+-*<>%\\/':
			if len(buff) > 0: tokens.append(buff)
			tokens.append(ch)
			buff = ''
		elif ch in ' 0123456789':
			buff += ch
			if len(buff) > 0: tokens.append(buff)
			buff = ''
		else:
			buff += ch

	if len(buff) > 0:
		tokens.append(buff)
	return tokens

# returns a list of the seperate arguments in a string
def broad_tokenize(line):
	stack = []
	tokens = line.split(' ')

	for token in tokens:
		stack.append(token)

	return stack

def tab_depth(line):
	c = 0
	for ch in line:
		if ch == '\t': c += 1
		else:
			break
	return c

# returns whether this is a valid name for a funcname or parameter
def valid_name(expression):
	for c in expression:
		if c not in 'qwertyuiopasdfghjklzxcvbnm#_':
			return False
	return True