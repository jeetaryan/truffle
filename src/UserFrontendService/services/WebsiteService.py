import datetime

from requests import Timeout

from services import DbConfig
import requests
import ssl
from bs4 import BeautifulSoup
from services.StringHelper import *
from services import CompanyService
import traceback
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from Screenshot import Screenshot
from PIL import Image
import validators
import cfscrape
import requests
import favicon
import socket
from time import sleep

from collections import namedtuple
import urllib.request as urllib2

db = DbConfig.getDB()


def getWebsiteById(dbId):
    try:
        data = db.execute('''
                select website, companyId, screenshot,
                 profile_li, profile_tw, profile_fb, profile_xi,
                 profile_ig, profile_tt, profile_yt, profile_twi, favicon, protocol  from websites
                where site_id=%s;
                ''', (dbId,))
        if len(data)>0:
            w = data[0]
            return Website(w[0], CompanyService.getCompanyById(int(w[1])), w[2], dbId, w[3], w[4], w[5], w[6], w[7], w[8], w[9], w[10], w[11], w[12])
        else:
            return None
    except BaseException:
        print("Exception caught while getting website site_id:", dbId)
        traceback.print_exc()
    return None

def getWebsitesOfCompany(company):
    if company is not None:
        result = []
        try:
            data = db.execute('''
                    select website, companyId, screenshot,
                     profile_li, profile_tw, profile_fb, profile_xi,
                     profile_ig, profile_tt, profile_yt, profile_twi, site_id, favicon, protocol from websites
                    where companyId=%s;
                    ''', (company.companyId,))
            for w in data:
                result.append(Website(w[0], company, w[2], w[11], w[3], w[4], w[5], w[6], w[7], w[8], w[9], w[10], w[12], w[13]))

        except BaseException:
            print("Exception caught while getting website of company ", company.companyName, "(companyId:", company.companyId, ")")
            traceback.print_exc()
        return result
    return None

def getWebsiteByUrl(url):
    try:
        data = db.execute('''
                select site_id, companyId, screenshot,
                 profile_li, profile_tw, profile_fb, profile_xi,
                 profile_ig, profile_tt, profile_yt, profile_twi, site_id, favicon, protocol from websites
                where website LIKE %s;
                ''', ('%' + clnWebsite(url) + '%',))

        if len(data) > 0:
            w = data[0]
            return Website(url, CompanyService.getCompanyById(int(w[1])), w[2], w[11], w[3], w[4], w[5], w[6], w[7], w[8], w[9], w[10], w[12], w[13])
        else:
            return Website(url, None)
    except BaseException:
        print("Exception caught while getting website ", url)
        traceback.print_exc()
    return None

def getAllWebsites():
    result = []
    try:
        data = db.execute('''
                select site_id, companyId, screenshot,
                 profile_li, profile_tw, profile_fb, profile_xi,
                 profile_ig, profile_tt, profile_yt, profile_twi, site_id, website, favicon, protocol from websites
                ''')

        for w in data:
            website = Website(w[12], CompanyService.getCompanyById(int(w[1])), w[2], w[11], w[3], w[4], w[5], w[6], w[7], w[8], w[9],
                                  w[10], w[12], w[13])
            #print(website.website)
            result.append(website)
        print("returning", str(len(result)), "websites")

    except BaseException:
        traceback.print_exc()
    return result
def getAllWebsitesModifiedBefore(datetime):
    result = []
    try:
        data = db.execute('''
                select site_id, companyId, screenshot,
                 profile_li, profile_tw, profile_fb, profile_xi,
                 profile_ig, profile_tt, profile_yt, profile_twi, site_id, website, favicon, protocol from websites
                 where lastModifiedOn<%s
                ''', (datetime,))

        for w in data:
            website = Website(w[12], CompanyService.getCompanyById(w[1]), w[2], w[11], w[3], w[4], w[5], w[6], w[7], w[8], w[9],
                                  w[10], w[12], w[13])
            print(website.website)
            result.append(website)
        print("got", str(len(result)), "websites")

    except BaseException:
        traceback.print_exc()
    return result

