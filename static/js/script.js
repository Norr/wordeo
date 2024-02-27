$(document).ready(function(){
  //================================= REGISTRATION FORM ========================
$("form#registrationForm").on("submit", function(e){
  $(this).addClass("was-validated")
  e.preventDefault();
  var oData = $(this).serializeArray();
  email = oData[0].value.replaceAll(" ", "")
  username = oData[1].value.replaceAll(" ", "")
  password = oData[2].value
  verify_password = oData[3].value
  if (!$(this).find("input").hasClass("is-invalid") && email != "" && username != "" & password != "" && verify_password != ""){
    grecaptcha.ready(function() {
      grecaptcha.execute('6Lfij3wpAAAAADzTgsttbGcHDJlkRaw3BQpWHNMB', {action: 'submit'}).then(function(token) {
        $.post( "https://wordeo.eu/auth/register", { email: email, username: username, password: password, verify_password:  verify_password, token:token} )
        .done(function(){
          //<button class="btn btn-primary registrButton" type="submit">Register</button>
          $("form#registrationForm").trigger("reset");
          $(".closeButton").trigger("click");
          $(".user_created").fadeIn().delay(3000).fadeOut()
        })
        
      });
    });
  
   
  } else {
    console.log("Nie ok")
  }
  
  

  // $.ajax({
  //   type: "POST",
  //   url: "/auth/register",
  //   data: {email: email, username: username, password: password, verify_password:verify_password}
  // })

  // $.post( "/auth/register", { email: email, username: username, password: password, verify_password:  verify_password} );

})

$("#registrationFormEmail").on("focusout", function(){
    $(this).checkEmail()

})
$("#registrationFormUsername").on("focusout", function(){
  $(this).checkUsername()

})

$("#registrationFormPasswordVerify").on("keyup", function(){
  $(this).verifyPassword()

})

$('#registrationFormPassword').on("keyup", function(){
  $(this).passwordRequirements()
});
 $('#registrationFormPassword').on("focus", function() {
    $(".passwordVerification").fadeIn()
 });
 $('#registrationFormPassword').on("blur", function() {
  $(".passwordVerification").fadeOut()
 });




  // ===========================================================================
  //============================ NAVIGATION TABS =============================
  /*
  
  
  */
  $(".nav-link").on("click", function(){
    $(".nav-link").removeClass("active")
    $(this).addClass("active")
    $("div.home-content > div").hide()
    $("div.home-content div." + $(this).attr("id")).show()   
    
  });

  //===========================================================================
    $(".translate_from button, .translate_to button").on("click", function(){
      //$('div:contains("test"):not(:has(*))')
      id = $(this).text()
      parent = $(this).parent("div").prop("classList")[1]
      if (parent == "translate_to"){
        oposite = "translate_from"
      } else {
        oposite = "translate_to"
      }
      //$(this).addClass("active")
      $("." + parent + " button.active").removeClass("active")
      $("." + oposite + " button.disabled").removeClass("disabled")
      if(!$("." + parent + " > button").hasClass("disabled"))
        $("." + oposite + " button:contains('" + id + "'):not(:has(*))").addClass("disabled")
      //tdo jak jest disabled to ma klasę aktive
      $(this).addClass("active")
      
   
    })
    $(".translate_button").on("click", function(){
      src_lang = $(".translate_from button.active").text()
      target_lang = $(".translate_to button.active").text()
      word = $(".word_to_translate").val()
      
      if (src_lang != "" && target_lang != "" && word != ""){
        ///{word}/{source_lang}/{target_lang}
        $.getJSON("/translate/" + word +"/" + src_lang + "/" + target_lang, function(result){
          
          if (result.translation.error != undefined){
            alert(result.translation.error)
            } else {
            result.translation.forEach(function(value, index) {         
              if (index == 0){
                $(".translation-block-text").text(value)
                if(result.translation.length > 1){
                  $('<div class="alternatives"><h2 class="decorated"><span>Alternatives</span></h2><ul></ul></div>').appendTo(".translation-block-text")
                }
              } else {
                $(".alternatives ul").append("<li>" + value + "</li>")
              }
            });
        }
                 
      })
      } else if (word == ""){
        alert("Type what you want to translate.")
      } else {
        alert("Languages for translation are not selected.")
      }

    })

    $(".game_languages button").on("click", function(){

      $(this).toggleClass("active");
      if($(".game_languages button.active").length > 1){
        $(".start-game-btn").removeClass("disabled")
      } else {
        if (!$(".start-game-btn").hasClass("disabled")){
          $(".start-game-btn").addClass("disabled")
        }
      }

    })

    $("button.start-game-btn").on("click", function(){
      $(".bubble-dices").show()
      if ($(".game_languages button.active").length == 2) {
        languages = $(".game_languages button.active").toArray()
        lang_1 = $(languages[0]).text()
        lang_2 = $(languages[1]).text()
           
      ///{src_lang}/{target_lang}/{nr_words}
        $.getJSON("/game/" + lang_1 +"/" + lang_2 + "/" + 4, function(result){
          $(".bubble-dices").hide()
          $(".game-word").html(result.word)
          $(".game-options").html('')
          for (var key in result.words_bag){
            $(".game-options").append('<div class="col option ' + result.words_bag[key] + '"> ' + key + '</div>')
          
          }
      })
      } else {
        $(".game_languages button.active").eq(1).remoceClass("active")
      }
      

    })

    $(document).on("click", ".game-options .option", function(){
      
        if($(this).hasClass("correct")){
          $(".bubble-ok").fadeIn(100)
          $(".bubble-ok").delay(1000).fadeOut(100)
          
          $.post('/game/action/add', function(result){
            $(".user-points").html(result.coin_count)
            $(".start-game-btn").trigger("click");
            
          })
        } else if($(this).hasClass("incorrect")){
          $(".bubble-wrong").fadeIn(100)
          $(".bubble-wrong").delay(1000).fadeOut(100)
          $.post('/game/action/substract', function(result){
            $(".user-points").html(result.coin_count)
          })
        }
    })


//================================ functions ============================

function alert(text){
  $(".alert").html(text)
  $(".alert").slideDown().delay(5000).slideUp()
}


});

