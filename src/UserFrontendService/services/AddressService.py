import urllib.parse
import requests
import traceback
import mysql.connector
from services.StringHelper import *
from services import DbConfig


db = DbConfig.getDB()

def getLatLon(street, city, postalcode, state, country):
    # print("     - get LAT/LON for ", street, postalcode, city, state, country)
    try:
        params = {"format": "json", "limit": "1", "addressdetails": "1"}
        if street: params["street"] = street
        if city: params["city"] = city
        if country: params["country"] = country
        if postalcode: params["postalcode"] = postalcode
        if state: params["state"] = state
        url = "https://nominatim.openstreetmap.org/?" + urllib.parse.urlencode(params)
        response = requests.get(url, timeout=3).json()
        if (len(response) == 0):
            print("     - no lat/lon found for", street, postalcode, city, state, country)
            return None
        else:
            print("     - geocoded lat:", float(response[0]["lat"]), "lon:", float(response[0]["lon"]))
            return float(response[0]["lat"]), float(response[0]["lon"])
    except BaseException as e:
        print("Exception caught while geocoding: ", e)
        traceback.print_exc()
        return None


def insertAddress(companyId, line_1, line_2, postal_code, city, country, country_short, state, state_short, is_hq, lat,
                  lon):
    print("     - inserting address ", line_1, postal_code, city, "for companyId", companyId)
    if (lat == 0 or lon == 0 or lat == '' or lon == '' or lat == None or lon == None):
        # get lat/lon if not provided
        latlon = getLatLon(line_1, city, postal_code, state, country)
        if latlon:
            lat = latlon[0]
            lon = latlon[1]
        else:
            lat = None
            lon = None

    try:
        ##############################################
        # todo: first check for dublicates!
        ##############################################
        isHQ = 1 if cln(is_hq) == "True" else 0
        address_value = (
        companyId, cln(line_1), cln(line_2), cln(postal_code), cln(city), cln(country), cln(country_short), cln(state),
        cln(state_short), isHQ, lat, lon)
        address_sql = "INSERT into addresses (companyId, line_1, line_2, postal_code, city, country, countryShort, state, stateShort, is_hq, latitude, longitude) " \
                      "values(%s,%s,%s, %s,%s,%s, %s,%s,%s,%s,%s, %s)"
        db.execute(address_sql, address_value, True)
        return 1
    except BaseException as e:
        print("Exception caught while inserting address into DB: ", e)
        traceback.print_exc()
        return 0
