var openedRow = null;
var openedDetail = null;

function closeDetailsRows(){
    let openedRows=document.querySelectorAll('.addlRow')
    for(let i=0;i<openedRows.length;i++){
        openedRows[i].remove()
    }
    if (openedRows.length > 0) {
        return true;
    } else {
        return false;
    }
}

function showDetailsRow(companyId, detailType){
    //close all detailsRows
    closeDetailsRows()

    //show detailsRow in case user did not click on same detailType and company
    if (openedDetail!=detailType || openedRow!=companyId){
        openedRow=companyId;
        openedDetail=detailType;
        return true;
    } else {
        openedRow=null;
        openedDetail=null;
        return false;
    }
}

function showSources(companyId) {
    if (showDetailsRow(companyId, "source")){
        $.ajax({
            url:'/company/'+companyId+'/getSources?dataType=html',
            type:'get',
            data: {},
            success:function(response){
                $('#company_row_'+companyId).after(response);
            }
        });
    }
}

function showSegments(companyId) {
    if (showDetailsRow(companyId, "segments")){
        $.ajax({
            url:'/company/'+companyId+'/getSegments?dataType=html',
            type:'post',
            data: {},
            success:function(response){
                $('#company_row_'+companyId).after(response);
            }
        });
    }
}

function removeCompaniesFromSegment(segmentId, companyIds){
    var ids = {companyIds: companyIds};

    $.ajax({
        url:'/segment/'+segmentId+'/removeCompanies',
        type:'post',
        data: JSON.stringify(ids),
        contentType: "application/json; charset=utf-8",
        success:function(response){

            for(const x of companyIds){
                // update table on segment config page (in case removed from there)
                let rowToBeDeleted = document.getElementById('targetCompany_'+x);
                if (rowToBeDeleted != null) {
                    rowToBeDeleted.remove();
                }

                //reload details on dashboard (in case removed from there)
                if (openedRow==x && openedDetail=="segments"){
                    openedRow=null;
                    showSegments(x);
                }
            }
            // update dashboard segment color codes
            loadSegments();
        }
    });
};

function addCompaniesToSegment(segmentId, companyIds){
    var ids = {companyIds: companyIds};

    $.ajax({
        url:'/segment/'+segmentId+'/addCompanies',
        type:'post',
        data: JSON.stringify(ids),
        contentType: "application/json; charset=utf-8",
        success:function(response){
            for(const x of companyIds){
                //update details on dashboard (in case one is opened)
                if (openedRow==x && openedDetail=="segments"){
                    openedRow=null;
                    showSegments(companyId);
                }
            }
            // update dashboard segment color codes
            loadSegments();
        }
    });
};