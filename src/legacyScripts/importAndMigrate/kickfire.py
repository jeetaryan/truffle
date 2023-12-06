import json
import connection
import datetime

# counting rows
connection.sqlConn.execute("SELECT * FROM kickfire")
connection.sqlConn.fetchall()
rowSkip = connection.sqlConn.rowcount
insertedRowcount = 0
for publicData in connection.publicIpRecord.find().skip(rowSkip):

    if not (publicData.get('_id') is None):
        publicIpRecord = publicData.get('_id')
    else:
        publicIpRecord = publicData.get('_id', '')
    publicIpRecord = str(publicIpRecord)
    # getting jsonResponseData from publicIpRecord table
    if (publicIpRecord == ""):
        print("No record found!!!")
    else:

        # inserting data into compnies table
        companies_values = (datetime.datetime.now(),)
        companies_sql = "INSERT into companies(created_on)Values(%s)"
        connection.sqlConn.execute(companies_sql, companies_values)
        connection.sqlDbCon.commit()
        # end

        # returning the last inserted company_id
        get_company_id_sql = "SELECT companyId from companies order by companyId desc limit 1"
        get_company_id = connection.sqlConn.execute(get_company_id_sql)
        comp_id = connection.sqlConn.fetchone()
        company_data_id = comp_id[0]
        # end

        jsonResponse = publicData.get('json_response_data')
        publicData = json.loads(jsonResponse)
        if not (publicData.get('country') is None):
            country = publicData.get('country')
        else:
            country = publicData.get('country', '')
        if not (publicData.get('isISP') is None):
            isISP = publicData.get('isISP')
        else:
            isISP = publicData.get('isISP', '')
        if not (publicData.get('city') is None):
            city = publicData.get('city')
        else:
            city = publicData.get('city', '')
        if not (publicData.get('companyName') is None):
            companyName = publicData.get('companyName')
        else:
            companyName = publicData.get('companyName', '')
        if not (publicData.get('latitude') is None):
            latitude = publicData.get('latitude')
        else:
            latitude = publicData.get('latitude', '')
        if not (publicData.get('sicGroup') is None):
            sicGroup = publicData.get('sicGroup')
        else:
            sicGroup = publicData.get('sicGroup', '')
        if not (publicData.get('tradeName') is None):
            tradeName = publicData.get('tradeName')
        else:
            tradeName = publicData.get('tradeName', '')
        if not (publicData.get('revenue') is None):
            revenue = publicData.get('revenue')
        else:
            revenue = publicData.get('revenue', '')
        if not (publicData.get('sicDesc') is None):
            sicDesc = publicData.get('sicDesc')
        else:
            sicDesc = publicData.get('sicDesc', '')
        if not (publicData.get('street') is None):
            street = publicData.get('street')
        else:
            street = publicData.get('street', '')
        if not (publicData.get('longitude') is None):
            longitude = publicData.get('longitude')
        else:
            longitude = publicData.get('longitude', '')
        if not (publicData.get('naicsCode') is None):
            naicsCode = publicData.get('naicsCode')
        else:
            naicsCode = publicData.get('naicsCode', '')
        if not (publicData.get('website') is None):
            website = publicData.get('website')
        else:
            website = publicData.get('website', '')
        if not (publicData.get('utcOffset') is None):
            utcOffset = publicData.get('utcOffset')
        else:
            utcOffset = publicData.get('utcOffset', '')
        if not (publicData.get('naicsGroup') is None):
            naicsGroup = publicData.get('naicsGroup')
        else:
            naicsGroup = publicData.get('naicsGroup', '')
        if not (publicData.get('timeZoneId') is None):
            timeZoneId = publicData.get('timeZoneId')
        else:
            timeZoneId = publicData.get('timeZoneId', '')
        if not (publicData.get('facebook') is None):
            facebook = publicData.get('facebook')
        else:
            facebook = publicData.get('facebook', '')
        if not (publicData.get('regionShort') is None):
            regionShort = publicData.get('regionShort')
        else:
            regionShort = publicData.get('regionShort', '')
        if not (publicData.get('dstOffset') is None):
            dstOffset = publicData.get('dstOffset')
        else:
            dstOffset = publicData.get('dstOffset', '')
        if not (publicData.get('linkedIn') is None):
            linkedIn = publicData.get('linkedIn')
        else:
            linkedIn = publicData.get('linkedIn', '')
        if not (publicData.get('stockSymbol') is None):
            stockSymbol = publicData.get('stockSymbol')
        else:
            stockSymbol = publicData.get('stockSymbol', '')
        if not (publicData.get('timeZoneName') is None):
            timeZoneName = publicData.get('timeZoneName')
        else:
            timeZoneName = publicData.get('timeZoneName', '')
        if not (publicData.get('phone') is None):
            phone = publicData.get('phone')
        else:
            phone = publicData.get('phone', '')
        if not (publicData.get('isWifi') is None):
            isWifi = publicData.get('isWifi')
        else:
            isWifi = publicData.get('isWifi', '')
        if not (publicData.get('sicCode') is None):
            sicCode = publicData.get('sicCode')
        else:
            sicCode = publicData.get('sicCode', '')
        if not (publicData.get('postal') is None):
            postal = publicData.get('postal')
        else:
            postal = publicData.get('postal', '')
        if not (publicData.get('naicsDesc') is None):
            naicsDesc = publicData.get('naicsDesc')
        else:
            naicsDesc = publicData.get('naicsDesc', '')
        if not (publicData.get('region') is None):
            region = publicData.get('region')
        else:
            region = publicData.get('region', '')
        if not (publicData.get('employees') is None):
            employees = publicData.get('employees')
        else:
            employees = publicData.get('employees', '')
        value_kickfire = (
            company_data_id, publicIpRecord, country, isISP, city, companyName, latitude, sicGroup, tradeName, revenue,
            sicDesc, street, longitude, naicsCode, website, utcOffset, naicsGroup, timeZoneId, facebook, regionShort,
            dstOffset, linkedIn, stockSymbol, timeZoneName, phone, isWifi, sicCode, postal, naicsDesc, region,
            employees)
        sql_kickfire = ("INSERT INTO kickfire(companyId,publicIpRecord,country, isISP, city, companyName, latitude, sicGroup,"
                        " tradeName, revenue, sicDesc, street, longitude, naicsCode, website, utcOffset, naicsGroup,"
                        " timeZoneId,facebook, regionShort, dstOffset, linkedIn, stockSymbol, timeZoneName, phone, isWifi,"
                        " sicCode, postal, naicsDesc, region, employees)"
                        "VALUES (%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,"
                        " %s,%s,%s,%s,%s,%s)")
        connection.sqlConn.execute(sql_kickfire, value_kickfire)
        connection.sqlDbCon.commit()
        # end

        # count inserted number of row
        connection.sqlConn.execute("SELECT * FROM kickfire")
        connection.sqlConn.fetchall()
        insertedRowcount = connection.sqlConn.rowcount
        # end
        print("Inserted kickfire data ", insertedRowcount)
