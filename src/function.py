from namespace import *

class Function:

	def __init__(this, path, params, lines, namespace, start, expecteddepth, infunc, inloop):

		# master list of all generated vanilla commands in the function
		this.commands = []

		# path to this function, e.g. ['main', 'load'] refers to the main.load function
		this.path = path
		this.name = '.'.join(path)

		this.namespace = namespace
		this.functions = namespace.functions

		this.refs = namespace.refs
		this.pack = namespace.pack

		# the parameters supplied to this function, follows the same format as refs
		this.params = params

		# the raw user input. an element of the list is in the format (tab-depth, str-content)
		this.lines = lines

		# stores the current line we are parsing
		this.pointer = start

		# stores the reference name of all variables declared locally in this function.
		this.locals = []

		# stores the expected indentation depth of this function when compiling. Used to ensure correct indentation.
		this.expecteddepth = expecteddepth

		# stores the number of times this function has forked to another function. Used to ensure unique function names.
		this.relcounter = 0

		# stores the content of the line before the one we are currently parsing. Currently only used for if-else logic.
		this.pastline = ''

		# this will get set to true when this function is called by another function. Unused functions will get "collapsed".
		this.used = False

		# stuff with break/return
		this.infunc = infunc # stores the fuser-defined which this function is a member of
		this.inloop = inloop # stores the loop (while/whilenot) which this function is most immediately a member of
		this.hasbreak = False
		this.hascontinue = False

	def __str__(this):

		out = this.name[5:]+': '
		out += str(this.params)
		out += ' ('+str('.'.join(this.infunc[1:]))+')'
		out += ' ('+str('.'.join(this.inloop[1:]))+')' if this.inloop != None else ' ()'
		out += '\n\n\t'+'\n\t'.join(this.commands)+'\n'
		return out

	# Return the path to a variable with name <var>. It will search starting with the current function, and then check upwards to parent functions.
	def reference_path(this, var):

		for i in range(len(this.path), 0, -1):
			test_path = '.'.join(this.path[:i])+'.'+var
			if test_path in this.refs:
				return test_path
		return None

	# Return the path to a function with name <var>. Works the same way as reference_path.
	def function_path(this, var):

		for i in range(len(this.path), 0, -1):
			test_path = '.'.join(this.path[:i])+'.'+var
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
			this.refs[this.name+'.'+p] = this.params[p]
			this.locals.append(this.name+'.'+p)

			if this.params[p] == 'i':
				this.namespace.ints.add(this.name+'.'+p)

		# pre-process function headers:
		for i, p in enumerate(this.lines[this.pointer:]):
			if p[0] < depth: break
			if p[0] > depth: continue
			if p[1][:3] == 'def':

				tokens = tokenize(p[1])
				funcpath = this.path+[tokens[1].strip()]
				if not valid_name(tokens[1].strip()):
					raise Exception('Invalid function name: "'+tokens[1].strip()+'"')

				funcparams = {}
				for token in (''.join(tokens[2:])).split(' '):
					token = token.strip(':')
					if len(token) == 0: continue
					if valid_name(token):
						param = token.split('#')
						if len(param) == 1:
							funcparams[token] = 'e'
						elif param[1] in ('e', 'i'):
							funcparams[param[0]] = param[1]
						else:
							raise Exception('Invalid parameter clarifier: "'+token.strip()+'" for function '+tokens[1].strip())
					else:
						raise Exception('Invalid parameter name "'+token.strip()+'" for function '+tokens[1].strip())

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

	# called on a single token. Detects references and handles clarifiers. For multi-token strings, use process_tokens.
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

			elif this.refs[path] == 'i': # integer variable
				return select_int(path, this.pack)+(' ' if expression[-1] == ' ' else '')

		# a simple constant
		return expression

	# processes the current line.
	def process_line(this):

		if this.hasbreak or this.hascontinue:
			return

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
				else: # something else
					pass

			# evaluate the right side, perform the new assignment
			expression = this.process_tokens(tokens[2:], True)
			refpath = this.reference_path((''.join(tokens[2:])).strip())

			if expression.isdigit(): # an integer constant
				this.refs[dest] = 'i'
				this.commands.append(assign_int(expression, dest, this.pack))
				this.namespace.ints.add(dest)

			elif refpath in this.refs and this.refs[refpath] == 'i': # an integer variable
				this.refs[dest] = 'i'
				this.commands.append(augment_int(dest, refpath, '=', this.pack))
				this.namespace.ints.add(dest)

			elif expression[0] == '@': # an entity
				this.refs[dest] = 'e'
				this.commands.append(assign_entity(expression, dest))
				# special case: assigning as a summon
				if expression == select_entity('assign'):
					this.commands.append(clear_tag('assign'))

			else: # something else
				raise Exception('Cannot assign "'+expression+'" to variable at '+this.name)

		# augmented assignment (for integers)
		elif len(tokens) > 2 and (tokens[1] in ('+', '-', '/', '*', '%') and tokens[2] == '=' or tokens[1].strip() in ('<', '>', '><')):

			var = tokens[0].strip()

			if tokens[1] in ('+', '-', '/', '*', '%'):
				op = tokens[1]+tokens[2]
				expression = (''.join(tokens[3:])).strip()
			elif tokens[1] == '>':
				if tokens[2] == '<':
					op = tokens[1]+tokens[2]
					expression = (''.join(tokens[3:])).strip()
				else:
					op = tokens[1].strip()
					expression = (''.join(tokens[2:])).strip()

			else:
				op = tokens[1].strip()
				expression = (''.join(tokens[2:])).strip()

			if len(tokens) == 2:
				raise Exception('Expected something after "'+op+'" at '+this.name)

			dest = this.reference_path(var)
			if dest == None or this.refs[dest] != 'i':
				raise Exception('Cannot perform augmented assignment on "'+var+'" at '+this.name)
			
			inref = this.reference_path(expression)
			if inref == None and expression.isdigit(): # int constant
				if op == '+=':
					this.commands.append(add_int(expression, dest, this.pack))
				elif op == '-=':
					this.commands.append(sub_int(expression, dest, this.pack))
				else:
					var2 = this.namespace.add_constant(expression)
					this.commands.append(augment_int(dest, var2, op, this.pack))

			elif inref == None or this.refs[inref] != 'i':
				raise Exception('Cannot perform augmented assignment with "'+expression+'" at '+this.name)

			# valid variable
			else:
				this.commands.append(augment_int(dest, inref, op, this.pack))

		# definining a new function
		elif tokens[0].strip() == 'def':

			this.functions[this.name+'.'+tokens[1].strip()].compile()

		# calling a custom function
		elif funcpath != None:

			if funcpath == '.'.join(this.infunc):
				raise Exception('Attempt at recursing in function '+'.'.join(this.infunc)+', this is not supported.')

			func = this.functions[funcpath]
			givenparams = broad_tokenize(''.join(tokens[1:]))
			for i, p in enumerate(func.params):
				try:
					expression = this.process_expression(givenparams[i]).strip()
				except IndexError:
					raise Exception('Not enough paramaters for function "'+tokens[0].strip()+'" at '+this.name)

				if func.params[p] == 'e': # an entity
					this.commands.append(assign_entity(expression, func.name+'.'+p))

				elif func.params[p] == 'i': # in integer
					if expression.isdigit(): # constant int
						this.commands.append(assign_int(expression, func.name+'.'+p, this.pack))
					elif expression[0] == '@': # reference to int
						this.commands.append(augment_int(func.name+'.'+p, this.reference_path(givenparams[i]), '=', this.pack))

			this.commands.append(this.call_function(funcpath))

		# implicit execute
		elif tokens[0].strip() in ('as', 'at', 'positioned', 'align', 'facing', 'rotated', 'in', 'anchored', 'if', 'unless', 'store'):
			if tokens[-1] == ':': tokens.pop() # remove a trailing ':'

			funcname = this.fork_function('e')
			# setup execution call
			this.commands.append('execute '+this.process_tokens(tokens, False, True)+' run '+this.call_function(funcname))
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
			for i in range(count):
				this.commands.append(this.call_function(funcname))
			this.check_break(funcname)

		# while loop
		elif tokens[0].strip() in ('while', 'whilenot'):
			if tokens[-1] == ':': tokens.pop() # remove a trailing ':'

			funcname = this.fork_function('w')
			# setup execution call
			if tokens[0].strip() == 'while':
				call = 'execute if '+this.process_tokens(tokens[1:], False, True)+' run '+this.call_function(funcname, True)
			else:
				call = 'execute unless '+this.process_tokens(tokens[1:], False, True)+' run '+this.call_function(funcname, True)
			this.commands.append(call)
			this.functions[funcname].call_loop(funcname, call)
			if this.functions[funcname].hasbreak:
				this.commands.append('kill @e[type=armor_stand,tag='+funcname+'.BREAK]')
			if this.functions[funcname].hascontinue:
				this.commands.append('kill @e[type=armor_stand,tag='+funcname+'.CONTINUE]')

		# break
		elif tokens[0].strip() == 'break':
			if this.inloop == None:
				raise Exception('"break" outside of loop at '+this.name)
			
			this.hasbreak = True
			this.commands.append('summon armor_stand 0 0 0 {Marker:1b,Invisible:1b,NoGravity:1b,Tags:["'+'.'.join(this.inloop)+'.BREAK"]}')

		# continue
		elif tokens[0].strip() == 'continue':
			if this.inloop == None:
				raise Exception('"continue" outside of loop at '+this.name)
			
			this.hascontinue = True
			this.commands.append('summon armor_stand 0 0 0 {Marker:1b,Invisible:1b,NoGravity:1b,Tags:["'+'.'.join(this.inloop)+'.CONTINUE"]}')

		# vanilla command
		elif this.infunc == None:
			raise Exception('Vanilla command outside of a function. This is not allowed, consider putting it inside the load function.')
		elif tokens[0].strip() == 'function':
			raise Exception('The /function command is no longer used. Just type your function as if it were a command. (at '+this.name+')')
		
		else:
			this.commands.append(this.process_tokens(tokens))

		this.pastline = line

	# called on a set of tokens, intended to evaluate to a single string which represents some value which can be inserted into vanilla commands.
	# this can be an entity, integer, or series of vanilla commands (or components thereof)
	# will handle references as part of an expression.
	def process_tokens(this, tokens, augsummon = False, conditional = False):

		args = broad_tokenize(''.join(tokens).strip())

		# special case: assigning as a summon
		if augsummon and args[0] == 'summon':
			ref = ' '.join(args)
			if 'Tags:[' in ref:
				this.commands.append(ref.replace('Tags:[', 'Tags:["assign",'))
			elif ref[-1] == '}':
				this.commands.append(ref[:-1]+',Tags:["assign"]}')
			else:
				this.commands.append(ref+' {Tags:["assign"]}')
			return select_entity('assign')

		# special case: conditional
		if conditional and len(args) > 2:
			for i in range(1, len(args)-1):
				op = args[i]
				if op in ('<', '>', '==', '<=', '>='):
					var = this.reference_path(args[i-1])
					if var == None or this.refs[var] != 'i':
						raise Exception('"'+args[i-1]+'" is not a valid integer variable at '+this.name)
					if not args[i+1].isdigit():
						raise Exception('"'+args[i+1]+'" is not an integer at '+this.name)
					if i > 1 and not args[i-2] in ('if', 'unless', 'while', 'whilenot'):
						raise Exception('Integer comparison without a conditional at '+this.name)
					args[i-1] = check_int(var, op, args[i+1], this.pack)
					args[i] = None
					args[i+1] = None

		tokens = tokenize(' '.join(a for a in args if a != None))

		for i, token in enumerate(tokens):
			refpath = this.reference_path(token.split('#')[0])
			token = this.process_expression(token)
			# narrowing
			if refpath != None and token[0] == '@' and i != len(tokens)-1 and tokens[i+1][0] == '[' and tokens[i][-1] != ' ':
				tokens[i+1] = ','+tokens[i+1][1:]
				token = token[:-1]
			tokens[i] = token

		return (''.join(tokens)).strip()

	# <code> refers to the type of function. These are the same codes as are used in function path/file names.
	# 'w' = while loop body
	# 'e' = implicit execution
	# 'r' = repeat loop body
	# 'b' = chained continue/break-check function
	# returns the name of the function which was generated
	def fork_function(this, code):

		# generate inner content as function
		inloop = this.inloop
		newpointer = this.pointer+1
		newdepth = this.expecteddepth+1

		funcpath = this.path+[code+str(this.relcounter)]

		# check if creating new loop
		if code in ('w'):
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
			# gonna be honest here, I barely remember writing this and it seems like black magic to me. But it works perfectly.
			if code != 'b': raise e

		this.relcounter += 1
		return funcname

	# this will call a sub-function of name <funcname>. <nocollapse> will disable collapsing a 1-line function
	def call_function(this, funcname, nocollapse = False):

		func = this.functions[funcname]
		if len(func.commands) > 1 or nocollapse:
			func.used = True
			return 'function '+this.pack+':'+funcname[5:]
		elif len(func.commands) == 1:
			# if a function is only 1 command, just execute it directly.
			return func.commands[0]
		else:
			func.used = True
			return 'function '+this.pack+':'+funcname[5:]

	# this is called after spawning a forked function. It checks if the function has a break/continue,
	# and will branch the current function accordingly.
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

			# if fork isn't in this.functions, then it was collapsed and we don't have to worry about it.
			if fork in this.functions and len(this.functions[fork].commands) > 0:
				call += 'run '+this.call_function(fork)
				this.commands.append(call)

			# breaks should always propagate backwards through a b-function chain.
			if this.functions[fork].hasbreak:
				this.hasbreak = True
			if this.functions[fork].hascontinue:
				this.hascontinue = True

	# this is called by a loop's parent function to set up that loop's self-call
	def call_loop(this, funcname, call):
		
		func = this.functions[funcname]
		while func.commands[-1][-2] == 'b':
			newname = 'main.'+func.commands[-1].split(':')[-1]
			func = this.functions[newname]

		# <call> should be a call directly to the outermost loop function
		newcall = call

		# if the loop has a break/continue, we need to ensure it hasn't been called before looping again
		if func.hasbreak or func.hascontinue:

			if func.hasbreak:
				newcall = 'unless entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.BREAK] run '+newcall

			if func.hascontinue:
				newcall = 'unless entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE] run '+newcall

			newcall = 'execute '+newcall

		func.commands.append(newcall)

		# if the loop has a continue, we need to reset it to the beginning if we reach the end and continue has been called
		if this.functions[funcname].hascontinue:

			cmd = 'kill @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE]'
			this.functions[funcname].commands.insert(0, cmd)

			cmd = 'execute if entity @e[type=armor_stand,tag='+'.'.join(this.inloop)+'.CONTINUE] run '+call
			this.functions[funcname].commands.append(cmd)