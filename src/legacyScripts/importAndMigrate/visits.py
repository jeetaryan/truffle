import mysql.connector
import connection
import ipaddress
from importAndMigrate.ionos import ip, timestamp
from importAndMigrate.gData import device, platform, parameters
from correctingScripts.optimizeVisits3 import ipAddress_int
from ipwhois import IPWhois


# sql connection
# conn = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
conn = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = conn.cursor()





# importiere js_filtered_data
# getting publicIpDone from temptable data
cursor.execute("select jsFilteredDataDone from temptable where id=1")
jsFilteredDataDone = cursor.fetchone()
jsFilteredDataDone = int(''.join(map(str, jsFilteredDataDone)))
for jsfd in connection.jsonFilteredData.find().skip(jsFilteredDataDone):
    ######################## basiscs #######################################
    browser = jsfd.get('browser', '')
    device = jsfd.get('device', '')
    platform = jsfd.get('platform', '')
    protocol = jsfd.get('protocol', '')
    win_height = jsfd.get('win_height', '')
    win_width = jsfd.get('win_width', '')
    
    ######################## IP #######################################
    ip = jsfd.get('ip', '')
    ipAddress_int = str(ipaddress.IPv4Address(ip))
    
    ######################## customerId #######################################
    client_domain_key = jsfd.get('client_domain_key', '')
    customerId = 0
    # t3n hardcoded, because these records are most
    if client_domain_key=="e7a13deb5efc41be":
        customerId = 4
    else:
        #lookup from customer table
        values = (client_domain_key, )
        sql = "SELECT customerId from customer WHERE client_domain_key=%s"
        cursor.execute(sql, values)
        customerId = cursor.fetchone()
        #insert neu customer if it does not exist
        if customerId==None:
            values = (client_domain_key, )
            sql = "INSERT INTO customer(client_domain_key) values(%s)"
            cursor.execute(sql)
            conn.commit()
            customerId = cursor.lastrowid
    
    ######################## nested Pages #######################################
    pages = jsfd.get('pages', '')
    for page in pages:

        pageVisit = page.get('page_visit', '')
        pageTitle = pages[res].get('page_title', '')
        originalUrl = pages[res].get('page_url', '')
        
        parameters = "NULL"
        
        ######################## Normalize URL #######################################
        baseUrl = originalUrl
        urlArray = originalUrl.split("?")
        baseUrlWithProtocol = urlArray[0]
        if len(urlArray)>1:
            parameters = baseUrlWithProtocol = urlArray[1]
        
        urlArray = baseUrlWithProtocol.split("://")
        if len(urlArray)>1:
            protocol = urlArray[0]
            baseUrl = urlArray[1]
        else:
            baseUrl = baseUrlWithProtocol
        
        ######################## lookup url in observed pages #######################################




