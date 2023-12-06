# Import module
from geopy.geocoders import Nominatim
import mysql.connector

# creating connection
# cnx = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor()
# end

# getting address from table addresses
count = 0
cursor.execute(
    "select distinct latitude, longitude from addresses where latitude is not null and longitude is not null and city is null and country is null")
for address in cursor.fetchall():
    latitude = str(address[0])
    longitude = str(address[1])

    # Initialize Nominatim API
    geolocator = Nominatim(user_agent="geoapiExercises")
    print(latitude, " : ", longitude)
    # Get location with geocode
    location = geolocator.geocode(latitude + "," + longitude)

    # converting location into list----------------------------
    address = list(location)
    # end-------------------------------------------------

    # converting list to string---------------------------------
    address = str(location)
    # end-------------------------------------------------
    string = address.split(',')
    line_1 = string[2] + string[1]
    city = string[3]
    state = string[5]
    postal = string[6]
    country = string[7]
    sql = "update addresses set line_1=%s, city=%s, states=%s,postal_code=%s, country=%s where latitude=%s and longitude=%s"
    values = (line_1, city, state, postal, country, latitude, longitude)
    cursor.execute(sql, values)
    cnx.commit()
    print("Address updated with address.")
