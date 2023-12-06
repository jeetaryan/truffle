import mysql.connector
import traceback

cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)

sql = "SELECT companyId, website  FROM kickfire where website is not null"

cursor.execute(sql)
data = cursor.fetchall()

for x in data:
    try:
        companyId=x[0]
        website=x[1]

        print("companyId: ", companyId, " - website: ", website)

        values = (website, companyId)
        sql = "insert ignore into websites(website, companyId) values(%s, %s)"
        cursor.execute(sql, values)
        cnx.commit()
    except BaseException as e:
        print("Exception caught: ", e)
        traceback.print_exc() 
