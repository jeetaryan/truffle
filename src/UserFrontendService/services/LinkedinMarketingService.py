import datetime, random, string, requests
from services import DbConfig
from services.LoginService import User
import json

db = DbConfig.getDB()


CLIENT_ID = "78mmp799dp6ddw"
CLIENT_SECRET = "KeKccmbBLvhGjyU3"
REDIRECT_URI = "https://login.truffle.one/linkedinConfig"
SCOPES = "rw_ads"

def getLinkedinConnection(user, auth_code=None, state=None):

    if auth_code is not None and auth_code != "" and state is not None and state != "":
        if user.getUserConfig("linkedinMarketing.auth_code_state") == state:

            headers = {'Content-Type': 'x-www-form-urlencoded'}
            response = requests.get(
                f"https://www.linkedin.com/oauth/v2/accessToken?code={auth_code}&grant_type=authorization_code&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&redirect_uri={REDIRECT_URI}",
                headers=headers)
            jsonresponse = response.json()
            #print(jsonresponse)



            return LinkedinConnection(user,
                  jsonresponse.get("access_token"),
                  jsonresponse.get("refresh_token"),
                  datetime.datetime.now() + datetime.timedelta(seconds=jsonresponse.get("expires_in")),
                  datetime.datetime.now() + datetime.timedelta(seconds=jsonresponse.get("refresh_token_expires_in")),
                  jsonresponse.get("scope")
                  )

    refresh_token_expiry = user.getUserConfig("linkedinMarketing.refresh_token_expiry")
    #print("exp", refresh_token_expiry)
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    if refresh_token_expiry is not None and datetime.datetime.strptime(refresh_token_expiry, '%Y-%m-%d %H:%M:%S.%f') > tomorrow:
        return LinkedinConnection(user)
    else:
        return None


def getAuthLink(user):
    state = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
    user.setUserConfig("linkedinMarketing.auth_code_state", state)
    return f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={state}&scope={SCOPES}"


