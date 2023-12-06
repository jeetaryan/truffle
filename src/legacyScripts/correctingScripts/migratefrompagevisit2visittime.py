import mysql.connector
import traceback

cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)





go = 0
deleted=0
chunksize=1000
while go==0:
    try: 
        print("deleting 1000 isp visits of t3n. Done: ", deleted)
        sql = "DELETE from `visits` where exists (SELECT companyId from companies where isISP=%s)  and customerId=%s LIMIT %s"
        values=(1,4, chunksize) 
        cursor.execute(sql, values)
        deleted+=chunksize
        if cursor.rowcount==0:
            go=1
        cnx.commit()
    except BaseException as e:
        print("Exception caught while deleting: ", e)
        go=0;
        traceback.print_exc()

deleted=0
while go==1:
    try: 
        print("migrating pageVisit in millisec. Done: ", deleted)
        sql = "Update visits set visitTime=FROM_UNIXTIME(FLOOR(pageVisit/%s)) where visitTime is null and pageVisit>%s LIMIT %s)" 
        values=(1000,1672441200, chunksize) #31.12.2022
        cursor.execute(sql, values)
        deleted+=chunksize
        if cursor.rowcount==0:
            go=2
        cnx.commit()
    except BaseException as e:
        print("Exception caught while deleting: ", e)
        go=0;
        traceback.print_exc()

deleted=0
while go==2:
    try: 
        print("migrating pageVisit in sec. done:", deleted)
        sql = "Update visits set visitTime=FROM_UNIXTIME(pageVisit) where visitTime is null and pageVisit<=%s LIMIT %s" 
        values=(1672441200, chunksize) #31.12.2022
        cursor.execute(sql, values)
        deleted+=chunksize
        if cursor.rowcount==0:
            go=3
        cnx.commit()
    except BaseException as e:
        print("Exception caught while deleting: ", e)
        go=0;
        traceback.print_exc()

while go==3:
    try: 
        print("updating durationSec")
        sql="UPDATE `visits` set durationSec=FLOOR(duration/%s) where duration is not null AND durationSec is null LIMIT %s;"
        values = (1000, chunksize)
        cursor.execute(sql, values)
        cnx.commit()
        deleted+=chunksize
        if cursor.rowcount==0:
            go=4
    except BaseException as e:
        print("Exception caught while deleting: ", e)
        go=0;
        traceback.print_exc()
    
if go == 4:
    try: 
        #delete indices, columns and add a new one
        print("deleting indices, deleting columns and  adding one new column")
        sql = "ALTER TABLE `visits` DROP INDEX `index_optimizeVisits1`, DROP INDEX `index_optimizeVisits2`, "\
            "ADD `sessionDurationSec` SMALLINT(5) NULL DEFAULT NULL AFTER `duration` "\
            "DROP `status`, DROP `platform`, DROP `protocol`, DROP `isISP`, DROP `status`, DROP `pageVisit`" \
            ", DROP `duration`"
        
        cursor.execute(sql)
        cnx.commit()
    except BaseException as e:
        print("Exception caught while deleting: ", e)
        traceback.print_exc()


cursor.close()
cnx.close()
print("done")