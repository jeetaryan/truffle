import translation6
import mysql.connector
import traceback





def unifyCompanies():
    sql = "SELECT count(*) as anzahl, companyId, companyName FROM companies kf Group by kf.companyName having anzahl>%s order by anzahl desc;"
    values=(1,)
    cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
    cursor = cnx.cursor(buffered=True)
    cursor.execute(sql, values)
    rows = cursor.fetchall()
    rowNum = len(rows)
    print(str(rowNum) + " companies with dublicates")
    
    for row in rows:
        anzahl = int(row[0])
        companyId = row[1]
        companyName = row[2]
        
        sql = "SELECT companyId from companies where companyName=%s and companyId<>%s order by createdOn DESC"

        values = (companyName, companyId)
        cursor.execute(sql, values)
        dublicates = cursor.fetchall()
        
        anzahl -= 1
        print("", str(anzahl), "dublicates found for", companyName, "(", rowNum, "/", len(rows), ")")
        n=0
        for dublicate in dublicates:
            n+=1
            print("   ", str(n), "/", str(anzahl), ": removing dublicate  of", companyName, ": ", str(companyId))
            dubId = dublicate[0]
            values = (companyId, dubId)
            sql = "UPDATE visits set companyId=%s where companyId=%s"
            cursor.execute(sql, values)
            cnx.commit()
            
            translation6.deleteCompanyWithoutVisits(dubId)
        rowNum -= 1
    cursor.close()
    cnx.close()

    


#updateCompanies()
unifyCompanies()
#translateData(500)