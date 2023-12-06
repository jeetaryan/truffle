from services import CompanyService as cs
from services import ProxyCurlService as pc
from services import CustomerService as custServ
from services import SegmentsService as ss
from services import WebsiteService as ws
import pandas as pd
import numpy as np



def importCompanies(filename, customer=None, segment=None):
    df = pd.read_excel(filename)
    counter = 0

    for row in df.itertuples(index=True):
        print("importing company", row[1], "with domain:", row[0])
        companyName = str(row[1]) if (str(row[1]) != "nan" and row[1] is not None) else None
        domain = str(row[2]) if (str(row[2]) != "nan" and row[2] is not None) else None
        company = None

        print("searching by domain", domain)
        # try to match with existing company
        company = cs.getCompanyByWebsite(domain, False)

        if company is None:
            print("not found, now searching by name", companyName)
            company = cs.getCompanyByName(companyName)

        if company is None:
            print("not found, now querying 3rd party API by domain", domain)
            company = cs.getCompanyByWebsite(domain, True)

        if company is None:
            print("not found, creating new company", companyName, "/", domain)
            company = cs.Company(companyName)
            company.save()

        print("imported company", company.companyName, "(ID:", company.companyId, ")")
        counter +=1

        # add website if not existing yet
        if domain is not None:
            websites = company.getWebsites()
            exists = False
            for website in websites:
                if website.website is not None and domain is not None and website.website == domain:
                    exists = True
            if exists == False:
                print("adding website", domain , "to company")
                w = ws.Website(domain, company)
                w.save()

        # assign company to customer
        if customer is not None:
            print("assigning company", companyName, "(", company.companyId, ") to customer", customer.customerName, "(", customer.customerId,")")
            customer.assignTargetCompany(company, 0)

        #assign company to segment
        if segment is not None:
            print("assigning company", companyName, "(", company.companyId, ") to segment", segment.name, "(", segment.id,")")
            segment.addCompany(company)
    print("imported", counter, "companies")

importCompanies("import.xlsx", custServ.getCustomer(79), ss.getSegment(3))
