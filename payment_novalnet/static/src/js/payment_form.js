odoo.define('payment_novalnet.payment_form', require => {
    'use strict';

    const core = require('web.core');
    const _t = core._t;
    const checkoutForm = require('payment.checkout_form');
    const Dialog = require('web.Dialog');

    var noval_cc_obj = new Object();
    const novalnetMixin = {



      start: async function () {
        await this._super(...arguments);
        noval_cc_obj = this;
        console.log(noval_cc_obj);
        this._createCredicardComponent();

      },

      _processPaymentRequest: function (code, paymentOptionId, flow, nnPaymentData) {
          return this._rpc({
              route: this.txContext.transactionRoute,
              params: this._prepareTransactionRouteParams(code, paymentOptionId, flow, nnPaymentData),
          }).then(processingValues => {
            console.log(processingValues);
              if (flow === 'redirect') {

                  return this._processRedirectPayment( code, paymentOptionId, processingValues );
              } else if (flow === 'direct' || flow === 'token') {

                  return this._processDirectPayment(code, paymentOptionId, processingValues);
              }
          }).guardedCatch(error => {
              error.event.preventDefault();
              noval_cc_obj._displayError(
                  _t("Server Error"),
                  _t("We are not able to process your payment."),
                  error.message.data.message
              );
          });

      },

      _createCredicardComponent: function(){
              var ccContainer = this.$(`[id="demo-container-cc-novalnet"]`);
              var clientToken = ccContainer.data('token');
              console.log(ccContainer.data('partner-name'));
              if(!clientToken) return;
              NovalnetUtility.setClientKey(clientToken);
              var configurationObject = {
              // You can handle the process here, when specific events occur.
              callback: {
                // Called once the pan_hash (temp. token) created successfully.
                on_success: function (data) {
                  const radio = noval_cc_obj.$('input[name="o_payment_radio"]:checked');
                  const code = noval_cc_obj._getProviderFromRadio(radio);
                  const paymentOptionId = $(radio).data('provider-id');

                  var flow = 'direct'
                  var payData = {
                            'pan_hash':data ['hash'],
                            'unique_id':data ['unique_id']
                          }
                  if (data ['do_redirect']=="1")
                  {
                      payData['enforce_3d'] = 1
                      flow = 'redirect'
                  }

                  const nnPaymentData = {'providerPaymentMethodId':noval_cc_obj._getPaymentOptionIdFromRadio(radio),'paydata':payData};
                  return noval_cc_obj._processPaymentRequest(code, paymentOptionId, flow, nnPaymentData);

                },

                // Called in case of an invalid payment data or incomplete input.
                on_error:  function (data) {
                  console.log(data);
                  if ( undefined !== data['error_message'] ) {
                    noval_cc_obj._displayError(_t(data['error_message']), _t(data['error_message']))
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
              customer: {

                    first_name: ccContainer.data('partner-name'),

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
                    place_holder: 'Name on the card',

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
                amount: this.txContext.amount ? parseFloat(this.txContext.amount) : undefined,

                // The three-character currency code as defined in ISO-4217.
                currency: this.txContext.currencyId ? parseInt(this.txContext.currencyId)   : undefined,
                enforce_3d: ccContainer.data('3d') ? 1 : 0,

                // Set to 1 for the TEST transaction (default - 0).
                test_mode: 1
              },
            };
            console.log(configurationObject);
            // Create the Credit Card form
            NovalnetUtility.createCreditCardForm(configurationObject);

      },

      _prepareInlineForm: function (code, paymentOptionId, flow) {
        const radio = this.$('input[name="o_payment_radio"]:checked');
        this._setPaymentFlow($(radio).data('payment-flow'));
      },

      _processDirectPayment: function (code, providerId, processingValues) {
          if (code !== 'novalnet') {
              return this._super(...arguments);
          }
          return this._rpc({
              route: '/payment/novalnet/simulate_payment',
              params: processingValues,
          }).then(() => {
              window.location = '/payment/status';
          });
      },
      _processTokenPayment: function (code, providerId, processingValues) {
          if (code !== 'novalnet') {
              return this._super(...arguments);
          }
          return this._rpc({
              route: '/payment/novalnet/simulate_payment',
              params: processingValues,
          }).then(() => {
              window.location = '/payment/status';
          });
      },

      _onClickPay: async function (ev) {
          ev.stopPropagation();
          ev.preventDefault();

          // Check that the user has selected a payment option
          const $checkedRadios = this.$('input[name="o_payment_radio"]:checked');
          if (!this._ensureRadioIsChecked($checkedRadios)) {
              return;
          }
          const checkedRadio = $checkedRadios[0];

          // Extract contextual values from the radio button
          const provider = this._getProviderFromRadio(checkedRadio);

          if (provider !== 'novalnet') {
              return this._super(...arguments); // Tokens are handled by the generic flow
          }

          const paymentOptionId = this._getPaymentOptionIdFromRadio(checkedRadio);
          const flow = this._getPaymentFlowFromRadio(checkedRadio);

          // Update the tx context with the value of the "Save my payment details" checkbox
          if (flow !== 'token') {
              const $tokenizeCheckbox = this.$(
                  `#o_payment_${provider}_inline_form_${paymentOptionId}` // Only match provider radios
              ).find('input[name="o_payment_save_as_token"]');
              this.txContext.tokenizationRequested = $tokenizeCheckbox.length === 1
                  && $tokenizeCheckbox[0].checked;
          } else {
              this.txContext.tokenizationRequested = false;
          }

          // Make the payment
          this._hideError(); // Don't keep the error displayed if the user is going through 3DS2
          this._disableButton(true); // Disable until it is needed again
          $('body').block({
              message: false,
              overlayCSS: {backgroundColor: "#000", opacity: 0, zIndex: 1050},
          });
          this._processPayment(provider, paymentOptionId, flow);
      },

      _getNovalnetPaymentMethod: radio => $(radio).data('payment-method'),

      _prepareTransactionRouteParams: function (provider, paymentOptionId, flow, payData) {
          const transactionRouteParams = this._super(provider, paymentOptionId, flow);
          if (provider !== 'novalnet') {
              return transactionRouteParams;
          }
          return {...transactionRouteParams,...payData};
      },

      _ibanValidation: function(code,paymentMethod){
        console.log(`[name="${code}-${paymentMethod}-iban"]`);
        var ibanField = this.$(`[name="${code}-${paymentMethod}-iban"]`);
        if (undefined !== ibanField){
            console.log(ibanField.val());
            if (undefined === ibanField.val() || ''=== ibanField.val()) {
              ibanField.addClass("is-invalid");
              this._displayError(_t('ValidationError'), _t('Missing Iban'));
              return false;
            }
            var iban = NovalnetUtility.formatAlphaNumeric( ibanField.val() );
            if ('' === iban) {
              ibanField.addClass("is-invalid")
              this._displayError(_t('ValidationError'), _t('IBAN validation failed'));
              return false;
            }
        }
        return ibanField.val();
      },
      _bicValidation:function(code,paymentMethod,ibanValidateval){
        var bicField = this.$(`[name="${code}-${paymentMethod}-bic"]`);
        if (undefined !== bicField){
            console.log(bicField.val());
              var iban = ibanValidateval.substring( 0, 2 );

      				if ( ['CH', 'MC', 'SM', 'GB'].includes( iban.toUpperCase() ) ) {
                  if (undefined === bicField.val() || ''=== bicField.val()) {
                    bicField.addClass("is-invalid");
                    this._displayError(_t('ValidationError'), _t('Missing BIC'));
                    return false;
                  }
                  return bicField.val();
      			}
        }
        return true;
      },

      _dobValidation:function (code, paymentMethod) {
        var dobField = this.$(`[name="${code}-${paymentMethod}-dob"]`);
        if ( dobField.length && undefined !== dobField){
            if (undefined === dobField.val() || ''=== dobField.val()) {
              dobField.addClass("is-invalid");
              this._displayError(_t('ValidationError'), _t('Missing DOB'));
              return false;
            }
            return dobField.val();
        }
        return true;
      },

      async _processPayment(code, paymentOptionId, flow) {
        if (code !== 'novalnet' || flow === 'token') {
            return this._super(...arguments); // Tokens are handled by the generic flow
        }
        const radio = this.$('input[name="o_payment_radio"]:checked');
        const paymentMethod = this._getNovalnetPaymentMethod(radio);
        let novalnetPaymentData = {}
        if (paymentMethod == 'CREDITCARD') {
            event.preventDefault();
            event.stopImmediatePropagation();
            NovalnetUtility.getPanHash();
        }
        else {
          var nnPaymentData = {'providerPaymentMethodId':noval_cc_obj._getPaymentOptionIdFromRadio(radio)};

          if (['DIRECT_DEBIT_SEPA','GUARANTEED_DIRECT_DEBIT_SEPA'].includes(paymentMethod)){
              var ibanValidateval = this._ibanValidation( code,paymentMethod );
              if (!ibanValidateval) return false ;
              var bicValidateval = this._bicValidation( code,paymentMethod, ibanValidateval );
              console.log(bicValidateval);
              if (!bicValidateval) return false ;
              nnPaymentData['paydata'] = { 'iban': ibanValidateval};
              if (bicValidateval!= true && ''!== bicValidateval) nnPaymentData['paydata']['bic'] =   bicValidateval;
          }

          console.log(paymentMethod);
          if(['GUARANTEED_DIRECT_DEBIT_SEPA','GUARANTEED_INVOICE'].includes(paymentMethod))
          {
              var dobValidateval = this._dobValidation( code, paymentMethod );
              if (!dobValidateval) return false ;
              console.log(dobValidateval);
              if (dobValidateval!= true && ''!== dobValidateval) nnPaymentData['birth_date'] = dobValidateval;
          }

          paymentOptionId = $(radio).data('provider-id');
          return this._processPaymentRequest(code,paymentOptionId,flow,nnPaymentData)

        }
      },
    };
    checkoutForm.include(novalnetMixin);
});
