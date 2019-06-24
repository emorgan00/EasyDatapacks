from reader import *
from commands import *
from function import *

class Namespace:

	def __init__(this, pack, files):

		this.pack = pack
		this.files = files

		# an entry follows this format: {Function.name : Function}
		this.functions = {}

		# stores all references in the format {variable-name : type}
		# type is either 'e' or 'i' (entity or integer)
		this.refs = {}

		# for integer variables
		this.consts = []
		this.ints = set()

	def add_constant(this, value):

		this.consts.append(value)
		return 'CONSTANT.'+str(len(this.consts)-1)

	def compile(this, verbose):

		# compile all files
		for file in this.files:
			with open(file, 'r') as f:
				name = file.split('/')[-1].split('\\')[-1].split('.')[0]
				lines = f.readlines()

				# pre-processing empty lines and comments
				lines = [(tab_depth(line), line.strip()) for line in lines if len(line.strip()) > 0 and line.strip()[0] != '#']

				Function(['main'], {}, lines, this, 0, 0, None, None).compile()

		# prune unused functions
		unused = []
		for f in this.functions:
			if not this.functions[f].used:
				unused.append(f)
		for f in unused:
			this.functions.pop(f)
			if verbose:
				print('collapsed branch '+f)

		# handle scoreboard variables
		if len(this.ints) > 0:

			if not 'main.load' in this.functions:
				print('automatically creating missing load function...')
				this.functions['main.load'] = Function(['main', 'load'], {}, [], this, 0, 0, ['main', 'load'], None)

			load = this.functions['main.load']
			commands = []

			# summon the .VARS armor stand
			commands.append(summon_vars(this.pack))

			for ref in this.ints:
				commands.append('scoreboard objectives add '+ref+' dummy')

			# handle constants
			for i, val in enumerate(this.consts):
				commands.append('scoreboard objectives add CONSTANT.'+str(i)+' dummy')
				commands.append(assign_int(val, 'CONSTANT.'+str(i), this.pack))

			# add the new commands to the beginning of the "load" function
			load.commands = commands+load.commands

		if verbose:
			print('')
			for f in this.functions:
				print(this.functions[f])