# Secuencia de Prompts para Reconstrucción de Tipitaka PTS Browser

Esta secuencia contiene prompts independientes para guiar a una IA en la reconstrucción paso a paso de la aplicación Tipitaka PTS Browser. Cada prompt es autónomo y puede ejecutarse individualmente.

---

## Fase 1: Análisis y Auditoría

### Prompt 1: Análisis completo del código base existente
**Contexto:** La aplicación Tipitaka PTS Browser v1.0.0 está escrita en Python 3.14 con PyQt6 y QML. Todo el código principal está en `squashfs-root/src/main/__init__.py` (monolítico de ~500 líneas). Necesitamos un análisis exhaustivo para entender todas las funcionalidades, dependencias y puntos de mejora.

**Tareas:**
1. Analizar el archivo `squashfs-root/src/main/__init__.py` línea por línea y documentar:
   - Todas las clases y métodos públicos/privados
   - Flujos de control principales (GUI vs CLI)
   - Interacción con la base de datos SQLite
   - Manejo de señales PyQt6 y QML
   - Gestión de datos (JSON, SQLite)

2. Analizar los archivos QML en `squashfs-root/src/qml/`:
   - `MainWindow.qml` (estructura principal)
   - `SettingsWindow.qml`
   - `VariantPopup.qml`
   - Identificar propiedades bindeadas a Python

3. Examinar la estructura de datos en `squashfs-root/src/data/`:
   - Esquema de `tipitaka.sqlite` (tablas, índices, relaciones)
   - Archivos JSON (`edition_conversions.json`, `matn_relations.json`, `philological_notes.json`)
   - Archivos CSV de referencias

4. Revisar `squashfs-root/src/requirements.txt` y `setup.py`:
   - Dependencias exactas y versiones
   - Scripts de entrada (entry_points)

5. Probar la aplicación funcionalmente:
   - Ejecutar en modo CLI (`python -m main`)
   - Verificar conexión a base de datos
   - Probar búsqueda básica

**Entregables:**
- Documento `ANALISIS_CODIGO.md` con:
  - Diagrama de clases actual
  - Mapa de dependencias
  - Lista de todas las funcionalidades
  - Problemas identificados (código espagueti, acoplamiento, etc.)
  - Archivos de datos y sus formatos

---

### Prompt 2: Análisis de la base de datos SQLite
**Contexto:** La aplicación usa `tipitaka.sqlite` como almacenamiento principal. Necesitamos entender completamente su esquema, relaciones y calidad de datos para diseñar una migración segura.

**Tareas:**
1. Conectarse a `squashfs-root/src/data/tipitaka.sqlite` y extraer:
   - Lista completa de tablas y sus schemas
   - Índices, triggers y vistas
   - Relaciones entre tablas (claves foráneas)

2. Analizar el contenido:
   - Tamaño aproximado de cada tabla
   - Muestra de datos de cada tabla (primeras 5 filas)
   - Identificar posibles inconsistencias de datos

3. Examinar los archivos JSON relacionados:
   - `edition_conversions.json` - conversiones entre ediciones
   - `matn_relations.json` - relaciones entre textos
   - `philological_notes.json` - notas filológicas

4. Probar consultas comunes:
   - Búsqueda de texto por ID
   - Búsqueda por contenido (LIKE)
   - Consultas de ediciones disponibles

**Entregables:**
- Archivo `ESQUEMA_BASE_DATOS.md` con:
  - Diagrama ER completo
  - Script SQL de creación de tablas
  - Estadísticas de datos (conteos, tamaños)
  - Recomendaciones para normalización/optimización

---

## Fase 2: Diseño de Arquitectura

### Prompt 3: Diseñar nueva arquitectura modular
**Contexto:** Basado en el análisis, necesitamos diseñar una arquitectura moderna que separe responsabilidades y facilite mantenimiento.

**Tareas:**
1. Diseñar estructura de directorios:
   ```
   tipitaka-browser/
   ├── src/
   │   ├── core/          # Lógica de negocio
   │   ├── ui/           # Interfaz de usuario  
   │   ├── data/         # Acceso a datos
   │   ├── services/     # Servicios externos
   │   └── utils/        # Utilidades
   ├── tests/           # Tests automatizados
   ├── docs/            # Documentación
   └── tools/           # Herramientas de desarrollo
   ```

