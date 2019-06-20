def select_entity(tag):
	return '@e[tag=%s]' % tag

def clear_tag(tag):
	return 'tag @e remove %s' % tag