class LinkedinConnection:
    def __init__(self, user, access_token=None, refresh_token=None, access_token_expiry=None, refresh_token_expiry=None, scope=None):
        self.user = user

        if access_token is None:
            self.access_token = self.user.getUserConfig("linkedinMarketing.access_token")
            self.refresh_token = self.user.getUserConfig("linkedinMarketing.refresh_token")
            self.access_token_expiry = self.user.getUserConfig("linkedinMarketing.access_token_expiry")
            self.access_token_expiry = self.user.getUserConfig("linkedinMarketing.refresh_token_expiry")
            self.scope = self.user.getUserConfig("linkedinMarketing.scope")


            #self.refreshAccessToken()
        else:
            self.access_token = access_token
            self.refresh_token = refresh_token
            self.access_token_expiry = access_token_expiry
            self.refresh_token_expiry = refresh_token_expiry
            self.scope = scope
            self.save()

    def save(self):
        self.user.setUserConfig("linkedinMarketing.access_token", self.access_token)
        self.user.setUserConfig("linkedinMarketing.refresh_token", self.refresh_token)
        self.user.setUserConfig("linkedinMarketing.access_token_expiry", self.access_token_expiry)
        self.user.setUserConfig("linkedinMarketing.refresh_token_expiry", self.access_token_expiry)
        self.user.setUserConfig("linkedinMarketing.scope", self.scope)

    def refreshAccessToken(self):
        # refreshing tokens only works for approved Marketing Developer Platform (MDP) partners.
        # https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens?context=linkedin%2Fcontext&view=li-lms-2023-04
        headers = {'Content-Type': 'x-www-form-urlencoded'}
        refresh_token = self.user.getUserConfig("linkedinMarketing.refresh_token")

        #print("--> access token before refreshing: ", self.user.getUserConfig("linkedinMarketing.access_token"))

        response = requests.get(
            f"https://www.linkedin.com/oauth/v2/accessToken?grant_type=refresh_token&refresh_token={refresh_token}&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}",
            headers=headers)
        jsonresponse = response.json()
        #print(jsonresponse)

        #print("--> access token after refreshing: ", jsonresponse.get("access_token"))
        self.access_token = jsonresponse.get("access_token")
        self.refresh_token = jsonresponse.get("refresh_token")
        self.access_token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=jsonresponse.get("expires_in"))
        self.refresh_token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=jsonresponse.get("refresh_token_expires_in"))
        self.scope = jsonresponse.get("scope")
        self.save()
        return

    def getAdAccounts(self):
        headers = {'Authorization': f'Bearer {self.access_token}',
                   'Linkedin-Version': '202304',
                   'Content-Type': 'application/json',
                   'X-Restli-Protocol-Version': '2.0.0'}
        response = requests.get(
            "https://api.linkedin.com/rest/adAccounts?q=search&search=(status:(values:List(ACTIVE,DRAFT)))&sort=(field:ID,order:ASCENDING)",
            headers=headers)
        adAccounts = []

        if response is not None:
            jsonresponse = response.json()
            print(jsonresponse)

            for c in jsonresponse.get("elements"):
                adAccounts.append(LinkedinAdAccount(c))

            if jsonresponse.get("paging") is not None:
                output_dict = [x for x in jsonresponse.get("paging").get("links") if x['rel'] == 'next']
                while output_dict is not None and len(output_dict) > 0:
                    href = "https://api.linkedin.com" + output_dict[0].get("href")
                    response = requests.get(href, headers=headers)
                    output_dict = None
                    if response is not None:
                        jsonresponse = response.json()
                        for c in jsonresponse.get("elements"):
                            adAccounts.append(LinkedinAdAccount(c))
                        output_dict = [x for x in jsonresponse.get("paging").get("links") if x['rel'] == 'next']
        return adAccounts

    def getCampaignGroups(self, adAccount = None):
        headers = {'Authorization': f'Bearer {self.access_token}',
                   'Linkedin-Version': '202304',
                   'Content-Type': 'application/json',
                   'X-Restli-Protocol-Version': '2.0.0'}
        if adAccount is not None and adAccount != "None":
            requestUrl = f"https://api.linkedin.com/rest/adCampaignGroups?q=search&search=(account:(values:List(urn%3Ali%3AsponsoredAccount%3A{adAccount})))&sort=(field:ID,order:ASCENDING)"
        else:
            requestUrl = f"https://api.linkedin.com/rest/adCampaignGroups?q=search&search=(status:(values:List(ACTIVE,DRAFT,PAUSED)))&sort=(field:ID,order:ASCENDING)"
        #print(requestUrl)
        response = requests.get(requestUrl, headers=headers)
        adGroups = []

        if response is not None:
            jsonresponse = response.json()
            #print(jsonresponse)

            for c in jsonresponse.get("elements"):
                adGroups.append(LinkedinCampaignGroup(c))

            if jsonresponse.get("paging") is not None:
                output_dict = [x for x in jsonresponse.get("paging").get("links") if x['rel'] == 'next']
                while output_dict is not None and len(output_dict)>0:
                    href = "https://api.linkedin.com" + output_dict[0].get("href")
                    response = requests.get(href, headers=headers)
                    output_dict = None
                    if response is not None:
                        jsonresponse = response.json()
                        for c in jsonresponse.get("elements"):
                            adGroups.append(LinkedinCampaignGroup(c))
                        output_dict = [x for x in jsonresponse.get("paging").get("links") if x['rel'] == 'next']
        return adGroups

    def getCampaigns(self, campaignGroup = None):
        headers = {'Authorization': f'Bearer {self.access_token}',
                   'Linkedin-Version': '202304',
                   'Content-Type': 'application/json',
                   'X-Restli-Protocol-Version': '2.0.0'}
        if campaignGroup is not None  and campaignGroup != "None":
            requestUrl = f"https://api.linkedin.com/rest/adCampaigns?q=search&search=(campaignGroup:(values:List(urn%3Ali%3AsponsoredCampaignGroup%3A{campaignGroup})))&sort=(field:ID,order:ASCENDING)"
        else:
            requestUrl = f"https://api.linkedin.com/rest/adCampaigns?q=search&search=(status:(values:List(ACTIVE,DRAFT,PAUSED)))&sort=(field:ID,order:ASCENDING)"
        # print(requestUrl)
        response = requests.get(requestUrl, headers=headers)

        campaigns = []

        if response is not None:
            jsonresponse = response.json()
            #print(jsonresponse)

            for c in jsonresponse.get("elements"):
                campaign = LinkedinCampaign(c)
                campaigns.append(campaign)

            if jsonresponse.get("paging") is not None:
                output_dict = [x for x in jsonresponse.get("paging").get("links") if x['rel'] == 'next']
                while output_dict is not None and len(output_dict)>0:
                    href = "https://api.linkedin.com" + output_dict[0].get("href")
                    response = requests.get(href, headers=headers)
                    output_dict = None
                    if response is not None:
                        jsonresponse = response.json()
                        for c in jsonresponse.get("elements"):
                            campaign = LinkedinCampaign(c)
                            campaigns.append(campaign)
                        output_dict = [x for x in jsonresponse.get("paging").get("links") if x['rel'] == 'next']
        return campaigns

    def getTargetCampaigns(self, segmentId):
        sql = "SELECT linkedInCampaignId from segments_linkedinTargetCampaigns where segmentId = %s"
        data = db.execute(sql, (segmentId, ))
        campaigns = []
        for d in data:
            campaigns.append(self.getCampaign(d[0]))
        return campaigns

    def addTargetCampaigns(self, campaignId, segmentId):
        try:
            sql = "INSERT INTO segments_linkedinTargetCampaigns(linkedInCampaignId, segmentId) values(%s, %s)"
            db.execute(sql, (campaignId, segmentId), True)
        except BaseException:
            return 0
        return 1

    def removeTargetCampaigns(self, campaignId, segmentId):
        sql = "DELETE FROM segments_linkedinTargetCampaigns where linkedInCampaignId=%s and segmentId=%s"
        db.execute(sql, (campaignId, segmentId), True)
        return


    def getCampaign(self, campaignId):
        headers = {'Authorization': f'Bearer {self.access_token}',
                   'Linkedin-Version': '202304',
                   'Content-Type': 'application/json',
                   'X-Restli-Protocol-Version': '2.0.0'}
        response = requests.get(
            f"https://api.linkedin.com/rest/adCampaigns/{campaignId}?fields=id,name,type,status,campaignGroupInfo,accountInfo",
            headers=headers)

        if response is not None:
            jsonresponse = response.json()
            #print(jsonresponse)

            return LinkedinCampaign(jsonresponse)

        return None

    def getCampaignGroup(self, adCampaignGroupsId):
        headers = {'Authorization': f'Bearer {self.access_token}',
                   'Linkedin-Version': '202304',
                   'Content-Type': 'application/json',
                   'X-Restli-Protocol-Version': '2.0.0'}
        response = requests.get(
            f"https://api.linkedin.com/rest/adCampaignGroups/{adCampaignGroupsId}",
            headers=headers)

        if response is not None:
            jsonresponse = response.json()
            #print(jsonresponse)
            return LinkedinCampaignGroup(jsonresponse)
        return None

    def getAdAccount(self, adAccountID):
        headers = {'Authorization': f'Bearer {self.access_token}',
                   'Linkedin-Version': '202304',
                   'Content-Type': 'application/json',
                   'X-Restli-Protocol-Version': '2.0.0'}
        response = requests.get(
            f"https://api.linkedin.com/rest/adAccounts/{adAccountID}",
            headers=headers)

        if response is not None:
            jsonresponse = response.json()
            #print(jsonresponse)
            return LinkedinAdAccount(jsonresponse)
        return None


