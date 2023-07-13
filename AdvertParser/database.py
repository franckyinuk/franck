import pyodbc
import sys
import traceback
import datetime
import pprint

ADVERT_URL = "advert_url";
TITLE = "title"
LOCATION = "location"
POSTCODE = "postcode"
PRICE = "price"
TYPE = "type"
DESCRIPTION = "description"
ROOMS = "rooms"
BEDROOMS = "bedrooms"
SURFACE = "surface"
GES = "ges"
ENERGY = "energy"
GARAGE = "garage"
BASEMENT = "basement"
ATTIC = "attic"
WELL = "well"
VIAGER = "viager"
START_DATE = "start_date"
LAST_UPDATE = "last_update"
END_DATE = "end_date"
IMAGE_LINKS = "image_links"
WEBSITE = "website"

TYPE_HOUSE = "house"
TYPE_FLAT = "flat"
TYPE_OTHER = "other"

"""
SELECT TOP 1000 [advert_id]
      ,[advert_url]
      ,[title]
      ,[location]
      ,[postcode]
      ,[price]
      ,[type]
      '[description]
      ,[rooms]
      ,[bedrooms]
      ,[surface]
      ,[ges]
      ,[energy]
      ,[garage]
      ,[basement]
      ,[attic]
      ,[well]
      ,[start_date]
      ,[last_update]
      ,[end_date]
      ,[website]
  FROM [Immobilier].[dbo].[adverts]
"""

class PYODBC_DATABASE:
    def __init__(self):
        self.connection = pyodbc.connect('DRIVER={SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=Immobilier')
        self.cursor = self.connection.cursor()
        
    def AddUpdateAdvertRecords(self, records):
        for record in records:
            try: 
                #self.cursor.execute("insert into adverts(advert_url, title, location, postcode, price, type, description, rooms, bedrooms, surface, ges, energy, garage, basement, attic, well) values (?, ?)", 'pyodbc', 'awesome library')
                # self.cursor.execute("insert into adverts(advert_url, title, price, bedrooms) values (?, ?, ?, ?)", 
                    # record[ADVERT_URL],
                    # record[TITLE],
                    # record[PRICE],
                    # record[BEDROOMS])
                
                # first check if this ad is already in the database
                self.cursor.execute("SELECT %s FROM adverts WHERE %s= ?" %(ADVERT_URL, ADVERT_URL), record[ADVERT_URL])
                rows = self.cursor.fetchall()
                # print("record:", record[ADVERT_URL])
                # print("rows:", rows)
                if len(rows) == 0:
                    # if this advert is not found then insert it
                    (fieldNameList, markerList, fieldValueList) = self.MakeListsForDataBaseQuery(record)
                    # add START_DATE
                    fieldNameList.append(START_DATE)
                    markerList.append("?")
                    fieldValueList.append(datetime.datetime.now())
                    
                    insertQuery = "INSERT INTO adverts(%s) values(%s)" % (", ".join(fieldNameList), ", ".join(markerList))
                    #print("insert:", insertQuery)
                    self.cursor.execute(insertQuery, fieldValueList)
                    self.connection.commit()
                elif len(rows) == 1:
                    # if found then only update it
                    (fieldNameList, markerList, fieldValueList) = self.MakeListsForDataBaseQuery(record)
                    # add LAST_UPDATE
                    fieldNameList.append(LAST_UPDATE)
                    markerList.append("?")
                    fieldValueList.append(datetime.datetime.now())

                    updateQuery = "UPDATE adverts SET %s WHERE %s = ?" % (", ".join(["%s = ?" % x for x in fieldNameList]), ADVERT_URL)
                    #print("update:", updateQuery)
                    fieldValueList.append(record[ADVERT_URL])
                    self.cursor.execute(updateQuery, fieldValueList)
                    self.connection.commit()
                else:
                    print("Error: url '%s' was found %d times in table adverts" % (record[ADVERT_URL], len(row)))
            except:
                print(traceback.format_exc())
                pprint.pprint(record)
                #print("Unexpected error:", sys.exc_info())
                #raise e
            
    
    def MakeListsForDataBaseQuery(self, record):
        fieldNameList = []
        markerList = []
        fieldValueList = []
        for fieldName in record:
            # ignore images for now
            if fieldName == IMAGE_LINKS:
                continue
            
            fieldValue = record[fieldName]
            fieldNameList.append(fieldName)
            markerList.append("?")
            fieldValueList.append(fieldValue)        
        return (fieldNameList, markerList, fieldValueList)

    def GetNewInterestingListings(self):
        results = []
        #latestUpdate = datetime.datetime.now().date()
        query = "SELECT TOP 1 %s FROM adverts ORDER BY %s DESC" % (START_DATE, START_DATE)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        latestUpdate = str(rows[0][0])[:10]
        
        print("Fetching houses with basement added since %s" % latestUpdate)
        query = "SELECT %s, %s FROM adverts WHERE %s<=325000 AND %s=1 AND %s>'%s' AND %s='%s' ORDER BY %s" % (PRICE, ADVERT_URL, PRICE, BASEMENT, START_DATE, latestUpdate, TYPE, TYPE_HOUSE, PRICE)
        print(query)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if len(rows):
            results.append("Found %d houses with basement" % len(rows))
        for row in rows:
            string = "%s, %s" % (row[0], row[1])
            print(string)
            results.append(string)
            
        print("Fetching houses with garage added since %s" % latestUpdate)
        query = "SELECT %s, %s FROM adverts WHERE %s<=325000 AND %s=1 AND %s>'%s' AND %s='%s' ORDER BY %s" % (PRICE, ADVERT_URL, PRICE, GARAGE, START_DATE, latestUpdate, TYPE, TYPE_HOUSE, PRICE)
        print(query)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if len(rows):
            results.append("Found %d houses with garage" % len(rows))
        for row in rows:
            string = "%s, %s" % (row[0], row[1])
            print(string)
            results.append(string)
            
        #print("Fetching flats with 4 bedrooms added since %s" % latestUpdate)
        #query = "SELECT %s, %s FROM adverts WHERE %s<=325000 AND %s>'%s' AND %s='%s' AND %s>=4 ORDER BY %s" % (PRICE, ADVERT_URL, PRICE, START_DATE, latestUpdate, TYPE, TYPE_FLAT, BEDROOMS, PRICE)
        #print(query)
        #self.cursor.execute(query)
        #rows = self.cursor.fetchall()
        #if len(rows):
        #    results.append("Found %d flats" % len(rows))
        #for row in rows:
        #    string = "%s, %s" % (row[0], row[1])
        #    print(string)
        #    results.append(string)
        
        return results


        