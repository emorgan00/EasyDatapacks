from entity import *
from reader import *

class Function:

	def __init__(this, header, params):
		this.header = header
		this.params = params
		this.body = ''

	def __str__(this):
		return this.header+':\n\tparams: '+str(this.params)+'\n\n\t'+this.body.replace('\n', '\n\t')

	def create_instance(this, params):
		pass

def create_function(pack, name, params, refs, body, functions):
	pointer = 0
	'''create a new function with a leading path, any number of parameters, a global reference dictionary, and a body'''

	cmds = []
	refs = refs.copy()

	def get_function(funcname):

		paths = name.split('.')
		for i in xrange(1, len(paths)+1):
			funcpath = '.'.join(paths[:i])+'.'+funcname
			if funcpath in functions:
				return functions[funcpath]
		return None

	def evaluate_command(tokens, pointer):

		# assignment
		if len(tokens) > 1 and tokens[1].strip() == '=':
			token = name+'.'+tokens[0].strip()
			refs[token] = evaluate_expression(token, tokens[2:])

		# definition
		elif tokens[0].strip() == 'def':
			funcname = name+'.'+tokens[1].strip()
			funcparams = {}
			for token in tokens[2:]:
				if all(c.isalnum() or c in '_*' for c in token):
					funcparams[token.replace('*', '')] = '*' in token
			funcbody = []
			while pointer < len(body) and body[pointer][0] in '\t\n':
				if body[pointer][0] == '\t':
					funcbody.append(body[pointer][1:])
				else:
					funcbody.append(body[pointer])
				pointer += 1
			functions[funcname] = create_function(pack, funcname, funcparams, refs, funcbody, functions)

		# custom function call
		elif get_function(tokens[0].strip()) != None:
			func = get_function(tokens[0].strip())
			# handle params
			funcparams = broad_tokenize(''.join(tokens[1:]))
			for i, p in enumerate(func.params):
				if func.params[p]:
					evaluate_expression(func.header+'.'+p, [funcparams[i]])
			cmds.append('function '+pack+':'+func.header)

		# vanilla command
		else:
			for i in xrange(len(tokens)):
				token = name+'.'+tokens[i].strip()
				if token in refs:
					if refs[token] == None:
						tokens[i] = select_entity(token)+(' ' if tokens[i][-1] == ' ' else '')
					else:
						tokens[i] = refs[token]+(' ' if tokens[i][-1] == ' ' else '')

			cmds.append(''.join(tokens))

		return pointer

	def evaluate_expression(destination, tokens):

		if destination in refs and refs[destination] == None:
			cmds.append(clear_tag(destination))

		if len(tokens) == 1:
			token = name+'.'+tokens[0].strip()
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

			# constant
			else:
				return ''.join(tokens)

		else:
			return ''.join(tokens)

	# handle params
	for p in params:
		if params[p]:
			refs[name+'.'+p] = None

	# generate body
	while pointer < len(body):
		line = body[pointer].strip()
		pointer += 1
		if len(line.strip()) == 0: continue
		pointer = evaluate_command(tokenize(line), pointer)

	# clean params
	for p in params:
		if params[p]:
			cmds.append(clear_tag(name+'.'+p))

	f = Function(name, params)
	f.body = '\n'.join(cmds)
	return f