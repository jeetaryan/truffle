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
from services import DbConfig, StringHelper, ProxyCurlService, IpService, ContactsService, WebsiteService
from services import ProxyCurlService as pc
import logging

db = DbConfig.getDB()
# company types ordered by length
typicalCompanyTypes = ["UG (haftungsbeschränkt)", "GmbH & Co. KG", "PartG mbH", "Limited", "REIT-AG", "GesnbR", "PartG", "InvAG", "GmbH", "KGaA", "SWIV", "VVaG", "KdöR", "AdöR", "Sarl", "Sàrl", "EURL", "mbH", "OHG", "GbR", "Ltd", "LLC", "PLC", "SCE", "SPE", "SpA", "gAG", "OEG", "KEG", "SCI", "SNC", "SCP", "SAS", "SCA", "srl", "snc", "sas", "LLP", "UG", "KG", "AG", "SE", "eG", "eV", "eK", "eU", "OG", "SC", "SA", "SL", "AB"]
# logging.basicConfig(filename='/var/log/truffle.one/noris-requests.log', level=logging.INFO)

def getCompany(id=None,
               website=None,
               email=None,
               linkdinUrl=None,
               linkedinStringId=None,
               linkedinNumericId=None,
               twitter=None,
               facebook=None,
               xing=None,
               instagram=None,
               youtube=None,
               tiktok=None,
               twitch=None,
               address=None,
               phoneNumber=None,
               stockSymbol=None,
               name=None):
    company = None
    if id: return getCompanyById(id)
    if website and not company: company = getCompanyByWebsite(website, True)
    if email and not company: company = getCompanyByEmail(email)

    if email and not company: company = getCompanyByEmail(email)
    if email and not company: company = getCompanyByEmail(email)
    if name and not company: company = getCompanyByName(name)
    return company

def getCompanyByEmail(email, queryAPI):
    company = None
    # lookup contact from DB and check if we have the company assigned
    contact = ContactsService.getContactByEmail(email)
    if contact and contact.company:
        company = contact.company

    # deduct domain from email and lookup by domain
    if not company:
        domain = email.rsplit("@")[0]
        company = getCompanyByWebsite(domain, queryAPI)
    return

def getCompanyById(companyId):
    try:
        data = db.execute('''
                select c.companyName, c.logoDate, c.logoFileExtension, pc.industry, c.wz2008Code,
                        c.naicsCode, c.employees_0, c.employees_1, c.revenue_0, c.revenue_1, c.linkedin, c.linkedInStringId,
                        c.twitter, c.facebook, c.isISP, c.manualISP, c.createdOn, c.lastModifiedOn
                from (SELECT * from companies where companyId=%s) as c
                LEFT JOIN proxycurl pc on pc.company_ID=c.companyId
                ''', (companyId,))
    except BaseException as e:
        traceback.print_exc()
    if len(data) > 0:
        i = data[0]
        return Company(i[0], companyId, i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13], i[14], i[16], i[17])
    else:
        return None

def getCompanyByLinkedinUrl(url):
    try:
        # fetch from own database (no external APIs)
        data = db.execute('''
                        select companyId from websites
                        where profile_li LIKE %s LIMIT 1;
                        ''', ('%' + url + '%',))
    except BaseException as e:
        traceback.print_exc()
    if len(data) > 0:
        dbId = data[0][0]
        return getCompanyById(dbId)
    else:
        return None

#todo: try to match the company from facebook id, twitter id, phone number, stock symbol

def getCompanyByIpInt(ipAddress, queryApisIfUnknown):
    return getCompanyByIp(StringHelper.int2ip(ipAddress), queryApisIfUnknown)

