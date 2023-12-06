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
from services import StringHelper, WebsiteService, AddressService, CompanyService, DbConfig


db = DbConfig.getDB()

filterwarnings(action="ignore")

#API keys
pcKey = 'ipW9Gdbl0mWW3iwHjnXvCg'

#shall we lookup ip ranges only (0) or even use rd party APIs to add new ones (1)?
addnewcompanies=1
countProxycurlData = 50
proxycurl_min = None
translatedDataDone =None
currentCreditProxycurl = None

def updateThresholds():
    try:
        #print("     - update thresholds")
        ############# Read Limits from Database
        x = db.execute('''SELECT proxycurl_min, translatedDataDone, currentCreditProxycurl
                        from temptable where id=%s LIMIT %s''', (1, 1))

        global countProxycurlData,  proxycurl_min, translatedDataDone, currentCreditProxycurl
        proxycurl_min = x[0][0]
        translatedDataDone = x[0][1]
        currentCreditProxycurl = x[0][2]
    except BaseException:
        print("Exception caught while updateing PC thresholds")
        traceback.print_exc()



def mayWeQueryProxycurl():
    #print("     - check pc threshold")
    updateThresholds()
    # checking the limit of hitting proxycurl
    global  countProxycurlData, proxycurl_min, translatedDataDone, currentCreditProxycurl

    if countProxycurlData >= 50:
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



def enrichCompany(company):
    if company is not None:
        try:
            linkedInStringId = company.linkedInStringId
            print("Enriching with PC:", company.companyName, "(", company.companyId, ")")
            # if not existing: try to get the linkedInStringId from our own DB Website table
            if linkedInStringId is None:
                print("- no linkedinStingId. trying to get it from website")
                websites = WebsiteService.getWebsitesOfCompany(company)
                for website in websites:
                    if website.profile_li is not None and linkedInStringId is None:
                        linkedInStringId = website.profile_li.split("linkedin.com/company/")[1].split("/")[0].split("#")[0].split("?")[0]

                # if not in websites table try to translate domain to linkedInStringId by ProxyCurl by ProxyCurl
                if linkedInStringId is None:
                    print("- no linkedinStingId in websites DB table. next step we try to scrape it from website")
                    for website in websites:
                        if linkedInStringId is None:
                            website.validate()
                            website.scrapeSocialProfiles()
                            if website.profile_li is not None:
                                linkedInStringId = website.profile_li.split("linkedin.com/company/")[1].split("/")[0].split("#")[0].split("?")[0]

                if linkedInStringId is None:
                    print("- no linkedinStingId in websites DB table. trying to lookup linkedinId from website URL via PC.")
                    for website in websites:
                        if linkedInStringId is not None:
                            linkedInStringId = __lookupLinkedInStringId(website=website.website)

                # if it cannot be translated from domain try to translate from name by ProxyCurl
                if linkedInStringId is None:
                    print("- no linkedinStingId in websites DB table. trying to lookup linkedinId from company Name via PC.")
                    linkedInStringId = __lookupLinkedInStringId(name=company.companyName)

            print("linkedInStringId =", linkedInStringId)
            #get company from PC and process in separate method
            if linkedInStringId:
                return linkedin2companyByProxycurl("https://www.linkedin.com/company/" + linkedInStringId, company)
            print("- ENRICHING WITH PC NOT SUCCESSFUL.")
        except BaseException:
            print("Exception caught while enriching with PC: company", company.companyName, "(companyId:",
                  company.companyId, ")")
            traceback.print_exc()
    return None

def getCompanyByWebsite(domain, queryAPI):
    company = None
    if domain is not None:
        if queryAPI:
            linkedInStringId = __lookupLinkedInStringId(domain)
            company = getCompanyByLinkedInStringId(linkedInStringId, queryAPI)
    return company



