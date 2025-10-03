# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