2. Definir módulos específicos:
   - `core/`: TextManager, SearchEngine, DictionaryService
   - `data/`: DatabaseRepository, models.py (SQLAlchemy)
   - `ui/`: ViewModels (MVVM), componentes QML reutilizables
   - `services/`: ExportService, ImportService, Analytics

3. Diseñar interfaces (ABCs) para:
   - Repositorio de datos
   - Motor de búsqueda
   - Servicio de diccionario

4. Plan de migración:
   - Script para migrar datos de SQLite actual a nuevo esquema
   - Sistema de versionado de esquema

**Entregables:**
- Archivo `ARQUITECTURA.md` con:
  - Diagrama de componentes
  - Especificación de interfaces
  - Plan de migración paso a paso
  - Dependencias entre módulos

---

### Prompt 4: Diseñar sistema de configuración y logging
**Contexto:** La aplicación actual no tiene sistema de logging estructurado y usa configuraciones ad-hoc.

**Tareas:**
1. Diseñar sistema de configuración:
   - Formato TOML para `config.toml`
   - Secciones: database, ui, search, dictionary
   - Validación con pydantic

2. Diseñar sistema de logging:
   - Logs estructurados (JSON en producción, texto en desarrollo)
   - Niveles: DEBUG, INFO, WARNING, ERROR
   - Rotación de archivos de log

3. Diseñar gestión de settings de usuario:
   - Almacenamiento en `~/.config/tipitaka-browser/`
   - Migración desde formato JSON anterior

**Entregables:**
- Archivo `CONFIGURACION_LOGGING.md` con:
  - Esquema de configuración (ejemplo completo)
  - Especificación de formato de logs
  - Código de ejemplo para inicialización

---

## Fase 3: Refactorización

### Prompt 5: Extraer módulo de base de datos
**Contexto:** El código actual mezcla lógica de base de datos con lógica de negocio y UI.

**Tareas:**
1. Crear `src/data/database.py` con:
   - Clase `DatabaseConnection` (context manager)
   - Métodos para conexión, migración, backup

2. Crear `src/data/models.py` con:
   - Modelos SQLAlchemy para todas las tablas
   - Relaciones bien definidas
   - Type hints completos

3. Crear `src/data/repository.py` con:
   - Clase `TextRepository` con métodos CRUD
   - Clase `DictionaryRepository`
   - Patrón Repository para abstraer SQL

4. Migrar gradualmente:
   - Primero crear nuevos modelos junto a código viejo
   - Luego actualizar llamadas una por una
   - Mantener compatibilidad durante transición

**Entregables:**
- Módulos `database.py`, `models.py`, `repository.py` funcionando
- Tests básicos para cada repositorio
- Script de migración de datos viejo → nuevo

---

### Prompt 6: Extraer motor de búsqueda
**Contexto:** La búsqueda actual usa SQL LIKE, necesitamos motor más sofisticado.

**Tareas:**
1. Crear `src/core/search/` con:
   - `search_engine.py`: interfaz abstracta
   - `sqlite_search.py`: implementación con FTS5
   - `text_processor.py`: normalización de texto Pali

2. Implementar búsqueda de texto completo con SQLite FTS5:
   - Crear tablas virtuales FTS5
   - Indexar todos los textos
   - Soporte para búsqueda por palabras, frases, operadores

3. Añadir búsqueda fonética para Pali:
   - Algoritmo para normalizar pronunciación
   - Búsqueda aproximada (Levenshtein)

4. Crear API consistente:
   - `search(query, limit=50, offset=0)`
   - `search_advanced(filters, sort_by)`

**Entregables:**
- Motor de búsqueda con FTS5 funcionando
- Tests de búsqueda con datos de ejemplo
- Benchmark comparativo vs búsqueda LIKE original

---

### Prompt 7: Refactorizar interfaz QML a componentes
**Contexto:** Los archivos QML actuales son monolíticos y difíciles de mantener.

**Tareas:**
1. Analizar `MainWindow.qml` y extraer componentes:
   - `TextReader.qml` - visualización de textos
   - `SearchPanel.qml` - panel de búsqueda
   - `DictionaryPanel.qml` - diccionario integrado
   - `NavigationBar.qml` - barra de navegación

