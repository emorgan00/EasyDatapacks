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