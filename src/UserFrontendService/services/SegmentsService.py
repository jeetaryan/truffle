import json
import re

from services import DbConfig, CompanyService, CustomerService
from threading import Thread
from datetime import datetime

#import querybuilder
#from querybuilder.filters import Filter
#from querybuilder.rules import Rule


db = DbConfig.getDB()


def getSegments(customer):

    sql = '''SELECT segmentId, name, description, colorCode FROM segments where ownerCustomer=%s'''
    segmentsData = db.execute(sql, (customer.customerId,))

    segments = []
    for s in segmentsData:
        segments.append(Segment(customer.customerId, s[1], s[2], s[3], s[0]))
    return segments


def getSegmentsOfCompany(company, customer):
    sql = '''SELECT s.segmentId, s.name, s.description, s.colorCode
        from (SELECT segmentId, name, description, colorCode FROM segments where ownerCustomer=%s) as s
        join (SELECT segmentId from segments_companies where companyId=%s) as sc on s.segmentId = sc.segmentId 
        '''
    segmentsData = db.execute(sql, (customer.customerId, company.companyId))

    segments = []
    for s in segmentsData:
        segments.append(Segment(customer.customerId, s[1], s[2], s[3], s[0]))
    return segments


def getSegment(segmentId):
    sql = '''SELECT ownerCustomer, name, description, colorCode FROM segments where segmentId=%s'''

    s = db.execute(sql, (segmentId,))

    if s is not None and len(s)>0:
        return Segment(s[0][0], s[0][1], s[0][2], s[0][3], segmentId)
    else:
        return None



segmentationServices = {}

def getSegmentationService(customer):
    global segmentationServices
    if customer not in segmentationServices:
        segmentationServices[customer] = SegmentationService(customer)
    return segmentationServices[customer]



class SegmentationService:
    def __init__(self, customer):
        self.customer = customer
        self.segmentationAttributes = {}
        self.tables = {}

        thread = Thread(target=self.loadAttributes)
        thread.start()

    def loadAttributes(self):
        # alle table laden. starten bei companies, dann die, die den table als jointable haben, rekursiv
        self.tables.clear()
        self.getTable("companies")

        # alle attribute laden, jeweils table aus tables dict
        self.segmentationAttributes.clear()
        attributesData = db.execute('''SELECT attributeId from segmentationAttributes where pythonClass is not NULL''')
        for a in attributesData:
            self.getAttribute(a[0])
            print("added id", int(a[0]))
        for a in self.segmentationAttributes.values():
            print("we have id", a.attributeId)


    def getAttributes(self):
        #TODO: alle attribute als dict rückgeben, damit in einem template die jqueryoptions generiert werden können
        for a in self.segmentationAttributes.values():
            print("Attribute ", a.attributeId, a.label)
        return self.segmentationAttributes.values()

    def getTable(self, tableName):
        if tableName is None:
            return None
        elif tableName not in self.tables:
            tableData = db.execute(
                '''SELECT tableName, joinColHere, joinTableThere, joinColThere from segmentationAttributeTables
                where tableName=%s''', (tableName,))
            if tableData is not None and len(tableData)>0:
                t = tableData[0]
                self.tables[tableName] = SqlTable(t[0], t[1], self.getTable(t[2]), t[3])
        return self.tables[tableName]

    def getAttribute(self, attributeId):
        if attributeId is None:
            return None
        attributeId = int(attributeId)
        if attributeId not in self.segmentationAttributes:
            #print("attributeId: " + str(attributeId))
            attributeData = db.execute(
                '''SELECT pythonClass
                from segmentationAttributes where attributeId=%s''', (attributeId,))

            if attributeData is not None and len(attributeData)>0:
                a = attributeData[0]
                kls = SegmentationService.__get_class__(a[0])
                self.segmentationAttributes[attributeId] = kls(attributeId, self)
        return self.segmentationAttributes[attributeId]

    def __get_class__(kls):
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m

    def loadRule(self, json):

        #print(json.__name__())
        if not isinstance(json, dict):
            raise SegmentationRuleValidationError('Rule must be a dictionary')

        result = None
        try:
            if json.get('empty'):
                # some rules
                result = SegmentationRuleCondition()
            elif SegmentationRule.group_fields.issubset(json):
                if not isinstance(json['rules'], list):
                    raise SegmentationRuleValidationError('\'rules\' must be a list')
                rules = []
                for r in json['rules']:
                    rules.append(self.loadRule(r))
                result = SegmentationRuleGroup(json['condition'], rules)

            elif SegmentationRule.rule_fields.issubset(json):
                result = SegmentationRuleCondition(self.getAttribute(json['id']), json['operator'], json['value'])
                #print(result.attribute.values)
            else:
                raise SegmentationRuleValidationError('Rule did not contain required fields')
        except ValueError as e:
            raise SegmentationRuleValidationError(e.message)
        return result

    '''
    def convertToSegmentationRule(self, string, ensure_list=False):
        #Returns rule objects from json, supports both a single rule or list of rules
        rule = json.loads(string)

        is_group = False
        is_empty = False  # note that an empty rule evaluates as true

        try:
            if rule.get('empty'):
                # some rules
                is_empty = True
            elif SegmentationRule.group_fields.issubset(rule):
                rules = [SegmentationRule.loads(rule) for rule in rule['rules']]
                return SegmentationRuleGroup(rule.get("condition"), rules)
            elif SegmentationRule.rule_fields.issubset(rule):
                attribute = getAttribute()
                return SegmentationRuleCondition(attribute, rule['operator'], rule['value'])
            else:
                raise ValidationError('Rule did not contain required fields')
        except ValueError as e:
            raise ValidationError(e.message)

    if isinstance(rule, (list, tuple)):
        return [cls(rule) for rule in rule]
    else:
        result = cls(rule)
        return [result] if ensure_list else result
    '''

