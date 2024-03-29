/****** Script for SelectTopNRows command from SSMS  ******/
SELECT [advert_id]
      ,[advert_url]
      ,[title]
      ,[location]
      ,[postcode]
      ,[price]
      ,[type]
      ,[description]
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
  FROM [Immobilier].[dbo].[adverts]
  WHERE price < 275000 AND (basement = 1 OR garage = 1) AND
  (
   (type = 'house' AND (surface > 70 OR attic = 1)) OR
   (type = 'flat' AND surface > 80 AND bedrooms > 4) OR
   (type = 'other')
   )
  ORDER BY price ASC