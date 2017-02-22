# -*- coding: utf-8 -*-
{
    'name': "l10n_lv_partner_title",

    'summary': """
        Adds a meands of distinguishing between company and individual titles.
        Browse, search by abbreviations.
        """,

    'description': """
    """,

    'author': "SIA ITS1",
    'website': "http://www.its1.lv",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_lv'],

    # always loaded
    'data': [
        'views/res_partner_title.xml',
        'data/res_partner_title.xml',
    ],
    #'pre_init_hook': 'set_title_types',
}
