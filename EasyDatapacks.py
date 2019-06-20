from entity import *

class Function:

	def __init__(this, header, params):
		this.header = header
		this.params = params
		this.body = ''

	def __str__(this):
		return this.header+':\n\n'+this.body

def create_function(name, params, body):
	'''create a new function with a leading path, any number of parameters, and a body'''

	cmds = []
	refs = {}

	def tokenize(line):
		return line.split(' ')

	def evaluate_command(tokens):

		# assignment
		if tokens[1] == '=':
			refs[name+'_'+tokens[0]] = evaluate_expression(name+'_'+tokens[0], tokens[2:])

		# vanilla command
		else:
			for i in xrange(len(tokens)):
				while name+'_'+tokens[i] in refs:
					if refs[name+'_'+tokens[i]] == None:
						tokens[i] = select_entity(name+'_'+tokens[i])
					else:
						tokens[i] = refs[name+'_'+tokens[i]]
			cmds.append(' '.join(tokens))

	def evaluate_expression(destination, tokens):

		if destination in refs and refs[destination] == None:
			cmds.append(clear_tag(destination))

		if len(tokens) == 1:
			token = name+'_'+tokens[0]
			# entity
			if tokens[0][0] == '@':
				cmds.append('tag %s add %s' % (tokens[0], destination))
				return None

			# ref to entity
			elif token in refs and refs[token] == None:
				cmds.append('tag %s add %s' % (select_entity(token), destination))
				return None

			# ref to constant
			elif token in refs:
				return refs[token]

			else:
				return ' '.join(tokens)

		else:
			return ' '.join(tokens)

	for line in body.split('\n'):
		line = line.strip()
		if len(line) == 0: continue
		evaluate_command(tokenize(line))

	f = Function(name, params)
	f.body = '\n'.join(cmds)
	return f

print create_function('main', [], '''

a = @p
b = @r
a = b
s = "hello!"
b = s
tellraw a s
tellraw b s

''')