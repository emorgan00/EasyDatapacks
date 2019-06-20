next_id = 0

class Entity:

	def __init__(this, query):
		this.query = query
		this.id = next_id

	def assignation(this):
		return 'scoreboard players set %s id %s' % (this.selector(), this.id)

	def selector(this):
		return '@e[scores={id=%i}]' % this.id