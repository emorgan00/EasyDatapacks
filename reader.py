def tokenize(line):
	tokens = []
	buff = ''

	for ch in line:
		buff += ch
		if ch in ' ,{}[]():"\'+-':
			tokens.append(buff)
			buff = ''

	if len(buff) > 0:
		tokens.append(buff)
	print tokens
	return tokens