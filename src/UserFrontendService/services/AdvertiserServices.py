from services import DbConfig
import datetime

db = DbConfig.getDB()


def bindAdvertiser():
    advertiserData = db.execute('''SELECT advertiserId, advertiserName FROM advertiser''')
    option = ""
    for x in advertiserData:
        option += f"<option value={x[0]} selected='selected'>{x[1]}</option>"
    return option


def addAdvertise(advertise):
    sql = "insert into advertiser(advertiserName) value(%s)"
    arg = [advertise]
    db.execute(sql, args=arg, commit=True)
    return "advertise inserted into table."


def deleteAdvertise(advertiseId):
    sql = ("delete from advertiser where advertiserId = %s")
    arg = [advertiseId]
    db.execute(sql, args=arg, commit=True)
    return "1"


def editAdvertise(advertiseId):
    sql = ("select * from advertiser where advertiserId = %s")
    arg = [advertiseId]
    data = db.execute(sql, args=arg, commit=False)
    return data


def updateAdvertise(advertiseId, advertiseName):
    sql = ("update advertiser set advertiserName= %s where advertiserId =%s")
    arg = [advertiseName, advertiseId]
    db.execute(sql, args=arg, commit=True)
    return "1"


def bindCampaign(advertiseId):
    sql = '''SELECT campaignId, campaignName FROM campaigns where advertiserId=%s'''
    arg = [advertiseId]
    campaignData = db.execute(sql, args=arg, commit=False)
    option = ""
    for x in campaignData:
        option += f"<option value={x[0]} selected='selected'>{x[1]}</option>"
    return option


def deleteCampaign(campaignId):
    sql = ("delete from campaigns where campaignId = %s")
    arg = [campaignId]
    db.execute(sql, args=arg, commit=True)
    return "1"


def campaignAdd(advertiseId, campaignName, customerId):
    sql = "insert into campaigns (advertiserId, campaignName, customerId) value(%s,%s,%s)"
    arg = [advertiseId, campaignName, customerId]
    db.execute(sql, args=arg, commit=True)
    return "1"


def campaignDetails(advertiseId, campaignId):
    sql = """select campaignId, campaignName, campaignStart, campaignEnd, active
                from campaigns where advertiserId =%s and campaignId=%s"""
    arg = [advertiseId, campaignId]
    data = db.execute(sql, args=arg, commit=False)
    return data


def addCampaignDetails(campaignId, campaignsName, fromData, tillData, activeData):
    # fromData = '2023-01-09 05:30:00'
    # tillData = '2023-01-09 05:30:00'
    sql = "UPDATE `campaigns` SET `campaignName`=%s,`campaignStart`=%s,`campaignEnd`=%s,`active`=%s WHERE campaignId=%s"

    arg = [campaignsName, fromData, tillData, activeData, campaignId]
    db.execute(sql, args=arg, commit=True)
    if db:
        return "Campaign details updated."
    else:
        return "Campaign details could not be updated."


def advertisingPostContent(campaignId, html1, html2, headline, headline2, textarea,
                           textarea2, link, link2, attribution, attribution2, split_url, split_url2, t3nContent,
                           t3nHome):
    def desktop(t3n):
        # for desktop ##################
        sql = """insert into nativeads (campaignId, type, adHeadline, adText, adLink, attribution, adCreative,
                                                    forMobile, html) values(%s, %s, %s,%s, %s, %s,%s,%s,%s)"""
        arg = [campaignId, t3n, headline, textarea, link, attribution, split_url, 0, html1]
        data = db.execute(sql, args=arg, commit=True)
        return data

    def mobile(t3n):
        # for mobile ###################
        sql = """insert into nativeads (campaignId, type, adHeadline, adText, adLink, attribution, adCreative,
                                        forMobile, html) values(%s, %s, %s,%s, %s, %s,%s,%s,%s)"""
        arg = [campaignId, t3n, headline2, textarea2, link2, attribution2, split_url2, 1, html2]
        data = db.execute(sql, args=arg, commit=True)
        return data

    if t3nContent == "1" and t3nHome == "2":
        desktop(t3nContent)
        mobile(t3nContent)
        desktop(t3nHome)
        mobile(t3nHome)
    elif t3nContent == "1":
        desktop(t3nContent)
        mobile(t3nContent)
    elif t3nHome == "2":
        desktop(t3nHome)
        mobile(t3nHome)
    else:
        print("no checkbox found.")

    return t3nContent


