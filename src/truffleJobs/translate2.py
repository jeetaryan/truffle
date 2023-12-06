from services import CustomerService, DbConfig, CompanyService

import datetime as dt


db = DbConfig.getDB()
def translateForBusinessesRecentMin(recentMinutes):
    customers = CustomerService.getAllBusinessCustomers()
    print("# customers:", len(customers))
    for c in customers:
        translateRecentMin(recentMinutes, c)

def translateRecentMin(recentMinutes, customer):
    endTime = dt.datetime.now()
    startTime = endTime - dt.timedelta(minutes=recentMinutes)
    visits = db.execute('''
        SELECT visitId, ipAddress_int FROM `visits` 
        where companyId is null and customerId= %s and visitTime>%s
        order by visitTime ASC
        ''',  (customer.customerId, startTime))
    print("Translating", len(visits), " visits for customer ", customer.customerName, "(", customer.customerId, ")")
    for visit in visits:
        company = CompanyService.getCompanyByIpInt(visit[1], True)
        if company is not None:
            db.execute("UPDATE visits set companyId=%s where visitId=%s", (company.companyId, visit[0]), True)
            print("- translated visit to ", company.companyName, "(", company.companyId,")")
        else:
            print("- cannot tranlate visit with IP address", visit[1])

translateForBusinessesRecentMin(60)