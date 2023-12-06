
$( document ).ready(function() {

    bindAdvertise();
    $("#btnUpdate").hide();
    let advertiseId = $("#advertiser").val();
    //advertisement tab
    $('#headline2').hide();
    $('#link2').hide();
    $('#textarea2').hide();
    $('#attribution2').hide();
    $('#file2').hide();
    $("#t1nativeAd").hide();
    $("#t2nativeAd").hide();
//  getting ip address ##########################
    $.getJSON("https://api.ipify.org?format=json", function(data) {

        // Setting text of element P with id gfg
        $("#ip").val(data.ip);
    })

// calling performance ###########################

    performance();
});

function bindAdvertise(){
    $.ajax({
		url:'/advertise/bindAdvertiser',
		type: "POST",
		data:{},
		cache: false,
		success:function(response){
		$("#advertiser").html(response);
		bindCampaigns();
            }
	});
}

function addAdvertise(){
    let advertiseName = $("#advertiseName").val();
    $.ajax({

		url:'/advertise/crudAdvertise',
		type: "POST",
		data:{'operationName':'add','advertiseName':advertiseName},
		cache: false,
		success:function(dataResult){
		    if(dataResult != ''){
		       console.log(dataResult);
		       bindAdvertise();
		       $("#advertiseName").val('');
		       $('#advertiseModel').modal('toggle');
		    }
		}
	});
   }

function deleteAdvertise(){

    let advertiseId = $("#advertiser").val();
    $.ajax({

		url:'/advertise/crudAdvertise',
		type: "POST",
		data:{'operationName':'delete','advertiseId':advertiseId},
		cache: false,
		success:function(dataResult){
		       console.log(dataResult);
		       bindAdvertise();
		}
	});
}

function editAdvertiser(){
    let advertiseId = $("#advertiser").val();
    $.ajax({
            url:'/advertise/crudAdvertise',
            type: "POST",
            data:{'operationName':'edit', 'advertiseId':advertiseId},
            cache: false,
            success:function(response){
                $.each(response , function(index, val) {
                      console.log(index, val)
                      $("#adId").val(val[0]);
                      $("#advertiseName").val(val[1]);
                      $("#btnAdd").hide();
                      $("#btnUpdate").show();
                    });
               }
        });
    }

function updateAdvertise(){
    let advertiseId = $("#adId").val();
    let advertiseName = $("#advertiseName").val();
    $.ajax({

		url:'/advertise/crudAdvertise',
		type: "POST",
		data:{'operationName':'update','advertiseName':advertiseName, 'advertiseId':advertiseId},
		cache: false,
		success:function(dataResult){
		    if(dataResult != ''){
		       console.log(dataResult);
		       bindAdvertise();
		       $("#advertiseName").val('');
		       $('#advertiseModel').modal('toggle');
		       $("#btnUpdate").hide();
		       $("#btnAdd").show();
		    }
		}
	});
   }

function bindCampaigns(){
let advertiseId = $("#advertiser").val();
$.ajax({
    url:'/campaign/bindCampaign',
    type: "POST",
		data:{'advertiseId':advertiseId},
		cache: false,
		success:function(response){
		$("#campaign").html(response);
		    let campaignId = $("#campaign").val();
		    if(campaignId == null){
		        $("#campaignDel").hide();
		        $("#campaignId").html('');
                $("#campaignsName").val('');
                $("#from").val('');
                $("#till").val('');
                $('#active').prop('checked', false);
		    }
		    else{
		    	$("#campaignDel").show();
		    	campaignDetails();
		    }
        }
	});
}

function deleteCampaign(){
    let campaignId = $("#campaign").val();
    $.ajax({
		url:'/campaign/crudCampaign',
		type: "POST",
		data:{'operationName':'delete','campaignId':campaignId},
		cache: false,
		success:function(dataResult){
		       console.log(dataResult);
		       bindCampaigns();
		}
	});

}

function addCampaign(){

    let advertiseId = $("#advertiser").val();
    let campaignName = $("#campaignName").val();
    $.ajax({

		url:'/campaign/crudCampaign',
		type: "POST",
		data:{'operationName':'add','campaignName':campaignName, 'advertiseId':advertiseId},
		cache: false,
		success:function(dataResult){
		    if(dataResult != ''){
		       console.log(dataResult);
		       bindAdvertise();
		       $("#campaignName").val('');
		       $('#campaignModel').modal('toggle');
		       bindCampaigns();
		    }
		}
	});
   }

