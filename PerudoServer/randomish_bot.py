#!c:\python24\python.exe -u

import perudo_client
import random
import common_utils

class RandomBot(perudo_client.Client):
	def set_name(self):
		self.name = "Randomish Bot"

	def get_call(self, dummy_text):
		# Automatically call, if the previous call is too high or is the highest call
		call_dudo = False
		if len(self.call_list) > 0:
			previous_call = self.call_list[-1]
			if self.is_call_impossible(previous_call, True) or self.is_highest_call(previous_call):
				call_dudo = True
			elif random.random() < self.probability_needed_for_dudo(previous_call):
				call_dudo = True

		if call_dudo:
			call = common_utils.Call(self.player_id, common_utils.DUDO)
		else:
			# formulate a normal call
			is_good_call = False
			par_dice = self.get_par_dice()
			if self.call_list:
				# Not the first call
				previous_call = self.call_list[-1]
				previous_quantity = previous_call.get_quantity()
				previous_value = previous_call.get_value()

				if self.is_round_palafico and len(self.dice) > 1:
					value = previous_value
					quantity = previous_quantity + 1
				else:
					value = random.randint(1, 6)
					quantity = self.get_lowest_raise_on_value(previous_call, value)
			else:
				if self.is_round_palafico:
					value = random.randint(1, 6)
					quantity = random.randint(1, max(1, par_dice))
				else:
					value = random.randint(1, 6)
					quantity = random.randint(max(1, par_dice - 1), min(par_dice + 1, self.get_num_dice_in_play()))

			call = common_utils.Call(self.player_id, "%dx%d" % (quantity, value))

		self.display("Trying %s" % call.get_call_string())
		self.send(call.get_call_string())

	def probability_needed_for_dudo(self, previous_call):
		par_dice = self.get_par_dice()
		if previous_call.get_value() == 1 and not self.is_round_palafico:
			par_dice /= 2
		if par_dice > previous_call.get_quantity() + 1:
			return 0
		if par_dice * 2 < previous_call.get_quantity():
			return 1
		return 1.0 / self.get_num_players_remaining()

	def get_par_dice(self):
		if self.is_round_palafico:
			return self.get_num_dice_in_play() / 6
		else:
			return self.get_num_dice_in_play() / 3

	def get_lowest_raise_on_value(self, previous_call, value):
		previous_quantity = previous_call.get_quantity()
		previous_value = previous_call.get_value()

		if value == previous_value:
			quantity = previous_quantity + 1
		elif not self.is_round_palafico and value == 1:
			quantity = (previous_quantity + 1) / 2
		elif not self.is_round_palafico and previous_value == 1:
			quantity = (previous_quantity * 2) + 1
		elif value < previous_value:
			quantity = previous_quantity + 1
		else:
			quantity = previous_quantity

		return quantity

if __name__ == "__main__":
	import optparse

	arguments = ['SERVER_NAME']
	parser = optparse.OptionParser(usage = "Usage: %%prog [options] %s" % ' '.join(arguments))
	(options, args) = parser.parse_args()

	if len(args) == 1:
		server = args[0]
		RandomBot(server)
	else:
		parser.print_help()
