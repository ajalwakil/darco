# -*- coding: utf-8 -*-
{
    'name': "purchase_report_project_inherit",

    'summary': "",

    'description': "",

    'author': "My Company",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','purchase'],

    # always loaded
    'data': [
        'views/purchase_report_inherit.xml',
        'views/picking_report_inherit.xml',
        'views/delivery_report_inherit.xml',
    ],

}
