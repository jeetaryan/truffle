import mysql.connector


# sql connection
# sqlDbCon = mysql.connector.connect(host="localhost", user="root", password="", database="proj_welva")
sqlDbCon = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlConn = sqlDbCon.cursor()

sql = "SELECT * from observed_pages"
sqlConn.execute(sql)
data = sqlConn.fetchall()

for row in data:
    alt = row[1]
    newPageUrl = row[1].split("://")
    if len(newPageUrl) > 1:
    	print(alt, " ->  ", newPageUrl[1])
    	values = (newPageUrl[1], row[0])
    	sql = "UPDATE observed_pages SET pageUrl=%s WHERE pageId=%s"
    	sqlConn.execute(sql, values)
    	sqlDbCon.commit()
sqlConn.close()
sqlDbCon.close()
