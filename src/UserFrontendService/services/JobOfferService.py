import requests
import datetime as dt
from services import DbConfig, CompanyService
#from CompanyService import Company

# create db_connection
db = DbConfig.getDB()

def getJobOfferSearchGroups(customer):
    #cid = customer.customerId
    sql = '''
        SELECT a.id, a.name, a.type, a.createdOn, a.lastModifiedOn, b.id, b.keyword, b.job_type,
        b.experience_level, b.when_, b.flexibility, b.geo_id, b.search_id, b.processed, b.createdOn, b.lastModifiedOn
        FROM (SELECT * from `jobOfferSearchGroups` where owner=%s) as a
        LEFT JOIN jobOfferSearches b on a.id=b.jobOfferGroup
        ORDER BY a.id;
        '''
    values = (customer.customerId, )
    data = db.execute(sql, values)

    josgs = []
    josg = None
    for d in data:
        if josg is None or josg.dbId != d[0]:
            #new Josg
            josg = JobOfferSearchGroup(d[1], customer, d[2], d[0])
            josgs.append(josg)
        if d[6] is not None:
            josg.jobOfferSearches.append(JobOfferSearch(josg, d[6], d[11], d[7], d[8], d[9], d[10], d[12], d[5], d[13]))
    return josgs

def getJobOfferSearchGroup(id):
    sql = '''
        SELECT a.owner, a.name, a.type, a.createdOn, a.lastModifiedOn, b.id, b.keyword, b.job_type,
        b.experience_level, b.when_, b.flexibility, b.geo_id, b.search_id, b.processed, b.createdOn, b.lastModifiedOn
        FROM (SELECT * from `jobOfferSearchGroups` where id=%s) as a
        LEFT JOIN jobOfferSearches b on a.id=b.jobOfferGroup
        '''
    values = (id,)
    data = db.execute(sql, values)

    josg = None
    for idx, d in enumerate(data):
        if idx == 0:
            josg = JobOfferSearchGroup(d[1], d[0], d[2], id)
        if d[6] is not None:
            josg.jobOfferSearches.append(JobOfferSearch(josg, d[6], d[11], d[7], d[8], d[9], d[10], d[12], d[5], d[13]))
    return josg

def getJobOfferSearch(id):
    sql = '''
        SELECT jobOfferGroup FROM jobOfferSearches where id=%s
        '''
    values = (id,)
    data = db.execute(sql, values)
    d = data[0]
    josg = getJobOfferSearchGroup(d[0])
    jos = josg.getJobOfferSearch(id)
    return jos

def getJobOfferSearchResult(id):
    # todo
    return

def getJobOfferSearchResults(jobOfferSearch):
    # todo
    return

def processAllJobOfferSearchTasks():
    oneMonthAgo = dt.date.today() - dt.timedelta(months=1)
    sql = '''
        select `jobOfferGroup`, `keyword`, `geo_id`, `job_type`, `experience_level`,
        `when_`, `flexibility`,  `search_id`, 'id', processed
        from jobOfferSearches where processed < %s'''
    values = (oneMonthAgo, )
    data = db.execute(sql, values)


    count = 0
    for j in data:
        JobOfferSearch(getJobOfferSearchGroup(j[0]), j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]).process()
        count += 1
    print("processed", count, "JobOfferSearch tasks.")
    return count




class JobOfferSearchGroup:
    # consists of a list of JobOfferSearch objects
    def __init__(self, name, ownerCustomer, type = 0, dbId=None):
        self.name = name
        self.jobOfferSearches = []
        self.owner = ownerCustomer
        self.type = type #0=identify, 1=qualify
        self.dbId = dbId

    def save(self):
        sql = '''INSERT INTO `jobOfferSearchGroups` (`name`, `owner`, `type`)
                    VALUES (%s, %s, %s)'''
        values = (self.name, self.owner, self.type)
        if self.dbId is not None:
            sql = '''UPDATE `jobOfferSearchGroups` set `name`=%s, `owner`=%s, `type`=%s where id=%s'''
            values = (self.name, self.owner, self.type, self.dbId)
        self.dbId = db.execute(sql, values, True)

        for jos in self.jobOfferSearches:
            jos.save()

    def delete(self):
        if self.dbId is not None:
            sql = '''DELETE FROM `jobOfferSearchGroups` where id=%s'''
            values = (self.dbId,)
        db.execute(sql, values, True)


    def process(self):
        for jos in self.jobOfferSearches:
            jos.process()

    def getJobOfferSearch(self, dbId):
        for jos in self.jobOfferSearches:
            if jos.dbId == dbId:
                return jos
        return None


