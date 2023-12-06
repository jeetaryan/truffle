from services import DbConfig, CompanyService

db = DbConfig.getDB()

def getCustomerWebsite(customer):
    #todo
    return CustomerWebsite()
class CustomerWebsite:
    def __init__(self):
        #todo: constructor
        return

    #todo: getTrackingcode()
    #todo: getVisitsOfPeriod(from, till)
    #todo: getVisitsOfCompany(company)

class WebsiteVisit:
    def __init__(self):
        self.visitId = visitId
        self.ipAddress_int = ipAddress_int
        companyId = companyId