





'''
{
  "condition": "AND",
  "rules": [
    {
      "id": "segment",
      "field": "segment",
      "type": "string",
      "input": "select",
      "operator": "equal",
      "value": "Bestandskunden"
    },
    {
      "id": "employees_0",
      "field": "employees_0",
      "type": "integer",
      "input": "text",
      "operator": "equal",
      "value": 4
    },
    {
      "id": "utm_medium",
      "field": "utm_medium",
      "type": "string",
      "input": "text",
      "operator": "equal",
      "value": "555"
    }
  ],
  "valid": true
}

'''
















Def Class rule:
# abstract Rule ist ...
# - entweder ein col, ein Operator, eine value
# - oder eine group

Def Class rulecondition(rule):
Self.col
Self.operator
Self.value

Def Class rulegroup(rule):
Self.grouptype
Self.rules[]




class SqlComponent:
    def __init__(self, columnNameHere, tableNameHere, joinColumnNameHere=None, joinTableNameThere=None, joinColumnNameThere=None):
        self.c = columnNameHere
        self.t = tableNameHere
        self.jch = joinColumnNameHere
        self.jt = joinTableNameThere
        self.jtt = joinColumnNameThere

class FilterAttribute:
    __validValues = None
    # return dict of key-value pairs
    # return null if any values is allowed

    TYPE_boolean = 1
    TYPE_int = 2
    TYPE_date = 3
    TYPE_string = 4
    TYPE_select = 5

    def __init__(self, name, type, dbId, validValues = None):
        self.name = name
        self.type = type
        self.dbId = dbId
        FilterAttribute.validValues = validValues

class FilterAttributeRevenueLower(FilterAttribute):
    def __init__(self):
        super().__init__("Umsatz min.", FilterAttribute.TYPE_int, 1 )

    def getValidValues(self, customer):
        if FilterAttributeRevenueLower.__validValues is None:
            data = db.execute("select distinct revenue_0 from companies")
            FilterAttributeRevenueLower.__validValues = []
            for d in data:
                FilterAttributeRevenueLower.__validValues.append((d[0], d[0]))
        return FilterAttributeRevenueLower.__validValues

    def getSqlComponents(self):
        result = []
        result.append(SqlComponent("revenue_0", "companies"))
        return result

class FilterAttributeIndustry(FilterAttribute):
    def __init__(self):
        super().__init__("Branche", FilterAttribute.TYPE_select )

    def getValidValues(self, customer):
        if FilterAttributeIndustry.__validValues is None:
            data = db.execute("SELECT distinct labelLinkedIn FROM `industryCodesNaics`")
            FilterAttributeIndustry.__validValues = []
            for d in data:
                FilterAttributeIndustry.__validValues.append((d[0], d[0]))
        return FilterAttributeIndustry.__validValues

    def getSqlComponents(self):
        result = []
        result.append(SqlComponent("naicsCode", "companies"))
        result.append(SqlComponent("labelLinkedIn", "industryCodesNaics", "naicsCode", "companies", "naicsCode"))
        return result





class FilterAttributeVisitedWebpage(FilterAttribute):
    def __init__(self):
        super().__init__("Besuchte Seite", FilterAttribute.TYPE_select )

    def getValidValues(self, customer):
        if FilterAttributeVisitedWebpage.__validValues is None:
            data = db.execute("SELECT pageUrl, pageId from observed_pages where customerId=%s order by pageUrl", (customer.customerId,))
            FilterAttributeVisitedWebpage.__validValues = []
            for d in data:
                FilterAttributeVisitedWebpage.__validValues.append((d[0], d[1]))
        return FilterAttributeVisitedWebpage.__validValues

    def getSqlComponents(self):
        result = []
        result.append(SqlComponent("pageUrl", "visits", ))
        result.append(("industryCodesNaics", "joinCompanies.naicsCode=joinIndustryCodesNaics.naicsCode", "labelLinkedIn"))
        return result


class FilterCondition:

    TYPE_equals = 1
    TYPE_not_equals = 2
    TYPE_lt = 3
    TYPE_gt = 4
    TYPE_lte = 5
    TYPE_gte = 6
    TYPE_contains = 7
    TYPE_not_contains = 8
    TYPE_startswith = 9
    TYPE_not_startswith = 10
    TYPE_endswith = 11
    TYPE_not_endswith = 12


    def __init__(self, filterAttribute, criterionType, value, group=None, dbId = None):
        self.criterionType = criterionType
        self.filterAttribute = filterAttribute
        self.value = value

    def getSqlComponents(self):
        pass
        # return condition & value

class FilterConditionGroup:

    TYPE_AND = 0
    TYPE_OR = 1

    def __init__(self, type = TYPE_AND, dbId = None):
        self.type = type
        self.dbId = dbId

    def addCriterion(self, criterion):
        pass
