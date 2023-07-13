import urllib.request
import time
import re
import pprint
import multiprocessing
import itertools
import imp
import os

GlobalUtils = imp.load_source('GlobalUtils.myutils', os.path.join('..', 'Utils', 'Python', 'python_utils.py'))

import database

class Advert():
    def __init__(self):
        return

s_adUrls = []        

class Utils:
    @staticmethod
    def ExtractTextFromPattern(pattern, html, caseInSensitive = False):
        # r'.*?<th>Classe .*?nergie :</th>.*?<td>.*?<a href="http.*?>(\w).*?</a>.*?</td>'
        match = None;
        if caseInSensitive:
            match = re.match(pattern, html, re.IGNORECASE)
        else:
            match = re.match(pattern, html)
            
        if match:
            return match.group(1)
        else:
            return None     

    @staticmethod
    def IsPatternInText(pattern, html, caseInSensitive = True):
        match = None;
        if caseInSensitive:
            match = re.match(pattern, html, re.IGNORECASE)
        else:
            match = re.match(pattern, html)
            
        if match:
            return 1
        else:
            return 0

    @staticmethod
    def GetUrlContent(url):
        #print("GetUrlContent:", url)
        html = urllib.request.urlopen(url).read()
        return str(html)        
                   
    @staticmethod
    def GetIntFromText(text):
        if text is None:
            return 0
        else:
            return int(text.replace(" ", ""))
        
    @staticmethod
    def GiveJobToWorkers(workerFuntion, jobList):
        # create a pool of workers, starts with has many worker as cores
        numCpu = multiprocessing.cpu_count()
        cpusToUse = numCpu * 4
        #print("Found %d CPUs and using %d" % (numCpu, cpusToUse))
        pool = multiprocessing.Pool(cpusToUse)
        chunksize = max(int(len(jobList) / (cpusToUse * 2)), cpusToUse)
        print("worker:", workerFuntion, "chunksize:", chunksize)
        results = pool.map(workerFuntion, jobList, chunksize = chunksize)
        pool.close()
        pool.join()         
        
        return results
    
# can't be in the class as used by worker thread
def GlobalCollectPageData(adURL):
    html = Utils.GetUrlContent(adURL)
    adFields = {}
    adFields[database.ADVERT_URL] = adURL
    
    coreText = LeBonCoinSimpleParser.CollectAdCoreText(html)
    adFields[database.WEBSITE] = "leboncoin"
    adFields[database.TITLE] = LeBonCoinSimpleParser.CollectAdTitle(coreText)
    adFields[database.PRICE] = LeBonCoinSimpleParser.CollectAdPrice(coreText)
    adFields[database.LOCATION] = LeBonCoinSimpleParser.CollectAdLocation(coreText)
    adFields[database.DESCRIPTION] = LeBonCoinSimpleParser.CollectAdDescription(coreText)
    adFields[database.POSTCODE] = LeBonCoinSimpleParser.CollectAdPostCode(coreText)
    adFields[database.TYPE]  = LeBonCoinSimpleParser.CollectAdType(coreText)
    adFields[database.ROOMS] = LeBonCoinSimpleParser.CollectAdNumberOfRooms(coreText)
    adFields[database.BEDROOMS] = LeBonCoinSimpleParser.CollectAdNumberOfBedrooms(coreText)
    adFields[database.SURFACE] = LeBonCoinSimpleParser.CollectAdSurface(coreText)
    adFields[database.GES] = LeBonCoinSimpleParser.CollectAdGES(coreText)
    adFields[database.ENERGY] = LeBonCoinSimpleParser.CollectAdEnergyRating(coreText)
    adFields[database.GARAGE] = LeBonCoinSimpleParser.CollectAdGarage(coreText)
    adFields[database.BASEMENT] = LeBonCoinSimpleParser.CollectAdBasement(coreText)
    adFields[database.ATTIC] = LeBonCoinSimpleParser.CollectAdAttic(coreText)
    adFields[database.WELL] = LeBonCoinSimpleParser.CollectAdWell(coreText)
    adFields[database.VIAGER] = LeBonCoinSimpleParser.CollectAdViager(coreText)
    adFields[database.IMAGE_LINKS] = LeBonCoinSimpleParser.CollectAdImages(coreText)
    return adFields
           
