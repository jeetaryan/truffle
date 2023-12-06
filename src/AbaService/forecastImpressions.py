import mysql.connector


database = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = database.cursor(buffered=True)

#todo remove hardcoding
campaignId=25


cursor.execute('''
    SELECT b.name, b.domain, COUNT(*) FROM `visits`
    inner join (SELECT companyId, name, domain from campaignTargetAccounts where campaignId=%s)
    as b on visits.companyId = b.companyId where lastModifiedOn>"2023-02-15" group by visits.companyId;
    ''', (campaignId, ))

cursor.close()
database.close()


