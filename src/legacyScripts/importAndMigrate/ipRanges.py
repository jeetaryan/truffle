import connection
from mysql.connector import Error

try:
    # cursor = connection.sqlDbCon.cursor(buffered=True)

    if connection.sqlDbCon.is_connected():
        connection.sqlConn.execute("SELECT * FROM ip_ranges")
        connection.sqlConn.fetchall()
        rowSkip = connection.sqlConn.rowcount
        count = 0
        publicIpRecord = ""
        insertedRowcount = 0
        for publicData in connection.ripeLookup.find().skip(rowSkip):

            if not (publicData.get('public_ip_record') is None):
                publicIpRecord = publicData.get('public_ip_record')
            else:
                publicIpRecord = publicData.get('public_ip_record', '')

            # getting jsonResponseData from publicIpRecord table
            publicIpRecord = str(publicIpRecord)
            if (publicIpRecord == ""):
                print("No record found!!!")
            else:
                if not (publicData.get('ip_range') is None):
                    ip_range = publicData.get('ip_range')
                else:
                    ip_range = publicData.get('ip_range', '')

                if not (publicData.get('start_ip_address') is None):
                    start_ip_address = publicData.get('start_ip_address')
                else:
                    start_ip_address = publicData.get('end_ip_address', '')

                if not (publicData.get('end_ip_address') is None):
                    end_ip_address = publicData.get('end_ip_address')
                else:
                    end_ip_address = publicData.get('end_ip_address', '')

                if not (publicData.get('ripe_description') is None):
                    ripe_description = publicData.get('ripe_description')
                else:
                    ripe_description = publicData.get('ripe_description', '')

                if not (publicData.get('ripe_org') is None):
                    ripe_org = publicData.get('ripe_org')
                else:
                    ripe_org = publicData.get('ripe_org', '')

                if not (publicData.get('ripe_netname') is None):
                    ripe_netname = publicData.get('ripe_netname')
                else:
                    ripe_netname = publicData.get('ripe_netname', '')

                if not (publicData.get('ripe_emailDomain') is None):
                    ripe_emailDomain = publicData.get('ripe_emailDomain')
                else:
                    ripe_emailDomain = publicData.get('ripe_emailDomain', '')

                if not (publicData.get('ripe_address') is None):
                    ripe_address = publicData.get('ripe_address')
                else:
                    ripe_address = publicData.get('ripe_address', '')

                if not (publicData.get('created_date_time') is None):
                    created_date_time = publicData.get('created_date_time')
                else:
                    created_date_time = publicData.get('created_date_time', '')

                if not (publicData.get('last_modified_date_time') is None):
                    last_modified_date_time = publicData.get('last_modified_date_time')
                else:
                    last_modified_date_time = publicData.get('last_modified_date_time', '')

                if not (publicData.get('active') is None):
                    active = publicData.get('active')
                else:
                    active = publicData.get('active', '')

                if not (publicData.get('deleted') is None):
                    deleted = publicData.get('deleted')
                else:
                    deleted = publicData.get('deleted', '')

                if not (publicData.get('_class') is None):
                    _class = publicData.get('_class')
                else:
                    _class = publicData.get('_class', '')

                ripepublicIpRecord = (publicIpRecord,)
                sql = "SELECT * from kickfire where publicIpRecord=%s"
                connection.sqlConn.execute(sql, ripepublicIpRecord)
                data = connection.sqlConn.fetchall()
                count = connection.sqlConn.rowcount
                companyId = ""
                if (count > 0):
                    for x in data:
                        companyId = x[0]
                        companyId = str(companyId)
                    value_ipRanges = (
                    companyId, ip_range, start_ip_address, end_ip_address, publicIpRecord, ripe_org, ripe_description,
                    ripe_netname, ripe_emailDomain, ripe_address, created_date_time, last_modified_date_time, active, deleted,
                    _class)
                    sql_ipRanges = ("INSERT into ip_ranges (companyId,ipRange,ipStart, ipEnd, publicIpRecord, rangeOrg,"
                                    " rangeDescription, rangeNetname, rangeEmailDomain, rangeAddress, createdDateTime,"
                                    " lastModifiedDateTime, active, deleted, _class) "
                                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")

                    connection.sqlConn.execute(sql_ipRanges, value_ipRanges)
                    connection.sqlDbCon.commit()
                    # end
                    # count inserted row into table
                    connection.sqlConn.execute("SELECT * FROM ip_ranges")
                    connection.sqlConn.fetchall()
                    insertedRowcount = connection.sqlConn.rowcount
                    print("Data inserted into ipRanges table!!! Inserted row numbers =", insertedRowcount)
                    # end
except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.sqlDbCon.is_connected():
        connection.sqlConn.close()
        connection.sqlDbCon.close()
        print("MySQL connection is closed")

