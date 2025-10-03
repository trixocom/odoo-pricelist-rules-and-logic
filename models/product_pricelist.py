# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare


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

    def _compute_price_rule(
        self, product, quantity, uom=None, date=False, currency=None, **kwargs
    ):
        """Override del método principal de cálculo de precios."""
        self.ensure_one()
        
        if not uom:
            uom = product.uom_id
        if not currency:
            currency = self.currency_id

        # Obtener todas las reglas aplicables
        rules = self._get_applicable_rules(
            product, quantity, uom=uom, date=date, **kwargs
        )

        # Separar reglas normales de reglas AND
        and_rules = rules.filtered(lambda r: r.apply_and_logic and r.and_group > 0)
        normal_rules = rules.filtered(lambda r: not r.apply_and_logic or r.and_group == 0)

        # Si hay reglas AND, verificar que se cumplan todas en cada grupo
        if and_rules:
            and_groups = {}
            for rule in and_rules:
                if rule.and_group not in and_groups:
                    and_groups[rule.and_group] = []
                and_groups[rule.and_group].append(rule)

            # Buscar un grupo donde todas las reglas se cumplan
            for group_id, group_rules in and_groups.items():
                # Verificar que todas las reglas del grupo se cumplan
                all_match = all(
                    self._check_rule_match(rule, product, quantity, uom, date, **kwargs)
                    for rule in group_rules
                )
                
                if all_match:
                    # Si todas se cumplen, calcular el precio con todas las reglas del grupo
                    price = self._calculate_combined_price(
                        group_rules, product, quantity, uom, date, currency, **kwargs
                    )
                    # Retornar el precio y la primera regla del grupo como referencia
                    return price, group_rules[0].id

        # Si no hay reglas AND aplicables, usar comportamiento normal
        if normal_rules:
            return super(ProductPricelist, self)._compute_price_rule(
                product, quantity, uom=uom, date=date, currency=currency, **kwargs
            )

        # Si no hay reglas aplicables, retornar precio base
        return product.lst_price, False

    def _check_rule_match(self, rule, product, quantity, uom, date, **kwargs):
        """Verifica si una regla individual coincide con los criterios."""
        # Verificar producto
        if rule.product_tmpl_id and rule.product_tmpl_id != product.product_tmpl_id:
            return False
        if rule.product_id and rule.product_id != product:
            return False

        # Verificar categoría
        if rule.categ_id:
            cat = product.categ_id
            while cat:
                if cat == rule.categ_id:
                    break
                cat = cat.parent_id
            else:
                return False

        # Verificar cantidad mínima
        if rule.min_quantity:
            qty_in_rule_uom = uom._compute_quantity(quantity, rule.product_uom_id or product.uom_id)
            if float_compare(
                qty_in_rule_uom, rule.min_quantity,
                precision_rounding=rule.product_uom_id.rounding or product.uom_id.rounding
            ) < 0:
                return False

        # Verificar fechas
        if rule.date_start and date and date < rule.date_start:
            return False
        if rule.date_end and date and date > rule.date_end:
            return False

        return True

    def _calculate_combined_price(
        self, rules, product, quantity, uom, date, currency, **kwargs
    ):
        """Calcula el precio combinado aplicando múltiples reglas."""
        # Comenzar con el precio base
        price = product.lst_price

        # Aplicar cada regla en secuencia
        for rule in rules.sorted('sequence'):
            if rule.compute_price == 'fixed':
                price = rule.fixed_price
            elif rule.compute_price == 'percentage':
                price = price - (price * (rule.percent_price / 100))
            elif rule.compute_price == 'formula':
                price_limit = price
                price = (price - (price * (rule.price_discount / 100))) + rule.price_surcharge
                
                if rule.price_round:
                    from odoo import tools
                    price = tools.float_round(price, precision_rounding=rule.price_round)
                
                if rule.price_min_margin:
                    price = max(price, price_limit + rule.price_min_margin)
                if rule.price_max_margin:
                    price = min(price, price_limit + rule.price_max_margin)

        # Convertir moneda si es necesario
        if currency != self.currency_id:
            price = self.currency_id._convert(
                price, currency, self.env.company, date or fields.Date.today()
            )

        return price

    def _get_applicable_rules(
        self, product, quantity, uom=None, date=False, **kwargs
    ):
        """Obtiene todas las reglas potencialmente aplicables."""
        self.ensure_one()
        
        if not date:
            date = fields.Date.context_today(self)

        rules = self.item_ids.filtered(
            lambda r: (
                (not r.product_tmpl_id or r.product_tmpl_id == product.product_tmpl_id) and
                (not r.product_id or r.product_id == product) and
                (not r.categ_id or product.categ_id.parent_of(r.categ_id)) and
                (not r.date_start or r.date_start <= date) and
                (not r.date_end or r.date_end >= date)
            )
        )

        return rules.sorted('sequence')
