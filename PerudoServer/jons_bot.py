#!c:\python24\python.exe -u

#test

import perudo_client
import random
import common_utils
import math
import threading

debug_print = False

def fact(n):
	return reduce(lambda i,j: i*j, range(1,n+1), 1)

def prob(r,n,c):
	t = 0
	while r <= n:
		t += math.pow(c - 1, n - r) * ( fact(n) / ( fact(n - r) * fact(r) ) )
		r += 1
	return t / math.pow(c, n)

class MyCall(object):

	def __init__(self, call_str):
		split_str =  call_str.split("x")
		self.quantity = int(split_str[0])
		self.value = int(split_str[1])
		
	def get_quantity(self):
		return self.quantity
		
	def get_value(self):
		return self.value
		
	def get_value_quantity(self):
		return (self.value, self.quantity)
		
class MyOpeningCall(MyCall):
	def __init__(self, is_palafico):
		if is_palafico:
			super(MyOpeningCall, self).__init__("1x1")
		else:
			super(MyOpeningCall, self).__init__("1x2")
		
class JonBot(perudo_client.Client):

	def init_params(self):
		self.limit_adj_range = 0.1
		self.limit_min = 0.15
		self.limit = 0.4
		self.player_limit_mod = -0.03
		self.palafico_truth_chance = 0.66
		self.palafico_limit_mod = -0.2
		self.analysis_adj = 1.0
		
	def __init__(self, server, args):
		self.init_params()
		if args:
			arg_list = args.split(',')

			if arg_list[0]:
					self.limit_adj_range = float(arg_list[0])
			if arg_list[1]:
					self.limit_min = float(arg_list[1])
			if arg_list[2]:
					self.limit = float(arg_list[2])
			if arg_list[3]:
					self.player_limit_mod = float(arg_list[3])
			if arg_list[4]:
					self.palafico_truth_chance = float(arg_list[4])		
		super(JonBot, self).__init__(server)
		
	def reset_limit_adj(self):
		self.limit_adj = (random.random() - 0.5) * self.limit_adj_range

	def get_limit_min(self):
		return self.limit_min + self.get_limit_adj()

	def get_limit(self):
		return self.limit + self.get_limit_adj()

	def get_player_limit_mod(self):
		return self.player_limit_mod
		
	def get_palafico_limit_mod(self):
		return self.palafico_limit_mod

	def get_palafico_truth_chance(self):
		return self.palafico_truth_chance * (3.0 / self.get_num_players_remaining())
		
	def get_analysis_adj(self):
		return self.analysis_adj

	def start_game(self, other):
		self.reset_limit_adj()
		super(JonBot, self).start_game(other)

	def set_name(self):
		self.name = "JonBot(v2.1)"
		
	def analyse_call(self, value, call):
		if call.get_player_id() == self.player_id:
			return 0.0
		v = call.get_value()
		if v != value and v != 1:
			return 0.0
		return self.get_analysis_adj() * float(self.player_list[call.get_player_id()].get_num_dice()) * (math.sqrt(call.get_quantity()) / float(self.get_num_dice_in_play()))
	
	def analyse_previous(self, value):
		n = 0.0
		for call in self.call_list:
			n += self.analyse_call(value, call)
		return int(n)
			
	def get_chance(self, quantity, value, opening):
		call_info_log = ['%dx%d ' % (quantity, value)]
		
		unknown_dice = self.get_num_dice_in_play() - len(self.dice)
		chance_per_die = 6	
		num_i_need = quantity - self.dice.count(value)
		
		if (value != 1) and not self.is_round_palafico:
			num_i_need -= self.dice.count(1)
			chance_per_die /= 2
		
		call_info_log.append('out of %d I need %d' % (unknown_dice, num_i_need))
		
		if self.is_round_palafico and (self.get_palafico_truth_chance() > random.random()) and not opening:
			num_i_need -= 1
			unknown_dice -= 1
			#call_info_log.append(' -1 for palafico')
			
		if not self.is_round_palafico and not opening:
			n = self.analyse_previous(value)
			num_i_need -= n
			unknown_dice -= n
			call_info_log.append(' -%d for analysis' % n)
		
		if num_i_need <= 0:
			ret = 1.0
		else:
			#print '%d @ %d @ %f'%(num_i_need, unknown_dice, chance_per_die)
			ret = prob(num_i_need, unknown_dice, chance_per_die)
		
		call_info_log.append(', chance is %f' % ret)
		if debug_print:
			self.display("".join(call_info_log))
		
		return ret
		
	def get_bing(self, previous_call, opening = False):
		keep_value = self.is_round_palafico and len(self.dice) != 1
		ones_wild = not self.is_round_palafico
		return common_utils.get_bing(previous_call, ones_wild, keep_value)
		
	def get_can_call_dudo(self, previous_call):
		n = self.dice.count(previous_call.get_value())
		if not self.is_round_palafico and previous_call.get_value() != 1:
			n += self.dice.count(1)
		return previous_call.get_quantity() > n
		
	def get_opening_call(self):
		chances = []
		next_call = MyOpeningCall(self.is_round_palafico)
		while next_call.get_quantity() <= self.get_num_dice_in_play():
			if not self.is_call_impossible(next_call, True):
				if self.is_round_palafico or (next_call.get_value() != 1):
					chances.append((self.get_chance(next_call.get_quantity(), next_call.get_value(), True), next_call.get_quantity(), next_call.get_value()))
			next_call = MyCall(self.get_bing(next_call, True))	
		return self.get_call_from_chances(chances, True, False)
	
	def get_nonopening_call(self, previous_call):
		chances = []
		next_call = MyCall(self.get_bing(previous_call))
		while next_call.get_quantity() <= self.get_num_dice_in_play():
			if not self.is_call_impossible(next_call, True):
				chances.append((self.get_chance(next_call.get_quantity(), next_call.get_value(), False), next_call.get_quantity(), next_call.get_value()))
			next_call = MyCall(self.get_bing(next_call))	
		return self.get_call_from_chances(chances, False, self.get_can_call_dudo(previous_call))
			
	def get_call_from_chances(self, chances, opening, can_call_dudo):
		chances.sort()
		
		limit = self.get_limit() + ((self.get_num_players_remaining() - 2) * self.get_player_limit_mod())
		if self.is_round_palafico:
			limit += self.get_palafico_limit_mod()
		if limit < self.get_limit_min():
			limit = self.get_limit_min()
	
		if debug_print:
			self.display('Limit: %f (%s)' % (limit, str(can_call_dudo)))
		if can_call_dudo and ((len(chances) == 0) or (not opening and chances[-1][0] < limit)):
			return common_utils.Call(self.player_id, common_utils.DUDO)
		i = -1
		while 1:
			if chances[i][0] <= limit*3:
				choices = [chances[i]]
				i -= 1
				while i >= -len(chances) and chances[i][0] == choices[0][0]:
					choices.append(chances[i])
					i -= 1
				break
			if debug_print:
				self.display('Rejected %dx%d, %f>%f' % (chances[i][1],chances[i][2],chances[i][0],limit*3))
			i -= 1
		if debug_print:
			self.display("Choices: " + str(choices))
		r = random.randint(0,len(choices)-1)
		return common_utils.Call(self.player_id, "%dx%d" % (choices[r][1], choices[r][2]))

	def get_call(self, dummy_text):
		if len(self.call_list) == 0:
			call = self.get_opening_call()
		else:
			call_dudo = False
			previous_call = self.call_list[-1]
			if self.is_call_impossible(previous_call, True) or self.is_highest_call(previous_call): 
				call = common_utils.Call(self.player_id, common_utils.DUDO)
			else:
				call = self.get_nonopening_call(previous_call)		
		self.display("Trying %s" % call.get_call_string())
		#threading._sleep(random.randint(1, 3))
		self.send(call.get_call_string())
		
	def get_limit_adj(self):
		return self.limit_adj

if __name__ == "__main__":
	import optparse

	arguments = ['SERVER_NAME']
	parser = optparse.OptionParser(usage = "Usage: %%prog [options] %s" % ' '.join(arguments))
	(options, args) = parser.parse_args()

	if len(args) == 1:
		server = args[0]
		JonBot(server, None)
	elif len(args) == 2:
		server = args[0]
		JonBot(server, args[1])
	else:
		parser.print_help()