def getCompanyByIp(ipAddress, queryApisIfUnknown):
    if (ipAddress != "" and ipAddress is not None):
        # print("Checking companyId for IP: ", ipAddress)

        try:
            sql = None
            values = None
            if "." in ipAddress:
                ipAddress_int = StringHelper.ip2int(ipAddress)
                sql = "SELECT companyId FROM ip_ranges where ipStartv4 <=%s and ipEndv4 >= %s LIMIT %s"
                values = (ipAddress_int, ipAddress_int, 1)
            elif ":" in ipAddress:
                sql = "SELECT companyId FROM ip_ranges where ipStartv6 <=%s and ipEndv6 >= %s LIMIT %s"
                values = (format(ipaddress.IPv6Address(ipAddress)), format(ipaddress.IPv6Address(ipAddress)), 1)
            else:
                return None

            dataSQL = db.execute(sql, values)
            if dataSQL is not None and len(dataSQL)>0:
                data = dataSQL[0]

                # great! existing company!
                print("   - Case 1: looked up companyID from IP-Ranges: ", data[0])
                return getCompanyById(data[0])
            elif (queryApisIfUnknown):
                print("   - Case 1: cannot lookup ip: ", ipAddress)
                company = __getCompanyByIpByIpInfo(ipAddress)

                if company is not None:
                    company.enrich()
                    company.chooseBestFirmographics()
                    IpService.updateIpRangesByIpi(None, company.companyId, False)
                    #todo: reactivate once asn column has been altered to bigint
                    #IpService.updateIpRangesByWhoIs(ipAddress, company.companyId)
                return company
        except BaseException as e:
            print("Exception caught during IP translation: ", e)
            traceback.print_exc()
    return None

def tryRemovingCompanyType(companyName):
    try:
        result = companyName
        for t in typicalCompanyTypes:
            regex = r'(.*)%s$' % re.escape(t)
            result = StringHelper.cln(re.sub(regex, r'\1', result))
            return result
    except BaseException as e:
        traceback.print_exc()
    return None


def __getCompanyByIpByIpInfo(ipAddress):
    ipiKey = "ef809b112a5aa8"
    print("     - query IPI by IP")
    company = None

    if (ipAddress != "" and ipAddress != None):
        try:
            api_endpoint = "https://ipinfo.io/" + ipAddress + "/json?token=" + ipiKey
            response = requests.get(api_endpoint, timeout=3)
            res = response.json()

            # print(res)
            jsonCompany = res.get("company")
            if jsonCompany is not None and jsonCompany != "":
                nameStr = StringHelper.cln(jsonCompany.get("name"))
                domainStr = StringHelper.clnWebsite(jsonCompany.get("domain"))
                type = StringHelper.cln(jsonCompany.get("type"))

                #try to match company
                if domainStr is not None:
                    company = getCompanyByWebsite(domainStr, True)
                if company is None and nameStr is not None:
                    company = getCompanyByName(nameStr)
                    if company is None:
                        company = Company(nameStr)
                        company.save()

                # try to match website
                if company is not None and domainStr is not None:
                    website = WebsiteService.getWebsiteByUrl(domainStr)
                    if website.company.companyId != company.companyId:
                        website.company = company
                        website.reCollectFromWebsite()

                if company is not None:
                    company.enrich()
                    company.chooseBestFirmographics()

                    #update IpInfo table
                    isIsp = 1 if type == "isp" else 0
                    values = (company.companyId, nameStr, type, isIsp, company.companyId, nameStr, type, isIsp)
                    print("   - Case 4: IPI queried: ", nameStr, "(", domainStr, ")")
                    sql = '''INSERT INTO companyIpInfo (companyId, companyName, companyType, isIsp)
                          VALUES(%s,%s, %s,%s)
                          ON DUPLICATE key UPDATE companyId=%s, companyName=%s, companyType=%s, isIsp=%s'''
                    db.execute(sql, values, True)

                return company
        except BaseException as e:
            print("Exception caught while triggering IPI with IP: ", e)
            traceback.print_exc()
            return None
    return company


def getCompanyByLinkedinId(linkedinId):
    try:
        #fetch from own database (no external APIs)
        data = db.execute('''
                    select companyId from companies
                    where linkedin=%s LIMIT 1;
                    ''', (linkedinId,))
        if len(data) > 0:
            dbId = data[0][0]
            return getCompanyById(dbId)
        else:
            data = db.execute('''
                        select company_ID from proxycurl
                        where linkedin_internal_id=%s LIMIT 1;
                        ''', (linkedinId,))
            if len(data) > 0:
                dbId = data[0][0]
                return getCompanyById(dbId)
            else:
                data = db.execute('''
                            select companyId from kickfire
                            where linkedin=%s LIMIT 1;
                            ''', (linkedinId,))
                if len(data) > 0:
                    dbId = data[0][0]
                    return getCompanyById(dbId)
                else:
                    return None
    except BaseException as e:
        traceback.print_exc()