class Website:
    def __init__(self, website, company, screenshot=None, dbId=None,
                 profile_li=None, profile_tw=None, profile_fb=None, profile_xi=None,
                 profile_ig=None, profile_tt=None, profile_yt=None, profile_twi=None,
                 favicon=None, protocol=0):
        if website is None:
            raise ValueError('Website may not be None.')
        # normalize to domain and subdomain only www.web.de
        self.website = clnWebsite(website)
        if validators.domain(self.website) == False:
            raise ValueError('Website seems not to be a valid domain.' + self.website)


        self.company = company
        self.scopes = []
        self.screenshot = screenshot
        self.profile_li = profile_li
        self.profile_tw = profile_tw
        self.profile_fb = profile_fb
        self.profile_xi = profile_xi
        self.profile_ig = profile_ig
        self.profile_yt = profile_yt
        self.profile_tt = profile_tt
        self.profile_twi = profile_twi
        self.favicon = favicon
        self.protocol = "http" if protocol == 1 else "https"

        self.dbId = dbId

    def reCollectFromWebsite(self):
        if self.dbId is None:
            self.save()
        self.validate()
        if self.screenshot is None:
            self.getScreenshot()
        if self.favicon is None:
            self.getFavIcon()
        if self.profile_fb is None and self.profile_li is None and \
            self.profile_tt is None and self.profile_yt is None and \
            self.profile_ig is None and self.profile_twi is None and \
            self.profile_tw is None and self.profile_xi is None:
            self.scrapeSocialProfiles()
    def __validate(self, url):
        try:
            port = 443
            host = url.split("://")
            if len(host) > 1:
                port = 80 if host[0] == "http" else 443
                host = clnWebsite(host[1])
            else:
                host = host[0]
            socket.getaddrinfo(host, port)

            response = requests.get(url, allow_redirects=True, timeout=10, verify=False)
            if response.history:
                return response.url
            elif response.status_code != 200:
                return None
            else:
                return url
        except socket.gaierror:
            print("Domain cannot be resolved: ", url)
            return None
        except requests.exceptions.ReadTimeout:
            print("Timeout on", url)
            return None
        except requests.exceptions.HTTPError:
            print("Http Error", url)
            return None



    def validate(self):
        print("- validating website URL: ", self.website)
        try:
            url2 = self.__validate(self.protocol + "://" + self.website)
            if url2 is None:
                tryCheck = self.website
                if self.website[0:4] == "www.":
                    tryCheck = self.website[4:]
                    url2 = self.__validate("https://" + tryCheck)
            if url2 is None:
                tryCheck = self.website
                if self.website[0:4] != "www.":
                    tryCheck = "www." + self.website
                    url2 = self.__validate("https://" + tryCheck)
            if url2 is None:
                tryCheck = self.website
                if self.website[0:4] == "www.":
                    tryCheck = self.website[4:]
                    url2 = self.__validate("http://" + tryCheck)
            if url2 is None:
                tryCheck = self.website
                if self.website[0:4] != "www.":
                    tryCheck = "www." + self.website
                    url2 = self.__validate("http://" + tryCheck)
            print("FINAL URL IS", url2)

            if url2 is None:
                print("  deleting", self.website)
                self.delete()

            elif url2 != self.protocol + "://" + self.website:
                split = url2.split("://")
                if len(split)>1:
                    print("  correcting website URL ", self.protocol, self.website, "to", self.protocol, clnWebsite(url2))
                    self.protocol = split[0]
                    self.website = clnWebsite(url2)
                    self.save()
                print("  URL correct", self.protocol, self.website)
        except BaseException as e:
            print("  There is a connection issue while validating website", self.website)
            print(e)

    def getFavIcon(self):
        print("- getting favicon")
        try:
            icons = favicon.get(self.protocol + "://" + self.website)
            if icons and len(icons)>0:
                icon = icons[0]
                response = requests.get(icon.url, stream=True, verify=False, timeout=10)
                filename = "/var/www/login.truffle.one/static/favicons/" + str(self.dbId) + "." + str(icon.format)
                with open(filename, 'wb') as image:
                    for chunk in response.iter_content(1024):
                        image.write(chunk)
                if len(str(icon.format)) == 3:
                    self.favicon = str(icon.format)
                else:
                    self.favicon = None
                return filename
            return None
        except BaseException as e:
            self.favicon = None
            print(e)
            traceback.print_exc()
            return None

    def getScopes(self, scopeType=None):
        if scopeType != None:
            returnScopes = []
            for scope in self.getScopes():
                if scope.scopeType == scopeType:
                    returnScopes.append(scope)
            return returnScopes
        else:
            if self.scopes is None or len(self.scopes) == 0:
                try:
                    data = db.execute('''
                            select scopeType, url, websiteScopeId
                            FROM website_scopes
                            where websiteId=%s;
                            ''', (self.dbId, ))

                    scopes = []
                    for scope in data:
                        scopes.append(WebsiteScope(self, scope[0], scope[1], scope[2]))
                    self.scopes = scopes
                except BaseException:
                    traceback.print_exc()
            return self.scopes

    def identifyScopes(self):
        print("- identifying scopes")
        scopeTypes = [1, 2, 3, 4, 5]
        scopes = self.getScopes()
        # update existing ones:
        for scope in scopes:
            scope.reIdentify()
            scopeTypes.remove(scope.scopeType)
        # create missing ones:
        for scopeType in scopeTypes:
            scope = WebsiteScope(self, scopeType)
            scope.reIdentify()

    def save(self):
        print("- saving.")
        try:
            companyId = None
            if self.company is not None:
                companyId = self.company.companyId
            protocol = 0 if self.protocol=="https" else 1
            if self.dbId is not None and self.dbId>0:
                # check if there is another website already with this website URL
                existing = db.execute('''SELECT site_id from websites where website=%s and site_id!=%s''',
                                      (self.website, self.dbId))
                if existing is not None and len(existing)>0:
                    print("  url already exists")
                    self.delete()
                else:
                    # update in SQL DB
                    db.execute('''
                        UPDATE websites set website=%s, companyId=%s, screenshot=%s, 
                            profile_tw=%s, profile_li=%s, profile_fb=%s, profile_xi=%s, profile_ig=%s,
                            profile_yt=%s, profile_tt=%s, profile_twi=%s, favicon=%s, protocol=%s
                            where site_id=%s
                        ''', (self.website, companyId, self.screenshot, self.profile_tw, self.profile_li, self.profile_fb,
                              self.profile_xi, self.profile_ig, self.profile_yt, self.profile_tt, self.profile_twi,
                              self.favicon, protocol, self.dbId),
                       True)
            else:
                # check if there is another website already with this website URL
                existing = db.execute('''SELECT site_id from websites where website=%s''',
                                      (self.website, ))
                if existing is not None and len(existing) > 0:
                    print("  url already exists")
                    self.delete()
                else:
                    # insert into db
                    self.dbId = db.execute('''
                        INSERT INTO websites(website, companyId, screenshot, 
                            profile_tw, profile_li, profile_fb, profile_xi, profile_ig,
                            profile_yt, profile_tt, profile_twi, favicon, protocol) 
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE companyId=%s;
                        ''', (self.website, companyId, self.screenshot, self.profile_tw, self.profile_li, self.profile_fb,
                              self.profile_xi, self.profile_ig, self.profile_yt, self.profile_tt, self.profile_twi,
                              self.favicon, protocol, companyId),
                        True)

            if self.dbId is not None:
                for scope in self.scopes:
                    scope.save()
        except BaseException:
            traceback.print_exc()
        return self.dbId

    def delete(self):
        print("- deleting")
        if self.dbId is not None:
            try:
                for scope in self.getScopes():
                    scope.delete()
                db.execute('''
                                DELETE FROM websites where site_id=%s;
                                ''', (self.dbId, ), True)
                self.dbId = None
            except BaseException:
                traceback.print_exc()
        return self.dbId

    def getScreenshot(self, evenIfExists=False):
        filename = f'/var/www/login.truffle.one/static/screenshots/{self.dbId}.png'
        try:
            if not evenIfExists:
                # check if exist
                oneMonthAgo = datetime.date.today() - datetime.timedelta(days=30)
                row = db.execute("select screenshot from websites where site_id=%s and screenshot>%s",
                                 (self.dbId, oneMonthAgo))
                if row:
                    return filename

            options = Options()
            options.headless = True
            # options.add_argument('--user-agent="Mozilla/5.0 (compatible; t1bot/1.0"')
            options.add_argument(
                '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"')
            options.add_argument("--window-size=1600x3600")

            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
            driver.set_page_load_timeout(10)
            driver.maximize_window()

            domain = self.website


            try:
                print("getting screenshot of", self.protocol + "://" + domain)
                driver.get(self.protocol + "://" + domain)
                sleep(5)
                # now we try to click away consent banners
                button = None
                try:
                    button = driver.find_element("xpath", "//button[contains(text(), 'gree')]")
                except BaseException as e:
                    pass
                ##### button with text
                if not button:
                    try:
                        button: button = driver.find_element("xpath", "//button[contains(text(), 'onsent')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[contains(text(), 'ccept')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[contains(text(), 'kzeptier')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[contains(text(), 'llow')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[contains(text(), 'ustimme')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[contains(text(), 'rlaube')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[contains(text(),'estätige')]")
                    except BaseException as e:
                        pass
                ##### a with text
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(), 'gree')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button: button = driver.find_element("xpath", "//a[contains(text(), 'onsent')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(), 'ccept')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(), 'kzeptier')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(), 'llow')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(), 'ustimme')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(), 'rlaube')]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[contains(text(),'estätige')]")
                    except BaseException as e:
                        pass
                ####button with subelememt that contains text
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(), 'gree')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button: button = driver.find_element("xpath", "//button[./*[contains(text(), 'onsent')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(), 'ccept')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(), 'kzeptier')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(), 'llow')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(), 'ustimme')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(), 'rlaube')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//button[./*[contains(text(),'estätige')]]")
                    except BaseException as e:
                        pass
                ####a with subelememt that contains text
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(), 'gree')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button: button = driver.find_element("xpath", "//a[./*[contains(text(), 'onsent')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(), 'ccept')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(), 'kzeptier')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(), 'llow')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(), 'ustimme')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(), 'rlaube')]]")
                    except BaseException as e:
                        pass
                if not button:
                    try:
                        button = driver.find_element("xpath", "//a[./*[contains(text(),'estätige')]]")
                    except BaseException as e:
                        pass

                if button:
                    try:
                        button.click()
                    except BaseException as e:
                        pass
                    # might not be interactable

                # take screenshot
                sleep(5)
                ob = Screenshot.Screenshot()
                element = driver.find_element("tag name", "body")
                screenShot = element.screenshot(filename)

                if screenShot:
                    # print("successfully got screenshot of ", domain)

                    # resize image to 250 px width
                    image = Image.open(filename)
                    width = image.size[0]
                    height = image.size[1]
                    newWidth = 320
                    newHeight = int(newWidth * height / width)
                    image = image.resize((newWidth, newHeight), Image.ANTIALIAS)
                    image.save(filename, optimize=True, quality=95)

                    self.screenshot = datetime.date.today()
                    self.save()
                else:
                    print("not able to get screenshot of ", domain)
                    self.screenshot = datetime.date(1900,1,1)
                    self.save()

                    filename = None
            except BaseException as e:
                print("Exception caught while taking screenshot for ", domain, "(site_id:", self.dbId, ")")
                traceback.print_exc()
                return None
            driver.close()
            driver.quit()
        except BaseException as e:
            print("Exception caught while taking screenshot for ", domain, "(site_id:", self.dbId, ")")
            traceback.print_exc()
            return None
        return filename

    def scrapeSocialProfiles(self):
        ssl.match_hostname = lambda cert, hostname: True

        if self.website is not None:
            print("- scraping social profiles... from", self.website)
            regex_li = ".*linkedin\.com\/company\/.*"
            regex_tw = ".*twitter\.com\/.*"
            regex_fb = ".*facebook\.com\/.*"
            regex_xi = ".*xing\.com\/companies\/.*"
            regex_ig = ".*instagram\.com\/.*"
            regex_yt = ".*youtube\.com\/user\/.*"
            regex_tt = ".*tiktok\.com\/.*"
            regex_twi = ".*twitch\.tv\/.*"

            self.profile_li = None
            self.profile_tw = None
            self.profile_fb = None
            self.profile_xi = None
            self.profile_ig = None
            self.profile_yt = None
            self.profile_tt = None
            self.profile_twi = None

            try:
                resultstr = None
                scraper = cfscrape.create_scraper()
                html_page = scraper.get(self.protocol + "://" + self.website, timeout=10, verify=False)
                soup = BeautifulSoup(html_page.text, "html.parser")

                regex_li = ".*linkedin\.com\/company\/.*"
                regex_tw = ".*twitter\.com\/.*"
                regex_fb = ".*facebook\.com\/.*"
                regex_xi = ".*xing\.com\/companies\/.*"
                regex_ig = ".*instagram\.com\/.*"
                regex_yt = ".*youtube\.com\/user\/.*"
                regex_tt = ".*tiktok\.com\/.*"
                regex_twi = ".*twitch\.tv\/.*"


                for link in soup.findAll('a', href=True):
                    # print("link: ", link['href'])
                    if re.search(regex_li, link['href']):
                        self.profile_li = unescapeSpecialLetters(
                            link['href'].split("linkedin.com/company/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_tw, link['href']):
                        self.profile_tw = unescapeSpecialLetters(
                            link['href'].split("twitter.com/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_fb, link['href']):
                        self.profile_fb = unescapeSpecialLetters(
                            link['href'].split("facebook.com/")[1].split("/")[0].split("#")[0].split("?")[0])
                        if self.profile_fb == "pages":
                            self.profile_fb = unescapeSpecialLetters(
                                link['href'].split("facebook.com/pages/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_xi, link['href']):
                        self.profile_xi = unescapeSpecialLetters(
                            link['href'].split("xing.com/companies/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_ig, link['href']):
                        self.profile_ig = unescapeSpecialLetters(
                            link['href'].split("instagram.com/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_tt, link['href']):
                        self.profile_tt = unescapeSpecialLetters(
                            link['href'].split("tiktok.com/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_yt, link['href']):
                        self.profile_yt = unescapeSpecialLetters(
                        link['href'].split("youtube.com/user/")[1].split("/")[0].split("#")[0].split("?")[0])
                    elif re.search(regex_twi, link['href']):
                        self.profile_twi = unescapeSpecialLetters(
                            link['href'].split("twitch.tv/")[1].split("/")[0].split("#")[0].split("?")[0])

                self.save()
            except BaseException as e:
                traceback.print_exc()
                return None
        return None

    def searchAddress(self, imprinturl):
        html = requests.get(imprinturl, verify=False, timeout=5).text

        # print(html)

        # the string starts with this regex
        sepstart = "((>\\s*)|\\r|\\n|^|(:\\s)|(;\\s)|(,\\s))+"
        # this is the street
        rstreet = "((\\d,)|[A-Za-zäöüÄÖÜß\\s\\d\\.-])+"
        # street and house number are separated with whitespace
        sep2 = "\\s*"
        # number of house in street
        rhaus = "(\\d+(\\s?[-|+/]?\\s?\\d+)?\\s*[a-z]?){1}"
        # sometimes you have a comment like "(appartmen xyz) or (formerly this street)
        comment = "(\\s\\({1}[A-Za-z0-9_\\säÄöÖüÜß-]*\\){1})?"
        # typically there is not only a separator but a new line between house and zip code
        # sepnl = "((\\s*<(^ÃŸ)>\\s*)|\\r|\\n|^|(;\\s)|(,\\s))+";
        # sepnl = "(\\s*<([(^ÃŸ)|\\r|\\n|^]>\\s*)|\\r|\\n|^|(;\\s)|(,\\s))+";
        # <.*?>
        sepnl = "((\\s*<.*?>\\s*)|\\r|\\n|^|(;\\s)|(,\\s))+"
        # sepnl = "(\\s*<([A-Za-z0-9_\\. äÄöÖüÜß\\\"\\s\\d\\'\\t\\n\\r&\\\\,-]*>\\s*)|\\r|\\n|^|(;\\s)|(,\\s))+";  // original

        # zip code                        /
        rzip = "(((D\\s?-\\s?)*[0-9]{5})|(CH\\s?-\\s?[0-9]{4}|(A\\s?-\\s?[0-9]{4})))"

        # whitespace between zip code and city
        sep3 = "\\s+";
        # city
        rcity = "[A-Z_ÄÖÜ]{1}[A-Za-z0-9_./ äÄöÖüÜß-]+"

        # sseparator at the end of the address string
        sepend = "((\\s*<)|\\r|\\n|^|(;\\s)|(,\\s))+"

        # print(sepstart+ rstreet + sep2 + rhaus + comment +sepnl+ rzip + sep3 + rcity + comment + sepend)
        # html = html.replace('/', '\\')

        regexp = sepstart + rstreet + sep2 + rhaus + comment + sepnl + rzip + sep3 + rcity + comment + sepend

        x = re.search(regexp, html)
        # print(regexp)
        # print(x.group())
        if x:
            address = self.parseAddress(x.group())

            # print("Street: ", address.street)
            # print("ZIP: ", address.zip)
            # print("City: ", address.city)
            # print("Country: ", address.country)

    def parseAddress(text):
        Address = namedtuple('Address', ['street', 'zip', 'city', 'country'])

        workstring = cleanFromHTMLTags(text)
        workstring = cleanStartAndEnd(workstring)

        # look for ZIP code and country, assume Germany if no country described
        regexp = "\\s+(((D\\s?-\\s?)*[0-9]{5})|(CH\\s?-\\s?[0-9]{4})|(A\\s?-\\s?[0-9]{4}))\\s+"

        x = re.findall(regexp, workstring)

        country = "DE"
        zip = ""
        initialzip = ""

        if (len(x) > 0):
            zip = x[0][1]
            initialzip = zip;
            zip = cleanStartAndEnd(zip);

            if (zip.startswith("CH")):
                # swiss cities have 4 digit ZIP codes
                country = "CH"
                zip = zip[(len(zip) - 4):len(zip)]
            elif (zip.startswith("A")):
                # austrian cities have 4 digit ZIP codes
                country = "AT"
                zip = zip[(len(zip) - 4):len(zip)]
            else:
                # German cities have 5 digit ZIP codes
                country = "DE"
                zip = zip[(len(zip) - 5):len(zip)]

        startInitialZip = workstring.find(initialzip)

        street = workstring[0:startInitialZip]
        street = cleanStartAndEnd(street)

        city = workstring[(startInitialZip + len(initialzip)):len(workstring)]
        city = cleanStartAndEnd(city)

        # Adding values
        result = Address(street, zip, city, country)

        return result


class WebsiteScope:
    def __init__(self, website=None, scopeType=0, url=None, dbId=None):
        self.website=website
        self.scopeType=scopeType
        self.url=url
        self.dbId=dbId


    def reIdentify(self):
        #print("reidentify scope: ", self.scopeType)
        try:
            result = None

            html_page = None
            try:
                ssl.match_hostname = lambda cert, hostname: True
                html_page = requests.get(self.website.protocol + "://" + self.website.website, timeout=10, verify=False).text
            except BaseException:
                pass

            if html_page is not None:

                if self.scopeType == 1:
                    # 1 = homepage
                    result = self.website.website
                elif 2 <= self.scopeType <= 5:
                    # in this table we have all the search terms we have too look for to identify the link to this scope
                    tests = db.execute('''select searchTerm FROM website_scopeTypes where scopeType=%s;''', (self.scopeType,))


                    soup = BeautifulSoup(html_page, "html.parser")
                    for test in tests:
                        for link in soup.findAll('a', href=True):
                            content = str(cleanStartAndEnd(link.string)).lower()
                            val = content.find(test[0])
                            if val >= 0:
                                result = link['href']
                                if not result.startswith("http"):
                                    # absolute path on same domain
                                    if (result.startswith("/")):
                                        # first occurance after "https://"
                                        slash = self.website.website.find("/", 9)
                                        # e.g. https://www.truffle.one/some/thing
                                        if slash > 0:
                                            rooturl = self.website.website[0:(slash - 1)]
                                        # e.g. http://www.truffle.one (just domain without ending slash)
                                        else:
                                            rooturl = self.website.website
                                        result = rooturl + result

                                    # relative path on same domain
                                    else:
                                        # find last occurance of "/"
                                        slash = self.website.website.rfind("/")
                                        rooturl = self.website.website[0:(slash - 1)]
                                        result = rooturl + result
                if result is not None:
                    result = clnUrlFromProtocol(clnUrlFromParameters(result))
                    self.url = result
                    self.save()
        except BaseException:
            traceback.print_exc()
        #print("identified: ", self.url)
        return self.url

    def save(self):
        #print("saving scope", self.website.website, self.scopeType )
        websiteId = None
        if self.website is not None:
            websiteId = self.website.dbId

        try:
            if self.dbId is not None:
                # update in SQL DB
                db.execute('''
                    UPDATE website_scopes set websiteId=%s, scopeType=%s, url=%s
                    where websiteScopeId=%s;
                    ''', (websiteId, self.scopeType, self.url, self.dbId), True)

            else:
                # insert into db
                self.dbId = db.execute('''
                    INSERT INTO website_scopes(websiteId, scopeType, url) 
                    values (%s, %s, %s);
                    ''', (websiteId, self.scopeType, self.url), True)
        except BaseException:
            traceback.print_exc()
        return self.dbId

    def delete(self):
        if self.dbId is not None:
            try:
                db.execute('''
                                DELETE FROM website_scopes where websiteScopeId=%s;
                                ''', (self.dbId, ), True)
                self.dbId = None
            except BaseException:
                traceback.print_exc()
        return self.dbId