function campaignDetails(){

    let advertiseId = $("#advertiser").val();
    let campaignId = $("#campaign").val();
    rangeTargeted(campaignId)
    $.ajax({
        url:'/campaign/campaignDetails',
        type: "POST",
        data:{'advertiseId':advertiseId, 'campaignId':campaignId},
        cache: false,
		success:function(response){
		 $.each(response , function(index, val) {
		$("#campaignId").html(val[0]);
		$("#campaignsName").val(val[1]);
		$("#from").val(moment(val[2]).format('YYYY-MM-DDTHH:mm'));
		$("#till").val(moment(val[3]).format('YYYY-MM-DDTHH:mm'));
		let isActive = (val[4]);
            if(isActive == 1){
                $('#active').prop('checked', true);
            }
            else{
                $('#active').prop('checked', false);
            }
        });
        }
    });
}


function addCampaignDetails(){
    let advertiseId = $("#campaignId").text();
    let advertiseName = $("#campaignsName").val();
	let from = $("#from").val();
	let till = $("#till").val();
	var checkBox = $('#active').is(':checked');
	console.log(checkBox);
	if(checkBox == true){
        var active = 1;
	}
	else{
        var active = 0;
	}
	$.ajax({
	    url:'campaign/crudCampaign',
	    type:'post',
	    data:{'operationName':'addCampaignDetails',
	          'campaignId':advertiseId,
	          'campaignsName':advertiseName,
	          'from':from, 'till':till, 'active':active},
		cache: false,
		success:function(response){
		console.log(response);
		}
	});
}

//rangeTargeted comment #######################

function rangeTargeted(campaignId){

    $.ajax({
		url:'/campaign/rangeTargeted',
		type: "POST",
		data:{'campaignId':campaignId},
		cache: false,
		success:function(response){
		    $("#rangeTargeted").html("Ranges targeted: "+response);
            }
	});
}

// get the content of advertising #################

//advertisement tab ################################################
function check1(){

    var check = document.getElementById('customSwitches1').checked;
        if(check == true){
            $("#headline2").show();
        }
        else{
            $("#headline2").hide();
        }
    }

function check2(){
    var check = document.getElementById('customSwitches2').checked;
        if(check == true){
            $("#textarea2").show();
        }
        else{
            $("#textarea2").hide();
        }
    }

function check3(){
    var check = document.getElementById('customSwitches3').checked;
        if(check == true){
            $("#link2").show();
        }
        else{
            $("#link2").hide();
        }
    }

function check4(){
    var check = document.getElementById('customSwitches4').checked;
        if(check == true){
            $("#attribution2").show();
        }
        else{
            $("#attribution2").hide();
        }
    }

function check5(){
    var check = document.getElementById('customSwitches5').checked;
        if(check == true){
            $("#file2").show();
        }
        else{
            $("#file2").hide();
        }
    }

// post content data ####################################
function postContentData(){
    var t1nativeAd = document.getElementById('t1nativeAd').removeAttribute('style');
    var t2nativeAd = document.getElementById('t2nativeAd').removeAttribute('style');

//before checked
    let headline = $("#headline1").val();
    let textarea = $("#textarea1").val();
    let link = $("#link1").val();
    let attribution = $("#attribution1").val();
    let string = $("#file1").val();
    let splitURL=string.toString().split("\\");
        splitURL = splitURL[2];
//after checked
    var headline2 = $("#headline2").val();
    var textarea3 = $("#textarea2").val();
    var link2 = $("#link2").val();
    var attribution2 = $("#attribution2").val();
    var string2 = $("#file2").val();
    var splitURL2=string2.toString().split("\\");
        splitURL2 = splitURL2[2];

    document.getElementById('c-pin__headline').innerHTML = headline;
    document.getElementById('textarea').innerHTML = textarea;
    var linkUrl1 = document.getElementById('link_url1');
        linkUrl1.setAttribute('href',link);
    var linkUrl2 = document.getElementById('link_url2');
        linkUrl2.setAttribute('href',link);
    var alt = document.getElementById('truffleone_img1');
        alt.setAttribute("alt", headline);
        alt.setAttribute("title", headline);
    var img1 = document.getElementById('truffleone_img1')
        img1.setAttribute("data-src", "https://api.truffle.one/static/ads/"+splitURL);
        img1.setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);