def getCompanyByName(name):
    return __getCompanyByName(name, True)

def __getCompanyByName(name, removeCompanyType=False):
    try:
        #fetch from own database (no external APIs)
        print("searching ", name)
        data = db.execute('''
                    select companyId from companies
                    where companyName LIKE "%s" LIMIT 1;
                    ''', ('%' + name + '%',))

        if len(data) > 0:
            dbId = data[0][0]
            return getCompanyById(dbId)
        else:
            data = db.execute('''
                        select company_ID from proxycurl
                        where company_name LIKE %s LIMIT 1;
                        ''', ('%' + name + '%',))

            if len(data) > 0:
                dbId = data[0][0]
                return getCompanyById(dbId)
            else:
                data = db.execute('''
                            select companyId from kickfire
                            where companyName LIKE %s LIMIT 1;
                            ''', ('%' + name + '%',))

                if len(data) > 0:
                    dbId = data[0][0]
                    return getCompanyById(dbId)
                else:
                    data = db.execute('''
                                            select companyId from companyIpInfo
                                            where companyName LIKE %s LIMIT 1;
                                            ''', ('%' + name + '%',))
                    if len(data) > 0:
                        dbId = data[0][0]
                        return getCompanyById(dbId)
                    else:
                        if removeCompanyType:
                            # now try all above, but cut off training company type abbreviation
                            return __getCompanyByName(tryRemovingCompanyType(name))
                        else:
                            return None
    except BaseException as e:
        traceback.print_exc()
    return None

def getCompanyByWebsite(domain_org, queryAPI):
    company = None
    logging.info("getCompanyByWebsite: " + domain_org)
    try:
        if domain_org is not None:
            domain = StringHelper.clnWebsite(domain_org)


            data = db.execute('''
                select companyId from websites
                where website LIKE %s LIMIT 1;
                ''', ('%' + domain + '%',))

            if len(data) > 0:
                company = getCompanyById(data[0][0])
            if not company:
                company = pc.getCompanyByWebsite(domain, queryAPI)
        if company:
            logging.info("orig: " + domain_org + " | clean: " + domain + " | " + company.companyName + " (" + str(company.companyId) + ")")
        else:
            logging.info("orig: " + domain_org + " | clean: " + domain + " | not found")
        return company
    except BaseException as e:
        traceback.print_exc()
        return None

################################## INDUSTRY CODE CONVERSION ####################################################

def naics2sic(naics):
    try:
        values = (naics, 1)
        sql = "select target from industryCodeConversion where source=%s and type=%s"
        result1 = db.execute(sql, values)
        result = None

        if result1 is not None and len(result1)>0:
            result = result1[0][0]
        return result if result else None
    except BaseException as e:
        traceback.print_exc()
        return None

def linkedinLabel2code(linkedinLabel):
    try:
        values = (linkedinLabel, 3)
        sql = "select code from industryCodes where labelEn=%s and codeScheme=%s"
        result1 = db.execute(sql, values)
        result = None
        if result1 is not None and len(result1) > 0:
            result = result1[0][0]
        return result if result else None
    except BaseException as e:
        traceback.print_exc()
        return None

def sic2naics(sic):
    try:
        values = (sic, 2)
        sql = "select target from industryCodeConversion where source=%s and type=%s"
        result1 = db.execute(sql, values)
        result = None
        if result1 is not None and len(result1) > 0:
            result = result1[0][0]
        return result if result else None
    except BaseException as e:
        traceback.print_exc()
        return None

