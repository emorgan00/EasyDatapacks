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
				name = file.split('/')[-1].split('\\')[-1].split('.')[0]
				lines = f.readlines()

				# pre-processing
				lines = [(tab_depth(line), line.strip()) for line in lines if len(line.strip()) > 0 and line.strip()[0] != '#']

				Function(['main'], {}, lines, this, 0, 0, None, None).compile()

		unused = []
		# prune unused functions
		for f in this.functions:
			if not this.functions[f].used:
				unused.append(f)
		for f in unused:
			this.functions.pop(f)
			if verbose:
				print 'collapsed branch '+f

		if verbose:
			print ''
			for f in this.functions:
				print this.functions[f]

class Function:

	def __init__(this, path, params, lines, namespace, start, expecteddepth, infunc, inloop):

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
		this.pastline = ''
		this.used = False

		# stuff with break/return
		this.infunc = infunc
		this.inloop = inloop
		this.hasbreak = False
		this.hascontinue = False

	def __str__(this):

		out = this.name[5:]+': '
		out += str(this.params)
		out += ' ('+str('.'.join(this.infunc[1:]))+')'
		out += ' ('+str('.'.join(this.inloop[1:]))+')' if this.inloop != None else ' ()'
		out += '\n\n\t'+'\n\t'.join(this.commands)+'\n'
		return out

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
				this.functions['.'.join(funcpath)] = Function(funcpath, funcparams, this.lines, this.namespace, this.pointer+i+1, depth+1, funcpath, None)
				this.functions['.'.join(funcpath)].used = True

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
			else: # something else
				pass

			this.refs.pop(ref)

	def process_expression(this, expression):

		components = expression.strip().split('#')
		ref = components[0]

		path = this.reference_path(ref)
		if path != None: # some reference
			if this.refs[path] == 'e': # an entity
				out = ''
				if len(components) == 2:
					clarifiers = expression.strip().split('#')[1]
					if clarifiers == '':
						out = select_entity(path)
					elif clarifiers == '1':
						out = select_entity1(path)
					elif clarifiers == 'p':
						out = select_player(path)
					elif clarifiers in ('1p', 'p1'):
						out = select_player1(path)
				else:
					out = select_entity(path)
				return out+(' ' if expression[-1] == ' ' else '')
			else: # something else
				pass

		# a simple constant
		return expression

	def process_line(this):

		line = this.lines[this.pointer][1]
		tokens = tokenize(line)

		funcpath = this.function_path(tokens[0].strip())

		if this.hasbreak or this.hascontinue:
			return

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
				else: # something else
					pass

			# evaluate the right side, perform the new assignment
			expression = this.process_tokens(tokens[2:], True)
			if expression[0] == '@': # an entity
				this.refs[dest] = 'e'
				this.commands.append(assign_entity(expression, dest))
				# special case: assigning as a summon
				if expression == select_entity('assign'):
					this.commands.append(clear_tag('assign'))
			else: # something else
				raise Exception('Invalid assignment: cannot assign "'+expression+'" to variable at '+this.name)

		# definining a new function
		elif tokens[0].strip() == 'def':

			this.functions[this.name+'.'+tokens[1].strip()].compile()

		# calling a custom function
		elif funcpath != None:
			func = this.functions[funcpath]
			funcparams = broad_tokenize(''.join(tokens[1:]))
			for i, p in enumerate(func.params):
				try:
					expression = this.process_expression(tokens[i+1])
				except IndexError:
					raise Exception('Not enough paramaters for function "'+tokens[0]+'" at '+this.name)
				if func.params[p] == 'e': # an entity
					this.commands.append(assign_entity(expression, func.name+'.'+p))

			this.commands.append(this.call_function(funcpath))

		# implicit execute
		elif tokens[0].strip() in ('as', 'at', 'positioned', 'align', 'facing', 'rotated', 'in', 'anchored', 'if', 'unless', 'store'):
			if tokens[-1] == ':': tokens.pop() # remove a trailing ':'

			funcname = this.fork_function('e')
			# setup execution call
			this.commands.append('execute '+this.process_tokens(tokens)+' run '+this.call_function(funcname))
			this.check_break(funcname)

		# if/else
		elif tokens[0].strip() == 'else':
			if this.pastline[:3] != 'if ':
				raise Exception('"else" without matching "if" at '+this.name)
			this.lines[this.pointer] = (this.lines[this.pointer][0], 'unless'+this.pastline[2:])
			this.process_line()
			return

		# repeat
		elif tokens[0].strip() == 'repeat':

			count = None
			for token in tokens[1:]:
				if token.isdigit():
					count = int(token)
					break
			if count == None:
				raise Exception('"repeat" without a number following it at '+this.name)

			funcname = this.fork_function('r')
			# setup execution call
			for i in xrange(count):
				this.commands.append(this.call_function(funcname))
			this.check_break(funcname)

		# while loop
		elif tokens[0].strip() in ('while', 'whilenot'):
			if tokens[-1] == ':': tokens.pop() # remove a trailing ':'

			funcname = this.fork_function('w')
			# setup execution call
			if tokens[0].strip() == 'while':
				call = 'execute if '+this.process_tokens(tokens[1:])+' run '+this.call_function(funcname, True)
			else:
				call = 'execute unless '+this.process_tokens(tokens[1:])+' run '+this.call_function(funcname, True)
			this.commands.append(call)
			this.functions[funcname].loopcall(funcname, call)
			if this.functions[funcname].hasbreak:
				this.commands.append('kill @e[type=armor_stand,tag='+funcname+'.BREAK]')
			if this.functions[funcname].hascontinue:
				this.commands.append('kill @e[type=armor_stand,tag='+funcname+'.CONTINUE]')

		# break
		elif tokens[0].strip() == 'break':
			if this.inloop == None:
				raise Exception('"break" outside of loop at '+this.name)
			
			this.hasbreak = True
			this.commands.append('summon armor_stand 0 0 0 {Marker:1b,Tags:["'+'.'.join(this.inloop)+'.BREAK"]}')

		# continue
		elif tokens[0].strip() == 'continue':
			if this.inloop == None:
				raise Exception('"continue" outside of loop at '+this.name)
			
			this.hascontinue = True
			this.commands.append('summon armor_stand 0 0 0 {Marker:1b,Tags:["'+'.'.join(this.inloop)+'.CONTINUE"]}')

		# vanilla command
		elif this.infunc == None:
			raise Exception('Vanilla command outside of a function. This is not allowed, consider putting it inside the load function.')
		else:
			this.commands.append(this.process_tokens(tokens))

		this.pastline = line

	def process_tokens(this, tokens, augsummon = False):

		# special case: assigning as a summon
		if augsummon and tokens[0].strip() == 'summon':
			ref = ''.join(tokens)
			if 'Tags:[' in ref:
				this.commands.append(ref.replace('Tags:[', 'Tags:["assign",'))
			elif ref[-1] == '}':
				this.commands.append(ref[:-1]+',Tags:["assign"]}')
			else:
				this.commands.append(ref+' {Tags:["assign"]}')
			return select_entity('assign')

		for i, token in enumerate(tokens):
			refpath = this.reference_path(token.split('#')[0])
			token = this.process_expression(token)
			# narrowing
			if refpath != None and token[0] == '@' and i != len(tokens)-1 and tokens[i+1][0] == '[':
				tokens[i+1] = ','+tokens[i+1][1:]
				token = token[:-1]
			tokens[i] = token
		return ''.join(tokens)

	def fork_function(this, code):

		# generate inner content as function
		inloop = this.inloop
		newpointer = this.pointer+1
		newdepth = this.expecteddepth+1

		funcpath = this.path+[code+str(this.relcounter)]

		# check if creating new loop
		if code in ('r', 'w'):
			inloop = funcpath

		# check if a break
		if code == 'b':
			newdepth -= 1
			while newpointer < len(this.lines) and this.lines[newpointer][0] > this.expecteddepth:
				newpointer += 1
			if this.path[-1][0] == 'b':
				funcpath = this.path[:-1]+['b'+str(int(this.path[-1][1])+1)]

		funcname = '.'.join(funcpath)

		try:
			this.functions[funcname] = Function(funcpath, {}, this.lines, this.namespace, newpointer, newdepth, this.infunc, inloop)
			this.functions[funcname].compile()
		except SyntaxError as e:
			if code != 'b': raise e

		this.relcounter += 1
		return funcname

	def call_function(this, funcname, nocollapse = False):

		func = this.functions[funcname]
		if len(func.commands) > 1 or nocollapse:
			func.used = True
			return 'function '+this.pack+':'+funcname[5:]
		elif len(func.commands) == 1:
			return func.commands[0]
		else:
			return None

	def check_break(this, funcname):

		func = this.functions[funcname]

		if this.inloop != None and (func.hasbreak or func.hascontinue):

			fork = this.fork_function('b')
			call = 'execute '

			if func.hasbreak:
				this.hasbreak = True
				call += 'unless entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.BREAK] '

			if func.hascontinue:
				this.hascontinue = True
				call += 'unless entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE] '

			if fork in this.functions and len(this.functions[fork].commands) > 0:
				call += 'run '+this.call_function(fork)
				this.commands.append(call)

			if this.functions[fork].hasbreak:
				this.hasbreak = True
			if this.functions[fork].hascontinue:
				this.hascontinue = True

	def loopcall(this, funcname, call):
		
		func = this.functions[funcname]
		while func.commands[-1][-2] == 'b':
			newname = 'main.'+func.commands[-1].split(':')[-1]
			func = this.functions[newname]

		newcall = call

		if func.hasbreak or func.hascontinue:

			if func.hasbreak:
				newcall = 'unless entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.BREAK] run '+newcall

			if func.hascontinue:
				newcall = 'unless entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE] run '+newcall

			newcall = 'execute '+newcall

		func.commands.append(newcall)

		if this.functions[funcname].hascontinue:

			cmd = 'kill @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE]'
			this.functions[funcname].commands.insert(0, cmd)
			
			cmd = 'execute if entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE] run '+call
			this.functions[funcname].commands.append(cmd)