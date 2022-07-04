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
        'views/picking_report_inherit.xml',
        'views/delivery_report_inherit.xml',
        'report/report.xml',
        'report/purchase_report_extend.xml',
    ],

}
