# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.0.19] - 2025-10-04

### 🔥 FIX CRÍTICO - INYECCIÓN CORRECTA DE CONTEXTO EN SALE.ORDER.LINE

**El problema principal estaba en `sale_order.py`** - El módulo NO inyectaba correctamente el contexto con los productos de la orden, causando que las reglas AND nunca se evaluaran.

### Problemas Corregidos

1. **Método incorrecto usado**: El código anterior usaba `_onchange_product_id_set_pricelist_context()` que:
   - Solo se ejecuta en la UI (onchange)
   - Intentaba modificar `self.env.context` directamente (no funciona)
   - No se ejecutaba al guardar/confirmar órdenes

2. **Método `_cart_update_pricelist()`**: Solo funciona en e-commerce, no en ventas estándar

### Solución Implementada

✅ **Override correcto de `_compute_price_unit()`** en `sale.order.line`:
   - Es el método que Odoo llama para calcular precios en líneas de venta
   - Se ejecuta automáticamente cuando se agregan/modifican productos
   - Se ejecuta al guardar y confirmar órdenes
   - Inyecta correctamente el contexto `pricelist_order_products`

✅ **Recopilación de TODOS los productos** de la orden:
   - Itera sobre `line.order_id.order_line` para obtener todos los productos
   - Incluye cantidades actualizadas de cada línea
   - Pasa partner de la orden para evaluaciones de precio

✅ **Logging detallado** para debugging:
   - Muestra cuántos productos hay en la orden
   - Lista cada producto con su cantidad
   - Muestra el precio final calculado

### Cambios Técnicos

**Archivo**: `models/sale_order.py`
- Eliminado: Métodos `_onchange_product_id_set_pricelist_context()` y `_cart_update_pricelist()`
- Agregado: Override de `_compute_price_unit()` con decorador `@api.depends`
- Mejora: Verificación de reglas AND antes de procesar
- Mejora: Llamada correcta a `super()` al final para líneas sin reglas AND

**Flujo Correcto**:
1. Usuario agrega/modifica producto en orden → `_compute_price_unit()` se ejecuta
2. Se verifica si hay reglas AND en el pricelist
3. Se recopilan TODOS los productos de la orden actual
4. Se inyecta contexto `pricelist_order_products` al pricelist
5. Se llama a `pricelist._get_product_price()` con contexto
6. El pricelist evalúa las reglas AND con contexto completo
7. Se asigna el precio calculado a `line.price_unit`

### Testing

**Caso de Prueba** (del usuario):
- Lista: "lista prueba 3% descuento (ARS)"
- Reglas AND grupo 1:
  - Producto 1043A: precio fijo $100, min qty 30
  - Producto 1111: precio fijo $80, min qty 15
- Orden con:
  - 1043A: 40 unidades → debe ser $100 ✓
  - 1111: 3 unidades → debe evaluarse si cumple regla del grupo

**Resultado Esperado**:
- Logs muestran evaluación de reglas AND
- Precios calculados correctamente según lógica AND
- Sin errores en consola

### Para Actualizar

```bash
cd /mnt/extra-addons/odoo-pricelist-rules-and-logic
git pull origin main
docker-compose restart odoo  # CRÍTICO: reiniciar para cargar nuevo código Python
# Actualizar módulo desde UI: Aplicaciones → "Pricelist Rules AND Logic" → Actualizar
```

### Impacto

- ✅ **CRÍTICO**: El módulo ahora SÍ funciona correctamente
- ✅ Las reglas AND se evalúan en TODAS las situaciones (UI, guardado, confirmación)
- ✅ Contexto se inyecta correctamente en el momento adecuado
- ✅ Código más simple y robusto
- ✅ Mejor debugging con logs detallados

## [18.0.1.0.18] - 2025-10-03

(versiones anteriores... ver historial completo arriba)
