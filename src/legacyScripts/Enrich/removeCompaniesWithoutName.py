#################################################
# removes companies without a company name ("") #
#################################################

import mysql.connector
import translation5



cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)
cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor3 = cnx3.cursor(buffered=True)

values = ("",)
sql = "SELECT companyId FROM kickfire where companyName=%s and not exists (SELECT * FROM proxycurl where proxycurl.company_ID=kickfire.companyId)"
cursor.execute(sql, values)
companies = cursor.fetchall()

for company in companies:
    companyId = company[0]
    deleteCompanyWithoutVisits(companyId)

values = ("",)
sql = "SELECT company_ID FROM proxycurl where company_name=%s and not exists (SELECT * FROM kickfire where proxycurl.company_ID=kickfire.companyId)"
cursor.execute(sql, values)
companies = cursor.fetchall()
for company in companies:
    companyId = company[0]
    deleteCompanyWithoutVisits(companyId)

