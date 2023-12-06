from flask import Flask, render_template, request, session, url_for, redirect, jsonify
from itsdangerous import URLSafeTimedSerializer

import datetime

from services import LoginService, UserDashboard, DbConfig, ContentScoreService, CustomerService, \
    LinkedinMarketingService, SegmentsService, JobOfferService, factSheetService, CompanyService
#from services.LinkedinMarketingService import T1jsonEncoder
from flask_mail import Mail
from flask_session import Session
from datetime import timedelta
from flask import Response
import json
from json import JSONEncoder

app = Flask(__name__)
db = DbConfig.getDB()

##############################################################
'''

HERE ARE SOME BASIC RULES FOR CODING WEB SERVICES:
- always start each endpoint with:
    if not session.get('emailId'):
        return redirect(url_for('login'))
- never handover a customerId in a remote request. Always get the current customer from:
    session.get("customer")       
- never use SQL here. Always have teh SQL in Service files.
- make use of objects and classes
- use JSON if possible


'''

#

# configure session ##########################################
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "/var/www/login_sessions"
Session(app)

# configuration of mail ######################################
app.config['MAIL_SERVER'] = 'smtp-relay.sendinblue.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'niko.bender@truffle.one'
app.config['MAIL_PASSWORD'] = '1D9TbMVBGwHIgO4j'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['SECRET_KEY'] = "J9FfvRMACfQ9HzoI1CpY"
mail = Mail(app)  # instantiate the mail class
s_key = URLSafeTimedSerializer(app.config["SECRET_KEY"])


@app.template_filter()
def hrsminsec(seconds):
    return "{}".format(str(timedelta(seconds=seconds)))


