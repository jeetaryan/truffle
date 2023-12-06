import mysql.connector
import traceback
import csv
conn = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cur = conn.cursor(buffered=True)

customerIds=[69]

for customerId in customerIds:
    print("")
    print("------------------------------------------")
    print("customer ID: ", customerId)
    print("------------------------------------------")

    print("counting total number of visits...")
    values = (customerId, )
    sql = "SELECT count(*) from visits where customerId=%s"
    cur.execute(sql, values)
    row = cur.fetchone()
    total=row[0]
    print("Visits: ", total)

    # visits von Bots
    print("counting number of visits by Bots...")
    values = (customerId, 1)
    sql = "SELECT count(*) from visits where customerId=%s and isBot=%s"
    cur.execute(sql, values)
    row = cur.fetchone()
    bots=row[0]
    print("Visits von Bots: ", bots, " (", bots*100/total, "% of all visits)")

    # mobile vs desktop
    print("counting number of visits by mobiles...")
    values = (1, 0, customerId)
    sql = "SELECT count(*) From visits WHERE isMobile=%s and isBot=%s and customerId=%s"
    cur.execute(sql, values)
    row = cur.fetchone()
    mobile=row[0]
    print("Visits von mobile: ", mobile, " (", mobile*100/(total-bots), "% of all human visits)")


    # visits von ISPs (sofern wir es wissen)
    print("counting number of visits by ISPs...")
    values = (1,1,0,customerId )
    sql = "SELECT count(*) From visits WHERE EXISTS (SELECT companyId from kickfire where visits.companyId=kickfire.companyId and (manualISP=%s or isISP=%s)) and isBot=%s and customerId=%s"
    cur.execute(sql, values)
    row = cur.fetchone()
    isps=row[0]
    print("Visits von ISPs: ", isps, " (", isps*100/total, "%)")

    identified=total-bots-isps
    print("Visits von erkannten Unternehmen: ", identified, " (", identified*100/(total-bots), "% of all human visits)")



###############################################################

    print("generating reports for identified companies:")
    counter=0
    values = (0, customerId, 0,0 )
    sql = "SELECT COUNT(*) TotalCount, a.companyId, b.companyId, b.companyName, b.revenue_0, b.revenue_1, b.employees_0, b.employees_1, b.sicCode, b.sicGroup, b.sicDesc, b.isISP, b.manualISP, " \
          "c.company_ID, c.company_name, c.company_size_0, c.company_size_1, c.industry " \
          "FROM (SELECT companyId from visits WHERE isBot=%s and customerId=%s ) as a " \
          "LEFT JOIN (SELECT companyId, companyName, revenue_0, revenue_1, employees_0, employees_1, sicCode, sicGroup, sicDesc, isISP, manualISP from kickfire WHERE manualISP=%s and isISP=%s ) as b ON a.companyId = b.companyId " \
          "LEFT JOIN proxycurl c ON a.companyId = c.company_ID GROUP BY a.companyId;"

    cur.execute(sql, values)
    data = cur.fetchall()

    # Create the csv file
    filename = "companies_" + str(customerId) + ".csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['Visits', 'ID', 'ID_KF', 'Name-KF', 'Umsatz Untergrenze', 'Umsatz Obergrenze', 'Mitarbeiter Untergrenze', 'Mitarbeiter Obergrenze', "Branchencode", "Branchengruppe", "Branche", "ISP", "manualISP", 
                  'ID-PC', 'Name', 'Mitarbeiter Untergrenze', 'Mitarbeiter Obergrenze', "Branche"]
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            counter +=1
            writer.writerow(row)
            #print(row[0], row[1], row[2], row[3])
    print("")
    print("Erkannte Unternehmen: ", counter)
    
    
    
    







######################## ALT #######################################


    print("")
    print("generating referrers without utm and gclid report")
    #utm
    values = (customerId, 0 )
    sql = "SELECT COUNT(*) total, parameters, referrer FROM visits where customerId=%s and isBot=%s and utm_source is null and gclid is null  GROUP BY referrer"

    cur.execute(sql, values)
    data = cur.fetchall()

    # Create the csv file
    filename = "companies_" + str(customerId) + "_referrers.csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['total', 'parameters', 'referrer']
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            writer.writerow(row)
            #print(row[0], row[1], row[2], row[3])
    print("")



######################## ALT #######################################
    print("")
    print("generating utm_parameters report")
    #utm
    values = (customerId, 0 )
    sql = "SELECT COUNT(*) total, utm_source, utm_medium, utm_campaign FROM visits where customerId=%s and isBot=%s GROUP BY CONCAT(visits.utm_source, visits.utm_medium, visits.utm_campaign)"

    cur.execute(sql, values)
    data = cur.fetchall()

    # Create the csv file
    filename = "companies_" + str(customerId) + "_utm_alt.csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['total', 'utm_source', 'utm_medium', 'utm_campaign']
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            writer.writerow(row)
            #print(row[0], row[1], row[2], row[3])
    print("")







