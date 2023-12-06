from services import DbConfig, WebsiteService
from services.CustomerService import Customer, getCustomer
import re
import requests
import ssl

# create db_connection
db = DbConfig.getDB()



def scoreAllUnscoredWebsites():
    websites = db.execute('''SELECT site_id, lastModifiedOn FROM websites
        where site_id not in (select websiteId from website_scopes)
        ORDER BY lastModifiedOn DESC;''')
    count=0
    for w in websites:
        website = WebsiteService.getWebsiteById(w[0])
        count+=1
        #print("processing ", website.website, "(", count, "/", len(websites), ")")
        website.validate()
        website.identifyScopes()
        calculateAllScoresForWebsite(website)

def getContentScoresOfCustomer(customer):
    # create Collection of ContentScores
    data = db.execute('''
        select a.owner, a.name, a.scopeType, c.contentScoreId, c.searchTerm, c.isRegEx, c.readCode, c.searchTermId
             from website_contentScore a
        JOIN (SELECT contentScoreId from website_contentScoreSubscribers where customerId=%s) as b
             on a.contentScoreId = b.contentScoreId
        JOIN website_searchTerms c
             on a.contentScoreId = c.contentScoreId;
        ''', (customer.customerId,))
    contentScores = []
    contentScore = None
    for d in data:
        if contentScore is None or d[3] != contentScore.dbId:
            contentScore = ContentScore(getCustomer(d[0]), d[1], d[2], d[3])
            contentScores.append(contentScore)
        contentScore.searchTerms.append(SearchTerm(contentScore, d[4], d[5], d[6], d[7]))
    return contentScores


def getContentScore(dbId):
    data = db.execute('''
        select a.owner, a.name, a.scopeType, c.contentScoreId, c.searchTerm, c.isRegEx, c.readCode, c.searchTermId
             from website_contentScore a
        JOIN (SELECT * from website_searchTerms where contentScoreId=%s) as c
             on a.contentScoreId = c.contentScoreId;
        ''', (dbId,))
    if data is None or len(data) == 0:
        return None
    d = data[0]
    contentScore = ContentScore(getCustomer(d[0]), d[1], d[2], d[3])
    for d in data:
        contentScore.searchTerms.append(SearchTerm(contentScore, d[4], d[5], d[6], d[7]))
    return contentScore


def getContentScoresForWebsite(website, scopeType=None, subscriber=None):
    # TODO return all contentscores we really have to calculate for this website
    # eigentlich müssten wir hier zurückgeben:
    # if subscriber is None:
    #  - alle, die identify sind
    #  - und alle, die qualify sind und bei deren subscribern sich die firma hinter dieser website in den targets befindet
    # else:
    #  - alle, die identify sind und diesen subscriber haben
    #  - und alle, die qualify sind, diesen subscriber haben und bei dem subscriber sich die firma hinter dieser website in den targets befindet
    #
    # Wir müssen eine Liste zurückgeben mit scores[], die jeweils enthält [score, subscriptionType]
    #
    # Aber wir geben für den Moment erst mal nur alle contentscores aller Kunden und aller Websites zurück
    return getAllContentScores(scopeType)


def getAllContentScores(scopeType=None):
    data = None
    if scopeType is not None and scopeType >= 0:
        data = db.execute('''
            SELECT
                cs.owner, cs.name, cs.scopeType, cs.contentScoreId, 
                st.searchTerm, st.isRegEx, st.readCode, st.searchTermId
            FROM (SELECT * from website_contentScore where scopeType=%s) as cs
            JOIN website_searchTerms st on st.contentScoreId = cs.contentScoreId;
            ''', (scopeType,))
    else:
        data = db.execute('''
            SELECT
                cs.owner, cs.name, cs.scopeType, cs.contentScoreId, 
                st.searchTerm, st.isRegEx, st.readCode, st.searchTermId
            FROM website_contentScore cs
            JOIN website_searchTerms st on st.contentScoreId = cs.contentScoreId
            ''')
    if data is None or len(data) == 0:
        return None
    contentScores = []
    contentScore = None
    for d in data:
        if contentScore is None or d[3] != contentScore.dbId:
            contentScore = ContentScore(getCustomer(d[0]), d[1], d[2], d[3])
            contentScores.append(contentScore)
        contentScore.searchTerms.append(SearchTerm(contentScore, d[4], d[5], d[6], d[7]))
        # print("content score =", contentScore)
    return contentScores


def calculateAllScoresForWebsite(website):
    '''0 = entire
    site
    1 = homepage
    2 = imprint
    page
    3 = contact
    page
    4 = privacy
    statement
    page
    5 = Terms and Conditions
    page
    '''
    #print("calculateAllScoresForWebsite")
    scopeTypes = [0, 1, 2, 3, 4, 5]
    for scopeType in scopeTypes:
        scores = getContentScoresForWebsite(website, scopeType)
        scopes = website.getScopes(scopeType)
        if scopes is None and scores is not None:
            #print("Scopes is None, Scores not")
            website.identifyScopes()

        if scores is not None and scopes is not None:
            for score in scores:
                for scope in scopes:
                    #print("scoring", score.name, "on scope", scope.url, "type", scope.scopeType)
                    # 0 = entire site
                    if scope.scopeType == 0:
                        # todo: count on all sub pages, avoid to count same page twice!
                        pass
                    else:
                        countSearchTerms(scope, score.searchTerms)


