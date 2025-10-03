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

    def _get_applicable_rules_with_and_logic(self, product, qty, date, partner):
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
            return all_rules
        
        # Obtener todos los productos de la orden desde el contexto
        order_products = self.env.context.get('pricelist_order_products', [])
        
        if not order_products:
            _logger.info(f"AND Logic: No hay productos en el contexto, usando solo el producto actual")
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
            
            # CADA regla del grupo debe tener AL MENOS UN producto que haga match
            for rule in group_rules:
                rule_has_match = False
                
                for prod_data in order_products:
                    # prod_data es un diccionario con 'product', 'qty', 'partner'
                    prod = prod_data.get('product')
                    prod_qty = prod_data.get('qty', 1.0)
                    
                    if self._check_product_match(rule, prod, prod_qty, partner):
                        _logger.info(f"AND Logic: Regla {rule.id} (min_qty:{rule.min_quantity}) MATCH con {prod.name} (qty:{prod_qty})")
                        rule_has_match = True
                        break
                
                if not rule_has_match:
                    _logger.info(f"AND Logic: Regla {rule.id} NO tiene match - Grupo {group_id} INVÁLIDO")
                    group_valid = False
                    break
            
            if group_valid:
                _logger.info(f"AND Logic: Grupo {group_id} VÁLIDO - Agregando {len(group_rules)} reglas")
                valid_and_rules |= self.env['product.pricelist.item'].browse([r.id for r in group_rules])
            else:
                _logger.info(f"AND Logic: Grupo {group_id} INVÁLIDO - Descartando reglas")
        
        result = normal_rules | valid_and_rules
        _logger.info(f"AND Logic: Retornando {len(result)} reglas ({len(normal_rules)} normales + {len(valid_and_rules)} AND)")
        return result

    @api.model
    def _compute_price_rule_multi(self, products_qty_partner, date=False, uom_id=False):
        """Override para implementar lógica AND evaluando productos individuales con contexto"""
        # Verificar si hay reglas AND en alguna de las pricelists involucradas
        has_and_rules = False
        for pricelist in self:
            if pricelist.item_ids.filtered(lambda i: i.apply_and_logic and i.and_group > 0):
                has_and_rules = True
                break
        
        # Si no hay reglas AND, usar comportamiento estándar
        if not has_and_rules:
            return super()._compute_price_rule_multi(products_qty_partner, date=date, uom_id=uom_id)
        
        if not date:
            date = fields.Date.context_today(self)
        
        # Resultado: {pricelist_id: {product_id: (price, rule_id)}}
        results = {}
        
        for pricelist in self:
            results[pricelist.id] = {}
            
            # Preparar datos de todos los productos de la orden para el contexto
            order_products_data = []
            for prod, qty, partner in products_qty_partner:
                order_products_data.append({
                    'product': prod,
                    'qty': qty,
                    'partner': partner
                })
            
            # Procesar cada producto individualmente con el contexto completo
            for product, qty, partner in products_qty_partner:
                # Obtener reglas aplicables con lógica AND
                pricelist_with_context = pricelist.with_context(
                    pricelist_order_products=order_products_data
                )
                
                applicable_rules = pricelist_with_context._get_applicable_rules_with_and_logic(
                    product, qty, date, partner
                )
                
                # Crear un recordset temporal con solo las reglas aplicables
                # usando un dominio SQL para mejor performance
                if applicable_rules:
                    # Filtrar las reglas del pricelist actual
                    temp_items = applicable_rules.filtered(lambda r: r.pricelist_id.id == pricelist.id)
                    
                    # Crear un pricelist temporal en memoria
                    temp_pricelist_vals = {
                        'name': pricelist.name,
                        'currency_id': pricelist.currency_id.id,
                        'company_id': pricelist.company_id.id if pricelist.company_id else False,
                    }
                    
                    # Usar sudo y new() para evitar problemas de permisos
                    temp_pricelist = pricelist.sudo().new(temp_pricelist_vals)
                    temp_pricelist.item_ids = temp_items
                    
                    # Llamar al super con el pricelist filtrado
                    temp_result = super(ProductPricelist, temp_pricelist)._compute_price_rule_multi(
                        [(product, qty, partner)], date=date, uom_id=uom_id
                    )
                    
                    if temp_pricelist.id in temp_result and product.id in temp_result[temp_pricelist.id]:
                        results[pricelist.id][product.id] = temp_result[temp_pricelist.id][product.id]
                else:
                    # Sin reglas aplicables, usar precio base
                    results[pricelist.id][product.id] = (product.lst_price, False)
        
        return results
