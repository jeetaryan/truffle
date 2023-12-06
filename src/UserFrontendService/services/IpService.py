from services import DbConfig, WebsiteService, StringHelper, CompanyService
import datetime as dt
import requests
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

db = DbConfig.getDB()


################################################################## Update IP ranges ############################################
def checkIpRangeOverlap(ipRange):
    print("ip-Range is:", ipRange)
    ip = IPNetwork(ipRange)
    values = None
    sql = None
    if "." in ipRange:
        values = (ip.first, ip.first, ip.last, ip.last)
        sql = "SELECT rangeId FROM `ip_ranges` where (ipStartv4<%s AND ipEndv4>%s) OR (ipStartv4<%s AND ipEndv4>%s) LIMIT 1"
    elif ":" in ipRange:
        values = (format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.first)),
                  format(ipaddress.IPv6Address(ip.last)), format(ipaddress.IPv6Address(ip.last)))
        sql = "SELECT rangeId FROM `ip_ranges` where (ipStartv6<%s AND ipEndv6>%s) OR (ipStartv6<%s AND ipEndv6>%s) LIMIT 1"
    else:
        print("no valid IP Network:", ipRange)
        return 0

    s = db.execute(sql, values)

    if len(s) > 0:
        return 1
    else:
        return 0


def deleteIpRangeOverlaps(ipRange):
    ip = IPNetwork(ipRange)

    values = None
    sql = None
    if "." in ipRange:
        values = (ip.first, ip.first, ip.last, ip.last)
        sql = "DELETE FROM `ip_ranges` where (ipStartv4<%s AND ipEndv4>%s) OR (ipStartv4<%s AND ipEndv4>%s)"
    elif ":" in ipRange:
        values = (format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.first)),
                  format(ipaddress.IPv6Address(ip.last)), format(ipaddress.IPv6Address(ip.last)))
        sql = "DELETE FROM `ip_ranges` where (ipStartv6<%s AND ipEndv6>%s) OR (ipStartv6<%s AND ipEndv6>%s)"
    else:
        print("no valid IP Network:", ipRange)
        return 0
    db.execute(sql, values, True)

    return 1


def deleteIpRangesOf(companyId):
    db.execute("DELETE FROM `ip_ranges` where companyId=%s", (companyId,), True)



ipiKey = "ef809b112a5aa8"
def updateIpRangesByIpi(domain, companyId, forceEvenIfYoungData):
    try:

        if companyId is None and domain is not None:
            company = WebsiteService.getCompanyByWebsite(domain, True)
            if company is not None:
                companyId = company.companyId
        if domain == None and companyId is not None:
            domains = WebsiteService.getWebsitesOfCompany(CompanyService.getCompanyById(companyId))
            if domains and len(domains)>0:
                domain = domains[0]
        oldData = False

        if not forceEvenIfYoungData:
            sql = "select lastModifiedOn from ip_ranges where companyId=%s order by lastModifiedOn DESC LIMIT 1"
            values = (companyId,)
            result = db.execute(sql, values)
            if result and (result[0][0] < (dt.datetime.now() - dt.timedelta(weeks=8))):
                oldData = True

        if oldData or forceEvenIfYoungData:
            api_endpoint = "https://ipinfo.io/ranges/" + domain + "?token=" + ipiKey
            # print("   - query ipi")
            response = requests.get(api_endpoint, timeout=3)
            if response.status_code == 200:
                res = response.json()
                ranges = res.get("ranges")

                if ranges and len(ranges) > 0:
                    print("   - adding", len(ranges), "ip ranges for", domain, companyId)
                    # remove existing ip ranges of this company, because there here are brand new
                    deleteIpRangesOf(companyId)
                    for ipRange in ranges:
                        ip = IPNetwork(ipRange)

                        # remove ip ranges that overlap with the new ones because these here are newer
                        deleteIpRangeOverlaps(ipRange)

                        if "." in ipRange:
                            values = (companyId, ip.first, ip.last)

                            sql = "INSERT INTO ip_ranges( companyId, ipStartv4, ipEndv4) values (%s, %s,%s)"

                            db.execute(sql, values, True)
                        elif ":" in ipRange:
                            values = (
                            companyId, format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.last)))
                            sql = "INSERT INTO ip_ranges( companyId, ipStartv6, ipEndv6) values (%s, %s,%s)"
                            db.execute(sql, values, True)
                        else:
                            print("no valid IP Address: " + ipRange)

                else:
                    print("no ranges found: " + domain)
            else:
                print("error ipi" + str(response.status_code))


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
        asn = StringHelper.clnInt(data['asn'])
        asn_cidr = str(data['asn_cidr'])
        asn_country_code = str(data['asn_country_code'])
        asn_date = dt.datetime.strptime(data['asn_date'], '%Y-%m-%d').date()
        asn_registry = str(data['asn_registry'])
        asn_description = str(data['asn_description'])

        if asn:
            values = (asn,)
            sql = "SELECT * FROM ip_ranges_asn where asn=%s"

            s = db.execute(sql, values)

            if len(s) == 0:
                print("ASN", StringHelper.cln(asn))
                values = (
                StringHelper.cln(asn), StringHelper.cln(asn_cidr), StringHelper.cln(asn_country_code),
                StringHelper.cln(asn_date), StringHelper.cln(asn_registry), StringHelper.cln(asn_description))
                sql = "INSERT into ip_ranges_asn (asn, asn_cidr, asn_country_code, asn_date, asn_registry, asn_description) VALUES (%s,%s,%s,%s,%s,%s)"
                db.execute(sql, values, True)
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
                ipStart = StringHelper.ip2int(a)
                ipEnd = StringHelper.ip2int(b)

                value = (
                    companyId, asn, ipRange, ipStart, ipEnd, cidr, name, handle, description, country, state, city,
                    address, postal_code, created, updated)

                # print(value)
                print("   - IP-Range added from Whois")
                sql = "INSERT into ip_ranges (companyId, asn, ipRange, ipStartv4, ipEndv4, cidr, name, handle, rangeDescription, " \
                      "country, state, city, address, postal_code, createdDateTime, updatedDateTime)" \
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)"



                db.execute(sql, value, True)

                success = 1

    except BaseException as e:
        print("Exception caught while checking whois: ", e)
        traceback.print_exc()
    return success

