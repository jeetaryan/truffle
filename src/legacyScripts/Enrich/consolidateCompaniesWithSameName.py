import mysql.connector
import traceback
import mysql.connector


cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)
cnx2 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor2 = cnx2.cursor(buffered=True)
cnx3 = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor3 = cnx3.cursor(buffered=True)

def deleteCompanyAndVisits(companyId):
    values = (companyId, )
    sql = "DELETE from visits where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_categories where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_specialties where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from ip_ranges where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE t from technographics t "\
    "LEFT JOIN websites w ON t.siteId = w.site_id "\
    "where w.companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companyIpInfo where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from websites where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from addresses where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from kickfire where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from proxycurl where company_ID=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companies where companyId=%s"
    cursor3.execute(sql, values)
    cnx3.commit()

def deleteCompanyWithoutVisits(companyId):
    values = (None, companyId )
    sql = "UPDATE visits set companyId=%s where companyId = %s"
    cursor3.execute(sql, values)

    values = (companyId, )
    sql = "DELETE from companyIpInfo where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_categories where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from linkedin_specialties where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from ip_ranges where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE t from technographics t "\
    "LEFT JOIN websites w ON t.siteId = w.site_id "\
    "where w.companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from websites where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from addresses where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from kickfire where companyId=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from proxycurl where company_ID=%s"
    cursor3.execute(sql, values)
    sql = "DELETE from companies where companyId=%s"
    cursor3.execute(sql, values)
    cnx3.commit()


############################################
# removes kf records without proper values #
############################################
sql = "DELETE FROM kickfire where companyName=website;"
cursor.execute(sql)
cnx.commit()

    


###########################################
# removes companies without KF/PC record) #
###########################################
sql = "SELECT a.companyId from companies a " \
        "WHERE  NOT EXISTS (SELECT * " \
        "                  FROM   kickfire b " \
        "                   WHERE  a.companyId = b.companyId) " \
        "AND NOT EXISTS (SELECT * " \
        "                   FROM   proxycurl c " \
        "                   WHERE  a.companyId = c.company_ID)"

cursor.execute(sql)
companies = cursor.fetchall()

for company in companies:
    companyId = company[0]
    print("deleting companyId: ", str(companyId), "because it is a zombi (without firmopgraphics)." )
    
    deleteCompanyWithoutVisits(companyId)



#################################################
# removes companies without a company name ("") #
#################################################

values = ("",)
sql = "SELECT companyId FROM kickfire where companyName=%s and not exists (SELECT * FROM proxycurl where proxycurl.company_ID=kickfire.companyId)"
cursor.execute(sql, values)
companies = cursor.fetchall()

for company in companies:
    companyId = company[0]
    print("deleting companyId", str(companyId), "because it is a zombi (without a name)." )
    deleteCompanyWithoutVisits(companyId)

values = ("",)
sql = "SELECT company_ID FROM proxycurl where company_name=%s and not exists (SELECT * FROM kickfire where proxycurl.company_ID=kickfire.companyId)"
cursor.execute(sql, values)
companies = cursor.fetchall()
for company in companies:
    companyId = company[0]
    deleteCompanyWithoutVisits(companyId)



########################################################
# removes dublicate companies (with same company Name) #
########################################################



# mehrfache vorkommen der gleichen Firma mit mehreren companyIDs in kickfire konsolidieren:
values=(1,)
sql = "SELECT count(*) as Anzahl, companyId, companyName FROM kickfire group by companyName having count(*)>%s order by Anzahl desc"
cursor.execute(sql, values)
companies = cursor.fetchall()
for company in companies:
    anzahl = company[0]
    companyId = company[1]
    companyName = company[2]
    if anzahl >1:
        print("processing ",  anzahl,  "dublicates of company", companyName, "(", companyId, ")")
        values = (companyName, companyId)
        sql = "SELECT companyId FROM kickfire where companyName=%s and companyId<>%s order by createdOn DESC"
        cursor2.execute(sql, values)
        dublicates = cursor2.fetchall()
        
        for dublicate in dublicates:
            oldCompanyId = dublicate[0]
            print("  removing dublicate: ", oldCompanyId)
            # alle Tabellen updaten, die die companyId referenzieren
            values = (companyId, oldCompanyId)
            sql = "UPDATE visits set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update linkedin_categories set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update linkedin_specialties set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "UPDATE companyIpInfo  set companyId = %s  where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update ip_ranges set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update websites set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update addresses set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            
            values = (companyId, )
            sql= "select * from proxycurl where company_ID=%s"
            cursor3.execute(sql, values)
            rows = cursor3.fetchall()
            if (rows and len(rows)>0):
                values = (oldCompanyId, )
                sql = "delete from proxycurl where company_ID=%s"
                cursor3.execute(sql, values)
            else:
                values = (companyId, oldCompanyId)
                sql = "update proxycurl set company_ID = %s where company_ID=%s"
                cursor3.execute(sql, values)
             # DELETE FROM TABLES
            values = (oldCompanyId, )
            sql = "delete from kickfire where companyId=%s"
            cursor3.execute(sql, values)
            sql = "delete from companies where companyId=%s"
            cursor3.execute(sql, values)    
            cnx3.commit()
values=(1,)
sql = "SELECT count(*) as Anzahl, company_ID, company_name FROM proxycurl group by company_name HAVING COUNT(*) > %s order by Anzahl desc"
cursor.execute(sql, values)
companies = cursor.fetchall()
for company in companies:
    anzahl = company[0]
    companyId = company[1]
    companyName = company[2]
    if anzahl >1:
        print("processing ",  anzahl,  "dublicates of company", companyName, "(", companyId, ")")
        values = (companyName, companyId)
        sql = "SELECT companyId FROM proxycurl where company_name=%s and company_ID<>%s"
        cursor2.execute(sql, values)
        dublicates = cursor2.fetchall()
        
        for dublicate in dublicates:
            oldCompanyId = dublicate[0]
            print("  removing dublicate: ", oldCompanyId)
            # alle Tabellen updaten, die die companyId referenzieren
            values = (companyId, oldCompanyId)
            sql = "UPDATE visits set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update linkedin_categories set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update linkedin_specialties set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "UPDATE companyIpInfo  set companyId = %s  where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update ip_ranges set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update websites set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            sql = "update addresses set companyId = %s where companyId=%s"
            cursor3.execute(sql, values)
            
            values = (companyId, )
            sql= "select * from kickfire where companyId=%s"
            cursor3.execute(sql, values)
            rows = cursor3.fetchall()
            if (rows and len(rows)>0):
                values = (oldCompanyId, )
                sql = "delete from kickfire where companyId=%s"
                cursor3.execute(sql, values)
            else:
                values = (companyId, oldCompanyId)
                sql = "update kickfire set companyId = %s where companyId=%s"
                cursor3.execute(sql, values)
            
             # DELETE FROM TABLES
            values = (oldCompanyId, )
            sql = "delete from proxycurl where company_ID=%s"
            cursor3.execute(sql, values)
            sql = "delete from companies where companyId=%s"
            cursor3.execute(sql, values)    
            cnx3.commit()
            

        
            
            




print("done")
       