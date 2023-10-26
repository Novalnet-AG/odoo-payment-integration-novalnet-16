
(function($){

	wc_novalnet_cc = {
    init : function() {
          NovalnetUtility.setClientKey("0f84e6cf6fe1b93f1db8198aa2eae719");
          var configurationObject = {

          // You can handle the process here, when specific events occur.
          callback: {

            // Called once the pan_hash (temp. token) created successfully.
            on_success: function (data) {
              document.getElementById('pan-hash').value = data ['hash'];
              document.getElementById('unique-id').value = data ['unique_id'];
              document.getElementById('do-redirect').value = data ['do_redirect'];
              return true;
            },

            // Called in case of an invalid payment data or incomplete input.
            on_error:  function (data) {
              if ( undefined !== data['error_message'] ) {
                alert(data['error_message']);
                console.log(this);
                // novalnetMixin._displayNovalnetError(_t("No payment option selected"), _t("Please select a payment option."))
                return false;
              }
            },

            // Called in case the Challenge window Overlay (for 3ds2.0) displays
            on_show_overlay:  function (data) {
              document.getElementById('novalnet_iframe').classList.add(".overlay");
            },

            // Called in case the Challenge window Overlay (for 3ds2.0) hided
            on_hide_overlay:  function (data) {
              document.getElementById('novalnet_iframe').classList.remove(".overlay");
            }
          },

          // You can customize your Iframe container styel, text etc.
          iframe: {

            // It is mandatory to pass the Iframe ID here.  Based on which the entire process will took place.
            id: "novalnet_iframe",

            // Set to 1 to make you Iframe input container more compact (default - 0)
            inline: 1,

            // You can customize the text of the Iframe container here
            text: {

              // The End-customers selected language. The Iframe container will be rendered in this Language.
              lang : "EN",

              // Basic Error Message
              error: "Your credit card details are invalid",

              // You can customize the text for the Card Holder here
              card_holder : {

                // You have to give the Customized label text for the Card Holder Container here
                label: "Card holder name",

                // You have to give the Customized placeholder text for the Card Holder Container here
                place_holder: "Name on card",

                // You have to give the Customized error text for the Card Holder Container here
                error: "Please enter the valid card holder name"
              },
              card_number : {

                // You have to give the Customized label text for the Card Number Container here
                label: "Card number",

                // You have to give the Customized placeholder text for the Card Number Container here
                place_holder: "XXXX XXXX XXXX XXXX",

                // You have to give the Customized error text for the Card Number Container here
                error: "Please enter the valid card number"
              },
              expiry_date : {

                // You have to give the Customized label text for the Expiry Date Container here
                label: "Expiry date",

                // You have to give the Customized error text for the Expiry Date Container here
                error: "Please enter the valid expiry month / year in the given format"
              },
              cvc : {

                // You have to give the Customized label text for the CVC/CVV/CID Container here
                label: "CVC/CVV/CID",

                // You have to give the Customized placeholder text for the CVC/CVV/CID Container here
                place_holder: "XXX",

                // You have to give the Customized error text for the CVC/CVV/CID Container here
                error: "Please enter the valid CVC/CVV/CID"
              }
            }
          },

          // Add transaction data
          transaction: {

            // The payable amount that can be charged for the transaction (in minor units), for eg:- Euro in Eurocents (5,22 EUR = 522).
            amount: 10,

            // The three-character currency code as defined in ISO-4217.
            currency: 'EUR',

            // Set to 1 for the TEST transaction (default - 0).
            test_mode: 1
          },
        };

        // Create the Credit Card form
        NovalnetUtility.createCreditCardForm(configurationObject);
    }

  };
  $( document ).ready(
      function () {

        const checkoutForm = require('payment.checkout_form');
        console.log(checkoutForm);
        wc_novalnet_cc.init();
      }
  );

})( jQuery );
