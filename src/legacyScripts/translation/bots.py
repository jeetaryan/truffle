import mysql.connector

# conn = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
conn = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = conn.cursor()

cursor.execute("select pattern from bots where patternId>160")
patterns = cursor.fetchall()
count = 0

for xPattern in patterns:
    count += 1
    xPatterns = str(''.join(xPattern))
    print("processing ", xPatterns, " pattern ", count, " of ", len(patterns))
    sql = "update visits set status=1, isBot=1 where status=0 and userAgent REGEXP %s"
    values = (xPatterns,)
    cursor.execute(sql, values)
    conn.commit()
print("updating status of remaining records")
cursor.execute("update visits set status=1 where status=0 and isBot=0")
conn.commit()
cursor.close()
conn.close()

print("done")