//noscript
    var element = document.getElementById('myElement').innerHTML;
        element = $(element)
        element[0].setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);
        element[0].setAttribute("alt", headline);
        element[0].setAttribute("title", headline);
        document.getElementById('myElement').innerHTML=element[0].outerHTML;

    let check1 = document.getElementById('customSwitches1').checked;
    let check2 = document.getElementById('customSwitches2').checked;
    let check3 = document.getElementById('customSwitches3').checked;
    let check4 = document.getElementById('customSwitches4').checked;
    let check5 = document.getElementById('customSwitches5').checked;
    if (check1 == true){
        document.getElementById('c-pin__headline2').innerHTML = headline2;
    }
    else{
        document.getElementById('c-pin__headline2').innerHTML = headline;
        headline2 = headline;
    }
    if (check2 == true){
        document.getElementById('textarea3').innerHTML = textarea3;
    }
    else{
        document.getElementById('textarea3').innerHTML = textarea;
        textarea3 = textarea;
    }
    if (check3 == true){
        var linkUrl1 = document.getElementById('link_url3');
            linkUrl1.setAttribute('href',link2);
        var linkUrl2 = document.getElementById('link_url4');
            linkUrl2.setAttribute('href',link2);
    }
    else{
        var linkUrl1 = document.getElementById('link_url3');
            linkUrl1.setAttribute('href',link);
        var linkUrl2 = document.getElementById('link_url4');
            linkUrl2.setAttribute('href',link);
            linkUrl2 = link;
    }
    if (check4 == true){
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline2);
            alt.setAttribute("title", headline2);
    }
    else{
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline);
            alt.setAttribute("title", headline);
            attribution2 = headline;
    }
    if (check5 == true){
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline2);
            alt.setAttribute("title", headline2);
        var img1 = document.getElementById('truffleone_img2')
            img1.setAttribute("data-src", "https://api.truffle.one/static/ads/"+splitURL2);
            img1.setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL2);

//noscript
        var element = document.getElementById('myElement2').innerHTML;
            element = $(element)
            element[0].setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL2);
            element[0].setAttribute("alt", headline2);
            element[0].setAttribute("title", headline2);
            document.getElementById('myElement2').innerHTML=element[0].outerHTML;
    }
    else{
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline);
            alt.setAttribute("title", headline);
        var img1 = document.getElementById('truffleone_img2')
            img1.setAttribute("data-src", "https://api.truffle.one/static/ads/"+splitURL);
            img1.setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);

//noscript
        var element = document.getElementById('myElement2').innerHTML;
            element = $(element)
            element[0].setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);
            element[0].setAttribute("alt", headline);
            element[0].setAttribute("title", headline);
            document.getElementById('myElement2').innerHTML=element[0].outerHTML;
    }

    var html1 = document.getElementById('a1').innerHTML;
    var html2 = document.getElementById('a2').innerHTML;
    var form_data = new FormData();
        form_data.append('file1', $('#file1').prop('files')[0]);
         if(check5 == true){
            form_data.append('file2', $('#file2').prop('files')[0]);
            }
         else{
            form_data.append('file2', $('#file1').prop('files')[0]);
            }
//get the checkbox ("t3n content page" and "t3n home page") value
    let t3nContent = document.getElementById("check1").value;
    let t3nHome = document.getElementById("check2").value;
        form_data.append('html1', html1);
        form_data.append('html2', html2);
        form_data.append('headline', headline);
        form_data.append('headline2', headline2);
        form_data.append('textarea', textarea);
        form_data.append('textarea3', textarea3);
        form_data.append('link', link);
        form_data.append('link2', linkUrl2);
        form_data.append('attribution', headline);
        form_data.append('attribution2', headline2);
        form_data.append('splitURL', splitURL);
        form_data.append('splitURL2', splitURL2)
        form_data.append('check1', t3nContent)
        form_data.append('check2', t3nHome)

//        calling customer_id from navigation page
        let customer_id= document.getElementById('customer_id').value;
            form_data.append('customer_id',customer_id)
            return {html1:html1, html2:html2};
 }

// show the preview of t3nContentPage ###################
function t3nContentPage(){
    $("#showContentText").val("");
    let t3nC = document.getElementById('t3nC').innerHTML;
    let doc = postContentData();
    $("#showContentText").val(doc.html1);
    $("#t1nativeAd").hide();
    $("#t2nativeAd").hide();
 }
//end t3nContentPage

// show the preview of t3nHtmlPage #######################
function t3nHtmlPage(){
    $("#showContentText").val("");
    let t3nH = document.getElementById('t3nH').innerHTML;
    let doc = postContentData();
    $("#showContentText").val(doc.html2);
    $("#t1nativeAd").hide();
    $("#t2nativeAd").hide();
 }
//end t3nHtmlPage

