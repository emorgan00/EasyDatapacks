from .commands import *
from .reader import *
from .validate import *


class CompilationError(Exception):
    pass

class CompilationSyntaxError(CompilationError):
    pass


class Function:

    def __init__(self, path, refs, params, defaults, lines, namespace, start, expecteddepth, infunc, inloop, stringdata):

        # master list of all generated vanilla commands in the function
        self.commands = []

        # commands which are needed to process another command, reset every line
        self.auxcommands = []

        # path to this function, e.g. ['main', 'load'] refers to the main.load function
        self.path = path
        self.name = '.'.join(path)

        self.namespace = namespace
        self.functions = namespace.functions

        self.refs = refs.copy()
        self.pack = namespace.pack

        # the parameters supplied to this function, follows the same format as refs
        self.params = params
        self.defaults = defaults

        # the raw user input. an element of the list is in the format (tab-depth, str-content, line-number)
        self.lines = lines

        # stores the current line we are parsing
        self.pointer = start

        # stores the reference name of all variables declared locally in this function.
        self.locals = []

        # stores the expected indentation depth of this function when compiling. Used to ensure correct indentation.
        self.expecteddepth = expecteddepth

        # stores the number of times this function has forked to another function. Used to ensure unique function names.
        self.relcounter = 0

        # stores the number of times this string-parametered function has instantiated. Used to ensure unique function names.
        # functions without string parameters will never use this.
        self.instancecounter = 0
        self.instantiable = 's' in params.values()

        # values for string parameters
        self.stringdata = stringdata

        # stores the content of the line before the one we are currently parsing. Currently only used for if-else logic.
        self.pastline = ''

        # this will get set to true when this function is called by another function. Unused functions will get "collapsed".
        self.used = False

        # stuff with break/return
        self.infunc = infunc  # stores the user-defined function which this function is a member of
        self.inloop = inloop  # stores the loop (while/whilenot) which this function is most immediately a member of
        self.hasbreak = False
        self.hascontinue = False

        # update the namespace intmap, this must be done in __init__ because other functions may call this function
        # before it has been compiled.
        for p in self.params:
            if self.params[p] == 'i':
                self.namespace.add_int('.'.join(self.infunc) + '.' + p)

    def __str__(self):

        out = self.name[5:] + ': '
        out += str(self.params)
        out += ' (' + str('.'.join(self.infunc[1:])) + ')'
        out += ' (' + str('.'.join(self.inloop[1:])) + ')' if self.inloop is not None else ' () '
        out += '\n\n\t' + '\n\t'.join(self.commands) + '\n'
        return out

    # Return the path to a variable with name <var>. It will search starting with the current function,
    # and then check upwards to parent functions.
    def reference_path(self, var):

        for i in range(len(self.path), 0, -1):
            test_path = '.'.join(self.path[:i]) + '.' + var
            if test_path in self.refs:
                return test_path
        return None

    # Return the path to a function with name <var>. Works the same way as reference_path.
    def function_path(self, var):

        for i in range(len(self.path), 0, -1):
            test_path = '.'.join(self.path[:i]) + '.' + var
            if test_path in self.functions:
                return test_path
        return None

    def parse_clarifiers(self, clarifiers, path):

        var, player, one = False, False, False

        for c in clarifiers:
            if c == 'v':
                var = True
            elif c == 'p':
                player = True
            elif c == '1':
                one = True
            elif c == 'e':
                pass
            else:
                self.raise_exception('Unknown clarifier: "%s"' % c)

        if var:
            return ref
        if player and one:
            return select_player1(path)
        elif player:
            return select_player(path)
        elif one:
            return select_entity1(path)
        else:
            return select_entity(path)

    # will create an exception with line number and function name
    # syntaxerror means we are dealing with missing content
    def raise_exception(self, string, syntaxerror=False):

        if syntaxerror:
            self.pointer -= 1
            out = 'Error after line '
        else:
            out = 'Error at line '

        try:
            out += '%i: "%s"\n\t' % (self.lines[self.pointer][2], self.lines[self.pointer][1])
        except IndexError:
            out = 'Error at line 0: ""\n\t'
        out += string

        if syntaxerror:
            raise CompilationSyntaxError(out)
        else:
            raise CompilationError(out)

    # adds the command to this function.
    def add_command(self, command):

        out = check(command)
        if out != None:
            self.raise_exception(out)
        self.commands.append(command)

    # adds the command to this function.
    def auxiliary_command(self, command):

        out = check(command)
        if out != None:
            self.raise_exception(out)
        self.auxcommands.append(command)

    def compile(self):

        if len(self.lines) <= self.pointer:
            self.raise_exception('Expected content, nothing found.', True)

        depth = self.lines[self.pointer][0]
        if depth != self.expecteddepth:
            self.raise_exception('Incorrect indentation.', True)

        # pre-process params into local variables
        for p in self.params:
            self.refs['.'.join(self.infunc) + '.' + p] = self.params[p]
            self.locals.append('.'.join(self.infunc) + '.' + p)

        # pre-process stringdata into local variables
        for p in self.stringdata:
            if p not in self.refs:
                self.refs[p] = 's'
                self.locals.append(p)

        storepointer = self.pointer

        # pre-process function headers:
        for i, p in enumerate(self.lines[self.pointer:]):
            if p[0] < depth:
                break
            if p[0] > depth:
                continue
            if p[1].startswith('def'):

                if len(self.defaults) > 0:
                    self.raise_exception('A function with defaults cannot have any sub-functions.')

                self.pointer = i
                tokens = tokenize(p[1])
                if len(tokens) < 2:
                    self.raise_exception('No function name provided.')

                if not valid_function(tokens[1].strip()):
                    self.raise_exception('Invalid function name: "' + tokens[1].strip() + '".')

                funcpath = self.path + [tokens[1].strip()]
                funcparams = {}
                funcdefaults = {}
                hasdefault = False

                for token in (''.join(tokens[2:])).split(' '):
                    token = token.strip(':')
                    default = None

                    equals = token.split('=')
                    param = equals[0].split('#')
                    if len(equals) > 1:
                        default = '='.join(equals[1:])
                        hasdefault = True

                    if default is None and hasdefault:
                        self.raise_exception('Can\'t have a non-default parameter after a default parameter.')
                    
                    if len(token) == 0:
                        continue
                    if valid_name(param[0]):
                        if len(param) == 1:
                            funcparams[param[0]] = 'e'
                        elif param[1] in ('e', 'i', 'p', '1', '1p', 'p1', 's'):
                            funcparams[param[0]] = param[1]
                        elif param[1] in ('e1', '1e'):
                            funcparams[param[0]] = '1'
                        else:
                            self.raise_exception(
                                'Invalid parameter clarifier "' + token.strip() + '" for function "' + tokens[
                                    1].strip() + '".')

                        if default:
                            funcdefaults[param[0]] = default
                    else:
                        self.raise_exception(
                            'Invalid parameter name "' + token.strip() + '" for function "' + tokens[1].strip() + '".')

                if '.'.join(funcpath) in self.functions:
                    self.raise_exception('Duplicate function "' + funcpath[-1] + '"')

                self.functions['.'.join(funcpath)] = Function(funcpath, self.refs, funcparams, funcdefaults, self.lines, self.namespace,
                                                              storepointer + i + 1, depth + 1, funcpath, None, self.stringdata)

        self.pointer = storepointer

        # process lines
        while self.pointer < len(self.lines):

            if self.lines[self.pointer][0] == depth:
                self.process_line()
            elif self.lines[self.pointer][0] < depth:
                break
            self.pointer += 1

    # called on a single token. Detects references and handles clarifiers. For multi-token strings, use process_tokens.
    def process_expression(self, expression):

        components = expression.strip().split('#')
        ref = components[0]

        if len(components) == 2 and components[1] == 'v':
            return ref

        path = self.reference_path(ref)
        if path is not None:  # some reference
            if self.refs[path] in ('e', 'p', '1', '1p', 'p1'):  # an entity
                out = ''

                if len(components) > 1:
                    clarifiers = components[1] + self.refs[path]
                else:
                    clarifiers = self.refs[path]

                return self.parse_clarifiers(clarifiers, path) + (' ' if expression[-1] == ' ' else '')

            elif self.refs[path] == 'i':  # integer variable
                out = ''
                if len(components) == 2:
                    clarifiers = expression.strip().split('#')[1]
                    if clarifiers == '':
                        out = select_int(path, self.namespace)
                    elif clarifiers == 't':
                        out = text_int(path, self.namespace)
                    else:
                        self.raise_exception('Unknown clarifier: "%s"' % clarifiers)
                else:
                    out = select_int(path, self.namespace)
                return out + (' ' if expression[-1] == ' ' else '')

            elif self.refs[path] == 's':  # string parameter
                if path in self.stringdata:
                    return self.stringdata[path] + (' ' if expression[-1] == ' ' else '')
                else:
                    return '!s{' + path + '}' + (' ' if expression[-1] == ' ' else '')

        # a simple constant
        return expression

    # processes the current line.
    def process_line(self):

        if self.hasbreak or self.hascontinue:
            return

        self.auxcommands = []
        line = self.lines[self.pointer][1]
        tokens = tokenize(line)

        funcpath = self.function_path(tokens[0].strip())

        # creating a new assignment
        if len(tokens) > 1 and tokens[1].strip() == '=':

            if len(tokens) == 2:
                self.raise_exception('Expected something after "=".')

            destdata = tokens[0].strip().split('#')
            dest = self.reference_path(destdata[0])

            clarifiers = ''
            if len(destdata) == 2:
                clarifiers = destdata[1]

            # assigning something for the first time
            if dest is None:
                dest = self.name + '.' + destdata[0]
                self.locals.append(dest)

            # clearing an old assignment
            else:
                if self.refs[dest] in ('e', 'p', '1', '1p', 'p1'):  # an entity
                    self.add_command(clear_tag(dest))
                elif self.refs[dest] == 's':  # a string
                    self.raise_exception('Strings are handled at compile time, so overwriting a string may produce undefined behavior.')
                else:  # something else
                    pass

            # evaluate the right side, perform the new assignment
            expression = self.process_tokens(tokens[2:], True, dest=dest)
            refpath = self.reference_path((''.join(tokens[2:])).strip())

            if clarifiers == '':

                if valid_int(expression):  # an integer constant
                    self.refs[dest] = 'i'
                    self.namespace.add_int(dest)
                    self.add_command(assign_int(expression, dest, self.namespace))

                elif refpath in self.refs and self.refs[refpath] == 'i':  # an integer variable

                    self.refs[dest] = 'i'
                    self.namespace.add_int(dest)
                    self.add_command(augment_int(dest, refpath, '=', self.namespace))

                elif expression[0] == '@':  # an entity

                    self.refs[dest] = 'e'
                    if expression != '@':
                        self.add_command(assign_entity(expression, dest))

                elif expression[0] == '#':  # a clarifier

                    if expression[1:] in ('e', 'i', 'p', '1', '1p', 'p1'):
                        self.refs[dest] = expression[1:]
                        if expression[1:] == 'i':
                            self.namespace.add_int(dest)
                    elif expression[1:] in ('e1', '1e'):
                        self.refs[dest] = '1'
                    else:
                        self.raise_exception('Invalid global variable: "' + expression + '".')

                else:
                    self.stringdata[dest] = expression
                    self.refs[dest] = 's'

            elif clarifiers in ('e', 'p', '1', '1p', 'p1', 'e1', '1e'):

                if expression[0] == '@':
                    if clarifiers in ('e1', '1e'):
                        self.refs[dest] = '1'
                    else:
                        self.refs[dest] = clarifiers
                    if expression != '@':
                        self.add_command(assign_entity(expression, dest))
                else:
                    self.raise_exception('"' + expression + '" is not a valid entity.')

            elif clarifiers == 'i':

                if valid_int(expression):  # an integer constant
                    self.refs[dest] = 'i'
                    self.namespace.add_int(dest)
                    self.add_command(assign_int(expression, dest, self.namespace))

                elif refpath in self.refs and self.refs[refpath] == 'i':  # an integer variable

                    self.refs[dest] = 'i'
                    self.namespace.add_int(dest)
                    self.add_command(augment_int(dest, refpath, '=', self.namespace))

                else:
                    self.raise_exception('"' + expression + '" is not a valid integer or integer variable.')

            elif clarifiers == 's':
                self.stringdata[dest] = expression
                self.refs[dest] = 's'

            else:
                self.raise_exception('Unknown clarifier: "%s"' % clarifiers)

        # augmented assignment (for integers)
        elif len(tokens) > 2 and (
                tokens[1] in ('+', '-', '/', '*', '%') and tokens[2] == '=' or tokens[1].strip() in ('<', '>', '><')):

            var = tokens[0].strip()

            if tokens[1] in ('+', '-', '/', '*', '%'):
                op = tokens[1] + tokens[2]
                expression = (''.join(tokens[3:])).strip()
            elif tokens[1] == '>':
                if tokens[2] == '<':
                    op = tokens[1] + tokens[2]
                    expression = (''.join(tokens[3:])).strip()
                else:
                    op = tokens[1].strip()
                    expression = (''.join(tokens[2:])).strip()

            else:
                op = tokens[1].strip()
                expression = (''.join(tokens[2:])).strip()

            if len(tokens) == 2:
                self.raise_exception('Expected something after "' + op + '"')

            dest = self.reference_path(var)
            if dest is None or self.refs[dest] != 'i':
                self.raise_exception('Cannot perform augmented assignment on "' + var + '"')

            inref = self.reference_path(expression)
            if inref is None and valid_int(expression):  # int constant
                if op == '+=':
                    self.add_command(add_int(expression, dest, self.namespace))
                elif op == '-=':
                    self.add_command(sub_int(expression, dest, self.namespace))
                else:
                    var2 = self.namespace.add_constant(expression)
                    self.add_command(augment_int(dest, var2, op, self.namespace))

            elif inref is None or self.refs[inref] != 'i':
                self.raise_exception('Cannot perform augmented assignment with "' + expression + '"')

            # valid variable
            else:
                self.add_command(augment_int(dest, inref, op, self.namespace))

        # increment / decrement
        elif len(tokens) > 2 and ''.join(tokens[1:]) in ('++', '--'):

            var = tokens[0].strip()
            ref = self.reference_path(var)
            if ref == None:
                self.raise_exception('Cannot perform augmented assignment on "' + var + '"')
            elif ''.join(tokens[1:]) == '++':
                self.add_command(add_int('1', ref, self.namespace))
            else:
                self.add_command(sub_int('1', ref, self.namespace))

        # definining a new function
        elif tokens[0].strip() == 'def':

            func = self.functions[self.name + '.' + tokens[1].strip()]
            func.refs.update(self.refs)
            if not func.instantiable:
                func.compile()
                func.used = True

        # calling a custom function
        elif funcpath is not None:

            if funcpath == '.'.join(self.infunc):
                self.raise_exception(
                    'Attempt at recursing in function ' + '.'.join(self.infunc) + ', this is not supported.')

            func = self.functions[funcpath]
            paramlist = tuple(func.params.keys())

            givenparams = broad_tokenize(''.join(tokens[1:]))
            funcdata = []
            paramindex = 0

            entitytags = []

            def add_param(p, expression, entitytags):
                if func.params[p] in ('e', 'p', '1', '1p', 'p1'): # expecting an entity
                    self.add_command(assign_entity(expression, func.name + '.' + p))
                    entitytags.append(func.name + '.' + p)

                elif func.params[p] == 'i': # expecting an integer
                    if expression.isdigit():  # constant int
                        self.add_command(assign_int(expression, func.name + '.' + p, self.namespace))
                    elif expression[0] == '@':  # reference to int
                        self.add_command(
                            augment_int(func.name + '.' + p, self.reference_path(givenparams[i]), '=', self.namespace))

                elif func.params[p] == 's': # expecting a string
                    funcdata.append(self.process_tokens(tokenize(expression)))

            for param in givenparams:
                expression = self.process_tokens(tokenize(param)).strip()

                if paramindex >= len(func.params): # expecting a sub-function

                    funcpath += '.' + param
                    if not funcpath in self.functions:
                        self.raise_exception('"' + param + '" is not a valid sub-function of function "' + \
                                             tokens[0].strip() + '".')
                    func = self.functions[funcpath]
                    paramlist = tuple(func.params.keys())
                    paramindex = 0

                else:
                    add_param(paramlist[paramindex], expression, entitytags)
                    paramindex += 1

            while paramindex < len(func.params):
                if paramlist[paramindex] in func.defaults:
                    expression = self.process_tokens(tokenize(func.defaults[paramlist[paramindex]]))
                    add_param(paramlist[paramindex], expression, entitytags)
                    paramindex += 1
                else:
                    self.raise_exception('Not enough parameters for function "' + func.name[5:] + '".')

            self.add_command(self.call_function(funcpath, *funcdata))
            for tag in entitytags:
                self.add_command(clear_tag(tag))

        # implicit execute
        elif tokens[0].strip() in (
                'as', 'at', 'positioned', 'align', 'facing', 'rotated', 'in', 'anchored', 'if', 'unless', 'store'):
            if tokens[-1] == ':':
                tokens.pop()  # remove a trailing ':'

            funcname = self.fork_function('e')
            # setup execution call
            call = 'execute ' + self.process_tokens(tokens, False, True) + ' run ' + self.call_function(funcname)
            for c in self.auxcommands:
                self.commands.append(c)
            self.add_command(call)
            self.check_break(funcname)

        # else
        elif tokens[0].strip() == 'else':
            if tokens[-1] == ':':
                tokens.pop()  # remove a trailing ':'

            pastline = tokenize(self.pastline)
            if len(pastline) == 0 or not pastline[0].strip() in (
                'as', 'at', 'positioned', 'align', 'facing', 'rotated', 'in', 'anchored', 'if', 'unless', 'store', 'else'):
                self.raise_exception('"else" without a matching execution block.')

            # else block content
            funcname = self.fork_function('e')

            # we know the pastline is valid, otherwise it would have already thrown an exception last time
            pastfuncname = self.function_path('e'+str(self.relcounter-2))
            entity = '@e[tag=' + funcname + '.ELSE]'
            summon = 'execute unless entity ' + entity + ' run summon area_effect_cloud 0 0 0 {Age:-2147483648,Duration:-1,WaitTime:-2147483648,Tags:["' + \
                funcname + '.ELSE"]}'
            self.functions[pastfuncname].commands.insert(0, summon)

            call = 'execute unless entity ' + entity + ' '

            # add additional execute params to the call
            params = self.process_tokens(tokens[1:], False, True)
            if len(params) == 0:
                call += 'run ' + self.call_function(funcname)
            else:
                call += params + ' run ' + self.call_function(funcname)  
            for c in self.auxcommands:
                self.commands.append(c)
            self.add_command(call)
            self.add_command('kill '+ entity)
            self.check_break(funcname)

        # repeat
        elif tokens[0].strip() == 'repeat':

            count = ''.join(tokens[1:]).strip().strip(':')

            try:
                count = int(count)
            except:
                self.raise_exception('"' + count + '" is not a valid number.')

            funcname = self.fork_function('r')
            # setup execution call
            for i in range(count):
                self.add_command(self.call_function(funcname))
            self.check_break(funcname)

        # while loop
        elif tokens[0].strip() in ('while', 'whilenot', 'loop'):
            if tokens[-1] == ':':
                tokens.pop()  # remove a trailing ':'

            funcname = self.fork_function('w')
            # setup execution call
            if tokens[1] == ':':
                tokens.pop(1)

            if tokens[0].strip() == 'loop':
                call = 'execute ' + self.process_tokens(tokens[1:], False, True) + ' run ' + self.call_function(funcname)
            elif tokens[0].strip() == 'while':
                call = 'execute if ' + self.process_tokens(tokens[1:], False, True) + ' run ' + self.call_function(funcname)
            else:
                call = 'execute unless ' + self.process_tokens(tokens[1:], False, True) + ' run ' + self.call_function(funcname)

            for c in self.auxcommands:
                self.add_command(c)
                self.functions[funcname].add_command(c)
            self.add_command(call)
            self.functions[funcname].call_loop(funcname, call)
            if self.functions[funcname].hasbreak:
                self.add_command('kill @e[tag=' + funcname + '.BREAK]')
            if self.functions[funcname].hascontinue:
                self.add_command('kill @e[tag=' + funcname + '.CONTINUE]')

        # break
        elif tokens[0].strip() == 'break':
            if self.inloop is None:
                self.raise_exception('"break" outside of loop.')

            self.hasbreak = True
            self.add_command('summon area_effect_cloud 0 0 0 {Age:-2147483648,Duration:-1,WaitTime:-2147483648,Tags:["' + '.'.join(
                self.inloop) + '.BREAK"]}')

        # continue
        elif tokens[0].strip() == 'continue':
            if self.inloop is None:
                self.raise_exception('"continue" outside of loop.')

            self.hascontinue = True
            self.add_command('summon area_effect_cloud 0 0 0 {Age:-2147483648,Duration:-1,WaitTime:-2147483648,Tags:["' + '.'.join(
                self.inloop) + '.CONTINUE"]}')

        # vanilla command
        elif self.infunc is None:
            self.raise_exception(
                'Vanilla command outside of a function. This is not allowed, consider putting it inside the load function.')
        elif tokens[0].strip() == 'function':
            self.raise_exception(
                'The /function command is no longer used. Just type your function as if it were a command.')
        elif tokens[0].strip() in ('include', 'file'):
            self.raise_exception(
                '"' + tokens[0].strip() + '" statement should not be inside of a function.')

        else:
            self.add_command(self.process_tokens(tokens))

        self.pastline = line

    # called on a set of tokens, intended to evaluate to a single string which represents some value which can be
    # inserted into vanilla commands. this can be an entity, integer, or series of vanilla commands (or components
    # thereof) will handle references as part of an expression.
    def process_tokens(self, tokens, augsummon=False, conditional=False, dest=None):

        args = broad_tokenize(''.join(tokens).strip())

        # special case: assigning as a summon
        if augsummon and args[0] == 'summon':
            ref = ' '.join(args)
            if 'Tags:[' in ref:
                self.add_command(ref.replace('Tags:[', 'Tags:["' + dest + '",'))
            elif ref[-1] == '}':
                self.add_command(ref[:-1] + ',Tags:["' + dest + '"]}')
            else:
                self.add_command(ref + ' {Tags:["' + dest + '"]}')
            return '@' # don't make any further assignments

        # special case: conditional
        if conditional and len(args) > 2:
            for i in range(1, len(args) - 1):
                op = args[i]
                if op in ('<', '>', '==', '<=', '>='):
                    refleft = self.reference_path(args[i - 1])
                    refright = self.reference_path(args[i + 1])
                    varleft, varright = None, None

                    # left side
                    if refleft != None and self.refs[refleft] == 'i':
                        varleft = refleft
                    elif args[i - 1].isdigit():
                        varleft = args[i - 1]
                    else:
                        self.raise_exception('"' + args[i - 1] + '" is not a valid integer variable or constant.')

                    # right side
                    if refright != None and self.refs[refright] == 'i':
                        varright = refright
                    elif args[i + 1].isdigit():
                        varright = args[i + 1]
                    else:
                        self.raise_exception('"' + args[i + 1] + '" is not a valid integer variable or constant.')

                    if i > 1 and not args[i - 2] in ('if', 'unless', 'while', 'whilenot'):
                        self.raise_exception('Integer comparison without a conditional.')

                    if varleft.isdigit() and varright.isdigit():
                        self.raise_exception('Cannot compare two constants.')
                    elif varleft.isdigit():
                        args[i - 1] = check_int(varright, op_converse(op), varleft, self.namespace)
                    elif varright.isdigit():
                        args[i - 1] = check_int(varleft, op, varright, self.namespace)
                    else:
                        self.namespace.add_int(varleft + '.TEST')
                        self.auxiliary_command(augment_int(varleft + '.TEST', varleft, '=', self.namespace))
                        self.auxiliary_command(augment_int(varleft + '.TEST', varright, '-=', self.namespace))
                        args[i - 1] = check_int(varleft + '.TEST', op, '0', self.namespace)

                    args[i], args[i + 1] = None, None

        tokens = tokenize(' '.join(a for a in args if a is not None))

        for i, token in enumerate(tokens):
            refpath = self.reference_path(token.split('#')[0])
            token = self.process_expression(token)
            # narrowing
            if refpath is not None and token[0] == '@' and i != len(tokens) - 1 and tokens[i + 1][0] == '[' \
                    and tokens[i][-1] != ' ':
                tokens[i + 1] = ',' + tokens[i + 1][1:]
                token = token[:-1]
            tokens[i] = token

        return (''.join(tokens)).strip()

    # <code> refers to the type of function. These are the same codes as are used in function path/file names.
    # 'w' = while loop body
    # 'e' = implicit execution
    # 'r' = repeat loop body
    # 'b' = chained continue/break-check function
    # 's' = forked string function (not used in this function)
    # returns the name of the function which was generated
    def fork_function(self, code):

        # generate inner content as function
        inloop = self.inloop
        newpointer = self.pointer + 1
        newdepth = self.expecteddepth + 1

        funcpath = self.path + [code + str(self.relcounter)]

        # check if creating new loop
        if code in 'w':
            inloop = funcpath

        # check if a break
        if code == 'b':
            newdepth -= 1
            while newpointer < len(self.lines) and self.lines[newpointer][0] > self.expecteddepth:
                newpointer += 1
            if self.path[-1][0] == 'b':
                funcpath = self.path[:-1] + ['b' + str(int(self.path[-1][1]) + 1)]

        funcname = '.'.join(funcpath)

        try:
            self.functions[funcname] = Function(funcpath, self.refs, {}, {}, self.lines, self.namespace, newpointer, newdepth,
                                                self.infunc, inloop, self.stringdata)
            # if this is a break-chain, we should carry over the pastline because its the same level of indentation
            if code == 'b':
                self.functions[funcname].pastline = self.lines[self.pointer][1]
            self.functions[funcname].compile()
        except CompilationSyntaxError as e:
            if code != 'b':
                raise e

        self.relcounter += 1
        return funcname

    # this will call a sub-function of name <funcname>
    def call_function(self, funcname, *funcdata):

        for f in funcdata:
            if f[-1] == '\\':
                self.raise_exception('"\\" cannot be the last character of a string.')

        return '!f{' + funcname + '}' + ''.join('{' + f.replace('}','\\}').replace('{','\\{') + '}' for f in funcdata)

    # this is called after spawning a forked function. It checks if the function has a break/continue,
    # and will branch the current function accordingly.
    def check_break(self, funcname):

        func = self.functions[funcname]

        if self.inloop is not None and (func.hasbreak or func.hascontinue):

            fork = self.fork_function('b')
            call = 'execute '

            if func.hasbreak:
                self.hasbreak = True
                call += 'unless entity @e[tag=' + '.'.join(self.inloop) + '.BREAK] '

            if func.hascontinue:
                self.hascontinue = True
                call += 'unless entity @e[tag=' + '.'.join(self.inloop) + '.CONTINUE] '

            # if fork isn't in self.functions, then it was collapsed and we don't have to worry about it.
            if fork in self.functions and len(self.functions[fork].commands) > 0:
                call += 'run ' + self.call_function(fork)
                self.add_command(call)

            # breaks should always propagate backwards through a b-function chain.
            if self.functions[fork].hasbreak:
                self.hasbreak = True
            if self.functions[fork].hascontinue:
                self.hascontinue = True

    # this is called by a loop's parent function to set up that loop's self-call
    def call_loop(self, funcname, call):

        func = self.functions[funcname]
        while len(func.commands[-1]) > 2 and func.commands[-1][-2] == 'b':
            newname = 'main.' + func.commands[-1].split(':')[-1]
            func = self.functions[newname]

        # <call> should be a call directly to the outermost loop function
        newcall = call

        # if the loop has a break/continue, we need to ensure it hasn't been called before looping again
        if func.hasbreak or func.hascontinue:

            if func.hasbreak:
                newcall = 'unless entity @e[tag=' + '.'.join(self.inloop) + '.BREAK] run ' + newcall

            if func.hascontinue:
                newcall = 'unless entity @e[tag=' + '.'.join(self.inloop) + '.CONTINUE] run ' + newcall

            newcall = 'execute ' + newcall

        func.commands.append(newcall)

        # if the loop has a continue,
        # we need to reset it to the beginning if we reach the end and continue has been called
        if self.functions[funcname].hascontinue:
            cmd = 'kill @e[tag=' + '.'.join(self.inloop) + '.CONTINUE]'
            self.functions[funcname].commands.insert(0, cmd)

            cmd = 'execute if entity @e[tag=' + '.'.join(self.inloop) + '.CONTINUE] run ' + call
            self.functions[funcname].commands.append(cmd)
