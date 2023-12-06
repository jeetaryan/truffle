/* get client id param ABA version */

var customerId = "";
var t1_params = t1_params || [];
if(t1_params && t1_params[0] && t1_params[0][0]){
	customerId = t1_params[0][0];
}

if (customerId == 4){
    // Load the script
    const script = document.createElement("script");
    script.src = 'https://ajax.googleapis.com/ajax/libs/jquery/3.6.1/jquery.min.js';
    script.type = 'text/javascript';
    script.addEventListener('load', () => {
    aba = {};
    aba['customerId']=customerId;

    if (location.pathname == "/" ) {
        aba['adType']=1
        var parentElement = null;
        var mobile = 0;
        parentElement = document.getElementsByClassName("o-grid__main")[0];

        if (parentElement == null) {
            mobile = 1
            parentElement = document.getElementsByClassName("neos-contentcollection")[0];
        }

        previousElement =  parentElement.getElementsByTagName("article")[0];
        followElement =  parentElement.getElementsByTagName("article")[1];

        if ((previousElement.innerHTML.includes("Anzeige")) ||
           (followElement.innerHTML.includes("Anzeige"))){
        } else {
            var abarequest = new XMLHttpRequest();
            abarequest.open('POST', 'https://api.truffle.one/aba', true);
            abarequest.setRequestHeader('Content-Type', 'application/json');
            abarequest.onload = function () {

                if(this.status == 200){
                    var data = this.response;
                    var datajson = JSON.parse(this.response);
                    $(document).ready(function(){
                        if (mobile == 1){
                            previousElement.insertAdjacentHTML("afterend", datajson.mobile);
                        } else {
                            previousElement.insertAdjacentHTML("afterend", datajson.desktop);
                        }
                    });
                }
            }
            abarequest.send(JSON.stringify(aba));
        }
    } else {
        aba['adType']=2
        var abarequest = new XMLHttpRequest();
        abarequest.open('POST', 'https://api.truffle.one/aba', true);
        abarequest.setRequestHeader('Content-Type', 'application/json');
        abarequest.onload = function () {

            if(this.status == 200){
                var data = this.response;
                var datajson = JSON.parse(this.response);
                //console.log(data);

                $(document).ready(function(){
                    var mainarticle = document.getElementById("main-content");
                    if (mainarticle == null){
                        mobile = 1
                        parentElement = document.querySelectorAll(".c-entry > div > p:not(.u-text-small)")
                        parentElement[0].insertAdjacentHTML("afterend", datajson.mobile);
                    }
                    else if (mainarticle.innerText.length > 1300){
                        var parentElement = document.getElementsByTagName("aside")[0];
                        if (parentElement != null){
                            parentElement.insertAdjacentHTML("beforeend", datajson.desktop);
                        }
                    }
                });
            }
        }
        abarequest.send(JSON.stringify(aba));
    }
    });
    document.head.appendChild(script);
}



/* get client id param */
class Trackcode {
	constructor(customerId) {
		self = this;
		this.customerId = customerId;
	  	this.apiUrl = 'https://api.truffle.one/visit';
		this.heartbeatUrl = 'https://api.truffle.one/heartbeat';
		this.obj = {};
		this.maxScrollDepth = 0;
		this.heartbeat = {
			scrollDepth: 0,
			pageId: 0,
			customerId: customerId
		};
		this.reqData = {};
		this.obj['recentPageUrl'] = "";
		this.obj['recentPageId'] =  null;
		this.obj['recentDuration'] = null;
		this.obj['customerId'] = customerId;
		this.lastVisitTime =  new Date().getTime();
		this.timer = null;
		this.currentScrollDepth = 0;
		this.pageId= 0;
		if (customerId != 4) {
			this.heartbeats = [5000, 15000, 30000, 60000, 3*60000, 5*60000, 10*60000, 15*60000, 30*60000]
		} else {
			this.heartbeats = []
		}
		this.currentHeartbeat = 0
		var self = this;

        var callback = function callback(id){
    		this.heartbeat['pageId']=id;
    	};
		var winheight, trackLength, throttlescroll;
		this.getmeasurements();
		window.addEventListener("resize", function(){
    			self.getmeasurements()
		}, false)

		window.addEventListener("scroll", function(){
    			clearTimeout(self.throttlescroll)
        		self.throttlescroll = setTimeout(function(){ // throttle code inside scroll to once every 50 milliseconds
                                self.getmeasurements()
        			self.amountscrolled()
				}, 50)
		}, false)
    }