def getCompanyByLinkedInStringId(linkedInStringId, queryAPI):
    company = None

    if linkedInStringId is not None:
        # 1. try to lookup in own DB
        sql = "SELECT company_ID from proxycurl where universal_name_id=%s"
        values =(linkedInStringId, )
        sqlData = db.execute(sql, values)
        if sqlData and len(sqlData)>0:
            company = CompanyService.getCompanyById(sqlData[0][0])

        # 2. query Proxycurl
        if not company and queryAPI:
            global countProxycurlData
            if (linkedInStringId != "" and linkedInStringId is not None and mayWeQueryProxycurl()):
                try:
                    api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company'
                    countProxycurlData += 1
                    if linkedInStringId[0:4] == "http":
                        linkedInStringId = linkedInStringId.split("linkedin.com/company/")[1].split("/")[0].split("&")[0].split("#")[0]
                    linkedin_profile_url = "https://www.linkedin.com/company/" + str(linkedInStringId)
                    header_dic = {'Authorization': 'Bearer ' + pcKey}
                    # Create a new dictionary
                    params = {'categories': 'include', 'funding_data': 'include', 'extra': 'include',
                              'exit_data': 'include', 'acquisitions': 'include', 'use_cache': 'if-recent',
                              'url': linkedin_profile_url}
                    if linkedInStringId.isnumeric():
                        params['resolve_numeric_id'] = 'true'
                    response = requests.get(api_endpoint, params=params, headers=header_dic, timeout=60)

                    res = response.json()
                    # 3. try to match an existing company
                    company = __getCompanyFromProxyCurlResponse(res)

                    # 4. generate a company
                    if company is None:
                        name = StringHelper.cln(res.get("name"))
                        print ("generating new company with name", name)
                        if name is not None:
                            company = CompanyService.Company(name)
                            company.save()

                    __processProxyCurl(res, company)

                except BaseException as e:
                    print("Exception caught while generating new companyId: ", e)
                    traceback.print_exc()
    return company

def __getCompanyFromProxyCurlResponse(jsonResponse):
    # get all attributes that might be useful to match a company
    print(jsonResponse)
    domain = jsonResponse.get("website")
    linkedin_internal_id = StringHelper.cln(jsonResponse.get("linkedin_internal_id"))
    universal_name_id = StringHelper.clnInt(jsonResponse.get("universal_name_id"))
    name = StringHelper.cln(jsonResponse.get("name"))
    extra = jsonResponse.get("extra")
    contact_email = extra.get("contact_email") if extra is not None else None
    extra_contact_email = StringHelper.clnEmail(contact_email) \
        if extra is not None and contact_email is not None else None

    # phone number: normalizing the phone number requires the country.
    hq_country = None
    hq = jsonResponse.get("hq")
    if hq is None:
        loc = jsonResponse.get("locations")
        if loc is not None and len(loc)>0:
            hq = loc[0]
    if hq is not None:
        StringHelper.cln(hq.get("country"))
    extra_phone_number = StringHelper.clnPhone(extra.get("phone_number"), hq_country)\
        if (extra is not None and hq_country is not None) else None
    extra_facebook_id = StringHelper.cln(extra.get("facebook_id"))\
        if extra is not None else None
    extra_twitter_id = StringHelper.cln(extra.get("twitter_id"))\
        if extra is not None else None
    extra_stock_symbol = StringHelper.cln(extra.get("stock_symbol"))\
        if extra is not None else None

    company = getCompanyByLinkedInStringId(universal_name_id, False)
    if company is None: company = getCompanyByLinkedInStringId(linkedin_internal_id, False)
    if company is None: company = CompanyService.getCompanyByWebsite(domain, False)
    if domain is None and extra_contact_email is not None:
        domain = extra_contact_email.rsplit("@")[0]
        company = CompanyService.getCompanyByWebsite(domain, False)
    if company is None: company = CompanyService.getCompanyByName(name)

    #todo: try to match teh company from facebook id, twitter id, phone number, stock symbol
    return company

def __lookupLinkedInStringId(website=None, name=None):

    api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company/resolve'
    header_dic = {'Authorization': 'Bearer ' + pcKey}
    params = {}
    #TODO: normalize domain

    if website is not None: params['company_domain'] = website
    if name is not None: params['company_name'] = name
    if len(params)>0:
        try:
            response = requests.get(api_endpoint, params=params, headers=header_dic, timeout=60)
            res = response.json()
            result = res.get("url")
            if result is not None:
                print(result)
                return StringHelper.unescapeSpecialLetters(result.split("linkedin.com/company/")[1].split("/")[0].split("#")[0].split("?")[0])
        except BaseException as e:
            print("Exception caught while generating new companyId: ", e)
            traceback.print_exc()


