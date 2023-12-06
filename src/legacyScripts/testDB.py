from services import DbConfig

db = DbConfig.DB()

result = db.execute("select * from users")
for r in result:
    print(r[0])