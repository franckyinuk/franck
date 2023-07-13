# ================================================================================
# Client
# ================================================================================

import socket
import common_network
import common_utils

class Client(object):	
	def __init__(self, host = socket.gethostname(), silent_mode = False):
		self.host = host
		self.port = common_network.PORT
		self.client_socket = None
		self.name = None
		self.dice = None
		self.call_list = []
		self.player_list = []
		self.player_id = None
		self.is_round_palafico = False
		self.silent_mode = silent_mode

		self.create_server_socket(host, self.port)

		self.actions = {
			common_network.GET_NAME: self.get_name,
			common_network.SET_PLAYER_ID: self.set_player_id,
			common_network.SET_DICE_ROLL: self.set_dice_roll,
			common_network.GET_CALL: self.get_call,
			common_network.ANNOUNCE_CALL: self.announce_call,
			common_network.INVALID_CALL: self.invalid_call,
			common_network.REVEAL_DICE: self.reveal_dice,
			common_network.ANNOUNCE_LOSER: self.announce_loser,
			common_network.TOO_LOW_CALL: self.too_low_call,
			common_network.TOO_SOON_FOR_DUDO: self.too_soon_for_dudo,
			common_network.INFO: self.info,
			common_network.START_GAME: self.start_game,
			common_network.END_OF_GAME: self.end_of_game,
			common_network.PALAFICO : self.palafico,
			}

		self.set_name()
		self.go()

	def __del__(self):
		self.client_socket.close()


	def create_server_socket(self, host, port):
		address = (host, port)
		
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect(address)

	def listen_on_socket(self):
		return  self.client_socket.recv(common_network.BUFSIZ)

	def go(self):
		while 1:
			data = self.listen_on_socket()
		
			if not data:
				break
			#print "data: " + data

			# there could be more than on message in the socket
			# so we have to check the length of each
			while len(data):
				msg_len = int(data[:common_network.MSG_LEN_TAG_LEN])
				msg_data = data[common_network.MSG_LEN_TAG_LEN:common_network.MSG_LEN_TAG_LEN + msg_len]
				data = data[common_network.MSG_LEN_TAG_LEN + msg_len:]

				#print "msg:data: " + msg_data
				
				message_type, content = msg_data.split(common_network.DELIMITER, 1)

				action = self.actions.get(message_type, self.default_function)

				action(content)
			
				if message_type == common_network.END_OF_GAME:
					return

	def get_num_dice_in_play(self):
		num = 0
		for player in self.player_list:
			num += player.get_num_dice()
		return num

	def get_num_players_remaining(self):
		return len([player for player in self.player_list if player.get_num_dice() > 0])
	
	def is_call_impossible(self, call, count_my_dice):
		ones_are_wild = not self.is_round_palafico
		(value, quantity) = call.get_value_quantity()

		dice_per_number = common_utils.get_dice_break_down(self.dice, {})

		if not count_my_dice:
			num_of_my_dice_which_dont_count = 0
		elif not ones_are_wild or value == 1:
			num_of_my_dice_which_dont_count = len(self.dice) - dice_per_number.get(value, 0)
		else:
			num_of_my_dice_which_dont_count = len(self.dice) - dice_per_number.get(value, 0) - dice_per_number.get(1, 0)

		res = quantity > (self.get_num_dice_in_play() - num_of_my_dice_which_dont_count)
		return res
		
	def is_highest_call(self, call):
		(value, quantity) = call.get_value_quantity()
		num_dice_in_play = self.get_num_dice_in_play()
		ones_are_wild = not self.is_round_palafico

		if not ones_are_wild or value == 1:
			return (quantity == num_dice_in_play) and (value == 6)
		else:
			if num_dice_in_play % 2 == 0:
				return (quantity == num_dice_in_play/2) and value == 1
			else:
				return (quantity == num_dice_in_play) and (value == 6)
		
	def set_name(self):
		self.name = self.prompt("What is your name?")

	# Useful methods
	#===============

	def display(self, text):
		print text

	def prompt(self, text):
		return raw_input(text + ' ')

	def send(self, text):
		# send the prompt
		cheeky_string = "%%%ds%%s" % common_network.MSG_LEN_TAG_LEN
		msg_text = cheeky_string % (len(text), text)
		#print "sending: " + msg_text
		self.client_socket.send(msg_text)

	def get_player(self, id):
		for player in self.player_list:
			if id == player.get_id():
				return player
		raise("Could find player %s in the list" % id)

	# API methods
	#============
	def default_function(self):
		self.display("Unknown function.")
	
	def get_name(self, dummy_text):
		self.send(self.name)

	def set_player_id(self, id):
		self.player_id = int(id)

	def set_dice_roll(self, dice_role):
		self.display(common_utils.get_delimiter_string(common_utils.START_ROUND_DELIMITER))
		num_dice_remaining = self.get_num_dice_in_play()
		self.display("%s dice remaining" % num_dice_remaining)
		if dice_role:
			self.dice = [int(x) for x in dice_role.split(',')]
			self.display("New roll: %s" % ' '.join([str(x) for x in self.dice]))
		
	def get_call(self, dummy_text):
		if not self.silent_mode:
			common_utils.beep(2)
		call_string = self.prompt("Your turn:")
		call = common_utils.Call(self.player_id, call_string)
		self.send(call.get_call_string())

	def announce_call(self, text):
		player_id, call = text.split(',')
		player_id = int(player_id)
		announced_call = common_utils.Call(player_id, call)
		self.call_list.append(announced_call)
		# Announce players' own calls, so the full call tree can easily be followed on screen
		self.display("%-32s %4s%s" % ("%s says:" % self.get_player(player_id), announced_call.get_call_string(), common_utils.get_call_name_appendage(self.call_list)))
		
	def invalid_call(self, text):
		self.display("Your call was rejected because it was invalid, i.e. wrong format or not used properly.")
		self.display("Try something like '3x5', '2x1' or  'dudo'")

	def reveal_dice(self, text):
		self.is_round_palafico = False
		players_dice = eval(text)
		self.display("Players dice:")
		for player_id in players_dice.keys():
			self.display("%-32s %s" % ("  %s had:" % self.get_player(player_id), ' '.join([str(x) for x in players_dice[player_id]])))
		self.call_list = []

	def announce_loser(self, id_string):
		loser_id = int(id_string)
		losing_player = self.get_player(loser_id)
		losing_player.lose_a_die()
		if loser_id == self.player_id:
			if losing_player.get_num_dice() != 0:
				self.display("You lose a die")
			else:
				self.display("You are out of the game")
		else:
			if losing_player.get_num_dice() != 0:
				self.display("%s loses a die" % losing_player)
			else:
				self.display("%s is out of the game" % losing_player)
		self.display(common_utils.get_delimiter_string(common_utils.END_ROUND_DELIMITER))

	def too_low_call(self, dummy_text):
		self.display("Your call is too low.")

	def too_soon_for_dudo(self, dummy_text):
		self.display("It is too soon to call DUDO.")

	def info(self, text):
		self.display("Info: %s" % text)

	def start_game(self, player_list_string):
		players = eval(player_list_string)
		for player_id in players:
			self.player_list.append(common_network.NetworkPlayer(player_id, players[player_id], None))
		self.display(common_utils.get_delimiter_string(common_utils.START_GAME_DELIMITER))

		self.display("Playing with %s" % [x.get_name() for x in self.player_list])

	def end_of_game(self, winner_id_string):
		winner_id = int(winner_id_string)
		if winner_id == self.player_id:
			self.display("You win the game.")
		else:
			self.display("%s wins the game." % self.player_list[winner_id])
		self.display(common_utils.get_delimiter_string(common_utils.END_GAME_DELIMITER))

	def palafico(self, dummy_text):
		self.display("!!!   Palafico  !!!")
		self.is_round_palafico = True;
