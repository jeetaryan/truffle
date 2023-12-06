import requests
import mysql.connector

# creating connection
# cnx = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor()
# end

# getting address from table addresses
count = 0
cursor.execute(
    "select address_id, line_1, postal_code, city, country from addresses where (latitude is null OR latitude=0) and (longitude is null OR longitude=0) and city is not null and country is not null")
for address in cursor.fetchall():
    count += 1
    address_id = address[0]
    line1 = address[1]
    postal_code = address[2]
    city = address[3]
    country = address[4]
    url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + city + "+" + country + "&format=json&limit=1"
    response = requests.get(url).json()
    length = len(response)
    if (length == 0):
        print("no latitude found")
    else:
        latitude = response[0]["lat"]
        longitude = response[0]["lon"]
        sql = "update addresses set latitude=%s, longitude=%s where address_id=%s"
        values = (latitude,longitude,address_id)
        cursor.execute(sql, values)
        cnx.commit()
        print("Converted number of address = ", count)