2. Crear sistema de temas:
   - `Theme.qml` - definición de colores, fuentes
   - `LightTheme.qml`, `DarkTheme.qml`
   - Soporte para cambio dinámico de tema

3. Implementar ViewModels en Python:
   - `TextViewModel` - estado y comandos para textos
   - `SearchViewModel` - estado de búsqueda
   - Comunicación via signals/slots

4. Mejorar accesibilidad:
   - Roles ARIA para componentes
   - Soporte para lectores de pantalla
   - Atajos de teclado configurables

**Entregables:**
- Componentes QML reutilizables en `src/ui/qml/components/`
- ViewModels correspondientes en `src/ui/viewmodels/`
- Sistema de temas funcional

---

## Fase 4: Sistema de Datos

### Prompt 8: Migrar y optimizar base de datos
**Contexto:** Necesitamos migrar del esquema actual a uno normalizado y optimizado.

**Tareas:**
1. Diseñar nuevo esquema SQLAlchemy:
   - Tablas: `texts`, `editions`, `chapters`, `verses`
   - Tablas: `dictionary_entries`, `translations`, `metadata`
   - Índices optimizados para búsquedas comunes

2. Crear sistema de migraciones:
   - Script `migrate_v1_to_v2.py`
   - Validación de integridad post-migración
   - Opción de rollback automático

3. Optimizar para rendimiento:
   - Índices FTS5 para búsqueda de texto completo
   - Caching de consultas frecuentes
   - Paginación eficiente para textos largos

4. Crear sistema de backup/restore:
   - Comando CLI `tipitaka-cli backup`
   - Backup incremental
   - Restauración verificada

**Entregables:**
- Nuevos modelos SQLAlchemy completos
- Script de migración validado
- Sistema de backup funcionando

---

### Prompt 9: Implementar diccionario Pali mejorado
**Contexto:** El diccionario actual es básico, necesitamos sistema completo.

**Tareas:**
1. Analizar datos del diccionario en `critical-pali-dictionary/`
2. Diseñar esquema para:
   - Entradas principales con definiciones múltiples
   - Etimologías y referencias cruzadas
   - Ejemplos de uso en textos canónicos
   - Conjugaciones/declinaciones

3. Implementar búsqueda avanzada:
   - Búsqueda por raíz (root)
   - Búsqueda por significado (inglés → pali)
   - Búsqueda fonética aproximada

4. Crear API:
   - `lookup(word)` - entrada completa
   - `search_meanings(query)` - búsqueda por significado
   - `get_examples(word, limit=5)` - ejemplos en contexto

**Entregables:**
- Módulo `DictionaryService` completo
- Interfaz QML para diccionario integrado
- Tests con datos reales del diccionario crítico

---

## Fase 5: Interfaz de Usuario

### Prompt 10: Implementar vista de lectura mejorada
**Contexto:** La vista actual de textos es básica, necesitamos características avanzadas.

**Tareas:**
1. Crear `TextReader.qml` con:
   - Soporte para múltiples ediciones lado a lado
   - Navegación por capítulos/versos
   - Marcadores y anotaciones persistentes
   - Búsqueda dentro del texto actual

2. Implementar sistema de anotaciones:
   - Notas personales por verso
   - Marcadores con categorías
   - Exportación de anotaciones

3. Añadir herramientas de estudio:
   - Contador de palabras/frecuencia
   - Comparación entre ediciones
   - Visualización de referencias cruzadas

4. Soporte para exportación:
   - Exportar a PDF con formato
   - Exportar a HTML/EPUB
   - Exportar anotaciones

**Entregables:**
- Componente `TextReader.qml` completo
- Sistema de anotaciones persistente
- Funciones de exportación a múltiples formatos

---

### Prompt 11: Implementar panel de búsqueda avanzada
**Contexto:** La búsqueda actual es básica, necesitamos interfaz con filtros.

**Tareas:**
1. Diseñar `AdvancedSearchPanel.qml`:
   - Campos: texto, edición, sección, rango de fechas
   - Operadores lógicos (AND, OR, NOT)
   - Guardar búsquedas frecuentes

