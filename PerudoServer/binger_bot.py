#!c:\python24\python.exe -u

import perudo_client
import random
import common_utils


class BingerBot(perudo_client.Client):
	def set_name(self):
		self.name = "Binger Bot"

	def get_call(self, dummy_text):
		# Automatically call, if the previous call is too high or is the highest call
		call_dudo = False
		if (len(self.call_list) > 0 and (self.is_call_impossible(self.call_list[-1], True) or self.is_highest_call(self.call_list[-1]))):
			call_dudo = True
		
		if call_dudo and len(self.call_list) > 0:
			call = common_utils.Call(self.player_id, common_utils.DUDO)
		else:
			previous_call = None
			if len(self.call_list) > 0:
				previous_call = self.call_list[-1]

			if self.is_round_palafico and len(self.dice) > 1:
				must_keep_value = True
			else:
				must_keep_value = False

			call = common_utils.Call(self.player_id, common_utils.get_bing(previous_call, not self.is_round_palafico, must_keep_value))

		self.display("Trying %s" % call.get_call_string())
		self.send(call.get_call_string())


if __name__ == "__main__":
	import optparse

	arguments = ['SERVER_NAME']
	parser = optparse.OptionParser(usage = "Usage: %%prog [options] %s" % ' '.join(arguments))
	(options, args) = parser.parse_args()

	if len(args) == 1:
		server = args[0]
		BingerBot(server)
	else:
		parser.print_help()
