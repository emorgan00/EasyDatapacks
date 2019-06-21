def assign_entity(query, tag):
	return 'tag %s add %s' % (query, tag)

def select_entity(tag):
	return '@e[tag=%s]' % tag

def clear_tag(tag):
	return 'tag @e[tag=%s] remove %s' % (tag, tag)