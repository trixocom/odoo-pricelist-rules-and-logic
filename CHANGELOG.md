# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [17.0.1.0.0] - 2025-10-03

### Agregado
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
- [ ] Soporte para Odoo 16.0
- [ ] Soporte para Odoo 15.0
- [ ] Implementar operadores OR además de AND
- [ ] Interfaz visual mejorada para gestión de grupos
- [ ] Validaciones adicionales en formularios
- [ ] Traducción al inglés
- [ ] Documentación de API
- [ ] Ejemplos de integración con otros módulos
- [ ] Performance optimizations para grandes cantidades de reglas
