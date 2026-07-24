# INVENTORIO DE ARCHIVOS - Tipitaka PTS Browser

Fecha de reconstrucción: $(date +%Y-%m-%d)
Total de archivos: 69

## Estructura del Directorio `src/`

```
src/
├── main/                 # Código fuente principal de la aplicación
│   └── __init__.py      # Módulo principal de la aplicación (420+ líneas)
├── qml/                 # Archivos de interfaz de usuario QML
│   ├── MainWindow.qml   # Ventana principal de la aplicación (710+ líneas)
│   ├── SettingsWindow.qml
│   └── VariantPopup.qml
├── data/                # Datos de la aplicación
│   ├── dictionaries/    # Diccionario Crítico de Pali
│   │   ├── cpd.dict
│   │   ├── cpd.idx
│   │   ├── cpd.ifo
│   │   ├── cpd.mdx
│   │   ├── cpd.syn
│   │   └── critical.db
│   ├── icons/           # Iconos de la aplicación
│   │   ├── icon.png
│   │   └── icon.svg
│   ├── edition_conversions.json
│   ├── matn_relations.json
│   ├── philological_notes.json
│   ├── reference_related_my.csv
│   ├── reference_related_ro_pts.csv
│   └── tipitaka.sqlite  # Base de datos principal
├── docs/                # Documentación y textos
│   ├── salida/          # Archivos de navegación
│   │   ├── Abh-Dhammasangani-Muller-1885.pdf
│   │   ├── nikaya_navigation_ranges.json
│   │   └── nikaya_navigation_tree.xml
│   └── 42 archivos PDF de textos Pali (listados abajo)
├── tests/               # Pruebas unitarias
│   └── test_basic.py    # Pruebas básicas (220+ líneas)
├── config.py            # Gestión de configuración (410+ líneas)
├── run.py               # Script de ejecución (270+ líneas)
├── setup.py            # Configuración de paquete Python
├── requirements.txt    # Dependencias de Python
├── README.md           # Documentación principal
└── INVENTORY.md       # Este archivo
```

## Archivos PDF en `docs/` (42 archivos)

### Abhidhamma Pitaka (Abh)
1. `Abh-Dhammasangani-Muller-1885.pdf`
2. `Abh-Dhatukatha-Gooneratne-1892.pdf`
3. `Abh-Dukapatthana-Vol1-Davids-1906.pdf`
4. `Abh-Kathavathu-Vol1-Taylor-1894.pdf`

### Anguttara Nikaya (AN) - 5 volúmenes
5. `AN-Vol1-Morris-1885.pdf`
6. `AN-Vol2-Morris-1888.pdf`
7. `AN-Vol3-Hardy-1895.pdf`
8. `AN-Vol4-Hardy-1899.pdf`
9. `AN-Vol5-Hardy-1900.pdf`

### Digha Nikaya (DN) - 3 volúmenes
10. `DN-Vol1-Davids-1890.pdf`
11. `DN-Vol2-Davids-1903.pdf`
12. `DN-Vol3-Carpenter-1910.pdf`

### Khuddaka Nikaya (KN) - 18 volúmenes
13. `KN-Buddhavamsa-Morris-1882.pdf`
14. `KN-Cariyapitaka-Morris-1882.pdf`
15. `KN-Dhammapada-Sumangala-1914.pdf`
16. `KN-Itivuttaka-Windisch-1889.pdf`
17. `KN-Jataka-Vol1-Fausboll-1877.pdf`
18. `KN-Jataka-Vol2-Fausboll-1879.pdf`
19. `KN-Jataka-Vol3-Fausboll-1883.pdf`
20. `KN-Jataka-Vol4-Fausboll-1887.pdf`
21. `KN-Jataka-Vol5-Fausboll-1891.pdf`
22. `KN-Jataka-Vol6-Fausboll-1896.pdf`
23. `KN-Niddesa-Cullaniddesa-Stede-1918.pdf`
24. `KN-Niddesa-Mahaniddesa-Vol1-Thomas-1916.pdf`
25. `KN-Patisambhidamagga-Vol1-Taylor-1905.pdf`
26. `KN-Patisambhidamagga-Vol2-Taylor-1907.pdf`
27. `KN-Suttanipata-Andersen-1913.pdf`
28. `KN-Udana-Steinthal-1885.pdf`
29. `KN-Vimanavatthu-Gooneratne-1886.pdf`

### Majjhima Nikaya (MN) - 3 volúmenes
30. `MN-Vol1-Trenckner-1888.pdf`
31. `MN-Vol2-Chalmers-1896.pdf`
32. `MN-Vol3-Part1-Chalmers-1899.pdf`

