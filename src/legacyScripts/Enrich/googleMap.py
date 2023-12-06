import time
import mysql.connector
# import urllib.request
import uuid
import requests

# creating connection
# cnx = mysql.connector.connect(host="localhost", user="root", password="", database="truffle")
cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor()
# end

# start  getting data from truffle.address

cursor.execute("select distinct latitude, longitude from addresses where latitude is not null and longitude is not null and file_name is null")
for latlong in cursor.fetchall():
    unique_filename = str(uuid.uuid4())
    latitude = latlong[0]
    longitude = latlong[1]

    # end getting data from truffle.address

    file_name = f"satellite{unique_filename}"
    imgUrl = f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&lable=true&zoom=18&scale=2&size=640x640&maptype=satellite&key=AIzaSyDcLGFnye5ZuQewUl6XY-VavlR193glq3Y&scale=2Y"
    # for local use----------------------------
    # urllib.request.urlretrieve(imgUrl, f"E:/Projects/truffle/images/{file_name}.jpg")
    # end-------------------------------
    r = requests.get(imgUrl, allow_redirects=True)
    # open(f"E:/Projects/truffle/images/{file_name}.jpg", 'wb').write(r.content)
    open(f"/home/debian/python_script/satPic/{file_name}.jpg", 'wb').write(r.content)

    # set time interval
    time.sleep(2)
    # inset data into table addresses
    sql = "update addresses set file_name=%s where latitude=%s and longitude=%s"
    values = (file_name, latitude, longitude)
    cursor.execute(sql, values)
    cnx.commit()
    print("Latitude = ", latitude, "Longitude = ", longitude, " Image downloaded.")

    # end