class LinkedinAdAccount:
    def __init__(self, jsonData=None, id = None, name = None, status = "ACTIVE"):
        if jsonData is not None:
            self.id = jsonData.get("id")
            self.name = jsonData.get("name")
            self.status = jsonData.get("status")
            #TODO: all the other infos from adaccount jsonData
        else:
            self.id = id
            self.name = name
            self.status = status
            self.campaignGroups = {}

class LinkedinCampaignGroup:
    def __init__(self, jsonData=None, id = None, name = None, status = "DRAFT", adAccount = None):
        if jsonData is not None:
            self.id = jsonData.get("id")
            self.name = jsonData.get("name")
            self.status = jsonData.get("status")
            self.adAccount = LinkedinAdAccount(jsonData.get("accountInfo"))

            #TODO: all the other infos from campaigngroup jsonData
        else:
            self.id = id
            self.name = name
            self.status = status
            self.adAccount = adAccount
            self.campaigns = {}

class LinkedinCampaign:
    def __init__(self, jsonData=None, id = None, name = None, status = "DRAFT", type = "SPONSORED_UPDATES", campaignGroup = None):
        if jsonData is not None:
            self.id = jsonData.get("id")
            self.name = jsonData.get("name")
            self.status = jsonData.get("status")
            self.type = jsonData.get("type")
            #TODO: all the other infos from campaign jsonData

            print(json.dumps(jsonData, indent=2))

            self.campaignGroup = LinkedinCampaignGroup(jsonData.get("campaignGroupInfo"))
            self.campaignGroup.adAccount = LinkedinAdAccount(jsonData.get("accountInfo"))

        else:
            self.id = id
            self.name = name
            self.campaignGroup = campaignGroup
            self.status = status
            self.type = type

    def __str__(self):
        return self.name + "(" + str(self.id) + ")"


