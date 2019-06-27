from commands import *
from reader import *
from validate import *


class CompilationError(Exception):
    pass

class CompilationSyntaxError(CompilationError):
    pass


class Function:

    def __init__(self, path, params, lines, namespace, start, expecteddepth, infunc, inloop):

        # master list of all generated vanilla commands in the function
        self.commands = []

        # commands which are needed to process another command, reset every line
        self.auxcommands = []

        # path to this function, e.g. ['main', 'load'] refers to the main.load function
        self.path = path
        self.name = '.'.join(path)

        self.namespace = namespace
        self.functions = namespace.functions

        self.refs = namespace.refs
        self.pack = namespace.pack

        # the parameters supplied to this function, follows the same format as refs
        self.params = params

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

        # stores the content of the line before the one we are currently parsing. Currently only used for if-else logic.
        self.pastline = ''

        # this will get set to true when this function is called by another function. Unused functions will get
        # "collapsed".
        self.used = False

        # stuff with break/return
        self.infunc = infunc  # stores the user-defined function which this function is a member of
        self.inloop = inloop  # stores the loop (while/whilenot) which this function is most immediately a member of
        self.hasbreak = False
        self.hascontinue = False

    def __str__(self):

        out = self.name[5:] + ': '
        out += str(self.params)
        out += ' (' + str('.'.join(self.infunc[1:])) + ')'
        out += ' (' + str('.'.join(self.inloop[1:])) + ')' if self.inloop is not None else ' ()'
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

    # will create an exception with line number and function name
    # syntaxerror means we are dealing with missing content
    def raise_exception(self, string, syntaxerror=False):

        if syntaxerror:
            self.pointer -= 1
            out = 'Error after line '
        else:
            out = 'Error at line '

        out += '%i: "%s"\n\t' % (self.lines[self.pointer][2], self.lines[self.pointer][1])
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
            self.refs[self.name + '.' + p] = self.params[p]
            self.locals.append(self.name + '.' + p)

            if self.params[p] == 'i':
                self.namespace.ints.add(self.name + '.' + p)

        # pre-process function headers:
        for i, p in enumerate(self.lines[self.pointer:]):
            if p[0] < depth:
                break
            if p[0] > depth:
                continue
            if p[1][:3] == 'def':

                tokens = tokenize(p[1])
                funcpath = self.path + [tokens[1].strip()]
                if not valid_name(tokens[1].strip()):
                    self.raise_exception('Invalid function name: "' + tokens[1].strip() + '".')

                funcparams = {}
                for token in (''.join(tokens[2:])).split(' '):
                    token = token.strip(':')
                    if len(token) == 0:
                        continue
                    if valid_name(token):
                        param = token.split('#')
                        if len(param) == 1:
                            funcparams[token] = 'e'
                        elif param[1] in ('e', 'i'):
                            funcparams[param[0]] = param[1]
                        else:
                            self.raise_exception(
                                'Invalid parameter clarifier: "' + token.strip() + '" for function ' + tokens[
                                    1].strip() + '.')
                    else:
                        self.raise_exception(
                            'Invalid parameter name "' + token.strip() + '" for function ' + tokens[1].strip() + '.')

                if '.'.join(funcpath) in self.functions:
                    self.raise_exception('Duplicate function "' + funcpath[-1] + '"')

                self.functions['.'.join(funcpath)] = Function(funcpath, funcparams, self.lines, self.namespace,
                                                              self.pointer + i + 1, depth + 1, funcpath, None)
                self.functions['.'.join(funcpath)].used = True

        # process lines
        while self.pointer < len(self.lines):

            if self.lines[self.pointer][0] == depth:
                self.process_line()
            elif self.lines[self.pointer][0] < depth:
                break
            self.pointer += 1

        # dispel locals
        for ref in self.locals:
            if self.refs[ref] == 'e':  # an entity
                self.add_command(clear_tag(ref))
            else:  # something else
                pass

            self.refs.pop(ref)

    # called on a single token. Detects references and handles clarifiers. For multi-token strings, use process_tokens.
    def process_expression(self, expression):

        components = expression.strip().split('#')
        ref = components[0]

        path = self.reference_path(ref)
        if path is not None:  # some reference
            if self.refs[path] == 'e':  # an entity
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
                return out + (' ' if expression[-1] == ' ' else '')

            elif self.refs[path] == 'i':  # integer variable
                return select_int(path, self.pack) + (' ' if expression[-1] == ' ' else '')

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
            dest = self.reference_path(tokens[0].strip())

            # assigning something for the first time
            if dest is None:
                dest = self.name + '.' + tokens[0].strip()
                self.locals.append(dest)

            # clearing an old assignment
            else:
                if self.refs[dest] == 'e':  # an entity
                    self.add_command(clear_tag(dest))
                else:  # something else
                    pass

            # evaluate the right side, perform the new assignment
            expression = self.process_tokens(tokens[2:], True)
            refpath = self.reference_path((''.join(tokens[2:])).strip())

            if expression.isdigit():  # an integer constant
                self.refs[dest] = 'i'
                self.add_command(assign_int(expression, dest, self.pack))
                self.namespace.ints.add(dest)

            elif refpath in self.refs and self.refs[refpath] == 'i':  # an integer variable
                self.refs[dest] = 'i'
                self.add_command(augment_int(dest, refpath, '=', self.pack))
                self.namespace.ints.add(dest)

            elif expression[0] == '@':  # an entity
                self.refs[dest] = 'e'
                self.add_command(assign_entity(expression, dest))
                # special case: assigning as a summon
                if expression == select_entity('assign'):
                    self.add_command(clear_tag('assign'))

            else:  # something else
                self.raise_exception('Cannot assign "' + expression + '" to variable.')

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
            if inref is None and expression.isdigit():  # int constant
                if op == '+=':
                    self.add_command(add_int(expression, dest, self.pack))
                elif op == '-=':
                    self.add_command(sub_int(expression, dest, self.pack))
                else:
                    var2 = self.namespace.add_constant(expression)
                    self.add_command(augment_int(dest, var2, op, self.pack))

            elif inref is None or self.refs[inref] != 'i':
                self.raise_exception('Cannot perform augmented assignment with "' + expression + '"')

            # valid variable
            else:
                self.add_command(augment_int(dest, inref, op, self.pack))

        # increment / decrement
        elif len(tokens) > 2 and ''.join(tokens[1:]) in ('++', '--'):

            var = tokens[0].strip()
            ref = self.reference_path(var)
            if ref == None:
                self.raise_exception('Cannot perform augmented assignment on "' + var + '"')
            elif ''.join(tokens[1:]) == '++':
                self.add_command(add_int('1', ref, self.pack))
            else:
                self.add_command(sub_int('1', ref, self.pack))

        # definining a new function
        elif tokens[0].strip() == 'def':

            self.functions[self.name + '.' + tokens[1].strip()].compile()

        # calling a custom function
        elif funcpath is not None:

            if funcpath == '.'.join(self.infunc):
                self.raise_exception(
                    'Attempt at recursing in function ' + '.'.join(self.infunc) + ', this is not supported.')

            func = self.functions[funcpath]
            givenparams = broad_tokenize(''.join(tokens[1:]))
            if len(givenparams) > len(func.params):
                self.raise_exception('Too many parameters for function "' + tokens[0].strip() + '".')

            for i, p in enumerate(func.params):

                expression = None
                try:
                    expression = self.process_expression(givenparams[i]).strip()
                except IndexError:
                    self.raise_exception('Not enough paramaters for function "' + tokens[0].strip() + '".')

                if func.params[p] == 'e':  # an entity
                    self.add_command(assign_entity(expression, func.name + '.' + p))

                elif func.params[p] == 'i':  # in integer
                    if expression.isdigit():  # constant int
                        self.add_command(assign_int(expression, func.name + '.' + p, self.pack))
                    elif expression[0] == '@':  # reference to int
                        self.add_command(
                            augment_int(func.name + '.' + p, self.reference_path(givenparams[i]), '=', self.pack))

            self.add_command(self.call_function(funcpath))

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

        # if/else
        elif tokens[0].strip() == 'else':
            if tokens[-1] == ':':
                tokens.pop()  # remove a trailing ':'

            if len(tokens) > 1:
                self.raise_exception('"else" does not take any additional parameters.')

            if self.pastline[:3] != 'if ':
                self.raise_exception('"else" without matching "if"')
            self.lines[self.pointer] = (self.lines[self.pointer][0], 'unless' + self.pastline[2:])
            self.process_line()
            return

        # repeat
        elif tokens[0].strip() == 'repeat':

            count = None
            for token in tokens[1:]:
                if token.isdigit():
                    count = int(token)
                    break
            if count is None:
                self.raise_exception('"repeat" without a number following it.')

            funcname = self.fork_function('r')
            # setup execution call
            for i in range(count):
                self.add_command(self.call_function(funcname))
            self.check_break(funcname)

        # while loop
        elif tokens[0].strip() in ('while', 'whilenot'):
            if tokens[-1] == ':':
                tokens.pop()  # remove a trailing ':'

            funcname = self.fork_function('w')
            # setup execution call
            if tokens[0].strip() == 'while':
                call = 'execute if ' + self.process_tokens(tokens[1:], False, True) + ' run ' + self.call_function(
                    funcname, True)
            else:
                call = 'execute unless ' + self.process_tokens(tokens[1:], False, True) + ' run ' + self.call_function(
                    funcname, True)
            for c in self.auxcommands:
                self.add_command(c)
                self.functions[funcname].add_command(c)
            self.add_command(call)
            self.functions[funcname].call_loop(funcname, call)
            if self.functions[funcname].hasbreak:
                self.add_command('kill @e[type=armor_stand,tag=' + funcname + '.BREAK]')
            if self.functions[funcname].hascontinue:
                self.add_command('kill @e[type=armor_stand,tag=' + funcname + '.CONTINUE]')

        # break
        elif tokens[0].strip() == 'break':
            if self.inloop is None:
                self.raise_exception('"break" outside of loop.')

            self.hasbreak = True
            self.add_command('summon armor_stand 0 0 0 {Marker:1b,Invisible:1b,NoGravity:1b,Tags:["' + '.'.join(
                self.inloop) + '.BREAK"]}')

        # continue
        elif tokens[0].strip() == 'continue':
            if self.inloop is None:
                self.raise_exception('"continue" outside of loop.')

            self.hascontinue = True
            self.add_command('summon armor_stand 0 0 0 {Marker:1b,Invisible:1b,NoGravity:1b,Tags:["' + '.'.join(
                self.inloop) + '.CONTINUE"]}')

        # vanilla command
        elif self.infunc is None:
            self.raise_exception(
                'Vanilla command outside of a function. This is not allowed, consider putting it inside the load '
                'function.')
        elif tokens[0].strip() == 'function':
            self.raise_exception(
                'The /function command is no longer used. Just type your function as if it were a command.')

        else:
            self.add_command(self.process_tokens(tokens))

        self.pastline = line

    # called on a set of tokens, intended to evaluate to a single string which represents some value which can be
    # inserted into vanilla commands. this can be an entity, integer, or series of vanilla commands (or components
    # thereof) will handle references as part of an expression.
    def process_tokens(self, tokens, augsummon=False, conditional=False):

        args = broad_tokenize(''.join(tokens).strip())

        # special case: assigning as a summon
        if augsummon and args[0] == 'summon':
            ref = ' '.join(args)
            if 'Tags:[' in ref:
                self.add_command(ref.replace('Tags:[', 'Tags:["assign",'))
            elif ref[-1] == '}':
                self.add_command(ref[:-1] + ',Tags:["assign"]}')
            else:
                self.add_command(ref + ' {Tags:["assign"]}')
            return select_entity('assign')

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
                        args[i - 1] = check_int(varright, op_converse(op), varleft, self.pack)
                    elif varright.isdigit():
                        args[i - 1] = check_int(varleft, op, varright, self.pack)
                    else:
                        self.namespace.ints.add(varleft + '.TEST')
                        self.auxiliary_command(augment_int(varleft + '.TEST', varleft, '=', self.pack))
                        self.auxiliary_command(augment_int(varleft + '.TEST', varright, '-=', self.pack))
                        args[i - 1] = check_int(varleft + '.TEST', op, '0', self.pack)

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
            self.functions[funcname] = Function(funcpath, {}, self.lines, self.namespace, newpointer, newdepth,
                                                self.infunc, inloop)
            self.functions[funcname].compile()
        except CompilationSyntaxError as e:
            if code != 'b':
                raise e

        self.relcounter += 1
        return funcname

    # this will call a sub-function of name <funcname>. <nocollapse> will disable collapsing a 1-line function
    def call_function(self, funcname, nocollapse=False):

        func = self.functions[funcname]
        if len(func.commands) > 1 or nocollapse:
            func.used = True
            return 'function ' + self.pack + ':' + funcname[5:]
        elif len(func.commands) == 1:
            # if a function is only 1 command, just execute it directly.
            return func.commands[0]
        else:
            func.used = True
            return 'function ' + self.pack + ':' + funcname[5:]

    # this is called after spawning a forked function. It checks if the function has a break/continue,
    # and will branch the current function accordingly.
    def check_break(self, funcname):

        func = self.functions[funcname]

        if self.inloop is not None and (func.hasbreak or func.hascontinue):

            fork = self.fork_function('b')
            call = 'execute '

            if func.hasbreak:
                self.hasbreak = True
                call += 'unless entity @e[type=armor_stand,tag=' + '.'.join(self.inloop) + '.BREAK] '

            if func.hascontinue:
                self.hascontinue = True
                call += 'unless entity @e[type=armor_stand,tag=' + '.'.join(self.inloop) + '.CONTINUE] '

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
                newcall = 'unless entity @e[type=armor_stand,tag=' + '.'.join(self.inloop) + '.BREAK] run ' + newcall

            if func.hascontinue:
                newcall = 'unless entity @e[type=armor_stand,tag=' + '.'.join(self.inloop) + '.CONTINUE] run ' + newcall

            newcall = 'execute ' + newcall

        func.commands.append(newcall)

        # if the loop has a continue, we need to reset it to the beginning if we reach the end and continue has been
        # called
        if self.functions[funcname].hascontinue:
            cmd = 'kill @e[type=armor_stand,tag=' + '.'.join(self.inloop) + '.CONTINUE]'
            self.functions[funcname].commands.insert(0, cmd)

            cmd = 'execute if entity @e[type=armor_stand,tag=' + '.'.join(self.inloop) + '.CONTINUE] run ' + call
            self.functions[funcname].commands.append(cmd)
