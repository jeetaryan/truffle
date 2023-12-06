from linkedin_v2 import  client

# LinkedIn API Zugangsdaten
client_id = '78mmp799dp6ddw'
client_secret = 'KeKccmbBLvhGjyU3'
redirect_uri = 'https://login.truffle.one/lirurl'

# Erstellen eines LinkedInApp-Objekts

app = client.LinkedInAuthentication(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri)

# Erhalten der Autorisierungs-URL
auth_url = app.get_authorize_url()

# Leiten Sie den Benutzer zur Autorisierungs-URL weiter
print("auth-URL: ", auth_url)
# Nach der Autorisierung wird der Benutzer zur angegebenen Redirect-URL zurückgeleitet

# Nachdem der Benutzer zur Redirect-URL zurückgeleitet wurde,
# erfassen Sie den Autorisierungscode (authorization code) aus der Query-Parameter der URL

authorization_code = input("Geben Sie den Autorisierungscode ein: ")

# Erhalten des Zugriffstokens
access_token = app.get_access_token(authorization_code)

# Verwenden des Zugriffstokens, um mit der LinkedIn-API zu interagieren
# Führen Sie die gewünschten Aktionen durch, indem Sie die Methoden des app-Objekts aufrufen

# Beispiel: Abrufen von Profildaten des Benutzers
profile_data = app.get_profile()
print("PROFLE DATA")
print(profile_data)

# Kampagnennamen abrufen
campaigns = linkedin_app.get_ad_campaigns()
campaign_names = [campaign['name'] for campaign in campaigns['elements']]
print("Kampagnennamen:")
for name in campaign_names:
    print(name)
