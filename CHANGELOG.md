# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.0.23] - 2025-10-04

### 🔥 FIX CRÍTICO - ELIMINAR LLAMADA MANUAL A get_product_price

**Error corregido**: `AttributeError: 'product.pricelist' object has no attribute 'get_product_price'. Did you mean: '_get_product_price'?`

### Problema Identificado

El archivo `sale_order.py` estaba llamando manualmente a `get_product_price()` del pricelist, pero:

1. El método `get_product_price()` (sin guion bajo) **no existe en Odoo 18**
2. **NO ES NECESARIO** llamar manualmente al pricelist
3. Con el override de `_get_applicable_rules()` ya implementado, el filtrado es automático

```python
# INCORRECTO - llamada manual innecesaria ✗
price = pricelist_with_context.get_product_price(...)  # Este método no existe
line.price_unit = price
```

### Solución Implementada

**Arquitectura correcta:**

1. **`sale_order.py`**: Solo inyecta contexto con productos de la orden
2. **`product_pricelist.py`**: Filtra reglas automáticamente en `_get_applicable_rules()`
3. **Odoo estándar**: Calcula precios normalmente usando reglas filtradas

```python
# CORRECTO - solo inyectar contexto y dejar que Odoo trabaje ✓
line_with_context = line.with_context(
    pricelist_order_products=order_products
)

# Dejar que Odoo calcule el precio normalmente
super(SaleOrderLine, line_with_context)._compute_price_unit()

# El override de _get_applicable_rules() filtrará automáticamente
```

### Flujo de Ejecución Correcto

1. Usuario cambia cantidad en línea de venta
2. `sale_order.py::_compute_price_unit()` se ejecuta
3. **Inyectamos contexto** con todos los productos de la orden
4. Llamamos a `super()._compute_price_unit()` con el contexto
5. Odoo internamente llama a `pricelist._compute_price_rule()`
6. Que a su vez llama a `pricelist._get_applicable_rules()`
7. **NUESTRO OVERRIDE** intercepta aquí y filtra reglas AND
8. Odoo continúa calculando precio con reglas filtradas
9. Precio se asigna automáticamente a la línea

### Cambios Técnicos

**Archivo**: `models/sale_order.py`

**Eliminado:**
- Llamada manual a `pricelist_with_context.get_product_price()`
- Asignación manual de `line.price_unit = price`
- Lógica innecesaria de cálculo manual de precios

**Mantenido:**
- Detección de reglas AND activas
- Recopilación de productos de la orden
- Inyección de contexto `pricelist_order_products`
- Logging para depuración

**Agregado:**
- Lógica para procesar múltiples órdenes si es necesario
- Separación clara entre líneas con/sin reglas AND
- Llamada correcta a `super()` con contexto inyectado

### Por qué esta arquitectura es correcta

✅ **Separación de responsabilidades:**
- `sale_order.py`: Maneja contexto de la orden
- `product_pricelist.py`: Filtra reglas según lógica de negocio
- Odoo core: Calcula precios usando su lógica estándar

✅ **No duplica lógica:**
- No reimplementamos cálculo de precios
- Solo filtramos qué reglas se usan

✅ **Compatible con extensiones:**
- Otros módulos que modifiquen precios funcionan normalmente
- No interferimos con flujo estándar de Odoo

✅ **Mantenible:**
- Código más simple y claro
- Menos puntos de falla
- Fácil de debuggear

### Testing

```bash
# 1. Actualizar código
cd /mnt/extra-addons/odoo-pricelist-rules-and-logic
git pull origin main

# 2. CRÍTICO: Reiniciar Odoo
docker-compose restart odoo

# 3. Actualizar módulo desde UI
# Aplicaciones → "Pricelist Rules AND Logic" → Actualizar

# 4. Pruebas:
# - Crear orden de venta
# - Agregar productos con cantidades
# - Cambiar lista de precios
# - MODIFICAR cantidades
# - Botón "Actualizar precios"
# - TODO debe funcionar sin errores

# 5. Revisar logs
docker logs odoo --tail=100 -f | grep "AND Logic"
```

### Casos de Prueba

**Caso 1: Cambiar cantidad** ✓
- Agregar 1043A con 40 unidades
- Cambiar a 50 unidades
- Precio se recalcula automáticamente

**Caso 2: Cambiar lista de precios** ✓
- Crear orden con productos
- Cambiar de "Predeterminado" a "lista prueba 3%"
- Precios se actualizan automáticamente

**Caso 3: Botón actualizar precios** ✓
- Crear orden con productos
- Cambiar lista
- Pulsar "Actualizar precios"
- TODO funciona correctamente

### Impacto

- ✅ **CRÍTICO**: Error de método inexistente resuelto
- ✅ Arquitectura correcta y mantenible
- ✅ Código más simple y claro
- ✅ Compatible con todo el ecosistema Odoo
- ✅ Fácil de extender en el futuro
- ✅ Sin duplicación de lógica

## [18.0.1.0.22] - 2025-10-04

(versiones anteriores... ver historial completo arriba)
