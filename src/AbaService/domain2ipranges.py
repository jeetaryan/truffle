from csv import reader
import requests
import mysql.connector
from netaddr import *
import traceback
import ipaddress
import urllib.parse
import tldextract
import time
import csv
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import datetime

#read file with domain names to be imported as campaign target accounts
# works fine 2023-03-16 Niko
# for each line
# query ipfind
# construct ipnetaddr 
# store ip.start and ip.end in campaignranges
# remove existing ipranges from ip ranges and store new with existing companyId?


cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)


########################### HARDCODING ###########################
# t3n
customerId = 4
campaignId = 25
file1 = open('t3n-targets.txt', 'r')
resultFile = open('t3n-forecast.csv', 'w')
startDate = datetime.datetime.now() - datetime.timedelta(weeks=4)
########################### END OF HARDCODING ####################

domains = file1.readlines()
writer = csv.writer(resultFile)
writer.writerow(['Given', 'Considered', 'Status', 'numberOfRanges', 'forecast'])
# Iterate over each row in the csv using reader object
countRanges = 0


importedCompanies = set()

for domain in domains:
    domain = domain.strip()
    domain2 = domain
    domain2test = domain
    result = "OK"
    numberOfRanges = 0



    ###################
    ##### start counter
    counter = 0
    ##### end counter
    ###################

    if domain[1:4] != "http":
        domain2test = "https://" + domain
    
    # row variable is a list that represents a row in csv
    #print("################################ ", domain)
    
    # check if valid domain
    validDomain = 1
    val = URLValidator()
    try:
        val(domain2test)
        validDomain = 1
    except ValidationError:
        validDomain = 0

            
    if domain and result=="OK":
        
        extracted = tldextract.extract(domain)
        domain = "{}.{}".format(extracted.domain, extracted.suffix)
                
        if domain not in importedCompanies:
            importedCompanies.add(domain)
            try:
                api_endpoint = "https://ipinfo.io/ranges/" + domain + "?token=ef809b112a5aa8"
                response = requests.get(api_endpoint)
                if response.status_code == 200:
                    res = response.json()
                    print(res)
                    numberOfRanges = res.get("num_ranges")
                    ranges = res.get("ranges")
                    
                    if ranges:
                        for ipRange in ranges:
                            countRanges+=1
                            ip = IPNetwork(ipRange)
                            
                            #print(domain, "range:", ipRange, " start:", ip.first, "end:", ip.last)
                            
                            if "." in ipRange:
                                values= (campaignId, customerId, domain, ip.first, ip.last, 0)
                                sql = "INSERT INTO campaignRanges( campaignId, customerId, domain, ipStartv4, ipEndv4, active) values (%s, %s,%s,%s,%s,%s)"
                                cursor.execute(sql, values)
                                cnx.commit()

                                ###################
                                ##### start counter
                                cursor.execute('''
                                    SELECT count(*) from visits where
                                        lastModifiedOn > %s and
                                        ipAddress_int >= %s and
                                        ipAddress_int <= %s and
                                        customerId = %s
                                        ''', (startDate, ip.first, ip.last, customerId))
                                data = cursor.fetchall()
                                if data and len(data) > 0:
                                    counter += data[0][0]
                                ##### end counter
                                #################

                            elif ":" in ipRange:
                                values= (campaignId, customerId, domain, format(ipaddress.IPv6Address(ip.first)), format(ipaddress.IPv6Address(ip.last)), 0)
                                sql = "INSERT INTO campaignRanges( campaignId, customerId, domain, ipStartv6, ipEndv6, active) values (%s, %s,%s,%s,%s,%s)"
                                cursor.execute(sql, values)
                                cnx.commit()
                            else:
                                result = "targeting not possible"
                                raise ValueError("no valid IP Address: " + ipRange)
                    else:
                        error = res.get("error")
                        if error:
                            result= "error II-" + error
                else:
                    result= "error II" + str(response.status_code)
            except BaseException as e:
                #print("Exception caught while importing from ipinfo: ", e)
                traceback.print_exc()
                result = "targeting not possible"
        else:
            result = "OK"




    writer.writerow([domain2, domain, result, numberOfRanges, counter])
    print(domain2, ",", domain, ",", result, ",", numberOfRanges, ",", counter)

resultFile.close()
cursor.close()
cnx.close()