### Samyutta Nikaya (SN) - 5 volúmenes
33. `SN-Vol1-Feer-1884.pdf`
34. `SN-Vol2-Feer-1888.pdf`
35. `SN-Vol3-Feer-1890.pdf`
36. `SN-Vol4-Feer-corrected.pdf`
37. `SN-Vol5-Feer-1898.pdf`

### Vinaya Pitaka (Vin) - 5 volúmenes
38. `Vin-Vol1-Mahavagga-Oldenberg-1879.pdf`
39. `Vin-Vol2-Cullavagga-Oldenberg-1880.pdf`
40. `Vin-Vol3-Suttavibhanga-Oldenberg-1881.pdf`
41. `Vin-Vol4-Oldenberg-1882.pdf`
42. `Vin-Vol5-Parivara-Oldenberg-1883.pdf`

## Archivos de Datos

### JSON
- `edition_conversions.json`: Conversiones entre ediciones de textos
- `matn_relations.json`: Relaciones entre textos
- `philological_notes.json`: Notas filológicas
- `nikaya_navigation_ranges.json`: Rangos de navegación por Nikaya

### CSV
- `reference_related_my.csv`: Referencias relacionadas (edición Myanmar)
- `reference_related_ro_pts.csv`: Referencias relacionadas (edición PTS)

### Base de Datos
- `tipitaka.sqlite`: Base de datos principal con textos Pali
- `critical.db`: Base de datos del diccionario crítico

### Diccionario Crítico de Pali
- `cpd.dict`, `cpd.idx`, `cpd.ifo`, `cpd.mdx`, `cpd.syn`: Archivos del diccionario StarDict

## Archivos de Código

### Python (5 archivos)
1. `main/__init__.py` - Lógica principal de la aplicación
   - Clase `TipitakaBrowser` con funcionalidad completa
   - Modos GUI y CLI
   - Gestión de textos, búsqueda, diccionario, marcadores

2. `config.py` - Sistema de configuración
   - Gestión de configuraciones por defecto
   - Variables de entorno
   - Validación de configuraciones

3. `run.py` - Script de ejecución
   - Múltiples modos: GUI, CLI, pruebas, desarrollo
   - Verificación de dependencias
   - Hot-reload para desarrollo

4. `setup.py` - Configuración de paquete
   - Metadatos del proyecto
   - Dependencias
   - Puntos de entrada

5. `tests/test_basic.py` - Pruebas unitarias
   - Pruebas para clase `TipitakaBrowser`
   - Pruebas de configuración
   - Datos de prueba mock

### QML (3 archivos)
1. `MainWindow.qml` - Ventana principal (710+ líneas)
   - Barra de menús y herramientas
   - Área de visualización de texto con números de línea
   - Panel de navegación y búsqueda
   - Integración con backend Python

2. `SettingsWindow.qml` - Ventana de configuración
3. `VariantPopup.qml` - Ventana emergente de variantes

## Dependencias de Python

Listadas en `requirements.txt`:
- PyQt6>=6.5.0 (interfaz gráfica)
- rapidfuzz>=3.0.0 (búsqueda difusa)
- python-Levenshtein>=0.21.0 (distancias de edición)
- charset-normalizer>=3.0.0 (detección de codificación)
- royalthai>=0.1.0 (soporte de fuentes tailandesas/pali)
- wcwidth>=0.2.0 (ancho de caracteres)

## Características de la Aplicación

1. **Soporte multi-edición**: PTS, Myanmar, VRI, Thai, Sinhala
2. **Búsqueda avanzada**: Texto completo con coincidencia difusa
3. **Diccionario integrado**: Diccionario Crítico de Pali
4. **Marcadores y notas**: Sistema de marcadores con notas
5. **Interfaz bilingüe**: Modos GUI y CLI
6. **Exportación**: PDF, HTML, texto plano
7. **Navegación**: Sistema de navegación por Nikayas y suttas
8. **Configuración flexible**: Sistema de configuración robusto

## Notas de Reconstrucción

- La aplicación original estaba empaquetada con PyInstaller
- Se ha reconstruido la estructura de código fuente completa
- Se han preservado todos los datos originales
- Se ha creado un sistema de configuración mejorado
- Se ha añadido documentación completa
- Se ha implementado un sistema de pruebas

## Uso

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo GUI
python run.py

# Ejecutar en modo CLI
python run.py cli

# Ejecutar pruebas
python run.py test

# Verificar dependencias
python run.py check
```

## Licencia

Los textos Pali y traducciones tienen sus propias licencias.
El código de la aplicación está bajo licencia GPL-3.0.