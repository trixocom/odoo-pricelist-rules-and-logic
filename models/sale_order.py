# -*- coding: utf-8 -*-

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update_pricelist(self, *args, **kwargs):
        """Inyectar contexto de productos al actualizar pricelist"""
        # Preparar datos de todos los productos de la orden
        order_products_data = []
        for line in self.order_line:
            if line.product_id:
                order_products_data.append({
                    'product': line.product_id,
                    'qty': line.product_uom_qty,
                    'partner': self.partner_id
                })
        
        # Agregar al contexto
        if order_products_data:
            self = self.with_context(pricelist_order_products=order_products_data)
        
        return super()._cart_update_pricelist(*args, **kwargs)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty', 'product_uom')
    def _onchange_product_id_set_pricelist_context(self):
        """Inyectar contexto al cambiar producto"""
        if not self.order_id or not self.order_id.pricelist_id:
            return
        
        # Verificar si hay reglas AND
        pricelist = self.order_id.pricelist_id
        has_and_rules = any(
            item.apply_and_logic and item.and_group > 0 
            for item in pricelist.item_ids
        )
        
        if not has_and_rules:
            return
        
        # Preparar datos de todos los productos
        order_products_data = []
        for line in self.order_id.order_line:
            if line.product_id:
                order_products_data.append({
                    'product': line.product_id,
                    'qty': line.product_uom_qty,
                    'partner': self.order_id.partner_id
                })
        
        _logger.info(f"AND Logic Context: Inyectando {len(order_products_data)} productos al contexto")
        
        # Actualizar el contexto del entorno
        self.env.context = dict(self.env.context, pricelist_order_products=order_products_data)
