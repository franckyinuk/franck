import common_utils
import sounds

def specific_name(needed_call_string, name):
    # We return a function ("closure") that accepts a call_list that
    # will test for the call and return the name if is matches.
    def closure(call_list):
        if call_list[-1].get_call_string() == needed_call_string:
            return name
    return closure

def chris(call_list):
    if bong(call_list) and call_list[-1].get_value() == 1:
        return 'Chris'

def bing(call_list):
    call_string = call_list[-1].get_call_string()
    try:
        prev_call = call_list[-2]
    except IndexError:
        return

    if common_utils.get_bing(prev_call, True) == call_string:
        return 'bing'

def bong(call_list):
    (value, quantity) = call_list[-1].get_value_quantity()  
    try:
        (prev_value, prev_quantity) = call_list[-2].get_value_quantity()
    except IndexError:
        return

    if value == prev_value and quantity == prev_quantity + 1:
        return 'bong'

def beethoven(call_list):
    if len(call_list) >= 5 and bong(call_list) == 'bong' and bing(call_list[:-1]) == 'bing' and bing(call_list[:-2]) == 'bing' and bing(call_list[:-3]) == 'bing':
        sounds.beethoven()
        return 'Beethoven'
		
def bob_pence(call_list):
    (value, quantity) = call_list[-1].get_value_quantity()
    if value == 2:
        return '%dp' % (quantity * 5)

def hotel(call_list):
	if len(call_list) >= 2:
		current_call = call_list[-1]
		previous_call = call_list[-2]
		if current_call.get_value() == previous_call.get_quantity() and current_call.get_quantity() == previous_call.get_value():
			return 'hotel'
		
def kirk(call_list):
	if len(call_list) >= 2:
		current_call = call_list[-1]
		previous_call = call_list[-2]
		if current_call.get_value() == previous_call.get_value() -1 and current_call.get_quantity() == previous_call.get_quantity() + 1:
			return 'Kirk'
		
	

call_name_test_funcs = [
    # Specific names first.  specific_name returns a function
    specific_name('1x2', 'Bob'),
    specific_name('2x2', 'four'),
    specific_name('3x3', 'nine'),
    specific_name('4x4', 'sixteen'),
    specific_name('5x4', 'belly'),
    specific_name('5x5', 'twenty-five'),
    specific_name('6x2', 'thong'),
    specific_name('6x3', 'arse'),
    specific_name('6x6', 'beast'),
    specific_name('6x6', 'thirty-six'),
    specific_name('3x1', 'Franck'),
    specific_name('7x3', 'Jordan'),
    specific_name('8x5', 'I\'ve got a coin in my dinner'),
    specific_name('9x5', 'working girl'),
    specific_name('9x6', 'I\'ve got a bone in my mouth'),
    specific_name('10x4', 'Barclays Lehmans forex good buddy'),
    specific_name('10x5', 'Bradford'),
    specific_name('10x6', 'Battle of Hastings'),
    specific_name('13x3', 'Adam'),
    specific_name('20x4', 'Kiefer'),
    # More generic towards the end
    bob_pence,
    chris,
    beethoven,
    kirk,
    hotel,
    bing,
    bong,
    ]
