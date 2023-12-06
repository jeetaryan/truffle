from services import DbConfig
import re
import requests

# creating connection
db = DbConfig.getDB()


def getContactByEmail(email, queryAPI):
    contact = None
    #todo get contact from email
    # first try in own DB

    # then query PC
    if not contact and queryAPI:
        lookupContactDetailsFromProxyCurl(email)
    return contact


def lookupContactDetailsFromProxyCurl(email):
    api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/profile/resolve/email'
    api_key = 'ipW9Gdbl0mWW3iwHjnXvCg'
    header_dic = {'Authorization': 'Bearer ' + api_key}
    domain_name = email.split('@')[1]
    # email = 'danial@nubela.co'
    params = {
        'work_email': email,
        'enrich_profile': 'enrich',
    }
    response = requests.get(api_endpoint,
                            params=params,
                            headers=header_dic)
    pcData = response.json()
    deductedData = deductContactDetailsFromEmail(email)

    if len(pcData) <= 1:
        return deductedData

    else:
        first_name = ""
        last_name = ""
        gender = ""
        if deductedData is not None:
            first_name = deductedData['first_name']
            last_name = deductedData['last_name']
            gender = deductedData['gender']
            company_name = deductedData['company_name']
        if pcData is not None:
            if first_name == "": first_name = pcData.get('profile')['first_name']
            if last_name == "": last_name = pcData.get('profile')['last_name']
            if gender == "":
                gender = 0 if pcData.get('profile')['gender'] == "Male" \
                    else 1 if pcData.get('profile')['gender'] == "Female" \
                    else 2

            if company_name == "": company_name = pcData.get('profile')['experiences'][-1]['company']
        linkedin_url = pcData.get('url')
        dict_data = {'first_name': first_name, 'last_name': last_name, 'gender': gender, 'company_name': company_name,
                     'linkedin_url': linkedin_url, 'email': email, 'domain_name': domain_name}
        return dict_data


def deductContactDetailsFromEmail(email):
    username = email.split('@')[0]
    domain_name = email.split('@')[1]
    first_name = ""
    last_name = ""
    gender = ""
    company_name = ""

    if username is not None:
        data = re.split(pattern=r"[-_\|\.\+ ]", string=username)

        if len(data) > 1:

            # lets check for firstname.lastname@company.com
            contactsgenderlookup_data = db.execute("select gender from contactsGenderLookup where firstName=%s", [data[0]])

            if contactsgenderlookup_data is not None and len(contactsgenderlookup_data) >0:
                gender = contactsgenderlookup_data[0][0]
                first_name = data[0].title()
                last_name = data[1].title()
            else:
                # lets check for lastname.firstname@company.com
                contactsgenderlookup_data = db.execute("select gender from contactsGenderLookup where firstName=%s", [data[1]])
                if contactsgenderlookup_data is not None and len(contactsgenderlookup_data) >0:
                    gender = contactsgenderlookup_data[0][0]
                    first_name = data[1].title()
                    last_name = data[0].title()

            if domain_name is not None:
                companies_name = db.execute("select a.companyName, a.companyId from companies a join (SELECT * from websites where website=%s) as b on b.companyId = a.companyId", [domain_name])
                if companies_name is not None and len(companies_name)>0:
                    company_name = companies_name[0][0]

    dict_data = {'first_name': first_name, 'last_name': last_name, 'gender': gender,
                 'company_name': company_name, 'linkedin_url': '', 'email': email, 'domain_name': domain_name}
    return dict_data


def guessGenderByFirstName(name):
    gender = None
    try:
        sql = "SELECT gender from contactsGenderLookup where firstName=%s LIMIT 1"
        values = (name,)
        gender = None
        genderSQL = db.execute(sql, values)
        if genderSQL is not None and len(genderSQL)>0:
            gender = genderSQL[0][0]
        return gender
    except BaseException as e:
        print("Exception caught while checking whois: ", e)
        traceback.print_exc()
        return gender


def guessGenderOfContactId(contactId, updateContact):
    gender = None
    try:
        sql = "SELECT b.gender FROM (SELECT firstName from contacts where contactId=%s) as a left JOIN contactsGenderLookup b ON a.firstName = b.firstName"
        values = (contactId,)

        genderSQL = db.execute(sql, values)
        if genderSQL is not None and len(genderSQL)>0:
            gender = genderSQL[0][0]
            if updateContact:
                sql = "UPDATE contacts set gender=%s where contactId=%s"
                values = (gender, contactId)
                db.execute(sql, values, True)
        return gender
    except BaseException as e:
        print("Exception caught while checking whois: ", e)
        traceback.print_exc()
        return gender


def guessGenderByFirstName(name):
    gender = None
    try:
        sql = "SELECT gender from contactsGenderLookup where firstName=%s LIMIT 1"
        values = (name,)
        genderSQL = db.execute(sql, values)
        if genderSQL is not None and len(genderSQL)>0:
            gender = genderSQL[0][0]
        return gender
    except BaseException as e:
        print("Exception caught while checking whois: ", e)
        traceback.print_exc()
        return gender


def guessGenderOfContactId(contactId, updateContact):
    gender = None
    try:
        sql = "SELECT b.gender FROM (SELECT firstName from contacts where contactId=%s) as a left JOIN contactsGenderLookup b ON a.firstName = b.firstName"
        values = (contactId,)
        genderSQL = db.execute(sql, values)
        if gender is not None and len(genderSQL)>0:
            gender = genderSQL[0][0]
            if updateContact:
                sql = "UPDATE contacts set gender=%s where contactId=%s"
                values = (gender, contactId)
                db.execute(sql, values, True)
        return gender
    except BaseException as e:
        print("Exception caught while checking whois: ", e)
        traceback.print_exc()
        return gender

class Contact:
    def __init__(self, firstname=None, lastname=None, email=None, company=None, dbId=None):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.company = company
        self.dbId = dbId
        #todo more attributes

    def save(self):
        #todo save contact
        return

    def delete(self):
        #todo delete contact
        return