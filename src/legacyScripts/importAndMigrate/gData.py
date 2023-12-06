import mysql.connector
import connection
import ipaddress
from mysql.connector import Error

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


insertedRowcount = 0
jsondatadone = 0
parameters = ""
domain = ""

# getting publicIpDone from temptable data
cursor.execute("select gdatadone  from temptable where id=1")
gdatadone = cursor.fetchone()
gdatadone = int(''.join(map(str, gdatadone)))
# end


for publicData in connection.jsonData.find({"client_domain_key": "bed0c3ca58f04380"}).skip(gdatadone):
    try:
        if not (publicData.get('_id') is None):
            publicRecordId = publicData.get('_id')
        else:
            publicRecordId = publicData.get('_id', '')

        if not (publicData.get('ip') is None):
            ipAddress = publicData.get('ip')
            ipAddress_int = ip_to_integer(ipAddress)
            ip_length = len(str(ipAddress_int))
            if (ip_length > 15):
                ipAddress_int = 0
            else:
                ipAddress_int = ipAddress_int
        else:
            ipAddress = publicData.get('ip', '')
            ipAddress_int = 0

        if not (publicData.get('browser') is None):
            browser = publicData.get('browser')
        else:
            browser = publicData.get('browser', '')

        if not (publicData.get('device') is None):
            device = publicData.get('device')
        else:
            device = publicData.get('device', '')

        if not (publicData.get('platform') is None):
            platform = publicData.get('platform')
        else:
            platform = publicData.get('platform', '')

        if not (publicData.get('win_height') is None):
            win_height = publicData.get('win_height')
        else:
            win_height = publicData.get('win_height', '')

        if not (publicData.get('win_width') is None):
            win_width = publicData.get('win_width')
        else:
            win_width = publicData.get('win_width', '')

        if not (publicData.get('user_org_id') is None):
            user_org_id = publicData.get('user_org_id')
        else:
            user_org_id = publicData.get('user_org_id', '')

        if not (publicData.get('protocol') is None):
            protocol = publicData.get('protocol')
        else:
            protocol = publicData.get('protocol', '')

        if not (publicData.get('last_modified_date_time') is None):
            pageLastModifiedDateTime = publicData.get('last_modified_date_time')
        else:
            pageLastModifiedDateTime = publicData.get('last_modified_date_time', '')

        if not (publicData.get('client_domain_key') is None):
            client_domain_key = publicData.get('client_domain_key')
        else:
            client_domain_key = publicData.get('client_domain_key', '')

        # getting pages data from publicIpRecord table
        publicIpRecord = str(publicRecordId)
        pages = publicData['pages']
        pagesLength = len(pages)
        gdatadone += 1
        if (publicIpRecord == "" or pagesLength == 0):


            values = (
                ipAddress, ipAddress_int, protocol, browser, device, platform, win_height, win_width, user_org_id,
                4, client_domain_key, domain, pageLastModifiedDateTime)
            sql = "INSERT into visits(ipAddress, ipAddress_int,protocol,browser, device, platform," \
                  " winHeight, winWidth, user_org_id, source,client_domain_key, client_domain_name, pageLastModifiedDateTime) " \
                  "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s, %s, %s)"
            cursor.execute(sql, values)
            conn.commit()
            lastVisitId = cursor.lastrowid
            print("added=", jsondatadone)

        else:
            for res in range(pagesLength):

                if not (pages[res].get('page_visit') is None):
                    pageVisit = pages[res].get('page_visit')
                else:
                    pageVisit = pages[res].get('page_visit', '')

                if not (pages[res].get('page_title') is None):
                    pageTitle = pages[res].get('page_title')
                else:
                    pageTitle = pages[res].get('page_title', '')

                if not (pages[res].get('last_modified_date_time') is None):
                    pageLastModifiedDateTime = pages[res].get('last_modified_date_time')
                else:
                    pageLastModifiedDateTime = pages[res].get('last_modified_date_time', '')

                if not (pages[res].get('page_url') is None):
                    pageUrl = pages[res].get('page_url')
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
                    sql_customer = "select customerId from customer where legacy_client_domain_key=%s"
                    value_customer = (client_domain_key,)
                    cursor.execute(sql_customer, value_customer)
                    customerID = cursor.fetchone()
                    customer_count = cursor.rowcount
                    if (customer_count > 0):
                        customerID = int(''.join(map(str, customerID)))
                    else:
                        sql = "insert into customer (customerName, legacy_client_domain_key, legacy_client_org_id, legacy_clientdomainname)values(%s,%s,%s,%s)"
                        values = (domain, client_domain_key, user_org_id, domain)
                        cursor.execute(sql, values)
                        conn.commit()
                        customerID = cursor.lastrowid
                    # end
                else:
                    pageUrl = pages[res].get('page_url', '')
                    customerID = 0

                # check if page already exists in observed pages or insert new record
                cursor.execute("SELECT pageId from observed_pages where pageUrl='" + splitUrl + "'")
                data = cursor.fetchone()
                pageId = 0
                if (cursor.rowcount > 0):
                    pageId = data[0]
                    sql = "Update observed_pages set pageTitle=%s, pageLastModified=%s where pageId=%s"
                    value = (pageTitle, pageLastModifiedDateTime, pageId)
                    cursor.execute(sql, value)
                    conn.commit()
                else:
                    values = (splitUrl, pageLastModifiedDateTime, pageTitle)
                    sql = "INSERT into observed_pages(pageUrl, pageLastModified, pageTitle) values(%s, %s, %s)"
                    cursor.execute(sql, values)
                    conn.commit()
                    pageId = cursor.lastrowid

                # updating utm Values into visits table
                utm_source = ""
                utm_campaign = ""
                utm_term = ""
                utm_content = ""
                utm_medium = ""
                gclid = ""
                parameters = ""

                special_characters = "?"

                if any(c in special_characters for c in url):
                    # insert parameters data into visits table
                    parameters = url.split("?")[1]

                    x = parameters.split("&")

                    for y in x:
                        asd = y.split("=")
                        length = len(asd)
                        if (length > 1):
                            if asd[0] == "utm_source":
                                utm_source = asd[1]
                            elif asd[0] == "utm_campaign":
                                utm_campaign = asd[1]
                            elif asd[0] == "utm_term":
                                utm_term = asd[1]
                            elif asd[0] == "utm_content":
                                utm_content = asd[1]
                            elif asd[0] == "utm_medium":
                                utm_medium = asd[1]
                            elif asd[0] == "gclid":
                                gclid = asd[1]
                        # end
                # then we add the visists record along with the pageId
                values = (pageId, ipAddress, ipAddress_int, protocol, pageVisit,
                          browser, device, platform, win_height, win_width, user_org_id, 4, customerID,
                          utm_source, utm_campaign, utm_term, utm_content, utm_medium, gclid, parameters,
                          client_domain_key, domain)
                sql = "INSERT into visits(pageId, ipAddress, ipAddress_int, protocol, pageVisit," \
                      "browser, device, platform, winHeight, winWidth, user_org_id, source, customerId," \
                      "utm_source, utm_campaign, utm_term, utm_content, utm_medium, gclid, parameters, client_domain_key, client_domain_name) " \
                      "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, values)
                lastVisitId = cursor.lastrowid

        # update counter
        sql = "update temptable set gdatadone = %s where id=1"
        values = (gdatadone,)
        cursor.execute(sql, values)
        conn.commit()
        print("added=", gdatadone, " visitId=", lastVisitId)

    except Error as e:
        print("Error while connecting to MySQL", e)
        conn.rollback()
if conn.is_connected():
    cursor.close()
    conn.close()
    print("MySQL connection is closed")
