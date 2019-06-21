from function import *

def compile(path_in, path_out):
	'''path_in points to a text file containing your code.
	path_out points to the folder where you want your datapack to end up'''

	f_in = open(path_in, 'r')

	name = path_out.split('/')[-1]
	lines = f_in.readlines()
	functions = {}
	functions[name] = create_function('', {}, {}, lines, functions)
	for f in functions:
		print functions[f], '\n'

	f_in.close()

compile('test.mcf', 'mydatapack')