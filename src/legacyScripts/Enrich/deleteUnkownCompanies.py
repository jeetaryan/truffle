import translation6
import mysql.connector
import traceback




def deleteCompaniesWithoutName():
    sql = "SELECT companyId from companies where companyName is null"
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    
    print("Total Rows: ", len(rows))
    for row in rows:
        try:
            print("deleting", row[0])
            translation6.deleteCompanyWithoutVisits(row[0])
        except BaseException as e:
            print("Exception caught while deleting: ", e)
            traceback.print_exc()

deleteCompaniesWithoutName()
#updateCompanies()
#unifyCompanies()
#translateData(500)