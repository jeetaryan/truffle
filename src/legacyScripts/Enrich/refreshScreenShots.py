import translation6
import mysql.connector
import traceback




def refreshAllScreenshots():
    sql = "SELECT site_id, website, companyId from websites"
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    
    print("Total Rows: ", len(rows))
    for row in rows:
        try:
            translation6.getScreenshot(row[0], row[1], True)
            #translation6.getLogo(row[2], row[1])
        except BaseException as e:
            print("Exception caught while updating visits after IP translation: ", e)
            traceback.print_exc()
#translation6.getScreenshot(4071, "1und1.net", True)
#translation6.getScreenshot(62724, "telekom.de", True)
#translation6.getScreenshot(4058, "vodafone.de", True)


refreshAllScreenshots()
#updateCompanies()
#unifyCompanies()
#translateData(500)