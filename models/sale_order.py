# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        """Override del cálculo de precio unitario para inyectar contexto de productos.
        
        Este es el método que Odoo llama para calcular precios en líneas de venta.
        Aquí inyectamos el contexto con todos los productos de la orden antes de
        calcular los precios con la lista de precios.
        """
        for line in self:
            # Solo procesar si hay orden y pricelist
            if not line.order_id or not line.order_id.pricelist_id:
                continue
            
            pricelist = line.order_id.pricelist_id
            
            # Verificar si hay reglas AND activas
            has_and_rules = any(
                item.apply_and_logic and item.and_group > 0 
                for item in pricelist.item_ids
            )
            
            if not has_and_rules:
                # Sin reglas AND, usar comportamiento estándar
                continue
            
            _logger.info(f"\n{'='*80}")
            _logger.info(f"AND Logic Sale: Procesando línea de venta para {line.product_id.name}")
            _logger.info(f"{'='*80}")
            
            # Recopilar TODOS los productos de la orden actual
            order_products = []
            for order_line in line.order_id.order_line:
                if order_line.product_id:
                    order_products.append({
                        'product': order_line.product_id,
                        'qty': order_line.product_uom_qty,
                        'partner': line.order_id.partner_id
                    })
            
            _logger.info(f"AND Logic Sale: Contexto de orden con {len(order_products)} productos:")
            for i, prod_data in enumerate(order_products, 1):
                _logger.info(f"  {i}. {prod_data['product'].name} - Qty: {prod_data['qty']}")
            
            # Calcular precio con contexto inyectado
            pricelist_with_context = pricelist.with_context(
                pricelist_order_products=order_products
            )
            
            # CRÍTICO: Usar get_product_price (sin guion bajo) con keyword arguments
            price = pricelist_with_context.get_product_price(
                line.product_id,
                line.product_uom_qty,
                line.order_id.partner_id or self.env['res.partner'],
                date=line.order_id.date_order or False,
                uom_id=line.product_uom.id if line.product_uom else False
            )
            
            _logger.info(f"AND Logic Sale: Precio calculado para {line.product_id.name}: ${price}")
            _logger.info(f"{'='*80}\n")
            
            # Asignar el precio calculado
            line.price_unit = price
        
        # Llamar al super para líneas sin reglas AND
        return super(SaleOrderLine, self)._compute_price_unit()
