# -*- coding: utf-8 -*-
{
    'name': 'Pricelist Rules AND Logic',
    'version': '18.0.1.0.21',
    'category': 'Sales',
    'summary': 'Implementa lógica AND entre reglas seleccionadas de lista de precios',
    'description': """
        Pricelist Rules AND Logic
        ==========================
        
        Este módulo permite aplicar lógica AND entre ciertas reglas seleccionadas 
        de la lista de precios, requiriendo que se cumplan todas las condiciones 
        para aplicar el descuento.
        
        Características:
        ----------------
        * Campo booleano para marcar reglas que deben cumplirse conjuntamente
        * Evaluación AND de múltiples reglas marcadas
        * Compatible con la lógica estándar de Odoo
        * Fácil configuración desde la interfaz de usuario
        * Detecta automáticamente todos los productos de la orden de venta
        * Logging detallado para depuración
        
        Versiones Soportadas:
        --------------------
        * Odoo 18.0
        * Odoo 17.0 (cambiar version a 17.0.1.0.1)
    """,
    'author': 'TRX',
    'website': 'https://github.com/trixocom/odoo-pricelist-rules-and-logic',
    'license': 'LGPL-3',
    'depends': ['product', 'sale'],
    'data': [
        'views/product_pricelist_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
