from flask import jsonify, render_template
import datetime as dt
from flask_mail import Message
from services import  ContentScoreService, WebsiteService, CustomerService, CompanyService, DbConfig

db = DbConfig.getDB()


def dashboard(customerId):

    # TODO: preload just latest records like first SQL. Then load large bulk (secod sql) via AJAX.

#i.labelDe
    sql = '''
        SELECT c.companyName, cc.lastModifiedOn, c.wz2008code, pc.industry, c.employees_0, c.employees_1, c.revenue_0, c.revenue_1, 
        c.logoFileExtension, cc.companyId, w.screenshot, w.site_id, w.website, contacts.contactCount, cc.customerId, i.labelLinkedin
        FROM (SELECT customerId, companyId, lastModifiedOn from companies_customers where customerId=%s) cc
        left JOIN (select * from companies where isISP=0 and manualISP=0) c on cc.companyId = c.companyId
        left join (SELECT labelLinkedin, naicsCode from industryCodesNaics) as i on c.naicsCode=i.naicsCode 
        left JOIN (select companyId, screenshot, website, site_id from (select distinct * from `websites` order by screenshot desc) as ws group by companyId) as w on cc.companyId = w.companyId  
        left join (select companyId, count(companyId) as contactCount from contacts where customerId=%s group by companyId) as contacts on contacts.companyId = cc.companyId 
        left join (select company_ID, industry from proxycurl) as pc on pc.company_ID = cc.companyId 
        where c.companyName is not null 
        ORDER BY lastModifiedOn desc
        LIMIT 10000;'''
    values = (customerId, customerId)
    data = db.execute(sql, values)
    return data


def visitDetails(companyId, customerId):
    sql = '''select a.visitTime, b.pageUrl, a.durationSec, a.scrollDepth, a.utm_source, a.utm_medium, a.utm_campaign, a.utm_term, a.utm_content, a.gclid, a.referrer, a.parameters
            FROM (SELECT visitTime, durationSec, scrollDepth, visitId, companyId, pageId, customerId, utm_source, utm_medium, utm_campaign, utm_term, utm_content, gclid, referrer, parameters  from `visits` where customerId=%s and companyId=%s and visitTime is not null order by visitTime DESC LIMIT 200) a 
            left JOIN observed_pages b on a.pageId=b.pageId  
            order by visitTime DESC LIMIT 100'''
    values = (customerId, companyId)
    data = db.execute(sql, values)
    return jsonify(
        {'htmlresponse': render_template('response.html', data=data, companyId=companyId, name="visit_details")})


def contactDetails(companyId, customerId):
    data = db.execute(
        '''select c.firstName, c.lastName, c.gender, c.position, c.phone, e.emailAddress, c.linkedinProfile,
        c.twitterProfile, a.line_1, a.city, a.country, a.postal_code from contacts c
        left join email_addresses e on c.primaryEmailId = e.emailId
        left join addresses a on c.primaryAddressId=a.address_id
        where c.companyId=%s and c.customerId=%s''',
        (companyId, customerId))

    contact_data = db.execute("select contactId from contacts where customerId=%s and companyId=%s", (customerId, companyId))

    emailaddresses = []
    for contact in contact_data:
        emailaddressesOfThisContactList = []
        contactId = contact[0]
        emailaddressesOfThisContact = db.execute("select emailAddress from email_addresses where contactId=%s", (contactId,))
        for email in emailaddressesOfThisContact:
            emailaddressesOfThisContactList.append(email[0])
        emailaddresses.append(emailaddressesOfThisContactList)
    # print("email addressses of all contatacts =", emailaddresses)
    return jsonify(
        {'htmlresponse': render_template('response.html', data=data, companyId=companyId, name="contact_details",
                                         email="emails", email_count=0)})


def track_mail(track_code, privacy, mail, email_id):
    msg = Message(
        'Information zur Einbindung von truffle.one in Ihre Website',
        sender=('Truffle.one', 'info@truffle.one'),
        recipients=['receiver', email_id]
    )
    track = track_code.replace("<", "&lt;")
    track = track.replace(">", "&gt;")
    msg.body = '<h3>Tracking code:</h3><html><body>' + track + '</body></html><h3>Datenschutzhinweis:</h3> ' + privacy
    mail.send(msg)
    return "mail sent"


def contentScore(customer_id, company_id):
    company = CompanyService.getCompanyById(company_id)
    websites = WebsiteService.getWebsitesOfCompany(company)
    result = []
    for w in websites:
        css = ContentScoreService.getContentScoresForWebsite(w, None, websites)

        for cs in css:
            #print(cs)
            cs.score(w)
        result.append(css)


    return jsonify(
        {'htmlresponse': render_template('response.html', data=result, companyId=company_id, name="contactScore")})


def profile(email):
    data = db.execute("select firstname, lastName, gender, language from users where email=%s", (email,))
    if len(data) > 0:
        data_list = [data[0][0], data[0][1], data[0][2], data[0][3]]
        return data_list
    else:
        return "0"


def updateProfile(profile_list):
    db.execute("update users set firstName=%s, lastname=%s, gender=%s, language=%s where email=%s",
                   (profile_list[0], profile_list[1], profile_list[2], profile_list[3], profile_list[4]), True)
    return ""