#todo


        sql = "SELECT pageId from observed_pages where pageUrl='" + b["pageUrl"] + "'"
        sqlConn.execute(sql)
        data = sqlConn.fetchone()
        #app.logger.warn("data is: " + data)
        #sqlConn.close()
        pageId = 0
        if (sqlConn.rowcount > 0):
            pageId = data[0]
            app.logger.warn("existing pageId is: " +  str(pageId))
            
        else:
            values = (b["pageUrl"], b["pageLastModified"], b["pageTitle"])
            #app.logger.warn("2nd SQL")
            #sqlConn = sqlDbCon.cursor()
            sql = "INSERT into observed_pages(pageUrl, pageLastModified, pageTitle) values(%s, %s, %s)"
            sqlConn.execute(sql, values)
            #sqlDbCon.commit()
            pageId = sqlConn.lastrowid
            app.logger.warn("new pageId is: " +  str(pageId))
            sqlDbCon.commit()
            #todo: lookup pageId from observed_pages where baseUrl
            pageId = 

        ######################## split parameters from URL ###########################
        
        utm_source= "NULL"
        utm_campaign= "NULL"
        utm_term= "NULL"
        utm_content= "NULL"
        utm_medium= "NULL"
        gclid= "NULL"
        
        
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

        # get infos on this visit wrt device etc.
        # select/insert into observed_pages:
    customerId
    pageId
    ipAddress_int
    browser
    device 
    platform 
    protocol 
    win_height 
    win_width
    
    parameters
    utm_source
    utm_campaign
    utm_term
    utm_content
    utm_medium
    gclid
    pageVisit
        
    
    
    
        #todo: insert into visits

    publicIpdone_id += 1
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            url = str(''.join(pageUrl))
            # getting url after removing parameters
            baseUrl = url.split("?")[0]
            # getting protocol
            protocol = baseUrl.split("://")[0]
            # getting url after removing protocol
            splitUrl = baseUrl.split("://")[1]
            # getting domain name
            domain = splitUrl.split("/")[0]


            # checking the customer table
            sql_customer = "select customerId from customer where customerName=%s or legacy_clientdomainname=%s"
            value_customer = (domain, domain)
            cursor.execute(sql_customer, value_customer)
            customerID = cursor.fetchone()
            customerID = int(''.join(map(str, customerID)))
            # end

            value_publicRecordId = (publicIpRecord,)
            sql = "SELECT companyId from kickfire where publicIpRecord=%s"
            cursor.execute(sql, value_publicRecordId)
            data = cursor.fetchall()
            count = cursor.rowcount
            companyId = ""

            if (count > 0):
                for x in data:
                    companyId = str(x[0])
                    cursor.execute("SELECT pageId from observed_pages where pageUrl='" + splitUrl + "'")
                    data = cursor.fetchone()
                    pageId = 0
                    if (cursor.rowcount > 0):
                        pageId = data[0]
                        sql = "Update observed_pages set pageTitle=%s where pageId=%s"
                        value = (pageTitle, pageId)
                        cursor.execute(sql, value)
                        conn.commit()

                    else:
                        values = (splitUrl, pageLastModifiedDateTime, pageTitle)
                        sql = "INSERT into observed_pages(pageUrl, pageLastModified, pageTitle) values(%s, %s, %s)"
                        cursor.execute(sql, values)
                        conn.commit()
                        pageId = cursor.lastrowid

                    values = (ipAddress, ipAddress_int, protocol, pageId, pageVisit, companyId, customerID, 3,
                              pageLastModifiedDateTime)
                    sql = "INSERT into visits(ipAddress, ipAddress_int,protocol, pageId, pageVisit, companyId,customerId, source, pageLastModifiedDateTime) " \
                          "values(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, values)
                    conn.commit()
                    lastVisitId = cursor.lastrowid
                    print("Public_Ip_Record matched, Data inserted into visits table!!! Number of migrated record = ",
                          publicIpdone_id)

                    # updating utm Values into visits table
                    special_characters = "?"
                    if any(c in special_characters for c in url):

                        # insert parameters data into visits table
                        parameters = url.split("?")[1]
                        values_parameters = (parameters, lastVisitId)
                        sql_parameters = "update visits set parameters= %s where visitId=%s"
                        cursor.execute(sql_parameters, values_parameters)
                        conn.commit()
                        # end

                        x = parameters.split("&")
                        columns = {"utm_source", "utm_campaign", "utm_term", "utm_context", "utm_medium",
                                   "gclid"}
                        for y in x:
                            asd = y.split("=")
                            length = len(asd)
                            if (length > 1):
                                mydic = {asd[0]: asd[1]}
                                for keys, value in mydic.items():
                                    for col in columns:
                                        if (col == keys):
                                            sql = "UPDATE visits set " + col + " = '" + value + "' where visitId = %s"
                                            value = (lastVisitId,)
                                            cursor.execute(sql, value)
                                conn.commit()
                        # end

            else:
                values = (ipAddress, ipAddress_int, protocol, pageVisit, pageTitle, pageUrl, customerID, 3,
                          pageLastModifiedDateTime)
                sql = "insert into visits (ipAddress, ipAddress_int, protocol, pageVisit, pageTitle, " \
                      "pageUrl, customerId, source, pageLastModifiedDateTime) values(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, values)
                conn.commit()
                print("Un-matched Public_Ip_Record data inserted into visits table !!! Number of migrated record = ",
                      publicIpdone_id)

        sql = "update temptable set publicIpdone = %s where id=1"
        values = (publicIpdone_id,)
        cursor.execute(sql, values)
        conn.commit()
cursor.close()
conn.close()




