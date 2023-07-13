# play music on the PC internal speaker
# tested with Python24 on a Windows XP computer vegaseat 15aug2005

# the notes
P = 0 # pause
C = 1
CS = 2 # C sharp
D = 3
DS = 4
E = 5
F = 6
FS = 7
G = 8
GS = 9
A = 10
AS = 11
B = 12
 
EN = 100 # eighth note
QN = 200 # quarter note
HN = 400 # half note
FN = 800 # full note
 
def play(octave, note, duration):
	try:
		import winsound
	except ImportError:
		return

	import time
	
	"""play note (C=1 to B=12), in octave (1-8), and duration (msec)"""
	if note == 0: # a pause
		time.sleep(duration/1000)
		return
	
	frequency = 32.7032 # C1
	for k in range(0, octave): # compute C in given octave
		frequency *= 2
 
	for k in range(0, note): # compute frequency of given note
		frequency *= 1.059463094 # 1.059463094 = 12th root of 2
	time.sleep(0.010) # delay between keys
 
	winsound.Beep(int(frequency), duration)
 
def bigben():
	play(4,E,HN)
	play(4,C,HN)
	play(4,D,HN)
	play(3,G,HN+QN);
	play(3,P,QN)
	play(3,G,HN)
	play(4,D,HN)
	play(4,E,HN)
	play(4,C,HN+QN)

def beethoven():
	play(4, E, HN)
	play(4, E, HN)
	play(4, E, HN)
	play(4, C, HN + QN)

