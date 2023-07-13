import datetime
import calls
import time

# ================================================================================
# Common const
# ================================================================================

DUDO = 'DUDO'
SPECIAL_CALLS = [DUDO]


START_GAME_DELIMITER = "Game starts"
END_GAME_DELIMITER = "Game ends"
START_ROUND_DELIMITER = "Round starts"
END_ROUND_DELIMITER = "Round ends"



# ================================================================================
# Common classes
# ================================================================================

class Call(object):
	def __init__(self, a_player_id, a_call):
		self.player_id = a_player_id
		self.quantity = None
		self.value = None
		a_call = a_call.upper()
		try:
			if a_call in SPECIAL_CALLS:
				self.call_string = a_call
				self.validation = True
			else:
				# validate the call
				(quantity, value) = a_call.split('X')
				self.quantity = int(quantity)
				self.value = int(value)
				if self.value < 1 or self.value > 6:
					self.validation = False
				else:
					self.call_string = "%sx%s" % (self.quantity,  self.value)
					self.validation = True
		except:
			self.validation = False
			self.call_string = a_call

	def __str__(self):
		return "%s -> %s" % (self.player_id, self.call_string)

	def __cmp__(self, other_call):
		if self.call_string == DUDO:
			return 1
		
		if (
			other_call is None or
			(self.value == 1 and other_call.value != 1 and self.quantity * 2 >= other_call.quantity) or 
			(self.value != 1 and other_call.value == 1 and self.quantity > other_call.quantity * 2)
			):
			return 1
		elif(
			((self.value == 1 and other_call.value == 1) or (self.value != 1 and other_call.value != 1)) and
			((self.quantity > other_call.quantity) or (self.quantity == other_call.quantity and self.value > other_call.value))
			):
			return 1
		elif self.quantity == other_call.quantity and self.value == other_call.value:
			return 0
		else:
			return -1
			

	def get_player_id(self):
		return self.player_id

	def is_valid(self):
		return self.validation

	def is_dudo(self):
		return self.call_string == DUDO

	def get_value_quantity(self):
		return (self.value, self.quantity)

	def get_value(self):
		return self.value

	def get_quantity(self):
		return self.quantity

	def get_call_string(self):
		return self.call_string

	def help():
		return "A valid call should be like 3x5 meaning three dice showing fives, or one of those special calls: %s" % ', '.join(SPECIAL_CALLS)


class PalaficoCall(Call):
	def __cmp__(self, other_call):
		if self.call_string == DUDO:
			return 1

		if other_call is None:
			return 1

		return cmp((self.quantity, self.value), (other_call.quantity, other_call.value))



# ================================================================================
# Common utils functions
# ================================================================================


def get_dice_break_down(dice, dice_dict = {}):
	for die in dice:
		dice_dict[die] = dice_dict.get(die, 0) + 1
	return dice_dict


def get_delimiter_string(text):
	new_text = "%s (%s)" % (text, datetime.datetime.now().strftime("%H:%M:%S"))
	text_len = len(new_text)

	max_char = 68
	if text_len < max_char:
		return '=' * (max_char/2 - text_len/2) + new_text + '=' * (max_char/2 - (text_len - text_len/2))
	else:
		return new_text

def get_bing(previous_call, ones_are_wild, must_keep_value = False):
	if previous_call is None:
		if ones_are_wild:
			return "1x2"
		else:
			return "1x1"

	(value, quantity) = previous_call.get_value_quantity()
	if ones_are_wild:
		if value == 1:
			return "%dx%d" % (2 * quantity + 1, 2)
		elif value != 6:
			return "%dx%d" % (quantity, value+1)
		elif value == 6:
			if (quantity % 2 == 0):
				return "%dx%d" % (quantity/2, 1)
			else:
				return "%dx%d" % (quantity + 1, 2)
	else:
		if must_keep_value:
			return "%dx%d" % (quantity + 1, value)
		else:
			if value != 6:
				return "%dx%d" % (quantity, value+1)
			elif value == 6:
				return "%dx%d" % (quantity + 1, 1)

def get_next_call_of(value, previous_call, ones_are_wild):
	dummy_player_id = 0
	possible_call = Call(dummy_player_id, get_bing(previous_call, ones_are_wild))

	while possible_call.get_value() != value:
		possible_call = Call(dummy_player_id, get_bing(possible_call, ones_are_wild))
	return possible_call.get_call_string()

def get_call_name_list(call_list):
	call_names = []
	for call_name_test_func in calls.call_name_test_funcs:
		potential_call_name = call_name_test_func(call_list)
		if potential_call_name:
			call_names.append(potential_call_name)
	return call_names

def get_call_name_appendage(call_list):
	"""Returns list of call names as a string " (bing, ace)".
	call_list[-1] is the latest call; call_list[-2] is the
	previous call etc.  If no call name exists then the empty
	string is returned (no brackets)."""
	name_list = get_call_name_list(call_list)
	if name_list:
		return ' (%s)' % (', '.join(name_list))
	else:
		return ''

def beep(number = 1):
	import sys
	if number < 1:
		return
	if number == 1:
		sys.stdout.write("%c" % 7)
	else:
		for i in range(number):
			sys.stdout.write("%c" % 7)
			time.sleep(0.2)


