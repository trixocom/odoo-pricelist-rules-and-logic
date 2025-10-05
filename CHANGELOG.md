# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.0.27] - 2025-10-05

### 🔥 FIX CRÍTICO - INTERCEPTAR MÉTODO CORRECTO EN ODOO 18

**Problema identificado**: El método `_get_applicable_pricelist_items` NO se estaba llamando en Odoo 18.

### Análisis del Problema

**Evidencia en logs:**
```
✅ AND Logic Sale: _compute_price_unit EJECUTÁNDOSE  (sale_order.py)
❌ AND Logic Pricelist: [SIN LOGS]  (product_pricelist.py NO ejecutándose)
```

**Diagnóstico:**
- El contexto se inyectaba correctamente desde `sale_order.py`
- Pero el método de filtrado de reglas NUNCA se ejecutaba
- Las reglas AND no se filtraban, aplicando comportamiento estándar

### Solución Implementada

**Cambio de arquitectura: Interceptar en `_get_product_price_rule()`**

En Odoo 18, el flujo correcto es:

```
_compute_price_unit() (sale.order.line)
    ↓
_get_product_price() (product.pricelist)
    ↓
_get_product_price_rule() (product.pricelist)  ← 🎯 INTERCEPTAMOS AQUÍ
    ↓
_compute_price_rule() (product.pricelist)
```

**Por qué este método:**
- ✅ Se ejecuta SIEMPRE que se calcula un precio
- ✅ Tiene acceso al producto, cantidad, UOM, fecha
- ✅ Retorna `(precio, rule_id)` - podemos controlar ambos
- ✅ Es el punto de control perfecto para validar grupos AND

### Lógica Implementada

```python
def _get_product_price_rule(self, product, quantity, uom, date, **kwargs):
    # 1. Si no hay reglas AND, comportamiento normal
    if not has_and_rules:
        return super()._get_product_price_rule(...)
    
    # 2. Si no hay contexto de orden, comportamiento normal
    if not order_products:
        return super()._get_product_price_rule(...)
    
    # 3. Llamar super() para obtener la regla que Odoo aplicaría
    price, rule_id = super()._get_product_price_rule(...)
    
    # 4. Si la regla no es AND, retornar normalmente
    if not rule.apply_and_logic:
        return price, rule_id
    
    # 5. Evaluar si el grupo AND es válido
    valid_groups = self._evaluate_and_groups_globally(...)
    
    # 6. Si el grupo NO es válido, NO aplicar descuento
    if rule.and_group not in valid_groups:
        return product.lst_price, False  # Precio sin descuento
    
    # 7. Grupo válido - aplicar descuento
    return price, rule_id
```

### Ventajas de este enfoque

✅ **Simple y directo:**
- Un solo punto de control
- Lógica clara y fácil de seguir

✅ **Logging completo:**
- Vemos exactamente qué está pasando
- Debugging fácil

✅ **No modifica flujo estándar:**
- Odoo calcula todo normalmente
- Solo validamos al final si aplicar o no

✅ **Caché de evaluación:**
- Evaluación global solo una vez por orden
- Resultado guardado en contexto

### Cambios Técnicos

**Archivo**: `models/product_pricelist.py`

**Eliminado:**
- Override de `_get_applicable_pricelist_items()` (no funciona en Odoo 18)

**Agregado:**
- Override de `_get_product_price_rule()` (método correcto)
- Validación de grupos AND DESPUÉS de que Odoo elija la regla
- Retorno de precio sin descuento si grupo inválido
- Logging detallado en cada paso

**Mantenido:**
- `_evaluate_and_groups_globally()` - evaluación de grupos
- `_check_product_match()` - verificación de reglas
- `_filter_rules_with_and_logic()` - filtrado (ahora interno)

### Testing

```bash
# 1. Actualizar código
cd /mnt/extra-addons/odoo-pricelist-rules-and-logic
git pull origin main

# 2. CRÍTICO: Reiniciar Odoo completamente
docker-compose restart odoo
sleep 30

# 3. Actualizar módulo desde UI
# Aplicaciones → "Pricelist Rules AND Logic" → Actualizar

# 4. Ver logs en tiempo real
docker logs amfanet-odoo-1 -f | grep "AND Logic"
```

### Casos de Prueba

**Configuración de prueba:**
- Lista de precios: "lista prueba 3% descuento (ARS)"
- Regla 1: Producto 1043A, min_qty=30, precio fijo=$100, AND=true, grupo=1
- Regla 2: Producto 1111, min_qty=15, precio fijo=$80, AND=true, grupo=1

**Test 1: Ambos productos cumplen ✅**
```
Orden: 1043A (50 unidades) + 1111 (50 unidades)
Resultado esperado:
  - 1043A: $100 (regla AND aplicada)
  - 1111: $80 (regla AND aplicada)
  - Logs: "GRUPO 1 VÁLIDO - Todas las reglas tienen match"
```

**Test 2: Un producto NO cumple ❌**
```
Orden: 1043A (20 unidades) + 1111 (50 unidades)
Resultado esperado:
  - 1043A: precio lista (sin descuento)
  - 1111: precio lista (sin descuento)
  - Logs: "GRUPO 1 INVÁLIDO - qty insuficiente (20 < 30)"
```

**Test 3: Solo un producto en orden ❌**
```
Orden: 1043A (50 unidades) solamente
Resultado esperado:
  - 1043A: precio lista (sin descuento)
  - Logs: "Regla '1111' NO tiene match - GRUPO 1 INVÁLIDO"
```

### Qué buscar en los logs

**🟢 Logs correctos (funcionando):**
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
AND Logic Pricelist: _get_product_price_rule EJECUTÁNDOSE
  Pricelist: lista prueba 3% descuento
  Producto: 1043A
  Cantidad: 50.0
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AND Logic: Evaluación GLOBAL de grupos AND
  Total productos en orden: 2
    - 1043A: qty=50.0
    - 1111: qty=50.0

AND Logic: === Evaluando GRUPO 1 GLOBALMENTE ===
  Reglas en grupo: 2

  Verificando regla: 1043A (min_qty=30.0)
    ✓ MATCH: 1043A con qty=50.0 cumple la regla

  Verificando regla: 1111 (min_qty=15.0)
    ✓ MATCH: 1111 con qty=50.0 cumple la regla

✅ GRUPO 1 VÁLIDO - Todas las reglas tienen match
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AND Logic Pricelist: GRUPO 1 VÁLIDO - Aplicar descuento
  Retornando precio: 100.0
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

**🔴 Problema si NO ves:**
```
# Si NO ves "AND Logic Pricelist:" significa que:
- El método NO se ejecuta
- Reinicia Odoo completamente
- Verifica que el módulo esté actualizado
```

### Impacto

- 🔥 **CRÍTICO**: Ahora el filtrado de reglas AND SÍ funciona
- ✅ Logs detallados en cada paso
- ✅ Fácil de debuggear
- ✅ Compatible con flujo estándar de Odoo
- ✅ Performance optimizada (evaluación global una sola vez)

## [18.0.1.0.26] - 2025-10-04

### 🔧 Reestructuración: Evaluación GLOBAL de grupos AND

(ver versiones anteriores en historial completo)

## [18.0.1.0.23] - 2025-10-04

### 🔥 FIX CRÍTICO - ELIMINAR LLAMADA MANUAL A get_product_price

(ver versiones anteriores en historial completo)
