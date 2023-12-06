import mysql.connector
import pymongo
# sql connection
# sqlDbCon = mysql.connector.connect(host="localhost", user="root", password="", database="proj_welva")
sqlDbCon = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
sqlConn = sqlDbCon.cursor()
# end

# mongo connection
mongoCon = pymongo.MongoClient("mongodb://welwa-prod-user:NYBVMyfePoDQQBK3@3.68.198.104:27017/myFirstDatabase?authSource=admin&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&directConnection=true&ssl=false")
mongoDB = mongoCon['WelwaMsTriggerNativeScript']
jsData = mongoDB["js_data"]
jsFilteredData = mongoDB["js_filtered_data"]
ripeLookup = mongoDB["ripe_lookup"]
publicIpRecord = mongoDB["public_ip_records"]
# end
