

import urllib2
import re
import datetime
import threading
import time


store_lock = None
output_lock = None
output_file = None
result_list = []
line_num = 2

web_to_reuters_symbol = {
	"ABC": "ABCA",
	"ABM": "ALBH",
	"ACS": "AICS",
	"ADM": "ADML",
	"APH": "ALAPH",
	"ATG": "ADVG",
	"BA":  "BAES",
	"BBY": "BALF",
	"CBG": "CBRO",
	"DPH": "DECP",
	"GNS": "GENS",
	"HAS": "HAYS",
	"HSP": "HRVG",
	"IMD": "IMED",
	"IND": "ID2A",
	"MRO": "MRS",
	"MUR": "MURG",
	"STT": "STTU",
	"TRE": "TREM",
	}

class DataCollector(threading.Thread):
	def __init__(self, symbol, index):
		self.symbol = symbol + ".L"
		self.index = index
		self.success = None
		self.data = {}
		self.errors = []
		threading.Thread.__init__(self)
		self.start()

	def collect(self):
		(ric, country_code) = self.symbol.rsplit(".", 1)
		url = "http://www.marketwatch.com/investing/stock/%s?countryCode=UK" %ric

		request = urllib2.Request(url, None, {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7"})
		self.success = False

		proxies = {'http': 'franck.mesirard:c696t6k99,,15@MHSPROXY.TFCORP.TFN.COM:80'}
		proxy_handler = urllib2.ProxyHandler(proxies)
		opener = urllib2.build_opener(proxy_handler)

		server_response = "HTTP 500"
		num_tries = 4
		html = ""
		while server_response.find("500") != -1 and num_tries > 0:
			num_tries -= 1
			try:
				page = opener.open(request)
				html = page.read()
				symbol_match = re.search(r'\<title\>\s*\n\s*(?P<symbol>\b\w+)\.? Stock Quote', html)

				if not symbol_match:
					#print "%s 's page returned some garbage"  % self.symbol
					server_response = "500"
				else:
					server_response = "OK"

			except Exception, e:
				server_response = str(e)
				if server_response.find("500") == -1:
					self.errors.append("Failed to get page for %s, url %s\n%s" %(ric, url, e))
					# remove spare dot
					new_symbol = self.symbol.replace("..", ".")
					if new_symbol != self.symbol:
						self.symbol = new_symbol
						self.collect()	
						return

		dividend_match = re.search(r'Dividend</p>\s*\n\s*<p class="data lastcolumn">(?P<dividend>[0-9.N/A]+)</p>', html)
		ex_date_match = re.search(r'Ex dividend date</p>\s*\n\s*<p class="data lastcolumn">(?P<ex_date>[0-9N/A]+)</p>', html)
		price_match = re.search(r'<p class="data bgLast">(?P<price>[0-9.,]+)</p>', html)

		if html and symbol_match and dividend_match and ex_date_match:
			if ric.lower() != str(symbol_match.group('symbol')).lower():
				self.errors.append("Error, for %s found RIC %s instead" %(self.symbol, symbol_match.group('symbol')))
				return
			
			self.data['dividend'] = dividend_match.group('dividend')
			if ex_date_match.group('ex_date') != "N/A":
				ex_date_found = [int(x) for x in ex_date_match.group('ex_date').split('/')]
				ex_date_found = datetime.date(ex_date_found[2]+ 2000, ex_date_found[0], ex_date_found[1])
			else:
				ex_date_found = datetime.date(1900, 1, 1)

			if price_match and self.data['dividend'] != "N/A":
				self.data['initial %'] = float(self.data['dividend'])/float(price_match.group('price').replace(',', ''))*100
			else:
				self.data['initial %'] = "??"

			# to cope with discrepencies between website and reuters names
			new_symbol = web_to_reuters_symbol.get(ric, ric) + ".L"
			self.data['ex_date'] = ex_date_found
			self.data['trader_fields'] = '=RStream({"%s"},{"DSPLY_NAME";"TRDPRC_1"},{"FEED";"REUTERS"})' % (new_symbol)
			self.data['percentage'] = "=$E%(index)d/$C%(index)d * 100"
			self.data['url'] = "=HYPERLINK(\"%s\",\"%s\")" %(url, new_symbol)
			self.success = True

		else:
			self.errors.append("Error, the page returned for %s is not valid." % (self.symbol))
			#file = open("%s.html" % self.symbol, 'w')
			#file.write(html)
			#file.close()

	def run(self):
		self.collect()
		if self.success:
			# string format to use "%s\t%s\t\t%s\t%s\t%s\n"
			store_results([self.data['url'], self.data['trader_fields'], self.data['ex_date'], self.data['dividend'], self.data['percentage'], self.data['initial %']])
			#safe_print("Successfuly collected data for %s" % self.symbol)
		else:
			safe_print('; '.join(self.errors))

def store_results(text):
	global store_lock
	if store_lock is None:
		store_lock = threading.Lock()
	store_lock.acquire()
	global result_list
	result_list.append(text)
	store_lock.release()

def safe_print(text):
	global output_lock
	if output_lock is None:
		output_lock = threading.Lock()
	output_lock.acquire()
	print text
	output_lock.release()


def filter_result(input):
	new_result = []
	for line in input:
		if line[2] <= datetime.datetime.now().date() or line[3] == "N/A":
			pass
		else:
			new_result.append(line)

	return new_result

def result_to_text(input):
	new_result = []
	index = 2
	new_result.append("\t".join(['Symbol', 'Name', 'Price', 'Ex-Date', 'Dividend', 'Div %', "Initial Div %"]) + "\n")
	for line in input:
		text = ("%s\t%s\t\t%s\t%s\t%s\t%s\n" %(line[0], line[1], line[2], line[3], line[4], line[5]))
		new_result.append(text % {"index":index})
		index += 1
	return new_result

def sort_result(input):
	new_result = [(line[-1], line) for line in input]
	new_result.sort()
	new_result.reverse()
	new_result = [item[1] for item in new_result]
	return new_result
	
def read_write_symbol_data(input):
	input_handle = open(input, 'r')

	index = 2

	num_processors = 2
	try:
		import mutliprocessing
		num_processors = mutliprocessing.cpu_count()
		print "Found number of processors: ", num_processors
	except ImportError, NotImplementedError:
		pass
	
	for line in input_handle:
		if line.startswith('#'):
			continue
		while threading.activeCount() > 1 + 10*num_processors:
			time.sleep(1)
		symbol = line[:-1]
		DataCollector(symbol, index)
		index += 1

	# wait for everyone to finish
	while threading.activeCount() > 1:
		time.sleep(1)

	# write to file
	input_handle.close()

	global result_list
	filtered_result = filter_result(result_list)
	sorted_result = sort_result(filtered_result)
	result_in_text = result_to_text(sorted_result)
	
	file = open("dividends_%s.txt" % datetime.datetime.now().date().strftime("%Y%m%d"), 'w')
	file.write(''.join(result_in_text))
	file.close()

if __name__ == "__main__":
	# symbols are avaialbe at http://www.moneyextra.com/stocks/ftse350
	read_write_symbol_data("symbols.txt")


