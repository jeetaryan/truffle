import mysql.connector
import time

# sql connection
# sqlDbCon = mysql.connector.connect(host="localhost", user="root", password="", database="proj_welva")
sqlDbCon = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlConn = sqlDbCon.cursor()

sql = "SELECT UNIQUE pageUrl from observed_pages"
sqlConn.execute(sql)
data = sqlConn.fetchall()

for row in data:
    sql = "SELECT pageId from observed_pages where pageUrl=\"" + row[0] + "\""
    #values=(row[0],)
    #print(sql)
    sqlConn.execute(sql)
    data2 = sqlConn.fetchall()
    masterId = 0
    #print("observed page dublicates: ", len(data2))
    for row2 in data2:
        if len(data2) > 1:
            if masterId==0:
                masterId = row2[0];
                print("masterId set to ", masterId)
            else:
                sql = "UPDATE visits set pageId=" + str(masterId) + " Where pageId=" + str(row2[0])
                print(sql)
                sqlConn.execute(sql)
                sqlDbCon.commit()

                sql = "DELETE FROM tags_observed_pages where pageId=" + str(row2[0])
                print(sql)
                sqlConn.execute(sql)
                sqlDbCon.commit()

                sql = "DELETE FROM observed_pages where pageId=" + str(row2[0])
                print(sql)
                sqlConn.execute(sql)
                sqlDbCon.commit()

        else:
                print(".", end='', flush=True)
sqlConn.close()
sqlDbCon.close()
