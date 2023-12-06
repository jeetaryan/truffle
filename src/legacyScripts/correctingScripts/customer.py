import mysql.connector
import connection

# conn = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
conn = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")

cursor = conn.cursor(buffered=True)
count = 0
cursor.execute("select count from customer where customerId=1")
data = cursor.fetchone()
count = int(''.join(map(str, data)))
for data in connection.jsonData.find().skip(count):
    count += 1
    if not (data.get('client_domain_key') is None):
        client_domain_key = data.get('client_domain_key')
    else:
        client_domain_key = data.get('client_domain_key', '')

    if not (data.get('client_domain_name') is None):
        client_domain_name = data.get('client_domain_name')
        # slit the url
        url = str(''.join(client_domain_name))
        # getting url after removing protocol
        client_domain_name = url.split("://")[1]
    else:
        client_domain_name = data.get('client_domain_name', '')

    # getting pages data from publicIpRecord table
    publicIpRecord = str(data)
    pages = data['pages']
    pagesLength = len(pages)
    if (publicIpRecord == "" or pagesLength == 0):
        print("No record found!!!")
    else:
        for res in range(pagesLength):
            if not (pages[res].get('page_url') is None):
                pageUrl = pages[res].get('page_url')
                # slit the url
                url = str(''.join(pageUrl))
                # getting url after removing parameters
                baseUrl = url.split("?")[0]
                # getting url after removing protocol
                splitUrl = baseUrl.split("://")[1]
                # getting only domain name
                legacy_clientdomainname = splitUrl.split("/")[0]
                # end
            else:
                legacy_clientdomainname = pages[res].get('page_url', '')

            if not (pages[res].get('user_org_id') is None):
                user_org_id = pages[res].get('user_org_id')
            else:
                user_org_id = pages[res].get('user_org_id', '')

    # sql = "select * from customerss where customerName=%s and legacy_client_domain_key =%s and legacy_client_org_id=%s or legacy_clientdomainname=%s"
    # values = (client_domain_name, client_domain_key, user_org_id, legacy_clientdomainname)
    sql = "select * from customer where customerName=%s or legacy_clientdomainname=%s"
    values = (client_domain_name, legacy_clientdomainname)
    cursor.execute(sql, values)
    if (cursor.rowcount > 0):
        print("Data is already into the table!!! rows = ", count, client_domain_name, " ", legacy_clientdomainname)
        sql = "update customer set count=%s where customerId=1"
        values = (count,)
        cursor.execute(sql, values)
        conn.commit()
    else:
        sql = "insert into customer (customerName, legacy_client_domain_key, legacy_client_org_id, legacy_clientdomainname)values(%s,%s,%s,%s)"
        values = (client_domain_name, client_domain_key, user_org_id, legacy_clientdomainname)
        cursor.execute(sql, values)
        conn.commit()
        sql = "update customer set count=%s where customerId=1"
        values = (count,)
        cursor.execute(sql, values)
        conn.commit()
        print("data inserted into customer table!!!")
