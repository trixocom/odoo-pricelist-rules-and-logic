# Odoo Pricelist Rules AND Logic

## 📋 Descripción

Módulo de Odoo que permite implementar lógica AND entre reglas seleccionadas de lista de precios. Esto significa que puedes configurar múltiples reglas que deben cumplirse **todas simultáneamente** para que se aplique un descuento o precio especial.

## ✨ Características

- ✅ Campo booleano `Aplicar Lógica AND` en las reglas de lista de precios
- ✅ Campo `Grupo AND` para agrupar reglas que deben cumplirse conjuntamente
- ✅ Evaluación inteligente de múltiples condiciones
- ✅ Compatible con la lógica estándar de Odoo
- ✅ Interfaz de usuario intuitiva
- ✅ No rompe funcionalidad existente

## 🚀 Instalación

### Usando Git

```bash
cd /path/to/odoo/addons
git clone https://github.com/trixocom/odoo-pricelist-rules-and-logic.git
```

### Docker (Recomendado)

```bash
# Clonar en el volumen de addons personalizados
docker exec -it odoo bash
cd /mnt/extra-addons
git clone https://github.com/trixocom/odoo-pricelist-rules-and-logic.git
exit

# Reiniciar el contenedor
docker restart odoo
```

### Activación

1. Ve a **Aplicaciones** en Odoo
2. Actualiza la lista de aplicaciones
3. Busca "Pricelist Rules AND Logic"
4. Haz clic en **Instalar**

## 📖 Uso

### Ejemplo 1: Descuento por Cantidad Y Categoría

Supongamos que quieres ofrecer un 10% de descuento solo cuando:
- El cliente compra más de 50 unidades
- Y el producto pertenece a la categoría "Electrónica"

**Configuración:**

1. Ve a **Ventas > Productos > Listas de Precios**
2. Abre o crea una lista de precios
3. En la pestaña de reglas, crea dos reglas:

**Regla 1:**
- Cantidad mínima: 50
- Aplicar Lógica AND: ☑️
- Grupo AND: 1
- Descuento: 10%

**Regla 2:**
- Categoría: Electrónica
- Aplicar Lógica AND: ☑️
- Grupo AND: 1
- Descuento: 10%

Ahora el descuento del 10% solo se aplicará si AMBAS condiciones se cumplen.

### Ejemplo 2: Múltiples Grupos AND

Puedes crear diferentes grupos AND para diferentes escenarios:

**Grupo AND 1** (Promoción A):
- Regla 1: Producto = "Laptop X" + AND Grupo = 1
- Regla 2: Cantidad >= 10 + AND Grupo = 1
- Descuento: 15%

**Grupo AND 2** (Promoción B):
- Regla 3: Categoría = "Accesorios" + AND Grupo = 2
- Regla 4: Cantidad >= 100 + AND Grupo = 2
- Descuento: 20%

## 🔧 Configuración Técnica

### Dependencias

- Odoo 17.0
- Módulo `product` (incluido en Odoo)

### Versiones Soportadas

- ✅ Odoo 17.0 (probado)
- ⚠️ Odoo 16.0 (requiere ajustes menores)
- ⚠️ Odoo 15.0 (requiere ajustes)

## 🏗️ Estructura del Proyecto

```
odoo-pricelist-rules-and-logic/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── product_pricelist.py
├── views/
│   └── product_pricelist_views.xml
└── README.md
```

## 🐳 Docker & Portainer

### Docker Compose Example

```yaml
version: '3.8'
services:
  odoo:
    image: odoo:17.0
    container_name: odoo
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
      - ./config:/etc/odoo
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo_password

  db:
    image: postgres:15
    container_name: odoo-db
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo_password
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  odoo-data:
  db-data:
```

### Desplegar en Swarm

```bash
docker stack deploy -c docker-compose.yml odoo-stack
```

## 🧪 Testing

```python
# TODO: Agregar tests unitarios
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Roadmap

- [ ] Tests unitarios
- [ ] Soporte para Odoo 16.0 y 15.0
- [ ] Operadores OR además de AND
- [ ] Interfaz visual para crear grupos de reglas
- [ ] Validaciones adicionales
- [ ] Documentación en inglés

## 📄 Licencia

LGPL-3.0

## 👤 Autor

**TRX**

- GitHub: [@trixocom](https://github.com/trixocom)

## 🙏 Agradecimientos

- Comunidad de Odoo
- Contributors

---

⭐ Si este proyecto te ha sido útil, considera darle una estrella en GitHub!
