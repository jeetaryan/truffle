import datetime
import socket
import struct
import ipaddress
import traceback
import mysql.connector
from flask import Flask, jsonify, render_template, request, json
from flask_cors import CORS, cross_origin
from user_agents import parse
from translation6 import ip2company



app = Flask(__name__)

CORS(app)


# 0 = normal
# 1 = t3n and aba idle, others run
# 2 = all idle
# 3 = aba is off, others work
idle = 0



@app.route('/targetme')
def targetme(): 
    if idle != 0:
        return ""
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = con.cursor(buffered=True)
    sql="INSERT into campaignRanges(campaignId, customerId, ipStartv4, IpEndv4, active) values(%s, %s, %s, %s, %s)"
    ip = ip_to_integer(str(request.remote_addr))
    values=(1, 76, ip, ip, 1 )
    cursor.execute(sql, values)
    con.commit()
    cursor.close()
    con.close()
    return render_template('targetme.html', ip=str(request.remote_addr))

@app.route('/untargetme')
def untargetme():
    if idle != 0:
        return ""
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = con.cursor(buffered=True)
    sql="DELETE FROM campaignRanges where ipStartv4=%s and IpEndv4=%s;"
    ip = ip_to_integer(str(request.remote_addr))
    values=(ip, ip )
    cursor.execute(sql, values)
    con.commit()
    cursor.close()
    con.close()
    return render_template('untargetme.html', ip=str(request.remote_addr))

@app.route('/lead', methods=['GET', 'POST'])
@cross_origin()
def lead():
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="elgoss")
    cursor = con.cursor(buffered=True)
    sql = "insert into leads(email) values(%s);"
    b = request.get_json()
    values = (b, )
    cursor.execute(sql, values)
    con.commit()
    cursor.close()
    con.close()
    return ""

@app.route('/')
def hello_world(): 
#return 'Hello, World'
    return render_template('index.html')


@app.route('/2')
def hello_world2():
#return 'Hello, World'
    return render_template('index.html')

def ip_to_integer(string_ip):
    try:
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv4Address:
            return int(ipaddress.IPv4Address(string_ip))
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv6Address:
            return int(ipaddress.IPv6Address(string_ip))
    except Exception as e:
        traceback.print_exc()
        return -1

@app.route('/abaclick', methods=['GET', 'POST'])
@cross_origin()
def abaclick():
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = con.cursor(buffered=True)
    
    b = request.get_json()
    print(str(request.remote_addr), " clicked on adId ", b["adId"])
    sql = "UPDATE nativeAds SET clicks = clicks + 1 where campaignDataId = %s"
    values = (b["adId"], )
    cursor.execute(sql, values)
    con.commit()
    cursor.close()
    con.close()
    
    return ""

@app.route('/aba', methods=['GET', 'POST'])
@cross_origin()
def aba():
    if idle != 0:
        return jsonify(mobile="", desktop="")
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = con.cursor(buffered=True)
    
    b = request.get_json()
    ip_string = str(request.remote_addr)
    
    customer = b["customerId"]
    adType = b["adType"]
    

    values= None
    sql = None       
    if "." in ip_string:
        ip_int = ip_to_integer(ip_string)
        sql="select nativeAds.mobile, nativeAds.desktop, nativeAds.campaignDataId from nativeAds "\
            "INNER JOIN campaigns ON nativeAds.campaignId = campaigns.campaignId "\
            "INNER JOIN campaignRanges ON campaignRanges.campaignId = nativeAds.campaignId "\
            "where (campaignRanges.ipStartv4<=%s and campaignRanges.ipEndv4>=%s) "\
            "and nativeAds.type=%s and campaigns.customerId=%s "\
            "and campaignRanges.active=%s and nativeAds.active=%s and campaigns.active=%s "\
            "ORDER BY campaigns.prio LIMIT 1;"
        values=(ip_int, ip_int, adType, customer, 1, 1, 1)
    elif ":" in ip_string:    
        sql="select nativeAds.mobile, nativeAds.desktop, nativeAds.campaignDataId  from nativeAds "\
            "INNER JOIN campaigns ON nativeAds.campaignId = campaigns.campaignId "\
            "INNER JOIN campaignRanges ON campaignRanges.campaignId = nativeAds.campaignId "\
            "where (campaignRanges.ipStartv6<=%s and campaignRanges.ipEndv6>=%s) "\
            "and nativeAds.type=%s and campaigns.customerId=%s "\
            "and campaignRanges.active=%s and nativeAds.active=%s and campaigns.active=%s "\
            "ORDER BY campaigns.prio LIMIT 1;"
        values=(format(ipaddress.IPv6Address(ip_string)), format(ipaddress.IPv6Address(ip_string)), adType, customer, 1, 1, 1)
    else:
        print("no valid IP:", ip_string)
        return "<!-- ABA Error 001 -->"
    cursor.execute(sql, values)
    data = cursor.fetchall()


    if (data):
        #print("campaignDataId=", data[0][2])
        sql = "UPDATE nativeAds SET impressions = impressions + 1 where campaignDataId = %s"
        values = (data[0][2], )
        cursor.execute(sql, values)
        con.commit()
        cursor.close()
        con.close()
        
        nativeAd = jsonify(mobile=data[0][0], desktop=data[0][1], id=data[0][2])
        return nativeAd
    else:
        cursor.close()
        con.close()
        nativeAd = jsonify(mobile="<!-- no campaign applicable -->", desktop="<!-- no campaign applicable -->")
        return nativeAd

