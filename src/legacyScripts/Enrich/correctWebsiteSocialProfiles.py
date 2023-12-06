from services import DbConfig, StringHelper, WebsiteService, CompanyService
import datetime




websites = WebsiteService.getAllWebsitesModifiedBefore(datetime.datetime(2023, 6, 27, 12, 14, 26))
#websites = WebsiteService.getAllWebsites()

for website in websites:
    print("-----", website.website, "------")
    website.validate()
    if website.dbId is not None:
        website.identifyScopes()
        website.getFavIcon()
        website.scrapeSocialProfiles()
        website.getScreenshot(True)
        website.save()
        if website.company is not None:
            website.company.enrich()
            website.company.chooseBestFirmographics()