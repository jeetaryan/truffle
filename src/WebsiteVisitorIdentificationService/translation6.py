#!/usr/bin/python
# coding: iso-8859-1

import datetime as dt
from datetime import datetime
from datetime import date, timedelta
from time import sleep
import time
import requests
import mysql.connector
from flask import json
import ipaddress
import traceback
from warnings import filterwarnings
import urllib.parse
from ipwhois import IPWhois
import re
import phonenumbers
import email_normalize
from netaddr import *
import traceback
import tldextract
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from Screenshot import Screenshot
from PIL import Image


filterwarnings(action="ignore")

#API keys
pcKey = 'ipW9Gdbl0mWW3iwHjnXvCg'
ipiKey = "ef809b112a5aa8"
kfKey="9645d43f79582ce1"

#shall we lookup ip ranges only (0) or even use rd party APIs to add new ones (1)?
addnewcompanies=1

#cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
#cursor = cnx.cursor(buffered=True)
#cnx2 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
#cursor2 = cnx2.cursor(buffered=True)
#cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
#cursor3 = cnx3.cursor(buffered=True)


########################################################## QUOTA MANAGEMENT ###################################################################
countKickfireData = 50
countProxycurlData = 50
kickfire_max = None
proxycurl_min = None
translatedDataDone =None
currentCreditProxycurl = None
currentUsagekickfire = None

def updateThresholds():
    #print("     - update thresholds")
    ############# Read Limits from Database
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute("SELECT kickfire_max, proxycurl_min, translatedDataDone, currentCreditProxycurl,"
                   "currentUsagekickfire from temptable where id=%s LIMIT %s", (1, 1))
    x = cursor.fetchall()[0]
    cursor.close()
    cnx.close()
    global countKickfireData, countProxycurlData, kickfire_max, proxycurl_min, translatedDataDone, currentCreditProxycurl, currentUsagekickfire
    kickfire_max = x[0]
    proxycurl_min = x[1]
    translatedDataDone = x[2]
    currentCreditProxycurl = x[3]
    currentUsagekickfire = x[4]

def mayWeQueryKickfire():
    #print("     - check kf threshold")
    updateThresholds()
    global countKickfireData, countProxycurlData, kickfire_max, proxycurl_min, translatedDataDone, currentCreditProxycurl, currentUsagekickfire

    #update limits for Kickfire
    if ( countKickfireData >= 50):
        #print("     - check kf API to get latest credit")
        try:
            endDate = datetime.today()
            startDate = datetime.today().replace(day=1)
            response = requests.get("https://api.kickfire.com/usage?key=9645d43f79582ce1&sdate=" + str(startDate) + "&edate=" + str(endDate)).json()
            #print(response)
            currentUsagekickfire = int(response.get("totalQueries"))
            #print("total queries KF: " + str(currentUsagekickfire) + " kickfire_max = " + str(kickfire_max))
            # update temptable.currentCreditProxycurl
            sql = "update temptable set currentUsagekickfire=%s where id=%s"
            value = ( currentUsagekickfire,1)
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(sql, value)
            cnx.commit()
            cursor.close()
            cnx.close()
            countKickfireData = 0
        except BaseException as e:
            print("Exception caught while checking ProxyCurl Credits: ", e)
            traceback.print_exc()
    if ( kickfire_max <  currentUsagekickfire):
        print('no kf credit')
        return 0
    else:
        #print("enough kf credit")
        return 1

def mayWeQueryProxycurl():
    #print("     - check pc threshold")
    updateThresholds()
    # checking the limit of hitting proxycurl
    global countKickfireData, countProxycurlData, kickfire_max, proxycurl_min, translatedDataDone, currentCreditProxycurl, currentUsagekickfire

    if ( countProxycurlData >= 50):
        #print("     - check pc API to get latest credit")
        try:
            api_endpoint = 'https://nubela.co/proxycurl/api/credit-balance'
            header_dic = {'Authorization': 'Bearer ' + pcKey}
            response = requests.get(api_endpoint, headers=header_dic, timeout=60)
            res = response.json()
            #print(res)
            currentCreditProxycurl = int(res.get("credit_balance"))
            # update temptable.currentCreditProxycurl
            sql = "update temptable set currentCreditProxycurl=%s where id=%s"
            value = ( currentCreditProxycurl,1)
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(sql, value)
            cnx.commit()
            cursor.close()
            cnx.close()
            countProxycurlData = 0
        except BaseException as e:
            print("Exception caught while checking ProxyCurl Credits: ", e)
            traceback.print_exc()
    if ( proxycurl_min > currentCreditProxycurl):
        print("no PC credits")
        return 0
    else:
        return 1

def mayWeQueryIpInfo():
    #todo
    return 1

########################################################## IP 2 company ###################################################################

def ip2company(ipAddress, queryApisIfUnknown):
    companyId = None
    if (ipAddress != "" and ipAddress != None):
        #print("Checking companyId for IP: ", ipAddress)

        sql = None
        values = None
        if "." in ipAddress:
            ipAddress_int = ip2int(ipAddress)
            sql = "SELECT companyId FROM ip_ranges where ipStartv4 <=%s and ipEndv4 >= %s LIMIT %s"
            values = (ipAddress_int, ipAddress_int, 1)
        elif ":" in ipAddress:
            sql = "SELECT companyId FROM ip_ranges where ipStartv6 <=%s and ipEndv6 >= %s LIMIT %s"
            values = (format(ipaddress.IPv6Address(ipAddress)), format(ipaddress.IPv6Address(ipAddress)), 1)             
        else:
            return companyId
        
        try:
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(sql, values)
            data = cursor.fetchone()
            count = cursor.rowcount
            
            if (count > 0):
                #great! existing company!
                companyId = data[0]
                print("   - Case 1: looked up companyID from IP-Ranges: ", companyId)
            elif (queryApisIfUnknown):
                print("   - Case 1: cannot lookup ip: ", ipAddress)
                # seems we have a visit from a company where we do not have the IP range

                # try to use Proxycurl
                # if not possible use IPInfo and enrich with Proxycurl.
                # if not successful, use Kickfire
                
                companyId = ip2companyByProxycurl(ipAddress)
                
                if companyId == None:
                    companyId = ip2companyByIpInfo(ipAddress)
                
                    if companyId != None:
                        linkedin2companyByProxycurl(domain2linkedin(companyId2Domain(companyId)), companyId)
                        
                #we have cancelled our kickfire account 2023-01-25
                #if companyId == None:
                    #    companyId = ip2companyByKickfire(ipAddress)
                    
                if companyId != None:
                    chooseBestFirmographics(companyId)
                    updateIpRangesByWhoIs(ipAddress, companyId)
                    updateIpRangesByIpi(None, companyId, False)
            cursor.close()
            cnx.close()
        except BaseException as e:
            print("Exception caught during IP translation: ", e)
            traceback.print_exc()
    return companyId