######################## ALT #######################################



    print("generating utm_parameters report from kickfire")
    #utm_source und isISP/ManualISP aus kickfire
    values = (customerId, 0 )
    sql = "SELECT COUNT(*) total, visits.utm_source, visits.utm_medium, visits.utm_campaign, CASE WHEN kickfire.isISP OR kickfire.manualISP THEN 1 ELSE 0 END AS ISP FROM visits INNER JOIN kickfire on visits.companyId=kickfire.companyId where customerId=%s and isBot=%s GROUP BY CONCAT(visits.utm_source, visits.utm_medium, visits.utm_campaign, '_', ISP) order by total DESC;"

    cur.execute(sql, values)
    data = cur.fetchall()

    # Create the csv file
    filename = "companies_" + str(customerId) + "_utm_A.csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['total', 'utm_source', 'utm_medium', 'utm_campaign', "ISP"]
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            writer.writerow(row)
            #print(row[0], row[1], row[2], row[3], row[4])
    print("")



######################## ALT #######################################


    print("generating utm_parameters report from proxycurl")

    #utm_source und isISP/ManualISP aus proxycurl
    values = (customerId, 0)
    sql = "SELECT COUNT(*) total, visits.utm_source, visits.utm_medium, visits.utm_campaign, proxycurl.manualISP as ISP FROM visits INNER JOIN proxycurl on visits.companyId=proxycurl.company_ID where customerId=%s and isBot=%s GROUP BY CONCAT(visits.utm_source, visits.utm_medium, visits.utm_campaign, '_', ISP) order by total DESC;"

    cur.execute(sql, values)
    data = cur.fetchall()

    # Create the csv file
    filename = "companies_" + str(customerId) + "_utm_B.csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['total', 'utm_source', 'utm_medium', 'utm_campaign', "ISP"]
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            writer.writerow(row)
            #print(row[0], row[1], row[2], row[3], row[4])
    print("")





######################## NEU #######################################

    print("generating Sources report...")
    #utm-parameter
    counter=0
    values = (0, customerId)
    sql = "SELECT visits.utm_source, visits.utm_medium, visits.utm_campaign, '', '', "\
          "CASE WHEN kickfire.isISP OR kickfire.manualISP OR proxycurl.manualISP THEN 1 ELSE 0 END AS ISP, "\
          "COUNT(*), " \
          "FROM visits "\
          "LEFT JOIN kickfire b ON visits.companyId = b.companyId "\
          "LEFT JOIN proxycurl c ON visits.companyId = c.company_ID "\
          "WHERE isBot=%s and customerId=%s and utm_source is not null"\
          "GROUP BY visits.utm_source, visits.utm_medium, visits.utm_campaign, ISP"

    cur.execute(sql, values)
    utmdata = cur.fetchall()

    # gclid-parameter
    values = (0, customerId)
    sql = "SELECT '', '', '', 'gclid', '', "\
          "CASE WHEN kickfire.isISP OR kickfire.manualISP OR proxycurl.manualISP THEN 1 ELSE 0 END AS ISP, "\
          "COUNT(*), " \
          "FROM visits "\
          "LEFT JOIN kickfire b ON visits.companyId = b.companyId "\
          "LEFT JOIN proxycurl c ON visits.companyId = c.company_ID "\
          "WHERE isBot=%s and customerId=%s and utm_source is null and gclid is not null"\
          "GROUP BY ISP"
    cur.execute(sql, values)
    gcliddata = cur.fetchall()
    
    # referrer for the remainder
    values = (0, customerId)
    sql = "SELECT '', '', '', '', referrer, "\
          "CASE WHEN kickfire.isISP OR kickfire.manualISP OR proxycurl.manualISP THEN 1 ELSE 0 END AS ISP, "\
          "COUNT(*), " \
          "FROM visits "\
          "LEFT JOIN kickfire b ON visits.companyId = b.companyId "\
          "LEFT JOIN proxycurl c ON visits.companyId = c.company_ID "\
          "WHERE isBot=%s and customerId=%s and utm_source is null and gclid is null"\
          "GROUP BY referrer, ISP"
    cur.execute(sql, values)
    referrerdata = cur.fetchall()



    # Create the csv file
    filename = "companies_" + str(customerId) + "_utm_neu.csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['utm_source', 'utm_medium', 'utm_campaign', "gclid", "Referrer", "ISP", 'total']
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in utmdata:
            writer.writerow(row)
        for row in gcliddata:
            writer.writerow(row)
        for row in referrerdata:
            writer.writerow(row)

    print("Sources Report done.")



###############################################################

    print("")
    print("generating parameters report")
    #utm
    values = (customerId, 0 )
    sql = "SELECT COUNT(*) total, parameters, gclid, referrer FROM visits where customerId=%s and isBot=%s and utm_source is null GROUP BY parameters"

    cur.execute(sql, values)
    data = cur.fetchall()

    # Create the csv file
    filename = "companies_" + str(customerId) + "_parameters.csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['total', 'parameters', 'gclid', 'referrer']
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            writer.writerow(row)
            #print(row[0], row[1], row[2], row[3])
    print("")


###############################################################

    print("creating languages report...")
    values = (0, customerId)
    sql = "SELECT count(*), langId, language From visits WHERE isBot=%s and customerId=%s group by langId"
    cur.execute(sql, values)
    data = cur.fetchall()
    
    # Create the csv file
    filename = "languages_" + str(customerId) + ".csv"
    with open(filename, 'w', newline='') as f_handle:
        writer = csv.writer(f_handle)
        # Add the header/column names
        header = ['total', 'langId', 'language']
        writer.writerow(header)
        # Iterate over `data`  and  write to the csv file
        for row in data:
            writer.writerow(row)
            print(row[0], row[1], row[2])
    print("")
cur.close()
conn.close()