class SqlTable:
    def __init__(self, tableName, joinColHere, joinTableThere, joinColThere):
        self.tableName = tableName
        self.joinColHere = joinColHere
        self.joinTableThere = joinTableThere
        self.joinColThere = joinColThere

    def __eq__(self, other):
        return self.tableName == other.tableName

    def getSqlJoin(self, segment):
        condition = ""
        if self.tableName == "visits" or self.tableName == "contacts":
            condition = " where customerId=%s" % segment.ownerCustomerId
        return "LEFT JOIN (SELECT * from " + self.tableName + condition + ") as gen_" + self.tableName\
                + " on gen_"  + self.tableName + "." + self.joinColHere\
                + " = gen_" + self.joinTableThere + "." +self.joinColThere



class SegmentationAttribute:
    TYPES = ["string", "integer", "double", "date", "time", "datetime", "boolean"]

    TYPE_STRING = 0
    TYPE_INTEGER = 1
    TYPE_DOUBLE = 2
    TYPE_DATE = 3
    TYPE_TIME = 4
    TYPE_DATETIME = 5
    TYPE_BOOLEAN = 6

    INPUTS = ["text", "number", "textarea", "radio", "checkbox", "select"]
    INPUT_TEXT = 0
    INPUT_NUMBER = 1
    INPUT_TEXTAREA = 2
    INPUT_RADIO = 3
    INPUT_CHECKBOX = 4
    INPUT_SELECT = 5

    def __init__(self, attributeId, segmentationService):
        attributeData = db.execute(
            '''SELECT 
            colName, sqlTable, label, description, type, optgroup, input, size, rows_,
            multiple, placeholder, vertical, validation, default_operator, default_value, pythonClass
            from segmentationAttributes where attributeId=%s''', (attributeId,))
        operators = db.execute('''SELECT operator from segmentationAttributeValidOperators where attributeId=%s''',
                               (attributeId,))
        values = db.execute('''SELECT validValue from segmentationAttributeValidValues where attributeId=%s''',
                            (attributeId,))
        if attributeData is not None and len(attributeData)>0:
            a = attributeData[0]
            self.attributeId = attributeId
            self.colName = a[0]
            self.sqlTable = segmentationService.getTable(a[1])
            self.label = a[2]
            self.description = a[3]
            self.attributeType = a[4]
            self.optgroup = a[5]
            self.attributeInput = a[6]
            self.size = a[7]
            self.rows = a[8]
            self.multiple = a[9]
            self.placeholder = a[10]
            self.vertical = a[11]
            self.validation = a[12]

            self.default_operator = a[13]
            self.operators = []
            for o in operators:
                self.operators.append(o[0])

            self.default_value = self.toType(a[14])
            self.values = {}
            for v in values:
                self.values.update({self.toType(v[0]): self.toType(v[0])})
        else:
            print("cannot find attributeId ", attributeId)

    def toType(self, value):
        if value is None:
            return value
        if self.attributeType == SegmentationAttribute.TYPE_INTEGER:
            return int(value)
        elif self.attributeType == SegmentationAttribute.TYPE_DOUBLE:
            return  float(value)
        elif self.attributeType == SegmentationAttribute.TYPE_BOOLEAN:
            return  bool(value)
        elif self.attributeType == SegmentationAttribute.TYPE_DATE:
            format = '%Y-%m-%d'
            return datetime.strptime(value, format)
        elif self.attributeType == SegmentationAttribute.TYPE_TIME:
            format = '%H:%M:%S'
            return datetime.strptime(value, format)
        elif self.attributeType == SegmentationAttribute.TYPE_DATETIME:
            format = '%Y-%m-%d %H:%M:%S'
            return datetime.strptime(value, format)
        else:
            return value

