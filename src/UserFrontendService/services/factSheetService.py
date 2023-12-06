from services import DbConfig

db = DbConfig.getDB()

def companyDetails(companyId):

    # company details ###################################
    company_data = db.execute("select * from companies where companyId=%s", [companyId])
    if len(company_data) == 0:
        company_data = '0'
    return company_data


def technographicsDetails(companyId):
    # technographics details #################
    technographhic_data = db.execute("""SELECT site_id, companyId,source,technographics_names.website, city,zip,
                            country, profile_li, profile_tw, profile_fb, profile_xi, profile_ig, profile_yt,
                            profile_tt, profile_twi, technographics_check, lastModifiedOn FROM websites inner join 
                            technographics on websites.site_id=technographics.siteId inner join technographics_names on 
                            technographics.slug = technographics_names.slug where websites.companyId=%s""", [companyId]
                   )
    if len(technographhic_data) == 0:
        technographhic_data = '0'
    return technographhic_data


def visitDetails(companyId, customerId):
    sql = '''select a.visitTime, b.pageUrl, a.durationSec, a.scrollDepth, a.utm_source, a.utm_medium, a.utm_campaign, a.utm_term, a.utm_content, a.gclid, a.referrer, a.parameters
            FROM (SELECT visitTime, durationSec, scrollDepth, visitId, companyId, pageId, customerId, utm_source, utm_medium, utm_campaign, utm_term, utm_content, gclid, referrer, parameters  from `visits` where customerId=%s and companyId=%s and visitTime is not null order by visitTime DESC LIMIT 200) a 
            left JOIN observed_pages b on a.pageId=b.pageId  
            order by visitTime DESC LIMIT 100'''
    values = (customerId, companyId)
    return db.execute(sql, values)



def segmentDetails(companyId):

    segment_data = db.execute("""select segments.name,segments.description, segments.colorCode
                            from segments_companies inner join
                       segments on segments_companies.segmentId=segments.segmentId
                        where segments_companies.companyId=%s""", [companyId])
    if len(segment_data) == 0:
        segment_data = '0'
    return segment_data


def fermographicDetails(companyId):
    data = db.execute("""SELECT companyName, wz2008Code, naicsCode, concat(employees_0,' - ', employees_1)
                        as employee, concat(revenue_0,' - ',revenue_1) as revenue, description,
                     linkedin, twitter, facebook, isISP, companies.manualISP, industry, company_type, exit_data,
                      Linkedin_URL, linkedin_internal_id, extra_ipo_status, extra_crunchbase_rank,extra_founding_date, 
                       extra_operating_status, extra_company_type, extra_contact_email, extra_phone_number,
                       extra_facebook_id, extra_twitter_id, extra_number_of_funding_rounds, extra_total_funding_amount,
                       extra_stock_symbol, extra_ipo_date, extra_number_of_lead_investors, extra_number_of_investors, 
                       extra_total_fund_raised, extra_number_of_investments, extra_number_of_lead_investments,
                        extra_number_of_exits, extra_number_of_acquisitions, follower_count, founded_year,
                        funding_data, tagline, website, company_size_on_linkedin,universal_name_id, search_id,
                        similar_companies
                        FROM `proxycurl` inner join companies on proxycurl.company_ID=companies.companyId
                      where companies.companyId=%s""", [2])
    if len(data) > 0:
        fermographicData = data

    else:
        fermographicData = '0'
    return fermographicData


def getNameAndLogo(companyId):
    data = db.execute("""SELECT companyId, companyName, logoFileExtension FROM `companies` where companyId=%s""",
                   [2])
    if  len(data) > 0:
        companyName = data

    else:
        companyName = '0'
    return companyName
