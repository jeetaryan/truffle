from services import DbConfig

db = DbConfig.getDB()



def getCustomer(customerId):
    # returns the customer with given id as stored in DB
    customers = db.execute('''
            select customerName, type, active, createdOn from customer
            where customerId=%s;
            ''', (customerId,))
    if len(customers) > 0:
        c = customers[0]
        return Customer(c[0], c[1], c[2], customerId, c[3])
    else:
        return None

def getAllCustomers():
    # returns the customer with given id as stored in DB
    customers = db.execute('''
            select customerName, type, active, createdOn, customerId from customer
            ''', )
    customers = []
    for c in customers:
        customers.append(Customer(c[0], c[1], c[2], c[4], c[3]))
    return customers

def getAllBusinessCustomers():
    # returns the customer with given id as stored in DB
    customerSQL = db.execute('''
            select customerName, type, active, createdOn, customerId from customer where type=%s
            ''', (0,) )
    customers = []
    for c in customerSQL:
        customers.append(Customer(c[0], c[1], c[2], c[4], c[3]))
    return customers

class Customer:
    def __init__(self, customerName=None, type=0, active=1, customerId=None, createdOn=None):
        self.customerName = customerName
        self.type = type
        self.active = active
        self.customerId = customerId
        self.createdOn = createdOn

    def __eq__(self, other):
        return self.customerId == other.customerId

    def __hash__(self):
        return hash(self.customerId)

    def __str__(self):
        return self.customerName + " (" + str(self.customerId) + ")"

    def assignTargetCompany(self, company, source):
        sql = '''INSERT INTO companies_customers(companyId, source, customerId) values(%s,%s,%s)
                ON DUPLICATE KEY update source=%s
              '''
        values = (company.companyId, source, self.customerId, source)
        id = db.execute(sql, values, True)
        return id

    def removeTargetCompany(self, company, source=None):
        sql = "DELETE FROM companies_customers where companyId=%s"
        values = (company.companyId, )
        if source is not None:
            sql = "DELETE FROM companies_customers where companyId=%s and source=%s and customerId=%s"
            values = (company.companyId, source, self.customerId)
        db.execute(sql, values, True)

    def removeTargetCompanyAssignment(self, id):
        db.execute("DELETE FROM companies_customers where id=%s", (id,), True)
