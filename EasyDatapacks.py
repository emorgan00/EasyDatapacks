from function import *

def compile(path_in, path_out):
	'''path_in points to a text file containing your code.
	path_out points to the folder where you want your datapack to end up'''

	f_in = open(path_in, 'r')
	f_out = open(path_out, 'w')

	name = '.'.join(path_out.split('/')[-1].split('.')[:-1])
	f = create_function(name, {}, {}, f_in.read())
	f_out.write(f.body)

	f_in.close()
	f_out.close()

compile('test.mcf', 'out.mcfunction')