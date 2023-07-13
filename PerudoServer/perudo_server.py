#!c:\python24\python.exe -u

import random
import socket
import select
import datetime
import optparse

import common_utils
import common_network


class GameLog(object):

	def __init__(self):
		self.base_name = "%s_games.txt"
		self.file_name = self.base_name % datetime.datetime.now().strftime("%Y-%m-%d")
		self.file_handle = open(self.file_name, 'a')
		self.add(common_utils.get_delimiter_string(common_utils.START_GAME_DELIMITER))

	def add(self, text):
		self.file_handle.write(text + '\n')

	def __del__(self):
		self.add(common_utils.get_delimiter_string(common_utils.END_GAME_DELIMITER))
		

	

# ================================================================================
# Server classes
# ================================================================================

class Server(object):

	def __init__(self, max_num_players):
		self.start_game(max_num_players)

	def start_game(self, max_num_players):
		game = Game(max_num_players)
				

class NetworkGame(object):

	def __init__(self, min_num_players, max_num_players, waiting_for_game, timeout_for_players):
		self.timeout_for_players = timeout_for_players
		self.connection_manager = ConnectionManager()
		self.starting_players = self.get_players(min_num_players, max_num_players, waiting_for_game)

		self.log_file = GameLog()

		if len(self.starting_players) < 2:
			self.broadcast_text(common_network, INFO, "Not enought players, game cancelled")
			return 

		self.describe_game(common_utils.get_delimiter_string(common_utils.START_GAME_DELIMITER))
		self.start_game()
		self.call_list = []

		self.remaining_players = self.get_remaining_players()
		starting_player_id = random.randint(1, len(self.remaining_players)) -1
		is_round_palafico = False
		while len(self.remaining_players) > 1:
			self.describe_game(common_utils.get_delimiter_string(common_utils.START_ROUND_DELIMITER))
			self.describe_game("Starting round with: %s" % ', '.join([str(player) for player in self.remaining_players]))
			loser_player = self.start_round(self.remaining_players, starting_player_id, is_round_palafico)
			self.reveal_dice()
			self.describe_game("End of round, revealing dice")
			for player in self.remaining_players:
				self.describe_game("  Player %s had: %s" % (player, ' '.join([str(x) for x in player.get_dice_roll()])))

			self.announce_loser(loser_player)
			self.describe_game("%s loses a die" % loser_player)
			loser_player.lose_a_die()

			self.describe_game(common_utils.get_delimiter_string(common_utils.END_ROUND_DELIMITER))
			
			self.remaining_players = self.get_remaining_players()

			is_round_palafico = False
			# get next player to start, look if the loser is still playing else get next player by id
			if loser_player.get_num_dice() > 0:
				if loser_player.get_num_dice() == 1 and len(self.remaining_players) > 2:
					self.announce_palafico()
					self.describe_game("!!! Palafico !!!")
					is_round_palafico = True

				starting_player_id = loser_player.get_id()
			else:
				loser_player_id = loser_player.get_id()
				for i in range(loser_player_id, loser_player_id + len(self.starting_players)):
					player = self.starting_players[i % len(self.starting_players)]
					if player.get_num_dice() > 0:
						starting_player_id = player.get_id()
						break

		self.describe_game("End of game, %s wins the game" % self.remaining_players[0])
		self.describe_game(common_utils.get_delimiter_string(common_utils.END_GAME_DELIMITER))
		self.end_of_game(self.remaining_players[0])

	def describe_game(self, text):
		print text

	def get_remaining_players(self):
		players = []
		for player in self.starting_players.values():
			if player.get_num_dice() > 0:
				players.append(player)

		return players

	def is_call_true(self, call, is_round_palafico):
		ones_are_wild = not is_round_palafico
		dice_dict = {}

		# count the dice
		for player in self.remaining_players:
			player_dice = player.get_dice_roll()
			common_utils.get_dice_break_down(player_dice, dice_dict)

		(value, quantity) = call.get_value_quantity()

		if not ones_are_wild or value == 1:
			actual_quantity = dice_dict.get(value, 0)
		else:
			actual_quantity = dice_dict.get(value, 0) + dice_dict.get(1, 0)

		# Find the top call
		if ones_are_wild:
			top_calls = [common_utils.Call(0, "%dx%d" % (dice_dict.get(i,0) + dice_dict.get(1, 0), i)) for i in range(2,7)]
			top_calls.append(common_utils.Call(0, "%dx1" % dice_dict.get(1, 0)))
		else:
			top_calls = [common_utils.PalaficoCall(0, "%dx%d" % (dice_dict.get(i,0), i)) for i in range(1,7)]

		top_calls.sort()
		top_calls.reverse()

		message = "Final call was %sx%s, actual count %sx%s, top calls: %s" % (quantity, value, actual_quantity, value, ', '.join([call.get_call_string() for call in top_calls if call.get_quantity() != 0]))
		self.describe_game(message)
		self.send_info(message)

		return actual_quantity >= quantity


	def start_round(self, players, starting_player_id, is_round_palafico):
		for player in self.starting_players.values():
			self.set_dice_roll(player)

		someone_called_dudo = False
		next_player_id = starting_player_id
		current_player_index = None
		current_player = None
		current_call = None
		max_num_tries = 3
		while not someone_called_dudo:
			previous_player = current_player
			current_player_index = self.get_player_index_in_list(next_player_id, players)
			current_player = players[current_player_index]
			previous_call = current_call
			current_call =  self.get_call(current_player)
			if is_round_palafico:
				current_call.__class__ = common_utils.PalaficoCall

