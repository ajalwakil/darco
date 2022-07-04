# -*- coding: utf-8 -*-
{
    'name': "Project BOQ",
    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/boq_rights.xml',
        'views/project_extend.xml',
        'views/project_seq.xml',
        'views/district.xml',
        'views/city.xml',
        'views/region.xml',
        'views/area.xml',
        'views/employee_extend.xml',

    ],

}