//jQuery functions
jQuery.fn.extend({

  // check checkboxes
  checkEmail: function() {
    if(/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(this.val())) {
      $(this).val($(this).val().replaceAll(" ", ""))
      element = $(this).attr("id")
      $.getJSON("/auth/check_email/" + this.val(), function(responseData){
        
        if (responseData.result == "email exists"){
          $("#" + element).removeClass('is-valid')          
          $("#" + element).addClass('is-invalid')
          $("span.emailInvalidFeedback").html("Email exists, please choose diffrent one.")
        } else {
          $("#" + element).removeClass('is-invalid')
          $("#" + element).removeClass('is-valid')
        }

      })
      
    } else {
      $(this).addClass('is-invalid')
      $("span.emailInvalidFeedback").html("Invalid email")
    }
  },
  checkUsername: function() {
    if(/^[A-z0-9]{4,10}?$/.test(this.val())) {
      element = $(this).attr("id")
      $.getJSON("/auth/check_username/" + this.val(), function(responseData){
        console.log(element, responseData)
        if (responseData.result == "username exists"){   
          $("#" + element).removeClass('is-valid')       
          $("#" + element).addClass('is-invalid')
          $("span.usernameInvalidFeedback").html("Username exists, please choose diffrent username.")
        } else if (responseData.result == "invalid username"){
          $("#" + element).removeClass('is-valid')
          $("#" + element).addClass('is-invalid')
          $("span.usernameInvalidFeedback").html("Invalid username.")
        } else {
          $("#" + element).removeClass('is-invalid')
          $("#" + element).addClass('is-valid')
          $("span.usernameInvalidFeedback").html("Invalid username.")
        }

      })
      
    } else {
      console.log("Invalid")
      $(this).removeClass('is-valid')
      $(this).addClass('is-invalid')
      $("span.usernameInvalidFeedback").html("Invalid username")
    }
  },
  verifyPassword: function() {
    var passwd = $("#registrationFormPassword").val()
    if ($(this).val() != passwd){
      $(this).removeClass("is-valid")
      $(this).addClass("is-invalid")
    } else {
      $(this).removeClass("is-invalid")
      $(this).addClass("is-valid")
    }
  },
  passwordRequirements: function() {
    //invalidPasswordRule
    //validPasswordRule
    var charactersLength = false
    var spaces = false
    var capitalLetter = false
    var number = false
    var special_character = false
  
      $(this).addClass("is-invalid")
      var passwordValue = $(this).val()
      if (passwordValue.length < 8 || passwordValue.length>32){
        var charactersLength = false      
        $(".passwordRequirementsSize").removeClass("validPasswordRule")
        $(".passwordRequirementsSize").addClass("invalidPasswordRule")
      }  else {
        var charactersLength = true   
        $(".passwordRequirementsSize").removeClass("invalidPasswordRule")
        $(".passwordRequirementsSize").addClass("validPasswordRule")
      }
  
      if (passwordValue.match(/ /)){
        var spaces = false
        $(".passwordRequirementsSpaces").removeClass("validPasswordRule")
        $(".passwordRequirementsSpaces").addClass("invalidPasswordRule")
        //passwordRequirementsSpaces
      } else {
        var spaces = true
        $(".passwordRequirementsSpaces").removeClass("invalidPasswordRule")
        $(".passwordRequirementsSpaces").addClass("validPasswordRule")
      }
  
      if (!passwordValue.match(/[A-Z]/)){
        var spaccapitalLetter = false
        $(".passwordRequirementsCapitalLeter").removeClass("validPasswordRule")
        $(".passwordRequirementsCapitalLeter").addClass("invalidPasswordRule")
        //passwordRequirementsSpaces
      } else {
        var capitalLetter = true
        $(".passwordRequirementsCapitalLeter").removeClass("invalidPasswordRule")
        $(".passwordRequirementsCapitalLeter").addClass("validPasswordRule")
      }
  
      if (!passwordValue.match(/[0-9]/)){
        var number = false
        $(".passwordRequirementsNumber").removeClass("validPasswordRule")
        $(".passwordRequirementsNumber").addClass("invalidPasswordRule")
        //passwordRequirementsSpaces
      } else {
        var number = true
        $(".passwordRequirementsNumber").removeClass("invalidPasswordRule")
        $(".passwordRequirementsNumber").addClass("validPasswordRule")
      }
      if (!passwordValue.match(/[~\!@#\$%\^\&\*\(\)\-_\=\+\[\{\}\]\\\|;\:\'",<.>\/\?\€\£\¥\₹]/)){
        var special_character = false
        $(".passwordRequirementsSpecialCharacters").removeClass("validPasswordRule")
        $(".passwordRequirementsSpecialCharacters").addClass("invalidPasswordRule")
        //passwordRequirementsSpaces
      } else {
        var special_character = true
        $(".passwordRequirementsSpecialCharacters").removeClass("invalidPasswordRule")
        $(".passwordRequirementsSpecialCharacters").addClass("validPasswordRule")
      }
      
      if (charactersLength && spaces && capitalLetter && number && special_character){
        $(this).removeClass("is-invalid")
        $(this).addClass("is-valid")
      }
  
      //~\!@#\$%\^\&\*\(\)\-_\=\+\[\{\}\]\\\|;\:\'",<.>\/\?\€\£\¥\₹
  }

});