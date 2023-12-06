import mysql.connector
import connection
import ipaddress
from ipwhois import IPWhois
import traceback
import json



def ip_to_integer(string_ip):
    try:
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv4Address:
            return int(ipaddress.IPv4Address(string_ip))
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv6Address:
            return int(ipaddress.IPv6Address(string_ip))
    except Exception as e:
        traceback.print_exc()
        return -1

# sql connection
# conn = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
conn = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = conn.cursor(buffered=True)


insertedRowcount = 0
publicIpdone_id = 0
parameters = ""
domain = ""


# getting publicIpDone from temptable data
cursor.execute("select publicIpdone from temptable where id=1")
offset = cursor.fetchone()
offset = int(''.join(map(str, offset)))

print("offset: ", offset)

counter = 0
publicIpRecords = connection.publicIpRecord.find().skip(offset)
all = len(list(publicIpRecords))

print("all: ", all)

#### importiere public IP records (kickfire-response ist das interessante)
for publicData in connection.publicIpRecord.find().skip(offset):
    
    ip =  publicData.get('ip', '')
    json_response_data  = publicData.get('json_response_data', '')
    created_date_time  = publicData.get('created_date_time', '')
    last_modified_date_time  = publicData.get('last_modified_date_time', '')
    
    companyId = 0
    counter += 1
    print("progress: ", counter, "/", all, " (", round(counter*100/all, 2), "%): ", ip)
    
    if (ip!=""):
        ipAddress_int = ip_to_integer(ip)
        ######################## lookup IP in ip ranges #######################################
        #todo
        count = 0
        try:
            value = (ipAddress_int, ipAddress_int )
            sql = "SELECT companyId FROM ip_ranges where ipStart <=%s and ipEnd >= %s"
            cursor.execute(sql, value)
            data = cursor.fetchone()
            count = cursor.rowcount
        except BaseException as e:
            print("Exception caught : ", e)
            traceback.print_exc()
            
        # great! We have figured out the company ID from looking up the IP range
        if (count > 0):
            companyId = data[0]
        
        ######################## insert company #######################################
        else:
            try:
                # inserting data into companies table
                companies_sql = "INSERT into companies Values()"
                cursor.execute(companies_sql)
                
                # returning the last inserted company_id
                companyId = cursor.lastrowid
                conn.commit()
            except BaseException as e:
                print("Exception caught while generating new companyId: ", e)
                traceback.print_exc()
    
            ######################## parse kickfire info #######################################
            
            
            
            try:
                
                datalist = json.loads(json_response_data)
                #print(datalist)
    
                if datalist.get("companyName") !="":
                    if "to" in datalist.get("employees"):   
                        employees_0, employees_1 = datalist.get("employees").replace(" ", "").replace(",", "").split("to")
                    else:
                        employees_0  = datalist.get("employees").replace(" ", "").replace(",", "").replace("+","")
                        employees_1 = 0
                        
                    if "to" in datalist.get("revenue"): 
                        revenue_0, revenue_1 = datalist.get("revenue").replace("$", "").replace(" ", "").replace(",", "").split("to")
                    else:
                        revenue_0 = datalist.get("revenue").replace("$", "").replace(" ", "").replace(",", "").replace("+","")
                        revenue_1 = 0
                    
                    values = (
                        companyId, datalist.get("companyName"), 
                        datalist.get("phone") if datalist.get("phone")!="" else None,
                        datalist.get("employees") if datalist.get("employees")!="" else None,
                        datalist.get("revenue") if datalist.get("revenue")!="" else None,
                        datalist.get("stockSymbol") if datalist.get("stockSymbol")!="" else None,
                        datalist.get("timeZoneId") if datalist.get("timeZoneId")!="" else None,
                        datalist.get("timeZoneName") if datalist.get("timeZoneName")!="" else None,
                        datalist.get("utcOffset") if datalist.get("utcOffset")!="" else None,
                        datalist.get("dstOffset") if datalist.get("dstOffset")!="" else None,
                        datalist.get("isISP") if datalist.get("isISP")!="" else None,
                        datalist.get("isWifi") if datalist.get("isWifi")!="" else None,
                        datalist.get("sicGroup") if datalist.get("sicGroup")!="" else None,
                        datalist.get("sicDesc") if datalist.get("sicDesc")!="" else None,
                        datalist.get("sicCode") if datalist.get("sicCode")!="" else None,
                        datalist.get("naicsGroup") if datalist.get("naicsGroup")!="" else None,
                        datalist.get("naicsDesc") if datalist.get("naicsDesc")!="" else None,
                        datalist.get("naicsCode") if datalist.get("naicsCode")!="" else None,
                        datalist.get("facebook") if datalist.get("facebook")!="" else None,
                        datalist.get("twitter") if datalist.get("twitter")!="" else None,
                        datalist.get("linkedIn") if datalist.get("linkedIn")!="" else None,
                        revenue_0 if revenue_0!="" else None,
                        revenue_1 if revenue_1!="" else None,
                        employees_0 if employees_0!="" else None,
                        employees_1 if employees_1!="" else None)
                    
                    #{'country': 'Spain', 'isISP': 0, 'city': 'Palma', 'companyName': 'Universitat de les Illes Balears', 'latitude': '39.641222', 'sicGroup': 'Educational Services', 'tradeName': 'Universitat de les Illes Balears', 'revenue': '$250,000,000 to $500,000,000', 'twitter': 'UIBuniversitat', 'sicDesc': 'Colleges, Universities, and Professional Schools', 'street': 'km 7.5 Carretera de Valldemossa', 'longitude': '2.645559', 'naicsCode': '611310', 'website': 'uib.cat', 'utcOffset': '+01:00', 'naicsGroup': 'Educational Services', 'countryShort': 'ES', 'timeZoneId': 'Europe/Madrid', 'facebook': 'estudiantsuib', 'confidence': 75, 'regionShort': '', 'dstOffset': 0, 'linkedIn': '391418', 'stockSymbol': '', 'timeZoneName': 'Central European Time', 'phone': '34 971 17 30 00', 'isWifi': 0, 'sicCode': '8221', 'postal': '07122', 'naicsDesc': 'Colleges, Universities, and Professional Schools', 'region': 'Illes Balears', 'employees': '2,500 to 5,000'}
        
                    
                    
                    sql = (
                        "INSERT INTO kickfire (companyId, companyName,  phone, employees, revenue," \
                        " stockSymbol, timeZoneId, timeZoneName, utcOffset, dstOffset, isIsp, isWifi, sicGroup," \
                        " sicDesc, sicCode, naicsGroup, naicsDesc, naicsCode,facebook, twitter, linkedIn,"\
                        " revenue_0, revenue_1, employees_0, employees_1)"\
                        " VALUES(%s,%s, %s,%s,%s, %s,%s,%s,%s, %s,%s,%s, %s,%s, %s, %s,%s,%s,%s,%s,%s, %s,%s,%s,%s)")
                    cursor.execute(sql, values)
                    conn.commit()
        
        
                    # insert into address table
                    if (datalist.get("city") != ""):
                        address_value = (companyId,
                                         datalist.get("city") if datalist.get("city")!="" else None,
                                         datalist.get("country") if datalist.get("country")!="" else None,
                                         datalist.get("postal") if datalist.get("postal")!="" else None,
                                         datalist.get("region") if datalist.get("region")!="" else None,
                                         datalist.get("street") if datalist.get("street")!="" else None,
                                         datalist.get("regionShort") if datalist.get("regionShort")!="" else None,
                                         datalist.get("countryShort") if datalist.get("countryShort")!="" else None,
                                         datalist.get("latitude") if datalist.get("latitude") != '' else None,
                                         datalist.get("longitude") if datalist.get("longitude") != '' else None,
                                         1)
                        address_sql = "INSERT into addresses (companyId,city, country, postal_code,states,line_1,stateShort," \
                                      "countryShort,latitude, longitude, source) values(%s,%s,%s, %s,%s,%s, %s,%s,%s,%s,%s)"
                        cursor.execute(address_sql, address_value)
                        conn.commit()
        
        
            except BaseException as e:
                print("Exception caught while getting kickfire Info and storing in DB: ", e)
                traceback.print_exc()
        
    
    
            ######################## insert IP Range #######################################
            try:
                obj = IPWhois(ip)
                data = obj.lookup_whois()
                data = data['nets']
                for x in data:
                    cidr = x['cidr']
                    name = x['name']
                    handle = x['handle']
                    ipRange = x['range']
                    description = x['description']
                    country = x['country']
                    state = x['state']
                    city = x['city']
                    address = x['address']
                    postal_code = x['postal_code']
                    created = x['created']
                    updated = x['updated']
                    if (ipRange != None):
                        a, b = ipRange.split(" - ")
                        ipStart = ip_to_integer(a)
                        ipEnd = ip_to_integer(b)
                              
                        value = (
                            companyId, ipRange, ipStart, ipEnd, cidr, name, handle, description, country, state, city,
                            address, postal_code, created)
    
                        sql = "INSERT into ip_ranges (companyId, ipRange, ipStart, ipEnd, cidr, name, handle, rangeDescription, " \
                              "country, state, city, address, postal_code, createdDateTime)" \
                              "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                        cursor.execute(sql, value)
                        conn.commit()
            except BaseException as e:
               print("Exception caught while checking whois: ", e)
               traceback.print_exc()
       
    ######################## update counter #######################################
    try:
        sql = "update temptable set publicIpdone = %s where id=1"
        
        values = (counter+offset,)
        cursor.execute(sql, values)
        conn.commit()
    except BaseException as e:
        print("Exception caught while updating counter: ", e)
        traceback.print_exc()

cursor.close()
conn.close()