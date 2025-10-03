# Documentación Técnica - Integración con Odoo 18

## 📚 Cómo Funciona el Sistema de Listas de Precios en Odoo 18

### Conceptos Básicos

En Odoo 18, las listas de precios funcionan mediante el modelo `product.pricelist` y `product.pricelist.item`. El flujo básico es:

1. **Usuario agrega producto a una orden** → Se activa el cálculo de precio
2. **Odoo busca la lista de precios** → Asignada al cliente o por defecto
3. **Se evalúan las reglas** → En orden de especificidad
4. **Se aplica la primera regla que coincide** → O el precio base del producto

### Flujo de Cálculo en Odoo 18

```python
Orden de Venta
    ↓
product.pricelist._compute_price_rule(productos, cantidades, partner)
    ↓
product.pricelist._compute_price_rule_get_items()  # Obtiene items aplicables
    ↓
Evaluación de reglas por especificidad
    ↓
Retorna: {product_id: (price, rule_id)}
```

## 🔧 Implementación del Módulo AND Logic

### Arquitectura del Módulo

Este módulo extiende el comportamiento estándar sin romper la funcionalidad existente:

```
ProductPricelistItem (heredado)
  ├── apply_and_logic (Boolean)
  └── and_group (Integer)

ProductPricelist (heredado)
  ├── _compute_price_rule_get_items()  [OVERRIDE]
  ├── _check_rule_match()              [NUEVO]
  └── _compute_price_rule()            [OVERRIDE LIGERO]
```

### Método 1: `_compute_price_rule_get_items()`

**Propósito**: Filtrar items ANTES de que Odoo los evalúe.

**Lógica**:
1. Obtiene todos los items mediante `super()`
2. Separa items normales de items AND
3. Agrupa items AND por `and_group`
4. Para cada grupo AND:
   - Verifica que TODAS las reglas coincidan para TODOS los productos
   - Si todas coinciden → incluir grupo en items válidos
   - Si alguna falla → descartar todo el grupo
5. Retorna: items normales + items AND válidos

**Código simplificado**:
```python
def _compute_price_rule_get_items(self, products_qty_partner, date, uom_id):
    items = super()._compute_price_rule_get_items(...)
    
    # Separar reglas AND
    and_items = items.filtered(lambda i: i.apply_and_logic and i.and_group > 0)
    normal_items = items.filtered(lambda i: not i.apply_and_logic or i.and_group == 0)
    
    if not and_items:
        return items
    
    # Agrupar por grupo AND
    and_groups = {}
    for item in and_items:
        and_groups.setdefault(item.and_group, []).append(item)
    
    # Validar grupos
    valid_and_items = self.env['product.pricelist.item']
    for group_id, group_items in and_groups.items():
        if self._validate_and_group(group_items, products_qty_partner, date, uom_id):
            valid_and_items |= group_items
    
    return normal_items | valid_and_items
```

### Método 2: `_check_rule_match()`

**Propósito**: Verificar si una regla individual coincide con un producto/contexto.

**Validaciones**:
1. ✅ Producto específico o plantilla
2. ✅ Categoría (incluyendo categorías padres)
3. ✅ Cantidad mínima (con conversión de UoM)
4. ✅ Fechas de validez

**Código simplificado**:
```python
def _check_rule_match(self, item, product, quantity, partner, date, uom_id):
    # Verificar producto/plantilla
    if item.product_id and item.product_id != product:
        return False
    
    # Verificar categoría (recursivo)
    if item.categ_id:
        if not self._check_category_match(product.categ_id, item.categ_id):
            return False
    
    # Verificar cantidad mínima
    if item.min_quantity:
        converted_qty = self._convert_quantity(quantity, uom_id, item.product_uom_id)
        if converted_qty < item.min_quantity:
            return False
    
    # Verificar fechas
    if item.date_start and date < item.date_start:
        return False
    if item.date_end and date > item.date_end:
        return False
    
    return True
```

## 🎯 Casos de Uso

### Caso 1: Descuento por Volumen + Categoría

**Requisito**: 15% de descuento solo si:
- Cantidad >= 100 unidades
- Categoría = "Electrónica Premium"

**Configuración**:
```
Regla 1:
  - min_quantity: 100
  - apply_and_logic: True
  - and_group: 1
  - discount: 15%

Regla 2:
  - categ_id: "Electrónica Premium"
  - apply_and_logic: True
  - and_group: 1
  - discount: 15%
```

**Resultado**: 
- Si compras 150 unidades de "Laptop Gaming" (Electrónica Premium) → ✅ 15% descuento
- Si compras 150 unidades de "Teclado USB" (Accesorios) → ❌ Sin descuento
- Si compras 50 unidades de "Laptop Gaming" → ❌ Sin descuento

### Caso 2: Promoción Temporal + Cliente VIP

**Requisito**: Precio especial $500 solo si:
- Fecha: 01/12/2025 - 31/12/2025
- Cliente: Grupo VIP

