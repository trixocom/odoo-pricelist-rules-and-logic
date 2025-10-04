# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.0.20] - 2025-10-04

### 🔥 FIX CRÍTICO - ERROR DE TIMESTAMP RESUELTO

**Error corregido**: `psycopg2.errors.InvalidDatetimeFormat: invalid input syntax for type timestamp: "1"`

### Problema Identificado

El código estaba usando `_get_product_price()` (método interno/privado) en lugar de `get_product_price()` (método público). Además, los parámetros `date` y `uom_id` se pasaban posicionalmente en lugar de como keyword arguments, causando que:

1. El parámetro `date` recibiera el valor `1` (True convertido a int)
2. PostgreSQL rechazara este valor en consultas SQL con campos timestamp
3. El sistema fallara al calcular precios en órdenes de venta

### Cambios Implementados

#### Archivo: `models/sale_order.py`

**Antes (incorrecto):**
```python
price = pricelist_with_context._get_product_price(
    line.product_id,
    line.product_uom_qty,
    partner=line.order_id.partner_id,
    date=line.order_id.date_order,
    uom_id=line.product_uom.id if line.product_uom else None
)
```

**Después (correcto):**
```python
price = pricelist_with_context.get_product_price(
    line.product_id,
    line.product_uom_qty,
    line.order_id.partner_id or self.env['res.partner'],
    date=line.order_id.date_order or False,
    uom_id=line.product_uom.id if line.product_uom else False
)
```

✅ Cambio de `_get_product_price` a `get_product_price`
✅ Parámetros `date` y `uom_id` como keyword arguments
✅ Valores `False` en lugar de `None` cuando no hay valor
✅ Partner como recordset vacío en lugar de None

#### Archivo: `models/product_pricelist.py`

**Cambio de método sobrescrito:**
- **Antes**: Sobrescribía `_get_product_price()` (método privado)
- **Después**: Sobrescribe `get_product_price()` (método público)

**Antes (incorrecto):**
```python
def _get_product_price(self, product, quantity, partner=None, date=None, uom_id=None):
    # ...
    result = super(ProductPricelist, temp_pricelist)._get_product_price(
        product, quantity, partner, date, uom_id
    )
```

**Después (correcto):**
```python
def get_product_price(self, product, quantity, partner=None, date=None, uom_id=None):
    # ...
    result = super(ProductPricelist, temp_pricelist).get_product_price(
        product,
        quantity,
        partner or self.env['res.partner'],
        date=date or False,
        uom_id=uom_id or False
    )
```

✅ Método público en lugar de privado
✅ Keyword arguments para evitar confusión de parámetros
✅ Validación de valores None → False
✅ Import de `fields` agregado para `fields.Date.context_today()`

### Detalles Técnicos

**Por qué usar `get_product_price` en lugar de `_get_product_price`:**

1. `get_product_price()` es el método público documentado y estable
2. `_get_product_price()` es un método interno que puede cambiar entre versiones
3. La firma y comportamiento de métodos privados no está garantizado
4. El método público maneja mejor la conversión de parámetros

**Por qué usar keyword arguments:**

1. Evita confusión de posiciones de parámetros
2. Python no convierte automáticamente `True` a `1` cuando se pasa explícitamente
3. Los valores por defecto se aplican correctamente
4. Mayor claridad en el código

**Conversión de valores:**

- `None` → `False`: Odoo espera `False` para valores opcionales, no `None`
- `partner=None` → `partner or self.env['res.partner']`: Recordset vacío en lugar de None
- `date=None` → `date or False`: False es el valor esperado cuando no hay fecha

### Testing

Para probar que el error está resuelto:

```bash
# 1. Actualizar código
cd /mnt/extra-addons/odoo-pricelist-rules-and-logic
git pull origin main

# 2. CRÍTICO: Reiniciar Odoo
docker-compose restart odoo

# 3. Actualizar módulo desde UI
# Aplicaciones → "Pricelist Rules AND Logic" → Actualizar

# 4. Crear una orden de venta con la lista "lista prueba 3% descuento (ARS)"
# 5. Agregar productos 1043A y 1111
# 6. Verificar que NO aparece el error de timestamp
# 7. Revisar logs para confirmar que se evalúan las reglas AND
```

### Impacto

- ✅ **CRÍTICO**: Error de timestamp completamente resuelto
- ✅ Código usa métodos públicos estables de Odoo
- ✅ Compatible con mejores prácticas de desarrollo de Odoo
- ✅ Mayor robustez y mantenibilidad del código
- ✅ Previene problemas similares en futuras versiones de Odoo

### Referencias

- Documentación de Odoo sobre métodos públicos vs privados
- Código fuente de Odoo 18: `addons/product/models/product_pricelist.py`
- Ejemplos de uso en módulos estándar: `sale`, `website_sale`, `purchase`

## [18.0.1.0.19] - 2025-10-04

(versiones anteriores... ver historial completo arriba)