def countSearchTerms(scope, searchTerms):
    # searchTerms is an array.
    # count multiple searchterms at once!
    result = 0

    text = None
    try:
        ssl.match_hostname = lambda cert, hostname: True
        text = requests.get("https://" + scope.url, timeout=3).text
    except BaseException:
        try:
            text = requests.get("https://www." + scope.url, timeout=3).text
        except BaseException:
            try:
                text = requests.get("http://" + scope.url, timeout=3).text
            except BaseException:
                try:
                    text = requests.get("http://www." + scope.url, timeout=3).text
                except BaseException:
                    pass

    if text is not None:
        for searchTerm in searchTerms:
            count = len(re.findall(searchTerm.searchTerm, text))
            result += count
            #print("  searchTerm", searchTerm.searchTerm, ":", count)
            db.execute('''
                INSERT INTO website_searchTermOccurrence(websiteScopeId, searchTermId, count)
                values(%s, %s, %s) ON DUPLICATE KEY UPDATE count=%s;
                ''', (scope.dbId, searchTerm.dbId, count, count), True)
    return result


class ContentScore:
    def __init__(self, owner, name="", scopeType=1, dbId=None):
        self.owner = owner
        self.name = name
        self.scopeType = scopeType
        self.dbId = dbId
        self.searchTerms = []

        # value exists only in case score(website) has been called
        self.scoredWebsite = None
        self.count = None

        # value only exists in case getContentScores() has been called with a subscriber as parameter
        self.subscriptionType = None

    def __str__(self):
        return self.name + " (" + str(self.dbId) + ")"

    def save(self):
        if self.dbId:
            # update in SQL DB
            db.execute('''
                UPDATE website_contentScore set name=%s, scopeType=%s, owner=%s
                where contentScoreId=%s;
                ''', (self.name, self.scopeType, self.dbId, self.owner.customerId), True)
            pass
        else:
            # insert into db
            self.dbId = db.execute('''
                INSERT INTO website_contentScore(name, scopeType, owner)
                values (%s, %s, %s);
                ''', (self.name, self.scopeType, self.owner.customerId), True)
        for searchTerm in self.searchTerms:
            searchTerm.save()
        return self.dbId

    def delete(self):
        if self.dbId is not None:
            for searchTerm in self.searchTerms:
                searchTerm.delete()
            db.execute('''
                            DELETE FROM website_contentScore where contentScoreId=%s;
                            ''', (self.dbId,), True)
            self.dbId = None

    def addSubscriber(self, customer, subscriptionType):
        if self.dbId is not None:
            db.execute('''
                INSERT INTO website_contentScoreSubscribers(contentScoreId, customerId, subscriptionType)
                values (%s, %s, %s) ON DUPLICATE KEY UPDATE subscriptionType=%s
                ''', (self.dbId, customer.customerId, subscriptionType, subscriptionType), True)
        else:
            raise Exception("Save ContentScore before adding a subscriber.")

    def removeSubscriber(self, customer):
        db.execute('''
            DELETE FROM website_contentScoreSubscribers where contentScoreId=%s and customerId=%s;
            ''', (self.dbId, customer.customerId), True)

    def getSubscribers(self):
        data = db.execute('''
            select a.customerName, a.type, a.active, a.customerId, a.createdOn, b.subscriptionType
                 from customer a
            INNER JOIN (SELECT customerId from website_contentScoreSubscribers where contentScoreId=%s) as b
                 on a.customerId = b.customerId;
            ''', (self.dbId,))
        subscribers = []
        for c in data:
            subscribers.append([Customer(c[0], c[1], c[2], c[3], c[4]), c[5]])
        return subscribers

    def score(self, website):
        scopes = website.getScopes(self.scopeType)
        self.scoredWebsite = website
        self.count = None
        
        if len(scopes) == 0:
            return None
        scopeId = scopes[0].dbId

        data = db.execute('''
            SELECT sum(oc.count)
            FROM (SELECT * FROM website_searchTermOccurrence where websiteScopeId=%s) as oc
            INNER JOIN (SELECT * FROM website_searchTerms where contentScoreId=%s) as st
                on oc.searchTermId=st.searchTermId
            ''', (scopeId, self.dbId))
        if len(data) > 0:
            self.count = data[0][0]

        for st in self.searchTerms:
            st.score(website)
        return self.count


class SearchTerm:

    def __init__(self, contentScore, searchTerm=None, isRegex=False, readCode=False, dbId=None):
        self.dbId = dbId
        self.searchTerm = searchTerm
        self.isRegex = isRegex
        self.readCode = readCode
        self.contentScore = contentScore

        # value exist only in case score(website) has been called
        self.scoredWebsite = None
        self.count = None

    def __str__(self):
        return self.searchTerm + " (" + str(self.dbId) + ")"

    def save(self):
        if self.dbId is not None:
            # update in SQL DB
            db.execute('''
                UPDATE website_searchTerms set searchTerm=%s, isRegEx=%s, readCode=%s, contentScoreId=%s
                where searchTermId=%s;
                ''', (self.searchTerm, self.isRegex, self.readCode, self.contentScore.dbId, self.dbId), True)
        else:
            # insert into db
            self.dbId = db.execute('''
                INSERT INTO website_searchTerms(searchTerm, isRegex, readCode, contentScoreId)
                values (%s, %s, %s, %s);
                ''', (self.searchTerm, self.isRegex, self.readCode, self.contentScore.dbId), True)
        return self.dbId

    def delete(self):
        if self.dbId is not None:
            db.execute('''
                DELETE FROM website_searchTerms where searchTermId=%s;
                ''', (self.dbId,))
            self.dbId = None

    def score(self, website):
        scopes = website.getScopes(self.contentScore.scopeType)
        self.scoredWebsite = website
        self.count = None

        if len(scopes) == 0:
            return None
        scopeId = scopes[0].dbId

        data = db.execute('''
            SELECT occurrenceId, count, lastModifiedOn
            FROM website_searchTermOccurrence
            where websiteScopeId=%s and searchTermId=%s
            ''', (scopeId, self.dbId))
        if len(data) > 0:
            self.count = data[0][1]
        return self.count
