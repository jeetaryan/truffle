import translation6
import mysql.connector
import traceback




def refreshAllCompanyLogos():
    sql = "SELECT c.companyId, w.website from companies c inner join (SELECT companyId, website from websites group by companyId) as w on w.companyId=c.companyId"
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    
    print("Total Rows: ", len(rows))
    for row in rows:
        try:
            #translation6.getScreenshot(row[0], row[1], True)
            translation6.getLogo(row[0], row[1])
        except BaseException as e:
            print("Exception caught while updating visits after IP translation: ", e)
            traceback.print_exc()


refreshAllCompanyLogos()