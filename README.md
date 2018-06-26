# vectortiles-postgis-openlayers

### Ejecutar el proyecto:
```docker-compose up```
> Docker es necesario

### Agregar datos a Postgis
##### 1. Crear una carpeta llamada `shapefiles` en la raíz del proyecto
##### 2. Ingresar al contenedor de postgis
```docker exec -it vpo_postgis bash```

##### 3. Ingresar a la carpeta shapefiles y generar el sql de un archivo shp
> Cada archivo shp requiere su respectivo dbf y shx

```cd shapefiles```

```shp2pgsql -s 4326 -I shapefile.shp public.nombre_tabla > nombre_tabla.sql```

> 4326 es el hace referencia a la proyección EPSG:4326, si el archivo esta en otra proyección debe ser reproyectado con una herramienta como QGIS

> Si sale error con la codificación agregar `-W "latin1"` al comando anterior

##### 4. Insertar los datos del sql en la base de datos
```psql -d geo24 -h db -U geo -f nombre_tabla.sql```

> El anterior comando requiere ingresar la contraseña, esta es **`geo`**

### Configurar los siguientes datos acorde a la tabla creada en `src/app.py`
```python
GEO_TABLE = 'provincias_ecuador'
ID_COLUMN = 'gid'
NAME_COLUMN = 'nombre_provincia'
```

### Abrir en proyecto en `localhost:5000`
> Los Vector Files se crearan dentro de `src/cache`, el rendimiento será bajo mientras estos son creados 

> Adicionalmente el proyecto viene con PgAdmin, se accede a este por `localhost:5050`
