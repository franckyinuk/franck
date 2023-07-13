#!/bin/python

import os
import threading
import socket
import re
import sys

class ServerThread(threading.Thread):
	def __init__(self, num_players):
		super(ServerThread,self).__init__()
		self.num_players = num_players
		self.start()
	def run(self):
		p = os.popen('python perudo_server.py -n %d' % self.num_players)
		self.output = p.read()

class PlayerThread(threading.Thread):
	def __init__(self, player):
		super(PlayerThread,self).__init__()
		self.player = player
		self.show_output = False
	def run(self):
		args = ""
		if self.player[1]:
			args = self.player[1]
		botname = self.player[0]
		if botname[0] == '*':
			botname = botname[1:]
			self.show_output = True
		if (len(botname) > 3) and (botname[-3:] == '.py'):
			botname = botname[:-3]
		p = os.popen('python %s.py %s %s' % (botname, socket.gethostname(), args))
		self.output = p.read()
		
def play(players):
	server_thread = ServerThread(len(players))
	threading._sleep(0.1)
	player_threads = []
	for player in players:
		player_threads.append(PlayerThread(player))
	for player_thread in player_threads:
		player_thread.start()
	for player_thread in player_threads:
		player_thread.join()
	server_thread.join()
	i =0
	
	for player_thread in player_threads:
		if re.search('You win',player_thread.output):
			w = i
		if player_thread.show_output:
			print '[Start of output for %s]' % str(player_thread.player)
			print player_thread.output	
			print '[End of output for %s]' % str(player_thread.player)
		i += 1
	return w
	
def print_results(results, players):
	print "\n%3s %-40s %4s" % ("Num", "Name", "Wins")
	print "--- ---------------------------------------- ----"
	for result in results:
		print "%3d %-40s %4d" % (result[1],str(players[result[1]]),result[0])

def play_games(players, num_games, on_results):
	winners = {}
	for i in range(0,num_games):
		winner = play(players)
		print "Winner: %d %s" % (winner,str(players[winner]))
		if winner in winners:
			winners[winner] += 1
		else:
			winners[winner] = 1
	results = []
	for winner,wins in winners.iteritems():
		results.append((wins,winner))
	results.sort()
	on_results(results, players)

def usage_and_exit():
	print "python %s <num_games> [*]<bot1> [*]<bot2> [*][bot3] ..." % sys.argv[0]
	print "\tAppend the bot name with a * to show output"
	exit()
	
def main():
	if len(sys.argv) < 4:
		usage_and_exit()
	players = []
	for i in range(2, len(sys.argv)):
		botname = sys.argv[i]
		players.append((botname,None))
	play_games(players, int(sys.argv[1]), print_results)	

if __name__ == '__main__':
	main()