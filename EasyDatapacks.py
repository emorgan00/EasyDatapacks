from function import *
import os
import shutil

MCMETA = '''{
	"pack" : {
		"pack_format" : 3,
		"description" : "data pack generated by EasyDatapacks"
	}
}
'''

LOADTICK = '''{
	"values" : [
		"%s"
	]
}'''

def compile(path_in, packname):
	'''path_in points to a text file containing your code.
	packname points to the folder where you want your datapack to end up'''

	functions = {}

	if isinstance(path_in, str):
		path_in = [path_in]

	for path in path_in:
		f_in = open(path, 'r')
		name = path.split('/')[-1].split('.')[0]
		lines = f_in.readlines()

		create_function(name, name, {}, {}, lines, functions)
		f_in.close()

	for f in functions:
		print functions[f], '\n'

	# generate the file layout
	try:
		shutil.rmtree(packname)
	except: pass
	os.mkdir(packname)
	os.mkdir(os.path.join(packname, 'data'))
	with open(os.path.join(packname, 'pack.mcmeta'), 'w') as f:
		f.write(MCMETA)
	os.mkdir(os.path.join(packname, 'data', 'minecraft'))
	os.mkdir(os.path.join(packname, 'data', 'minecraft', 'tags'))
	os.mkdir(os.path.join(packname, 'data', 'minecraft', 'tags', 'functions'))

	# load
	with open(os.path.join(packname, 'data', 'minecraft', 'tags', 'functions', 'load.json'), 'w') as f:
		for func in functions:
			if len(func) > 4 and func[-5:] == '_load':
				f.write(LOADTICK % (packname+':'+func))
				break

	# tick
	with open(os.path.join(packname, 'data', 'minecraft', 'tags', 'functions', 'tick.json'), 'w') as f:
		for func in functions:
			if len(func) > 4 and func[-5:] == '_tick':
				f.write(LOADTICK % (packname+':'+func))
				break

	# actual datapack
	os.mkdir(os.path.join(packname, 'data', packname))
	os.mkdir(os.path.join(packname, 'data', packname, 'functions'))
	for func in functions:
		with open(os.path.join(packname, 'data', packname, 'functions', func+'.mcfunction'), 'w') as f:
			f.write(functions[func].body)


compile(['test.mcf'], 'mydatapack')