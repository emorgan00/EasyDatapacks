import os

from .commands import *
from .function import *
from .reader import *


class Namespace:

    def __init__(self, pack, files):

        self.pack = pack
        self.files = files

        # an entry follows this format: {Function.name : Function}
        self.functions = {}

        # for integer variables
        self.consts = []
        self.ints = set()

        # to comply with objectives being no longer than 16 chars
        self.intmap = {}

        # for displaying at the end when verbose
        self.clonedfunctions = []

    def add_constant(self, value):

        if value in self.consts:
            return 'CONSTANT.'+str(self.consts.index(value))

        self.consts.append(value)
        ref = 'CONSTANT.' + str(len(self.consts) - 1)
        self.intmap[ref] = ref[-16:]
        return ref

    def add_int(self, ref):

        if ref not in self.ints:
            self.ints.add(ref)
            self.intmap[ref] = (ref + '.' + str(len(self.intmap)))[-16:]

    def add_file(self, path):

        if not path.endswith('.mcf'):
            path += '.mcf'
        path = os.path.abspath(path)

        if os.path.isfile(path) and not any(os.path.samefile(f, path) for f in self.files):
            print('importing "' + path + '"...')
            self.files.append(path)
        else:
            print('failed to import "' + path + '".')

    def compile(self, verbose):

        rawlines = []

        # read all files
        for file in self.files:
            with open(file, 'r') as f:
                name = file.split('/')[-1].split('\\')[-1]
                base = file.replace(name, '')

                # handle imports
                for line in f.readlines():
                    if line.startswith('include '):
                        newfile = line[8:].strip()
                        path = os.path.join(base, newfile)
                        self.add_file(path)
                    else:
                        rawlines.append(line)

        # auto-detect tab width
        tab_width = 4
        for line in rawlines:
            spaces = 0
            for ch in line:
                if ch == ' ':
                    spaces += 1
                else:
                    break
            if spaces > 0:
                tab_width = spaces
                break

        # pre-processing empty lines and comments
        lines = []
        for i, line in enumerate(rawlines):

            td = tab_depth(line, tab_width)
            tokens = broad_tokenize(line)

            for j, token in enumerate(tokens):
                if token == '#':
                    line = ' '.join(tokens[:j])
                    break

            if len(line.strip()) == 0:
                continue

            if td == None:
                out = 'Error at line %i: "%s"\n\tUnknown indentation. There may be a missing or extra space character.' % (i, line.strip())
                raise CompilationSyntaxError(out)
            lines.append((td, line.strip(), i + 1))

        Function(['main'], {}, {}, {}, lines, self, 0, 0, None, None, {}).compile()

        # post-process
        funcpointer = 0
        while funcpointer < len(self.functions):
            func = tuple(self.functions.values())[funcpointer]

            for i, line in enumerate(func.commands):
                func.commands[i] = self.post_process_line(line)

            funcpointer += 1

        # prune unused functions
        unused = []
        for f in self.functions:
            if not self.functions[f].used or len(self.functions[f].commands) == 0:
                unused.append(f)
        for f in unused:
            self.functions.pop(f)

        if verbose and len(unused) > 0:
            print('\ncollapsing branches...')
            print('\n\t' + ', '.join(f[5:] for f in unused if f not in self.clonedfunctions))

        if verbose and len(self.clonedfunctions) > 0:
            print('\ncloning string functions...')
            print('\n\t' + ', '.join(f[5:] for f in self.clonedfunctions))

        # handle scoreboard variables
        if len(self.ints) > 0:

            if 'main.load' not in self.functions:
                print('\nautomatically creating missing load function...')
                self.functions['main.load'] = Function(['main', 'load'], {}, {}, {}, [], self, 0, 0, ['main', 'load'], None, {})

            load = self.functions['main.load']

            # summon the .VARS armor stand
            commands = [summon_vars(self.pack)]

            for ref in self.ints:
                commands.append('scoreboard objectives add ' + self.intmap[ref] + ' dummy')

            # handle constants
            for i, val in enumerate(self.consts):
                commands.append('scoreboard objectives add CONSTANT.' + str(i) + ' dummy')
                commands.append(assign_int(val, 'CONSTANT.' + str(i), self))

            # add the new commands to the beginning of the "load" function
            load.commands = commands + load.commands

        if verbose:
            print('')
            for f in self.functions:
                print(self.functions[f])

    def post_process_line(self, line):

        # function call
        index = line.find('!f{')
        if index != -1:

            start = index

            data = []
            buff = ''
            index += 2
            while index < len(line) and line[index] == '{':
                index += 1
                while index < len(line) and line[index] != '}':
                    if line[index] == '\\':
                        index += 1
                    buff += line[index]
                    index += 1
                data.append(buff)
                buff = ''
                index += 1

            callfuncname = data[0]
            callfunc = self.functions[callfuncname]

            if len(data) > 1:  # string params

                stringdata = {}
                i = 1
                for param in callfunc.params:
                    if callfunc.params[param] == 's':
                        stringdata[callfuncname + '.' + param] = data[i]
                        i += 1

                callfuncname = self.instantiate_string_function(callfuncname, stringdata)
                callfunc = self.functions[callfuncname]

            if len(callfunc.commands) > 1:
                callfunc.used = True
                return line[:start] + 'function ' + self.pack + ':' + callfuncname[5:]
            elif len(callfunc.commands) == 1:
                # if a function is only 1 command, just execute it directly.
                return line[:start] + self.post_process_line(callfunc.commands[0])
            else:
                return '# ' + line[:start] + 'function ' + self.pack + ':' + callfuncname[5:]

        return line

    def instantiate_string_function(self, funcname, data):

        func = self.functions[funcname]
        newpath = func.path + ['s' + str(func.instancecounter)]
        func.instancecounter += 1

        params = {p: func.params[p] for p in func.params if func.params[p] != 's'}
        
        data = data.copy()
        data.update(func.stringdata)
        copy = Function(newpath, func.refs, params, func.defaults, func.lines, self,
                        func.pointer, func.expecteddepth, func.infunc, func.inloop, data)

        copy.compile()
        self.functions[copy.name] = copy

        self.clonedfunctions.append(copy.name)

        return copy.name

