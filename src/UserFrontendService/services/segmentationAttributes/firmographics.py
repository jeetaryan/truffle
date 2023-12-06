from services.SegmentsService import SegmentationService, SegmentationAttribute
from services import DbConfig

db = DbConfig.getDB()

class Revenue_0(SegmentationAttribute):
    def __init__(self, attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        valuesData = db.execute("SELECT DISTINCT revenue_0 FROM `companies` WHERE revenue_0 is not NULL ORDER BY revenue_0;")
        for v in valuesData:
            self.values.update({self.toType(v[0]): self.toType(v[0])})

class Revenue_1(SegmentationAttribute):
    def __init__(self, attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        valuesData = db.execute("SELECT DISTINCT revenue_1 FROM `companies` WHERE revenue_1 is not NULL ORDER BY revenue_1;")
        for v in valuesData:
            self.values.update({self.toType(v[0]): self.toType(v[0])})

class Employees_0(SegmentationAttribute):
    def __init__(self, attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        valuesData = db.execute("SELECT DISTINCT employees_0 FROM `companies` WHERE employees_0 is not NULL  ORDER BY employees_0;")
        for v in valuesData:
            self.values.update({self.toType(v[0]): self.toType(v[0])})

class Employees_1(SegmentationAttribute):
    def __init__(self, attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        valuesData = db.execute("SELECT DISTINCT employees_1 FROM `companies` WHERE employees_1 is not NULL ORDER BY employees_1;")
        for v in valuesData:
            self.values.update({self.toType(v[0]): self.toType(v[0])})

class LabelEn(SegmentationAttribute):
    def __init__(self, attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        valuesData = db.execute("SELECT DISTINCT naicsCode, labelEn FROM `industryCodesNaics` WHERE naicsCode is not NULL ORDER BY labelEn;")
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[1])})

class PageUrl(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute("SELECT DISTINCT pageId, pageUrl FROM `observed_pages` where customerId=%s and PageId is not NULL ORDER BY pageUrl;",
                                (customerId, ))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[1])})

class Segment(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute("SELECT distinct segmentId, name FROM `segments` WHERE ownerCustomer=%s and segmentId is not NULL order by name;",
                                (customerId, ))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[1])})

class Source(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute("SELECT distinct sourceId, name FROM `companySources` order by name;")
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[1])})


class VisitTime(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)


class DurationSec(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

class ScrollDepth(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        x = 0
        while x<=100:
            self.values.update({x/100: str(x)+"%"})
            x +=1

class UtmSource(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            "SELECT DISTINCT utm_source FROM `visits` where customerId=%s and utm_source is not NULL ORDER BY utm_source;",
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[0])})

class UtmMedium(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            "SELECT DISTINCT utm_medium FROM `visits` where customerId=%s and utm_medium is not NULL  ORDER BY utm_medium;",
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[0])})

class UtmCampaign(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            "SELECT DISTINCT utm_campaign FROM `visits` where customerId=%s and utm_campaign is not NULL  ORDER BY utm_campaign;",
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[0])})

class UtmTerm(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            "SELECT DISTINCT utm_term FROM `visits` where customerId=%s and utm_term is not NULL  ORDER BY utm_term;",
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[0])})

class UtmContent(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            "SELECT DISTINCT utm_content FROM `visits` where customerId=%s and utm_content is not NULL  ORDER BY utm_content;",
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[0])})

class Referrer(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            "SELECT DISTINCT referrer FROM `visits` where customerId=%s and referrer is not NULL ORDER BY referrer;",
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[0])})

class Language(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        customerId = segmentationService.customer.customerId
        valuesData = db.execute(
            '''SELECT DISTINCT languages.langId, languages.language
            FROM (SELECT langId FROM `visits` where customerId=%s and language is not NULL) as a
            JOIN languages on languages.langId=a.langId
             ORDER BY language;
            ''',
            (customerId,))
        for v in valuesData:
            self.values.update({v[0]: self.toType(v[1])})

class Gclid(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

        # override valid Values
        self.values.clear()
        self.values.update({"vorhanden": 1})
        self.values.update({"nicht vorhanden": 0})

class Parameters(SegmentationAttribute):
    def __init__(self,attributeId, segmentationService):
        super().__init__(attributeId, segmentationService)