def sic2linkedin(sic):
    try:
        values = (sic, 3)
        sql = "select target from industryCodeConversion where source=%s and type=%s"
        result1 = db.execute(sql, values)
        result = None
        if result1 is not None and len(result1) > 0:
            result = result1[0][0]
        return result if result else None
    except BaseException as e:
        traceback.print_exc()
        return None


class Company:
    def __init__(self, companyName, companyId=None, logoDate=None, logoFileExtension=None, industry=None, wz2008Code=None,
                naicsCode=None, employees_0=None, employees_1=None, revenue_0=None, revenue_1=None, linkedin=None,
                 linkedInStringId=None, twitter=None, facebook=None, isISP=0, manualISP=0, createdOn=None, lastModifiedOn=None):
        self.companyName = companyName
        self.companyId = companyId
        self.logoDate = logoDate
        self.logoFileExtension = logoFileExtension
        self.industry = industry
        self.wz2008Code = wz2008Code
        self.naicsCode = naicsCode
        self.employees_0 = employees_0
        self.employees_1 = employees_1
        self.revenue_0 = revenue_0
        self.revenue_1 = revenue_1
        self.linkedin = linkedin
        self.linkedInStringId = linkedInStringId
        self.twitter = twitter
        self.facebook = facebook
        self.isISP = isISP
        self.manualISP = manualISP
        self.createdOn = createdOn
        self.lastModifiedOn = lastModifiedOn


    def save(self):
        try:
            if self.companyId is not None:
                sql = '''UPDATE `companies` set companyName=%s, logoDate=%s, logoFileExtension=%s, wz2008Code=%s,
                        naicsCode=%s, employees_0=%s, employees_1=%s, revenue_0=%s, revenue_1=%s, linkedin=%s, linkedInStringId=%s,
                        twitter=%s, facebook=%s, isISP=%s, manualISP=%s where companyId=%s'''
                values = (self.companyName, self.logoDate, self.logoFileExtension, self.wz2008Code, self.naicsCode,
                          self.employees_0, self.employees_1, self.revenue_0, self.revenue_1, self.linkedin, self.linkedInStringId,
                          self.twitter, self.facebook, self.isISP, self.manualISP, self.companyId)
                db.execute(sql, values, True)
            else:
                sql = '''INSERT INTO `companies` (companyName, logoDate, logoFileExtension, wz2008Code, naicsCode,
                        employees_0, employees_1, revenue_0, revenue_1, linkedin, linkedInStringId, twitter, facebook, isISP, manualISP)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                values = (self.companyName, self.logoDate, self.logoFileExtension, self.wz2008Code,
                          self.naicsCode, self.employees_0, self.employees_1, self.revenue_0, self.revenue_1,
                          self.linkedin, self.linkedInStringId, self.twitter, self.facebook, self.isISP, self.manualISP)

                self.companyId = db.execute(sql, values, True)
            print("Company ", self.companyName, "stored with companyId", self.companyId)
        except BaseException as e:
            traceback.print_exc()

    def delete(self):
        try:
            if self.companyId is not None:
                sql = '''DELETE FROM `companies` where companyId=%s'''
                values = (self.companyId, )
                db.execute(sql, values, True)
        except BaseException as e:
            traceback.print_exc()
            return None

    def enrich(self):
        #trigger ProxyCurl (and maybe others in future)
        ProxyCurlService.enrichCompany(self)

    def chooseBestFirmographics(self):
        try:
            print("trying to identify best Firmographics... for companyId ", self.companyId)
            sql = '''SELECT c.companyId, pc.company_name, pc.industry, pc.company_size_0, pc.company_size_1, pc.linkedin_internal_id, pc.extra_twitter_id, pc.extra_facebook_id, pc.manualISP, 
                  kf.companyName, kf.employees_0, kf.employees_1, kf.revenue_0, kf.revenue_1, kf.sicCode, kf.naicsCode, kf.twitter, kf.facebook, kf.linkedin, kf.isISP, kf.manualISP, 
                  ipi.companyName, ipi.isIsp, w.website, w.profile_li, w.profile_tw, w.profile_fb, c.companyName, c.linkedInStringId, pc.universal_name_id 
                  FROM (SELECT * from companies where companyId=%s) as c 
                  left JOIN proxycurl pc on c.companyId=pc.company_ID 
                  left JOIN kickfire kf on kf.companyId=c.companyId 
                  left JOIN websites w on w.companyId=c.companyId 
                  left JOIN companyIpInfo ipi on ipi.companyId=c.companyId
                  GROUP BY c.companyId;'''

            values = (self.companyId,)
            company1 = db.execute(sql, values)
            if company1 is not None and len(company1)>0:
                company = company1[0]

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
                industryNaicsKF = company[15] if company[15] else sic2naics(company[14])
                twitterKF = company[16]
                facebookKF = company[17]
                linkedinKF = company[18]
                ispKF = company[19]
                manualIspKF = company[20]
                nameIPI = company[21]
                ispIpi = company[22]
                linkedinWebsite = company[24]
                twitterWebsite = company[25]
                facebookWebsite = company[26]
                origCompanyName = company[27]
                linkedInStringId = company[28]
                linkedInStringIdPC = company[29]

                self.companyName = namePC if not (namePC is None or namePC == "Unauthorized") \
                    else nameIPI if nameIPI is not None \
                    else nameKF if nameKF is not None else origCompanyName
                self.wz2008Code = industrySicKF if industrySicKF is not None else industrySicPC
                self.naicsCode = industryNaicsKF if industryNaicsKF is not None else industryNaicsPC
                self.employees_0 = empl0PC if empl0PC is not None else empl0KF
                self.employees_1 = empl1PC if empl1PC is not None else empl1KF
                self.revenue_0 = rev0KF
                self.revenue_1 = rev1KF
                self.linkedin = linkedinPC if linkedinPC is not None else linkedinKF
                self.linkedInStringId = linkedInStringId if linkedInStringId is not None \
                    else linkedInStringIdPC if linkedInStringIdPC is not None \
                    else linkedinWebsite.split("linkedin.com/company/")[1].split("/")[0].split("&")[0].split("#")[0] \
                    if linkedinWebsite is not None else None
                self.twitter = twitterPC if twitterKF is not None else twitterPC if twitterPC is not None  else twitterWebsite
                self.facebook = facebookPC if facebookPC is not None else facebookKF if facebookKF is not None else facebookWebsite
                self.isISP = ispIpi if ispIpi is not None else ispKF if ispKF is not None else 0
                self.manualISP = manualIspKF if manualIspKF is not None else manualIspPC if manualIspPC is not None else 0

                self.save()
            else:
                print("company not found while trying to choose best firmographics: ", self.companyId)
        except BaseException as e:
            traceback.print_exc()

    def getSources(self, customer):
        try:
            sql ='''select cs.sourceId, cs.name, cs.colorCode
                from companySources cs
                join (SELECT source from companies_customers where customerId=%s and companyId=%s) as cc on cc.source = cs.sourceId
                '''
            data = db.execute(sql, (customer.customerId, self.companyId))
            sources = []
            for s in data:
                sources.append(Source(customer.customerId, s[1], s[2], s[0]))
            return sources
        except BaseException as e:
            traceback.print_exc()
            return None

    def getWebsites(self):
        return WebsiteService.getWebsitesOfCompany(self)

    def getFirmographics(self):
        try:
            data = db.execute('''
                SELECT companyName, concat('login.truffle.one/static/companylogos/', companyId , '.', logoFileExtension) as logoUrl,
                    employees_0, employees_1, revenue_0, revenue_1, pc.industry, wz2008Code, c.naicsCode,
                    pc.company_type, pc.extra_founding_date, pc.founded_year, i.labelLinkedin
                FROM (SELECT * from `companies` where companyId=%s) as c
                left join (SELECT labelLinkedin, naicsCode from industryCodesNaics) as i on c.naicsCode=i.naicsCode 
                left join (SELECT company_ID, company_type, extra_founding_date, founded_year, industry from proxycurl
                    where company_ID=%s) as pc on c.companyId = pc.company_ID
                ''', [self.companyId, self.companyId])
            if data is None or len(data) == 0:
                return None
            else:
                f = data[0]
                if f[11] is not None and f[11]!="":
                    foundingYear = f[11]
                elif f[10] is not None and len(str(f[10]))>=4:
                    foundingYear = str(f[10])[:4]
                else:
                    foundingYear = None

                industry = f[6] if f[6] is not None else  f[12]
                result = CompanyFirmographics(f[0], f[1], f[2], f[3], f[4], f[5], industry, f[7], f[8], f[9], foundingYear)
                return result
        except BaseException as e:
            traceback.print_exc()
            return None

    def getFinanceData(self):
        try:
            data = db.execute('''
                        SELECT extra_crunchbase_rank, funding_data, extra_number_of_funding_rounds,
                        extra_total_funding_amount, extra_total_fund_raised, extra_number_of_investors,
                        extra_number_of_lead_investors, extra_number_of_investments, extra_number_of_lead_investments,
                        exit_data, extra_number_of_exits, extra_number_of_acquisitions, acquisitions,
                        extra_ipo_status, extra_ipo_date, extra_stock_symbol
                        FROM proxycurl where company_ID=%s
                        ''', [self.companyId])
            if data is None or len(data) == 0:
                return None
            else:
                f = data[0]
                return CompanyFinanceData(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], f[10], f[11], f[12], f[13], f[14], f[15])
        except BaseException as e:
            traceback.print_exc()
            return None

    def getLinkedInData(self):
        try:
            data = db.execute('''
                        SELECT Linkedin_URL, linkedin_internal_id, universal_name_id, follower_count,
                        company_size_on_linkedin, description, tagline, updates
                        FROM proxycurl where company_ID=%s
                        ''', [self.companyId])
            if data is None or len(data) == 0:
                return None
            else:
                specialtiesSql = db.execute('''
                        SELECT specialities
                        FROM linkedin_specialties where companyId=%s
                        ''', [self.companyId])
                specialties = ""
                for index, s in enumerate(specialtiesSql):
                    if index == 0:
                        specialties += s[0]
                    else:
                        specialties += ", " + s[0]

                categoriesSql = db.execute('''
                        SELECT category
                        FROM linkedin_categories where companyId=%s
                        ''', [self.companyId])
                categories = ""
                for index, c in enumerate(categoriesSql):
                    if index == 0:
                        categories += c[0]
                    else:
                        categories += ", " + c[0]

                f = data[0]
                return CompanyLinkedinData(f[0], f[1], f[2], f[3], f[4], f[5], f[6],
                                           categories, specialties, f[7])
        except BaseException as e:
            traceback.print_exc()
            return None

    def getContactData(self):
        try:
            data = db.execute('''
                    SELECT extra_phone_number, extra_contact_email, extra_twitter_id, extra_facebook_id
                    FROM proxycurl where company_ID=%s
                    ''', [self.companyId])
            if data is None or len(data) == 0:
                return None
            else:
                f = data[0]
                return CompanyContactData(f[0], f[1], f[2], f[3])
        except BaseException as e:
            traceback.print_exc()
            return None

class CompanyLinkedinData:
    def __init__(self, profileUrl=None, numericId=None, stringId=None,
                 followerCount=None, employeesOnLinkedin=None,
                 description=None, tagline=None, categories=None, specialties=None,
                 updates=None,
                 profilePicUrl=None, backgroundCoverUrl=None, similarCompanies=None):
        self.profileUrl = profileUrl
        self.numericId = numericId
        self.stringId = stringId
        self.followerCount = followerCount
        self.employeesOnLinkedin = employeesOnLinkedin
        self.description = description
        self.tagline = tagline
        self.categories = categories
        self.specialties = specialties
        self.updates = updates
        self.profilePicUrl = profilePicUrl
        self.backgroundCoverUrl = backgroundCoverUrl
        self.similarCompanies = similarCompanies
class CompanyFinanceData:
    def __init__(self, crunchBaseRank=None, funding_data=None, fundingRoundsCount=None,
                 totalFundingAmount=None, totalfundRaised=None, investorsCount=None,
                 leadInvestorsCount=None, investmentsCount=None, leadInvestmentsCount=None,
                 exit_data=None, exitsCount=None, acquisitionsCount=None, acquisitions=None,
                 ipoStatus=None, ipoDate=None, stockSymbol=None):
        self.crunchBaseRank =crunchBaseRank
        self.funding_data = funding_data
        self.fundingRoundsCount = fundingRoundsCount
        self.totalFundingAmount =totalFundingAmount
        self.totalfundRaised = totalfundRaised
        self.investorsCount = investorsCount
        self.leadInvestorsCount = leadInvestorsCount
        self.investmentsCount = investmentsCount
        self.leadInvestmentsCount = leadInvestmentsCount
        self.exit_data = exit_data
        self.exitsCount = exitsCount
        self.acquisitionsCount = acquisitionsCount
        self.acquisitions = acquisitions
        self.ipoStatus = ipoStatus
        self.ipoDate = ipoDate
        self.stockSymbol = stockSymbol

class CompanyContactData:
    def __init__(self, phone=None, email=None, twitter=None, facebook=None):
        self.phone=phone
        self.email=email
        self.twitter=twitter
        self.facebook=facebook

class CompanyFirmographics:
    def __init__(self, companyName=None, logoUrl=None,
                 employees_0=None, employees_1=None, revenue_0=None, revenue_1=None,
                 linkedInIndustry=None,
                 sicCode=None, naicsCode=None, companyType=None, foundingYear=None):

        self.companyName = companyName
        self.logoUrl = logoUrl
        self.employees_0 = employees_0
        self.employees_1 = employees_1
        self.revenue_0 = revenue_0
        self.revenue_1 = revenue_1
        self.industry = linkedInIndustry
        self.sicCode = sicCode
        self.naicsCode = naicsCode
        self.companyType = companyType
        self.foundingYear = foundingYear
        self.sicLabelDe = None
        self.sicCatLevelDe1 = None
        self.sicCatLevelDe2 = None
        self.sicCatLevelDe3 = None
        self.sicCatLevelDe4 = None
        self.sicCatLevelDe5 = None
        self.sicCatLevelDe6 = None
        self.naicsLabelDe = None
        self.naicsCatLevelDe1 = None
        self.naicsCatLevelDe2 = None
        self.naicsCatLevelDe3 = None
        self.naicsCatLevelDe4 = None
        self.naicsCatLevelDe5 = None
        self.naicsCatLevelDe6 = None
        self.updateIndustryLabels()

    def updateIndustryLabels(self):
        try:
            data = db.execute('''
                SELECT labelDe, catLevelDe1, catLevelDe2, catLevelDe3,
                catLevelDe4, catLevelDe5, catLevelDe6 from industryCodes where codeScheme=%s and code=%s
                ''', (1, self.sicCode))
            if data is not None and len(data)>0:
                self.sicLabelDe = data[0][0]
                self.sicCatLevelDe1 = data[0][1]
                self.sicCatLevelDe2 = data[0][2]
                self.sicCatLevelDe3 = data[0][3]
                self.sicCatLevelDe4 = data[0][4]
                self.sicCatLevelDe5 = data[0][5]
                self.sicCatLevelDe6 = data[0][6]
            data = db.execute('''
                SELECT labelEn, catLevelEn1, catLevelEn2, catLevelEn3,
                catLevelEn4, catLevelEn5, catLevelEn6 from industryCodes where codeScheme=%s and code=%s
                ''', (2, self.naicsCode))
            if data is not None and len(data) > 0:
                self.naicsLabelEn = data[0][0]
                self.naicsCatLevelEn1 = data[0][1]
                self.naicsCatLevelEn2 = data[0][2]
                self.naicsCatLevelEn3 = data[0][3]
                self.naicsCatLevelEn4 = data[0][4]
                self.naicsCatLevelEn5 = data[0][5]
                self.naicsCatLevelEn6 = data[0][6]
        except BaseException as e:
            traceback.print_exc()
            return None

class Source:
    def __init__(self, customerId=None, name=None, colorCode=None, dbId=None):
        self.customerId = customerId
        self.name = name
        self.colorCode = colorCode
        self.dbId = dbId