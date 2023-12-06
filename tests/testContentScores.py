from services.ContentScoreService import ContentScore, SearchTerm, getContentScoresOfCustomer
from services.CustomerService import Customer
from services.WebsiteService import Website
import services.CustomerService as cs
import services.WebsiteService as ws

############################################################################################################
# LOADING THE CONTENT SCORE CONFIG PAGE:

# truffle.one test customer
customer = cs.getCustomer(39)

### get all ContentScores of a customer
css = getContentScoresOfCustomer(customer)
print("ALL CONTENTSCORES OF CUSTOMER", customer)
for cs in css:
    print("scope name: ", cs.name)
    print ("ScopeType: ", cs.scopeType)
    for st in cs.searchTerms:
        print("  ", st.searchTerm)

    #scopes:
    # 1 = homepage
    # 3 = imprint page
    # 4 = contact page
    # 5 = privacy statement page
    # 6 = T&C
##############################################################################################################
# modifying / adding/deleteing scores and search terms

### generate new ContentScores and save them in the data base
cs1 = ContentScore(customer,  "IOT", 1)
for term in ["Internet of Things", "IOT", "I.?O.?T"]:
    cs1.searchTerms.append(SearchTerm(cs1, term, True, False))
cs1.save()
cs1.addSubscriber(customer, 0)

cs2 = ContentScore(customer, "Body and Head Tags", 3)
for term in ["body", "head"]:
    cs2.searchTerms.append(SearchTerm(cs2, term, False, True))
cs2.save()
cs2.addSubscriber(customer, 0)

cs3 = ContentScore(customer, "Names", 1)
for term in ["Niko", "Jeet", "Amresh"]:
    cs3.searchTerms.append(SearchTerm(cs3, term, True, False))
cs3.save()
cs3.addSubscriber(customer, 0)

# modify a contentScore name
cs1.name = "new name"
cs1.save()

# modify a searchTerm
cs1.searchTerms[0].searchTerm="newSearchTErm"
cs1.save()

######delete an entire ContentScore
cs1.delete()

##### delete a specific searchTerm
cs2.searchTerms[0].delete()

############ delete all contentScores
for cs in css:
    cs.delete()



########### WORK TILL HERE #######################################


