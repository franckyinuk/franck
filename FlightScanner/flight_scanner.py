import urllib.request
import bs4
import imp
import os
from selenium import webdriver
import sys
import time
import re
import string
import datetime

GlobalUtils = imp.load_source('GlobalUtils.myutils', os.path.join('..', 'Utils', 'Python', 'python_utils.py'))

def GetUrlContent(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    return str(html)  

def GetUrlContentWithSelenium(url):
    response = ""
    try:
        browser = webdriver.Firefox()
        browser.set_page_load_timeout(25)
        browser.get(url)
        response = browser.execute_script("return document.documentElement.innerHTML;")

        # some time there seem to be 2 levels of javascript so further wait is needed to get the page fully loaded, so we wait and execute the script twice
        time.sleep(10)
        response = browser.execute_script("return document.documentElement.innerHTML;")
        browser.close()

    except:
        None

    return str(response)

class Flight:
    def __init__(self, price, departureTime, airline):
        self.price = price
        self.departureTime = departureTime
        self.airline = airline
    
def GetFlightPrice(url):
    result = []
    html = GetUrlContentWithSelenium(url)
    parsed_html = bs4.BeautifulSoup(html)
        
    # looking for flight result
    # <div class="resultWrapper">
    # <div class="resultInner keel-grid">
    # <div class="col-info result-column">
   # <span class="price option-text">75 €</span>
    for flight in parsed_html.body.find_all('div', attrs={'class':'resultWrapper'}):
        price = flight.find('span', attrs={'class':'price'}).text.strip()
        time = flight.find('div', attrs={'class':'depart'}).find('div', attrs={'class':'top'}).text.strip()
        airline = flight.find('div', attrs={'class':'carrier'}).find('div', attrs={'class':'bottom'}).text.strip()
        result.append(Flight(price, time, airline))

    return result

def GetFileNameFromURL(url):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in url if c in valid_chars)+".csv"
    
def GetReturnUrlPrice(url, sendingEmailFromSiemens, receipients, priceLimit):
    
    # do a search for single flights
    match = re.search(r"/((\w\w\w)-(\w\w\w)/(\d\d\d\d-\d\d-\d\d)/(\d\d\d\d-\d\d-\d\d))", url)
    if match:
        departureAiport = match.groups()[1]
        arrivalAiport = match.groups()[2]
        departureDate = match.groups()[3]
        arrivalDate = match.groups()[4]
        outgoingUrl = url.replace(match.groups()[0], "%s-%s/%s" %(departureAiport, arrivalAiport, departureDate))
        returnUrl = url.replace(match.groups()[0], "%s-%s/%s" %(arrivalAiport, departureAiport, arrivalDate))
        outgoingResults = GetFlightPrice(outgoingUrl)
        resultFound = False
        if len(outgoingResults) > 0:
            returnResults = GetFlightPrice(returnUrl)
            if len(returnResults) > 0:
                resultFound = True
                outgoingFlight = outgoingResults[0]
                returnFlight = returnResults[0]
                totalPrice = int(outgoingFlight.price[:-1]) + int(returnFlight.price[:-1])
                msg = "Flight: %s" %(url) + "\n"\
                    "Best price %d , the alert price is set to %d\n" %(totalPrice, priceLimit) +\
                    "  - %d %s %s" %(int(outgoingFlight.price[:-1]), outgoingFlight.departureTime, outgoingFlight.airline) + "\n"\
                    "  - %d %s %s" %(int(returnFlight.price[:-1]), returnFlight.departureTime, returnFlight.airline) + "\n"

                print(msg)
                fileExists = os.path.isfile(GetFileNameFromURL(url))
                with open(GetFileNameFromURL(url), "a") as myfile:
                    # add some headers if the file is new
                    if not fileExists:
                        myfile.write("timestamp,date and time, total price, on going price, time, company, return price, time, company\n")
                    
                    # add a the current flight data to the file
                    time = datetime.datetime.now()
                    myfile.write(','.join([
                                            str(int(time.timestamp())), 
                                            time.strftime("%Y-%m-%d %H:%M:%S"), 
                                            str(totalPrice),
                                            str(int(outgoingFlight.price[:-1])), 
                                            outgoingFlight.departureTime, 
                                            outgoingFlight.airline, 
                                            str(int(returnFlight.price[:-1])), 
                                            returnFlight.departureTime, 
                                            returnFlight.airline,
                                            "\n"]))
                if (totalPrice <= priceLimit):
                    print("sending email")
                    GlobalUtils.send_email2("Flight scanner email alert", [msg], receipients, sendingEmailFromSiemens)

        global s_errorSent
        if not resultFound and not s_errorSent:
            msg = "Flight: %s" %(url) + "\n No result found\n"
            GlobalUtils.send_email2("Flight scanner error", [msg], ["franck.mesirard@siemens.com"], sendingEmailFromSiemens)
            s_errorSent = True


    
    