// save postContent data ################################
function savePostContentData(){
    var t1nativeAd = document.getElementById('t1nativeAd').removeAttribute('style');
    var t2nativeAd = document.getElementById('t2nativeAd').removeAttribute('style');
//        calling customer_id from navigation page
    let campaignId = $("#campaign").val();
//before checked
    let headline = $("#headline1").val();
    let textarea = $("#textarea1").val();
    let link = $("#link1").val();
    let attribution = $("#attribution1").val();
    let string = $("#file1").val();
    let splitURL=string.toString().split("\\");
        splitURL = splitURL[2];
    if(headline == "" || textarea == "" || link == "" || attribution == "" || string == ""){
            $("#notification").show();
			$("#inner-message").html("All fields are required...");
			$("#notification").delay(3000).show().fadeOut('slow');
			$("#t1nativeAd").hide();
            $("#t2nativeAd").hide();
           }
    else{

//after checked
    var headline2 = $("#headline2").val();
    var textarea3 = $("#textarea2").val();
    var link2 = $("#link2").val();
    var attribution2 = $("#attribution2").val();
    var string2 = $("#file2").val();
    var splitURL2=string2.toString().split("\\");
        splitURL2 = splitURL2[2];

    document.getElementById('c-pin__headline').innerHTML = headline;
    document.getElementById('textarea').innerHTML = textarea;
    var linkUrl1 = document.getElementById('link_url1');
        linkUrl1.setAttribute('href',link);
    var linkUrl2 = document.getElementById('link_url2');
        linkUrl2.setAttribute('href',link);
    var alt = document.getElementById('truffleone_img1');
        alt.setAttribute("alt", headline);
        alt.setAttribute("title", headline);
    var img1 = document.getElementById('truffleone_img1')
        img1.setAttribute("data-src", "https://api.truffle.one/static/ads/"+splitURL);
        img1.setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);

//noscript
    var element = document.getElementById('myElement').innerHTML;
        element = $(element)
        element[0].setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);
        element[0].setAttribute("alt", headline);
        element[0].setAttribute("title", headline);
        document.getElementById('myElement').innerHTML=element[0].outerHTML;

    let check1 = document.getElementById('customSwitches1').checked;
    let check2 = document.getElementById('customSwitches2').checked;
    let check3 = document.getElementById('customSwitches3').checked;
    let check4 = document.getElementById('customSwitches4').checked;
    let check5 = document.getElementById('customSwitches5').checked;
    if (check1 == true){
        document.getElementById('c-pin__headline2').innerHTML = headline2;
    }
    else{
        document.getElementById('c-pin__headline2').innerHTML = headline;
        headline2 = headline;
    }
    if (check2 == true){
        document.getElementById('textarea3').innerHTML = textarea3;
    }
    else{
        document.getElementById('textarea3').innerHTML = textarea;
        textarea3 = textarea;
    }
    if (check3 == true){
        var linkUrl1 = document.getElementById('link_url3');
            linkUrl1.setAttribute('href',link2);
        var linkUrl2 = document.getElementById('link_url4');
            linkUrl2.setAttribute('href',link2);
    }
    else{
        var linkUrl1 = document.getElementById('link_url3');
            linkUrl1.setAttribute('href',link);
        var linkUrl2 = document.getElementById('link_url4');
            linkUrl2.setAttribute('href',link);
            linkUrl2 = link;
    }
    if (check4 == true){
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline2);
            alt.setAttribute("title", headline2);
    }
    else{
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline);
            alt.setAttribute("title", headline);
            attribution2 = headline;
    }
    if (check5 == true){
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline2);
            alt.setAttribute("title", headline2);
        var img1 = document.getElementById('truffleone_img2')
            img1.setAttribute("data-src", "https://api.truffle.one/static/ads/"+splitURL2);
            img1.setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL2);

//noscript
        var element = document.getElementById('myElement2').innerHTML;
            element = $(element)
            element[0].setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL2);
            element[0].setAttribute("alt", headline2);
            element[0].setAttribute("title", headline2);
            document.getElementById('myElement2').innerHTML=element[0].outerHTML;
    }
    else{
            splitURL2=splitURL;
        var alt = document.getElementById('truffleone_img2');
            alt.setAttribute("alt", headline);
            alt.setAttribute("title", headline);
        var img1 = document.getElementById('truffleone_img2')
            img1.setAttribute("data-src", "https://api.truffle.one/static/ads/"+splitURL);
            img1.setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);

