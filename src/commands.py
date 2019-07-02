# entity tools


def assign_entity(query, tag):
    return 'tag %s add %s' % (query, tag)


def select_entity(tag):
    return '@e[tag=%s]' % tag


def select_player(tag):
    return '@p[tag=%s]' % tag


def select_entity1(tag):
    return '@e[tag=%s,limit=1]' % tag


def select_player1(tag):
    return '@p[tag=%s,limit=1]' % tag


def clear_tag(tag):
    return 'tag @e[tag=%s] remove %s' % (tag, tag)


# integer tools

def assign_int(value, var, namespace):
    return 'scoreboard players set @e[name=%s.VARS,limit=1] %s %s' % (namespace.pack, namespace.intmap[var], value)


def add_int(value, var, namespace):
    return 'scoreboard players add @e[name=%s.VARS,limit=1] %s %s' % (namespace.pack, namespace.intmap[var], value)


def sub_int(value, var, namespace):
    return 'scoreboard players remove @e[name=%s.VARS,limit=1] %s %s' % (namespace.pack, namespace.intmap[var], value)


def augment_int(var1, var2, op, namespace):
    return 'scoreboard players operation @e[name=%s.VARS,limit=1] %s %s @e[name=%s.VARS,limit=1] %s' % (
    namespace.pack, namespace.intmap[var1], op, namespace.pack, namespace.intmap[var2])


def select_int(var, namespace):
    return '@e[name=%s.VARS,limit=1] %s' % (namespace.pack, namespace.intmap[var])


def text_int(var, namespace):
    return '{"score":{"name":"@e[name=%s.VARS]","objective":"%s"}}' % (namespace.pack, namespace.intmap[var])


def summon_vars(pack):
    return 'execute unless entity @e[name=' + pack + '.VARS] run summon armor_stand 0 0 0 {Marker:1b,Invisible:1b,NoGravity:1b,CustomName:"\\"' + pack + '.VARS\\""}'


def check_int(var, op, val, namespace):
    if op == '==':
        return 'entity @e[name=%s.VARS,scores={%s=%s}]' % (namespace.pack, namespace.intmap[var], val)
    if op == '>=':
        return 'entity @e[name=%s.VARS,scores={%s=%s..}]' % (namespace.pack, namespace.intmap[var], val)
    if op == '<=':
        return 'entity @e[name=%s.VARS,scores={%s=..%s}]' % (namespace.pack, namespace.intmap[var], val)
    if op == '>':
        return 'entity @e[name=%s.VARS,scores={%s=%s..}]' % (namespace.pack, namespace.intmap[var], str(int(val) + 1))
    if op == '<':
        return 'entity @e[name=%s.VARS,scores={%s=..%s}]' % (namespace.pack, namespace.intmap[var], str(int(val) - 1))


def op_converse(op):
    return op.replace('>', '@').replace('<', '>').replace('@', '<')