2. Implementar resultados en tiempo real:
   - Vista previa de resultados al escribir
   - Highlight de términos encontrados
   - Ordenamiento por relevancia/fecha

3. Historial de búsquedas:
   - Almacenamiento local
   - Búsquedas frecuentes
   - Limpieza automática

4. Integrar con diccionario:
   - Búsqueda de palabras desde resultados
   - Análisis de frecuencia en resultados

**Entregables:**
- Panel de búsqueda avanzada funcional
- Historial de búsquedas persistente
- Integración completa con motor de búsqueda

---

## Fase 6: Testing y Calidad

### Prompt 12: Configurar entorno de testing completo
**Contexto:** Necesitamos tests automatizados para garantizar calidad.

**Tareas:**
1. Configurar pytest con plugins:
   - `pytest-qt` para tests de UI
   - `pytest-cov` para cobertura
   - `pytest-mock` para mocking

2. Crear fixtures comunes:
   - Base de datos en memoria para tests
   - Aplicación Qt mockeada
   - Datos de prueba (textos de ejemplo)

3. Escribir tests unitarios para:
   - Todos los modelos de datos
   - Repositorios (DatabaseRepository)
   - Servicios (SearchEngine, DictionaryService)

4. Escribir tests de integración:
   - Flujo completo de búsqueda
   - Migración de datos
   - Exportación/importación

**Entregables:**
- Configuración completa de pytest en `pyproject.toml`
- Fixtures en `tests/conftest.py`
- Tests unitarios para módulos críticos
- Cobertura > 80% en módulos core

---

### Prompt 13: Implementar tests de UI con pytest-qt
**Contexto:** La UI QML necesita tests automatizados.

**Tareas:**
1. Configurar `pytest-qt` para pruebas QML:
   - Inicialización de QApplication
   - Carga de componentes QML
   - Timeouts apropiados

2. Escribir tests para componentes QML:
   - `TextReader` - carga de textos, navegación
   - `SearchPanel` - búsqueda, filtros
   - `DictionaryPanel` - lookup, ejemplos

3. Tests de interacción:
   - Clicks, texto ingresado
   - Cambio de propiedades
   - Señales emitidas

4. Tests de integración UI-backend:
   - Búsqueda desde UI → resultados
   - Clic en palabra → lookup diccionario
   - Cambio de edición → actualización texto

**Entregables:**
- Tests para todos los componentes QML principales
- Tests de integración UI-backend
- CI configurado para ejecutar tests de UI

---

## Fase 7: Documentación

### Prompt 14: Crear documentación técnica completa
**Contexto:** Falta documentación para desarrolladores.

**Tareas:**
1. Documentar arquitectura:
   - Diagramas Mermaid en README
   - Guía de instalación para desarrollo
   - Configuración de entorno

2. Documentar API interna:
   - Docstrings en todos los módulos públicos
   - Ejemplos de uso para cada servicio
   - Guía de extensión (plugins, temas)

3. Documentar datos:
   - Esquema de base de datos
   - Formato de archivos de importación
   - Licencias y atribuciones de datos

4. Crear guías:
   - Contribución (CONTRIBUTING.md)
   - Código de conducta
   - Roadmap público

**Entregables:**
- `docs/developer/` completo con:
  - `architecture.md`
  - `api-reference.md`
  - `data-schema.md`
  - `contributing.md`

---

### Prompt 15: Crear documentación de usuario
**Contexto:** Los usuarios necesitan manuales completos.

**Tareas:**
1. Crear guías paso a paso:
   - Instalación en cada plataforma
   - Primeros pasos (tutorial interactivo)
   - Características principales

2. Documentar todas las funcionalidades:
   - Búsqueda avanzada (con ejemplos)
   - Diccionario integrado
   - Sistema de anotaciones
   - Exportación de datos

3. Crear FAQ:
   - Problemas comunes y soluciones
   - Preguntas técnicas
   - Recursos adicionales (estudio Pali)

4. Sistema de ayuda integrado:
   - Tooltips en toda la UI
   - Página de ayuda en la aplicación
   - Tutorial contextual

**Entregables:**
- `docs/user/` completo con:
  - `getting-started.md`
  - `features.md`
  - `faq.md`
  - `tutorials/` (varios tutoriales)

---

## Fase 8: Empaquetado y Distribución

