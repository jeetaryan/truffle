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

# start getScreenshot
def getScreenshot(companyId, domain):
    # setting up chrome path for driver
    driver = webdriver.Chrome('static/doc')
    # end driver path setup

    httpsUrl = "https://www."
    httpUrl = "http://www."
    wwwUrl = "www."
    preHttp = "http://"
    preWww = "http://www."
    comDomain = ""
    count = 0

    if companyId == None or domain == None:
        cursor.execute("update websites set screenshot='' where companyId=%s", (companyId,))
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
        print("count = ", count, "Domain name = ", comDomain)
        driver.get(comDomain)
        sleep(1)
        # driver.save_screenshot(f'/var/www/login.truffle.one/static/screenshots/{companyId}.png')
        screenShot = driver.save_screenshot(f'static/images/{companyId}.png')
        if screenShot:
            todayDate = date.today()
            cursor.execute(f"update websites set screenshot=%s where companyId=%s", (todayDate, companyId))
        else:
            cursor.execute(f"update websites set screenshot=%s where companyId=%s", ('1900-01-01', companyId))

        conn.commit()
    conn.close()
    cursor.close()
    return "true"


# end getScreenshot

# start getLogo
def getLogo(companyId, domain):
    # setting up chrome path for driver
    driver = webdriver.Chrome('static/doc')
    # end driver path setup

    httpsUrl = "https://www."
    httpUrl = "http://www."
    wwwUrl = "www."
    preHttp = "http://"
    preWww = "http://www."
    comDomain = ""
    count = 0

    if companyId == None or domain == None:
        cursor.execute("update companies set logo='' where companyId=%s", (companyId,))
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
        if logo.status_code == 200:
            print("companyId = ", companyId)
            # driver.save_screenshot(f'/var/www/login.truffle.one/static/companylogos/{companyId}.png')
            open(f"static/images/{companyId}.jpg", 'wb').write(logo.content)
            todayDate = date.today()
            cursor.execute(f"update companies set logo=%s where companyId=%s", (todayDate, companyId))
        else:
            cursor.execute(f"update companies set logo=%s where companyId=%s", ('1900-01-01', companyId))
        conn.commit()
    conn.close()
    cursor.close()
    return "true"

# end getLogo