**Configuración**:
```
Regla 1:
  - date_start: 2025-12-01
  - date_end: 2025-12-31
  - apply_and_logic: True
  - and_group: 2
  - fixed_price: 500

Regla 2:
  - (campo personalizado: is_vip = True)
  - apply_and_logic: True
  - and_group: 2
  - fixed_price: 500
```

## 🔍 Debugging y Troubleshooting

### Activar Modo Debug

```python
import logging
_logger = logging.getLogger(__name__)

# En _compute_price_rule_get_items
_logger.info(f"Items originales: {len(items)}")
_logger.info(f"Items AND: {len(and_items)}")
_logger.info(f"Grupos AND detectados: {list(and_groups.keys())}")
_logger.info(f"Items AND válidos: {len(valid_and_items)}")
```

### Verificar Reglas desde Shell

```python
# Conectar a Odoo shell
odoo-bin shell -d tu_database

# Obtener lista de precios
pricelist = env['product.pricelist'].browse(1)

# Obtener reglas AND
and_rules = pricelist.item_ids.filtered(
    lambda r: r.apply_and_logic and r.and_group > 0
)

# Ver grupos
groups = {}
for rule in and_rules:
    groups.setdefault(rule.and_group, []).append(rule.id)
print(f"Grupos AND: {groups}")

# Probar cálculo
product = env['product.product'].browse(123)
price, rule_id = pricelist._compute_price_rule(
    [(product, 100, env.user.partner_id)],
    date=fields.Date.today(),
    uom_id=product.uom_id
)
print(f"Precio: {price}, Regla: {rule_id}")
```

### Errores Comunes

#### Error 1: "El descuento no se aplica"

**Diagnóstico**:
```python
# Verificar que TODAS las reglas del grupo tengan:
# - Mismo número de grupo AND
# - apply_and_logic = True
# - and_group > 0

for rule in pricelist.item_ids.filtered(lambda r: r.and_group == 1):
    print(f"Regla {rule.id}: apply_and_logic={rule.apply_and_logic}, and_group={rule.and_group}")
```

#### Error 2: "Grupo AND no se evalúa"

**Causa**: Una regla del grupo no coincide.

**Solución**: Verificar cada regla individualmente:
```python
product = env['product.product'].browse(123)
for rule in group_rules:
    match = pricelist._check_rule_match(
        rule, product, 100, partner, date, uom
    )
    print(f"Regla {rule.id}: {'✅' if match else '❌'}")
```

## 📊 Performance

### Optimizaciones Implementadas

1. **Filtrado temprano**: Las reglas AND se filtran antes de evaluación costosa
2. **Caché de grupos**: Los grupos AND se calculan una sola vez
3. **Evaluación perezosa**: Solo se evalúan grupos potencialmente válidos
4. **Compatible con índices DB**: Las consultas usan índices existentes

### Recomendaciones

- ✅ Máximo 5-10 reglas por grupo AND
- ✅ Usar secuencias para ordenar reglas
- ✅ Evitar grupos AND muy complejos
- ⚠️ Cuidado con categorías muy profundas (>5 niveles)

## 🔄 Migración y Actualización

### Desde Odoo 17 a Odoo 18

1. **Actualizar `__manifest__.py`**:
```python
'version': '18.0.1.0.0',  # Cambiar de 17.0.1.0.0
```

2. **No requiere migración de datos**: La estructura de BD es compatible

3. **Reiniciar Odoo**:
```bash
odoo-bin -d tu_database -u odoo_pricelist_rules_and_logic
```

### Rollback (de 18 a 17)

```python
# En __manifest__.py
'version': '17.0.1.0.0',

# Restaurar vistas XML (usar attrs en lugar de invisible)
# Ver commit anterior en GitHub
```

## 🧪 Testing Manual

### Test 1: Grupo AND Básico

```python
# Setup
pricelist = env['product.pricelist'].create({'name': 'Test AND'})
product = env['product.product'].create({'name': 'Test Product'})

# Crear reglas
rule1 = env['product.pricelist.item'].create({
    'pricelist_id': pricelist.id,
    'product_id': product.id,
    'min_quantity': 10,
    'apply_and_logic': True,
    'and_group': 1,
    'percent_price': 10,
})

rule2 = env['product.pricelist.item'].create({
    'pricelist_id': pricelist.id,
    'categ_id': product.categ_id.id,
    'apply_and_logic': True,
    'and_group': 1,
    'percent_price': 10,
})

# Test con 10 unidades (debe aplicar)
price1, _ = pricelist._compute_price_rule(
    [(product, 10, env.user.partner_id)],
    date=fields.Date.today(),
    uom_id=product.uom_id
)
assert price1 < product.lst_price  # Debe tener descuento

# Test con 5 unidades (NO debe aplicar)
price2, _ = pricelist._compute_price_rule(
    [(product, 5, env.user.partner_id)],
    date=fields.Date.today(),
    uom_id=product.uom_id
)
assert price2 == product.lst_price  # No debe tener descuento
```

## 📞 Soporte

Para reportar bugs o solicitar features:
- Issues: https://github.com/trixocom/odoo-pricelist-rules-and-logic/issues
- Documentación: README.md, USAGE_GUIDE.md, CHANGELOG.md
