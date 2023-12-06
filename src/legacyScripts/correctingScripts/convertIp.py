import mysql.connector
import time
import sys
import ipaddress

# sql connection
# sqlDbCon = mysql.connector.connect(host="localhost", user="root", password="", database="proj_welva")
sqlDbCon = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlConn = sqlDbCon.cursor()
loopno= 0
chunk=1000
count = 1 

while 1:
        sql = "SELECT visitId, ipAddress from visits where ipaddress_int is null LIMIT " + str(chunk)
        sqlConn.execute(sql)
        data = sqlConn.fetchall()
        numberofrows = len(data) + loopno*chunk
        loopno += 1

        if len(data) == 0:
            sys.exit()

        for row in data:
            print("Updating ", count, " of ", numberofrows)
            sql = "UPDATE visits set ipaddress_int=" + str(int(ipaddress.IPv4Address(row[1]))) + " where visitId=" + str(row[0])
            print(sql)
            sqlConn.execute(sql)
            sqlDbCon.commit()
            count += 1
