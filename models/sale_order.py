# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        """Override para pasar contexto con todos los productos de la orden"""
        for line in self:
            if not line.product_id or not line.order_id or not line.order_id.pricelist_id:
                continue
            
            # Verificar si el pricelist tiene reglas AND
            pricelist = line.order_id.pricelist_id
            has_and_rules = any(
                item.apply_and_logic and item.and_group > 0 
                for item in pricelist.item_ids
            )
            
            if not has_and_rules:
                # Sin reglas AND, usar comportamiento estándar
                continue
            
            # Preparar datos de todos los productos de la orden
            order_products_data = []
            for order_line in line.order_id.order_line:
                if order_line.product_id:
                    order_products_data.append({
                        'product': order_line.product_id,
                        'qty': order_line.product_uom_qty,
                        'partner': line.order_id.partner_id
                    })
            
            _logger.info(f"AND Logic: Computando precio para {line.product_id.name} con {len(order_products_data)} productos en contexto")
            
            # Agregar el contexto con todos los productos
            pricelist_with_context = pricelist.with_context(
                pricelist_order_products=order_products_data
            )
            
            # Calcular precio usando el pricelist con contexto - MÉTODO CORRECTO EN ODOO 18
            price = pricelist_with_context._get_product_price(
                line.product_id,
                line.product_uom_qty,
                line.order_id.partner_id,
                date=line.order_id.date_order,
                uom_id=line.product_uom.id
            )
            
            if price != line.price_unit:
                _logger.info(f"AND Logic: Precio actualizado de {line.price_unit} a {price}")
                line.price_unit = price
        
        # Llamar al super para líneas sin lógica AND
        return super()._compute_price_unit()
