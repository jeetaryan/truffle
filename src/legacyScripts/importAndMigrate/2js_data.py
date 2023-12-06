import mysql.connector
import ipaddress
from mysql.connector import Error
import traceback
import smtplib, ssl
from datetime import timedelta
from datetime import datetime
import pymongo

#indicates the month to be processed
month = 2

#testmode does not delete and insert
testmode = 0


# sql connection
# conn = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
conn = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = conn.cursor(buffered=True)


def ip_to_integer(string_ip):
    try:
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv4Address:
            return int(ipaddress.IPv4Address(string_ip))
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv6Address:
            return int(ipaddress.IPv6Address(string_ip))
    except Exception as e:
        return -1


source = 4

# getting offset from temptable data

cursor.execute("select jsDataDone, jsDataFound, jsDataNotFound, jsDataLimitDate, offsetThisDay  from temptable where id=%s", (month, ))

data = cursor.fetchone()
offset = int(data[0])
found=int(data[1])
notfound=int(data[2])

# upper limit for each iteration
limitDate =data[3]

# lower limit for this iteration, always one day below limitDate
startDate = limitDate - timedelta(hours=1)

# absolute end of this script
endDate = datetime.fromisoformat("2022-0" + str(month+1) + "-01")
offsetThisDay=int(data[4])


mongoDB = pymongo.MongoClient("mongodb://welwa-prod-user:NYBVMyfePoDQQBK3@3.68.198.104:27017/myFirstDatabase?authSource=admin&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&directConnection=true&ssl=false")
client = mongoDB['WelwaMsTriggerNativeScript']
coll = client["js_data"]

