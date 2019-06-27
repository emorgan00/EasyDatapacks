from src.commands import *
from src.function import *
from src.reader import *


class Namespace:

    def __init__(self, pack, files):

        self.pack = pack
        self.files = files

        # an entry follows this format: {Function.name : Function}
        self.functions = {}

        # stores all references in the format {variable-name : type}
        # type is either 'e' or 'i' (entity or integer)
        self.refs = {}

        # for integer variables
        self.consts = []
        self.ints = set()

    def add_constant(self, value):

        self.consts.append(value)
        return 'CONSTANT.' + str(len(self.consts) - 1)

    def compile(self, verbose):

        # compile all files
        for file in self.files:
            with open(file, 'r') as f:
                name = file.split('/')[-1].split('\\')[-1].split('.')[0]
                rawlines = f.readlines()

                # pre-processing empty lines and comments
                lines = []
                for i, line in enumerate(rawlines):
                    if len(line.strip()) > 0 and line.strip()[0] != '#':
                        lines.append((tab_depth(line), line.strip(), i + 1))

                Function(['main'], {}, lines, self, 0, 0, None, None).compile()

        # prune unused functions
        unused = []
        for f in self.functions:
            if not self.functions[f].used:
                unused.append(f)
        for f in unused:
            self.functions.pop(f)
            if verbose:
                print('collapsed branch ' + f)

        # handle scoreboard variables
        if len(self.ints) > 0:

            if 'main.load' not in self.functions:
                print('automatically creating missing load function...')
                self.functions['main.load'] = Function(['main', 'load'], {}, [], self, 0, 0, ['main', 'load'], None)

            load = self.functions['main.load']

            # summon the .VARS armor stand
            commands = [summon_vars(self.pack)]

            for ref in self.ints:
                commands.append('scoreboard objectives add ' + ref + ' dummy')

            # handle constants
            for i, val in enumerate(self.consts):
                commands.append('scoreboard objectives add CONSTANT.' + str(i) + ' dummy')
                commands.append(assign_int(val, 'CONSTANT.' + str(i), self.pack))

            # add the new commands to the beginning of the "load" function
            load.commands = commands + load.commands

        if verbose:
            print('')
            for f in self.functions:
                print(self.functions[f])