### Prompt 16: Configurar empaquetado multiplataforma
**Contexto:** Actualmente solo AppImage para Linux.

**Tareas:**
1. Configurar PyInstaller para:
   - Linux: AppImage, Flatpak, .deb, .rpm
   - Windows: .exe, MSI installer
   - macOS: .dmg, .app bundle

2. Crear scripts de build:
   - `build_linux.sh` - todas las variantes Linux
   - `build_windows.ps1` - instalador Windows
   - `build_macos.sh` - bundle macOS

3. Configurar GitHub Actions:
   - Build automático en tags
   - Publicación en Releases
   - Notificaciones a usuarios

4. Firmado de aplicaciones:
   - Certificados para Windows/macOS
   - GPG para Linux packages
   - Verificación de integridad

**Entregables:**
- Scripts de build para las 3 plataformas
- Configuración de CI/CD en `.github/workflows/`
- Instrucciones de empaquetado

---

### Prompt 17: Implementar sistema de actualizaciones
**Contexto:** Los usuarios necesitan actualizaciones sencillas.

**Tareas:**
1. Sistema de actualización automática:
   - Check periódico de nuevas versiones
   - Descarga silenciosa en segundo plano
   - Instalación con consentimiento usuario

2. Para cada plataforma:
   - Linux: repositorios APT/RPM, FlatHub
   - Windows: Windows Installer con actualizaciones
   - macOS: Sparkle framework

3. Canales de actualización:
   - Stable (releases oficiales)
   - Beta (pre-releases)
   - Nightly (desarrollo)

4. Notificaciones:
   - Changelog visual en actualizaciones
   - Notificación de actualizaciones críticas
   - Recordatorios amigables

**Entregables:**
- Módulo `UpdateService` para manejo de actualizaciones
- Configuración para cada plataforma
- UI para gestión de actualizaciones

---

## Fase 9: Lanzamiento

### Prompt 18: Plan de migración y lanzamiento
**Contexto:** Necesitamos migrar usuarios existentes sin perder datos.

**Tareas:**
1. Crear script de migración:
   - Detección automática de instalación anterior
   - Migración de: configuraciones, marcadores, anotaciones
   - Validación post-migración

2. Lanzamiento por fases:
   - Fase 1: Beta testing con usuarios existentes
   - Fase 2: Release candidate amplio
   - Fase 3: Lanzamiento general

3. Comunicación:
   - Changelog detallado
   - Guía de migración paso a paso
   - Canales de soporte post-lanzamiento

4. Rollback plan:
   - Instrucciones para volver a versión anterior
   - Backup automático antes de migración
   - Verificación de compatibilidad

**Entregables:**
- Script `migrate_from_v1.py` completo
- Plan de lanzamiento detallado
- Materiales de comunicación (changelog, guías)

---

### Prompt 19: Configurar monitorización y feedback
**Contexto:** Post-lanzamiento necesitamos métricas y feedback.

**Tareas:**
1. Sistema de reporte de errores:
   - Captura automática de crashes
   - Reporte anónimo de errores
   - Stack traces con contexto

2. Métricas de uso anónimas:
   - Funcionalidades más usadas
   - Tiempos de carga
   - Errores más frecuentes

3. Sistema de feedback integrado:
   - Botón "Enviar feedback" en aplicación
   - Captura de contexto automático
   - Integración con GitHub Issues

4. Panel de métricas:
   - Dashboard básico para desarrolladores
   - Alertas de errores críticos
   - Tendencias de uso

**Entregables:**
- Módulo `AnalyticsService` (opt-in)
- Configuración de Sentry/opcional
- Formulario de feedback integrado

---

## Uso de esta secuencia

1. **Ejecutar en orden:** Los prompts están diseñados para ejecutarse secuencialmente
2. **Validar entregables:** Cada prompt produce entregables específicos que deben verificarse
3. **Adaptar según necesidades:** Ajustar detalles según hallazgos durante la reconstrucción
4. **Iterar:** Algunas fases pueden requerir múltiples iteraciones

**Nota:** Cada prompt asume que la IA tiene acceso completo al código base y puede ejecutar herramientas de desarrollo (terminal, editores, etc.).

---
*Última actualización: [fecha]*
*Versión: 1.0*