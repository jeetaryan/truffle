import time

import cfscrape 
from services import DbConfig
from bs4 import BeautifulSoup
from datetime import datetime

import traceback

db = DbConfig.getDB()


# customerId 4 is t3n
x = db.execute("select pageId, pageUrl from observed_pages where customerId=%s and rawContent is NULL", (4,))
print("länge", len(x))
for url in x:
    pageId = url[0]
    url = str(url[1])
    print(".")
    title = None
    rawContent = ""

    try:
        cookies = {'t3n_consent': '8'}
        scraper = cfscrape.create_scraper()
        html_page = scraper.get("https://" + url, cookies=cookies)
        print("downloaded")
        soup = BeautifulSoup(html_page.text, "html.parser")
        
        rawContent = ' '.join(soup.get_text().split())
        title = soup.title.get_text() if soup.title.get_text()!="" else None

        values = (title, rawContent, pageId)
        sql = "update observed_pages set pageTitle=%s, rawContent=%s where pageId=%s"
        db.execute(sql, values, True)
    except BaseException as e:
        print("Exception caught:: ", e)
        traceback.print_exc()