	getmeasurements(){
    		this.winheight= window.innerHeight || (document.documentElement || document.body).clientHeight;
    		this.docheight = this.getDocHeight();
    		this.trackLength = this.docheight - this.winheight;
	}

	amountscrolled(){
 		var scrollTop = window.pageYOffset || (document.documentElement || document.body.parentNode || document.body).scrollTop;
		this.currentScrollDepth = Math.floor(scrollTop/this.trackLength * 100); // gets percentage scrolled (ie: 80 or NaN if tracklength == 0);
                if (this.maxScrollDepth < this.currentScrollDepth){
                   this.heartbeat['scrollDepth']  = this.currentScrollDepth;
                   this.maxScrollDepth = this.currentScrollDepth;
//                   console.log("T1: " +  this.currentScrollDepth);
                }
	}

	getDocHeight() {
		var D = document;
		return Math.max(
    		D.body.scrollHeight, D.documentElement.scrollHeight,
    		D.body.offsetHeight, D.documentElement.offsetHeight,
    		D.body.clientHeight, D.documentElement.clientHeight
		)
	}


	getBasicDetails(){
		this.getmeasurements();
		this.obj['winHeight'] = screen.height;
		this.obj['winWidth'] = screen.width;
		this.obj['protocol'] = document.location.protocol;
		this.obj['referrer'] = document.referrer;
		this.obj['platform'] = navigator.platform;
        this.obj['userAgent'] = navigator.userAgent;
		this.obj['language'] = navigator.language || navigator.userLanguage; 
        this.heartbeat['pageId'] = 0;


		var url = window.location.href;
		var arr = url.split("/");
		this.obj['clientDomainName'] = arr[0] + "//" + arr[2];
		
		//get my IP
		var request = new XMLHttpRequest();
		request.open('GET', 'https://api.truffle.one/my_ip', true); 
		var self = this;
		request.onload = function () {
			if(this.status == 200){
				var data = JSON.parse(this.response);  
				if(data.ip){
					self.obj['ip'] = data.ip;
					self.obj['ip_int'] = data.ip.split(".").reduce((int, v) => int * 256 + +v);
	                //set visit ID if not existing yet
        			let pageVisitorId = localStorage.getItem("t1sid");
        			if (pageVisitorId) {
        			    self.obj['pageVisitorId'] = pageVisitorId;
						self.heartbeat['pageVisitorId']= pageVisitorId;
						if (location.href !=  localStorage.getItem("t1lp")){
							self.sendData(function(id){
					        	self.heartbeat['pageId']=id;
								localStorage.setItem("t1lid", id);
                			});
						} else {
							//reload
							//self.heartbeat['pageId']=parseInt(localStorage.getItem("t1lid"));
						}
        			} else {
            			var f = data.ip;
            			var d = f.split('.');
            			self.obj['pageVisitorId'] = ((+d[0])+100).toString()+((+d[1])+100).toString()+((+d[2])+100).toString()+((+d[3])+100).toString() + new Date().getTime();
						self.heartbeat['pageVisitorId']= self.obj['pageVisitorId'];
						localStorage.setItem("t1sid", self.obj['pageVisitorId']);
                        self.sendData(function(id){
							self.heartbeat['pageId']=id;
							localStorage.setItem("t1lid", id);
                        });
					}
				}
			}
		}
		request.send();		
	}
	

