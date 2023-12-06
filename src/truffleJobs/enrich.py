from services import DbConfig, CompanyService

db = DbConfig.getDB()
customerIds = db.execute('''select c.companyId, cc.lastModifiedOn
from (SELECT companyId from companies where employees_0 is Null) as c
LEFT JOIN (SELECT companyId, lastModifiedOn from companies_customers where customerId=%s) as cc on cc.companyId=c.companyId
ORDER by cc.lastModifiedOn DESC;
            ''', (79,))




for c in customerIds:
    company = CompanyService.getCompanyById(c[0])
    company.enrich()
    company.chooseBestFirmographics()
    print("-----> Enriched", company.companyName, ", e.g. employees_0=", company.employees_1, "industry=", company.industry)
