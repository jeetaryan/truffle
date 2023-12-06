import mysql.connector
import traceback

cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)

sql = "SELECT companyId, employees, revenue  FROM `kickfire` where (employees_0 is null or employees_1 is null or revenue_0 is null or revenue_1 is null)"

cursor.execute(sql)
data = cursor.fetchall()

for x in data:
    try:
        companyId=x[0]
        employees=x[1]
        revenue=x[2]
        
        employees_0=0
        employees_1=0
        revenue_0=0
        revenue_1=0
        
        if "to" in employees:   
            employees_0, employees_1 = employees.replace(" ", "").replace(",", "").split("to")
        elif employees=="":
            employees_0  = 0
            employees_1 = 0
        else:
            employees_0  = employees.replace(" ", "").replace(",", "").replace("+","")
            employees_1 = 0
            
        if "to" in revenue: 
            revenue_0, revenue_1 = revenue.replace("$", "").replace(" ", "").replace(",", "").split("to")
        elif revenue=="":
            revenue_0  = 0
            revenue_1 = 0
        else:
            revenue_0 = revenue.replace("$", "").replace(" ", "").replace(",", "").replace("+","")
            revenue_1 = 0
        
        print("split ", employees, " into ", employees_0, " and ", employees_1)
        print("split ", revenue, " into ", revenue_0, " and ", revenue_1)

        values = (employees_0, employees_1,	revenue_0, revenue_1, companyId)
        sql = "UPDATE kickfire set employees_0=%s, employees_1=%s,	revenue_0=%s, revenue_1=%s where companyId=%s"
        cursor.execute(sql, values)
        cnx.commit()
    except BaseException as e:
        print("Exception caught while updateing all records with same IP: ", e)
        traceback.print_exc() 