with mongoDB.start_session() as session:

    while limitDate<=endDate:
    
        print("offset:", offset, "found:", found, "Not found:", notfound, "offsetThisDay:", offsetThisDay, "limitDate:", limitDate)
        
        #Zeitverschiebung um 2 Stunden beruecksichtigen
        #{"$and" : [ {"created_dateTime" : { "$lt" : ISODate("2022-07-03 16:00:00") }}, {"created_dateTime" : { "$gte" : ISODate("2022-07-03 15:00:00") }}]}
        records = coll.find({"$and" : [ {"created_dateTime" : { "$lt" : limitDate }}, {"created_dateTime" : { "$gte" : startDate }}]}, no_cursor_timeout=True, batch_size=20, session=session).skip(offsetThisDay)
        
        lengthOfThisIteration = len(list(records))
        print("------------------------- ITERATION STARTED. records >=", startDate, "and <", limitDate ,"lengthOfThisIteration:", lengthOfThisIteration, "---------------------------------")
        
        for jsfd in coll.find({"$and" : [ {"created_dateTime" : { "$lt" : limitDate }}, {"created_dateTime" : { "$gte" : startDate }}]}, no_cursor_timeout=True, batch_size=20, session=session).skip(offsetThisDay):
            
            if testmode:
                print("ping")
                offset+=lengthOfThisIteration
                break
            else:
                ######################## IP #######################################
                ip = jsfd.get("ip") if jsfd.get("ip")!="" else None
                if ip and len(ip)<=15:
                    ipAddress_int = ip_to_integer(ip)
                    
                    ######## try to look up company ID from RIPE Records ###################
                    companyId=None
                    #print("IP: ", ip, "progress:", round(offset*100/all, 2), "%")
                    try:
                        values = (ipAddress_int, ipAddress_int)
                        sql = "SELECT companyId FROM ip_ranges where ipStart <=%s and ipEnd >= %s"
                        cursor.execute(sql, values)
                        data = cursor.fetchone()
                        if (cursor.rowcount>0):
                            companyId = data[0]
                            found+=1
                        else:
                            notfound +=1
                    except BaseException as e:
                        print("Exception caught : ", e)
                        traceback.print_exc()
                        
                    
                    ######################## basics #######################################
                    browser = jsfd.get("browser") if jsfd.get("browser")!="" else None
                    device = jsfd.get("device") if jsfd.get("device")!="" else None
                    platform = jsfd.get("platform") if jsfd.get("platform")!="" else None
                    win_height = jsfd.get("win_height") if jsfd.get("win_height")!="" else None
                    win_width = jsfd.get("win_width") if jsfd.get("win_width")!="" else None
                    protocol = jsfd.get("protocol") if jsfd.get("protocol")!="" else None
                    
                    ######################## customerId #######################################
                    client_domain_key = jsfd.get("client_domain_key") if jsfd.get("client_domain_key") != '' else None
                    customerId = None
                    
                    # t3n hardcoded, because these records are most
                    if client_domain_key=="e7a13deb5efc41be":
                        customerId = 4
                    elif client_domain_key=="bed0c3ca58f04380":
                        customerId = 74
                    else:
                        #lookup from customer table
                        values = (client_domain_key, )
                        sql = "SELECT customerId from customer WHERE client_domain_key=%s"
                        cursor.execute(sql, values)
                        data = cursor.fetchone()
                        
                        if (cursor.rowcount>0):
                            customerId = data[0]
                        else:
                            values = (client_domain_key, )
                            sql = "INSERT INTO customer(client_domain_key) values(%s)"
                            cursor.execute(sql,values)
                            conn.commit()
                            customerId = cursor.lastrowid
                    
                    ######################## nested Pages #######################################
                    pages = jsfd.get("pages") if jsfd.get("pages")!="" else None
                    for page in pages:
                        
                        pageVisit = page.get("page_visit") if page.get("page_visit")!="" else None
                        pageTitle = page.get("page_title") if page.get("page_title")!="" else None
                        originalUrl = page.get("page_url") if page.get("page_url")!="" else None
                        
                        ######################## Normalize URL #######################################
                        baseUrlWithProtocol = originalUrl
                        
                        parameters = None
                        urlArray = originalUrl.split("?")
                        if len(urlArray)>1:
                            baseUrlWithProtocol = urlArray[0]
                            parameters = urlArray[1]
                        
                        baseUrl = baseUrlWithProtocol
                        urlArray = baseUrlWithProtocol.split("://")
                        if len(urlArray)>1:
                            protocol = urlArray[0]
                            baseUrl = urlArray[1]
                        
                        ######################## lookup url in observed pages #######################################
                        values = (baseUrl, )
                        sql = "SELECT pageId from observed_pages where pageUrl=%s"
                        cursor.execute(sql, values)
                        data = cursor.fetchone()
                        pageId = 0
                        if (cursor.rowcount > 0):
                            pageId = data[0]
                            
                        else:
                            values = (baseUrl, pageTitle)
                            sql = "INSERT into observed_pages(pageUrl, pageTitle) values(%s, %s)"
                            cursor.execute(sql, values)
                            pageId = cursor.lastrowid
                            conn.commit()
            
                
                        ######################## split parameters from URL ###########################
                        
                        utm_source= None
                        utm_campaign= None
                        utm_term= None
                        utm_content= None
                        utm_medium= None
                        gclid= None
                        
                        if parameters:
                            x = parameters.split("&")
                            for y in x:
                                asd = y.split("=")
                                if (len(asd) > 1):
                                    if asd[0]=="utm_source":
                                        utm_source=asd[1]
                                    elif asd[0]=="utm_medium":
                                        utm_medium=asd[1]
                                    elif asd[0]=="utm_campaign":
                                        utm_campaign=asd[1]
                                    elif asd[0]=="utm_term":
                                        utm_term=asd[1]
                                    elif asd[0]=="utm_content":
                                        utm_content=asd[1]
                                    elif asd[0]=="gclid":
                                        gclid=asd[1]                         
                
                        ######################## insert into visitsL ###########################
                        try:
                            values=(
                                companyId, ipAddress_int, customerId, pageId, pageVisit,
                                win_height, win_width, browser, device, platform, protocol, parameters, utm_source, 
                                utm_medium, utm_campaign, utm_term, utm_content, gclid, source)
                
                            sql = "INSERT into visits(companyId, ipAddress_int, customerId, pageId, pageVisit, " \
                                  "winHeight, winWidth, browser, device, platform, protocol, parameters, utm_source, " \
                                  "utm_medium, utm_campaign, utm_term, utm_content, gclid, source) " \
                                  "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                
                            cursor.execute(sql, values)
                            conn.commit()
                        except BaseException as e:
                            print("Exception caught : ", e)
                            traceback.print_exc()

            # Periodically (after 2500 records each) refresh the session to keep it and the cursor alive
            if (offset/2500 == 0):
                client.admin.command('refreshSessions', [session.session_id], session=session)
        
            ######################## update temptable ###########################
            offset += 1
            offsetThisDay +=1
            
            sql = "update temptable set jsDataDone = %s, jsDataFound = %s, jsDataNotFound = %s, offsetThisDay=%s where id=%s"
            values = (offset, found, notfound, offsetThisDay, month)
            cursor.execute(sql, values)
            conn.commit()
        
    
        print("deleting records >=", startDate, "and <", limitDate)
        if not testmode:
            coll.delete_many({"$and" : [ {"created_dateTime" : { "$lt" : limitDate }}, {"created_dateTime" : { "$gte" : startDate }}]})
        
        startDate = limitDate
        limitDate += timedelta(hours=1)
        
        offsetThisDay =0
        sql = "update temptable set jsDataLimitDate=%s, offsetThisDay=%s where id=%s"
        values = (limitDate, offsetThisDay, month)
        cursor.execute(sql, values)
        conn.commit()
    
cursor.close()
conn.close()

