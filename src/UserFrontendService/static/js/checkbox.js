var actionsShown = false;
var table = null;

function hideActions(){
    $("#addToSegmentDropdown").hide();
    $("#removeFromSegmentDropdown").hide();
    $("#deleteCompaniesButton").hide();
    $("#selectedCompaniesInfo").text("")
    actionsShown = false;
}

function showActions(){
    //if at least one checkbox selected
    selectedCompanies = getSelectedCompanies();
    if (selectedCompanies.length>0){
        $("#selectedCompaniesInfo").text(selectedCompanies.length + " Unternehmen ausgewählt.")
        if (actionsShown == false){
            $("#addToSegmentDropdown").show();
            $("#removeFromSegmentDropdown").show();
            $("#deleteCompaniesButton").show();
            actionsShown = true;
        }
    } else {
        hideActions();
    }
}

function getSelectedCompanies(){
    selectedCompanies = [];

    // Get all rows with search applied
    var rows = table.rows({ 'search': 'applied' }).nodes();
    $('.companySelection:checkbox:checked', rows).each(function() {
       selectedCompanies.push($(this).val());
    });
    console.log(selectedCompanies);
    return selectedCompanies;
}

function deselectAll(){
    var rows = table.rows({ 'search': 'applied' }).nodes();
    $('.companySelection:checkbox:checked', rows).prop('checked', false);
    $('#select_all').prop('checked', false);
    $('#select_current').prop('checked', false);
    $('#addToSegmentDropdown').val(-1);
    $('#removeFromSegmentDropdown').val(-1);
    hideActions();
}

function loadSegmentDropdownsForDashboard(){
    $.ajax({
        url:'/getSegments',
        type:'get',
        data:{},
        success:function(response){
            $('#addToSegmentDropdown').empty();
            $('#addToSegmentDropdown').append('<option value="-1" selected="selected">Zu Segment hinzufügen</select>');
            jsonobj = JSON.parse(response);
            $('#addToSegmentDropdown').append(jsonobj.map(function(sObj){
                return '<option value=' + sObj.id + '>' + sObj.name + '</option>';
            }));

            $('#removeFromSegmentDropdown').empty();
            $('#removeFromSegmentDropdown').append('<option value="-1" selected="selected">Aus Segment entfernen</select>');
            jsonobj = JSON.parse(response);
            $('#removeFromSegmentDropdown').append(jsonobj.map(function(sObj){
                return '<option value=' + sObj.id + '>' + sObj.name + '</option>';
            }));
        }
    });
}


$(document).ready(function() {
    hideActions();
    loadSegmentDropdownsForDashboard();

    $(".companySelection").click(function () {
        showActions();
    });

    //check the all checkboxes on current page #############################
    $("#select_current").click(function () {
       $(".companySelection").prop("checked", this.checked);
       showActions();
    });

    //check the all checkboxes of all pages #############################
    $('#select_all').click(function(){
      // Get all rows with search applied
      var rows = table.rows({ 'search': 'applied' }).nodes();
      $('input[type="checkbox"]', rows).prop('checked', this.checked);
      $('#select_current').prop('checked', this.checked);
      showActions();
    });

    $("#addToSegmentDropdown").change(function() {
        segmentId = $("#addToSegmentDropdown").val();
        if (segmentId != -1){
            companyIds = getSelectedCompanies();
            addCompaniesToSegment(segmentId, companyIds);
            deselectAll();
        }
    });

    $("#removeFromSegmentDropdown").change(function() {
        segmentId = $("#removeFromSegmentDropdown").val();
        if (segmentId != -1){
            companyIds = getSelectedCompanies();
            removeCompaniesFromSegment(segmentId, companyIds);
            deselectAll();
        }
    });

    $("#deleteCompaniesButton").click(function() {
        alert("sicher?");
        //TODO
    });
});