# can't be in the class as used by worker thread
def GlobalCollectAddUrlsOnPage(pageUrl):
    #print("pageUrl:", pageUrl)
    foundAds = []
    html = Utils.GetUrlContent(pageUrl)
    """<a href="http://www.leboncoin.fr/ventes_immobilieres/557446149.htm?ca=18_s" title="R&eacute;novation St Philbert&#45;en&#45;M(49600) 45min de Nantes">"""
    pageLinkPattern = re.compile('<a [^<]+ title[^<]+>')
    pageLinkMatches = pageLinkPattern.findall(html)
    #print(html)
    for pageLinkMatch in pageLinkMatches:
        #print(pageLinkMatch)
        # find the href bit
        match = re.match(r'.*?href="([^"]+?)"', pageLinkMatch)
        if match:
            foundAds.append(match.group(1))
    return foundAds

           
class LeBonCoinSimpleParser():
    def __init__(self):
        self.m_pageUrls = []
        self.m_adUrls = []
        self.m_lock = multiprocessing.Manager().Lock()
        self.Run()

    def Run(self):
        self.GetSearchUrls()
        self.CollectAddsUrls()
        allAdsData = []
        allAdsData = self.CollectPagesData()
               
        self.AddAdvertsToDatabase(allAdsData)


        db = database.PYODBC_DATABASE()
        listing = db.GetNewInterestingListings()
        if (len(listing)):
            GlobalUtils.send_email(listing, ["franck.mesirard@yahoo.fr"])
                 
    def AddAdvertsToDatabase(self, adverts):
        with GlobalUtils.Timer() as t:
            db = database.PYODBC_DATABASE()
            db.AddUpdateAdvertRecords(adverts)     
        print("Added %d records to the database in %s" % (len(adverts), GlobalUtils.humanize_time(t.secs)))
        
        
    def GetSearchUrls(self):
        with GlobalUtils.Timer() as t:

            criteria = []
            # house, 60m2+, 0 < price < 325000
            criteria.append(r"http://www.leboncoin.fr/ventes_immobilieres/offres/pays_de_la_loire/?o=1&pe=13&sqs=7&ret=1&location=%s&sp=1")
            # flat, 60m2+, 0 < price < 275000
            #criteria.append(r"http://www.leboncoin.fr/ventes_immobilieres/offres/pays_de_la_loire/?o=1&pe=11&sqs=7&ret=2&location=%s&sp=1")
            towns = []
            towns.append("Nantes")                                  # Nantes 44000, 44100, 44200, 44300
            #towns.append("Thouar%E9-sur-Loire%2044470")             # Thouaré-sur-Loire 44470
            towns.append("Saint-Herblain 44800")                    # Saint-Herblain 44800
            towns.append("Indre 44610")                             # Indre 44610
            #towns.append("La Montagne 44620")                       # La Montagne 44620
            #towns.append("Bouguenais 44340")                        # Bouguenais 44340
            #towns.append("Rez%E9%2044400")                          # Rezé 44400
            #towns.append("Les%20Sorini%E8res%2044840")              # Les Sorinières 44840
            #towns.append("Saint-S%E9bastien-sur-Loire%2044230")     # Saint-Sébastien-sur-Loire 44230
            #towns.append("Vertou 44120")                            # Vertou 44120
            #towns.append("Basse-Goulaine 44115")                    # Basse-Goulaine 44115
            #towns.append("Haute-Goulaine 44115")                    # Haute-Goulaine 44115 
            #towns.append("Sainte-Luce-sur-Loire 44980")             # Sainte-Luce-sur-Loire 44980
            towns.append("Carquefou 44470")                         # Carquefou 44470
            towns.append("La Chapelle-sur-Erdre 44240")             # La Chapelle-sur-Erdre 44240
            #towns.append("Treilli%E8res%2044119")                   # Treillières 44119
            towns.append("Orvault 44700")                           # Orvault 44700
            #towns.append("Sautron 44880")                           # Sautron 44880
            
            firstSearchResultPages = []
            for criterion in criteria:
                for town in towns:
                    firstSearchResultPages.append(criterion % town)
                   
            for firstPage in firstSearchResultPages:
                self.GenerateSearchUrls(firstPage)
            
        print("Found %d search pages in %s" % (len(self.m_pageUrls), GlobalUtils.humanize_time(t.secs)))


    def GenerateSearchUrls(self, firstPage):
        html = Utils.GetUrlContent(firstPage)
        # find the last search page of this search
        #<a href="http://www.leboncoin.fr/ventes_immobilieres/offres/pays_de_la_loire/?o=123&amp;location=Nantes&amp;sp=1">&gt;&gt;</a>
        lastPageNumber = Utils.ExtractTextFromPattern(r'.*?<a[^<]*?o=(\d+)[^<]*?>&gt;&gt;</a>', html)
        if lastPageNumber is None:
            lastPageNumber = 1
        #print("Last page:", lastPageNumber)
        for index in range(1,int(lastPageNumber) + 1):
            resultPage = firstPage.replace("o=1", "o=%d" % index)
            self.AddAdUrl(resultPage)

    def AddAdUrl(self, url):
        #print("AddAdUrl:", url)
        with self.m_lock:
            self.m_pageUrls.append(url)
                
    def CollectAddsUrls(self):
        with GlobalUtils.Timer() as t:
            #print("CollectAddsUrls:", self.m_pageUrls)
            unFlattenedList = []
            # for pageUrl in self.m_pageUrls:
                # newunFlattenedList = LeBonCoinSimpleParser.CollectAddUrlsOnPage(pageUrl)
                # unFlattenedList.append(newunFlattenedList)
                
            # create a pool of workers to do the job
            unFlattenedList = Utils.GiveJobToWorkers(GlobalCollectAddUrlsOnPage, self.m_pageUrls)
            #unFlattenedList = Utils.GiveJobToWorkers(LeBonCoinSimpleParser.CollectAddUrlsOnPage, self.m_pageUrls)
            
            # unFlattenedList is a list of list so we need to flatten it
            chain = itertools.chain(*unFlattenedList)
            #print("unFlattenedList:", unFlattenedList)
            self.m_adUrls = list(chain)
        print("Found %d ads in %s" %(len(self.m_adUrls), GlobalUtils.humanize_time(t.secs)))

    @staticmethod
    def CollectAddUrlsOnPage(pageUrl):
        return GlobalCollectAddUrlsOnPage(pageUrl)
        
    def CollectPagesData(self):
        with GlobalUtils.Timer() as t:
            #self.m_adUrls = ["http://www.leboncoin.fr/ventes_immobilieres/560931069.htm?ca=18_s", "http://www.leboncoin.fr/ventes_immobilieres/557146320.htm?ca=18_s"]
            allAdsData = []
            
            if False:           
                for adURL in self.m_adUrls:
                    adData = LeBonCoinSimpleParser.CollectPageData(adURL)
                    allAdsData.append(adData)
            else:
                # create a pool of workers to do the job
                allAdsData = Utils.GiveJobToWorkers(GlobalCollectPageData, self.m_adUrls)
        
        #print("allAdsData:", allAdsData)
        print("Collected %d ads in %s" %(len(allAdsData), GlobalUtils.humanize_time(t.secs)))
        return allAdsData
        
    def CollectPageData(adURL):
        return GlobalCollectPageData(adURL)
    
    def CollectAdCoreText(html):
        """<div class="lbcContainer">...
        <div id="adview_advise" class="lbcAdvise">"""
        return Utils.ExtractTextFromPattern(r'.*?<div class="lbcContainer">(.*?)<div id="adview_advise" class="lbcAdvise">', html)
    
    def CollectAdTitle(html):
        """<h2 id="ad_subject">Appartement 5 pièces 101 m²</h2>"""
        return Utils.ExtractTextFromPattern(r'.*?<h2 id="ad_subject">(.*?)</h2>', html)
            
    def CollectAdPrice(html):
        """<span class="price">250 000&nbsp;€</span>"""
        numberString = Utils.ExtractTextFromPattern(r'.*?<span class="price">(.+?)&nbsp;&euro;</span>', html)
        return Utils.GetIntFromText(numberString)
            
    def CollectAdLocation(html):
        """<th>Ville :</th>  <td>Nantes</td>"""
        return Utils.ExtractTextFromPattern(r'.*?<th>Ville :</th>.*?<td>(.+?)</td>', html) 

    def CollectAdPostCode(html):
        """<th>Code postal :</th>  <td>44000</td>"""
        return Utils.ExtractTextFromPattern(r'.*?<th>Code postal :</th>.*?<td>(.+?)</td>', html)

    def CollectAdType(html):
        """<th>Type de bien : </th>   <td>Maison</td>"""
        type = Utils.ExtractTextFromPattern(r'.*?<th>Type de bien : </th>.*?<td>(.+?)</td>', html)
        if type == "Maison":
            return database.TYPE_HOUSE
        elif type == "Appartement":
            return database.TYPE_FLAT
        else:
            return database.TYPE_OTHER
            
        

    def CollectAdNumberOfRooms(html):
        """<th>Pièces : </th>  <td>6</td>"""
        # r'.*?<th>Pi.*?ces : </th>.*?<td>(.+?)</td>'
        numberString = Utils.ExtractTextFromPattern(r'.*?<th>Pi.*?ces : </th>.*?<td>(.+?)</td>', html)
        return Utils.GetIntFromText(numberString)

    def CollectAdSurface(html):
        """<th>Surface : </th>  <td>198 m<sup>2</sup></td>"""
        numberString = Utils.ExtractTextFromPattern(r'.*?<th>Surface : </th>.*?<td>(.+?) m<sup>2</sup></td>', html)
        return Utils.GetIntFromText(numberString)

    def CollectAdGES(html):
        """<th>GES :</th>
                <td>
                    <script type="text/javascript">
                        document.write('<a href="javascript:;" onClick="window.open(\'http://www.leboncoin.fr/popup_diagnostic_performance_energetique.htm\', \'DPE\', \'scrollbars=yes,width=560,height=560\')">D (de 21 &agrave; 35)<' + '/a>');
                    </script><a href="javascript:;" onclick="window.open('http://www.leboncoin.fr/popup_diagnostic_performance_energetique.htm', 'DPE', 'scrollbars=yes,width=560,height=560')">D (de 21 à 35)</a>
                    <noscript>
                        <a href="http://www.leboncoin.fr/popup_diagnostic_performance_energetique.htm" target="_blank">Vierge (de 21 &agrave; 35)</a>
                    </noscript>
                </td>"""
        return Utils.ExtractTextFromPattern(r'.*?<th>GES :</th>.*?<td>.*?<a href="http.*?>(\w+).*?</a>.*?</td>', html)

    def CollectAdEnergyRating(html):
        """<th>Classe énergie :</th>
                <td>
                    <script type="text/javascript">
                        document.write('<a href="javascript:;" onClick="window.open(\'http://www.leboncoin.fr/popup_diagnostic_performance_energetique.htm\', \'DPE\', \'scrollbars=yes,width=560,height=560\')">D (de 21 &agrave; 35)<' + '/a>');
                    </script><a href="javascript:;" onclick="window.open('http://www.leboncoin.fr/popup_diagnostic_performance_energetique.htm', 'DPE', 'scrollbars=yes,width=560,height=560')">D (de 21 à 35)</a>
                    <noscript>
                        <a href="http://www.leboncoin.fr/popup_diagnostic_performance_energetique.htm" target="_blank">D (de 21 &agrave; 35)</a>
                    </noscript>
                </td>"""
        return Utils.ExtractTextFromPattern(r'.*?<th>Classe .*?nergie :</th>.*?<td>.*?<a href="http.*?>(\w+).*?</a>.*?</td>', html)


    def CollectAdGarage(html):
        """<div class="content">
        A 2 km du bourg de legé !!! Belle longère de 144
m² habitable en pierre entièrement rénovée en
2006. <br>Dans un cadre de vie agréable.<br>Pièce de vie de 65 m² avec cuisine familiale et
salon cheminée, 4 grandes chambres à l'étage +
maison rénovée indépendante de 54 m² offrant 2
chambres(possibilité locatif). <br>Jardin en campagne et sans vis à vis de 2800 m²
avec des arbres fruitiers.<br>Commerces, écoles, Mairie, école à proximité<br>Particulier. Disponible pour répondre à toutes vos
questions.
    </div>"""
        return Utils.IsPatternInText(r'.*?<div class="content">.*?(garage|pandance|pendance).*?</div>', html)

    def CollectAdBasement(html):
        return Utils.IsPatternInText(r'.*?<div class="content">.*?(soussol|sous-sol|sous sol).*?</div>', html)

    def CollectAdViager(html):
        return Utils.IsPatternInText(r'.*?<div class="content">.*?(viag).*?</div>', html)

    def CollectAdNumberOfBedrooms(html):
        numberOfRooms = 0
        options = {
            '1' : 1,
            '2' : 2,
            '3' : 3,
            '4' : 4,
            '5' : 5,
            '6' : 6,
            '7' : 7,
            'un': 1,
            'une': 1,
            'deux': 2,
            'trois': 3,
            'quatre': 4,
            'cing': 5,
            'six': 6,
            'sept': 7,
            }
        match = re.match(r'.*?<div class="content">(.*?)</div>', html, re.IGNORECASE)
        if match:
            descriptionText = match.group(1).replace(r"\n", ' ')
            descriptionText = descriptionText.replace(r"<br>", ' ', re.IGNORECASE)
            #print(descriptionText)
            matches = re.findall(r'(1|2|3|4|5|6|7|une|un|deux|trois|quatre|cinq|six|sept)\s*?\w*?\s*?(ch|chs|chambre|chambres)[^\w]', descriptionText, re.IGNORECASE)
            for match in matches:
                numberOfRooms += options.get(match[0].lower(), 0)
        return numberOfRooms

    def CollectAdImages(html):
        """                  <div class="thumbs_carousel_window">
                            <div id="thumbs_carousel">
                                <a id="thumb_0" class="thumbs_cadre active" href="#" onclick="return showImage(0);"> \n                                    
                                    <span class="thumbs" style="background-image: url(\'http://193.164.197.50/thumbs/093/093331094845396.jpg\');"></span> \n                                </a>\n                            
                                <a id="thumb_1" class="thumbs_cadre" href="#" onclick="return showImage(1);"> \n                                    
                                    <span class="thumbs" style="background-image: url(\'http://193.164.197.30/thumbs/091/091331093447390.jpg\');"></span> \n                                </a>\n                            
                                <a id="thumb_2" class="thumbs_cadre" href="#" onclick="return showImage(2);"> \n                                    
                                    <span class="thumbs" style="background-image: url(\'http://193.164.197.60/thumbs/095/095331099923504.jpg\');"></span> \n                                </a>\n                            
                                <a id="thumb_3" class="thumbs_cadre" href="#" onclick="return showImage(3);"> \n                                    
                                    <span class="thumbs" style="background-image: url(\'http://193.164.196.30/thumbs/096/096331094795592.jpg\');"></span> \n                                </a>\n                            
                                <a id="thumb_4" class="thumbs_cadre" href="#" onclick="return showImage(4);"> \n                                    
                                    <span class="thumbs" style="background-image: url(\'http://193.164.196.50/thumbs/090/090331094536366.jpg\');"></span> \n                                </a>\n                            \n                            
                            </div>
                        </div>"""
        images  = []
        match = re.match(r'.*?<div id="thumbs_carousel">(.*?)</div>', html, re.IGNORECASE)
        if match:
            imageGroup = match.group(1)
            #print(imageGroup)
            matches = re.findall(r"url\(\\'(.+?)\\'\)", imageGroup, re.IGNORECASE)
            for match in matches:
                thumbNailAddress = match
                #print(thumbNailAddress)
                fullImageAddress = thumbNailAddress.replace("/thumbs/", "/images/")
                images.append(fullImageAddress)
        return images

    def CollectAdWell(html):
        return Utils.IsPatternInText(r'.*?<div class="content">.*?puit.*?</div>', html)

    def CollectAdAttic(html):
        return Utils.IsPatternInText(r'.*?<div class="content">.*?(grenier|comble).*?</div>', html)

    def CollectAdDescription(html):
        return Utils.ExtractTextFromPattern(r'.*?<div class="content">(.*?)</div>', html)
        
        
if __name__ == "__main__":
    with GlobalUtils.Timer() as t:
        LeBonCoinSimpleParser()
    print("Completed in", GlobalUtils.humanize_time(t.secs))