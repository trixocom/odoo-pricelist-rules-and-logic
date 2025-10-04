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

    def _filter_rules_with_and_logic(self, rules, order_products, partner):
        """Filtra reglas considerando la lógica AND"""
        
        # Separar reglas AND de reglas normales
        and_rules = rules.filtered(lambda r: r.apply_and_logic and r.and_group > 0)
        normal_rules = rules.filtered(lambda r: not r.apply_and_logic or r.and_group == 0)
        
        if not and_rules:
            _logger.info(f"AND Logic: No hay reglas AND en el conjunto")
            return rules
        
        # Si no hay productos de la orden en contexto, no podemos evaluar AND
        if not order_products:
            _logger.info(f"AND Logic: No hay productos en contexto - usando solo reglas normales")
            return normal_rules
        
        _logger.info(f"AND Logic: Filtrando {len(and_rules)} reglas AND con {len(order_products)} productos")
        
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
        _logger.info(f"AND Logic: Retornando {len(result)} reglas filtradas ({len(normal_rules)} normales + {len(valid_and_rules)} AND)")
        return result

    def _get_applicable_rules(self, products, date, **kwargs):
        """Override del método que obtiene reglas aplicables.
        
        Este es el método que Odoo llama internamente para obtener las reglas
        que se deben evaluar. Aquí interceptamos y filtramos según lógica AND.
        """
        # Llamar al super para obtener las reglas estándar
        rules = super()._get_applicable_rules(products, date, **kwargs)
        
        # Verificar si hay reglas AND en este pricelist
        has_and_rules = any(
            item.apply_and_logic and item.and_group > 0 
            for item in self.item_ids
        )
        
        if not has_and_rules:
            # Sin reglas AND, retornar reglas estándar
            return rules
        
        _logger.info(f"\n{'='*80}")
        _logger.info(f"AND Logic: Filtrando reglas para {len(products)} producto(s)")
        _logger.info(f"{'='*80}")
        
        # Obtener productos de la orden desde el contexto
        order_products = self.env.context.get('pricelist_order_products')
        
        # Obtener partner desde kwargs o contexto
        partner = kwargs.get('partner') or self.env.context.get('partner_id')
        if partner and isinstance(partner, int):
            partner = self.env['res.partner'].browse(partner)
        
        # Filtrar reglas con lógica AND
        filtered_rules = self._filter_rules_with_and_logic(rules, order_products, partner)
        
        _logger.info(f"{'='*80}\n")
        
        return filtered_rules
