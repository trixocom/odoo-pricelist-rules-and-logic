# -*- coding: utf-8 -*-

from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_pricelist_item_id(self):
        """
        Override para pasar el contexto de la orden completa al cálculo de precios.
        Esto permite que las reglas AND evalúen todos los productos de la orden.
        """
        for line in self:
            if not line.product_id or not line.order_id.pricelist_id:
                line.pricelist_item_id = False
                continue
            
            # Preparar todos los productos de la orden para evaluación AND
            order_products = []
            for order_line in line.order_id.order_line:
                if order_line.product_id:
                    order_products.append((
                        order_line.product_id,
                        order_line.product_uom_qty,
                        line.order_id.partner_id
                    ))
            
            # Llamar al método con todos los productos de la orden
            pricelist = line.order_id.pricelist_id
            
            # Pasar el contexto con el order_id
            pricelist_with_context = pricelist.with_context(
                order_id=line.order_id.id,
                all_order_products=order_products
            )
            
            # CORREGIDO: Llamar correctamente con kwargs
            line.pricelist_item_id = pricelist_with_context._get_product_rule(
                product=line.product_id,
                quantity=line.product_uom_qty,
                uom=line.product_uom,
                date=line.order_id.date_order,
            )[1]
