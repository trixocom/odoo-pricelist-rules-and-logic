# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.0.5] - 2025-10-03

### Corregido
- 🐛 **ValueError al desempaquetar products_qty_partner**: Corregido error al cambiar cantidades en líneas de venta
  - Error resuelto: "ValueError: not enough values to unpack (expected 3, got 1)"
  - El método `_compute_price_rule()` puede ser llamado de múltiples formas:
    - Con una lista de tuplas: `[(product, qty, partner), ...]`
    - Con un solo producto: `_compute_price_rule(product, qty=x, partner=y)`
  - Nuevo método `_normalize_products_qty_partner()` para unificar ambos formatos
  - Manejo robusto de desempaquetado de tuplas con soporte para 1, 2 o 3 elementos
  - Extracción segura de `qty` y `partner` desde kwargs cuando no están en la tupla

### Técnico
- Mejora en la robustez del código para manejar diferentes firmas de llamada
- Mejor compatibilidad con módulos de terceros que llaman a `_compute_price_rule()`
- Código más defensivo con validación de tipos y longitudes de tuplas

## [18.0.1.0.4] - 2025-10-03

### Corregido
- 🐛 **Método _compute_price_rule_get_items inexistente**: Corregido AttributeError al agregar productos a órdenes de venta
  - Error resuelto: "AttributeError: 'super' object has no attribute '_compute_price_rule_get_items'"
  - El método `_compute_price_rule_get_items()` no existe en Odoo 18, fue un método que asumimos incorrectamente
  - Solución: Eliminado el override de `_compute_price_rule_get_items` y movida toda la lógica a `_compute_price_rule`
  - Nuevo método: `_get_applicable_pricelist_items()` para obtener items filtrados según lógica AND
  - Modificación temporal de `self.item_ids` para filtrar items antes de llamar al super()

### Técnico
- Refactorización completa del manejo de filtrado de items de pricelist
- Enfoque más robusto que no depende de métodos inexistentes en la API de Odoo 18
- Mejor manejo del ciclo de vida de los items durante el cálculo de precios

## [18.0.1.0.3] - 2025-10-03

### Corregido
- 🐛 **Parámetro compute_price en _compute_price_rule**: Corregido TypeError al procesar órdenes de venta
  - Agregado parámetro explícito `compute_price=True` en la firma del método `_compute_price_rule()`
  - Error resuelto: "TypeError: ProductPricelist._compute_price_rule() got an unexpected keyword argument 'compute_price'"
  - El método `_get_product_rule()` de Odoo 18 llama a `_compute_price_rule()` con `compute_price=False`
  - Firma actualizada: `def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, compute_price=True, **kwargs)`

### Técnico
- Mejora en compatibilidad con API estándar de Odoo 18 para listas de precios
- Firma de método ahora coincide exactamente con la esperada por el core de Odoo 18

## [18.0.1.0.2] - 2025-10-03

### Corregido
- 🐛 **XPath en vista tree**: Corregido error de ParseError al heredar vista tree de items de lista de precios
  - Cambio de `//tree` con `position="inside"` a xpath específico apuntando al campo `name`
  - Solución: `<xpath expr="//field[@name='name']" position="after">` para agregar campos
  - El error ocurría porque Odoo 18 requiere xpaths más específicos en herencia de vistas
  - Error resuelto: "El elemento '<xpath expr="//tree">' no se puede localizar en la vista principal"

### Técnico
- Mejora en la herencia de vistas para mayor compatibilidad con Odoo 18
- Código más robusto siguiendo mejores prácticas de Odoo para herencia de vistas

## [18.0.1.0.1] - 2025-10-03

### Actualizado
- Versión inicial publicada en GitHub
- Documentación completa agregada

## [18.0.1.0.0] - 2025-10-03

### Actualizado para Odoo 18.0
- ✅ Código actualizado para compatibilidad total con Odoo 18.0
- ✅ Método `_compute_price_rule_get_items` implementado según nueva API de Odoo 18
- ✅ Reemplazo de atributo `attrs` por `invisible` en vistas XML (nuevo estándar Odoo 18)
- ✅ Docker Compose actualizado a imagen `odoo:18.0`
- ✅ Mejoras en el método `_check_rule_match` para mayor robustez
- ✅ Mejor manejo de conversiones de unidades de medida
- ✅ Validaciones mejoradas para fechas y cantidades mínimas

### Características Principales
- Campo `apply_and_logic` (booleano) en reglas de lista de precios
- Campo `and_group` (entero) para agrupar reglas AND
- Evaluación AND entre reglas del mismo grupo
- Compatible con múltiples grupos AND independientes
- No afecta el comportamiento de reglas normales

### Características Técnicas
- Override de método `_compute_price_rule` compatible con Odoo 18
- Método `_compute_price_rule_get_items` para filtrado de items
- Método `_check_rule_match` para verificar coincidencia de reglas individuales
- Vistas heredadas para formulario y árbol de items de lista de precios
- Documentación completa en README.md y USAGE_GUIDE.md

## [17.0.1.0.0] - 2025-10-03 (versión inicial)

### Agregado (versión para Odoo 17)
- Campo `apply_and_logic` (booleano) en reglas de lista de precios
- Campo `and_group` (entero) para agrupar reglas AND
- Override de método `_compute_price_rule` para implementar lógica AND
- Método `_check_rule_match` para verificar coincidencia de reglas individuales
- Método `_calculate_combined_price` para calcular precio con múltiples reglas
- Método `_get_applicable_rules` para obtener reglas aplicables
- Vistas heredadas para formulario y árbol de items de lista de precios
- Documentación completa en README.md
- Guía de uso en USAGE_GUIDE.md
- Docker Compose para desarrollo
- Archivo .gitignore para Python/Odoo
- Ejemplos de uso y casos comunes

### Características
- Soporte para múltiples grupos AND independientes
- Compatibilidad con lógica estándar de Odoo
- No rompe funcionalidad existente
- Interfaz de usuario intuitiva
- Evaluación inteligente de condiciones múltiples

## [Unreleased]

### Por Hacer
- [ ] Tests unitarios con pytest
- [ ] Soporte específico para Odoo 16.0 y 15.0
- [ ] Implementar operadores OR además de AND
- [ ] Interfaz visual mejorada para gestión de grupos
- [ ] Validaciones adicionales en formularios
- [ ] Traducción al inglés
- [ ] Documentación de API
- [ ] Ejemplos de integración con otros módulos
- [ ] Performance optimizations para grandes cantidades de reglas
- [ ] Wizard para creación asistida de grupos AND

## Notas de Migración

### De 17.0 a 18.0
1. Actualizar `__manifest__.py` version a `18.0.1.0.0`
2. La estructura de datos es compatible (no requiere migración de BD)
3. Las vistas XML usan el nuevo formato de Odoo 18
4. El método `_compute_price_rule` fue actualizado para usar la nueva API

### Compatibilidad
- **Odoo 18.0**: ✅ Totalmente compatible (versión actual)
- **Odoo 17.0**: ✅ Compatible (usar versión 17.0.1.0.0)
- **Odoo 16.0**: ⚠️ Requiere ajustes en el código
- **Odoo 15.0**: ⚠️ Requiere ajustes en el código
