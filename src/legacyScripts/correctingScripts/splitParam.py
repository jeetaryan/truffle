import mysql.connector
from mysql.connector import Error

# connection = mysql.connector.connect(host="localhost", user="root", password="", database="proj_welva")
connection = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = connection.cursor(buffered=True)
try:

    cursor.execute("select pageUrl, pageTitle, visitId from visits where pageUrl is not null")
    print("Data found!!!")
    data = cursor.fetchall()
    pageUrl = ""
    pageTitle = ""
    parametersUrl = ""
    baseUrl = ""
    filterDataCount = 0
    processData = 0
    for x in data:
        filterDataCount += 1
        pageUrl = x[0]
        pageTitle = x[1]
        visitId = x[2]
        if (pageUrl == ""):
            print("No page url found!!!")
        else:
            # update utm_parameters
            special_characters = "?"
            if any(c in special_characters for c in pageUrl):

                url = str(''.join(pageUrl))
                # getting url after removing parameters
                baseUrl = url.split("?")[0]
                # getting protocol
                protocol = baseUrl.split("://")[0]
                # getting url after removing protocol
                splitUrl = baseUrl.split("://")[1]
                # feching pageUrl from observed_pages table
                sql_observedTable_pageUrl = "select pageUrl, pageId from observed_pages where pageUrl=%s"

                values_observedTable = (splitUrl,)
                cursor.execute(sql_observedTable_pageUrl, values_observedTable)
                data = cursor.fetchone()
                count = cursor.rowcount

                if (count > 0):
                    processData += 1
                    print("processed data =", processData)
                    observedTable_url = data[0]
                    observedTable_pageId = data[1]

                    # update parameters and pageId in visit table
                    sql_visits_parameters = "update visits set parameters =%s, pageId=%s where pageUrl=%s"
                    value_parameters = (parametersUrl, observedTable_pageId, splitUrl)
                    cursor.execute(sql_visits_parameters, value_parameters)
                    # end

                    # update observedPages.pageTitle
                    pageTitle = str(''.join(pageTitle))
                    sql_pageTitle = "update observed_pages set pageTitle =%s where pageUrl=%s"
                    value_pageTitle = (pageTitle, splitUrl)
                    cursor.execute(sql_pageTitle, value_pageTitle)
                    # end

                    # updating utm Values into visits table
                    x = parametersUrl.split("&")
                    columns = {"utm_source", "utm_campaign", "utm_term", "utm_context", "utm_medium",
                               "gclid"}
                    for y in x:
                        asd = y.split("=")
                        length = len(asd)
                        if (length > 1):
                            mydic = {asd[0]: asd[1]}
                            for keys, value in mydic.items():
                                for col in columns:
                                    if (col == keys):
                                        sql = "UPDATE visits set " + col + " = '" + value + "' where visitId = %s"
                                        value = (visitId,)
                                        cursor.execute(sql, value)
                                        connection.commit()
                                        print("Record Updated successfully ")  # end
                    # update pageUrl=NULL
                    sql_observedTable_pageUrl_empty = "Update visits set pageUrl=%s, pageTitle=%s where visitId=%s"
                    pageUrl = "NULL"
                    pageTitle = "NULL"
                    values_pageUrl = (pageUrl, pageTitle, visitId)
                    cursor.execute(sql_observedTable_pageUrl_empty, values_pageUrl)
                    connection.commit()
                else:
                    # insert observedPages.pageTitle and url
                    sql = "insert observed_pages(pageUrl ,pageTitle)values(%s,%s)"
                    value = (splitUrl, pageTitle)
                    cursor.execute(sql, value)
                    connection.commit()
                    pageId = cursor.lastrowid
                    sql_update = "Update visits set pageId=%s"
                    value_update = (pageId,)
                    cursor.execute(sql_update, value_update)
                    connection.commit()

                    # end
        print("filter Data Count =", filterDataCount)

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
