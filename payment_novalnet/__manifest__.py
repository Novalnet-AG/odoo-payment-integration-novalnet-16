{
    'name': 'Payment Provider: Novalnet',
    'version': '3.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': "A payment service provider covering several payment.",
    'author': 'Novalnet',
    'website': 'https://www.novalnet.com',
    'description': '''
	All-in-one-solution for worldwide payments and services on a single platform. Accept 200+ payment methods in 150+ currencies globally in a highly secure, state-of-the-art environment supported by AI-powered risk management for SMEs & large enterprises. Novalnet hosts multiple value-added features & services including recurring payments, debt collection, automated marketplace. Visit www.novalnet.de for more details.
    ''',
    'depends': ['sale','payment'],
    'data': [
        'views/payment_novalnet_templates.xml',
        'views/payment_provider_views.xml',
        'views/novalnet_payment_method.xml',
        'views/callback_notification.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/payment_provider_data.xml',
        'wizards/payment_link_wizard_views.xml',
    ],
    'application': True,
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'payment_novalnet/static/src/js/payment_form.js',
        ],
    },
    'images': [
        'static/description/cover.png',
    ],
    'license': 'LGPL-3'
}
