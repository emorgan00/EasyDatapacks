import datapack, sys

USAGE = '''
usage:
	datapack <output-folder> <input-file(s)>

flags:
	-v, -verbose: print out all generated commands.
	-n, -nofiles: don't actually generate any files, just print out the generated commands.
'''

if __name__ == '__main__':

	params = []
	verbose, nofiles = False, False

	for param in sys.argv:
		if param in ('-v', '-verbose'):
			verbose = True
		elif param in ('-n', '-nofiles'):
			nofiles = True
			verbose = True
		elif param[-3:] == '.py':
			print 'ignoring .py file as parameter'
		else:
			params.append(param)

	if len(params) < 2:
		print 'error: not enough parameters were supplied'
		print USAGE
		sys.exit()

	if nofiles:
		datapack.Namespace(params[0].split('/')[-1].split('\\')[-1], params[1:]).compile(verbose)
	else:
		datapack.compile(params[0], params[1:], verbose)