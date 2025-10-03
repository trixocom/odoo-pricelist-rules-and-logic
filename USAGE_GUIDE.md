# Guía de Uso: Pricelist Rules AND Logic

## 🎯 Casos de Uso Comunes

### Caso 1: Descuento por Volumen Y Cliente VIP

**Objetivo:** Ofrecer 20% de descuento solo a clientes VIP que compren más de 100 unidades.

**Configuración:**
1. Crear dos reglas en la lista de precios:

```
Regla 1 - Condición de Cantidad:
- Cantidad mínima: 100
- Aplicar Lógica AND: ☑️
- Grupo AND: 1
- Tipo de cálculo: Porcentaje
- Porcentaje de precio: 20%

Regla 2 - Condición de Cliente:
- (Asumiendo que tienes un campo personalizado para clientes VIP)
- Aplicar Lógica AND: ☑️
- Grupo AND: 1
```

### Caso 2: Precio Especial por Temporada Y Ubicación

**Objetivo:** Precio especial de $50 para productos en temporada alta vendidos en ciertas ubicaciones.

```
Regla 1 - Temporada:
- Fecha inicio: 2025-12-01
- Fecha fin: 2025-12-31
- Aplicar Lógica AND: ☑️
- Grupo AND: 2
- Tipo: Precio fijo
- Precio fijo: $50

Regla 2 - Ubicación:
- (Campo personalizado de ubicación)
- Aplicar Lógica AND: ☑️
- Grupo AND: 2
```

### Caso 3: Promoción Cruzada (Combo)

**Objetivo:** 15% de descuento al comprar Producto A Y Producto B juntos.

```
Regla 1:
- Producto: Producto A
- Aplicar Lógica AND: ☑️
- Grupo AND: 3
- Descuento: 15%

Regla 2:
- Producto: Producto B
- Aplicar Lógica AND: ☑️
- Grupo AND: 3
- Descuento: 15%
```

## 📊 Diagrama de Flujo de Decisión

```
┌─────────────────────────────────┐
│  Calcular precio de producto    │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ ¿Hay reglas con "AND Logic"?    │
└──────┬──────────────┬───────────┘
       │ No           │ Sí
       │              ▼
       │    ┌──────────────────────┐
       │    │ Agrupar por Grupo AND│
       │    └──────┬───────────────┘
       │           │
       │           ▼
       │    ┌──────────────────────────┐
       │    │ Para cada grupo:         │
       │    │ ¿Todas las reglas se     │
       │    │ cumplen?                 │
       │    └───┬──────────────┬───────┘
       │        │ Sí           │ No
       │        ▼              │
       │    ┌────────────┐    │
       │    │ Aplicar    │    │
       │    │ precio     │    │
       │    │ combinado  │    │
       │    └────────────┘    │
       │                      │
       ▼                      ▼
┌──────────────────────────────────┐
│  Aplicar lógica estándar de Odoo │
└──────────────────────────────────┘
```

## 🔍 Ejemplos de Debugging

### Verificar si las reglas se aplican

Puedes agregar logging temporal en el código para debug:

```python
import logging
_logger = logging.getLogger(__name__)

# En el método _compute_price_rule
_logger.info(f"Reglas AND encontradas: {and_rules}")
_logger.info(f"Grupos AND: {and_groups}")
_logger.info(f"Precio calculado: {price}")
```

### Probar condiciones manualmente

En el shell de Odoo:

```python
# Obtener lista de precios
pricelist = env['product.pricelist'].browse(1)

# Obtener producto
product = env['product.product'].browse(1)

# Calcular precio
price, rule_id = pricelist._compute_price_rule(product, 100)

print(f"Precio: {price}, Regla ID: {rule_id}")
```

## ⚠️ Consideraciones Importantes

### 1. Orden de Evaluación
- Las reglas AND se evalúan **antes** que las reglas normales
- Dentro de un grupo AND, las reglas se aplican en orden de secuencia
- Solo se necesita que UN grupo AND se cumpla completamente

### 2. Compatibilidad con Reglas Normales
- Las reglas normales (sin AND logic) funcionan como siempre
- Si ningún grupo AND se cumple, se aplican las reglas normales
- Puedes mezclar reglas AND y normales en la misma lista de precios

### 3. Performance
- Muchas reglas AND pueden afectar el rendimiento
- Recomendado: máximo 5-10 reglas por grupo AND
- Usa índices en campos personalizados si filtras por ellos

## 🐛 Troubleshooting

### Problema: El descuento no se aplica

**Solución:**
1. Verifica que TODAS las reglas del grupo tengan el mismo número de grupo AND
2. Confirma que TODAS las condiciones se cumplen (cantidad, categoría, fechas, etc.)
3. Revisa la secuencia de las reglas
4. Verifica que el campo "Aplicar Lógica AND" esté marcado

### Problema: Se aplica el descuento incorrecto

**Solución:**
1. Revisa el orden de secuencia de las reglas
2. Verifica que no haya grupos AND duplicados con diferentes descuentos
3. Confirma que las reglas tengan el tipo de cálculo correcto

### Problema: Conflicto con otras personalizaciones

**Solución:**
1. Verifica que no haya otros módulos que sobrescriban `_compute_price_rule`
2. Revisa el orden de carga de módulos en el `__manifest__.py`
3. Usa `super()` correctamente si hay herencia múltiple

## 📧 Soporte

Si encuentras algún problema:
1. Revisa los logs de Odoo
2. Verifica la configuración de las reglas
3. Abre un issue en GitHub: https://github.com/trixocom/odoo-pricelist-rules-and-logic/issues

## 🔄 Actualizaciones

Después de actualizar el módulo:

```bash
# Actualizar el módulo
odoo-bin -d tu_database -u odoo-pricelist-rules-and-logic

# O desde la interfaz:
# Aplicaciones > Buscar módulo > Actualizar
```

## 💡 Tips y Trucos

### Tip 1: Usar grupos AND para promociones temporales
Crea grupos AND separados para cada promoción, así puedes activar/desactivar fácilmente.

### Tip 2: Documentar las reglas
Usa el campo de descripción para explicar qué hace cada grupo AND.

### Tip 3: Probar en entorno de desarrollo
Siempre prueba las reglas complejas en un entorno de desarrollo primero.

### Tip 4: Backup antes de cambios importantes
Haz backup de tu base de datos antes de modificar reglas críticas.
