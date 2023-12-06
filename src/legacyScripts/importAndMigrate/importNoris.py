#!/usr/bin/python
# coding: iso-8859-1

import pandas as pd
import numpy as np
from translation6 import getCompanyId, assignCompany, domain2companyIdKickfire, generateNewCompanyId, \
    chooseBestFirmographics, guessGenderOfContactId, linkedin2companyByProxycurl, domain2linkedinByProxycurl
import mysql.connector

df = pd.read_excel('20230300 imports.xlsx')

cnx = mysql.connector.connect(host="localhost", user="truffle", password="anothertry", database="truffle")
cursor = cnx.cursor(buffered=True)


############ columnnames#############################
hasCompany = False
hasContact = False
hasEmail = False
hasAddress = False



#todo remove hardcoding:
colNames = ["contacts.firstname", "contacts.lastname", "email_addresses.emailAddress", "companies.name", "websites.website"]

hasCompany = True
hasContact = True
hasEmail = True

domainCol = 5
emailCol = 3
companyNameCol = 4

cols_insertContact = [1, 2]
cols_insertEmail = [3]
cols_insertAddress = []

##end hardcoding
#todo: lookup correct column names
'''
for cell in df.columns:
    print("cell value: ", cell)

    values = (clnSpacesAndDashes(cell), )

    #1 lookup columName
    sql = "SELECT tableName, colName, rule FROM importColumnNames WHERE name=%s"
    cursor.execute(sql, values)
    rows = cursor.fetchall()
        
    propositions = ["New custom company field: " + cell]
    sqls = ["INSERT INTO "]
    for row in rows:    
        if row[2] == None:
            propositions.insert(0, row[0]+"."+row[1])
            if row[0]=="contacts":
                hasContact = True
            pass
        else:
            #todo
            #applyrule
            pass
        
    
    for proposition in propositions:
        
        print(cell, "could be: ", propositions)
    
    domainCol = 5
    emailCol = 3
    companyNameCol = 4

    #hasCompany = True
    #hasContact = True
    #hasEmail = True
    #hasAddress = True
'''  


################# build sql statements #################################################################
sql_insertContact = "INSERT INTO contacts(customerId, companyId, "
lastpart = ") values(%s, %s,"
i = 0
for col in cols_insertContact:
    if i != 0:
        sql_insertContact = sql_insertContact + ", "
        lastpart = lastpart + ", "
    sql_insertContact = sql_insertContact + colNames[col-1]
    lastpart = lastpart + "%s"
    i +=1
sql_insertContact = sql_insertContact + lastpart + ")"

sql_insertEmail = "INSERT INTO email_addresses(customerId, useType, contactId, companyId, "
lastpart = ") values(%s, %s, %s, %s, "
i = 0
for col in cols_insertEmail:
    if i != 0:
        sql_insertEmail = sql_insertEmail + ", "
        lastpart = lastpart + ", "
    sql_insertEmail = sql_insertEmail + colNames[col-1]
    lastpart = lastpart + "%s"
    i +=1
sql_insertEmail = sql_insertEmail + lastpart + ")"

sql_insertAddress = "INSERT INTO addresses(contactId, companyId, "
lastpart = ") values(%s, %s,"
i = 0
for col in cols_insertAddress:
    if i != 0:
        sql_insertAddress = sql_insertAddress + ", "
        lastpart = lastpart + ", "
    sql_insertAddress = sql_insertAddress + colNames[col-1]
    lastpart = lastpart + "%s"
    i +=1
sql_insertAddress = sql_insertAddress + lastpart + ")"

print(sql_insertContact)
print(sql_insertEmail)
print(sql_insertAddress)


i2 = 0
############# values #######################################################################################
for row in df.itertuples(index = True):
    contactId = None
    companyId = None
    emailId = None
    addressId = None
    

    #todo: fetch domain from email
    #if not companyId and not row[domainCol] and row[emailCol]:

    #todo try to lookup the company über adresse und umkreis von lat/lon
    companyId = getCompanyId(str(row[companyNameCol]), str(row[domainCol]))
    #if companyId == None: companyId = domain2companyIdKickfire(str(row[domainCol]))
    if companyId == None:
        linkedInProfile = domain2linkedinByProxycurl(str(row[domainCol]))
        linkedin2companyByProxycurl(linkedInProfile, companyId)
    if companyId == None: companyId = generateNewCompanyId(str(row[companyNameCol]))
    
    print ("companyId for", str(row[companyNameCol]), "(", str(row[domainCol]), ") is:", companyId)
    #cursor.execute("UPDATE ")


    assignCompany(companyId, 79)
    
    chooseBestFirmographics(companyId)
    
    ####################################################################################################################################################
    #################################################### ###########################################################
    ####################################################  ###############################################
    #################################################### weitere rules prüfen ##########################################################################
    #################################################### SQL-Statements executen #######################################################################
    ####################################################################################################################################################
    ####################################################################################################################################################
    ####################################################################################################################################################
    ######################################################insert email -> useType, isFunctional, isMailservice #########################################
    ######################################################vorname und nachname ableiten aus email-adresse#########################################
    ####################################################################################################################################################
    ####################################################################################################################################################
    ####################################################################################################################################################
    #todo update company - aber nur für diesen customer


    ####################INSERTING IN DB ############################
    
    #todo: try to lookup contact via email address, name, company
    # contactId = 
    #if contactId:
    # update
    # else:
    val_insertContact = [79, companyId]
    for col in cols_insertContact:
        if str(row[col]) != "nan":
            val_insertContact.append(row[col])
        else:
            val_insertContact.append(None)
    print("values insertcontact: ", val_insertContact)
    if len(val_insertContact)>2:
        cursor.execute(sql_insertContact, val_insertContact)
        contactId = cursor.lastrowid
        cnx.commit()
        guessGenderOfContactId(contactId, True)

    #todo: check ob es schon gibt und der contactId / companyId zugewiesen
    val_insertEmail = [79, 0, contactId, companyId]
    for col in cols_insertEmail:
        
        if str(row[col]) != "nan":
            val_insertEmail.append(row[col])
        else:
            val_insertEmail.append(None)
    print (val_insertEmail)
    emailId = None
    if len(val_insertEmail)>4:
        cursor.execute(sql_insertEmail, val_insertEmail)
        emailId = cursor.lastrowid
        cnx.commit()
    if contactId and emailId:
        val_updateContact = (emailId, contactId)
        sql_updateContact = "UPDATE contacts set primaryEmailId=%s where contactId=%s"
        cursor.execute(sql_updateContact, val_updateContact)
        cnx.commit()
    
    
    #todo: check ob es schon gibt und der contactId / companyId zugewiesen
    val_insertAddress = [contactId, companyId]
    for col in cols_insertAddress:
        if str(row[col]) != "nan":
            val_insertAddress.append(row[col])
        else:
            val_insertAddress.append(None)
    print (val_insertAddress)
    if len(val_insertAddress)>2:
        cursor.execute(sql_insertAddress, val_insertAddress)
        addressId = cursor.lastrowid
        cnx.commit()
    if contactId and addressId:
        val_updateContact = (addressId, contactId)
        sql_updateContact = "UPDATE contacts set primaryAddressId=%s where contactId=%s"
        cursor.execute(sql_updateContact, val_updateContact)
        cnx.commit()



