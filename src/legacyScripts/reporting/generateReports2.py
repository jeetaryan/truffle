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


######################## NEU #######################################

    print("generating Sources report...")
    #utm-parameter
    counter=0
    values = (0, customerId)
    sql = "SELECT visits.utm_source, visits.utm_medium, visits.utm_campaign, '', '', "\
          "CASE WHEN b.isISP OR b.manualISP OR c.manualISP THEN 1 ELSE 0 END AS ISP, "\
          "COUNT(*) " \
          "FROM visits "\
          "LEFT JOIN kickfire b ON visits.companyId = b.companyId "\
          "LEFT JOIN proxycurl c ON visits.companyId = c.company_ID "\
          "WHERE isBot=%s and customerId=%s and utm_source is not null "\
          "GROUP BY visits.utm_source, visits.utm_medium, visits.utm_campaign, ISP"

    cur.execute(sql, values)
    utmdata = cur.fetchall()

    # gclid-parameter
    values = (0, customerId)
    sql = "SELECT '', '', '', 'gclid', '', "\
          "CASE WHEN b.isISP OR b.manualISP OR c.manualISP THEN 1 ELSE 0 END AS ISP, "\
          "COUNT(*) " \
          "FROM visits "\
          "LEFT JOIN kickfire b ON visits.companyId = b.companyId "\
          "LEFT JOIN proxycurl c ON visits.companyId = c.company_ID "\
          "WHERE isBot=%s and customerId=%s and utm_source is null and gclid is not null "\
          "GROUP BY ISP"
    cur.execute(sql, values)
    gcliddata = cur.fetchall()
    
    # referrer for the remainder
    values = (0, customerId)
    sql = "SELECT '', '', '', '', referrer, "\
          "CASE WHEN b.isISP OR b.manualISP OR c.manualISP THEN 1 ELSE 0 END AS ISP, "\
          "COUNT(*) " \
          "FROM visits "\
          "LEFT JOIN kickfire b ON visits.companyId = b.companyId "\
          "LEFT JOIN proxycurl c ON visits.companyId = c.company_ID "\
          "WHERE isBot=%s and customerId=%s and utm_source is null and gclid is null "\
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


cur.close()
conn.close()