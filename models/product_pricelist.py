# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    apply_and_logic = fields.Boolean(
        string='Aplicar Lógica AND',
        default=False,
        help="Si está marcado, esta regla debe cumplirse junto con otras reglas "
             "marcadas con AND para que se aplique el descuento."
    )
    and_group = fields.Integer(
        string='Grupo AND',
        default=0,
        help="Las reglas con el mismo número de grupo AND deben cumplirse todas. "
             "0 = sin grupo (comportamiento normal)"
    )


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _check_product_match(self, rule, product, qty, partner):
        """Verifica si una regla hace match con un producto específico"""
        # Producto específico
        if rule.product_id:
            if rule.product_id.id != product.id:
                return False
        # Template de producto
        elif rule.product_tmpl_id:
            if rule.product_tmpl_id.id != product.product_tmpl_id.id:
                return False
        # Categoría
        elif rule.categ_id:
            cat = product.categ_id
            found = False
            while cat:
                if cat.id == rule.categ_id.id:
                    found = True
                    break
                cat = cat.parent_id
            if not found:
                return False
        
        # Verificar cantidad mínima
        if rule.min_quantity > 0:
            if qty < rule.min_quantity:
                return False
        
        return True

    def _get_applicable_rules_with_and_logic(self, product, qty, date, partner, order_products=None):
        """Retorna las reglas aplicables considerando la lógica AND"""
        self.ensure_one()
        
        # Obtener todas las reglas activas en el rango de fechas
        domain = [('pricelist_id', '=', self.id)]
        if date:
            domain += ['|', ('date_start', '=', False), ('date_start', '<=', date),
                      '|', ('date_end', '=', False), ('date_end', '>=', date)]
        
        all_rules = self.env['product.pricelist.item'].search(domain)
        
        # Separar reglas AND de reglas normales
        and_rules = all_rules.filtered(lambda r: r.apply_and_logic and r.and_group > 0)
        normal_rules = all_rules.filtered(lambda r: not r.apply_and_logic or r.and_group == 0)
        
        if not and_rules:
            _logger.info(f"AND Logic: No hay reglas AND activas")
            return all_rules
        
        # Si no hay productos de la orden en contexto, no podemos evaluar AND
        if not order_products:
            _logger.info(f"AND Logic: No hay productos en contexto - usando solo reglas normales")
            return normal_rules
        
        _logger.info(f"AND Logic: Evaluando {len(and_rules)} reglas AND con {len(order_products)} productos")
        
        # Agrupar reglas AND por grupo
        and_groups = {}
        for rule in and_rules:
            if rule.and_group not in and_groups:
                and_groups[rule.and_group] = []
            and_groups[rule.and_group].append(rule)
        
        # Evaluar cada grupo AND
        valid_and_rules = self.env['product.pricelist.item']
        
        for group_id, group_rules in and_groups.items():
            group_valid = True
            
            _logger.info(f"AND Logic: === Evaluando GRUPO {group_id} con {len(group_rules)} reglas ===")
            
            # CADA regla del grupo debe tener AL MENOS UN producto que haga match
            for rule in group_rules:
                rule_has_match = False
                rule_name = rule.product_id.name if rule.product_id else f"min_qty:{rule.min_quantity}"
                
                for prod_data in order_products:
                    prod = prod_data.get('product')
                    prod_qty = prod_data.get('qty', 1.0)
                    
                    if self._check_product_match(rule, prod, prod_qty, partner):
                        _logger.info(f"AND Logic:   ✓ Regla '{rule_name}' MATCH con {prod.name} (qty:{prod_qty})")
                        rule_has_match = True
                        break
                
                if not rule_has_match:
                    _logger.info(f"AND Logic:   ✗ Regla '{rule_name}' NO tiene match - GRUPO {group_id} DESCARTADO")
                    group_valid = False
                    break
            
            if group_valid:
                _logger.info(f"AND Logic: ✓✓✓ GRUPO {group_id} VÁLIDO - Agregando {len(group_rules)} reglas ✓✓✓")
                valid_and_rules |= self.env['product.pricelist.item'].browse([r.id for r in group_rules])
            else:
                _logger.info(f"AND Logic: ✗✗✗ GRUPO {group_id} INVÁLIDO - Descartando reglas ✗✗✗")
        
        result = normal_rules | valid_and_rules
        _logger.info(f"AND Logic: FINAL - Retornando {len(result)} reglas ({len(normal_rules)} normales + {len(valid_and_rules)} AND válidas)")
        return result

    def _get_product_price(self, product, quantity, partner=None, date=None, uom_id=None):
        """Override principal - intercepta TODOS los cálculos de precios"""
        self.ensure_one()
        
        # Verificar si hay reglas AND
        has_and_rules = any(
            item.apply_and_logic and item.and_group > 0 
            for item in self.item_ids
        )
        
        if not has_and_rules:
            # Sin reglas AND, comportamiento estándar
            return super()._get_product_price(product, quantity, partner, date, uom_id)
        
        _logger.info(f"\n{'='*80}")
        _logger.info(f"AND Logic: INICIO - Calculando precio para {product.name} (qty:{quantity})")
        _logger.info(f"{'='*80}")
        
        # Obtener productos de la orden desde el contexto
        order_products = self.env.context.get('pricelist_order_products')
        
        if not order_products:
            _logger.warning(f"AND Logic: ⚠️ NO hay contexto de orden - intentando obtener de sale.order.line")
            # Intentar obtener desde la orden actual si existe
            sale_line = self.env.context.get('sale_order_line')
            if sale_line and sale_line.order_id:
                order_products = []
                for line in sale_line.order_id.order_line:
                    if line.product_id:
                        order_products.append({
                            'product': line.product_id,
                            'qty': line.product_uom_qty,
                            'partner': sale_line.order_id.partner_id
                        })
                _logger.info(f"AND Logic: Recuperados {len(order_products)} productos de la orden")
        
        # Obtener reglas aplicables con lógica AND
        applicable_rules = self._get_applicable_rules_with_and_logic(
            product, quantity, date or fields.Date.context_today(self), partner, order_products
        )
        
        # Crear pricelist temporal con solo las reglas aplicables
        temp_pricelist_vals = {
            'name': self.name,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id if self.company_id else False,
        }
        
        temp_pricelist = self.sudo().new(temp_pricelist_vals)
        temp_pricelist.item_ids = applicable_rules
        
        # Calcular precio con el pricelist filtrado
        result = super(ProductPricelist, temp_pricelist)._get_product_price(
            product, quantity, partner, date, uom_id
        )
        
        _logger.info(f"AND Logic: Precio final calculado: ${result}")
        _logger.info(f"{'='*80}\n")
        
        return result
