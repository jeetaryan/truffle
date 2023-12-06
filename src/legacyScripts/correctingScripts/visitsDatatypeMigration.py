'''
Created on 18.08.2022

@author: nikob
'''
import mysql.connector
from user_agents import parse

# sql connection
sqlDb = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlCursor = sqlDb.cursor(buffered=True)
sqlDb2 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlCursor2 = sqlDb2.cursor(buffered=True)

sql="SELECT userAgent, visitId, language FROM visits WHERE customerId=69 and browser_family is NULL;"
sqlCursor.execute(sql)

rows = sqlCursor.fetchall()
all = sqlCursor.rowcount

count=0

for row in rows:   

    # 1. Useragent parsen
    # 2. language korrekt eintragen
    # 3. lookup
    # 4. UPDATE visits set visitTime=FROM_UNIXTIME(pageVisit), os_family=device where visitId=%s
    # 5. altes visits.browser nach browserfamily und browserversion
    # duration auf sec
    # isISP in visits


    langId=None    
    if row[2]:
        lang_code = row[2][0:2]

        #print(lang_code)
    
        if lang_code == "en":
            langId=1
        elif lang_code == "de":
            langId=2
        elif lang_code == "fr":
            langId=3
        elif lang_code == "es":
            langId=4
        elif lang_code == "nl":
            langId=5
        else:
            # retrieving data from languages table on response of visits table------------------
    
            sql = "select langId from languages where code=%s"
            values = (lang_code,)
            sqlCursor2.execute(sql, values)
            data = sqlCursor2.fetchone()
            if data:
                if len(data)>0:
                    langId = data[0]
                    
                    
    user_agent = parse(row[0])
    
    browserversion= None
    try:
        if len(user_agent.browser.version) >0:
            browserversion=user_agent.browser.version[0]
        if len(user_agent.browser.version) > 1:
            browserversion=float(str(user_agent.browser.version[0]) + "." + str(user_agent.browser.version[1]))
    except ValueError:
        browserversion = None    
    
    osversion= None
    try:
        
        if len(user_agent.os.version) >0:
            osversion=user_agent.os.version[0]
        if len(user_agent.os.version) > 1:
            osversion=float(str(user_agent.os.version[0]) + "." + str(user_agent.os.version[1]))
            
        if osversion == "XP":
            osversion=5.1
        elif osversion == "Me":
            osversion=4.9
        elif osversion == "Vista":
            osversion=6.0
        elif osversion == "NT":
            osversion=3.5
        
        val = float(str(osversion))
    except ValueError:
        osversion = None
    
    osfamily = user_agent.os.family
    if len(str(osfamily)) > 32:
        osfamily = str(user_agent.os.family).split(" ")[0]
    
    devicefamily = user_agent.device.family
    if len(str(devicefamily)) > 32:
        devicefamily = str(user_agent.device.family).split(" ")[0]
    
    devicebrand= user_agent.device.brand
    if len(str(devicebrand)) > 32:
        devicebrand = str(user_agent.device.brand).split(" ")[0]
        
    devicemodel= user_agent.device.model
    if len(str(devicemodel)) > 32:
        devicemodel = str(user_agent.device.model).split(" ")[0]
        
    browserfamily= user_agent.browser.family
    if len(str(browserfamily)) > 32:
        browserfamily = str(user_agent.browser.family)[0:32]
    
    
    values= (browserfamily, browserversion, 
    osfamily, osversion, devicefamily, devicebrand,
    devicemodel, user_agent.is_mobile, user_agent.is_tablet, user_agent.is_touch_capable,
    user_agent.is_pc, user_agent.is_bot, int(row[1]))
    print(values)
    sql = "UPDATE visits set browser_family=%s, browser_version=%s, os_family=%s, os_version=%s, device_family=%s, device_brand=%s, device_model=%s, isMobile=%s, isTablet=%s, isTouch=%s, isPc=%s, isBot=%s where visitId=%s"
    sqlCursor2.execute(sql, values)
    sqlDb2.commit()
    count+=1
    print("inserted ", count , " (", count/all*100," %)")
    

sqlCursor.close()
sqlDb.close()
sqlCursor2.close()
sqlDb2.close()



    
    