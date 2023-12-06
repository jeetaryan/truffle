import pandas as pd
import translation6
import mysql.connector

df = pd.read_excel('test.xlsx')


numOfRows = df.shape[0]
numOfCol = df.shape[1]
print("number of rows:", numOfRows)
print("number of columns:", numOfCol)



    
cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)

#todo:
#FileNotFoundError

######################### IDENTIFY COLUMN NAMES #####################
hasContactData = False

companyId = None
contactId = None

for cell in df.columns:
    print("cell value: ", cell)

    values = (clnSpacesAndDashes(cell), )

    #1 lookup columName
    sql = "SELECT tableName, colName, rule FROM importColumnNames WHERE name=%s"
    cursor.execute(sql, values)
    rows = cursor.fetchall()
        
    propositions = ["New custom company field: " + cell]
    sqls = ["INSERT INTO "]
    for row in rows:    
        if row[2] == None:
            propositions.insert(0, row[0]+"."+row[1])
            if row[0]=="contacts":
                hasContactData = True
            pass
        else:
            #todo
            #applyrule
            pass
        
    
    for proposition in propositions:
        
        print(cell, "could be: ", propositions)
    