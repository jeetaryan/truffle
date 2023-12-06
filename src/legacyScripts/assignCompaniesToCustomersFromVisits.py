import mysql.connector
import datetime

con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = con.cursor(buffered=True)



sql = '''SELECT customerId, customerName from customer where type!=%s ORDER BY customerId DESC'''
values = (1,)
cursor.execute(sql, values)
customers = cursor.fetchall()

end = datetime.datetime(2023,6,1,16,00)

for c in customers:
    print("-----------------------------------------------------------------------------------------")
    visitId = 0
    go = True
    while go == True:
        sql = '''
            SELECT DISTINCT companyId, visitId, createdOn from visits
            WHERE customerId=%s and createdOn<%s and visitId>%s and companyId is not NULL LIMIT 1000
            '''
        values = (c[0], end, visitId)
        cursor.execute(sql, values)
        sqlResult = cursor.fetchall()
        print("Assigning", len(sqlResult), "companies to customer", c[1], "(", c[0],")")
        if sqlResult is None or len(sqlResult) == 0:
            go = False
        for a in sqlResult:
            sql = '''INSERT into companies_customers(customerId, companyId, source, createdOn, lastModifiedOn)
                values (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE lastModifiedOn=%s
                '''
            values = (c[0], a[0], 1, a[2], a[2], a[2])
            cursor.execute(sql, values)
            con.commit()
            visitId = a[1]
cursor.close()
con.close()