def performance():
    import math
    # where type=1 and for desktop
    sql = "select impressions, clicks from nativeads where type=1 and forMobile=0"
    data = db.execute(sql, commit=False)
    impressions = 0
    clicks = 0
    for x in data:
        impressions += x[0]
        clicks += x[1]
    percentage = round((clicks / impressions) * 100)
    listType1Desktop = [impressions, clicks, percentage]

    # where type=1 and for mobile
    sql = "select impressions, clicks from nativeads where type=1 and forMobile=1"
    data = db.execute(sql, commit=False)
    impressions = 0
    clicks = 0
    for x in data:
        impressions += x[0]
        clicks += x[1]
    percentage = round((clicks / impressions) * 100)
    listType1Mobile = [impressions, clicks, percentage]

    # where type=2 and for desktop
    sql = "select impressions, clicks from nativeads where type=2 and forMobile=0"
    data = db.execute(sql, commit=False)
    impressions = 0
    clicks = 0
    for x in data:
        impressions += x[0]
        clicks += x[1]
    percentage = round((clicks / impressions) * 100)
    listType2Desktop = [impressions, clicks, percentage]

    # where type=2 and for MObile
    sql = "select impressions, clicks from nativeads where type=2 and forMobile=1"
    data = db.execute(sql, commit=False)
    impressions = 0
    clicks = 0
    for x in data:
        impressions += x[0]
        clicks += x[1]
    percentage = round((clicks / impressions) * 100)
    listType2Mobile = [impressions, clicks, percentage]

    # total all type #################################
    totalImpressionsType1 = listType1Desktop[0] + listType1Mobile[0]
    totalImpressionsType2 = listType2Desktop[0] + listType2Mobile[0]
    totalClickType1 = listType1Desktop[1] + listType1Mobile[1]
    totalClickType2 = listType2Desktop[1] + listType2Mobile[1]
    totalPercentageType1 = round((totalClickType1 / totalImpressionsType1) * 100)
    totalPercentageType2 = round((totalClickType2 / totalImpressionsType2) * 100)
    totalData = [totalImpressionsType1, totalClickType1, totalPercentageType1
        , totalImpressionsType2, totalClickType2, totalPercentageType2]
    totalTotalImpressions = totalData[0] + totalData[3]
    totalTotalClick = totalData[1] + totalData[4]
    totalTotalPercentage = round((totalTotalClick / totalTotalImpressions) * 100)
    data = [totalTotalImpressions, totalTotalClick, totalTotalPercentage]
    totalData.extend(data)

    # end of total all type

    # total of desktop ##########################
    totalDesktopImpressions = listType1Desktop[0] + listType2Desktop[0]
    totalDesktopClick = listType1Desktop[1] + listType2Desktop[1]
    totalDesktopPercentage = round((totalDesktopClick / totalDesktopImpressions)*100)
    TotalDesktop = [totalDesktopImpressions, totalDesktopClick, totalDesktopPercentage]
    totalData.extend(TotalDesktop)
    # end of desktop totalData

    # total of mobile ##########################
    totalMobileImpressions = listType1Mobile[0] + listType2Mobile[0]
    totalMobileClick = listType1Mobile[1] + listType2Mobile[1]
    totalMobilePercentage = round((totalMobileClick / totalMobileImpressions)*100)
    TotalMobile = [totalMobileImpressions, totalMobileClick, totalMobilePercentage]
    totalData.extend(TotalMobile)
    # end of desktop totalData

    return {'totalData': totalData, 'listType1Desktop': listType1Desktop, 'listType1Mobile': listType1Mobile,
            'listType2Desktop': listType2Desktop, 'listType2Mobile': listType2Mobile}
