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

    def _evaluate_and_groups_globally(self, rules, order_products, partner):
        """Evalúa qué grupos AND son válidos considerando TODOS los productos de la orden.
        
        Retorna un set con los IDs de grupos AND válidos.
        """
        and_rules = rules.filtered(lambda r: r.apply_and_logic and r.and_group > 0)
        
        if not and_rules or not order_products:
            return set()
        
        _logger.info(f"\n{'~'*80}")
        _logger.info(f"AND Logic: Evaluación GLOBAL de grupos AND")
        _logger.info(f"  Total productos en orden: {len(order_products)}")
        for prod_data in order_products:
            _logger.info(f"    - {prod_data['product'].name}: qty={prod_data['qty']}")
        
        # Agrupar reglas AND por grupo
        and_groups = {}
        for rule in and_rules:
            if rule.and_group not in and_groups:
                and_groups[rule.and_group] = []
            and_groups[rule.and_group].append(rule)
        
        valid_groups = set()
        
        for group_id, group_rules in and_groups.items():
            group_valid = True
            
            _logger.info(f"\nAND Logic: === Evaluando GRUPO {group_id} GLOBALMENTE ===")
            _logger.info(f"  Reglas en grupo: {len(group_rules)}")
            
            # CADA regla del grupo debe tener AL MENOS UN producto de la orden que haga match
            for rule in group_rules:
                rule_has_match = False
                rule_name = rule.product_id.name if rule.product_id else f"min_qty:{rule.min_quantity}"
                
                _logger.info(f"\n  Verificando regla: {rule_name} (min_qty={rule.min_quantity})")
                
                for prod_data in order_products:
                    prod = prod_data.get('product')
                    prod_qty = prod_data.get('qty', 1.0)
                    
                    if self._check_product_match(rule, prod, prod_qty, partner):
                        _logger.info(f"    ✓ MATCH: {prod.name} con qty={prod_qty} cumple la regla")
                        rule_has_match = True
                        break
                    else:
                        # Mostrar por qué no matchó
                        if rule.product_id and rule.product_id.id != prod.id:
                            reason = "producto diferente"
                        elif rule.min_quantity > prod_qty:
                            reason = f"qty insuficiente ({prod_qty} < {rule.min_quantity})"
                        else:
                            reason = "otra razón"
                        _logger.info(f"    ✗ NO match: {prod.name} con qty={prod_qty} - {reason}")
                
                if not rule_has_match:
                    _logger.info(f"  ❌ Regla '{rule_name}' NO tiene match - GRUPO {group_id} INVÁLIDO")
                    group_valid = False
                    break
            
            if group_valid:
                _logger.info(f"\n✅ GRUPO {group_id} VÁLIDO - Todas las reglas tienen match")
                valid_groups.add(group_id)
            else:
                _logger.info(f"\n❌ GRUPO {group_id} INVÁLIDO - Al menos una regla no tiene match")
        
        _logger.info(f"\nAND Logic: Grupos válidos: {valid_groups}")
        _logger.info(f"{'~'*80}\n")
        
        return valid_groups

    def _filter_rules_with_and_logic(self, rules, order_products, partner):
        """Filtra reglas considerando la lógica AND.
        
        Usa la evaluación global de grupos AND si está en contexto.
        """
        # Separar reglas AND de reglas normales
        and_rules = rules.filtered(lambda r: r.apply_and_logic and r.and_group > 0)
        normal_rules = rules.filtered(lambda r: not r.apply_and_logic or r.and_group == 0)
        
        if not and_rules:
            return rules
        
        # Si no hay productos de la orden en contexto, no podemos evaluar AND
        if not order_products:
            _logger.info(f"AND Logic Filter: No hay productos en contexto - usando solo reglas normales")
            return normal_rules
        
        # Verificar si ya tenemos la evaluación global en contexto
        valid_groups = self.env.context.get('valid_and_groups')
        
        if valid_groups is None:
            # Primera vez: evaluar globalmente
            valid_groups = self._evaluate_and_groups_globally(rules, order_products, partner)
            # Guardar en contexto para próximas llamadas
            self = self.with_context(valid_and_groups=valid_groups)
        else:
            _logger.info(f"AND Logic Filter: Usando evaluación global del contexto: {valid_groups}")
        
        # Filtrar reglas AND según grupos válidos
        valid_and_rules = self.env['product.pricelist.item']
        for rule in and_rules:
            if rule.and_group in valid_groups:
                _logger.info(f"  ✓ Regla {rule.product_id.name if rule.product_id else 'Todos'} del grupo {rule.and_group} ACEPTADA")
                valid_and_rules |= rule
            else:
                _logger.info(f"  ✗ Regla {rule.product_id.name if rule.product_id else 'Todos'} del grupo {rule.and_group} RECHAZADA")
        
        result = normal_rules | valid_and_rules
        _logger.info(f"\nAND Logic Filter: Retornando {len(result)} reglas ({len(normal_rules)} normales + {len(valid_and_rules)} AND)")
        return result

    def _get_product_price_rule(self, product, quantity, uom, date, **kwargs):
        """Override del método que calcula el precio según reglas.
        
        Este es el método correcto que se llama en Odoo 18.
        """
        self.ensure_one()
        
        # LOG CRÍTICO: Verificar que este método se ejecuta
        _logger.info(f"\n{'@'*80}")
        _logger.info(f"AND Logic Pricelist: _get_product_price_rule EJECUTÁNDOSE")
        _logger.info(f"  Pricelist: {self.name}")
        _logger.info(f"  Producto: {product.name}")
        _logger.info(f"  Cantidad: {quantity}")
        _logger.info(f"{'@'*80}")
        
        # Verificar si hay reglas AND en este pricelist
        has_and_rules = any(
            item.apply_and_logic and item.and_group > 0 
            for item in self.item_ids
        )
        
        _logger.info(f"AND Logic Pricelist: has_and_rules = {has_and_rules}")
        
        if not has_and_rules:
            _logger.info(f"AND Logic Pricelist: Sin reglas AND, usando super()")
            return super()._get_product_price_rule(product, quantity, uom, date, **kwargs)
        
        # Obtener productos de la orden desde el contexto
        order_products = self.env.context.get('pricelist_order_products')
        _logger.info(f"AND Logic Pricelist: order_products en contexto: {order_products is not None}")
        if order_products:
            _logger.info(f"AND Logic Pricelist: {len(order_products)} productos en contexto")
        
        # Si no hay contexto de orden, usar comportamiento normal
        if not order_products:
            _logger.info(f"AND Logic Pricelist: Sin contexto de orden, usando super()")
            return super()._get_product_price_rule(product, quantity, uom, date, **kwargs)
        
        # Obtener partner del contexto o kwargs
        partner = kwargs.get('partner') or self.env.context.get('partner')
        
        # Llamar al super para obtener todas las reglas aplicables
        _logger.info(f"AND Logic Pricelist: Llamando super() para obtener reglas base")
        price, rule_id = super()._get_product_price_rule(product, quantity, uom, date, **kwargs)
        
        # Si no hay regla aplicable, retornar
        if not rule_id:
            _logger.info(f"AND Logic Pricelist: Super no retornó regla, usando precio: {price}")
            return price, rule_id
        
        # Obtener la regla
        rule = self.env['product.pricelist.item'].browse(rule_id)
        _logger.info(f"AND Logic Pricelist: Regla retornada: {rule.product_id.name if rule.product_id else 'Todos'}")
        _logger.info(f"  - AND={rule.apply_and_logic}, grupo={rule.and_group}")
        
        # Si la regla no es AND, retornar normalmente
        if not rule.apply_and_logic or rule.and_group == 0:
            _logger.info(f"AND Logic Pricelist: Regla no es AND, retornando precio: {price}")
            return price, rule_id
        
        # Evaluar si el grupo AND es válido
        all_rules = self.item_ids
        valid_groups = self.env.context.get('valid_and_groups')
        
        if valid_groups is None:
            # Primera evaluación
            valid_groups = self._evaluate_and_groups_globally(all_rules, order_products, partner)
            self = self.with_context(valid_and_groups=valid_groups)
        
        # Si el grupo de la regla NO es válido, no aplicar el descuento
        if rule.and_group not in valid_groups:
            _logger.info(f"AND Logic Pricelist: GRUPO {rule.and_group} NO VÁLIDO - NO aplicar descuento")
            _logger.info(f"  Retornando precio lista: {product.lst_price}")
            return product.lst_price, False
        
        _logger.info(f"AND Logic Pricelist: GRUPO {rule.and_group} VÁLIDO - Aplicar descuento")
        _logger.info(f"  Retornando precio: {price}")
        _logger.info(f"{'@'*80}\n")
        
        return price, rule_id
