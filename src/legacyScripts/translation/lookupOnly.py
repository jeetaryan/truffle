import translation6
import mysql.connector
import traceback


def translateData(amount):

    translation6.updateThresholds()
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    
    # checking the number of translated data
    countTranslatedData = 0 

    chunksize = 10000
    done = 0

    while done <= amount:
        values =(done, chunksize)
        sql = "SELECT visitId, ipAddress_int FROM `visits` where companyId is null order by visitTime DESC limit %s, %s"
        done += chunksize
        cursor.execute(sql, values)
        data = cursor.fetchall()

    
        for x in data:
    
            countTranslatedData += 1 
            visitId = x[0]
            ipAddress_int = x[1]
            ipAddress = translation6.int2ip(ipAddress_int) 
            print("NEXT IP TO BE TRANSLATED: " + ipAddress + " (" +str(countTranslatedData)+"/"+str(amount)+")")
            
            companyId = translation6.ip2company(ipAddress, False)
            try:
                values = (companyId, visitId)
                sql = "update visits set companyId=%s where visitId=%s"
                cursor.execute(sql, values)
                cnx.commit()
                
            except BaseException as e:
                print("Exception caught while updating visits after IP translation: ", e)
                traceback.print_exc()
    cursor.close()
    cnx.close()

translateData(10000000)