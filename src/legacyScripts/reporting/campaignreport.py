import mysql.connector
import datetime as dt


cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)


sql = "SELECT * FROM (select ipAddress_int, visitId from visits where customerId = %s and visitTime>=%s) as a inner join (SELECT * from campaignRanges where campaignId=%s) b on ((a.ipAddress_int > b.ipStartv4) and (a.ipAddress_int < b.ipEndv4)) group by a.visitId"
values = (4, dt.datetime(2022,10,29), 2)

cursor.execute(sql, values)
rows = cursor.fetchall()
print("Impressions: ", len(rows))