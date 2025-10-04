# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        """Inyecta contexto de productos antes de calcular precios.
        
        NO calcula precios manualmente - solo inyecta el contexto y deja
        que Odoo haga su trabajo. El filtrado de reglas AND se hace
        automáticamente en _get_applicable_rules() del pricelist.
        """
        lines_with_and_logic = self.env['sale.order.line']
        
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
            
            if has_and_rules:
                lines_with_and_logic |= line
        
        if not lines_with_and_logic:
            # Sin reglas AND, comportamiento estándar
            return super()._compute_price_unit()
        
        _logger.info(f"\n{'='*80}")
        _logger.info(f"AND Logic Sale: Procesando {len(lines_with_and_logic)} línea(s) con reglas AND")
        _logger.info(f"{'='*80}")
        
        # Recopilar TODOS los productos de TODAS las órdenes involucradas
        orders_context = {}
        for line in lines_with_and_logic:
            order_id = line.order_id.id
            if order_id not in orders_context:
                order_products = []
                for order_line in line.order_id.order_line:
                    if order_line.product_id:
                        order_products.append({
                            'product': order_line.product_id,
                            'qty': order_line.product_uom_qty,
                            'partner': line.order_id.partner_id
                        })
                orders_context[order_id] = order_products
                
                _logger.info(f"AND Logic Sale: Orden {order_id} con {len(order_products)} productos:")
                for i, prod_data in enumerate(order_products, 1):
                    _logger.info(f"  {i}. {prod_data['product'].name} - Qty: {prod_data['qty']}")
        
        # Procesar líneas con contexto inyectado
        for line in lines_with_and_logic:
            order_products = orders_context.get(line.order_id.id, [])
            
            # Inyectar contexto y llamar al super()
            # El override de _get_applicable_rules() filtrará automáticamente
            line_with_context = line.with_context(
                pricelist_order_products=order_products
            )
            
            # Dejar que Odoo calcule el precio normalmente
            super(SaleOrderLine, line_with_context)._compute_price_unit()
        
        _logger.info(f"{'='*80}\n")
        
        # Procesar líneas sin reglas AND
        lines_without_and_logic = self - lines_with_and_logic
        if lines_without_and_logic:
            return super(SaleOrderLine, lines_without_and_logic)._compute_price_unit()