@app.route("/", methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = LoginService.authenticateUser(username, password)
        if user != None:
            session['user'] = user
            session['username'] = user.firstName + ' ' + user.lastName
            customer_id = user.customerId
            session['emailId'] = user.email
            session['customerId'] = customer_id
            session["LinkedinMarketingConnection"] = LinkedinMarketingService.getLinkedinConnection(user)
            session["customer"] = CustomerService.getCustomer(customer_id)
            session["segmentationService"] = SegmentsService.getSegmentationService(session["customer"])



            data = UserDashboard.dashboard(customer_id)
            if data != None:
                return render_template("dashboard.html", data=data)
            else:
                data = 0
                return render_template("dashboard.html", data=data)
        else:
            return render_template("index.html", msg="Entered username or password is not correct.")
    elif 'customerId' in session:
        data = UserDashboard.dashboard(session['customerId'])
        if data != None:
            return render_template("dashboard.html", data=data)
        else:
            data = 0
            return render_template("dashboard.html", data=data)
    else:
        return render_template('index.html')


@app.route("/dashboard_back/<customer_id>")
def dashboard_back(customer_id):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    data = UserDashboard.dashboard(customer_id)
    return render_template("dashboard.html", data=data)


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        print(request.form)
        email = request.form['username']
        token = s_key.dumps(email, salt='email-confirmation-key')
        data = LoginService.register(email, mail=mail, token=token)
        if len(data) == 1:
            print("slsklksl1")
            return render_template('register.html', pre_reg=data['msg'])
        else:
            print("slsklksl2")
            return render_template('verify.html', verify_msg=data['msg'], data='')
    else:
        return render_template('register.html')


@app.route("/verify/<token>/<otp>", methods=['POST', 'GET'])
def verify(token, otp):
    if request.method == 'GET':
        email = s_key.loads(token, salt='email-confirmation-key', max_age=36000)
        data = LoginService.verify(email, otp)

        if data == 0:
            return render_template('register.html')
        else:
            return render_template('verify.html', data=data, verify_msg='')
    else:
        return render_template('register.html')


@app.route("/save_password", methods=['POST', 'GET'])
def save_password():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        f_name = request.form['f_name']
        l_name = request.form['l_name']
        gender = request.form['gender']
        company_name = request.form['company_name']
        email = session.get('emailId')
        password = request.form['password']
        data = LoginService.savePassword(f_name, l_name, gender, company_name, email, password)
        return data
    else:
        return render_template('register.html')


@app.route("/forget", methods=['POST', 'GET'])
def forget():
    if request.method == 'POST':
        email = request.form['email']
        token = s_key.dumps(email, salt='email-confirmation-key')
        data = LoginService.sendOtp(email, mail, token)
        return {'output': data}
    else:
        return render_template('forget.html')


@app.route("/verify_for_forget/<token>/<otp>", methods=['POST', 'GET'])
def verify_for_forget(token, otp):
    if request.method == 'GET':
        email = s_key.loads(token, salt='email-confirmation-key', max_age=36000)
        data = LoginService.verify_for_forget(email, otp)
        return render_template('forget.html', data=data)
    else:
        return render_template('forget.html')


@app.route("/update_password", methods=['POST', 'GET'])
def update_password():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        data = LoginService.update_password(email, password)
        return data
    else:
        return render_template('forget.html')


@app.route("/resetPassword", methods=['POST', 'GET'])
def resetPassword():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        old_password = request.form['password']
        email = request.form['email']
        data = LoginService.reset(old_password, new_password, email)
        return data
    else:
        return render_template('resetPassword.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/dashboard")
def dashboard():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    else:
        return render_template('dashboard.html')


@app.route('/visitDetails', methods=['POST', 'GET'])
def visitDetails():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        company_id = request.form['companyId']
        customer_id = session['customerId']
        data = UserDashboard.visitDetails(company_id, customer_id)
        return data
    else:
        return render_template('dashboard.html')


@app.route('/contactDetails', methods=['POST', 'GET'])
def contactDetails():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        company_id = request.form['companyId']
        customer_id = session['customerId']
        data = UserDashboard.contactDetails(company_id, customer_id)
        return data
    else:
        return render_template('dashboard.html')



@app.route('/wviConfig')
def wviConfig():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    return render_template('wviConfig.html', customerId=session.get("customerId"))

@app.route('/userPreferences')
def userPreferences():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    return render_template('userPreferences.html')



@app.route('/jobOfferSearchConfig')
def jobOfferSearchConfig():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    josgs = JobOfferService.getJobOfferSearchGroups(session.get("customer"))
    return render_template('jobOfferSearchConfig.html', josgs=josgs)

@app.route('/contentScoreDefinition')
def contentScoreDefinition():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    else:
        cid = session.get('customerId')
        css = ContentScoreService.getContentScoresOfCustomer(CustomerService.getCustomer(cid))

        for cs in css:
            #print("debug cs:", cs.name)
            for st in cs.searchTerms:
                pass
                #print("debug st:", st.searchTerm)

        return render_template('contentScoreDefinition.html', css=css)


@app.route('/contentScore', methods=['POST', 'GET'])
def contentScore():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        company_id = request.form['companyId']
        customer_id = session['customerId']
        data = UserDashboard.contentScore(customer_id, company_id)
        return data
    else:
        return render_template('dashboard.html')


@app.route('/updateProfile', methods=['POST', 'GET'])
def updateProfile():
    if not session.get('emailId'):
        return redirect(url_for('login'))


    session['user'].firstName = request.form['f_name']
    session['user'].lastName = request.form['l_name']
    session['user'].gender = request.form['gender']
    session['user'].language = request.form['language']
    session['user'].save()
    session['username'] = session['user'].firstName + " " + session['user'].lastName
    return ""


@app.route('/linkedinConfig', methods=['POST', 'GET'])
def linkedinConfig():
    if not session.get('emailId'):
        return redirect(url_for('login'))

    auth_code = request.args.get('code')
    state = request.args.get('state')

    # if this is a valid redirect from LinkedIn OAuth
    if auth_code is not None and state is not None:
        con = LinkedinMarketingService.getLinkedinConnection(session["user"], auth_code, state)
        if con is not None:
            session["LinkedinMarketingConnection"] = con

    return segment_config()


@app.route('/isLinkedinConnected', methods=['POST', 'GET'])
def isLinkedinConnected():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    if session["LinkedinMarketingConnection"] is not None:
        return True
    return False


@app.route('/getLinkedinOAuthLink', methods=['POST', 'GET'])
def getLinkedinOAuthLink():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    return LinkedinMarketingService.getAuthLink(session.get("user"))


@app.route('/getLinkedinAdAccounts', methods=['POST', 'GET'])
def getLinkedinAdAccounts():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    return T1jsonEncoder().encode(session["LinkedinMarketingConnection"].getAdAccounts())


@app.route('/getLinkedinCampaignGroups', methods=['POST', 'GET'])
def getLinkedinCampaignGroups():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    adAccount = None
    if request.method == 'POST':
        adAccount = request.form['adAccount']

    return T1jsonEncoder().encode(session["LinkedinMarketingConnection"].getCampaignGroups(adAccount))


@app.route('/getLinkedinCampaigns', methods=['POST', 'GET'])
def getLinkedinCampaigns():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    campaignGroup = None
    if request.method == 'POST':
        campaignGroup = request.form['campaignGroup']
    return T1jsonEncoder().encode(session["LinkedinMarketingConnection"].getCampaigns(campaignGroup))


@app.route('/deleteJosg', methods=['POST'])
def deleteJosg():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    jsonDoc = json.loads(request.data)
    JobOfferService.getJobOfferSearchGroup(int(jsonDoc.get("josgId"))).delete()
    data = {}
    data['status'] = "deleted"
    return json.dumps(data)

@app.route('/addJosg', methods=['POST'])
def addJosg():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    jsonDoc = json.loads(request.data)
    josg = JobOfferService.JobOfferSearchGroup(jsonDoc.get("josgName"), session.get("customer").customerId,
                                               jsonDoc.get("josgType"))
    josg.save()
    data = {}
    data['josgId'] = josg.dbId
    return json.dumps(data)

@app.route('/editJosg', methods=['POST'])
def editJosg():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    jsonDoc = json.loads(request.data)
    josgId = int(jsonDoc.get("josgId"))
    josg = JobOfferService.getJobOfferSearchGroup(josgId)
    josg.type = jsonDoc.get("josgType")
    josg.name = jsonDoc.get("josgName")
    josg.save()
    data = {}
    data['status'] = "edited"
    return json.dumps(data)

@app.route('/deleteJos', methods=['POST'])
def deleteJos():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    jsonDoc = json.loads(request.data)
    JobOfferService.getJobOfferSearch(int(jsonDoc.get("josId"))).delete()
    data = {}
    data['status'] = "deleted"
    return json.dumps(data)

@app.route('/addJos', methods=['POST'])
def addJos():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    jsonDoc = json.loads(request.data)
    josg = JobOfferService.getJobOfferSearchGroup(jsonDoc.get("josgId"))
    kw = jsonDoc.get("josKeyword")
    jos = JobOfferService.JobOfferSearch(josg, kw)
    jos.save()
    data = {}
    data['josId'] = jos.dbId
    return json.dumps(data)

@app.route('/editJos', methods=['POST'])
def editJos():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    jsonDoc = json.loads(request.data)
    josId = jsonDoc.get("josId")
    jos = JobOfferService.getJobOfferSearch(int(josId))
    jos.keyword = jsonDoc.get("josKeyword")
    jos.save()
    data = {}
    data['status'] = "edited"
    return json.dumps(data)

@app.route("/segment_config")
def segment_config():
    if not session.get('emailId'):
        return redirect(url_for('login'))

    linkedInOauth_link = None
    if session["LinkedinMarketingConnection"] is None:
        linkedInOauth_link = LinkedinMarketingService.getAuthLink(session.get("user"))

    return render_template('segment_config.html',
                           segments=SegmentsService.getSegments(session["customer"]),
                           linkedInOauth_link=linkedInOauth_link)


@app.route("/company/<companyId>/getSources", methods=["GET"])
def getSourcesOfCompany(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    company = CompanyService.getCompanyById(companyId)
    sources = company.getSources(session["customer"])
    dataType = request.args.get("dataType")
    if dataType is None or dataType == "json":
        return T1jsonEncoder().encode(sources)
    else:
        return render_template('response.html', sources=sources, name="sources")

@app.route("/company/<companyId>/getSegments", methods=["POST"])
def getSegmentsOfCompany(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    segments = SegmentsService.getSegmentsOfCompany(CompanyService.getCompanyById(companyId), session["customer"])

    dataType = request.args.get("dataType")
    if dataType is None or dataType == "json":
        return T1jsonEncoder().encode(segments)
    else:
        return render_template('response.html', segments=segments, name="segments", companyId=companyId)


# TODO to be replaced by getSourcesOfCompany (see above)
@app.route('/getSegmentCodes', methods=['POST', 'GET'])
def getSegmentCodes():
    if not session.get('emailId'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        companyIds = json.loads(request.data)
        data = {}
        data['companySegments'] = []

        for companyId in companyIds.get("companyIds"):
            companyCodes = {'companyId': companyId, 'colorCodes': []}

            sql = '''select colorCode
                     from (select * from segments_companies where companyId = %s) as a 
                     JOIN (SELECT * FROM segments where ownerCustomer=%s) as b on a.segmentId = b.segmentId

                        '''

            sqldata = db.execute(sql, (companyId, session["customerId"]))

            for code in sqldata:
                companyCodes["colorCodes"].append(code[0])
            data['companySegments'].append(companyCodes)
        return json.dumps(data)
    return ""


# TODO to be replaced by getSourcesOfCompany (see above)
@app.route('/getSourceCodes', methods=['POST'])
def getSourceCodes():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    companyIds = json.loads(request.data)
    data = {}
    data['companySegments'] = []

    for companyId in companyIds.get("companyIds"):
        companyCodes = {'companyId': companyId, 'colorCodes': []}

        sql = '''select colorCode
                 from (SELECT * from companies_customers where companyId = %s and customerId=%s) as a
                 JOIN companySources b on a.source=b.sourceId
                    '''

        sqldata = db.execute(sql, (companyId, session.get("customerId")))

        for code in sqldata:
            companyCodes["colorCodes"].append(code[0])
        data['companySegments'].append(companyCodes)
    return json.dumps(data)


@app.route('/getSegments', methods=['GET'])
def getSegments():
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    segments = SegmentsService.getSegments(session.get("customer"))
    return T1jsonEncoder().encode(segments)

@app.route('/segment/addSegment', methods=['GET', 'POST'])
def addSegment():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    data = json.loads(request.data)
    name = data.get("name")
    description = data.get("description")
    colorCode = data.get("colorCode")

    s = SegmentsService.Segment(session.get("customerId"), name, description, colorCode)
    s.save()
    return str(s.id)

@app.route('/segment/<segmentId>/getDetails', methods=['GET'])
def getDetailsOfSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    segment = SegmentsService.getSegment(segmentId)
    if session.get('customerId') == segment.ownerCustomerId:
        return T1jsonEncoder().encode(segment)
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')

@app.route('/segment/<segmentId>/update', methods=['POST'])
def updateSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    data = json.loads(request.data)
    name = data.get("name")
    description = data.get("description")
    colorCode = data.get("colorCode")

    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        s.save(name, description, colorCode)
        return str(s.id)
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')

@app.route('/segment/<segmentId>/delete', methods=['POST'])
def deleteSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')

    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        s.delete()
        return ""
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route('/segment/<segmentId>/setFilter', methods=['POST'])
def setFilterOfSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')

    data = json.loads(request.data)
    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        s.setFilter(data.get("filter"))
        s.setAutoUpdate(data.get("autoUpdate"))
        s.setReplaceTargets(data.get("replaceTargets"))
        return ""
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')

@app.route('/segment/<segmentId>/getFilter', methods=['POST'])
def getFilterOfSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')

    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        segmentFilter = s.getFilter()
        autoUpdate = s.getAutoUpdate()
        replaceTargets = s.getReplaceTargets()
        if segmentFilter is None:
            return ""
        else:
            return jsonify(filter=segmentFilter, autoUpdate=autoUpdate, replaceTargets=replaceTargets)
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route('/segment/<segmentId>/addCompanies', methods=['POST'])
def addCompaniesToSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    data = json.loads(request.data)
    companyIds = data.get("companyIds")

    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        for companyId in companyIds:
            s.addCompany(CompanyService.getCompanyById(companyId))
        return "OK"
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route('/segment/<segmentId>/removeCompanies', methods=['POST'])
def removeCompaniesFromSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    data = json.loads(request.data)
    companyIds = data.get("companyIds")
    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        for companyId in companyIds:
            s.removeCompany(CompanyService.getCompanyById(companyId))
        return "OK"
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route("/segment/<segmentId>/getCompanies", methods=["GET"])
def getCompaniesOfSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')

    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        return T1jsonEncoder().encode(s.getCompanies())
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route('/segment/<segmentId>/getLinkedinTargetings', methods=['GET'])
def getLinkedinTargetingsOfSegment(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        return T1jsonEncoder().encode(session["LinkedinMarketingConnection"].getTargetCampaigns(segmentId))
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route('/segment/<segmentId>/addLinkedinTargeting', methods=['POST'])
def addLinkedinTargeting(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    campaignId = request.form['campaignId']
    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        session["LinkedinMarketingConnection"].addTargetCampaigns(campaignId, segmentId)
        return ""
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')


@app.route('/segment/<segmentId>/removeLinkedinTargeting', methods=['POST'])
def removeLinkedinTargeting(segmentId):
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    campaignId = request.form['campaignId']
    s = SegmentsService.getSegment(segmentId)
    if s.ownerCustomerId == session.get("customerId"):
        session["LinkedinMarketingConnection"].removeTargetCampaigns(campaignId, segmentId)
        return ""
    return Response("{'error':'No permission'}", status=403, mimetype='application/json')




@app.route('/domain/<domain>/factsheet', methods=['GET'])
def factSheetByDomain(domain):
    headers = request.headers
    auth = headers.get("T1-Api-Key")
    if auth != "pjVyJSSISpAsQOCK4ZMmeHBIMxpDOswJ":
        return Response("{'error':'No permission'}", status=403, mimetype='application/json')
    company = CompanyService.getCompanyByWebsite(domain, False)
    if company is None:
        return Response("{'error':'Company not found'}", status=404, mimetype='application/json')
    return factSheet(company, CustomerService.getCustomer(79))

@app.route('/company/<companyId>/factsheet')
def factSheetByCompanyId(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    company = CompanyService.getCompanyById(companyId)
    return factSheet(company, session["customer"])

def factSheet(company, customer):
    if company is None:
        return Response("{'error':'Company not found'}", status=404, mimetype='application/json')
    sourcesData = company.getSources(customer)
    #check if customer may see this company (customer_companies table)
    if sourcesData is None or len(sourcesData) == 0:
        return Response("{'error':'No permission'}", status=403, mimetype='application/json')

    firmographics = company.getFirmographics()
    contactData = company.getContactData()
    financeData = company.getFinanceData()
    linkedinData = company.getLinkedInData()
    visitData = factSheetService.visitDetails(company.companyId, customer.customerId)
    segmentData = SegmentsService.getSegmentsOfCompany(company, customer)
    websites = company.getWebsites()
    joboffers = 1

    technographicsData = factSheetService.technographicsDetails(company.companyId)
    if firmographics is not None:
        companyName = firmographics.companyName
        companyLogo = firmographics.logoUrl
    else:
        companyName = ""
        companyLogo=None

    return render_template('factSheet.html', companyName=companyName, companyLogo=companyLogo,
                           firmographics=firmographics, contactData=contactData, financeData=financeData,
                           linkedinData=linkedinData, visitData=visitData, segmentData=segmentData,
                           sourcesData=sourcesData, technographicsData=technographicsData, websites=websites,
                           joboffers=joboffers)

@app.route('/company/<companyId>/firmographics', methods=['GET'])
def getFirmographicsOfCompany(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    firmographics = CompanyService.getCompanyById(companyId).getFirmographics()
    dataType = request.args.get("dataType")
    if dataType is None or dataType == "json":
        return T1jsonEncoder().encode(firmographics)
    else:
        return render_template('response.html', firmographics=firmographics, name="firmographics")

@app.route('/company/<companyId>/financedata', methods=['GET'])
def getFinanceDataOfCompany(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    financedata = CompanyService.getCompanyById(companyId).getFinanceData()
    dataType = request.args.get("dataType")
    if dataType is None or dataType == "json":
        return T1jsonEncoder().encode(financedata)
    else:
        return render_template('response.html', financedata=financedata, name="financedata")

@app.route('/company/<companyId>/contactdata', methods=['GET'])
def getContactDataOfCompany(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    contactData = CompanyService.getCompanyById(companyId).getContactData()
    dataType = request.args.get("dataType")
    if dataType is None or dataType == "json":
        return T1jsonEncoder().encode(contactData)
    else:
        return render_template('response.html', contactData=contactData, name="contactData")

@app.route('/company/<companyId>/linkedindata', methods=['GET'])
def getLinkedinDataOfCompany(companyId):
    if not session.get('emailId'):
        return redirect(url_for('login'))
    linkedinData = CompanyService.getCompanyById(companyId).getLinkedInData()
    dataType = request.args.get("dataType")
    if dataType is None or dataType == "json":
        return T1jsonEncoder().encode(linkedinData)
    else:
        return render_template('response.html', linkedinData=linkedinData, name="financedata")



@app.route('/filter.js', methods=['GET'])
def getFilterJs():
    if not session.get('emailId'):
        return redirect(url_for('login'))
    attributes = session["segmentationService"].getAttributes()
    return render_template('filter.js', attributes=attributes)

@app.route('/abaConfig')
def abaConfig():
    if not session.get('emailId'):
        return Response("{'error':'Login to use this Service'}", status=403, mimetype='application/json')
    else:
        return render_template("abaConfig.html")


@app.route('/advertise/bindAdvertiser', methods=['GET', 'POST'])
def bindAdvertiser():
    data = AdvertiserServices.bindAdvertiser()
    return data


@app.route('/advertise/crudAdvertise', methods=['GET', 'POST'])
def crudAdvertise():
    operationName = request.form['operationName']
    if operationName == 'add':
        advertiseName = request.form['advertiseName']
        data = AdvertiserServices.addAdvertise(advertiseName)

    elif operationName == 'delete':
        advertiseId = request.form['advertiseId']
        data = AdvertiserServices.deleteAdvertise(advertiseId)

    elif operationName == 'edit':
        advertiseId = request.form['advertiseId']
        data = AdvertiserServices.editAdvertise(advertiseId)

    else:
        advertiseId = request.form['advertiseId']
        advertiseName = request.form['advertiseName']
        data = AdvertiserServices.updateAdvertise(advertiseId, advertiseName)
    return data


@app.route('/campaign/bindCampaign', methods=['GET', 'POST'])
def bindCampaign():
    advertiseId = request.form['advertiseId']
    data = AdvertiserServices.bindCampaign(advertiseId)
    return data


@app.route('/campaign/crudCampaign', methods=['GET', 'POST'])
def crudCampaign():
    operationName = request.form['operationName']
    if operationName == "delete":
        campaignId = request.form['campaignId']
        data = AdvertiserServices.deleteCampaign(campaignId)
    elif operationName == "addCampaignDetails":
        campaignId = request.form['campaignId']
        campaignsName = request.form['campaignsName']
        fromData = request.form['from']
        tillData = request.form['from']
        activeData = request.form['active']
        data = AdvertiserServices.addCampaignDetails(campaignId, campaignsName, fromData, tillData, activeData)
    else:
        advertiseId = request.form['advertiseId']
        campaignName = request.form['campaignName']
        customerId = session['customerId']
        data = AdvertiserServices.campaignAdd(advertiseId, campaignName, customerId)
    return data


@app.route("/campaign/campaignDetails", methods=['POST', 'GET'])
def campaignDetails():
    advertiseId = request.form['advertiseId']
    campaignId = request.form['campaignId']
    data = AdvertiserServices.campaignDetails(advertiseId, campaignId)
    return data


@app.route('/campaign/addTargeting', methods=['POST', 'GET'])
def addTargeting():
    import pandas as pd
    if request.method == 'POST':
        ipAddress = request.form['ip']
        filename = request.files['filename']
        data = pd.read_csv(filename)
        df = pd.DataFrame(data)
        for row in df.itertuples():
            sql = "insert into tbl_csv (ip, company, domain) values(%s,%s,%s)"
            arg = [ipAddress, row.companyName, row.domain]
            db.execute(sql, args=arg, commit=True)
    return render_template('abaConfig.html')


@app.route('/campaign/rangeTargeted', methods=['post', 'get'])
def rangeTargeted():
    campaignId = request.form['campaignId']
    sql = "select count(*) from campaigns where campaignId=%s"
    # sql = "select count(*) from campaignRanges where campaignId=%s"
    arg = [campaignId]
    count = db.execute(sql, args=arg, commit=False)
    return count


@app.route('/test', methods=['post', 'get'])
def test():
    return render_template('test.html')


@app.route('/campaign/advertisingPostContent', methods=['post', 'get'])
def advertisingPostContent():
    file_name1 = request.files.get('file1')
    file_name2 = request.files.get('file2')
    file_name1.save("static/images/" + file_name1.filename)
    file_name2.save("static/images/" + file_name2.filename)
    html1 = request.form.get('html1')
    html2 = request.form.get('html2')
    headline = request.form.get('headline')
    headline2 = request.form.get('headline2')
    textarea = request.form.get('textarea')
    textarea2 = request.form.get('textarea3')
    link = request.form.get('link')
    link2 = request.form.get('link2')
    attribution = request.form.get('attribution')
    attribution2 = request.form.get('attribution2')
    campaignId = request.form.get('campaignId')
    split_url = request.form.get('splitURL')
    split_url2 = request.form.get('splitURL2')
    t3nContent = request.form.get('t3nContent')
    t3nHome = request.form.get('t3nHome')
    data = AdvertiserServices.advertisingPostContent(campaignId, html1, html2, headline,
                                                     headline2, textarea, textarea2, link, link2, attribution,
                                                     attribution2, split_url, split_url2, t3nContent, t3nHome)
    return data


@app.route('/campaign/performance')
def performance():
    data = AdvertiserServices.performance()
    return data


# technographicsService #####################################################
# creating the object of the Technographics class
# technographic = technographicsService.Technographics()


@app.route('/technographic/technographicConfig')
def technographicConfig():
    return render_template("technographicConfig.html")


@app.route('/technographic/getTechnographicsByCustomer')
def getTechnographicsByCustomer():
    response = technographic.getTechnographicsByCustomer(79)
    return response


if __name__ == '__main__':
    app.run(debug=True)

class T1jsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return str(o)

        return o.__dict__