	updatePageDetails(){
		this.lastVisitTime = localStorage.getItem("t1lvt");
		if (this.lastpage = localStorage.getItem("t1lp")){
			if (location.href !=  this.lastpage){
				//navigated to another page
				this.obj['visitTime'] = new Date().getTime();
				this.obj['recentPageUrl'] = this.lastpage;
				this.obj['recentPageId'] = localStorage.getItem("t1lid");
				this.obj['recentDuration'] = this.obj['visitTime']  - this.lastVisitTime;
				//this.lastVisitTime = this.obj['visitTime']
			} else {
				//on reload
				this.obj['visitTime'] = this.lastVisitTime;
			}
		} else {
//			console.log("new visit");
			this.obj['visitTime'] = new Date().getTime();
			//this.lastVisitTime = this.obj['visitTime']
		}

		this.obj['pageUrl']  = location.host  + location.pathname;
		this.obj['utm_source'] = null;
		this.obj['utm_medium'] = null;
		this.obj['utm_campaign'] = null;
		this.obj['utm_content'] = null;
		this.obj['utm_term'] = null;
		this.obj['gclid'] = null;

		var myArray = location.href.split("?");

		this.obj['parameters']=null;
		if (myArray.length > 1) {
			this.obj['parameters'] = myArray[1];
			myArray = this.obj['parameters'].split("&");
			for (let i in myArray) {
				if (myArray[i].startsWith("utm_source") || myArray[i].startsWith("utm_medium") || myArray[i].startsWith("utm_campaign") || myArray[i].startsWith("utm_term") || myArray[i].startsWith("utm_content") || myArray[i].startsWith("gclid")){
					var utmparams = myArray[i].split("=");
					this.obj[utmparams[0]] = utmparams[1];
				}
			}
		} 
		
		this.obj['pageTitle'] = document.title;

		var date = new Date(document.lastModified.replace(/-/g, '/'))
		this.obj['pageLastModified'] = date.toISOString().slice(0, 19).replace('T', ' ');
		this.heartbeat['pageUrl'] = this.obj['pageUrl'];
	}

    sendHeartbeat(){
        if (this.obj) {
            try {
                this.heartbeat['duration']= new Date().getTime() - this.obj['visitTime'];
                var saveRequest = new XMLHttpRequest();
                saveRequest.open('POST', this.heartbeatUrl);
                saveRequest.setRequestHeader('Content-Type', 'application/json');
                saveRequest.onreadystatechange = function () {
                    if (saveRequest.readyState == 4) {

                    }
                };
                saveRequest.send(JSON.stringify(this.heartbeat));
            } catch (e) {	
                //ignore
            }
        }
    }

	sendData(callback){
        var pageId = 0
		if (this.obj) {
        	    try {
	                var saveRequest = new XMLHttpRequest();
	                saveRequest.open('POST', this.apiUrl);
	                saveRequest.setRequestHeader('Content-Type', 'application/json');
	                saveRequest.onreadystatechange = function () {
	                    if (saveRequest.readyState == 4  && saveRequest.status == 200) {
							pageId = parseInt(saveRequest.responseText);
				         	callback(pageId);
							return pageId;
	                    }
	                };
	                saveRequest.send(JSON.stringify(this.obj));
	            } catch (e) {
                
                //ignore
	            }
	        }
	}


	manageRequestData() {
		this.updatePageDetails();
		this.getBasicDetails();
		var self = this;
        	setTimeout( function() {
			localStorage.setItem("t1lp", location.href);
			localStorage.setItem("t1lvt", self.obj['visitTime']);
		}, 2000);
		for (let i = 0; i < this.heartbeats.length; i++) {
	        	setTimeout(function() {
        	        	self.sendHeartbeat();
        		}, this.heartbeats[i]);
			this.currentHeartbeat +=1;
		}
	}
}






trackObj = new Trackcode(customerId);
trackObj.manageRequestData();
