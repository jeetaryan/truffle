# creating connection---------------------------------
import mysql.connector
cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
# cnx = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")

cursor = cnx.cursor(buffered=True)
# end----------------------------------------
chunksize = 100000
notFound = 0
stop = 0
while not stop:
    # getting the language from visits table
    cursor.execute("select visitId, language from visits where langId is NULL and language is not NULL LIMIT %s", (chunksize+notFound, ))
    records = cursor.fetchall()
    if len(list(records))<chunksize:
        stop=1
    for row in records:
        visitId=row[0]
        lang_code = row[1][0:2]
        langId=0
        #print(lang_code)

        if lang_code == "en":
            langId=1
        elif lang_code == "de":
            langId=2
        elif lang_code == "fr":
            langId=3
        elif lang_code == "es":
            langId=4
        elif lang_code == "nl":
            langId=5
        else:
            # retrieving data from languages table on response of visits table------------------

            sql = "select langId from languages where code=%s"
            values = (lang_code,)
            cursor.execute(sql, values)
            data = cursor.fetchone()
            if data:
                if len(data)>0:
                    langId = data[0]
        
        if (langId != 0):
            values = (langId, visitId)
            sql = "UPDATE visits set langId = %s where visitId = %s"
            cursor.execute(sql, values)
            cnx.commit()
        else:
            notFound+=1
            #print("cannot parse langId for language: ", row[1])
    
    cursor.close()
    cnx.close()
