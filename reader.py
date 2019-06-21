def tokenize(line):
	tokens = []
	buff = ''

	for ch in line:
		if ch in ',{}[]():"\'+-':
			if len(buff) > 0: tokens.append(buff)
			tokens.append(ch)
			buff = ''
		elif ch == ' ':
			buff += ch
			if len(buff) > 0: tokens.append(buff)
			buff = ''
		else:
			buff += ch

	if len(buff) > 0:
		tokens.append(buff)
	return tokens

def broad_tokenize(line):
	return line.split(' ')

def tab_depth(line):
	c = 0
	for ch in line:
		if ch == '\t': c += 1
		else:
			break
	return c