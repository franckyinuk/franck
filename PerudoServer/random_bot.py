#!c:\python24\python.exe -u

import perudo_client
import random
import common_utils


class RandomBot(perudo_client.Client):
	def set_name(self):
		self.name = "Random Bot"

	def get_call(self, dummy_text):
		# Automatically call, if the previous call is too high or is the highest call
		call_dudo = False
		if (len(self.call_list) > 0 and (self.is_call_impossible(self.call_list[-1], True) or self.is_highest_call(self.call_list[-1]))):
			call_dudo = True
		
		if call_dudo and len(self.call_list) > 0:
			call = common_utils.Call(self.player_id, common_utils.DUDO)
		else:
			# formulate a normal call
			is_good_call = False
			while not is_good_call:
				value = random.randint(1, 6)
				num_dice = random.randint(1, self.get_num_dice_in_play())
				call = common_utils.Call(self.player_id, "%dx%d" %(num_dice, value))
				#print "Thinking of %s" % call
				if self.is_round_palafico:
					call.__class__ = common_utils.PalaficoCall

				is_good_call = True
				if self.is_call_impossible(call, False):
					is_good_call = False
				elif len(self.call_list) > 0:
					# Not the first call; check it is an increase (calls know
					# whether they are Palafico or not)
					previous_call = self.call_list[-1]
					if call <= previous_call:
						is_good_call = False
				elif (not self.is_round_palafico) and (value == 1):
					# First call.  If not Palafico then can't start on ones
					is_good_call = False


		self.display("Trying %s" % call.get_call_string())
		self.send(call.get_call_string())


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