'''
    def getFilter(self):
        #return jQueryBuilder.Filter
        return Filter(str(self.attributeId), str(self.attributeId), self.label, self.description,
                      SegmentationAttribute.TYPES[self.attributeType],
                      self.optgroup, SegmentationAttribute.INPUTS[self.attributeInput], self.values,
                      "", self.default_value, None, self.size, self.rows, self.multiple, self.placeholder,
                      self.vertical, self.validation, self.operators)
'''
class SegmentationRule:
    rule_fields = set(['id', 'field', 'input', 'operator', 'type', 'value'])
    group_fields = set(['condition', 'rules'])

    def getSqlCondition(self, top=False):
        pass

    def getSqlJoinTables(self):
        return None



class SegmentationRuleValidationError(Exception):
    pass


class SegmentationRuleGroup(SegmentationRule):
    GROUP_TYPE_AND = "AND"
    GROUP_TYPE_OR = "OR"

    def __init__(self, groupType=GROUP_TYPE_AND, rules=()):
        self.groupType = groupType
        self.rules = rules

    def getSqlCondition(self, top=False):
        result = ""
        for i, r in enumerate(self.rules):
            if i == 0:
                result += "("
            else:
                result += " " + self.groupType + " "
            result += r.getSqlCondition()
            if i == len(self.rules)-1:
                result += ")"

        return result

    def getSqlJoinTables(self):
        result = []
        for r in self.rules:
            tbls = r.getSqlJoinTables()
            for t in tbls:
                if t not in result:
                    result.append(t)
        return result


