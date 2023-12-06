import connection
import socket
import struct
import os
import sys
import ciso8601
import time
import traceback


directory = os.fsencode("./ionos/")

cursor = connection.sqlDbCon.cursor(buffered=True)


for filename in os.listdir(directory):
     with open(os.path.join(directory, filename)) as file:
        print("importing file: ", file)
        Lines = file.readlines()

        count = 0
        for line in Lines:
            col = line.split("|")
            t = col[0]
            ts = ciso8601.parse_datetime(t)
            timestamp = round(time.mktime(ts.timetuple()))
            ionos2 = col[1]
            ionos3 = col[2]
            ionos4 = col[3]
            ionos5 = col[4]
            ip = col[5]
            userAgent = col[6]
            language = col[7]
            if len(col)>9:
                referrer = col[8]
                if len(referrer)>1998:
                    referrer=referrer[:1998]
                pageUrl = col[9]
            else:
                referrer = "null"
                pageUrl = col[8]
                
            ipAddress_int = struct.unpack("!I", socket.inet_aton(col[5]))[0]

            baseUrl=pageUrl
            utm_source="null"
            utm_campaign="null"
            utm_term="null"
            utm_content="null"
            utm_medium="null"
            gclid="null"
            protocol="null"
            parameters="null"
            pageId="null"
            
            try:
                pageUrlSplit=pageUrl.split("://")
                
                if len(pageUrlSplit)>1:
                    protocol = pageUrlSplit[0]
                    uri = pageUrlSplit[1]
                    uriSplit = uri.split("?")
                    if len(uriSplit) >1:
                        baseUrl = uriSplit[0]
                        parameters = uriSplit[1]
                        params = parameters.split("&")
                        for param in params:
                            paramSplit=param.split("=")
                            key=paramSplit[0]
                            if len(paramSplit)>1:
                                value=paramSplit[1]
                                if key == "utm_source":
                                    utm_source=value
                                elif key == "utm_campaign":
                                    utm_campaign=value
                                elif key == "utm_term":
                                    utm_term=value
                                elif key == "utm_content":
                                    utm_content=value
                                elif key == "utm_medium":
                                    utm_medium=value
                                elif key == "gclid":
                                    gclid=value
            except BaseException as e:
                print("Exception caught : ", e)
                traceback.print_exc()

            #get companyId and isBots assignment from old record
            values=(ipAddress_int, timestamp)
            sql="SELECT companyId, isBot, visitId, customerId FROM visits WHERE ipAddress_int=%s AND pageVisit=%s and customerId=4"
            #print(sql, values)
            cursor.execute(sql, values)
            row = cursor.fetchone()

            companyId=row[0]
            isBot=row[1]
            visitId=row[2]
            customerId=row[3]

            #get pageId if existing
            values = (baseUrl, )
            sql="SELECT pageId FROM observed_pages WHERE pageUrl=%s"
            #print(sql, values)
            cursor.execute(sql, values)
            row = cursor.fetchone()
            if row != None:
                pageId=str(row[0])
            else:
                values = (baseUrl, )
                sql = "INSERT INTO observed_pages(pageUrl) values(%s)"
                #print(sql, values)
                connection.sqlConn.execute(sql, values)
                pageId = str(connection.sqlConn.lastrowid)

            values = (timestamp, ionos2, ionos3, ionos4, ionos5, ip, ipAddress_int, userAgent, language, referrer, pageUrl, companyId, isBot, 70, protocol, utm_source, utm_campaign, utm_term, utm_content, utm_medium, gclid, parameters, 1, customerId, pageId)
            sql = "INSERT into visits (pageVisit, ionos_import_2, ionos_import_3, ionos_import_4, " \
             "ionos_import_5, ipAddress, ipAddress_int, userAgent, language, referrer, pageUrl, companyId, isBot, status, " \
             "protocol, utm_source, utm_campaign, utm_term, utm_content, utm_medium, gclid, parameters, source, customerId, pageId) " \
             "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            print("Inserting visitID=", connection.sqlConn.lastrowid, " in place of ", visitId)
            connection.sqlConn.execute(sql, values)

            #mark old record
            values=(visitId, )
            sql="UPDATE visits set status=60 where visitId=%s"
            #print("updated. ", visitId)
            cursor.execute(sql, values)
            #print("")

            
            
            connection.sqlDbCon.commit()


cursor.close()
connection.sqlDbCon.close()
