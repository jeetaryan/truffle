import re
from netaddr import *
import traceback
import phonenumbers
import email_normalize
from netaddr import *
import ipaddress

from urllib.parse import unquote

def unescapeSpecialLetters(string):
    try:
        return unquote(string, errors='strict')
    except UnicodeDecodeError:
        return unquote(string, encoding='latin-1')

def cleanFromHTMLTags(text):
    return re.sub("<.*>", " ", text)


# trims strings in terms of removing starting and ending separators etc.
def cleanStartAndEnd(text):
    result = str(text);
    workstring = str(text);

    # clean at beginning and end
    matchstrings = re.findall("([^A-Za-z0-9äÄöÖüÜß()])*", str(text))

    for matchString in matchstrings:

        # clean beginning
        if (result.startswith(matchString)):
            result = result[len(matchString):len(result)]

        # clean end
        elif (result.endswith(matchString)):
            result = result[0: len(result) - len(matchString)]

        # print(result)

    # in cases where more than one char need to be removed
    if (result == text):
        return result
    else:
        return cleanStartAndEnd(result)


# find out if we have German syntax (100.000.000,00) or English Syntax (100,000,000.00)
# 1=de, 0=en
def isNumberEnOrDe(string):
    language = -1
    countDot = string.count(".")
    countComma = string.count(",")
    if (countDot > 1 and countComma <= 1):
        language = 1  # more dots than commas (-> German syntax)
    elif (countDot <= 1 and countComma > 1):
        language = 0  # more commas than dots (-> English syntax)
    elif (countDot == 0 and countComma == 0):
        language = 0  # any language (like an integer)
    elif (countDot == 1 and countComma == 1):
        # is comma first or dot?
        language = 1 if (string.rfind(',') > string.rfind('.')) else 0
    return language


# remove ending and trailing spaces and CRNL
# make it None if len = 0
def cln(string):
    result = None
    if string:
        result = str(string)
        if result != None: result = result.strip()
        if result == "": result = None
    return result


def removeCharOtherThanDotsAndCommas(string):
    return re.sub(r'[^0-9.,]', '', str(string))


def removeCharAll(string):
    result = re.sub(r'[^0-9]', '', str(string))
    return result


def clnSpacesAndDashes(string):
    result = string.replace(" ", "")
    result = result.replace("-", "")
    result = result.replace("/", "")
    result = result.replace("\\", "")
    return result


def clnFloat(string):
    result = cln(str(string))

    if result != None:
        result = removeCharOtherThanDotsAndCommas(result)
        if result != "":
            language = isNumberEnOrDe(result)
            # remove dots or commas
            result = float(result.replace(".", "")) if (language == 1) else float(result.replace(",", ""))
        else:
            result = None
    return result


def clnInt(string):
    result = cln(str(string))
    if result != None:
        result = removeCharAll(result)
        if result != "":
            result = int(result)
        else:
            result = None
    return result


def clnContinuumInt(string):
    result = cln(str(string))
    result_0 = None
    result_1 = None

    if result != None:
        if "to" in result:
            result_0, result_1 = result.split("to")
            result_1 = clnInt(result_1)
        elif "-" in result:
            result_0, result_1 = result.split("-")
            result_1 = clnInt(result_1)
        elif "bis" in result:
            result_0, result_1 = result.split("bis")
            result_1 = clnInt(result_1)
        else:
            result_0 = clnInt(result)
        result_0 = clnInt(result_0)
    return result_0, result_1, result


def clnContinuumFloat(string):
    result = cln(str(string))
    result_0 = None
    result_1 = None

    if result != None:
        if "to" in result:
            result_0, result_1 = result.split("to")
            result_1 = clnFloat(result_1)
        elif "-" in result:
            result_0, result_1 = result.split("-")
            result_1 = clnFloat(result_1)
        elif "bis" in result:
            result_0, result_1 = result.split("bis")
            result_1 = clnFloat(result_1)
        else:
            result_0 = clnFloat(result)
        result_0 = clnFloat(result_0)
    return result_0, result_1, result


def clnPhone(string, countrycode):
    if string:
        num = cln(string)
        if num and num != "":
            # print (num)
            my_number = phonenumbers.parse(num, countrycode)
            if phonenumbers.is_possible_number(my_number):
                return str(phonenumbers.format_number(my_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
    return None


def clnEmail(string):
    if string is not None:
        return str(email_normalize.normalize(cln(string)).normalized_address)
    return None

def clnWebsite(string):
    # normalize to domain and subdomain only www.web.de
    website = cln(string)
    if website != None:
        websiteSplit = website.split("://")
        if len(websiteSplit) > 1:
            website = websiteSplit[1]
        if website[len(website) - 1] == "/":
            website = website[:-1]

        websiteSplit = website.split("/")
        website = websiteSplit[0]

        websiteSplit = website.split("?")
        website = websiteSplit[0]

        websiteSplit = website.split("#")
        website = websiteSplit[0]
    return website


def clnSubDomain(string):
    # normalize to domain only web.de
    website = cln(string)
    if website != None:
        website = clnWebsite(website)
        if website != None:
            websiteSplit = website.split("/")
            if len(websiteSplit) > 1:
                website = websiteSplit[0]
    return website


def clnUrlFromParameters(string):
    # normalize to protocol, subdomain, domain, path without parameters and #, http://www.web.de/somepage/some.php
    website = cln(string)
    if website != None:
        websiteSplit = website.split("?")
        if len(websiteSplit) > 1:
            website = websiteSplit[0]

        websiteSplit = website.split("#")
        if len(websiteSplit) > 1:
            website = websiteSplit[0]
    return website


def clnUrlFromProtocol(string):
    # normalize to subdomain, domain, path, parameters and #, www.web.de/somepage/some.php#what?ever=2
    website = cln(string)
    if website != None:
        websiteSplit = website.split("//")
        if len(websiteSplit) > 1:
            website = websiteSplit[1]

    return website


################################## IP CONVERSION ####################################################

def ip2int(string_ip):
    try:
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv4Address:
            return int(ipaddress.IPv4Address(string_ip))
        if type(ipaddress.ip_address(string_ip)) is ipaddress.IPv6Address:
            return int(ipaddress.IPv6Address(string_ip))
    except Exception as e:
        traceback.print_exc()
        return -1


def int2ip(int_ip):
    try:
        if int_ip <= 4294967295:
            return format(ipaddress.IPv4Address(int_ip))
        else:
            return format(ipaddress.IPv6Address(int_ip))
    except Exception as e:
        traceback.print_exc()
        return -1