class SegmentationRuleCondition(SegmentationRule):
    OPERATORS = ["equal", "not_equal", "in", "not_in", "less", "less_or_equal", "greater", "greater_or_equal",
    "between", "not_between", "begins_with", "not_begins_with", "contains", "not_contains", "ends_with",
    "not_ends_with", "is_empty", "is_not_empty", "is_null", "is_not_null"]
    SQL_OPERATORS = ["=", "!=", "in", "not in", "<", "<=", ">", ">=",
                 "between", "not_between", "begins_with", "not_begins_with", "contains", "not_contains", "ends_with",
                 "not_ends_with", "is_empty", "is_not_empty", "is_null", "is_not_null"]

    OPERATOR_EQUAL = 0
    OPERATOR_NOT_EQUAL = 1
    OPERATOR_IN = 2
    OPERATOR_NOT_IN = 3
    OPERATOR_LESS = 4
    OPERATOR_LESS_OR_EQUAL = 5
    OPERATOR_GREATER = 6
    OPERATOR_GREATER_OR_EQUAL = 7
    OPERATOR_BETWEEN = 8
    OPERATOR_NOT_BETWEEN = 9
    OPERATOR_BEGINS_WITH = 10
    OPERATOR_NOT_BEGINS_WITH = 11
    OPERATOR_CONTAINS = 12
    OPERATOR_NOT_CONTAINS = 13
    OPERATOR_ENDS_WITH = 14
    OPERATOR_NOT_ENDS_WITH = 15
    OPERATOR_IS_EMPTY = 16
    OPERATOR_IS_NOT_EMPTY = 17
    OPERATOR_IS_NULL = 18
    OPERATOR_IS_NOT_NULL = 19

    def __init__(self, attribute=None, operator=None, value=None):
        self.attribute = attribute
        self.operator = SegmentationRuleCondition.OPERATORS.index(operator)
        self.value = value

    def getSqlCondition(self, top=False):
        result = "(" + self.attribute.colName
        if self.operator in (0, 1, 4, 5, 6, 7):
            result += SegmentationRuleCondition.SQL_OPERATORS[self.operator] + str(self.value) + ")"
        elif self.operator == SegmentationRuleCondition.OPERATOR_BEGINS_WITH:
            result += " LIKE '%" + str(self.value) + "')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_CONTAINS:
            result += " LIKE '%" + str(self.value) + "%')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_ENDS_WITH:
            result += " LIKE '" + str(self.value) + "%')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_NOT_BEGINS_WITH:
            result += " NOT LIKE '%" + str(self.value) + "')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_NOT_CONTAINS:
            result += " NOT LIKE '%" + str(self.value) + "%')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_NOT_ENDS_WITH:
            result += " NOT LIKE '" + str(self.value) + "%')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_IS_EMPTY:
            result += "='')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_IS_NOT_EMPTY:
            result += "!='')"
        elif self.operator == SegmentationRuleCondition.OPERATOR_IS_NULL:
            result += " is null)"
        elif self.operator == SegmentationRuleCondition.OPERATOR_IS_NOT_NULL:
            result += " is not null)"
        else:
            # e.g. if rule empty
            result = "(True)"

        # TODO: 2,3,8,9 (in, not in, between, not between)

        return result

    def getSqlJoinTables(self):
        return self.attribute.sqlTable





