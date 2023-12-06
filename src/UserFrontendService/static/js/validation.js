
$(document).ready(function(){
    const forms = document.querySelectorAll('.t1-validate-form')
    Array.from(forms).forEach(form => {
        $( "#" + form.id).on( "submit", function( event ) {
            //validate input fields
            elements = $("#"+event.target.id+" .t1-validate")
            for (let i = 0; i < elements.length; i++) {
                if (!validate(elements[i].id)){
                    event.preventDefault();
                    event.stopPropagation();
                    let msg = $("#" + elements[i].id).attr('validation-msg')
                    $("#" + msg).show();
                } else {
                    let msg = $("#" + elements[i].id).attr('validation-msg')
                    $("#" + msg).hide();
                }
            }

            //validate passwords to match if need to be provided twice
            elements = $("#"+event.target.id+" .t1-validateMatch")
            if (elements.length >0){
                element = match_password(elements)
                if (element != null) {
                    event.preventDefault();
                    event.stopPropagation();
                    let msg = $("#" + element.id).attr('validation-msg')
                    $("#" + msg).show();
                }
            }
        });
    })
})

$(document).ready(function(){
    fields = document.querySelectorAll('.t1-validate')
    Array.from(fields).forEach(field => {
        $( "#" + field.id).on( "keyup", function( event ) {
            if (!validate(field.id)){
                field.form.querySelector('button[type="submit"]').disabled=true;
                let msg = $("#" + field.id).attr('validation-msg')
                $("#" + msg).show();
            } else {
                field.form.querySelector('button[type="submit"]').disabled=false;
                let msg = $("#" + field.id).attr('validation-msg')
                $("#" + msg).hide();
            }

        });
    })

    fields = document.querySelectorAll('.t1-validateMatch')
    Array.from(fields).forEach(field => {
        $( "#" + field.id).on( "keyup", function( event ) {
            //validate passwords to match if need to be provided twice
            elements = $("#"+event.target.id+" .t1-validateMatch")
            element = match_password(elements)
            if (element != null) {
                field.form.querySelector('button[type="submit"]').disabled=true;
                let msg = $("#" + field.id).attr('validation-msg')
                $("#" + msg).show();
            } else {
                field.form.querySelector('button[type="submit"]').disabled=false;
                let msg = $("#" + field.id).attr('validation-msg')
                $("#" + msg).hide();
            }

        });
    })
})

$(document).ready(function(){
    const fields = document.querySelectorAll('.t1-validate')
    Array.from(fields).forEach(field => {
        $( "#" + field.id).on( "keyup", function( event ) {
            if (!validate(field.id)){
                field.form.querySelector('button[type="submit"]').disabled=true;
                let msg = $("#" + field.id).attr('validation-msg')
                $("#" + msg).show();
            } else {
                field.form.querySelector('button[type="submit"]').disabled=false;
                let msg = $("#" + field.id).attr('validation-msg')
                $("#" + msg).hide();
            }

        });
    })
})



function validate(elementid){
    let element = $("#" + elementid);
    let type = element.attr('type');
    if (type === "email"){
        let text = element.val().toLowerCase();
        const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/u;
        return regex.test(text);
    } else if (type === "password"){
        let text = element.val();
        const regex = /^(?=.*[A-Za-züöäÜÖÄ])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-züöäÜÖÄ\d@$!%*#?&]{8,}$/;
        return regex.test(text);
    } else if (type === "checkbox"){
        return element.is(':checked')
    }
    return true;
}

function match_password(elements){
    if (elements.length > 0) {
        base = elements[0].value
        for (let i = 1; i < elements.length; i++) {
            if (elements[i].value != base){
                return elements[i];
            }
        }
    }
    return true;
}