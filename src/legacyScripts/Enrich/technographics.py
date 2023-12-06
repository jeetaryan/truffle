import json
import time
import subprocess
import mysql.connector
from datetime import datetime




def getTechnographics(siteId, website):
	
	sqlDbCon = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
	sqlConn = sqlDbCon.cursor()
	
	website="https://"+ website
	
	print("checking technographics for " + website)
	result = subprocess.run(['wappalyzer', website], stdout=subprocess.PIPE)
	b = json.loads(result.stdout)
	urls = b["urls"]

	for url in urls:
		if "error" in urls[url]:
			print("ERROR with siteId=" + str(siteId) + "(" + website + "): " +urls[url]["error"])
		else:
			techs = b["technologies"]
			for t in techs:
				#introeduce sug if not exist
				values = ( t["slug"], t["name"], t["icon"], t["website"], t["cpe"])
				sql = "INSERT IGNORE into technographics_names(slug, name, icon, website, cpe) values(%s, %s, %s, %s, %s);"
				sqlConn.execute(sql, values)

				#add technographics to website
				values = ( siteId, t["slug"], t["confidence"], t["version"])
				sql = "INSERT into technographics(siteId, slug, confidence, version) values(%s, %s, %s, %s);"
				sqlConn.execute(sql, values)

		now = datetime.now()
		values = (now, siteId)
		sql = "UPDATE websites set technographics_check = %s where site_id = %s"
		sqlConn.execute(sql, values)
		sqlDbCon.commit()
	sqlConn.close()
	sqlDbCon.close()

#getTechnographics(64000, "harman.com")