class JobOfferSearch:
    def __init__(self, jobOfferSearchGroup, keyword, geo_id=101282230, job_type=None, experience_level=None, when=None,
                 flexibility=None, search_id=None, dbId=None, processed=None):
        self.dbId = dbId
        self.keyword = keyword
        self.jobOfferSearchGroup = jobOfferSearchGroup

        # 101282230 = Germany
        self.geo_id = geo_id

        # for future use:
        self.job_type = job_type
        self.experience_level = experience_level
        self.when = when
        self.flexibility = flexibility
        self.search_id = search_id
        self.processed = processed

    def save(self):
        sql = '''INSERT INTO `jobOfferSearches` (`jobOfferGroup`, `keyword`, `job_type`, `experience_level`,
            `when_`, `flexibility`, `geo_id`, `search_id`, `processed`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        values = (self.jobOfferSearchGroup.dbId, self.keyword, self.job_type, self.experience_level,
                  self.when, self.flexibility, self.geo_id, self.search_id, self.processed)
        if self.dbId is not None:
            sql = '''UPDATE `jobOfferSearches`  set `keyword`=%s, `job_type`=%s,
                `experience_level`=%s, `when_`=%s, `flexibility`=%s, `geo_id`=%s, `search_id`=%s, `processed`=%s
                where id=%s'''
            values = (self.keyword, self.job_type, self.experience_level,
                      self.when, self.flexibility, self.geo_id, self.search_id, self.processed, self.dbId)
        self.dbId = db.execute(sql, values, True)


    def delete(self):
        if self.dbId is not None:
            sql = '''DELETE FROM `jobOfferSearches` where id=%s'''
            values = (self.dbId, )
            db.execute(sql, values, True)


    def process(self):
        #delete job offer search results of this jos
        josrs = getJobOfferSearchResults(self)
        for josr in josrs:
            josr.delete()

        josResults = []
        api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin/company/job'
        api_key = 'ipW9Gdbl0mWW3iwHjnXvCg'
        header_dic = {'Authorization': 'Bearer ' + api_key}
        params = {
            # 'job_type': 'anything',
            # 'experience_level': 'entry_level',
            # 'when': 'past-month',
            # 'flexibility': 'remote',
            'keyword': self.keyword,
            'geo_id': self.geo_id,
            # 'search_id': '1035',
        }
        response = requests.get(api_endpoint,
                                params=params,
                                headers=header_dic)
        jsonData = response.json()

        if "job" in jsonData:
            jobs = jsonData.get('job')
            josResults + (self.__processJsonJobs(jobs))

        while "next_page_api_url" in jsonData:
            pagingUrl = jsonData.get('next_page_api_url')
            response = requests.get(pagingUrl,
                                    headers=header_dic)
            jsonData = response.json()
            if "job" in jsonData:
                jobs = jsonData.get('job')
                josResults + (self.__processJsonJobs(jobs))

        #assign targets to customer
        owner = self.jobOfferSearchGroup.owner
        for josr in josResults:
            owner.assignTarget(josr.company, 3)

        # update processed date
        self.processed = dt.date.today()
        self.save()
        return josResults

    def __processJsonJobs(self, jsonArray):
        josResults = []
        for job in jsonArray:
            companyLinkedinUrl = job.get("company_url")

            #todo: try to lookup companyId or create one
            company = CompanyService.getCompanyByLinkedinUrl(companyLinkedinUrl)
            if company is None:
                companyName = job.get("company")
                company = CompanyService.getCompanyByName(companyName)
                if company is None:
                    company = CompanyService.Company(companyName)
                    company.linkedInStringId = companyLinkedinUrl.split("linkedin.com/company/")[1].split("/")[0].split("&")[0].split("#")[0]
                    company.save()
                    company.enrich()
                    company.chooseBestFirmographics()

            job_title = job.get("job_title")
            job_url = job.get("job_url")
            list_date = job.get("list_date")
            location = job.get("location")

            josr = JobOfferSearchResult(self, company, job_title, job_url, list_date, location)
            josr.save()
            josResults.append(josr)
        return josResults

class JobOfferSearchResult:
    def __init__(self, jobOfferSearch, company, job_title, job_url, list_date, location, customerCompanyAssignment=None, resultId=None ):
        self.resultId = resultId
        self.jobOfferSearch = jobOfferSearch
        self.company = company
        self.job_title = job_title
        self.job_url = job_url
        self.list_date = list_date
        self.location = location
        self.createdOn = None
        self.lastModifiedOn = None
        self.customerCompanyAssignment = customerCompanyAssignment

    def save(self):
        if self.customerCompanyAssignment is None:
            self.customerCompanyAssignment = self.jobOfferSearch.jobOfferSearchGroup.owner.assignTargetCompany(self.company, 3)
        if self.resultId is None:
            sql = "INSERT INTO `jobOfferSearchResults` (`jobOfferSearch`, `companyId`, `job_title`, `job_url`, `list_date`, `location`, customerCompanyAssignment) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (
                self.jobOfferSearch.dbId, self.company.dbId, self.job_title, self.job_url, self.list_date,
                self.location, self.customerCompanyAssignment)
            db.execute(sql, values, True)

        else:
            sql = "UPDATE `jobOfferSearchResults` set `jobOfferSearch`=%s, `companyId`=%s, `job_title`=%s, `job_url`=%s, `list_date`=%s, `location`=%s customerCompanyAssignment=%s where resultId=%s)"
            values = (self.jobOfferSearch.dbId, self.company.dbId, self.job_title, self.job_url, self.list_date,
                      self.location, self.customerCompanyAssignment, self.resultId)
            db.execute(sql, values, True)




    def delete(self):
        if self.customerCompanyAssignment is not None:
            self.jobOfferSearch.jobOfferSearchGroup.owner.removeTargetCompanyAssignment(self.customerCompanyAssignment)
        if self.resultId is not None:
            sql = '''DELETE FROM `companies_customers` where id = (SELECT customerCompanyAssignment from jobOfferSearchResults where resultId=%s);'''
            values = (self.resultId,)
            db.execute(sql, values, True)
            sql = '''DELETE FROM `jobOfferSearches` where resultId=%s'''
            values = (self.resultId,)
            db.execute(sql, values, True)
