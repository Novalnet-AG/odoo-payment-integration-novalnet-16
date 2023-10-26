PAYMENT_FLOW = {
    'ALIPAY' : 'redirect',
    'BANCONTACT' : 'redirect',
    'CASHPAYMENT' : 'direct',
    'CREDITCARD' : 'direct',
    'DIRECT_DEBIT_SEPA' : 'direct',
    'EPS' : 'redirect',
    'GIROPAY' : 'redirect',
    'GUARANTEED_DIRECT_DEBIT_SEPA' : 'direct',
    'GUARANTEED_INVOICE' : 'direct',
    'IDEAL' : 'redirect',
    'MULTIBANCO' : 'direct',
    'ONLINE_BANK_TRANSFER' : 'redirect',
    'ONLINE_TRANSFER' : 'redirect',
    'PAYPAL' : 'redirect',
    'POSTFINANCE' : 'redirect',
    'POSTFINANCE_CARD' : 'redirect',
    'PRZELEWY24' : 'redirect',
    'TRUSTLY' : 'redirect',
    'WECHATPAY' : 'redirect',
    'INVOICE' : 'direct',
    'PREPAYMENT' : 'direct',
}

PAYMENT_NAME = {
    "ALIPAY": {
        "lang": {"en_US": "Alipay", "de_DE": "Alipay"},
        "description": {"en_US": "You will be redirected to Alipay. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu Alipay weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist."},
    },
    "BANCONTACT": {
        "lang": {"en_US": "Bancontact", "de_DE": "Bancontact"},
        "description": {"en_US": "You will be redirected to Bancontact. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu Bancontact weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "CASHPAYMENT": {
        "lang": {"en_US": "Barzahlen/viacash", "de_DE": "Barzahlen/viacash"},
        "description": {"en_US": "On successful checkout, you will receive a payment slip/SMS to pay your online purchase at one of our retail partners (e.g. supermarket)", "de_DE": "Nach erfolgreichem Bestellabschluss erhalten Sie einen Zahlschein bzw. eine SMS. Damit können Sie Ihre Online-Bestellung bei einem unserer Partner im Einzelhandel (z.B. Drogerie, Supermarkt etc.) bezahlen"},
    },
    "CREDITCARD": {
        "lang": {"en_US": "Credit/Debit Cards", "de_DE": "Kredit- / Debitkarte"},
        "description": {"en_US": "Your credit/debit card will be charged immediately after the order is completed", "de_DE": "Ihre Karte wird nach Bestellabschluss sofort belastet"},
    },
    "DIRECT_DEBIT_SEPA": {
        "lang": {"en_US": "Direct Debit SEPA", "de_DE": "SEPA-Lastschrift"},
        "description": {"en_US":"""<ul>
    <li>The amount will be debited from your account by Novalnet</li>
    <li><a id="novalnet_guaranteed_sepa_mandate" style="cursor:pointer;text-decoration: underline;" onclick="jQuery('#novalnet_guaranteed_sepa_about_mandate').toggle('slow')">I hereby grant the mandate for the SEPA direct debit (electronic transmission) and confirm that the given bank details are correct!</a>
    <div class="woocommerce-info novalnet-display-none" id="novalnet_guaranteed_sepa_about_mandate" style="display: none;"><p></p>
    <p>I authorise (A) Novalnet AG to send instructions to my bank to debit my account and (B) my bank to debit my account in accordance with the instructions from Novalnet AG.</p>
    <p><strong>Creditor identifier: DE53ZZZ00000004253</strong></p>
    <p><strong>Note:</strong>You are entitled to a refund from your bank under the terms and conditions of your agreement with bank. A refund must be claimed within 8 weeks starting from the date on which your account was debited.</p>
    </div>
    </li>
    </ul>""", "de_DE": """<ul>
<li>Der Betrag wird durch Novalnet von Ihrem Konto abgebucht</li>
<li><a id="novalnet_guaranteed_sepa_mandate" style="cursor:pointer;text-decoration: underline;" onclick="jQuery('#novalnet_guaranteed_sepa_about_mandate').toggle('slow')">Ich erteile hiermit das SEPA-Lastschriftmandat (elektronische Übermittlung) und bestätige, dass die Bankverbindung korrekt ist</a>
<div class="woocommerce-info novalnet-display-none" id="novalnet_guaranteed_sepa_about_mandate" style="display: none;"><p></p>
<p>Ich ermächtige den Zahlungsempfänger, Zahlungen von meinem Konto mittels Lastschrift einzuziehen. Zugleich weise ich mein Kreditinstitut an, die von dem Zahlungsempfänger auf mein Konto gezogenen Lastschriften einzulösen.</p>
<p><strong>Gläubiger-Identifikationsnummer: DE53ZZZ00000004253</strong></p>
<p><strong>Hinweis:</strong>Ich kann innerhalb von acht Wochen, beginnend mit dem Belastungsdatum, die Erstattung des belasteten Betrages verlangen. Es gelten dabei die mit meinem Kreditinstitut vereinbarten Bedingungen.</p>
</div>
</li>
</ul>"""},
    },
    "EPS": {
        "lang": {"en_US": "eps", "de_DE": "eps"},
        "description": {"en_US": "You will be redirected to eps. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu eps weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "GIROPAY": {
        "lang": {"en_US": "giropay", "de_DE": "giropay"},
        "description": {"en_US": "You will be redirected to giropay. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu giropay weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "GUARANTEED_DIRECT_DEBIT_SEPA": {
        "lang": {
            "en_US": "Direct debit SEPA with payment guarantee",
            "de_DE": "SEPA-Lastschrift mit Zahlungsgarantie",
        },
        "description": {"en_US": "The amount will be debited from your account by Novalnet", "de_DE": "Der Betrag wird durch Novalnet von Ihrem Konto abgebucht"},
    },
    "GUARANTEED_INVOICE": {
        "lang": {
            "en_US": "Invoice with payment guarantee",
            "de_DE": "Rechnung mit Zahlungsgarantie",
        },
        "description": {"en_US": "You will receive an e-mail with the Novalnet account details to complete the payment.", "de_DE": "Sie erhalten eine E-Mail mit den Bankdaten von Novalnet, um die Zahlung abzuschließen."},
    },
    "IDEAL": {
        "lang": {"en_US": "iDEAL", "de_DE": "iDEAL"},
        "description": {"en_US": "You will be redirected to iDEAL. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu iDEAL weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist."},
    },
    "MULTIBANCO": {
        "lang": {"en_US": "Multibanco", "de_DE": "Multibanco"},
        "description": {"en_US": "On successful checkout, you will receive a payment reference. Using this payment reference, you can either pay in the Multibanco ATM or through your online bank account ", "de_DE": "Nach erfolgreichem Bestellabschluss erhalten Sie eine Zahlungsreferenz. Damit können Sie entweder an einem Multibanco-Geldautomaten oder im Onlinebanking bezahlen."},
    },
    "ONLINE_BANK_TRANSFER": {
        "lang": {"en_US": "Online bank transfer", "de_DE": "Onlineüberweisung"},
        "description": {"en_US": "You will be redirected to Online bank transfer. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden auf die Banking-Seite weitergeleitet. Bitte schließen oder aktualisieren Sie den Browser nicht, bis die Zahlung abgeschlossen ist."},
    },
    "ONLINE_TRANSFER": {
        "lang": {"en_US": "Sofort", "de_DE": "Sofortüberweisung"},
        "description": {"en_US": "You will be redirected to Sofort. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu Sofortüberweisung weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "PAYPAL": {
        "lang": {"en_US": "PayPal", "de_DE": "PayPal"},
        "description": {"en_US": "You will be redirected to PayPal. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu PayPal weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "POSTFINANCE": {
        "lang": {"en_US": "PostFinance", "de_DE": "PostFinance"},
        "description": {"en_US": "You will be redirected to PostFinance. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu PostFinance weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "POSTFINANCE_CARD": {
        "lang": {"en_US": "PostFinance Card", "de_DE": "PostFinance Card"},
        "description": {"en_US": "You will be redirected to PostFinance Card. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu PostFinance weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "PRZELEWY24": {
        "lang": {"en_US": "Przelewy24", "de_DE": "Przelewy24"},
        "description": {"en_US": "You will be redirected to Przelewy24. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu Przelewy24 weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist"},
    },
    "TRUSTLY": {
        "lang": {"en_US": "Trustly", "de_DE": "Trustly"},
        "description": {"en_US": "You will be redirected to Trustly. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu Trustly weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist."},
    },
    "WECHATPAY": {
        "lang": {"en_US": "WeChat Pay", "de_DE": "WeChat Pay"},
        "description": {"en_US": "You will be redirected to WeChat Pay. Please don’t close or refresh the browser until the payment is completed", "de_DE": "Sie werden zu WeChat Pay weitergeleitet. Um eine erfolgreiche Zahlung zu gewährleisten, darf die Seite nicht geschlossen oder neu geladen werden, bis die Bezahlung abgeschlossen ist."},
    },
    "INVOICE": {
        "lang": {"en_US": "Invoice", "de_DE": "Kauf auf Rechnung"},
        "description": {"en_US": "You will receive an e-mail with the Novalnet account details to complete the payment.", "de_DE": "Sie erhalten eine E-Mail mit den Bankdaten von Novalnet, um die Zahlung abzuschließen."},
    },
    "PREPAYMENT": {
        "lang": {"en_US": "Prepayment", "de_DE": "Vorkasse"},
        "description": {"en_US": " You will receive an e-mail with the Novalnet account details to complete the payment.", "de_DE": "Sie erhalten eine E-Mail mit den Bankdaten von Novalnet, um die Zahlung abzuschließen."},
    },
}



DEACTIVATED_PAYMENT = ['INSTALMENT_DIRECT_DEBIT_SEPA', 'INSTALMENT_INVOICE', 'INSTALMENT_DIRECT_DEBIT_SEPA_WITH_RATE', 'INSTALMENT_INVOICE_WITH_RATE', 'COLLECTION_ASSIGNMENT', 'PAY_BY_INVOICE_NN', 'DIRECT_DEBIT_SEPA_SIGNED', 'CASH_ON_DELIVERY', 'FUNDS_TRANSFER', 'SEPA_CREDIT', 'GOOGLEPAY', 'APPLEPAY']

RESULT_CODES_MAPPING = {
    'CONFIRMED': 'done',
    'ON_HOLD': 'authorize',
    'PENDING': 'pending',
    'DEACTIVATED': 'cancel',
    'FAILURE': 'error',
}
