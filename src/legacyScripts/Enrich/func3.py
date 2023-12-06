from datetime import date
from time import sleep

import requests
from flask import Flask, render_template
from connection import connect
from selenium import webdriver

# creating connection variable----------------
conn = connect()
cursor = conn.cursor()


# end -------------------------------


# end previousData------------------------


# start getLogo
def getLogo(companyId, domain):
    # setting up chrome path for driver
    driver = webdriver.Chrome('static/doc')
    # end driver path setup

    domain = normalizeDomain()

    if companyId == None or domain == None:
        cursor.execute("update companies set logo=%s where companyId=%s", (None, companyId))
        conn.commit()
    else:
        if domain.startswith(httpsUrl):
            comDomain = domain
        else:
            if domain.startswith(httpUrl):
                comDomain = domain
            else:
                if domain.startswith(wwwUrl):
                    data = preHttp + domain
                    comDomain = data
                else:
                    data = preWww + domain
                    comDomain = data
        api = f"https://api.kickfire.com/logo?website={comDomain}"
        logo = requests.get(api, allow_redirects=True)
        data = logo.headers['content-type']
        data = data.split("/")
        data = data[1]
        svgData = str(data)
        if svgData == 'svg+xml':
            data = svgData.split("+")
            data = data[0]
        else:
            data = data

        if logo.status_code == 200:
            print(companyId, data)

            open(f"static/images/{companyId}.{data}", 'wb').write(logo.content)
            todayDate = date.today()
            cursor.execute(f"update companies set logo=%s where companyId=%s", (todayDate, companyId))
        else:
            cursor.execute(f"update companies set logo=%s where companyId=%s", ('1900-01-01', companyId))
        conn.commit()
    cursor.close()
    conn.close()
    return "true"

# end getLogo
