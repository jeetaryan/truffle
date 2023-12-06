import time
import requests
import mysql.connector
from  translation6 import mayWeQueryProxycurl, pcKey, clnUrlFromParameters, countProxycurlData
from flask import json
import traceback





#gets contactId of a contact
def LinkedinContactProfile2contactId(linkedinContactProfileUrl, customerId):
#1. in contacts table, lookup contactID from linkedinContactProfileUrl
#2. if not found or not owned by customerId: LinkedinContactProfile2contactIdByProxyCurl(linkedinContactProfileUrl, customerId)
#3. return contactId


    print("     - query pc by linkedin contact profile")
    global countProxycurlData
    # Getting data from proxycurl using company linkeding url
    if (linkedinContactProfileUrl != "" and linkedinContactProfileUrl != None and  mayWeQueryProxycurl()):
        try:
            if linkedinContactProfileUrl[0:4]=="http":
                linkedinContactProfileUrl = clnUrlFromParameters(linkedinContactProfileUrl)
                
                if linkedinContactProfileUrl[len(linkedinContactProfileUrl)-1]=="/": linkedinContactProfileUrl = linkedinContactProfileUrl[0:len(linkedinContactProfileUrl)-1] 
                websiteSplit = linkedinContactProfileUrl.rsplit('/', 1)
                if len(websiteSplit) > 1:
                    linkedinContactProfileUrl = websiteSplit[1]
            

            linkedinContactProfileUrl = "https://www.linkedin.com/in/" + str(linkedinContactProfileUrl) + "/"
            print(linkedinContactProfileUrl)
            api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
            header_dic = {'Authorization': 'Bearer ' + pcKey}

            params = {
            'url': linkedinContactProfileUrl,
            'fallback_to_cache': 'on-error',
            'use_cache': 'if-present',
            'skills': 'include',
            'inferred_salary': 'include',
            'personal_email': 'include',
            'personal_contact_number': 'include',
            'twitter_profile_id': 'include',
            'facebook_profile_id': 'include',
            'github_profile_id': 'include',
            'extra': 'include',
            }
            
            response = requests.get(api_endpoint,
                                    params=params,
                                    headers=header_dic)
            
            countProxycurlData += 1
            
            print(response.json())

        except BaseException as e:
            print("Exception caught while triggering proxycurl with linkedin profile id: ", e)
            traceback.print_exc()


#query Proxycurl API to get contactInfo (and trigger getting the companyId of the current employer)
'''
def LinkedinContactProfile2contactIdByProxyCurl(linkedinContactProfileUrl, customerId):
1. Proxycurl "Person Profile Endpoint" -> gets contactInfo 
2. use companyId you get from linkedinCompanyProfileUrl2companyId(linkedinCompanyProfileUrl)
3. return contactId

#gets a companyId
def linkedinCompanyProfileUrl2companyId(linkedinCompanyProfileUrl):
1. lookup companyId from companies table
2. if no result: linkedinCompanyProfileUrl2companyIdByProxyCurl()
3. return companyId

#query proxycurl API to get companyInfo
def linkedinCompanyProfileUrl2companyIdByProxyCurl(linkedinCompanyProfileUrl):
1. Proxycurl "Company Profile Endpoint" -> gets LinkedIn-Company-Profile
2. store proxycurl table
3. run chooseBestFirmographics(companyId) as defined in translation6.py
4. return companyId
'''
            
LinkedinContactProfile2contactId("https://www.linkedin.com/in/lorenzfanelli/", 100)