# 			self.log_file.add(self.get_msg(INFO, "%s:%s > %s:%s = %s" % (current_call.__class__, current_call, previous_call.__class__, previous_call, (current_call > previous_call))))

			is_call_acceptable = False
			num_tries = max_num_tries
			while not is_call_acceptable:
				if current_call is None:
					self.player_has_deconnected(current_player)
					return current_player
					
				if num_tries == 0:
					self.send_info("Player %s has failed %d times to produce a valid call. Therefore he loses this round." % (current_player, max_num_tries))
					self.describe_game("%s has failed %d times to produce a valid call. Therefore he loses this round." % (current_player, max_num_tries))
					return current_player

				if (current_call <= previous_call):
					self.send_text(common_network.TOO_LOW_CALL, "", [current_player])
					self.log_file.add(self.get_msg(common_network.TOO_LOW_CALL, str(current_call)))
				elif ((previous_call is None ) and (current_call.is_dudo())):
					self.send_text(common_network.TOO_SOON_FOR_DUDO, "", [current_player])
				elif ((not is_round_palafico) and (previous_call is None) and (current_call.get_value() == 1)):
					self.send_text_to_player("Can't start on ones.", current_player)
					self.send_text(common_network.INVALID_CALL, "", [current_player])
					self.log_file.add(self.get_msg(common_network.INVALID_CALL, str(current_call)))
				elif (is_round_palafico and (not current_call.is_dudo()) and previous_call and (current_player.get_num_dice() > 1) and (current_call.get_value() != previous_call.get_value())):
					self.send_text_to_player("Invalid Palafico call, must be %ss" % previous_call.get_value(), current_player)
					self.send_text(common_network.INVALID_CALL, "", [current_player])
					self.log_file.add(self.get_msg(common_network.INVALID_CALL, str(current_call)))
				else:
					is_call_acceptable = True

				if not is_call_acceptable:
					current_call =  self.get_call(current_player)
					if is_round_palafico:
						current_call.__class__ = common_utils.PalaficoCall
					num_tries = num_tries - 1
				

			self.describe_game("%s: %s" %(current_player,  current_call.get_call_string()))
			self.broadcast_call(current_call)
			someone_called_dudo = current_call.is_dudo()
			self.call_list.append(current_call)

			next_player_id = players[(current_player_index + 1) % len(players)].get_id()

		# Check the last call
		loser_player = None
		if self.is_call_true(previous_call, is_round_palafico):
			loser_player = current_player
		else:
			loser_player = previous_player

		return loser_player

	def player_has_deconnected(self, player):
		player.has_left_the_game()
		self.send_info("Player %s has left the server. Therefore he loses this round and quits the game" % player)
		self.describe_game("Player %s has left the server. Therefore he loses this round and quits the game" % player)
		

	def get_player_index_in_list(self, player_id, players):
		for i in range(len(players)):
			if players[i].get_id() == player_id:
				return i
		raise("Could not find player id %d in %s" %(player_id, players))

	# GAME CALLS
	# =============
	
	def set_dice_roll(self, player):
		dice_roll = [random.randint(1, 6) for i in range(player.get_num_dice())]
		player.set_dice_roll(dice_roll)
		self.send_text(common_network.SET_DICE_ROLL, ','.join([str(x) for x in dice_roll]), [player])
		
	def announce_loser(self, player):
		self.broadcast_text(common_network.ANNOUNCE_LOSER, str(player.get_id()))

	def announce_palafico(self):
		self.broadcast_text(common_network.PALAFICO, '')

	def send_text_to_player(self, text, player):
		self.send_text(common_network.INFO, text, [player])
		
	def send_info(self, text):
		self.broadcast_text(common_network.INFO, text)
		
	def broadcast_call(self, call):
		self.broadcast_text(common_network.ANNOUNCE_CALL, "%d,%s" % (call.get_player_id(), call.get_call_string()))

	def reveal_dice(self):
		dice_per_player = {}
		for player in self.remaining_players:
			dice_per_player[player.get_id()] = player.get_dice_roll()
		
		self.broadcast_text(common_network.REVEAL_DICE, str(dice_per_player))
			
	def get_call(self, player):
		answer = self.prompt(player, common_network.GET_CALL, "")
		if answer is None:
			return None
		call = common_utils.Call(player.get_id(), answer)
		
		while not call.is_valid():
			self.send_text(common_network.INVALID_CALL, "", [player])
			answer = self.prompt(player, common_network.GET_CALL, "")
			if answer is None:
				return None
			call = common_utils.Call(player.get_id(), answer)
			
		return call

	def start_game(self):
		simple_player_dict = {}
		players = self.starting_players.values()
		for player in players:
			simple_player_dict[player.get_id()] = player.get_name()
		self.broadcast_text(common_network.START_GAME, str(simple_player_dict))

	def end_of_game(self, winner):
		self.broadcast_text(common_network.END_OF_GAME, str(winner.get_id()))
		
	def get_players(self, min_num_players, max_num_players, waiting_time):
		client_socket_list = self.connection_manager.get_client_sockets(max_num_players, waiting_time)

		player_list = {}

		random.shuffle(client_socket_list)

		for (i, client_socket) in enumerate(client_socket_list):
			self.send_text_to_sockets(common_network.SET_PLAYER_ID, str(i), [client_socket])
			name = self.prompt_socket(client_socket, common_network.GET_NAME, "")
			if name:
				player_list[i] = common_network.NetworkPlayer(i, name, client_socket)

		return player_list

					
	# GENERIC CALLS
	# =============

	# make the msg
	def get_msg(self, msg_type, text):
		return msg_type + common_network.DELIMITER + text
	
	# send text to everyone
	def broadcast_text(self, msg_type, text):
		self.log_file.add(self.get_msg(msg_type, text))
		self.send_text(msg_type, text, self.starting_players.values())

	# send text to a limited list of sockets
	def send_text_to_sockets(self, msg_type, text, sockets):
		self.connection_manager.send_text(self.get_msg(msg_type, text), sockets)

	# send text to a limited list of players
	def send_text(self, msg_type, text, players):
		self.send_text_to_sockets(msg_type, text, [x.get_socket() for x in players if x.get_socket()])

	# ask something to one socket
	def prompt_socket(self, a_socket, msg_type, prompt_message):
		try:
			return self.connection_manager.prompt(a_socket, self.get_msg(msg_type, prompt_message), self.timeout_for_players)
		except socket.error:
			return None

	# ask something to one player
	def prompt(self, player, msg_type, prompt_message):
		return self.prompt_socket(player.get_socket(), msg_type, prompt_message)




