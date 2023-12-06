from services import StringHelper
import mysql.connector
import traceback
#import technographics


def normalizeAllWebsites():
    connection = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = connection.cursor(buffered=True)
    sql = "SELECT site_id, website from websites"
    cursor.execute(sql)
    rows = cursor.fetchall()
    print("Total Rows: ", len(rows))
    for row in rows:
        print(row[1])
        website = StringHelper.clnWebsite(row[1])
        if website != row[1]:
            try:
                print("processing Domain: ", website)
                sql = "update websites set website=%s where site_id=%s"
                values = (website, row[0])
                cursor.execute(sql, values)
                connection.commit()
            except mysql.connector.IntegrityError as err:
                print("Domain seems to exist already: ", website)
                try:
                    sql = "DELETE from websites where site_id=%s"
                    values = (row[0],)
                    cursor.execute(sql, values)
                    connection.commit()
                except BaseException as e:
                    print("Exception caught: {}".format(e))
                    traceback.print_exc()
            except BaseException as e:
                print("Exception caught: {}".format(e))
                traceback.print_exc()
            #translation6.getScreenshot(row[0], row[1], True)
        #translation6.getScreenshot(row[0], row[1], False)
        #translation6.getLogo(row[2], row[1])
        #technographics.getTechnographics(row[0], row[1])
    cursor.close()
    connection.close()

normalizeAllWebsites()