//noscript
        var element = document.getElementById('myElement2').innerHTML;
            element = $(element)
            element[0].setAttribute("src", "https://api.truffle.one/static/ads/"+splitURL);
            element[0].setAttribute("alt", headline);
            element[0].setAttribute("title", headline);
            document.getElementById('myElement2').innerHTML=element[0].outerHTML;
    }

    var html1 = document.getElementById('a1').innerHTML;
    var html2 = document.getElementById('a2').innerHTML;
    var form_data = new FormData();
        form_data.append('file1', $('#file1').prop('files')[0]);
         if(check5 == true){
            form_data.append('file2', $('#file2').prop('files')[0]);
            }
         else{
            form_data.append('file2', $('#file1').prop('files')[0]);
            }
//get the checkbox ("t3n content page" and "t3n home page") value
    let t3nContent;
    let t3nHome;
    if ($('#check1').is(":checked"))
        {
            t3nContent= 1;
        }
        else{
            t3nContent= 0;
        }
    if ($('#check2').is(":checked"))
        {
            t3nHome= 2;
        }
        else{
            t3nHome= 0;
        }

        form_data.append('html1', html1);
        form_data.append('html2', html2);
        form_data.append('headline', headline);
        form_data.append('headline2', headline2);
        form_data.append('textarea', textarea);
        form_data.append('textarea3', textarea3);
        form_data.append('link', link);
        form_data.append('link2', linkUrl2);
        form_data.append('attribution', headline);
        form_data.append('attribution2', headline2);
        form_data.append('splitURL', splitURL);
        form_data.append('splitURL2', splitURL2);
        form_data.append('t3nContent', t3nContent);
        form_data.append('t3nHome', t3nHome);
        form_data.append('campaignId',campaignId)
            $.ajax({
                type: 'POST',
                url: '/campaign/advertisingPostContent',
                data: form_data,
                contentType: false,
                cache: false,
                processData: false,
                success: function(data) {
                    $("#t1nativeAd").hide();
                    $("#t2nativeAd").hide();
                    if(data == "1"){
                        $("#notification").show();
                        $("#inner-message").html("Data saved successfully...");
                        $("#notification").delay(3000).show().fadeOut('slow');
//  crear all the control from the current page
                        $("#headline1").val("");
                        $("#textarea1").val("");
                        ("#link1").val("");
                        ("#attribution1").val("");

                        $("#headline2").val("");
                        $("#textarea2").val("");
                        ("#link2").val("");
                        ("#attribution2").val("");
                    }
                    else{
                        $("#notification").show();
                        $("#inner-message").html("Data could not be saved successfully...");
                        $("#notification").delay(3000).show().fadeOut('slow');
                    }
                },
            });
    }
}

//posting performance data ##############################
function performance(){
    $.ajax({
        url:'/campaign/performance',
        type:'GET',
        success:function(response){
            $("#t3nHomePage").append("<td>"+ response.totalData[0] +"</td>")
                             .append("<td>"+ response.totalData[1] +"</td>")
                             .append("<td>"+ response.totalData[2] +"%</td>")

                             .append("<td>"+ response.listType1Desktop[0] +"</td>")
                             .append("<td>"+ response.listType1Desktop[1] +"</td>")
                             .append("<td>"+ response.listType1Desktop[2] +"%</td>")

                             .append("<td>"+ response.listType1Mobile[0] +"</td>")
                             .append("<td>"+ response.listType1Mobile[1] +"</td>")
                             .append("<td>"+ response.listType1Mobile[2] +"%</td>")

            $("#t3nContentPage").append("<td>"+ response.totalData[3] +"</td>")
                             .append("<td>"+ response.totalData[4] +"</td>")
                             .append("<td>"+ response.totalData[5] +"%</td>")

                             .append("<td>"+ response.listType2Desktop[0] +"</td>")
                             .append("<td>"+ response.listType2Desktop[1] +"</td>")
                             .append("<td>"+ response.listType2Desktop[2] +"%</td>")

                             .append("<td>"+ response.listType2Mobile[0] +"</td>")
                             .append("<td>"+ response.listType2Mobile[1] +"</td>")
                             .append("<td>"+ response.listType2Mobile[2] +"%</td>")

            $("#t3nTotal").append("<td>"+ response.totalData[6] +"</td>")
                             .append("<td>"+ response.totalData[7] +"</td>")
                             .append("<td>"+ response.totalData[8] +"%</td>")

                             .append("<td>"+ response.totalData[9] +"</td>")
                             .append("<td>"+ response.totalData[10] +"</td>")
                             .append("<td>"+ response.totalData[11] +"%</td>")

                             .append("<td>"+ response.totalData[12] +"</td>")
                             .append("<td>"+ response.totalData[13] +"</td>")
                             .append("<td>"+ response.totalData[14] +"%</td>")

        }
    });
}