def ip2companyByKickfire(ipAddress):
    print("     - Query KF")
    companyId = None
    global countKickfireData
    if  mayWeQueryKickfire():
        try:
            print("     - query KF API")
            countKickfireData += 1
            response = requests.get(f'https://api.kickfire.com/v3/company:(all)?ip={ipAddress}&key={kfKey}').json()
            #print("response from KF:", response)
            if response['status'] == "success":
                datalist = response['data'][0]
    
                employees = clnContinuumInt(datalist.get("employees"))
                revenue = clnContinuumFloat(datalist.get("revenue"))
                name = cln(datalist.get("companyName"))
                domain = datalist.get("website")
                
                
                companyId = getCompanyId(name, domain)
                if companyId == None: companyId = generateNewCompanyId(name)
                insertWebsite(companyId, domain, 0)
                print("   - Case 3: company identified by KF:", name, domain, "(companyId:", companyId, ")")
                
                #insert into kickfire            
                values = (
                    companyId, name, cln(datalist.get("tradeName")), clnPhone(datalist.get("phone"), datalist.get("countryShort")), employees[2],
                    revenue[2], cln(datalist.get("stockSymbol")), cln(datalist.get("timeZoneId")),
                    cln(datalist.get("timeZoneName")), cln(datalist.get("utcOffset")), cln(datalist.get("dstOffset")),
                    cln(datalist.get("isISP")), cln(datalist.get("isWifi")), cln(datalist.get("isMobile")), cln(datalist.get("sicCode")), cln(datalist.get("naicsCode")), cln(datalist.get("facebook")),
                    cln(datalist.get("twitter")), cln(datalist.get("linkedIn")), revenue[0], revenue[1], employees[0], employees[1],
                    companyId, name, cln(datalist.get("tradeName")), clnPhone(datalist.get("phone"), datalist.get("countryShort")), employees[2],
                    revenue[2], cln(datalist.get("stockSymbol")), cln(datalist.get("timeZoneId")),
                    cln(datalist.get("timeZoneName")), cln(datalist.get("utcOffset")), cln(datalist.get("dstOffset")),
                    cln(datalist.get("isISP")), cln(datalist.get("isWifi")), cln(datalist.get("isMobile")), cln(datalist.get("sicCode")), cln(datalist.get("naicsCode")), cln(datalist.get("facebook")),
                    cln(datalist.get("twitter")), cln(datalist.get("linkedIn")), revenue[0], revenue[1], employees[0], employees[1])

                sql = "INSERT INTO kickfire (companyId, companyName, tradeName, phone, employees, revenue," \
                    " stockSymbol, timeZoneId, timeZoneName, utcOffset, dstOffset, isIsp, isWifi, isMobile, " \
                    " sicCode,  naicsCode, facebook, twitter, linkedIn,"\
                    " revenue_0, revenue_1, employees_0, employees_1)"\
                    " VALUES(%s,%s, %s,%s,%s, %s,%s,%s, %s,%s, %s,%s,%s, %s,%s, %s, %s,%s,%s,%s,%s,%s, %s)"\
                    " ON DUPLICATE KEY UPDATE companyId=%s, companyName=%s, tradeName=%s, phone=%s, employees=%s, revenue=%s," \
                    " stockSymbol=%s, timeZoneId=%s, timeZoneName=%s, utcOffset=%s, dstOffset=%s, isIsp=%s, isWifi=%s, isMobile=%s, " \
                    " sicCode=%s,  naicsCode=%s, facebook=%s, twitter=%s, linkedIn=%s,"\
                    " revenue_0=%s, revenue_1=%s, employees_0=%s, employees_1=%s;"
                cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                cursor = cnx.cursor(buffered=True)
                cursor.execute(sql, values)
                cnx.commit()
                cursor.close()
                cnx.close()
                
                # insert into address table
                #ompanyId, line_1, line_2, postal_code, city, country, country_short, state, state_short, is_hq, lat, lon):
                insertAddress(companyId, datalist.get("street"), None, datalist.get("postal"), datalist.get("city"), 
                              datalist.get("country"), datalist.get("countryShort"), datalist.get("region"), datalist.get("regionShort"), 
                              None, datalist.get("latitude"), datalist.get("longitude"))
                
                insertWebsite(companyId, domain, 1)
                linkedin2companyByProxycurl(cln(datalist.get("linkedIn")), companyId)
        except BaseException as e:
                print("Exception caught while getting kickfire Info and storing in DB: ", e)
                traceback.print_exc()
    return companyId

def ip2companyByIpInfo(ipAddress):
    print("     - query IPI by IP")
    companyId=None
    global countIpInfoData

    if (ipAddress != "" and ipAddress != None and  mayWeQueryIpInfo()):
        try:
            api_endpoint = "https://ipinfo.io/" + ipAddress + "/json?token=" + ipiKey
            response = requests.get(api_endpoint)
            res = response.json()
            
            print(res)
            company = res.get("company")
            if company != None and company != "":
                name = cln(company.get("name"))
                domain = clnWebsite(company.get("domain"))
                
                companyId = getCompanyId(name, domain)
                if companyId == None: companyId = generateNewCompanyId(name)
                insertWebsite(companyId, domain, 0)
                
                type = cln(company.get("type"))
                isIsp = 1 if type == "isp"  else 0
                
                values = (companyId, name, type, isIsp, companyId, name, type, isIsp)
                print("   - Case 4: IPI queried: ", name, "(", domain, ")")
                
                sql = "INSERT INTO companyIpInfo (companyId, companyName, companyType, isIsp)"\
                    " VALUES(%s,%s, %s,%s) ON DUpLICATE key UPDATE companyId=%s, companyName=%s, companyType=%s, isIsp=%s"
                cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                cursor = cnx.cursor(buffered=True)
                cursor.execute(sql, values)
                cnx.commit() 
                cursor.close()
                cnx.close()
                                
                #  todo: ipi schickt noch andere Dasten (z.B. die Domains, die auf der IP-Adresse gehostet sind. Die muessen aber nicht die gleiche Firma sein.). Man koennte mal ueberlegen, ob die Daten wertvoll sind
                insertWebsite(companyId, domain, 4)
        except BaseException as e:
            print("Exception caught while triggering IPI with IP: ", e)
            traceback.print_exc()
    return companyId
      
def ip2companyByProxycurl(ipAddress):
    print("     - Query PC")
    companyId = None
    global countProxycurlData
    if mayWeQueryProxycurl():
        try:
            print("     - query PC API")
            api_endpoint = 'https://nubela.co/proxycurl/api/reveal/company'
            
            header_dic = {'Authorization': 'Bearer ' + pcKey}
            params = {
                'resolve_numeric_id': 'true',
                'categories': 'include',
                'funding_data': 'include',
                'extra': 'include',
                'exit_data': 'include',
                'acquisitions': 'include',
                'use_cache': 'if-present',
                'ip': ipAddress
            }
            response = requests.get(api_endpoint, params=params, headers=header_dic, timeout=60)
            # counting the value of hitting the proxycurl api
            countProxycurlData += 1
            
            companyId = processProxyCurl(response, False, None)
            if companyId:
                print("   - Case 2: ProxyCurl successfully queried") 
            else:
                print("   - Case 2: Bad result from Proxycurl reveal.") 

        except BaseException as e:
            print("Exception caught while fetching from Proxycurl reveal or storing in DB: ", e)
            traceback.print_exc()
    return companyId