if __name__ == "__main__":
    print("Starting")
    sendingEmailFromSiemens = True
    s_errorSent = False
    flightsToCheck = []
    
    receipients = ["franck.mesirard@yahoo.fr", "franck.mesirard@siemens.com"]
    franck = ["franck.mesirard@siemens.com"]
    
    #GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2016-04-02/2016-04-16/1adults", sendingEmailFromSiemens, receipients, 0)  # Avril 2016
    #GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2016-04-02/2016-04-12/1adults", sendingEmailFromSiemens, receipients, 0)  # Avril 2016
    #GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2016-10-19/2016-11-02/1adults", sendingEmailFromSiemens, receipients, 0)  # Toussaint 2016
    #GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2016-10-19/2016-10-29/1adults", sendingEmailFromSiemens, receipients, 0)  # Toussaint 2016
    #GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2016-10-18/2016-10-29/1adults", sendingEmailFromSiemens, receipients, 0)  # Toussaint 2016
    #GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2016-09-24/2016-10-05/1adults", sendingEmailFromSiemens, receipients, 0)  # Septembre 2016
    # GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2017-04-08/2017-04-21/1adults", sendingEmailFromSiemens, receipients, 150)  # Avril 2017
    # GetReturnUrlPrice(r"http://www.kayak.fr/flights/NTE-AGP/2017-04-08/2017-04-22/1adults", sendingEmailFromSiemens, receipients, 150)  # Avril 2017
    #GetReturnUrlPrice(r"https://www.kayak.fr/flights/NTE-AGP/2017-05-05/2017-05-10/1adults", sendingEmailFromSiemens, receipients, 100)  # Mai 2017 communion

    # Toussain 2017
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-21/2017-10-30?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-21/2017-11-01?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-21/2017-11-04?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-23/2017-10-30?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-23/2017-11-01?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-23/2017-11-04?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-AGP/2017-10-25/2017-11-04?fs=stops=0", sendingEmailFromSiemens, franck, 200])
    michele = ["michele.bretonniere@free.fr", "franck.mesirard@siemens.com"]
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-LIS/2017-10-05/2017-10-08?fs=stops=0", sendingEmailFromSiemens, franck, 150]) # Toussaint 2017
    flightsToCheck.append([r"https://www.kayak.fr/flights/NTE-LIS/2017-10-06/2017-10-08?fs=stops=0", sendingEmailFromSiemens, franck, 150]) # Toussaint 2017
    
    
    for flight in flightsToCheck:
        try:
            GetReturnUrlPrice(flight[0], flight[1], flight[2], flight[3])
        except Exception as exception:
            msg = "Exception when checking %s: %s " %(flight[0], exception)
            print(msg)
            GlobalUtils.send_email2("Flight scanner error", [msg], ["franck.mesirard@siemens.com"], sendingEmailFromSiemens)
                      
    
