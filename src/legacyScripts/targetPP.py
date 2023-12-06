import mysql.connector

cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)

sql = '''select ipStartv4, ipEndv4 from ip_ranges where companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s OR companyId=%s'''
values = (74, 88, 83, 183, 185, 198, 207, 213, 278, 405, 416, 432, 440, 443, 463, 469, 479, 508, 511, 514, 538, 556, 559, 583, 605, 630, 652, 654, 675, 684, 682, 703, 694, 709, 717, 724, 736, 98910, 98862, 58610, 58617, 58621, 58613, 58635, 58645, 58479)

cursor.execute(sql, values)
resultdata = cursor.fetchall()
for range in resultdata:
    values = (23, 4, range[0], range[1], 1)
    cursor.execute("INSERT INTO `campaignRanges` (`campaignId`, `customerId`, `ipStartv4`, `ipEndv4`, `active`) VALUES (%s, %s, %s,%s, %s)", values)
    cnx.commit()