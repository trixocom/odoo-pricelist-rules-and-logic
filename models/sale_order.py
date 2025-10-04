# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        """Inyecta contexto de productos antes de calcular precios."""
        
        # LOG CRÍTICO: Verificar que este método se ejecuta
        _logger.info(f"\n{'#'*80}")
        _logger.info(f"AND Logic Sale: _compute_price_unit EJECUTÁNDOSE para {len(self)} línea(s)")
        _logger.info(f"{'#'*80}")
        
        lines_with_and_logic = self.env['sale.order.line']
        
        for line in self:
            _logger.info(f"AND Logic Sale: Procesando línea: {line.product_id.name if line.product_id else 'SIN PRODUCTO'}")
            
            # Solo procesar si hay orden y pricelist
            if not line.order_id or not line.order_id.pricelist_id:
                _logger.info(f"AND Logic Sale: Línea sin orden o pricelist, saltando")
                continue
            
            pricelist = line.order_id.pricelist_id
            _logger.info(f"AND Logic Sale: Pricelist: {pricelist.name}")
            _logger.info(f"AND Logic Sale: Items en pricelist: {len(pricelist.item_ids)}")
            
            # Verificar si hay reglas AND activas
            and_items = [item for item in pricelist.item_ids if item.apply_and_logic and item.and_group > 0]
            _logger.info(f"AND Logic Sale: Items con AND: {len(and_items)}")
            
            if and_items:
                for item in and_items:
                    prod_name = item.product_id.name if item.product_id else 'Todos'
                    _logger.info(f"  - Item AND: {prod_name}, grupo={item.and_group}, min_qty={item.min_quantity}")
            
            has_and_rules = len(and_items) > 0
            
            if has_and_rules:
                _logger.info(f"AND Logic Sale: ✓ Línea TIENE reglas AND, agregando a lista")
                lines_with_and_logic |= line
            else:
                _logger.info(f"AND Logic Sale: ✗ Línea NO tiene reglas AND")
        
        if not lines_with_and_logic:
            _logger.info(f"AND Logic Sale: NO hay líneas con reglas AND, llamando super() normal")
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
                
                _logger.info(f"AND Logic Sale: Orden {line.order_id.name} con {len(order_products)} productos:")
                for i, prod_data in enumerate(order_products, 1):
                    _logger.info(f"  {i}. {prod_data['product'].name} - Qty: {prod_data['qty']}")
        
        # IMPORTANTE: Inyectar contexto compartido UNA VEZ para todas las líneas de la misma orden
        # Esto asegura que la evaluación global de grupos AND se haga solo una vez
        for order_id, order_products in orders_context.items():
            order_lines = lines_with_and_logic.filtered(lambda l: l.order_id.id == order_id)
            
            _logger.info(f"\n{'>'*80}")
            _logger.info(f"AND Logic Sale: Procesando {len(order_lines)} líneas de la orden {order_lines[0].order_id.name}")
            _logger.info(f"{'>'*80}")
            
            # Inyectar contexto compartido para todas las líneas de esta orden
            # CLAVE: El contexto se comparte, así la evaluación global se hace solo una vez
            lines_with_context = order_lines.with_context(
                pricelist_order_products=order_products,
                valid_and_groups=None  # Forzar nueva evaluación global
            )
            
            # Procesar cada línea
            for line in lines_with_context:
                _logger.info(f"\nAND Logic Sale: Calculando precio para {line.product_id.name}")
                super(SaleOrderLine, line)._compute_price_unit()
                _logger.info(f"AND Logic Sale: Precio final: {line.price_unit}")
        
        _logger.info(f"\n{'='*80}\n")
        
        # Procesar líneas sin reglas AND
        lines_without_and_logic = self - lines_with_and_logic
        if lines_without_and_logic:
            _logger.info(f"AND Logic Sale: Procesando {len(lines_without_and_logic)} líneas sin reglas AND")
            return super(SaleOrderLine, lines_without_and_logic)._compute_price_unit()
