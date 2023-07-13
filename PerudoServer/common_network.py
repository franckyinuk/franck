# Sockets const
PORT = 22222
BUFSIZ = 1024
MSG_LEN_TAG_LEN = 10

# messages type
GET_NAME = 'GET_NAME'
SET_PLAYER_ID = 'SET_PLAYER_ID'
GET_CALL = 'GET_CALL'
INVALID_CALL = 'INVALID_CALL'
TOO_LOW_CALL = 'TOO_LOW_CALL'
TOO_SOON_FOR_DUDO = 'TOO_SOON_FOR_DUDO'
INFO = 'INFO'
ANNOUNCE_LOSER = 'ANNOUNCE_LOSER'
ANNOUNCE_CALL = 'ANNOUNCE_CALL'
SET_DICE_ROLL = 'SET_DICE_ROLL'
REVEAL_DICE = 'REVEAL_DICE'
START_GAME = 'START_GAME'
END_OF_GAME = 'END_OF_GAME'
PALAFICO = "PALAFICO"

MESSAGE_TYPES = [GET_NAME, SET_PLAYER_ID, GET_CALL, INVALID_CALL, TOO_LOW_CALL, INFO, TOO_SOON_FOR_DUDO,
				 ANNOUNCE_LOSER, ANNOUNCE_CALL, SET_DICE_ROLL, REVEAL_DICE, START_GAME, END_OF_GAME, PALAFICO]
MESSAGE_TYPES_EXPECTING_ANSWER = [GET_NAME, GET_CALL]

DELIMITER = '::'


class NetworkPlayer(object):

	def __init__(self, id, name, socket):
		self.player_id = id
		self.name = name
		self.socket = socket
		self.dice_roll = []
		self.num_dice = 5

	def __str__(self):
		return "%s (%d)" % (self.name, self.player_id)
	
	def get_id(self):
		return self.player_id

	def get_name(self):
		return self.name

	def get_socket(self):
		return self.socket

	def lose_a_die(self):
		self.num_dice = self.num_dice - 1
		
	def has_left_the_game(self):
		self.num_dice = 0
		self.socket = None
		
	def win_a_die(self):
		self.num_dice = self.num_dice + 1
		
	def get_num_dice(self):
		return self.num_dice

	def set_dice_roll(self, dice):
		dice.sort()
		self.dice_roll = dice

	def get_dice_roll(self):
		return self.dice_roll



