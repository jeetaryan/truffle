import hashlib

from flask import url_for
from flask_mail import Message
import random
from services import DbConfig, ContactsService

# create db_connection
db = DbConfig.getDB()



def authenticateUser(username, password):
    hash_password = hashlib.md5(password.encode("utf-8")).hexdigest()
    data = db.execute(
        "select userId, email, customerId, firstName, lastName, gender, language from users where email=%s and password=%s and status=%s",
        (username, hash_password, 1))
    if data is not None and len(data)>0:
        return User(data[0][0], data[0][1], data[0][2], data[0][3], data[0][4], data[0][5], data[0][6])
    else:
        return None


def register(email, mail, token):
    c = db.execute("select * from users where email=%s and status=1", (email,))
    if len(c) > 0:
        return {'msg': 'Diese Email-Adresse ist bereits registriert'}
    else:
        verification_code = random.randint(10000, 100000)
        msg = Message(
            'Noch ein Klick für Account Based Marketing',
            sender=('Truffle.one', 'info@truffle.one'),
            recipients=['receiver', email]
        )
        link = url_for('verify', token=token, otp=verification_code, _external=True, max_age=36000)
        msg.html = '''<h5>Bitte bestätigen Sie Ihre Registrierung, indem Sie auf den folgenden Link klicken:</h5><br>''' '<a href=' + link + '>' + link + '</a>'
        mail.send(msg)

        customerId = db.execute("insert into customer() values()", None, True)

        db.execute('''Insert into users (email,status,verification_code, customerId) values(%s,%s,%s,%s)
                   ON duplicate Key update verification_code=%s
                   ''', (email, 0, verification_code, customerId, verification_code), True)

        msg = 'Bitte bestätigen Sie die Email, die wir Ihnen gesendet haben.'
        return {'msg': msg, 'email': email}


def verify(email, otp):
    m = db.execute("select * from users where email=%s and verification_code=%s", (email, otp))
    if len(m) > 0:
        data = 1
        # commented out because Looking up contact Details does not work properly
        #data = ContactsService.lookupContactDetailsFromProxyCurl(email)
    else:
        data = 0
    return data


def savePassword(f_name, l_name, gender, company_name, email, password):

    customer_id = db.execute("select customerId from users where email=%s", [email])[0]

    if customer_id is not None:
        db.execute("update customer set customerName=%s where customerId=%s", (company_name, customer_id[0]), True)

    # Hashing the password
    hash_password = hashlib.md5(password.encode("utf-8")).hexdigest()
    dbid= db.execute(
        "update users set firstName=%s, lastName=%s,gender=%s, password=%s , status=%s where email=%s",
        (f_name, l_name, gender, hash_password, 1, email), True)
    if (dbid > 0):
        data = '1'
    else:
        data = '0'
    return data


def sendOtp(email, mail, token):
    s = db.execute("select * from users where email=%s and status=1", (email,))
    if len(s) == 0:
        return {'msg': 'Dies ist keine gültige Email-Adresse!'}
    else:
        verification_code = random.randint(1000, 100000)

        db.execute("Update users set verification_code=%s where email=%s", (verification_code, email), True)
        msg = Message(
            'Ihr Zugang zu truffle.one',
            sender=('Truffle.one', 'info@truffle.one'),
            recipients=['receiver', email]
        )
        link = url_for('verify_for_forget', token=token, otp=verification_code, _external=True)
        msg.html = '''<h5>Setzen Sie hier ein neues Passwort für Ihren Zugang zu truffle.one:</h5>''' + link
        mail.send(msg)
        msg = 'Bitte bestätigen Sie die Email, die wir Ihnen gesendet haben.'
        return {'msg': msg, 'email': email}


def verify_for_forget(email, otp):
    s = db.execute("select * from users where email=%s and verification_code=%s", (email, otp))
    if len(s) > 0:
        data = email
    else:
        data = 0
    return data


def update_password(email, password):
    hash_password = hashlib.md5(password.encode("utf-8")).hexdigest()

    s = db.execute("update users set password=%s where email=%s", (hash_password, email), True)
    if (s > 0):
        data = "1"
    else:
        data = "0"
    return data


def reset(old_password, new_password, email):
    old_password = hashlib.md5(old_password.encode("utf-8")).hexdigest()
    new_password = hashlib.md5(new_password.encode("utf-8")).hexdigest()

    s = db.execute("select * from users where email=%s and password = %s", (email, old_password))
    if len(s) > 0:
        db.execute("update users set password=%s where email=%s", (new_password, email), True)
        data = "1"
    else:
        data = "0"
    return data

class User:
    def __init__(self, dbId, email=None, customerId=None, firstName=None, lastName=None, gender=None, language=None):
        self.dbId = dbId
        self.firstName = firstName
        self.lastName = lastName
        self.customerId = customerId
        self.gender = gender
        self.language = language
        self.email = email

    def getUserConfig(self, userConfigKey):
        result = db.execute("select userConfigValue from userConfig where user=%s and userConfigKey = %s", (self.dbId, userConfigKey))
        if result is not None and len(result)>0:
            return result[0][0]
        else:
            return None

    def setUserConfig(self, userConfigKey, userConfigValue):
        db.execute('''INSERT INTO userConfig(user, userConfigKey, userConfigValue) values(%s, %s, %s)
                       ON DUPLICATE KEY UPDATE userConfigValue=%s''',
                       (self.dbId, userConfigKey, userConfigValue, userConfigValue), True)

    def save(self):
        if self.dbId:
            db.execute('''UPDATE users set firstName=%s, lastName=%s, gender=%s, language=%s where userId=%s''',
                       (self.firstName, self.lastName, self.gender, self.language, self.dbId), True)
        else:
            db.execute('''insert INTO users(firstName, lastName, gender, language)
                    values(%s, %s, %s, %s)''',
                   (self.firstName, self.lastName, self.gender, self.language), True)