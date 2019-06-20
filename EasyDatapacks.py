from function import *

print create_function('give_food', {'player': True}, {}, '''

give player steak 1
tellraw player "hi"

''')