class ConnectionManager(object):
	def __init__(self):
		self.client_socket_list = []
		self.server_socket = None
		self.create_server_socket()


	def create_server_socket(self):
		address = (socket.gethostname(), common_network.PORT)
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_socket.bind(address)
		self.server_socket.listen(4)
		self.server_socket.settimeout(0)
		
	
	def get_client_sockets(self, max_num_players, timeout):
		self.client_socket_list = []
		start_time = datetime.datetime.now()
		time_elapsed = 0
		while ((time_elapsed < timeout) and (len(self.client_socket_list) < max_num_players)):
			if time_elapsed % 5 == 0:
				print "%d seconds to wait before starting the game." % (timeout - time_elapsed)
			ready_to_read, ready_to_write, in_error = select.select([self.server_socket], [],[], 1)
			for readable_socket in ready_to_read:
				if readable_socket == self.server_socket:
					clientsock, addr = self.server_socket.accept()
					hostname = socket.gethostbyaddr(addr[0])[0].split('.')[0]
					print 'Client %s (%s) is connected on socket: %s' % (hostname, addr[0], clientsock.getsockname())
					self.client_socket_list.append(clientsock)
				else:
					print "Error: wait_for_players, another socket was readable. Shouldn't happen."
			time_elapsed = self.timedelta_to_second(datetime.datetime.now() - start_time)

		return self.client_socket_list


	def prompt(self, client_socket, prompt_message, timeout):
		# send the prompt
		#use a select here, todo
		self.send_text(prompt_message, [client_socket])

		# get answer
		start_time = datetime.datetime.now()
		time_diff = 0
		answer = None
		while (time_diff < timeout and answer is None):
			ready_to_read, ready_to_write, in_error = select.select([client_socket], [],[], 1)
			for readable_socket in ready_to_read:
				if readable_socket == client_socket:
					answer, sender = readable_socket.recvfrom(common_network.BUFSIZ)
					msg_len = int(answer[:common_network.MSG_LEN_TAG_LEN])
					answer = answer[common_network.MSG_LEN_TAG_LEN:common_network.MSG_LEN_TAG_LEN + msg_len]
				else:
					print "Error: prompt, another socket was readable. Shouldn't happen."
			time_diff = self.timedelta_to_second(datetime.datetime.now() - start_time)

		return answer
		
	def send_text(self, text, client_sockets):
		# use a select here, todo
		for client_socket in client_sockets:
			# add the length of the text in a fixed length field
			if len(str(len(text))) > common_network.MSG_LEN_TAG_LEN:
				raise("Can't send message, because its lenght is more than %d characters long: %s" % (common_network.MSG_LEN_TAG_LEN, text))
			
			# send the prompt
			checky_string = "%%%ds%%s" % common_network.MSG_LEN_TAG_LEN
			client_socket.send(checky_string % (len(text), text))


	def timedelta_to_second(self, td):
		return (td.days * 60 * 60 * 24) + td.seconds


if __name__ == "__main__":

	parser = optparse.OptionParser(usage = "Usage: %prog [options]")

	parser.add_option("-m", "--min_num_players", dest = "min_num_players", action = "store", type = "int", help="Set the minimum number of players", default = 2)
	parser.add_option("-n", "--max_num_players", dest = "max_num_players", action = "store", type = "int", help="Set the maximum number of players", default = 2)
	parser.add_option("-w", "--waiting_for_game", dest = "waiting_for_game", action = "store", type = "int", help="How long to wait before starting the game", default = 60*5)
	parser.add_option("-t", "--timeout_for_players", dest = "timeout_for_players", action = "store", type = "int", help="How long to wait for players to answer", default = 60*60)
	
	(options, args) = parser.parse_args()

	NetworkGame(options.min_num_players, options.max_num_players, options.waiting_for_game, options.timeout_for_players)

# TO DO
# Allow client to join opened server, make the server write to a file whenever a game is being played
# add version number to client and server for checks
# use a select when prompting clients, look for todo
# Remove too_soon_for_dudo and too_low_call from api, simply make the call invalid and send an info msg
# deal with unresponsive clients