class Segment:
    def __init__(self, ownerCustomerId=None, name=None, description=None, colorCode=None, id=None):
        self.id = id
        self.ownerCustomerId = ownerCustomerId
        self.segmentationService = getSegmentationService(CustomerService.getCustomer(ownerCustomerId))
        self.name = name
        self.description = description
        if colorCode[0] == "#":
            self.colorCode = colorCode[1:]
        else:
            self.colorCode = colorCode

    def addCompany(self, company):
        db.execute("INSERT IGNORE into segments_companies (segmentId, companyId) values(%s,%s)",
                   (self.id, company.companyId), True)

    def removeCompany(self, company):
        db.execute("delete from segments_companies where segmentId=%s and companyId=%s",
                   (self.id, company.companyId), True)

    def getCompanies(self):
        companies = []
        sqlResult = db.execute("SELECT companyId from segments_companies where segmentId=%s", (self.id,))
        for c in sqlResult:
            companies.append(CompanyService.getCompanyById(c[0]))
        return companies

    def delete(self):
        db.execute("delete from segments where segmentId=%s", (self.id,), True)
        return

    def save(self, name=None, description=None, colorCode=None, ownerCustomerId=None):
        if name is not None: self.name=name
        if description is not None: self.description = description
        if colorCode is not None:
            if colorCode[0] == "#":
                self.colorCode = colorCode[1:]
            else:
                self.colorCode = colorCode
        if ownerCustomerId is not None: self.ownerCustomerId = ownerCustomerId

        if self.id is None:
            self.id = db.execute("insert into segments(name, description, colorCode, ownerCustomer) values (%s, %s, %s, %s)",
                       (self.name, self.description, self.colorCode, self.ownerCustomerId), True)
        else:
            db.execute("UPDATE segments set name=%s, description=%s, colorCode=%s, ownerCustomer=%s where segmentId=%s",
                   (self.name, self.description, self.colorCode, self.ownerCustomerId, self.id), True)
        return self.id


    def setFilter(self, jsonData):
        db.execute("UPDATE segments set filter=%s where segmentId=%s",
                   (json.dumps(jsonData), self.id),
                   True)

        thread = Thread(target=self.applyFilter)
        thread.start()

    def getFilter(self):
        data = db.execute("SELECT filter from segments where segmentId=%s", (self.id, ))
        if len(data)>0:
            if data[0][0] is not None:
                return json.loads(data[0][0])
        return None

    def setAutoUpdate(self, value):
        db.execute("UPDATE segments set autoUpdate=%s where segmentId=%s",
                   (value, self.id),
                   True)
    def getAutoUpdate(self):
        data = db.execute("SELECT autoUpdate FROM `segments` WHERE segmentId=%s", (self.id, ))
        if len(data)>0:
            return data[0][0]
        return None

    def setReplaceTargets(self, value):
        db.execute("UPDATE segments set replaceTargets=%s where segmentId=%s",
                   (value, self.id),
                   True)
    def getReplaceTargets(self):
        data = db.execute("select replaceTargets from segments where segmentId=%s", (self.id, ))
        if len(data)>0:
            return data[0][0]
        return None
    def applyFilter(self):
        filter = self.getFilter()
        rule = self.segmentationService.loadRule(json.loads(filter))

        db.execute("DELETE FROM segments_companies where segmentId=%s", (self.id,), True)

        sql = '''
        insert into segments_companies(companyId, segmentId) 
        SELECT DISTINCT cc.companyId, %s FROM (SELECT companyId, source FROM companies_customers where customerId=%s) cc
        left join (SELECT * FROM segments_companies) cs on cs.companyId = cc.companyId
        left JOIN (SELECT companyId, companyName, naicsCode, employees_0, employees_1, revenue_0, revenue_1  from companies where isISP=0 and manualISP=0 and companyName is not null) c on cc.companyId = c.companyId
        left join (SELECT labelLinkedin, naicsCode from industryCodesNaics) as i on c.naicsCode=i.naicsCode
        left join (SELECT companyId, pageId, visitTime, durationSec, scrollDepth, winHeight, winWidth, browser_family, browser_version, os_family, device_family, device_brand, device_model, isMobile, isTablet, isTouch, isPc, langId, referrer, utm_source, utm_medium, utm_campaign, utm_term, utm_content from visits where customerId=%s) as v on v.companyId=cc.companyId
        left join (SELECT langId, language from languages) as l on l.langId=v.langId
        left JOIN (SELECT companyId, website, site_id from websites) as w on cc.companyId = w.companyId
        left join (SELECT companyId, count(companyId) as contactCount from contacts where customerId=%s group by companyId) as contacts on contacts.companyId = cc.companyId 
        '''
        sql += "where " + rule.getSqlCondition(True)
        db.execute(sql, (self.id, self.ownerCustomerId, self.ownerCustomerId, self.ownerCustomerId), True)





    '''
Colnames in join zeile 478ff
Colnames in sqlcondition zeile 376ff
'''