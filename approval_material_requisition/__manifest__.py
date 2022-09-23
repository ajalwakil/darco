{

    'name': 'Approval Material Requisition',
    'category': 'Construction Management',
    'summary': 'Construction Management',
    'description': "This module will be give Construction Management . ",
    'author': 'Hafiz Junaid',
    'depends': ['base', 'approvals', 'purchase', 'project', 'stock', 'approvals_purchase'
                ],
    'data': [
        'security/group.xml',
        # 'security/ir.model.access.csv',
        'views/models_extend.xml',
  
    ],
    'installable': True,

    'license': 'AGPL-3',

}
