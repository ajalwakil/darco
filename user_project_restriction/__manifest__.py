# -*- coding: utf-8 -*-
{
    'name': "Projects Restriction on Users",

    'summary': """
    User Allowed Project Only.
    """,

    'description': """
        - This Module adds restriction on users for accessing Projects.
        - User can not see the Projects if not allowed by the admin.
        - User can only see and operate on Allowed Project.
    """,

    'author': 'Itech Resources',
    'maintainer': 'Itech Resources',
    'company': 'Itech Resources',
    'version': '0.1',

    'depends': ['base', 'stock', 'purchase', 'project', 'approvals', 'hr'],

    'data': [
        'views/user_view.xml',
    ],
}
