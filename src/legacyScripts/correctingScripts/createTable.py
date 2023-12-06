import connection

# creating compnies
connection.sqlConn.execute(
    "create table if not exists companies(companyId bigint primary key AUTO_INCREMENT, created_on datetime)")
# end

# creating table named tag
connection.sqlConn.execute("create table if not exists observed_pages(pageId int primary key AUTO_INCREMENT,"
                           "pageUrl text, pageTitle text, rawContent text)")
# end

# creating tags table
connection.sqlConn.execute("create table if not exists tags(tagId int primary key AUTO_INCREMENT,"
                           " tag char(255))")
# end

# creating table named tag
connection.sqlConn.execute("CREATE TABLE IF NOT EXISTS kickfire(companyId bigint, foreign  key(companyId) references companies(companyId),"
                           "companyName char(255),publicIpRecord char(50), tradeName char(255), website char(50), street char(255),"
                           "city char(50), regionShort char(10), region char(20), postal char(20),"
                           " countryShort char(50), country char(50), phone char(15), latitude char(20), "
                           "longitude char(20), employees char(30), revenue char(50), sicGroup char(50),"
                           "sicDesc char(50), sicCode char(50), naicsGroup char(50), naicsDesc char(50), "
                           "naicsCode char(50), stockSymbol char(50), facebook char(50), twitter char(50), linkedin char(50),"
                           " timeZoneId char(50), timeZoneName char(100), utcOffset char(50), dstOffset char(50),"
                           "isISP int, isWifi int)")
# end

# creating table named visits
connection.sqlConn.execute(
    "CREATE TABLE IF NOT EXISTS visits (visitId int primary key AUTO_INCREMENT, companyId bigint,"
    "FOREIGN KEY(companyId) REFERENCES companies(companyId),"
    "ipAddress char (20), client_domain_key CHAR(50), client_domain_name char(50), timestamp text,"
    " browser char(30), device char(30), platform char(30), protocol char(30), visitorId char(20),winHeight char(30),"
    " winWidth char(30), user_org_id char(30),"
    " referrer char(255),parameters text, utm_source text, utm_medium text, utm_campaign text, utm_term text, utm_content text,"
    "gclid text,pageVisitorId char(20), pageVisit char(20),pageId int,FOREIGN KEY(pageId) REFERENCES observed_pages(pageId),"
    " pageUrl varchar(1000), pageTitle varchar(1000), pageLastModifiedDateTime char(20), createdOn timestamp )")
# end

# creating table named Ip_range
connection.sqlConn.execute("create table if not exists ip_ranges(rangeId int primary key AUTO_INCREMENT, "
                           "companyId bigint, FOREIGN KEY(companyId) REFERENCES companies(companyId), ipRange char(50), "
                           "ipStart bigint, ipEnd bigint, publicIpRecord char(100), rangeOrg char(50),"
                           " rangeDescription varchar(5000), rangeNetname char(255),"
                           "rangeEmailDomain char(100), rangeAddress char(255), createdDateTime timestamp,"
                           "lastModifiedDateTime datetime, active int,deleted int, _class char(150), cidr char(20),"
                           "name char(30), handle char(30), address char(255), emails char(150), country char(30),"
                           "state char(30), city char(30), postal_code char(30), timestamp datetime default current_timestamp )")
# end

# creating observed_pages table
connection.sqlConn.execute(
    "create table if not exists tags_observed_pages(tagObservedId int primary key AUTO_INCREMENT,"
    "pageId int, FOREIGN KEY (pageId) REFERENCES observed_pages(pageId),"
    "tagId int, FOREIGN KEY(tagId) REFERENCES tags(tagId) )")
# end

# creting linkedid_categories table
connection.sqlConn.execute("create table if not exists linkedin_categories(id int primary key AUTO_INCREMENT,"
                           "companyId bigint, FOREIGN KEY (companyId) REFERENCES companies(companyId),"
                           "category varchar (500))")
# end

# creting proxycurl table
connection.sqlConn.execute(
    "create table if not exists proxycurl(company_ID bigint, FOREIGN KEY (company_ID) REFERENCES companies(companyId),"
    "acquisitions char(100),company_size_0 char(13),company_size_1 char(13), company_type char(50), description text,exit_data char(50),"
    "Linkedin_URL varchar (500),full_info json,linkedin_internal_id char(50),"
    "extra_ipo_status varchar(500),extra_crunchbase_rank varchar(500),extra_founding_date varchar(500),"
    "extra_operating_status char(50),extra_company_type char(50), extra_contact_email char(50), extra_phone_number char(50),"
    "extra_facebook_id char(50),extra_twitter_id char(50), extra_number_of_funding_rounds char(50), extra_total_funding_amount char(50),"
    "extra_stock_symbol char(50),extra_ipo_date char(50),extra_number_of_lead_investors char(50),"
    "extra_number_of_investors char(50), extra_total_fund_raised char(50), extra_number_of_investments char(50),"
    "extra_number_of_lead_investments char(50), extra_number_of_exits char(50),extra_number_of_acquisitions char(50),"
    "follower_count char(50),founded_year char(50), funding_data char(100),tagline text, locations text,"
    "website varchar(500),industry char(100),company_size_on_linkedin char(50),"
    " company_name char(100),universal_name_id char(100),search_id char(50),similar_companies text, updates char(50))")
# end

# creating Linkedin_Specialties table
connection.sqlConn.execute("create table if not exists linkedin_specialties(id int primary key AUTO_INCREMENT,"
                           "companyId bigint, FOREIGN KEY (companyId) REFERENCES companies(companyId),"
                           "specialities text)")
# end

# creting websites table
connection.sqlConn.execute("create table if not exists websites(site_id int primary key AUTO_INCREMENT,"
                           "companyId bigint, FOREIGN KEY (companyId) REFERENCES companies(companyId),"
                           "website varchar (200))")
# end

# creating addresses table
connection.sqlConn.execute(
    "create table if not exists addresses(companyId bigint, FOREIGN KEY (companyId) REFERENCES companies(companyId),"
    "line_1 varchar(100),line_2 varchar(100),postal_code char(50),city char(50),country char(50),states char(50),is_hq char(50))")
# end

print("Table created successfully!!!")
