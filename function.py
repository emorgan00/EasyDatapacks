from reader import *
from entity import *

class Namespace:

	def __init__(this, pack, files):

		this.pack = pack
		this.files = files
		this.functions = {}
		this.refs = {}

	def compile(this, verbose):

		for file in this.files:
			with open(file, 'r') as f:
				name = file.split('/')[-1].split('.')[0]
				lines = f.readlines()

				# pre-processing
				lines = [(tab_depth(line), line.strip()) for line in lines if len(line.strip()) > 0 and line.strip()[0] != '#']

				Function([name], {}, lines, this, 0, 0).compile()

		if verbose:
			for f in this.functions:
				print this.functions[f]

class Function:

	def __init__(this, path, params, lines, namespace, start, expecteddepth):

		this.commands = []
		this.path = path
		this.name = '.'.join(path)
		this.namespace = namespace
		this.functions = namespace.functions
		this.refs = namespace.refs
		this.pack = namespace.pack
		this.params = params
		this.lines = lines
		this.pointer = start
		this.locals = []
		this.expecteddepth = expecteddepth
		this.relcounter = 0

	def __str__(this):
		return this.name+': '+str(this.params)+'\n\n\t'+'\n\t'.join(this.commands)+'\n'

	def reference_path(this, tail):

		for i in xrange(len(this.path), 0, -1):
			test_path = '.'.join(this.path[:i])+'.'+tail
			if test_path in this.refs:
				return test_path
		return None

	def function_path(this, tail):

		for i in xrange(len(this.path), 0, -1):
			test_path = '.'.join(this.path[:i])+'.'+tail
			if test_path in this.functions:
				return test_path
		return None

	def compile(this):

		try:
			depth = this.lines[this.pointer][0]
		except:
			raise SyntaxError('Expected content at '+this.name+', nothing found')
		if depth != this.expecteddepth:
			raise SyntaxError('Incorrect indentation at '+this.name)

		# pre-process params into local variables
		for p in this.params:
			this.refs[this.name+'.'+p] = 'e'
			this.locals.append(this.name+'.'+p)

		# pre-process function headers:
		for i, p in enumerate(this.lines[this.pointer:]):
			if p[0] < depth: break
			if p[0] > depth: continue
			if p[1][:3] == 'def':
				tokens = tokenize(p[1])
				funcpath = this.path+[tokens[1].strip()]
				funcparams = {}
				for token in tokens[2:]:
					if all(c.isalnum() or c in '_' for c in token):
						funcparams[token] = 'e'
				if '.'.join(funcpath) in this.functions:
					raise Exception('Duplicate function "'+funcpath[-1]+'" in '+this.name)
				this.functions['.'.join(funcpath)] = Function(funcpath, funcparams, this.lines, this.namespace, this.pointer+i+1, depth+1)

		# process lines
		while this.pointer < len(this.lines):

			if this.lines[this.pointer][0] == depth:
				this.process_line()
			elif this.lines[this.pointer][0] < depth:
				break
			this.pointer += 1

		# dispel locals
		for ref in this.locals:
			if this.refs[ref] == 'e': # an entity
				this.commands.append(clear_tag(ref))
			else: # something else, NOT FINISHED
				pass

			this.refs.pop(ref)

	def process_expression(this, expression):

		ref = expression.strip()

		path = this.reference_path(ref)
		if path != None: # some reference
			if this.refs[path] == 'e': # an entity
				return select_entity(path)+(' ' if expression[-1] == ' ' else '')
			else: # something else, NOT FINISHED
				pass

		# a simple constant
		return expression

	def fork_function(this, line):

		pass

	def process_line(this):

		line = this.lines[this.pointer][1]
		tokens = tokenize(line)

		funcpath = this.function_path(tokens[0].strip())

		# creating a new assignment
		if len(tokens) > 1 and tokens[1].strip() == '=':

			if len(tokens) == 2:
				raise Exception('Expected something after "=" at '+this.name)
			dest = this.reference_path(tokens[0].strip())

			# assigning something for the first time
			if dest == None:
				dest = this.name+'.'+tokens[0].strip()
				this.locals.append(dest)

			# clearing an old assignment
			else:
				if this.refs[dest] == 'e': # an entity
					this.commands.append(clear_tag(dest))
				else: # something else, NOT FINISHED
					pass

			# evaluate the right side, perform the new assignment
			expression = this.process_expression(''.join(tokens[2:]))
			if expression[0] == '@': # an entity
				this.refs[dest] = 'e'
				this.commands.append(assign_entity(expression, dest))
			else: # something else, NOT FINISHED 
				pass

		# definining a new function
		elif tokens[0].strip() == 'def':

			this.functions[this.name+'.'+tokens[1].strip()].compile()

		# calling a custom function
		elif funcpath != None:
			func = this.functions[funcpath]
			funcparams = broad_tokenize(''.join(tokens[1:]))
			for i, p in enumerate(func.params):
				expression = this.process_expression(tokens[i+1])
				if func.params[p] == 'e': # an entity
					this.commands.append(assign_entity(expression, func.name+'.'+p))
			this.commands.append('function '+this.pack+':'+func.name)

		# implicit execute
		elif tokens[0].strip() in ('as', 'at', 'positioned', 'align', 'facing', 'rotated', 'in', 'anchored', 'if', 'unless', 'store'):
			if tokens[-1] == ':': tokens.pop() # remove a trailing ':'

			# generate inner content as function
			funcname = this.path+['rel'+str(this.relcounter)]
			this.functions['.'.join(funcname)] = Function(funcname, {}, this.lines, this.namespace, this.pointer+1, this.expecteddepth+1)
			this.functions['.'.join(funcname)].compile()
			this.relcounter += 1

			# setup execution call
			this.commands.append('execute '+''.join(this.process_expression(token) for token in tokens)+' run function '+this.pack+':'+'.'.join(funcname))

		# vanilla command
		else:
			this.commands.append(''.join(this.process_expression(token) for token in tokens))