def processProxyCurl(http_response, liid, companyId):
    #liid=1 if response is coming from liid lookup, else:0
    print("     - processing proxycurl response")
    
    try:
        res = http_response.json()
        #print("response from pc:", res)
        if not liid:
            res = res.get("company")
        
        
        if (res):
            name = cln(res.get("name"))
            if name == "Not Found":
                return None 
            else:       
                # ---- simple data types ---
                linkedin_internal_id = cln(res.get("linkedin_internal_id"))
                description = cln(res.get("description"))
                industry = cln(res.get("industry"))
                company_size_on_linkedin = clnInt(res.get("company_size_on_linkedin"))
                company_type = cln(res.get("company_type"))
                founded_year = clnInt(res.get("founded_year"))
                tagline = cln(res.get("tagline"))
                universal_name_id = clnInt(res.get("universal_name_id"))
                profile_pic_url = clnWebsite(res.get("profile_pic_url"))
                background_cover_image_url = clnWebsite(res.get("background_cover_image_url"))
                search_id = clnInt(res.get("search_id"))
                follower_count = clnInt(res.get("follower_count"))
    
                # for the time being we just dump theses values into the DB
                #print("A") if a > b else print("B")
                similar_companies = None if res.get("similar_companies") == None else str(res.get("similar_companies"))[1:-1]
                updates = None if res.get("updates") == None else str(res.get("updates"))[1:-1]
                acquisitions = None if res.get("acquisitions") == None else str(res.get("acquisitions"))[1:-1]
                exit_data = None if res.get("exit_data") == None else str(res.get("exit_data"))[1:-1]
                funding_data = None if res.get("funding_data") == None else str(res.get("funding_data"))[1:-1]
                
                # Company Size
                company_size = res.get("company_size")
                company_size_0 = None
                company_size_1 = None
                if (company_size):
                    company_size_0 = clnInt(company_size[0])
                    company_size_1 = clnInt(company_size[1])
    
                
                # extra
                extra_ipo_status = None
                extra_crunchbase_rank = None
                extra_operating_status = None
                extra_company_type = None
                extra_contact_email = None
                extra_phone_number = None
                extra_facebook_id = None
                extra_twitter_id = None
                extra_number_of_funding_rounds = None
                extra_total_funding_amount = None
                extra_stock_symbol = None
                extra_number_of_lead_investors = None
                extra_number_of_investors = None
                extra_total_fund_raised = None
                extra_number_of_investments = None
                extra_number_of_lead_investments = None
                extra_number_of_exits = None
                extra_number_of_acquisitions = None
                extra_ipo_date_date = None
                extra_founding_date_date = None
                
                extra = res.get("extra")
                if (extra):
                    extra_ipo_status = cln(extra.get("ipo_status"))
                    extra_crunchbase_rank = clnInt(extra.get("crunchbase_rank"))
                    extra_operating_status = cln(extra.get("operating_status"))
                    extra_company_type = cln(extra.get("company_type"))
                    extra_contact_email = clnEmail(extra.get("contact_email"))
                    hq_country = cln(res.get("hq").get("country")) if res.get("hq") else None
                    extra_phone_number = clnPhone(extra.get("phone_number"), hq_country)
                    extra_facebook_id = cln(extra.get("facebook_id"))
                    extra_twitter_id = cln(extra.get("twitter_id"))
                    extra_number_of_funding_rounds = clnInt(extra.get("number_of_funding_rounds"))
                    extra_total_funding_amount = clnInt(extra.get("total_funding_amount"))
                    extra_stock_symbol = cln(extra.get("stock_symbol"))
                    extra_number_of_lead_investors = clnInt(extra.get("number_of_lead_investors"))
                    extra_number_of_investors = clnInt(extra.get("number_of_investors"))
                    extra_total_fund_raised = clnInt(extra.get("total_fund_raised"))
                    extra_number_of_investments = clnInt(extra.get("number_of_investments"))
                    extra_number_of_lead_investments = clnInt(extra.get("number_of_lead_investments"))
                    extra_number_of_exits = clnInt(extra.get("number_of_exits"))
                    extra_number_of_acquisitions = clnInt(extra.get("number_of_acquisitions"))
    
                    #dates
                    founding_date = extra.get("founding_date")
                    if (founding_date):
                        extra_founding_date_date = dt.datetime(int(founding_date.get("year")), int(founding_date.get("month")), int(founding_date.get("day")))
                        
                    ipo_date = extra.get("ipo_date")
                    if (ipo_date):
                        extra_ipo_date_date = dt.datetime(int(ipo_date.get("year")), int(ipo_date.get("month")), int(ipo_date.get("day")))
                #print("name is ", name)
                if (name != None):
                    domain = res.get("website")
                    if companyId==None: companyId = getCompanyId(name, domain)
                    if companyId == None: companyId = generateNewCompanyId(name)
                    insertWebsite(companyId, domain, 0)
                                    
                    #insert basic values into proxycurl table
                    val = (companyId, linkedin_internal_id, description, industry, company_size_on_linkedin, 
                            company_type, founded_year, name, tagline, universal_name_id, profile_pic_url, 
                            background_cover_image_url, search_id, follower_count, similar_companies, 
                            updates, acquisitions, exit_data, funding_data, company_size_0, company_size_1, 
                            #None, None, None, None, None, None, extra_facebook_id, extra_twitter_id, None, None, None, None, None, None, None, None, None, None, None, None,
                            extra_ipo_status, extra_crunchbase_rank, extra_operating_status, extra_company_type, 
                            extra_contact_email, extra_phone_number, extra_facebook_id, extra_twitter_id, 
                            extra_number_of_funding_rounds, extra_total_funding_amount, extra_stock_symbol, 
                            extra_number_of_lead_investors, extra_number_of_investors, extra_total_fund_raised, 
                            extra_number_of_investments, extra_number_of_lead_investments, extra_number_of_exits, 
                            extra_number_of_acquisitions, extra_founding_date_date, extra_ipo_date_date,
                            
                            companyId, linkedin_internal_id,description, industry, company_size_on_linkedin, 
                            company_type, founded_year, name, tagline, universal_name_id, profile_pic_url, 
                            background_cover_image_url, search_id, follower_count, similar_companies, 
                            updates, acquisitions, exit_data, funding_data, company_size_0, company_size_1, 
                            #None, None, None, None, None, None, extra_facebook_id, extra_twitter_id, None, None, None, None, None, None, None, None, None, None, None, None)
                            extra_ipo_status, extra_crunchbase_rank, extra_operating_status, extra_company_type, 
                            extra_contact_email, extra_phone_number, extra_facebook_id, extra_twitter_id, 
                            extra_number_of_funding_rounds, extra_total_funding_amount, extra_stock_symbol, 
                            extra_number_of_lead_investors, extra_number_of_investors, extra_total_fund_raised, 
                            extra_number_of_investments, extra_number_of_lead_investments, extra_number_of_exits, 
                            extra_number_of_acquisitions, extra_founding_date_date, extra_ipo_date_date )
    
                    sql =  "insert into proxycurl(" \
                    "company_ID, linkedin_internal_id, description, industry, company_size_on_linkedin, company_type, "\
                    "founded_year, company_name, tagline, universal_name_id, profile_pic_url, background_cover_image_url, "\
                    "search_id, follower_count, similar_companies, updates, acquisitions, exit_data, "\
                    "funding_data, company_size_0, company_size_1, extra_ipo_status, extra_crunchbase_rank, "\
                    "extra_operating_status, extra_company_type, extra_contact_email, extra_phone_number, "\
                    "extra_facebook_id, extra_twitter_id, extra_number_of_funding_rounds, extra_total_funding_amount, "\
                    "extra_stock_symbol, extra_number_of_lead_investors, extra_number_of_investors, "\
                    "extra_total_fund_raised, extra_number_of_investments, extra_number_of_lead_investments, "\
                    "extra_number_of_exits, extra_number_of_acquisitions, extra_founding_date, extra_ipo_date) "\
                    "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "\
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "\
                    "ON DUPLICATE KEY UPDATE "\
                    "company_ID=%s, linkedin_internal_id=%s, description=%s, industry=%s, company_size_on_linkedin=%s, company_type=%s, "\
                    "founded_year=%s, company_name=%s, tagline=%s, universal_name_id=%s, profile_pic_url=%s, background_cover_image_url=%s, "\
                    "search_id=%s, follower_count=%s, similar_companies=%s, updates=%s, acquisitions=%s, exit_data=%s, "\
                    "funding_data=%s, company_size_0=%s, company_size_1=%s, extra_ipo_status=%s, extra_crunchbase_rank=%s, "\
                    "extra_operating_status=%s, extra_company_type=%s, extra_contact_email=%s, extra_phone_number=%s, "\
                    "extra_facebook_id=%s, extra_twitter_id=%s, extra_number_of_funding_rounds=%s, extra_total_funding_amount=%s, "\
                    "extra_stock_symbol=%s, extra_number_of_lead_investors=%s, extra_number_of_investors=%s, "\
                    "extra_total_fund_raised=%s, extra_number_of_investments=%s, extra_number_of_lead_investments=%s, "\
                    "extra_number_of_exits=%s, extra_number_of_acquisitions=%s, extra_founding_date=%s, extra_ipo_date=%s"
                    
                    print("     - identified by PC: ", name, domain, "(companyId: ", companyId, ")")
                    
                    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                    cursor = cnx.cursor(buffered=True)
                    cursor.execute(sql, val)
                    cnx.commit()
                    
                    
                    insertWebsite(companyId, domain, 2)
                    
                    #add categories into proxycurl_categories table
                    categories = res.get("categories")
                    if (categories):
                        values = (companyId, )
                        sql = "delete from linkedin_categories where companyId=%s"
                        cursor.execute(sql, values)
                        cnx.commit()
                        for cat in categories:
                            values = (companyId, cln(cat))
                            sql = "insert into linkedin_categories(companyId, category) values(%s, %s)"
                            cursor.execute(sql, values)
                            cnx.commit()
                            
                    specialities = res.get("specialities")
                    if (specialities):
                        values = (companyId, )
                        sql = "delete from linkedin_specialties where companyId=%s"
                        cursor.execute(sql, values)
                        cnx.commit()
                        for spec in specialities:
                            values = (companyId, cln(spec))
                            sql = "insert into linkedin_specialties(companyId, specialities) values(%s, %s)"
                            cursor.execute(sql, values)
                            cnx.commit()
                    cursor.close()
                    cnx.close()
                    #location object
                    locations = res.get("locations")
                    if (locations):
                        for loc in locations:
                            insertAddress(companyId, loc.get("line_1"), None, loc.get("postal_code"), loc.get("city"), loc.get("country"), None, loc.get("state") , None, loc.get("is_hq"), None, None)
    except BaseException as e:
        print("Exception caught while processing ProxyCurl response: ", e)
        traceback.print_exc()
        return None
    return companyId
    
