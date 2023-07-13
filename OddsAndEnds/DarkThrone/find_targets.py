

import urllib2
import sys
import re
import datetime
import threading
import time
import optparse
import cookielib
import ClientForm
import os.path


output_lock = None
store_lock = None
result_list = []

class DarkThroneLogin:
	def __init__(self, email, password, proxies):
		self.email = email
		self.password = password
		self.url = 'http://www.darkthrone.com'

		self.level = None
		self.offence_soldier = None
		self.num_pages = None
		self.pseudo = None

		cookiejar = cookielib.LWPCookieJar()
		cookiejar = urllib2.HTTPCookieProcessor(cookiejar)
		debugger = urllib2.HTTPHandler(debuglevel=1)

		proxy_handler = urllib2.ProxyHandler(proxies)

		opener = urllib2.build_opener(cookiejar, proxy_handler)
		urllib2.install_opener(opener)

		self.login()
		self.collect_info()

	def login(self):
		#collect form
		response = urllib2.urlopen(self.url)
		forms = ClientForm.ParseResponse(response, backwards_compat=False)

		form = forms[0]
		try:
			form['user[email]'] = self.email
			form['user[password]'] = self.password
		except Exception, e:
			print 'The following error occured: \n"%s"' % e
			print
			print 'A good idea is to open a browser and see if you can log in from there.'
			print 'URL:', self.url
			exit()

		# login
		self.page = urllib2.urlopen(form.click()).read()

	def collect_info(self):
		match = re.search("<strong>(.*)</strong> is a", self.page)
		self.pseudo = match.group(1)

		html = urllib2.urlopen("http://www.darkthrone.com/armory").read()
		match = re.search("Level: (\d+)<br />", html)
		self.level = int(match.group(1))
		
		match = re.search("Offensive Units:</dt><dd>([\d,]+)</dd>", html)
		self.offence_soldier = int(match.group(1).replace(',', ''))
		
		html = urllib2.urlopen("http://www.darkthrone.com/userlist/attack").read()
		match = re.search("Viewing page \d+ of (\d+)", html)
		self.num_pages = int(match.group(1))

		print "Logged in"
	
class DarkThroneDataCollector(threading.Thread):
	def __init__(self, url):
		self.url = url
		self.success = None
		self.data = []
		#self.errors = []
		threading.Thread.__init__(self)
		self.start()

	def collect(self):
		self.success = False
		html = urllib2.urlopen(self.url).read()
		""" 
                 <tr>
        <td><!--14999-->14,999</td>
        <td class="align_left"><!--Killik101--><a href="/viewprofile/index/2025968" id="character_name_2025968">Killik101</a></td>

        <td><!--2720751-->2,720,751</td>
        <td><!--582-->582</td>
        <td><!--85514-->8</td>
        <td><!--4--><img src="/images/ico/4.gif" alt="Elf" /></td>
      </tr>
      		"""
 		block_pattern = re.compile('<tr>((\n.*<!--.*-->.*)+)\n.*</tr>')
		data_pattern = re.compile('<!--.*-->(.*)</td>')

		blocks = block_pattern.findall(html)
		for block in blocks:
			data = data_pattern.findall(block[0])
			data = [item.replace(',', '') for item in data]
			target_id = re.search("/viewprofile/index/(\d+)", block[0]).group(1)
			data += ['<a href="http://www.darkthrone.com/viewprofile/index/%s">Link</a>' %target_id]
			self.data.append(data)
		self.success = True

	def run(self):
		self.collect()
		if self.success:
			store_results(self.data)
		else:
			safe_print('; '.join(self.errors))

def store_results(a_result_list):
	global store_lock
	if store_lock is None:
		store_lock = threading.Lock()
	store_lock.acquire()
	global result_list
	result_list.extend(a_result_list)
	store_lock.release()

def safe_print(text):
	global output_lock
	if output_lock is None:
		output_lock = threading.Lock()
	output_lock.acquire()
	print text
	output_lock.release()


def filter_result(input, offence_soldier, level):
	#Rank Username Gold Army-Size Level Race
	new_result = []
	for line in input:
		army_level = int(line[4])
		army_size = int(line[3])
		gold = int(line[2])
		
		if (gold < 2000000) or army_size > offence_soldier*1.2 or army_level < level - 5 or army_level > level + 5:
			#print "Ignoring:", line
			pass
		else:
			new_result.append(line)

	return new_result

def get_more_readable_number(text):
	new_num = list(text)
	length = len(new_num)
	index = length
	for i in range ((length-1)/3):
		index -= 3
		new_num.insert(index, ',')
	return ''.join(new_num)
	
	
def result_to_text(input):
	new_result = ["""
<html>
<table border="1">
"""]
	headers = "Rank Username Gold Army-Size Level Race Link"
	new_result.append("<tr><td>" + "<td>".join(headers.split(' ')))
	for line in input:
		line[2] = get_more_readable_number(line[2])
		new_result.append("<tr><td>" + "<td>".join(line))
	new_result.append("""
</table>
</html>
""")
	return new_result

def sort_result(input):
	new_result = [(int(line[2]), line) for line in input]
	new_result.sort()
	new_result.reverse()
	new_result = [item[1] for item in new_result]
	return new_result
	
def collect_data(force_download, num_pages):
	num_processors = 2
	try:
		import mutliprocessing
		num_processors = mutliprocessing.cpu_count()
		print "Found number of processors: ", num_processors
	except ImportError, NotImplementedError:
		pass
	
	raw_results_file_name = "raw_results%s.py" % datetime.datetime.now().date().strftime("%Y%m%d")
	if not os.path.isfile(raw_results_file_name) or force_download:
		global result_list
		for index in range(1, num_pages + 1):
			while threading.activeCount() > 1 + 20*num_processors:
				time.sleep(1)
			DarkThroneDataCollector("http://www.darkthrone.com/userlist/attack?page=%s" % (index))

		# wait for everyone to finish
		while threading.activeCount() > 1:
			time.sleep(1)

		file = open(raw_results_file_name, 'w')
		file.write(str(result_list))
	else:
		file = open(raw_results_file_name, 'r')
		result_list = eval(file.read())

	return result_list


if __name__ == "__main__":
	parser = optparse.OptionParser("usage: %prog [options] email password")
	parser.add_option("-f", "--force_download", action="store_true", dest="force_download", help="force the download of target data",default=False)
	parser.add_option("-p", "--proxy", action="store_true", dest="use_proxy", help="Use TR proxy",default=False)
	(options, args) = parser.parse_args()

	if options.use_proxy:
		proxies = {'http': 'franck.mesirard:c696t6k99,,14@MHSPROXY.TFCORP.TFN.COM:80'}
	else:
		proxies = {}


	if len(args) != 2:
		parser.error("Requires username and password.")
	else:
		dtl = DarkThroneLogin(args[0], args[1], proxies)
		print "Pseudo:", dtl.pseudo
		print "Level:", dtl.level
		print "Offence_Soldier:", dtl.offence_soldier
		print "Num_Pages:", dtl.num_pages

		result_list = collect_data(options.force_download, dtl.num_pages)


		filtered_result = filter_result(result_list, dtl.offence_soldier, dtl.level)
		sorted_result = sort_result(filtered_result)
		result_in_text = result_to_text(sorted_result)
	
		file = open("targets_%s.html" % (dtl.pseudo), 'w')
		file.write('\n'.join(result_in_text))
		file.close()

