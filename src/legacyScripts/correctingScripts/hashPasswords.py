import hashlib

from services import DbConfig

# create db_connection
dbConnection = DbConfig.connection()
cursor = dbConnection.cursor(buffered=True)

cursor.execute("select userId, password from users")
data = cursor.fetchall()
for user in data:
    hash_password = hashlib.md5(user[1].encode("utf-8")).hexdigest()
    print(user[1])
    cursor.execute("UPDATE users set password=%s where userId=%s", (hash_password, user[0]))
    dbConnection.commit()
cursor.close()
dbConnection.close()