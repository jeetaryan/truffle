import mysql.connector
import time
import sys

# sql connection
# sqlDbCon = mysql.connector.connect(host="localhost", user="root", password="", database="proj_welva")
sqlDbCon = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlConn = sqlDbCon.cursor()
loopno= 0
chunk=1000
count = 1 

while 1:
        sql = "SELECT DISTINCT ipAddress_int from visits where status=0 and companyId is null and ipAddress_int is not null LIMIT " + str(chunk)
        sqlConn.execute(sql)
        data = sqlConn.fetchall()
        numberofrows = len(data) + loopno*chunk
        loopno += 1

        if len(data) == 0:
            sql = "UPDATE visits set status=0 where status=6 and companyId is null"
            sqlConn.execute(sql)
            sqlDbCon.commit()
            sqlConn.close()
            sqlDbCon.close()

            sys.exit()

        for row in data:
            print("Updating ", count, " of ", numberofrows)
            sql = "UPDATE visits set companyId=(SELECT companyId from ip_ranges where ipStart<=" + str(row[0]) + " and ipEnd>=" + str(row[0]) + " LIMIT 1), status=6 where ipAddress_int=" + str(row[0])
            #print(sql)
            sqlConn.execute(sql)
            sqlDbCon.commit()
            count += 1