def domain2companyIdKickfire(domain):
    domain = clnSubDomain(domain)
    
    print("     - Query KF for domain ", domain)
    companyId = None
    global countKickfireData
    if  mayWeQueryKickfire():
        try:
            countKickfireData += 1
            response = requests.get(f'https://api.kickfire.com/v3/company:(all)?website={domain}&key={kfKey}').json()
            #print(response)
            if response['status'] == "success":
                datalist = response['data'][0]
    
                employees = clnContinuumInt(datalist.get("employees"))
                revenue = clnContinuumFloat(datalist.get("revenue"))
                name = cln(datalist.get("companyName"))
                domain = datalist.get("website")
                
                
                companyId = getCompanyId(name, domain)
                if companyId == None: companyId = generateNewCompanyId(name)

                #insert into kickfire            
                values = (
                    companyId, name, cln(datalist.get("tradeName")), clnPhone(datalist.get("phone"), datalist.get("countryShort")), employees[2],
                    revenue[2], cln(datalist.get("stockSymbol")), cln(datalist.get("timeZoneId")),
                    cln(datalist.get("timeZoneName")), cln(datalist.get("utcOffset")), cln(datalist.get("dstOffset")),
                    cln(datalist.get("isISP")), cln(datalist.get("isWifi")), cln(datalist.get("isMobile")), cln(datalist.get("sicCode")), cln(datalist.get("naicsCode")), cln(datalist.get("facebook")),
                    cln(datalist.get("twitter")), cln(datalist.get("linkedIn")), revenue[0], revenue[1], employees[0], employees[1],
                    companyId, name, cln(datalist.get("tradeName")), clnPhone(datalist.get("phone"), datalist.get("countryShort")), employees[2],
                    revenue[2], cln(datalist.get("stockSymbol")), cln(datalist.get("timeZoneId")),
                    cln(datalist.get("timeZoneName")), cln(datalist.get("utcOffset")), cln(datalist.get("dstOffset")),
                    cln(datalist.get("isISP")), cln(datalist.get("isWifi")), cln(datalist.get("isMobile")), cln(datalist.get("sicCode")), cln(datalist.get("naicsCode")), cln(datalist.get("facebook")),
                    cln(datalist.get("twitter")), cln(datalist.get("linkedIn")), revenue[0], revenue[1], employees[0], employees[1])
                print("   - Case 3: Kickfire queried: ", cln(datalist.get("companyName")))

                sql = "INSERT INTO kickfire (companyId, companyName, tradeName, phone, employees, revenue," \
                    " stockSymbol, timeZoneId, timeZoneName, utcOffset, dstOffset, isIsp, isWifi, isMobile, " \
                    " sicCode,  naicsCode, facebook, twitter, linkedIn,"\
                    " revenue_0, revenue_1, employees_0, employees_1)"\
                    " VALUES(%s,%s, %s,%s,%s, %s,%s,%s, %s,%s, %s,%s,%s, %s,%s, %s, %s,%s,%s,%s,%s,%s, %s)"\
                    " ON DUPLICATE KEY UPDATE companyId=%s, companyName=%s, tradeName=%s, phone=%s, employees=%s, revenue=%s," \
                    " stockSymbol=%s, timeZoneId=%s, timeZoneName=%s, utcOffset=%s, dstOffset=%s, isIsp=%s, isWifi=%s, isMobile=%s, " \
                    " sicCode=%s,  naicsCode=%s, facebook=%s, twitter=%s, linkedIn=%s,"\
                    " revenue_0=%s, revenue_1=%s, employees_0=%s, employees_1=%s;"
                cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                cursor = cnx.cursor(buffered=True)

                cursor.execute(sql, values)
                cnx.commit()
                cursor.close()
                cnx.close()
                # insert into address table
                #ompanyId, line_1, line_2, postal_code, city, country, country_short, state, state_short, is_hq, lat, lon):
                insertAddress(companyId, datalist.get("street"), None, datalist.get("postal"), datalist.get("city"), 
                              datalist.get("country"), datalist.get("countryShort"), datalist.get("region"), datalist.get("regionShort"), 
                              None, datalist.get("latitude"), datalist.get("longitude"))
                
                insertWebsite(companyId, domain, 1)
                linkedin2companyByProxycurl(cln(datalist.get("linkedIn")), companyId)
        except BaseException as e:
                print("Exception caught while getting kickfire Info and storing in DB: ", e)
                traceback.print_exc()
    return companyId

def domain2linkedin(domain):
    linkedin = domain2linkedinByScrapingWebsite(domain)
    if linkedin == None:
        try:
            sql = "select linkedin from companies JOIN (SELECT companyId from websites where website=%s) w on companies.companyId=w.companyId "
            values = (domain,)
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(sql, values)
            res = cursor.fetchall()
            cursor.close()
            cnx.close()
            if res and len(res)>0:
                linkedin = res[0][0]
                print("   - linkedinURL ", linkedin)
        except BaseException as e:
            print("Exception caught while translating domain to linkedin : ", e)
            traceback.print_exc()

    if linkedin == None: linkedin = domain2linkedinByKickfire(domain)
    if linkedin == None: linkedin = domain2linkedinByProxycurl(domain)
    
    return linkedin

