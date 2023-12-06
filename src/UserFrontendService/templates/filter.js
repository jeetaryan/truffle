{% set dict_attributeType = ["string", "integer", "double", "date", "time", "datetime", "boolean"] %}
{% set dict_attributeInput = ["text", "number", "textarea", "radio", "checkbox", "select"] %}
{% set dict_attributeOperators = ["equal", "not_equal", "in", "not_in", "less", "less_or_equal", "greater", "greater_or_equal",
    "between", "not_between", "begins_with", "not_begins_with", "contains", "not_contains", "ends_with",
    "not_ends_with", "is_empty", "is_not_empty", "is_null", "is_not_null"] %}

function loadSegmentFilter(segmentId){
    var options = {
        allow_empty: true,
        filters: [
    {% for a in attributes %}
            {
                label: '{{a.label}}',
                {% if a.size is defined and a.size is not none and not a.size == "" %}
                size: {{a.size}},
                {% endif %}
                {% if a.optgroup is not none %}
                optgroup: '{{a.optgroup}}',
                {% endif %}
                {% if a.rows is not none %}
                rows: {{a.rows}},
                {% endif %}
                {% if a.multiple is not none %}
                multiple: {{a.multiple}},
                {% endif %}
                {% if a.placeholder is not none %}
                placeholder: '{{a.placeholder}}',
                {% endif %}
                {% if a.vertical is not none %}
                vertical: {{a.vertical}},
                {% endif %}
                {% if a.validation is not none %}
                validation: '{{a.validation}}',
                {% endif %}
                {% if a.default_value is not none %}
                default_value: '{{a.default_value}}',
                {% endif %}
                {% if a.attributeInput is not none %}
                input: '{{dict_attributeInput[a.attributeInput]}}',
                {% endif %}
                {% if a.attributeType is not none %}
                type: '{{dict_attributeType[a.attributeType]}}',
                {% endif %}
                {% if a.default_operator is not none %}
                default_operator: '{{dict_attributeOperators[a.default_operator]}}',
                {% endif %}
                {% for o in a.operators %}{% if loop.first %}operators: [{% else %},{% endif %}'{{dict_attributeOperators[o]}}'{% if loop.last %}],{% endif %}{% endfor %}
                values: {{a.values}},
                id: '{{a.attributeId}}'
            }
            {% if not loop.last %},{% endif %}
    {% endfor %}
        ]
    };

    $('#filterBuilder').queryBuilder(options);
    $('#filterBuilder').queryBuilder('reset');

    if (segmentId != null) {
        $.ajax({
            url:'segment/'+segmentId+'/getFilter',
            type:'post',
            data: JSON.stringify({}),
            contentType: "application/json; charset=utf-8",
            success:function(response){
                if (response != ''){
                    $('#filterBuilder').queryBuilder('setRules', response.filter );
                }
            }
        });
    }
}


$('#replaceTargetsByFilter').on('click', function(){
    segmentId = $('#segmentId').text();
    //<!-- modal confirmation -->

    $.ajax({
        url: '/segment/'+segmentId+'/setFilter',
        type:'post',
        data: JSON.stringify({"filter": $('#filterBuilder').queryBuilder('getRules'), "replaceTargets": true, "autoUpdate": true}, undefined, 2),
        contentType: "application/json; charset=utf-8",
        success:function(response){
            //console.log(response);
            loadTargetCompanies(segmentId);
        }
    });
});

$('#addTargetsByFilter').on('click', function(){
    segmentId = $('#segmentId').text();
    //<!-- modal confirmation -->
    $.ajax({
        url: '/segment/'+segmentId+'/setFilter',
        type:'post',
        data: JSON.stringify({"filter": $('#filterBuilder').queryBuilder('getRules'), "replace": false, "autoUpdate": true}, undefined, 2),
        contentType: "application/json; charset=utf-8",
        success:function(response){
            //console.log(response);
            loadTargetCompanies(segmentId);
        }
    });
});