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

def assign_int(value, var, pack):
	return 'scoreboard players set @e[name=%s.VARS,limit=1] %s %s' % (pack, var, value)

def add_int(value, var, pack):
	return 'scoreboard players add @e[name=%s.VARS,limit=1] %s %s' % (pack, var, value)

def sub_int(value, var, pack):
	return 'scoreboard players remove @e[name=%s.VARS,limit=1] %s %s' % (pack, var, value)

def augment_int(var1, var2, op, pack):
	return 'scoreboard players operation @e[name=%s.VARS,limit=1] %s %s @e[name=%s.VARS,limit=1] %s' % (pack, var1, op, pack, var2)

def select_int(var, pack):
	return '@e[name=%s.VARS,limit=1] %s' % (pack, var)

def summon_vars(pack):
	return 'execute unless entity @e[name='+pack+'.VARS] run summon armor_stand 0 0 0 {Marker:1b,Invisible:1b,NoGravity:1b,CustomName:"\\"'+pack+'.VARS\\""}'

def check_int(var, op, val, pack):
	if op == '==':
		return 'entity @e[name=%s.VARS,scores={%s=%s}]' % (pack, var, val)
	if op == '>=':
		return 'entity @e[name=%s.VARS,scores={%s=%s..}]' % (pack, var, val)
	if op == '<=':
		return 'entity @e[name=%s.VARS,scores={%s=..%s}]' % (pack, var, val)
	if op == '>':
		return 'entity @e[name=%s.VARS,scores={%s=%s..}]' % (pack, var, str(int(val)+1))
	if op == '<':
		return 'entity @e[name=%s.VARS,scores={%s=..%s}]' % (pack, var, str(int(val)-1))