def domain2linkedinByScrapingWebsite(domain):
    linkedin = None
    try:
        sql = "select profile_li from websites where website=%s"
        values = (domain,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        if res and len(res)>0:
            linkedin = res[0][0]
            print("   - linkedinURL ", linkedin)
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return linkedin
    
def domain2linkedinByProxycurl(domain):
    result = None
    try:
        sql = "select universal_name_id from proxycurl k JOIN (SELECT companyId from websites where website=%s) w on k.company_ID=w.companyId "
        values = (domain,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        if res and len(res)>0:
            result = res[0][0]
            print("   - linkedinURL ", result)
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
        
    if not result and mayWeQueryProxycurl():
        try:
            api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company/resolve'
            header_dic = {'Authorization': 'Bearer ' + pcKey}
            params = {
                'company_location': 'sg',
                'company_domain': domain,
            }
            response = requests.get(api_endpoint,
                                    params=params,
                                    headers=header_dic, timeout=60)
            res = response.json()
            result = res.get("url")
        except BaseException as e:
            print("Exception caught while generating new companyId: ", e)
            traceback.print_exc()
    return result

def domain2linkedinByKickfire(domain):
    linkedin = None
    try:
        sql = "select linkedin from kickfire k JOIN (SELECT companyId from websites where website=%s) w on k.companyId=w.companyId "
        values = (domain,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        if res and len(res)>0:
            linkedin = res[0][0]
            print("   - linkedinURL ", linkedin)
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return linkedin


def linkedin2companyByProxycurl(linkedInProfile, companyId):
    print("     - query pc by linkedin profile")
    success = 0
    global countProxycurlData
    # Getting data from proxycurl using company linkeding url
    if (linkedInProfile != "" and linkedInProfile != None and  mayWeQueryProxycurl()):
        try:
            api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company'
            countProxycurlData += 1
            if linkedInProfile[0:4]=="http":
                linkedInProfile = clnUrlFromParameters(linkedInProfile)
                
                
                websiteSplit = linkedInProfile.split("company/")
                if len(websiteSplit) > 1:
                    linkedInProfile = websiteSplit[1]
            
            linkedin_profile_url = "https://www.linkedin.com/company/" + str(linkedInProfile)
            # print("company linkedin address =",linkedin_profile_url)
            header_dic = {'Authorization': 'Bearer ' + pcKey}
            response = requests.get(api_endpoint, params={
                                    'resolve_numeric_id': 'true',
                                    'categories': 'include',
                                    'funding_data': 'include',
                                    'extra': 'include',
                                    'exit_data': 'include',
                                    'acquisitions': 'include',
                                    'use_cache': 'if-recent',
                                    'url': linkedin_profile_url},
                                    headers=header_dic, timeout=60)
            
            success = processProxyCurl(response, True, companyId)
            if success:
                print("   - Case 4: looked up proxycurl for LinkedinId: ", linkedin_profile_url)
            else:
                print("   - Case 4: proxycurl lookup failed for linkedin ID : ", linkedin_profile_url)
                print(response)
        except BaseException as e:
            print("Exception caught while triggering proxycurl with linkedin profile id: ", e)
            traceback.print_exc()
    return success



################################################################## Store Addresses, Websites ############################################      

def getLatLon(street, city, postalcode, state, country):
    #print("     - get LAT/LON for ", street, postalcode, city, state, country)
    try:
        params = {"format": "json", "limit": "1", "addressdetails": "1"}
        if street: params["street"] = street
        if city: params["city"] = city
        if country: params["country"] = country
        if postalcode: params["postalcode"] = postalcode
        if state: params["state"] = state
        url = "https://nominatim.openstreetmap.org/?" + urllib.parse.urlencode(params)
        response = requests.get(url).json()
        if (len(response) == 0):
            print("     - no lat/lon found for", street, postalcode, city, state, country)
            return None
        else:
            print("     - geocoded lat:", float(response[0]["lat"]), "lon:", float(response[0]["lon"]))
            return float(response[0]["lat"]), float(response[0]["lon"])
    except BaseException as e:
        print("Exception caught while geocoding: ", e)
        traceback.print_exc()
        return None

def insertAddress(companyId, line_1, line_2, postal_code, city, country, country_short, state, state_short, is_hq, lat, lon):
    print("     - inserting address ", line_1, postal_code, city, "for companyId", companyId)
    if (lat == 0 or lon == 0 or lat == '' or lon =='' or lat == None or lon == None):
        # get lat/lon if not provided
        latlon = getLatLon(line_1, city, postal_code, state, country)
        if latlon:
            lat = latlon[0]
            lon = latlon[1]
        else:
            lat = None
            lon = None
        
    try:
        ##############################################
        #todo: first check for dublicates!
        ##############################################
        isHQ=1 if cln(is_hq)=="True" else 0
        address_value = (companyId, cln(line_1), cln(line_2), cln(postal_code), cln(city), cln(country), cln(country_short), cln(state), cln(state_short), isHQ, lat, lon)
        address_sql = "INSERT into addresses (companyId, line_1, line_2, postal_code, city, country, countryShort, state, stateShort, is_hq, latitude, longitude) "\
                      "values(%s,%s,%s, %s,%s,%s, %s,%s,%s,%s,%s, %s)"
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(address_sql, address_value)
        cnx.commit()
        cursor.close()
        cnx.close()
        return 1
    except BaseException as e:
        print("Exception caught while inserting address into DB: ", e)
        traceback.print_exc()
        return 0

def insertWebsite(companyId, website, source):
    
    try:
        website2 = clnSubDomain(website)
        print("     - insert website:", website2, "for companyId:", companyId)
        if website2:
            values = (companyId, website2, source, companyId, source )
            sql = "INSERT INTO websites (companyId, website, source) values(%s, %s, %s) ON DUPLICATE KEY UPDATE companyId=%s, source=%s"
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(sql, values)
            site_id = cursor.lastrowid
            cnx.commit()
            cursor.close()
            cnx.close()
            getScreenshot(site_id, website2, False)
            return True
        else:
            return False
    except BaseException as e:
        print("Exception caught while inserting website into DB: ", e)
        traceback.print_exc()
        return False
    
def companyId2Domain(companyId):
    sql = "select website from websites where companyId=%s"
    values= (companyId, )
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)

    cursor3.execute(sql, values)
    website = cursor3.fetchone()
    
    cursor3.close()
    cnx3.close()
    if website:
        return website[0]
    else:
        return None
    
################################################################## Update IP ranges ############################################      
def checkIpRangeOverlap(ipRange):
    print("ip-Range is:", ipRange)
    ip = IPNetwork(ipRange)
    values= None
    sql = None       
    if "." in ipRange:
        values = (ip.first, ip.first, ip.last, ip.last)
        sql = "SELECT rangeId FROM `ip_ranges` where (ipStartv4<%s AND ipEndv4>%s) OR (ipStartv4<%s AND ipEndv4>%s) LIMIT 1"
    elif ":" in ipRange:    
        values = (format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.last)), format(ipaddress.IPv6Address(ip.last)))
        sql = "SELECT rangeId FROM `ip_ranges` where (ipStartv6<%s AND ipEndv6>%s) OR (ipStartv6<%s AND ipEndv6>%s) LIMIT 1"
    else:
        print("no valid IP Network:", ipRange)
        return 0
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql, values)
    count = cursor.rowcount
    cursor.close()
    cnx.close()
    if cursor>0:
        return 1
    else:
        return 0

def deleteIpRangeOverlaps(ipRange):
    ip = IPNetwork(ipRange)
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    values = None
    sql = None       
    if "." in ipRange:
        values= (ip.first, ip.first, ip.last, ip.last)
        sql = "DELETE FROM `ip_ranges` where (ipStartv4<%s AND ipEndv4>%s) OR (ipStartv4<%s AND ipEndv4>%s)"
    elif ":" in ipRange:    
        values= (format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.last)), format(ipaddress.IPv6Address(ip.last)))
        sql = "DELETE FROM `ip_ranges` where (ipStartv6<%s AND ipEndv6>%s) OR (ipStartv6<%s AND ipEndv6>%s)"
    else:
        print("no valid IP Network:", ipRange)
        return 0
    cursor.execute(sql, values)
    cnx.commit()
    cursor.close()
    cnx.close()
    return 1

def deleteIpRangesOf(companyId):
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute("DELETE FROM `ip_ranges` where companyId=%s", (companyId,))
    cnx.commit()
    cursor.close()
    cnx.close()

def updateIpRangesByIpi(domain, companyId, forceEvenIfYoungData):
    try:
        if companyId==None and domain !=None:
            companyId= domain2companyId(domain, True)
        if domain==None:
            domain = companyId2Domain(companyId)
        oldData = False
        
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        
        if not forceEvenIfYoungData:
            sql = "select lastModifiedOn from ip_ranges where companyId=%s order by lastModifiedOn DESC LIMIT 1"
            values=(companyId, )
            cursor.execute(sql, values)
            result = cursor.fetchall()        
            if result and (result[0][0] < ( datetime.now() - dt.timedelta(weeks=8))):
                oldData = True
        
        if oldData or forceEvenIfYoungData:
            api_endpoint = "https://ipinfo.io/ranges/" + domain + "?token=" + ipiKey
            #print("   - query ipi")
            response = requests.get(api_endpoint)
            if response.status_code == 200:
                res = response.json()
                ranges = res.get("ranges")
                
                if ranges and len(ranges)>0:
                    print("   - adding", len(ranges), "ip ranges for", domain, companyId)
                    #remove existing ip ranges of this company, because there here are brand new
                    deleteIpRangesOf(companyId)
                    for ipRange in ranges:
                        ip = IPNetwork(ipRange)
                        

                        # remove ip ranges that overlap with the new ones because these here are newer
                        deleteIpRangeOverlaps(ipRange)
                        
                                       
                        if "." in ipRange:
                            values= (companyId, ip.first, ip.last)
                            
                            sql = "INSERT INTO ip_ranges( companyId, ipStartv4, ipEndv4) values (%s, %s,%s)"
                            
                            cursor.execute(sql, values)
                            cnx.commit()
                        elif ":" in ipRange:
                            values= (companyId, format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.last)))                        
                            sql = "INSERT INTO ip_ranges( companyId, ipStartv6, ipEndv6) values (%s, %s,%s)"
                            cursor.execute(sql, values)
                            cnx.commit()
                        else:
                            print("no valid IP Address: " + ipRange)
                        
                else:
                    print("no ranges found: " + domain)
            else:
                print("error ipi" + str(response.status_code))
        
        cursor.close()
        cnx.close()
    except BaseException as e:
        traceback.print_exc()
        print("error while updateing IP ranges from ipi" + e)