def linkedin2companyByProxycurl(linkedInProfile, company):
    print("checking company details for ", linkedInProfile, "(", company.companyName, ", ", company.companyId, ")")
    success = 0
    global countProxycurlData
    # Getting data from proxycurl using company linkeding url
    if (linkedInProfile != "" and linkedInProfile != None and mayWeQueryProxycurl()):
        try:
            api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company'
            countProxycurlData += 1
            if linkedInProfile[0:4] == "http":
                linkedInProfile = StringHelper.unescapeSpecialLetters(linkedInProfile.split("linkedin.com/company/")[1].split("/")[0].split("#")[0].split("?")[0])
            linkedin_profile_url = "https://www.linkedin.com/company/" + str(linkedInProfile)
            header_dic = {'Authorization': 'Bearer ' + pcKey}
            # Create a new dictionary
            params = {}
            params['categories'] = 'include'
            params['funding_data'] = 'include'
            params['extra'] = 'include'
            params['exit_data'] = 'include'
            params['acquisitions'] = 'include'
            params['use_cache'] = 'if-recent'
            params['url'] = linkedin_profile_url
            if linkedInProfile.isnumeric():
                params['resolve_numeric_id'] = 'true'
            response = requests.get(api_endpoint, params=params, headers=header_dic, timeout=60)
            success = __processProxyCurl(response.json(), company)
            if success:
                print("   - Case 4: looked up proxycurl for LinkedinId: ", linkedin_profile_url)
            else:
                print("   - Case 4: proxycurl lookup failed for linkedin ID : ", linkedin_profile_url)
                print(response)
        except BaseException as e:
            print("Exception caught while triggering proxycurl with linkedin profile id: ", e)
            traceback.print_exc()
    return success