@app.route('/visit', methods=['GET', 'POST'])
@cross_origin()
def details():
    if idle == 2:
        return ""
    b = request.get_json()
    if idle == 1 and b["customerId"]==4:
        return ""
    
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = con.cursor(buffered=True)
    sql = "SELECT pageId from observed_pages where pageUrl = %s LIMIT 1"

    cursor.execute(sql, ( str(b["pageUrl"]), ) )
    data = cursor.fetchall()
    pageId = 0

    if (cursor.rowcount>0):
        pageId = data[0][0]
        #app.logger.warn("existing pageId is: " +  str(pageId))
        
    else:
        values = (b["pageUrl"], b["pageLastModified"], b["pageTitle"], b["customerId"])
        #app.logger.warn("insert: "+ b["pageUrl"] + " PageLastmodified:" +  str(b["pageLastModified"]) + " pageTitle: " + b["pageTitle"])
        sql = "INSERT into observed_pages(pageUrl, pageLastModified, pageTitle, customerId) values(%s, %s, %s, %s)"
        
        cursor.execute(sql, values)

        pageId = cursor.lastrowid
        con.commit()
        #app.logger.warn("new pageId is: " +  str(pageId))


    #app.logger.warn(b["device"])
    #app.logger.warn("browser: " + b["browser"])
    #app.logger.warn("recentPageID: " + str(b["recentPageId"]))
    #app.logger.warn("recentDuration: " + str(b["recentDuration"]))
    #app.logger.warn("pageVisitorId: " + str(b["pageVisitorId"]))
    #app.logger.warn(b["ip_int"])
    #app.logger.warn(b["platform"])
    #app.logger.warn(b["protocol"])
    #app.logger.warn(b["referrer"])
    #app.logger.warn(b["userAgent"])
    #app.logger.warn(b["visitTime"])
    #app.logger.warn(b["winHeight"])
    #app.logger.warn(b["winWidth"])
    #app.logger.warn(b["parameters"])
    #app.logger.warn(b["utm_source"])
    #app.logger.warn(b["utm_medium"])
    #app.logger.warn(b["utm_campaign"])
    #app.logger.warn(b["utm_term"])
    #app.logger.warn(b["utm_content"])
    #app.logger.warn(b["gclid"])

    user_agent = parse(b["userAgent"])
    
    lang_code = str(b["language"])[0:2]
    langId=None
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
        cursor.execute(sql, values)
        data = cursor.fetchone()
        if data:
            if len(data)>0:
                langId = data[0]
    
    
    #app.logger.warn("device family " + user_agent.device.family)
    
    browserversion= None
    
    if len(user_agent.browser.version) >0:
        browserversion=user_agent.browser.version[0]
    if len(user_agent.browser.version) > 1:
        browserversion=float(str(user_agent.browser.version[0]) + "." + str(user_agent.browser.version[1]))
        
    osversion= None
    if len(user_agent.os.version) >0:
        osversion=user_agent.os.version[0]
        if osversion=="XP": osversion=5.0
        elif osversion=="Vista": osversion=6.0
        elif osversion=="Me": osversion=4.9
        elif osversion=="NT": osversion=3.5
    if len(user_agent.os.version) > 1:
        osversion=float(str(user_agent.os.version[0]) + "." + str(user_agent.os.version[1]))

    visitTime=int(int(b["visitTime"])/1000)
    
    
    #try to translate by looking up in ip_ranges
    companyId = ip2company(request.remote_addr, False)
    

    values = (companyId, langId, str(b["language"]), str(b["pageVisitorId"]), b["customerId"], \
    ip_to_integer(str(request.remote_addr)), pageId, b["platform"], b["protocol"], b["referrer"], \
    b["userAgent"], visitTime, b["winHeight"], b["winWidth"], b["parameters"], \
    b["utm_source"], b["utm_medium"] , b["utm_campaign"] , b["utm_term"] , b["utm_content"], b["gclid"], 
    str(user_agent.browser.family)[:30], browserversion, 
    str(user_agent.os.family)[:30], osversion, str(user_agent.device.family)[:30], str(user_agent.device.brand)[:30],
    str(user_agent.device.model)[:30], user_agent.is_mobile, user_agent.is_tablet, user_agent.is_touch_capable,
    user_agent.is_pc, user_agent.is_bot, 2)
    

    sql = "INSERT into visits(companyId, langId, language, pageVisitorId_dec, customerId, " \
    "ipAddress_int, pageId, platform, protocol, referrer, userAgent, visitTime, winHeight, winWidth, parameters, utm_source, utm_medium, utm_campaign, utm_term, utm_content, gclid, " \
    "browser_family, browser_version, os_family, os_version, device_family, device_brand, device_model, isMobile, isTablet, isTouch, isPc, isBot, source) " \
    "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    

    cursor.execute(sql, values)
    con.commit()

    ##### assign this visiting company to the customer
    sql = "SELECT type from customer where customerId=%s"
    values = (b["customerId"], )
    cursor.execute(sql, values)
    sqlResult = cursor.fetchall()
    if sqlResult is not None and len(sqlResult)>0:
        type = sqlResult[0][0]

        if type == 0 and companyId is not None:
            try:
                # we update one column to get lastModifiedOn updated automatically
                sql = '''INSERT into companies_customers(customerId, companyId, source) values (%s, %s, %s)
                ON DUPLICATE KEY UPDATE companyId=%s'''
                values = (b["customerId"], companyId, 1, companyId)
                cursor.execute(sql, values)
                con.commit()
            except BaseException:
                pass

    ###### update duration of recent visit (the one before this one) assuming the user left the page of recent visit
    if (b["recentPageId"] != 0 and b["recentPageId"] != None):
        
        duration = int(int(b["recentDuration"])/1000)
        duration = min(duration, 65535)
        duration = max(0, duration)
        values =  (duration, b["recentPageId"], b["pageVisitorId"])
        sql = "UPDATE visits set durationSec = %s where pageId = %s and pageVisitorId_dec = %s"
        cursor.execute(sql, values)
        con.commit()

    cursor.close()
    con.close()
    return (str(pageId))

@app.route('/heartbeat', methods=['GET', 'POST'])
@cross_origin()
def heartbeat():
    if idle == 2:
        return ""
    b = request.get_json()
    if idle == 1 and b["customerId"]==4:
        return ""
    
    con = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = con.cursor(buffered=True)
    #app.logger.warn("scrolldepth: " + str(b["scrollDepth"]))

    if "pageVisitorId" in b:

       
        scrolldepth = min(float(b["scrollDepth"]), 100)
        scrolldepth = max(0, scrolldepth)
        
        duration = int(int(b["duration"])/1000)
        duration = min(duration, 65535)
        duration = max(0, duration)


          
        values =  (scrolldepth, duration, b["pageId"], b["pageVisitorId"])
        sql = "UPDATE visits set scrollDepth = %s, durationSec = %s where pageId = %s and pageVisitorId_dec = %s"

        cursor.execute(sql, values)
        con.commit()
    cursor.close()
    con.close()
    return ("")


@app.route("/my_ip", methods=["GET"])
@cross_origin()
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200

if __name__ == '__main__':
    app.run()