def updateIpRangesByWhoIs(ipAddress, companyId):
    print("     - update IP ranges")


    # todo: avoid duplicates!

    
    success = 0
    # We have fetched company information for that IP address. 
    # now we try to find out the IP range and ad the IP range to our table.
    # so we do not have to lookup company for any IP in the IP range next time.
    try:
        obj = IPWhois(ipAddress)
        data = obj.lookup_whois()
        asn = clnInt(data['asn'])
        asn_cidr = str(data['asn_cidr'])
        asn_country_code = str(data['asn_country_code'])
        asn_date = dt.datetime.strptime(data['asn_date'], '%Y-%m-%d').date()
        asn_registry = str(data['asn_registry'])
        asn_description = str(data['asn_description'])
        
        if asn:
            values = (asn, )
            sql = "SELECT * FROM ip_ranges_asn where asn=%s"
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(sql, values)
            count = cursor.rowcount
            if count == 0:
                values = (cln(asn), cln(asn_cidr), cln(asn_country_code), cln(asn_date), cln(asn_registry), cln(asn_description))
                sql = "INSERT into ip_ranges_asn (asn, asn_cidr, asn_country_code, asn_date, asn_registry, asn_description) VALUES (%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, values)
                cnx.commit()
            cursor.close()
            cnx.close()
        else:
            asn = 0

        
        nets = data['nets']
        for x in nets:
            cidr = x['cidr']
            name = x['name']
            handle = x['handle']
            ipRange = x['range']
            description = x['description']
            country = x['country']
            state = x['state']
            city = x['city']
            address = x['address']
            postal_code = x['postal_code']
            created = x['created']
            updated = x['updated']
            if (ipRange == None):
                ipStart = ""
                ipEnd = ""
            else:
                a, b = ipRange.split(" - ")
                
                # todo: ipv6 support
                ipStart = ip2int(a)
                ipEnd = ip2int(b)

                value = (
                    companyId, asn, ipRange, ipStart, ipEnd, cidr, name, handle, description, country, state, city,
                    address, postal_code, created, updated)
                
                # print(value)
                print("   - IP-Range added from Whois")
                sql = "INSERT into ip_ranges (companyId, asn, ipRange, ipStartv4, ipEndv4, cidr, name, handle, rangeDescription, " \
                      "country, state, city, address, postal_code, createdDateTime, updatedDateTime)" \
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)"

                cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                cursor = cnx.cursor(buffered=True)

                cursor.execute(sql, value)
                cnx.commit()
                cursor.close()
                cnx.close()
                success = 1

    except BaseException as e:
       print("Exception caught while checking whois: ", e)
       traceback.print_exc()
    return success
    