def __processProxyCurl(jsonResponse, company):
    print("     - processing proxycurl response")
    companyId = company.companyId
    try:
        # print("response from pc:", res)
        if jsonResponse is not None:
            name = StringHelper.cln(jsonResponse.get("name"))
            if name == "Not Found":
                return None
            else:
                # ---- simple data types ---
                linkedin_internal_id = StringHelper.cln(jsonResponse.get("linkedin_internal_id"))
                description = StringHelper.cln(jsonResponse.get("description"))
                industry = StringHelper.cln(jsonResponse.get("industry"))
                company_size_on_linkedin = StringHelper.clnInt(jsonResponse.get("company_size_on_linkedin"))
                company_type = StringHelper.cln(jsonResponse.get("company_type"))
                founded_year = StringHelper.clnInt(jsonResponse.get("founded_year"))
                tagline = StringHelper.cln(jsonResponse.get("tagline"))
                universal_name_id = StringHelper.clnInt(jsonResponse.get("universal_name_id"))
                profile_pic_url = StringHelper.clnWebsite(jsonResponse.get("profile_pic_url"))
                background_cover_image_url = StringHelper.clnWebsite(jsonResponse.get("background_cover_image_url"))
                search_id = StringHelper.clnInt(jsonResponse.get("search_id"))
                follower_count = StringHelper.clnInt(jsonResponse.get("follower_count"))

                # for the time being we just dump theses values into the DB
                # print("A") if a > b else print("B")
                similar_companies = None if jsonResponse.get("similar_companies") is None else str(jsonResponse.get("similar_companies"))[1:-1]
                updates = None if jsonResponse.get("updates") is None else str(jsonResponse.get("updates"))[1:-1]
                acquisitions = None if jsonResponse.get("acquisitions") is None else str(jsonResponse.get("acquisitions"))[1:-1]
                exit_data = None if jsonResponse.get("exit_data") is None else str(jsonResponse.get("exit_data"))[1:-1]
                funding_data = None if jsonResponse.get("funding_data") is None else str(jsonResponse.get("funding_data"))[1:-1]


                # Company Size
                company_size = jsonResponse.get("company_size")
                company_size_0 = None
                company_size_1 = None
                if (company_size):
                    company_size_0 = StringHelper.clnInt(company_size[0])
                    company_size_1 = StringHelper.clnInt(company_size[1])

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


                extra = jsonResponse.get("extra")
                if extra is not None:
                    extra_ipo_status = StringHelper.cln(extra.get("ipo_status"))
                    extra_crunchbase_rank = StringHelper.clnInt(extra.get("crunchbase_rank"))
                    extra_operating_status = StringHelper.cln(extra.get("operating_status"))
                    extra_company_type = StringHelper.cln(extra.get("company_type"))

                    extra_contact_email = StringHelper.clnEmail(extra.get("contact_email"))
                    hq_country = StringHelper.cln(jsonResponse.get("hq").get("country")) \
                        if jsonResponse.get("hq") is not None else None
                    print(extra.get("phone_number"))
                    extra_phone_number = StringHelper.clnPhone(extra.get("phone_number"), hq_country)
                    extra_facebook_id = StringHelper.cln(extra.get("facebook_id"))
                    extra_twitter_id = StringHelper.cln(extra.get("twitter_id"))
                    extra_number_of_funding_rounds = StringHelper.clnInt(extra.get("number_of_funding_rounds"))
                    extra_total_funding_amount = StringHelper.clnInt(extra.get("total_funding_amount"))
                    extra_stock_symbol = StringHelper.cln(extra.get("stock_symbol"))
                    extra_number_of_lead_investors = StringHelper.clnInt(extra.get("number_of_lead_investors"))
                    extra_number_of_investors = StringHelper.clnInt(extra.get("number_of_investors"))
                    extra_total_fund_raised = StringHelper.clnInt(extra.get("total_fund_raised"))
                    extra_number_of_investments = StringHelper.clnInt(extra.get("number_of_investments"))
                    extra_number_of_lead_investments = StringHelper.clnInt(extra.get("number_of_lead_investments"))
                    extra_number_of_exits = StringHelper.clnInt(extra.get("number_of_exits"))
                    extra_number_of_acquisitions = StringHelper.clnInt(extra.get("number_of_acquisitions"))

                    # dates
                    founding_date = extra.get("founding_date")
                    if founding_date is not None:
                        extra_founding_date_date = dt.datetime(int(founding_date.get("year")), int(founding_date.get("month")), int(founding_date.get("day")))

                    ipo_date = extra.get("ipo_date")
                    if ipo_date is not None:
                        extra_ipo_date_date = dt.datetime(int(ipo_date.get("year")), int(ipo_date.get("month")), int(ipo_date.get("day")))

                if (name is not None):
                    domain = jsonResponse.get("website")
                    if domain is not None:
                        WebsiteService.Website(domain, company).save()


                    # insert basic values into proxycurl table
                    val = (company.companyId, linkedin_internal_id, description, industry, company_size_on_linkedin,
                           company_type, founded_year, name, tagline, universal_name_id, profile_pic_url,
                           background_cover_image_url, search_id, follower_count, similar_companies,
                           updates, acquisitions, exit_data, funding_data, company_size_0, company_size_1,
                           # None, None, None, None, None, None, extra_facebook_id, extra_twitter_id, None, None, None, None, None, None, None, None, None, None, None, None,
                           extra_ipo_status, extra_crunchbase_rank, extra_operating_status, extra_company_type,
                           extra_contact_email, extra_phone_number, extra_facebook_id, extra_twitter_id,
                           extra_number_of_funding_rounds, extra_total_funding_amount, extra_stock_symbol,
                           extra_number_of_lead_investors, extra_number_of_investors, extra_total_fund_raised,
                           extra_number_of_investments, extra_number_of_lead_investments, extra_number_of_exits,
                           extra_number_of_acquisitions, extra_founding_date_date, extra_ipo_date_date,

                           company.companyId, linkedin_internal_id ,description, industry, company_size_on_linkedin,
                           company_type, founded_year, name, tagline, universal_name_id, profile_pic_url,
                           background_cover_image_url, search_id, follower_count, similar_companies,
                           updates, acquisitions, exit_data, funding_data, company_size_0, company_size_1,
                           # None, None, None, None, None, None, extra_facebook_id, extra_twitter_id, None, None, None, None, None, None, None, None, None, None, None, None)
                           extra_ipo_status, extra_crunchbase_rank, extra_operating_status, extra_company_type,
                           extra_contact_email, extra_phone_number, extra_facebook_id, extra_twitter_id,
                           extra_number_of_funding_rounds, extra_total_funding_amount, extra_stock_symbol,
                           extra_number_of_lead_investors, extra_number_of_investors, extra_total_fund_raised,
                           extra_number_of_investments, extra_number_of_lead_investments, extra_number_of_exits,
                           extra_number_of_acquisitions, extra_founding_date_date, extra_ipo_date_date )

                    sql =  "insert into proxycurl(" \
                           "company_ID, linkedin_internal_id, description, industry, company_size_on_linkedin, company_type, " \
                           "founded_year, company_name, tagline, universal_name_id, profile_pic_url, background_cover_image_url, " \
                           "search_id, follower_count, similar_companies, updates, acquisitions, exit_data, " \
                           "funding_data, company_size_0, company_size_1, extra_ipo_status, extra_crunchbase_rank, " \
                           "extra_operating_status, extra_company_type, extra_contact_email, extra_phone_number, " \
                           "extra_facebook_id, extra_twitter_id, extra_number_of_funding_rounds, extra_total_funding_amount, " \
                           "extra_stock_symbol, extra_number_of_lead_investors, extra_number_of_investors, " \
                           "extra_total_fund_raised, extra_number_of_investments, extra_number_of_lead_investments, " \
                           "extra_number_of_exits, extra_number_of_acquisitions, extra_founding_date, extra_ipo_date) " \
                           "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                           "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) " \
                           "ON DUPLICATE KEY UPDATE " \
                           "company_ID=%s, linkedin_internal_id=%s, description=%s, industry=%s, company_size_on_linkedin=%s, company_type=%s, " \
                           "founded_year=%s, company_name=%s, tagline=%s, universal_name_id=%s, profile_pic_url=%s, background_cover_image_url=%s, " \
                           "search_id=%s, follower_count=%s, similar_companies=%s, updates=%s, acquisitions=%s, exit_data=%s, " \
                           "funding_data=%s, company_size_0=%s, company_size_1=%s, extra_ipo_status=%s, extra_crunchbase_rank=%s, " \
                           "extra_operating_status=%s, extra_company_type=%s, extra_contact_email=%s, extra_phone_number=%s, " \
                           "extra_facebook_id=%s, extra_twitter_id=%s, extra_number_of_funding_rounds=%s, extra_total_funding_amount=%s, " \
                           "extra_stock_symbol=%s, extra_number_of_lead_investors=%s, extra_number_of_investors=%s, " \
                           "extra_total_fund_raised=%s, extra_number_of_investments=%s, extra_number_of_lead_investments=%s, " \
                           "extra_number_of_exits=%s, extra_number_of_acquisitions=%s, extra_founding_date=%s, extra_ipo_date=%s"

                    print("     - identified by PC: ", name, domain, "(companyId: ", companyId, ")")


                    db.execute(sql, val, True)

                    # add categories into proxycurl_categories table
                    categories = jsonResponse.get("categories")
                    if (categories):
                        values = (company.companyId, )
                        sql = "delete from linkedin_categories where companyId=%s"
                        db.execute(sql, values, True)
                        for cat in categories:
                            values = (company.companyId, StringHelper.cln(cat))
                            sql = "insert into linkedin_categories(companyId, category) values(%s, %s)"
                            db.execute(sql, values, True)

                    specialities = jsonResponse.get("specialities")
                    if (specialities):
                        values = (company.companyId, )
                        sql = "delete from linkedin_specialties where companyId=%s"
                        db.execute(sql, values, True)
                        for spec in specialities:
                            values = (company.companyId, StringHelper.cln(spec))
                            sql = "insert into linkedin_specialties(companyId, specialities) values(%s, %s)"
                            db.execute(sql, values, True)

                    # location object
                    locations = jsonResponse.get("locations")
                    if (locations):
                        for loc in locations:
                            AddressService.insertAddress(companyId, loc.get("line_1"), None, loc.get("postal_code"), loc.get("city"), loc.get("country"), None, loc.get("state") , None, loc.get("is_hq"), None, None)
        company.chooseBestFirmographics()
    except BaseException as e:
        print("Exception caught while processing ProxyCurl response: ", e)
        traceback.print_exc()
        return None
    return companyId