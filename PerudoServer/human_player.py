#!c:\python24\python.exe -u

import perudo_client

if __name__ == "__main__":
	import optparse

	arguments = ['SERVER_NAME']
	parser = optparse.OptionParser(usage = "Usage: %%prog [options] %s" % ' '.join(arguments))
	parser.add_option("-s", "--silent", dest = "silent_mode", action = "store_true", help="Stop the terminal from beeping when prompt", default = False)
	
	(options, args) = parser.parse_args()

	if len(args) == 1:
		server = args[0]
		perudo_client.Client(server, options.silent_mode)
	else:
		parser.print_help()
