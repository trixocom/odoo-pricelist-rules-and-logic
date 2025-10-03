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
            # En Odoo 18 el campo es product_uom, no product_uom_id
            product_uom = item.product_uom or product.uom_id
            
            # CRÍTICO: Asegurar que product_uom sea un recordset
            if not hasattr(product_uom, 'rounding'):
                # Si no tiene el atributo rounding, puede ser un ID o un string
                if product_uom:
                    # Intentar convertir a int (si es un ID numérico)
                    try:
                        uom_id_value = int(product_uom)
                        product_uom = self.env['uom.uom'].browse(uom_id_value)
                    except (ValueError, TypeError):
                        # Si falla, es un string (nombre de UoM) u otro tipo - usar el del producto
                        product_uom = product.uom_id
                else:
                    product_uom = product.uom_id
            
            # CRÍTICO: Asegurar que uom_id también sea un recordset si existe
            if uom_id:
                if not hasattr(uom_id, '_compute_quantity'):
                    # Si no tiene método _compute_quantity, es un ID - convertir a recordset
                    try:
                        uom_id_value = int(uom_id)
                        uom_id = self.env['uom.uom'].browse(uom_id_value)
                    except (ValueError, TypeError):
                        # Si falla la conversión, usar None
                        uom_id = None
            
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

    def _normalize_products_qty_partner(self, products_qty_partner, qty=0, partner=False):
        """
        Normaliza el parámetro products_qty_partner para asegurar que sea una lista de tuplas.
        
        El método puede ser llamado de dos formas:
        1. _compute_price_rule([(product1, qty1, partner1), (product2, qty2, partner2)])
        2. _compute_price_rule(product, qty, partner)
        
        Esta función normaliza ambos casos al formato 1.
        """
        # Si ya es una lista de tuplas, retornarla
        if isinstance(products_qty_partner, (list, tuple)) and len(products_qty_partner) > 0:
            first_elem = products_qty_partner[0]
            # Verificar si es una lista de tuplas (product, qty, partner)
            if isinstance(first_elem, (list, tuple)) and len(first_elem) >= 3:
                return products_qty_partner
        
        # Si es un solo producto (recordset), convertirlo a lista de tuplas
        if hasattr(products_qty_partner, '_name') and products_qty_partner._name == 'product.product':
            return [(products_qty_partner, qty, partner)]
        
        # Caso por defecto: asumir que ya está en el formato correcto
        return products_qty_partner

    def _get_applicable_pricelist_items(self, products_qty_partner, date, uom_id):
        """
        Obtiene los items aplicables de la pricelist considerando la lógica AND.
        
        LÓGICA AND CORRECTA:
        - Para que un grupo AND sea válido, CADA regla del grupo debe tener
          al menos UN producto en el pedido que haga match con ella.
        - Si alguna regla del grupo no tiene ningún producto que haga match,
          entonces TODO el grupo AND se descarta.
        """
        self.ensure_one()
        
        # Normalizar products_qty_partner
        products_qty_partner = self._normalize_products_qty_partner(products_qty_partner)
        
        # NUEVO: Intentar obtener todos los productos desde el contexto
        all_order_products = self.env.context.get('all_order_products')
        if all_order_products:
            _logger.info(f"AND Logic: Usando productos del contexto: {len(all_order_products)} productos")
            products_qty_partner = all_order_products
        else:
            _logger.info(f"AND Logic: Productos recibidos: {len(products_qty_partner)} producto(s)")
        
        # Obtener todos los items activos de esta pricelist
        all_items = self.item_ids.filtered(lambda i: not i.date_start or i.date_start <= date).filtered(
            lambda i: not i.date_end or i.date_end >= date
        )
        
        # Separar reglas normales de reglas AND
        and_items = all_items.filtered(lambda i: i.apply_and_logic and i.and_group > 0)
        normal_items = all_items.filtered(lambda i: not i.apply_and_logic or i.and_group == 0)
        
        if not and_items:
            return all_items
        
        _logger.info(f"AND Logic: Encontradas {len(and_items)} reglas AND activas")
        
        # Agrupar por grupos AND
        and_groups = {}
        for item in and_items:
            if item.and_group not in and_groups:
                and_groups[item.and_group] = []
            and_groups[item.and_group].append(item)
        
        # Verificar grupos AND con la LÓGICA CORRECTA
        valid_and_items = self.env['product.pricelist.item']
        
        for group_id, group_items in and_groups.items():
            _logger.info(f"AND Logic: Evaluando grupo {group_id} con {len(group_items)} reglas")
            
            # Para que el grupo sea válido, CADA regla debe tener al menos
            # UN producto del pedido que haga match
            group_is_valid = True
            
            # Verificar CADA regla del grupo
            for rule_item in group_items:
                # Buscar si HAY AL MENOS UN producto que haga match con esta regla
                rule_has_match = False
                
                for prod_info in products_qty_partner:
                    # Desempaquetar la tupla de forma segura
                    if isinstance(prod_info, (list, tuple)):
                        if len(prod_info) >= 3:
                            product, qty, partner = prod_info[0], prod_info[1], prod_info[2]
                        elif len(prod_info) == 2:
                            product, qty = prod_info[0], prod_info[1]
                            partner = False
                        else:
                            product = prod_info[0]
                            qty = 1.0
                            partner = False
                    else:
                        product = prod_info
                        qty = 1.0
                        partner = False
                    
                    # Verificar si este producto hace match con la regla
                    if self._check_rule_match(rule_item, product, qty, partner, date, uom_id):
                        _logger.info(f"AND Logic: Regla {rule_item.id} (producto {rule_item.product_id.name if rule_item.product_id else 'N/A'}, min_qty: {rule_item.min_quantity}) hace MATCH con {product.name} (qty: {qty})")
                        rule_has_match = True
                        break  # Ya encontramos un match, no seguir buscando
                
                # Si esta regla NO tiene ningún producto que haga match,
                # entonces TODO el grupo AND es inválido
                if not rule_has_match:
                    _logger.info(f"AND Logic: Regla {rule_item.id} (producto {rule_item.product_id.name if rule_item.product_id else 'N/A'}, min_qty: {rule_item.min_quantity}) NO tiene match - Grupo {group_id} DESCARTADO")
                    group_is_valid = False
                    break  # No seguir verificando las demás reglas de este grupo
            
            # Si TODAS las reglas del grupo tienen al menos un producto que hace match,
            # entonces el grupo es válido y agregamos todas sus reglas
            if group_is_valid:
                _logger.info(f"AND Logic: Grupo {group_id} es VÁLIDO - Aplicando {len(group_items)} reglas")
                valid_and_items |= self.env['product.pricelist.item'].browse([i.id for i in group_items])
            else:
                _logger.info(f"AND Logic: Grupo {group_id} es INVÁLIDO - Descartando reglas")
        
        # Retornar reglas normales + reglas AND válidas
        result = normal_items | valid_and_items
        _logger.info(f"AND Logic: Retornando {len(result)} reglas totales ({len(normal_items)} normales + {len(valid_and_items)} AND)")
        return result

    def _compute_price_rule_get_items(self, products_qty_partner, date, **kwargs):
        """
        NUEVO MÉTODO: Override del método que Odoo 18 usa para obtener items.
        En lugar de modificar self.item_ids (que causa errores), sobrescribimos
        el método que retorna los items para filtrarlos según lógica AND.
        """
        # Verificar si hay reglas AND activas
        has_and_rules = any(
            item.apply_and_logic and item.and_group > 0 
            for item in self.item_ids
        )
        
        # Si no hay reglas AND, usar el comportamiento estándar
        if not has_and_rules:
            return super(ProductPricelist, self)._compute_price_rule_get_items(
                products_qty_partner, date, **kwargs
            )
        
        # Normalizar products_qty_partner
        qty = kwargs.get('qty', 1.0)
        partner = kwargs.get('partner', False)
        uom_id = kwargs.get('uom_id', False)
        normalized_products = self._normalize_products_qty_partner(products_qty_partner, qty, partner)
        
        # Obtener items aplicables considerando lógica AND
        applicable_items = self._get_applicable_pricelist_items(normalized_products, date, uom_id)
        
        return applicable_items

    @api.model
    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, compute_price=True, **kwargs):
        """
        Override del método principal de cálculo de precios para Odoo 18.
        Ahora usa _compute_price_rule_get_items en lugar de modificar self.item_ids.
        """
        # Llamar al método estándar - ahora _compute_price_rule_get_items
        # se encargará del filtrado
        return super(ProductPricelist, self)._compute_price_rule(
            products_qty_partner, date=date, uom_id=uom_id, compute_price=compute_price, **kwargs
        )
