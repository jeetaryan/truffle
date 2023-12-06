import sys
import translation6
import mysql.connector
import traceback
import datetime as dt
#from translation6 import linkedin2companyByProxycurl, chooseBestFirmographics


# 2023-01-25: Built to recover pc firmographics that have been overwritten by "Unauthorized" when we have used a wrong PC credential
def correctPCUnauthorized():
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    sql = "SELECT linkedin, companyId from companies where companyName=%s"
    values = ("unauthorized",)
    cursor.execute(sql, values)
    data = cursor.fetchall()

    for x in data:
        result = linkedin2companyByProxycurl(x[0], int(x[1]))
        chooseBestFirmographics(x[1])
    print("done")

def translateForBusinessesRecentMin(recentMinutes):
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    sql = "SELECT customerId FROM `customer` where type=%s and active=%s"
    values = (0, 1)
    cursor.execute(sql, values)
    data = cursor.fetchall()

    for x in data:
        translateRecentMin(recentMinutes, x[0])
    cursor.close()
    cnx.close() 
    
def translateRecentMin(recentMinutes, customerId):
    translation6.updateThresholds()
    countTranslatedData = 0

    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)

    try:
        sql = "SELECT type from customer where customerId=%s"
        values = (customerId,)
        cursor.execute(sql, values)
        sqlResult = cursor.fetchall()
        customerType = 1
        if sqlResult is not None and len(sqlResult) > 0:
            customerType = sqlResult[0][0]

        endTime = dt.datetime.now()
        startTime = endTime - dt.timedelta(minutes=recentMinutes)

        #todo: ipv6 support
        sql = '''SELECT visitId, ipAddress_int FROM `visits` 
            where companyId is null and customerId= %s and visitTime>%s
            order by visitTime ASC'''
        values = (customerId, startTime)
        cursor.execute(sql, values)
        amount = cursor.rowcount

        data = cursor.fetchall()
        if amount>0:
            print("Customer:", customerId, ":", amount, "visits to be translated")
            for x in data:
                countTranslatedData += 1
                visitId = x[0]
                ipAddress_int = x[1]
                ipAddress = translation6.int2ip(ipAddress_int)

                companyId = translation6.ip2company(ipAddress, True)


                values = (companyId, visitId)
                sql = "update visits set companyId=%s where visitId=%s"
                cursor.execute(sql, values)
                cnx.commit()

                if customerType == 0 and companyId is not None:
                    # we update one column to get lastModifiedOn updated automatically
                    sql = '''INSERT into companies_customers(customerId, companyId, source) values (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE companyId=%s'''
                    values = (customerId, companyId, 1, companyId)
                    cursor.execute(sql, values)
                    cnx.commit()

            print(endTime, ": Translated", countTranslatedData, " visits since", startTime)

    except BaseException as e:
        print("Exception caught while updating visits after IP translation: ", e)
        traceback.print_exc()
    cursor.close()
    cnx.close()        

def translateData(amount):
    translation6.updateThresholds()
    countTranslatedData = 1 

    chunksize = 10000
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    
    while countTranslatedData <= amount:
        values =(amount, )
        #todo: ipv6 support
        sql = "SELECT visitId, ipAddress_int FROM `visits` where companyId is null order by visitTime DESC limit %s"
        cursor.execute(sql, values)
        data = cursor.fetchall()
    
        for x in data:
    
             
            visitId = x[0]
            ipAddress_int = x[1]
            ipAddress = translation6.int2ip(ipAddress_int) 
            print("-------------------------------------------------------------------------------------------------------------------------------------------------")
            print("---------------------------------------------------NEXT IP TO BE TRANSLATED )" + ipAddress + "------------------------------------------------------")
            print("---------------------------------------------------"+str(countTranslatedData)+"/"+str(amount)+"--------------------------------------------------------------")
            
            companyId = translation6.ip2company(ipAddress, True)
    
            
            try:
                values = (companyId, visitId)
                sql = "update visits set companyId=%s where visitId=%s"
                cursor.execute(sql, values)
                cnx.commit()
                
            except BaseException as e:
                print("Exception caught while updating visits after IP translation: ", e)
                traceback.print_exc()
            countTranslatedData += 1
    cursor.close()
    cnx.close()            

def updateCompanies():
    translation6.updateThresholds()
    sql = "SELECT companyId FROM companies a "\
          "WHERE  NOT EXISTS (SELECT * FROM   kickfire b WHERE  a.companyId = b.companyId) " \
          "AND NOT EXISTS (SELECT * FROM   proxycurl c WHERE  a.companyId = c.company_ID);"
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql)
    data = cursor.fetchall()
    
    for x in data:
        companyId = x[0]
        print("companyId " + str(companyId))
        values = (companyId, )
        sql = "select ipAddress_int from visits where companyId=%s LIMIT 1;"
        cursor.execute(sql, values)
        ipoutput = cursor.fetchall()
        print (ipoutput)
        if cursor.rowcount>0:
            ipAddress_int = ipoutput[0][0]
            print("ip " + str(ipAddress_int))
            ipAddress = translation6.int2ip(ipAddress_int)
            
            
            #if not (ip2companyByProxycurl(ipAddress, companyId)):
            #    ip2companyByKickfire(ipAddress, companyId)
            translation6.ip2companyByIpInfo(ipAddress, companyId)
        else:
            translation6.deleteCompanyAndVisits(companyId)
    cursor.close()
    cnx.close()



def unifyCompanies():
    sql = "SELECT count(*) as anzahl, companyId, companyName FROM companies kf Group by kf.companyName order by anzahl desc;"
    
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    for row in rows:
        companyId = row[1]
        companyName = row[2]
        
        sql = "SELECT companyId from companies where companyName=%s and companyId<>%s order by createdOn DESC"
        values = (companyName, companyId)
        cursor.execute(sql)
        dublicates = cursor.fetchall()
        
        for dublicate in dublicates:
            dubId = dublicate[0]
            values = (companyId, dubId)
            sql = "UPDATE visits set companyId=%s where companyId=%s"
            cursor.execute(sql, values)
            cnx.commit()
            
            translation6.deleteCompanyWithoutVisits(dubId)
    cursor.close()
    cnx.close()

    
    

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
        except BaseException as e:
            print("Exception caught while updating visits after IP translation: ", e)
            traceback.print_exc()

#updateCompanies()
#unifyCompanies()
#translateData(4000)


#print(sys.argv)
if len(sys.argv)>1:
   translateRecentMin(int(sys.argv[1]), int(sys.argv[2]))
else:
   translateForBusinessesRecentMin(1)