def guessGenderByFirstName(name):
    gender = None
    try:
        sql = "SELECT gender from contactsGenderLookup where firstName=%s LIMIT 1"
        values= (name,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        gender = cursor.fetchone()[0]
        cursor.close()
        cnx.close()
        return gender
    except BaseException as e:
       print("Exception caught while checking whois: ", e)
       traceback.print_exc()
       return gender
   
def guessGenderOfContactId(contactId, updateContact):
    gender = None
    try:
        sql = "SELECT b.gender FROM (SELECT firstName from contacts where contactId=%s) as a left JOIN contactsGenderLookup b ON a.firstName = b.firstName"
        values= (contactId,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        gender = cursor.fetchone()[0]
        print("GENDER IS ", gender)
        if updateContact:
            sql = "UPDATE contacts set gender=%s where contactId=%s"
            values= (gender, contactId)
            cursor.execute(sql, values)
            cnx.commit()
        cursor.close()
        cnx.close()
        return gender
    except BaseException as e:
       print("Exception caught while checking whois: ", e)
       traceback.print_exc()
       return gender

################################################################## looking up companies ############################################




def getCompanyId(name, domain):
    # this function looks up a companyId
    # it creates a new company Id and stores name/domain, but it does not and shall not enrich!
    # it is called by kickfire, proxcurl and ipinfo functions.
    companyId = None
        
    if domain:
        companyId=domain2companyId(domain, False)
        if companyId != None: setCompanyName(name, companyId)
    if companyId==None and name!=None and name!="":
        companyId = companyName2companyIdbyKickfire(name)
        if companyId != None: setCompanyName(name, companyId)
    if companyId==None and name!=None and name!="":
        companyId = companyName2companyIdbyProxycurl(name)
        if companyId != None: setCompanyName(name, companyId)
    if companyId==None and name!=None and name!="":
        companyId = companyName2companyIdbyIpInfo(name)
        if companyId != None: setCompanyName(name, companyId)
    return companyId


def setCompanyName(companyName, companyId):
    try:
        sql = "Update companies set companyName=%s where companyId=%s"
        values= (companyName, companyId)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        cnx.commit()
        cursor.close()
        cnx.close()
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        return False
    return True
    
def companyName2companyIdbyKickfire(name):
    try:
        sql = "select companyId from kickfire where companyName=%s"
        values = (name,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        
        if res and len(res)>0:
            companyId = res[0][0]
            #print("   - existing CompanyId KF ", companyId)
            return companyId
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return None

def companyName2companyIdbyProxycurl(name):
    try:
        sql = "select company_ID from proxycurl where company_name=%s"
        values = (name,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        if res and len(res)>0:
            companyId = res[0][0]
            #print("   - existing CompanyId PC ", companyId)
            return companyId
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return None

def companyName2companyIdbyIpInfo(name):
    try:
        sql = "select companyId from companyIpInfo where companyName=%s"
        values = (name,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        if res and len(res)>0:
            companyId = res[0][0]
            #print("   - existing CompanyId IPI", companyId)
            return companyId
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return None

def domain2companyId(domain, createIfNotExist):
    if domain==None or domain=="": return None
    companyId= None
    try:
        sql = "select companyId from websites where website=%s LIMIT 1"
        values = (domain,)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        res = cursor.fetchall()
        cursor.close()
        cnx.close()
        if res and len(res)>0:
            companyId = res[0][0]
            #print("   - existing CompanyId websites", companyId)
        
        if companyId==None and createIfNotExist:
            
            companyId = domain2companyIdKickfire(domain)
            if companyId == None:
                companyId = generateNewCompanyId(None)
                if domain!=None and domain!="": insertWebsite(companyId, domain, 0)
            
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return companyId

################################################################## creating new companies ############################################

# generate a new company ID without enriching with data

def generateNewCompanyId(name):
    #if name == None or name=="": return None
    print("     - generate new company ID")
    companyId = None
    try:
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        # inserting data into companies table
        if name:
            companies_sql = "INSERT into companies(companyName) Values(%s)"
            cursor.execute(companies_sql, (name, ))
        else:
            companies_sql = "INSERT into companies Values()"
            cursor.execute(companies_sql)
        cnx.commit()
        # returning the last inserted company_id
        companyId = cursor.lastrowid
        cursor.close()
        cnx.close()
        print("   - generated new CompanyId", companyId, "for", name)        
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()
    return companyId

################################################################## deleting companies ############################################

def companyName2domainByKickfire(name, queryApisIfNotExist):
    domain = None
    
    #first lookup in own data
    sql = "select w.website from (SELECT companyId from kickfire where companyName=%s) as k JOIN websites w on k.companyId=w.companyId LIMIT 1"
    values = (name, )
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql, values)
    res = cursor.fetchall()
    if res and len(res)>0:
        domain = res[0][0]
    elif queryApisIfNotExist:
        response = requests.get("https://api.kickfire.com/v1/name2website?key="+ kfKey+"&name=" + urllib.parse.quote(name))
        if response.status_code == 200:
            response = response.json()
            data =  response.get("data")
            #print(data[0])
            if data and len(data)>0:
                matchRate = float(data[0].get("matchRate"))
                if matchRate > 75:
                    domain = data[0].get("website")
                    #print(domain2, ", corrected, ", domain)
                else:
                    print("company not identified: ",  name)
            else:
                print("company not identified: ",  name)
                print("error KF" + str(response.status_code))
        else:
            print("company not identified: ",  name)
            print("error KF" + str(response.status_code))
    cursor.close()
    cnx.close()
    return domain

def deleteCompanyAndVisits(companyId):
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)
    values = (companyId, )
    sql = "DELETE from visits where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_categories where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_specialties where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from ip_ranges where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE t from technographics t "\
    "LEFT JOIN websites w ON t.siteId = w.site_id "\
    "where w.companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from websites where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from addresses where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from kickfire where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from proxycurl where company_ID=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companyIpInfo where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companies where companyId=%s"
    cursor3.execute(sql, values)
    cnx3.commit()
    cursor3.close()
    cnx3.close()
    
def deleteCompanyWithoutVisits(companyId):
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)
    
    values = (None, companyId )
    sql = "UPDATE visits set companyId=%s where companyId = %s"
    cursor3.execute(sql, values)
    
    values = (companyId, )
    sql = "DELETE from linkedin_categories where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_specialties where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from ip_ranges where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE t from technographics t "\
    "LEFT JOIN websites w ON t.siteId = w.site_id "\
    "where w.companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from websites where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from addresses where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from kickfire where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from proxycurl where company_ID=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companyIpInfo where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companies where companyId=%s"
    cursor3.execute(sql, values)
    cnx3.commit()
    cursor3.close()
    cnx3.close()

def assignCompany(companyId, customerId):
    try: 
        sql = "INSERT INTO companies_customers(companyId, customerId) values(%s, %s)"
        values = (companyId, customerId)
        cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor = cnx.cursor(buffered=True)
        cursor.execute(sql, values)
        cnx.commit()
        cursor.close()
        cnx.close()
    except BaseException as e:
        print("Exception caught while generating new companyId: ", e)
        traceback.print_exc()

##################################################################
# choose firmographics from kf or pc and stor in companies table #
##################################################################

def chooseBestFirmographics(companyId):
    sql = "SELECT c.companyId, pc.company_name, pc.industry, pc.company_size_0, pc.company_size_1, pc.linkedin_internal_id, pc.extra_twitter_id, pc.extra_facebook_id, pc.manualISP, " \
        "kf.companyName, kf.employees_0, kf.employees_1, kf.revenue_0, kf.revenue_1, kf.sicCode, kf.naicsCode, kf.twitter, kf.facebook, kf.linkedin, kf.isISP, kf.manualISP, " \
        "ipi.companyName, ipi.isIsp, w.website, w.profile_li, w.profile_tw, w.profile_fb "\
        "FROM (SELECT * from companies where companyId=%s) c "\
        "left JOIN proxycurl pc on c.companyId=pc.company_ID "\
        "left JOIN kickfire kf on kf.companyId=c.companyId "\
        "left JOIN websites w on w.companyId=c.companyId "\
        "left JOIN companyIpInfo ipi on ipi.companyId=c.companyId "\
        "GROUP BY c.companyId;"

    values = (companyId,)
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql, values)
    company = cursor.fetchone()
    cursor.close()
    cnx.close()
    if company:      
        companyId = company[0]
        namePC = company[1]
        industryNaicsPC = linkedinLabel2code(company[2])
        industrySicPC = naics2sic(industryNaicsPC)
        empl0PC = company[3]
        empl1PC = company[4]
        linkedinPC = company[5]
        twitterPC = company[6]
        facebookPC = company[7]
        manualIspPC = company[8]
        nameKF = company[9]
        empl0KF = company[10]
        empl1KF = company[11]
        rev0KF = company[12]
        rev1KF = company[13]
        industrySicKF = company[14] if company[14] else naics2sic(company[15])
        industryNaicsKF =  company[15] if company[15] else sic2naics(company[14])
        twitterKF = company[16]
        facebookKF = company[17]
        linkedinKF = company[18]
        ispKF = company[19]
        manualIspKF = company[20]
        nameIPI = company[21]
        ispIpi = company[22]
        website = company[23]
        linkedinWebsite = company[24]
        twitterWebsite = company[25]
        facebookWebsite = company[26]
        
        companyName = namePC if not (namePC == None or namePC == "Unauthorized")  else nameIPI if nameIPI else nameKF
        wz2008Code = industrySicKF if industrySicKF else industrySicPC
        naicsCode = industryNaicsKF if industryNaicsKF else industryNaicsPC
        employees_0 = empl0PC if empl0PC else empl0KF
        employees_1 = empl1PC if empl1PC else empl1KF
        revenue_0 = rev0KF
        revenue_1 = rev1KF
        linkedin = linkedinPC if linkedinPC else linkedinKF if linkedinKF else linkedinWebsite
        twitter = twitterPC if twitterKF else twitterPC if twitterPC else twitterWebsite
        facebook = facebookPC if facebookPC else facebookKF if facebookKF else facebookWebsite
        isISP = ispIpi if ispIpi else ispKF if ispKF else 0
        manualISP = manualIspKF if manualIspKF else manualIspPC if manualIspPC else 0
        
        print("     - Selecting best firmographics for :", companyName, "(", str(companyId), ")" )
        cnx2 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
        cursor2 = cnx2.cursor(buffered=True)
        values = (companyName, wz2008Code, naicsCode, employees_0, employees_1, revenue_0, revenue_1, linkedin, twitter, facebook, isISP, manualISP, companyId)
        sql = "UPDATE companies set companyName=%s, wz2008Code=%s, naicsCode=%s, employees_0=%s, employees_1=%s, revenue_0=%s, revenue_1=%s, linkedin=%s, twitter=%s, facebook=%s, isISP=%s, manualISP=%s where companyId=%s"
        cursor2.execute(sql, values)
        cnx2.commit()
        cursor2.close()
        cnx2.close()
        getLogo(companyId, website)
    else:
        print("company not found while trying to choose best firmographics: ", companyId)
    

################################## Get Logo and screenshot ####################################################

def getLogo(companyId, domain):
    if domain == None:
        domain = companyId2Domain(companyId)
    if companyId == None:
        companyId = domain2companyId(domain, 1)
        
    domain = clnSubDomain(domain)
    
    try:
        logo = requests.get(f"https://api.kickfire.com/logo?website={domain}", allow_redirects=True)
    
        if logo.status_code == 200:
            ext = logo.headers['content-type']
            ext = ext.split("/")[1]
            if ext == 'svg+xml': ext = "svg"
            
            print("    - got", ext, "companyLogo for ", domain, companyId)
            filename = f"/var/www/login.truffle.one/static/companylogos/{companyId}.{ext}"
            open(filename, 'wb').write(logo.content)
            todayDate = date.today()
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(f"update companies set logoDate=%s, logoFileExtension=%s where companyId=%s", (todayDate, ext, companyId))
            cnx.commit()
            cursor.close()
            cnx.close()
            return filename
        elif domain[0:4] != "www.":
            domain = "www." + domain
            return getLogo(companyId, domain)
        else:
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            cursor.execute(f"update companies set logoDate=%s where companyId=%s", ('1900-01-01', companyId))
            cnx.commit()
            cursor.close()
            cnx.close()
            return None
    except BaseException as e:
        print("Exception caught while fetching logo for company: ", companyId, "with domain", domain)
        return None
    return None


def getScreenshot(site_id, domain, evenIfExists):
    filename = f'/var/www/login.truffle.one/static/screenshots/{site_id}.png'
    try:
        if not evenIfExists:
            #check if exist
            cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
            cursor = cnx.cursor(buffered=True)
            oneMonthAgo = date.today()-timedelta(days=30)
            cursor.execute("select screenshot from websites where site_id=%s and screenshot>%s", (site_id, oneMonthAgo))
            row = cursor.fetchone()
            cursor.close()
            cnx.close()
            if row:
                return filename
        
        options = Options()
        options.headless = True    
        #options.add_argument('--user-agent="Mozilla/5.0 (compatible; t1bot/1.0"')
        options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"')
        options.add_argument("--window-size=1600x3600") 
        #options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #options.add_experimental_option('useAutomationExtension', False)
        #options.add_experimental_option('extensionLoadTimeout', 30000)
    
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.set_page_load_timeout(10)
        driver.maximize_window()
                
        domain = clnSubDomain(domain)
        #print(domain)
        
        try:            
            print("     - getting screenshot of ", domain)
            driver.get("https://" + domain)
            sleep(5)
            # now we try to click away consent banners
            button = None
            try: button = driver.find_element("xpath", "//button[contains(text(), 'gree')]")
            except BaseException as e: pass
            ##### button with text
            if not button:
                try: button: button = driver.find_element("xpath", "//button[contains(text(), 'onsent')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[contains(text(), 'ccept')]")
                except BaseException as e: pass
            if not button: 
                try: button = driver.find_element("xpath", "//button[contains(text(), 'kzeptier')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[contains(text(), 'llow')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[contains(text(), 'ustimme')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[contains(text(), 'rlaube')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[contains(text(),'estätige')]")
                except BaseException as e: pass
            ##### a with text
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(), 'gree')]")
                except BaseException as e: pass
            if not button:
                try: button: button = driver.find_element("xpath", "//a[contains(text(), 'onsent')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(), 'ccept')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(), 'kzeptier')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(), 'llow')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(), 'ustimme')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(), 'rlaube')]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[contains(text(),'estätige')]")
                except BaseException as e: pass
            ####button with subelememt that contains text
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(), 'gree')]]")
                except BaseException as e: pass
            if not button:
                try: button: button = driver.find_element("xpath", "//button[./*[contains(text(), 'onsent')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(), 'ccept')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(), 'kzeptier')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(), 'llow')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(), 'ustimme')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(), 'rlaube')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//button[./*[contains(text(),'estätige')]]")
                except BaseException as e: pass
            ####a with subelememt that contains text
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(), 'gree')]]")
                except BaseException as e: pass
            if not button:
                try: button: button = driver.find_element("xpath", "//a[./*[contains(text(), 'onsent')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(), 'ccept')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(), 'kzeptier')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(), 'llow')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(), 'ustimme')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(), 'rlaube')]]")
                except BaseException as e: pass
            if not button:
                try: button = driver.find_element("xpath", "//a[./*[contains(text(),'estätige')]]")
                except BaseException as e: pass
                
            if button:
                try: button.click()
                except BaseException as e: pass
                #might not be interactable

            sleep(5)
            #take screenshot
            ob = Screenshot.Screenshot()
            element = driver.find_element("tag name", "body")
            screenShot = element.screenshot(filename)
            
            
            if screenShot:
                #print("successfully got screenshot of ", domain)
                
                #resize image to 250 px width
                image = Image.open(filename)
                width = image.size[0]
                height = image.size[1]
                newWidth = 320
                newHeight = int(newWidth * height/width)
                image = image.resize((newWidth, newHeight), Image.ANTIALIAS)
                image.save(filename, optimize=True, quality=95) 
                
                todayDate = date.today()
                cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                cursor = cnx.cursor(buffered=True)
                cursor.execute("update websites set screenshot=%s where site_id=%s", (todayDate, site_id))
                cnx.commit()
                cursor.close()
                cnx.close()
            elif domain[0:4] != "www.":
                domain = "www." + domain
                filename = getScreenshot(site_id, domain, False)
            else:
                cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
                cursor = cnx.cursor(buffered=True)
                print("not able to get screenshot of ", domain)
                cursor.execute("update websites set screenshot=%s where site_id=%s", ('1900-01-01', site_id))
                cnx.commit()
                cursor.close()
                cnx.close()
                filename = None
        except BaseException as e:
            print("Exception caught while taking screenshot for ", domain , "(site_id:", site_id, ")")
            traceback.print_exc()
            return None
        driver.close()
        driver.quit()
    except BaseException as e:
            print("Exception caught while taking screenshot for ", domain , "(site_id:", site_id, ")")
            traceback.print_exc()
            return None
    return filename


