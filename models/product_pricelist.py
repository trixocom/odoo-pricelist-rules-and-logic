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

    def _check_rule_match(self, item, product, quantity, partner, date, uom_id):
        """
        Verifica si una regla individual coincide con los criterios dados.
        Compatible con Odoo 18.
        """
        # Verificar si el item aplica al producto
        if item.product_tmpl_id and item.product_tmpl_id != product.product_tmpl_id:
            return False
        
        if item.product_id and item.product_id != product:
            return False
        
        # Verificar categoría
        if item.categ_id:
            if not product.categ_id:
                return False
            cat = product.categ_id
            found = False
            while cat:
                if cat == item.categ_id:
                    found = True
                    break
                cat = cat.parent_id
            if not found:
                return False
        
        # Verificar cantidad mínima
        if item.min_quantity:
            product_uom = item.product_uom_id or product.uom_id
            if uom_id and uom_id != product_uom:
                # Convertir cantidad a la UoM de la regla
                try:
                    converted_qty = uom_id._compute_quantity(quantity, product_uom)
                except:
                    converted_qty = quantity
            else:
                converted_qty = quantity
            
            if float_compare(
                converted_qty,
                item.min_quantity,
                precision_rounding=product_uom.rounding
            ) < 0:
                return False
        
        # Verificar fechas
        if item.date_start and date:
            if date < item.date_start:
                return False
        
        if item.date_end and date:
            if date > item.date_end:
                return False
        
        return True

    def _get_applicable_pricelist_items(self, products_qty_partner, date, uom_id):
        """
        Obtiene los items aplicables de la pricelist considerando la lógica AND.
        """
        self.ensure_one()
        
        # Obtener todos los items activos de esta pricelist
        all_items = self.item_ids.filtered(lambda i: not i.date_start or i.date_start <= date).filtered(
            lambda i: not i.date_end or i.date_end >= date
        )
        
        # Separar reglas normales de reglas AND
        and_items = all_items.filtered(lambda i: i.apply_and_logic and i.and_group > 0)
        normal_items = all_items.filtered(lambda i: not i.apply_and_logic or i.and_group == 0)
        
        if not and_items:
            return all_items
        
        # Agrupar por grupos AND
        and_groups = {}
        for item in and_items:
            if item.and_group not in and_groups:
                and_groups[item.and_group] = []
            and_groups[item.and_group].append(item)
        
        # Verificar grupos AND
        valid_and_items = self.env['product.pricelist.item']
        for group_id, group_items in and_groups.items():
            # Verificar que todas las reglas del grupo se cumplan para todos los productos
            all_products_match = True
            
            for product, qty, partner in products_qty_partner:
                group_matches_for_product = all(
                    self._check_rule_match(item, product, qty, partner, date, uom_id)
                    for item in group_items
                )
                
                if not group_matches_for_product:
                    all_products_match = False
                    break
            
            # Si todas las reglas del grupo se cumplen para todos los productos,
            # agregamos estas reglas a las válidas
            if all_products_match:
                valid_and_items |= self.env['product.pricelist.item'].browse([i.id for i in group_items])
        
        # Retornar reglas normales + reglas AND válidas
        return normal_items | valid_and_items

    @api.model
    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, compute_price=True, **kwargs):
        """
        Override del método principal de cálculo de precios para Odoo 18.
        Implementa lógica AND para grupos de reglas.
        
        Este método es compatible con la firma de Odoo 18 donde recibe:
        - products_qty_partner: lista de tuplas (product, qty, partner)
        - date: fecha de aplicación
        - uom_id: unidad de medida
        - compute_price: si debe calcular el precio o solo retornar la regla
        - **kwargs: otros parámetros adicionales
        """
        self.ensure_one()
        
        if not date:
            date = fields.Date.context_today(self)
        
        # Verificar si hay reglas AND activas
        has_and_rules = any(
            item.apply_and_logic and item.and_group > 0 
            for item in self.item_ids
        )
        
        # Si no hay reglas AND, usar el comportamiento estándar
        if not has_and_rules:
            return super(ProductPricelist, self)._compute_price_rule(
                products_qty_partner, date=date, uom_id=uom_id, compute_price=compute_price, **kwargs
            )
        
        # Temporalmente deshabilitar las reglas AND que no se deben aplicar
        items_to_filter = self._get_applicable_pricelist_items(products_qty_partner, date, uom_id)
        all_item_ids = set(self.item_ids.ids)
        items_to_keep = set(items_to_filter.ids)
        items_to_disable = all_item_ids - items_to_keep
        
        # Si hay items a deshabilitar temporalmente
        if items_to_disable:
            # Crear un contexto para marcar los items que deben ser ignorados
            self_with_context = self.with_context(disabled_pricelist_items=items_to_disable)
            
            # Filtrar temporalmente los items antes de llamar al super
            original_items = self.item_ids
            try:
                # Temporalmente modificar item_ids para que super() solo vea los items válidos
                self.item_ids = items_to_filter
                
                result = super(ProductPricelist, self_with_context)._compute_price_rule(
                    products_qty_partner, date=date, uom_id=uom_id, compute_price=compute_price, **kwargs
                )
            finally:
                # Restaurar los items originales
                self.item_ids = original_items
            
            return result
        else:
            # Si no hay items para deshabilitar, llamar directamente al super
            return super(ProductPricelist, self)._compute_price_rule(
                products_qty_partner, date=date, uom_id=uom_id, compute_price=compute_price, **kwargs
            )
