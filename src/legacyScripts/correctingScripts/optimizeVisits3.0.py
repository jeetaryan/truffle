import mysql.connector
from datetime import datetime
from datetime import timedelta
import ipaddress

# connection creating---------------------------------------

cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
#cnx = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")

cursor = cnx.cursor(buffered=True)
cursor2 = cnx.cursor(buffered=True)

# end of connection--------------------------------------

# getting timestamp(pageVisit) from visits table--------------------

cursor.execute("select optimizeVisitsDate from temptable where id=%s", (1,))
row = cursor.fetchone()
startVisitTime = row[0].timestamp()*1000
#10 minutes
chunksize_in_msec=600000
endVisitTime=startVisitTime+chunksize_in_msec

# select first chunk of records
print("selecting first chunk from ", startVisitTime, " to ", endVisitTime)
sql = "SELECT  ipAddress_int, pageVisit from visits where pageVisit >= %s and pageVisit < %s and (source=%s or source=%s) ORDER BY pageVisit"
value = (startVisitTime, endVisitTime, 4, 5)
cursor.execute(sql, value)
records = cursor.fetchall()

#print(datetime.now().timestamp(), " ", startVisitTime)
# print("Data stamp = ", value)
while startVisitTime < datetime.now().timestamp()*1000:
    #process all records in this chunk
    print("len:", len(records))
    for currentRecord in records:

        ipAddress_int = currentRecord[0]
        pageVisit = currentRecord[1]
        
        ########################
        # assign records to dame session
        # We assume all visits with same IP during maxSessionIdleTime belong to the same person.
        # 30 minutes = same as in google analytics
        maxSessionIdleTime = 1800000
        new_final_time = pageVisit + maxSessionIdleTime
        
        sql = "SELECT visitId, pageId, pageVisit, masterVisitId, duration, firstOfSession, sessionDuration, pageVisitorId_dec from visits where ipAddress_int = %s and pageVisit >= %s and pageVisit <= %s and (source=%s or source=%s) order by pageVisit"
        value = (ipAddress_int, pageVisit, new_final_time, 4, 5)
        cursor2.execute(sql, value)
        sessionRecord = cursor2.fetchone()

        ########## Handle Session ###############
        firstOfSession = sessionRecord[5] if sessionRecord[5] else sessionRecord[0]
        sessionDuration = sessionRecord[6] if sessionRecord[6] else 0
        startOfSession = None
        pageVisitorId_dec = None

        # new session 
        if (firstOfSession == sessionRecord[0]):
            # calculate pageVisitorId_dec
            f = str(ipaddress.IPv4Address(ipAddress_int))
            d = f.split('.')
            pageVisitorId_dec = (str(+d[0])+100)+str((+d[1])+100)+str((+d[2])+100)+str((+d[3])+100) + sessionRecord[2] 
            startOfSession = sessionRecord[2]
            
        # existing Session
        else:
            pageVisitorId_dec = sessionRecord[7]
            
            sql = "SELECT pageVisit from visits where visitId=%s"
            values = (firstOfSession, )
            cursor2.execute(sql, value)
            startOfSession = cursor2.fetchone()[0]
            
            

        pageId = sessionRecord[1]
        # wenn Teil eines Visits sessionRecord[3] sonst neuer Visit
        firstOfVisit = sessionRecord[3] if sessionRecord[3] else sessionRecord[0]
        # wenn Teil eines Visits sessionRecord[3] sonst 0
        visitDuration = sessionRecord[4] if sessionRecord[4] else 0 
        # wenn neuer Visit, dann sessionRecord[2] sonst selektieren
        startOfVisit = sessionRecord[2]
        if sessionRecord[3]:
            sql = "SELECT pageVisit from visits where visitId=%s"
            values = (firstOfVisit, )
            cursor2.execute(sql, value)
            startOfVisit = cursor2.fetchone()[0]


        
        ########## Handle Visits that belong to this session ###############    
        while sessionRecord is not None:
            #wenn mastervisitId existiert: ueberspringen!
            if not sessionRecord[3]:
                calcvisitduration = sessionRecord[2] - startOfVisit            
                visitDuration = calcvisitduration if calcvisitduration > visitDuration else visitDuration
                
                calcsessionduration = sessionRecord[2] - startOfSession     
                sessionDuration = calcsessionduration if calcsessionduration > sessionDuration else sessionDuration
                
                cursor2.execute("UPDATE visits set duration=%s, sessionDuration=%s where visitId=%s", (visitDuration, sessionDuration, firstOfVisit))
                cnx.commit()
                    
                # not same page: start new visit-
                if pageId != sessionRecord[1]:
                    pageId = sessionRecord[1]
                    firstOfVisit = sessionRecord[0]
                    visitDuration = 0
                    startOfVisit = sessionRecord[2]
    
                values = (firstOfVisit, visitDuration, firstOfSession, sessionDuration, pageVisitorId_dec, sessionRecord[0])
                cursor2.execute("UPDATE visits set masterVisitId=%s, duration=%s, firstOfSession=%s, sessionDuration=%s, pageVisitorId_dec=%s where visitId=%s", values)
                cnx.commit()

            sessionRecord = cursor.fetchone()
            

    # Update Timestamps for next chunk of records
    startVisitTime = endVisitTime
    endVisitTime = endVisitTime + chunksize_in_msec
    
    storedTimestamp = datetime.fromtimestamp(startVisitTime/1000.0)
    
    #print("new start:", startVisitTime, "new end: ", endVisitTime, "stored:", storedTimestamp)
    cursor.execute("UPDATE temptable set optimizeVisitsDate=%s where id=%s", (storedTimestamp, 1))
    cnx.commit()
    #print("updated")
    
    # Select next chunk of records
    print("selecting next chunk from ", startVisitTime, " to ", endVisitTime)
    sql = "SELECT  ipAddress_int, pageVisit from visits where pageVisit >= %s and pageVisit < %s and (source=%s or source=%s) ORDER BY pageVisit"
    value = (startVisitTime, endVisitTime, 4, 5)
    cursor.execute(sql, value)
    records = cursor.fetchall()

cursor.close()
cnx.close()