################################## INDUSTRY CODE CONVERSION ####################################################

def naics2sic(naics):
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)

    values=(naics, 1)
    sql = "select target from industryCodeConversion where source=%s and type=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    cursor3.close()
    cnx3.close()
    return result[0] if result else None

def linkedinLabel2code(linkedinLabel):
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)
    values=(linkedinLabel, 3)
    sql = "select code from industryCodes where labelEn=%s and codeScheme=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    cursor3.close()
    cnx3.close()
    return result[0] if result else None

def sic2naics(sic):
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)
    values=(sic, 2)
    sql = "select target from industryCodeConversion where source=%s and type=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    cursor3.close()
    cnx3.close()
    return result[0] if result else None

def sic2linkedin(sic):
    cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor3 = cnx3.cursor(buffered=True)
    values=(sic, 3)
    sql = "select target from industryCodeConversion where source=%s and type=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    cursor3.close()
    cnx3.close()
    return result[0] if result else None

################################## IP CONVERSION ####################################################

def ip2int(string_ip):
    try:
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv4Address:
            return int(ipaddress.IPv4Address(string_ip))
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv6Address:
            return int(ipaddress.IPv6Address(string_ip))
    except Exception as e:
        traceback.print_exc()
        return -1
    
def int2ip(int_ip):
    try:
        if int_ip<=4294967295:
            return format(ipaddress.IPv4Address(int_ip))
        else:
            return format(ipaddress.IPv6Address(int_ip))
    except Exception as e:
        traceback.print_exc()
        return -1

################################################################################ CLEAN Data typs ################################################################################

# find out if we have German syntax (100.000.000,00) or English Syntax (100,000,000.00)
# 1=de, 0=en
def isNumberEnOrDe(string):
    language = -1
    countDot = string.count(".")
    countComma = string.count(",")
    if   (countDot >  1 and countComma <= 1): language = 1 # more dots than commas (-> German syntax)
    elif (countDot <= 1 and countComma >  1): language = 0 # more commas than dots (-> English syntax) 
    elif (countDot == 0 and countComma == 0): language = 0 # any language (like an integer)
    elif (countDot == 1 and countComma == 1):
        #is comma first or dot?
        language = 1 if (string.rfind(',') > string.rfind('.')) else 0
    return language


#remove ending and trailing spaces and CRNL
#make it None if len = 0
def cln(string):
    result = None
    if string:
        result = str(string)
        if result != None: result = result.strip()
        if result == "": result = None
    return result

def removeCharOtherThanDotsAndCommas(string):
    return re.sub(r'[^0-9.,]', '', str(string))

def removeCharAll(string):
    result = re.sub(r'[^0-9]', '', str(string))
    return result

def clnSpacesAndDashes(string):
    result = string.replace(" ", "")
    result = result.replace("-", "")
    result = result.replace("/", "")
    result = result.replace("\\", "")
    return result
    
def clnFloat(string):
    result = cln(str(string))

    if result != None:
        result = removeCharOtherThanDotsAndCommas(result)
        if result != "":
            language = isNumberEnOrDe(result)
            #remove dots or commas
            result = float(result.replace(".", "")) if (language == 1) else float(result.replace(",", ""))
        else:
            result = None
    return result
        
def clnInt(string):
    result = cln(str(string))
    if result != None:
        result = removeCharAll(result)
        if result != "":
            result = int(result)
        else:
            result = None
    return result
    
def clnContinuumInt(string):
    result = cln(str(string))
    result_0 = None
    result_1 = None

    if result != None:
        if "to" in result:   
            result_0, result_1 = result.split("to")
            result_1 = clnInt(result_1)
        elif "-" in result:   
            result_0, result_1 = result.split("-")
            result_1 = clnInt(result_1)
        elif "bis" in result:   
            result_0, result_1 = result.split("bis")
            result_1 = clnInt(result_1)
        else:
            result_0 = clnInt(result)
        result_0 = clnInt(result_0)  
    return result_0, result_1, result

def clnContinuumFloat(string):
    result = cln(str(string))
    result_0 = None 
    result_1 = None

    if result != None:
        if "to" in result:   
            result_0, result_1 = result.split("to")
            result_1 = clnFloat(result_1)
        elif "-" in result:   
            result_0, result_1 = result.split("-")
            result_1 = clnFloat(result_1)
        elif "bis" in result:   
            result_0, result_1 = result.split("bis")
            result_1 = clnFloat(result_1)
        else:
            result_0 = clnFloat(result)
        result_0 = clnFloat(result_0)  
    return result_0, result_1, result

def clnPhone(string, countrycode):
    if string:
        num = cln(string)
        if num and num != "":
            #print (num)
            my_number = phonenumbers.parse(num, countrycode)
            if phonenumbers.is_possible_number(my_number):
                return str(phonenumbers.format_number(my_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
    return None

def clnEmail(string):
    return str(email_normalize.normalize(cln(string)).normalized_address)

def clnWebsite(string):
    # normalize to domain and subdomain only www.web.de
    website = cln(string)
    if website != None:
        websiteSplit = website.split("://")
        if len(websiteSplit) > 1:
            website = websiteSplit[1]
        if website[len(website)-1] == "/":
            website = website[:-1]
    return website

def clnSubDomain(string):
    # normalize to domain only web.de
    website = cln(string)
    if website != None:
        website = clnWebsite(website)
        if website != None:
            websiteSplit = website.split("/")
            if len(websiteSplit) > 1:
                website = websiteSplit[0]
    return website

def clnUrlFromParameters(string):
    # normalize to protocol, subdomain, domain, path without parameters and #, http://www.web.de/somepage/some.php
    website = cln(string)
    if website != None:
        websiteSplit = website.split("?")
        if len(websiteSplit) > 1:
            website = websiteSplit[0]
        
        websiteSplit = website.split("#")
        if len(websiteSplit) > 1:
            website = websiteSplit[0]
    return website

