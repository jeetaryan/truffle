##################################################################
# choose firmographics from kf or pc and stor in companies table #
##################################################################

import mysql.connector
import traceback


cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)
cnx2 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor2 = cnx2.cursor(buffered=True)
cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor3 = cnx3.cursor(buffered=True)

def naics2sic(naics):
    values=(naics, 1)
    sql = "select target from industryCodeConversion where source=%s and type=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    return result[0] if result else None

def sic2naics(sic):
    values=(sic, 2)
    sql = "select target from industryCodeConversion where source=%s and type=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    return result[0] if result else None

def sic2linkedin(sic):
    values=(sic, 3)
    sql = "select target from industryCodeConversion where source=%s and type=%s"
    cursor3.execute(sql, values)
    result = cursor3.fetchone()
    return result[0] if result else None




sql = "SELECT c.companyId, pc.company_name, pc.industry, pc.company_size_0, pc.company_size_1, pc.Linkedin_URL, pc.extra_twitter_id, pc.extra_facebook_id, pc.manualISP, " \
    "kf.companyName, kf.employees_0, kf.employees_1, kf.revenue_0, kf.revenue_1, kf.sicCode, kf.naicsCode, kf.twitter, kf.facebook, kf.linkedin, kf.isISP, kf.manualISP, " \
    "ipi.companyName, ipi.isIsp, w.website, w.profile_li, w.profile_tw, w.profile_fb "\
    "FROM companies c "\
    "left JOIN proxycurl pc on c.companyId=pc.company_ID "\
    "left JOIN kickfire kf on kf.companyId=c.companyId "\
    "left JOIN websites w on w.companyId=c.companyId "\
    "left JOIN companyIpInfo ipi on ipi.companyId=c.companyId "\
    "GROUP BY c.companyId;"
cursor.execute(sql)
companies = cursor.fetchall()

for company in companies:

    companyId = company[0]
    namePC = company[1]
    industryNaicsPC = company[2]
    industrySicPC = naics2sic(company[2])
    empl0PC = company[3]
    empl1PC = company[4]
    linkedinPC = company[5]
    twitterPC = company[6]
    facebookPC = company[7]
    manualIspPC = company[8]
    nameKF = company[9]
    empl0KF = company[10]
    empl1KF = company[11]
    rev0KF = company[12]
    rev1KF = company[13]
    industrySicKF = company[14] if company[14] else naics2sic(company[15])
    industryNaicsKF =  company[15] if company[15] else sic2naics(company[14])
    twitterKF = company[16]
    facebookKF = company[17]
    linkedinKF = company[18]
    ispKF = company[19]
    manualIspKF = company[20]
    nameIPI = company[21]
    ispIpi = company[22]
    website = company[23]
    linkedinWebsite = company[24]
    twitterWebsite = company[25]
    facebookWebsite = company[26]
    
    companyName = namePC if namePC else nameIPI if nameIPI else nameKF
    wz2008Code = industrySicKF if industrySicKF else industrySicPC
    naicsCode = industryNaicsKF if industryNaicsKF else industryNaicsPC
    employees_0 = empl0PC if empl0PC else empl0KF
    employees_1 = empl1PC if empl1PC else empl1KF
    revenue_0 = rev0KF
    revenue_1 = rev1KF
    linkedin = linkedinPC if linkedinPC else linkedinKF if linkedinKF else linkedinWebsite
    twitter = twitterPC if twitterKF else twitterPC if twitterPC else twitterWebsite
    facebook = facebookPC if facebookPC else facebookKF if facebookKF else facebookWebsite
    isISP = ispIpi if ispIpi else ispKF if ispKF else 0
    manualISP = manualIspKF if manualIspKF else manualIspPC if manualIspPC else 0
    
    print("processing:", companyName, "(", str(companyId), ")" )
        
    values = (companyName, wz2008Code, naicsCode, employees_0, employees_1, revenue_0, revenue_1, linkedin, twitter, facebook, isISP, manualISP, companyId)
    sql = "UPDATE companies set companyName=%s, wz2008Code=%s, naicsCode=%s, employees_0=%s, employees_1=%s, revenue_0=%s, revenue_1=%s, linkedin=%s, twitter=%s, facebook=%s, isISP=%s, manualISP=%s where companyId=%s"
    cursor2.execute(sql, values)
    cnx2.commit()
