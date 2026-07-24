
# Plan de Reconstrucción: Tipitaka PTS Browser

## 1. Resumen Ejecutivo

**Aplicación Actual:** Tipitaka PTS Browser v1.0.0  
**Tecnologías:** Python 3.14, PyQt6, QML, SQLite  
**Formato Actual:** AppImage (Linux)  
**Estado:** Aplicación funcional pero con oportunidades de mejora en arquitectura, mantenibilidad y características

**Objetivo:** Reconstruir la aplicación manteniendo todas las funcionalidades existentes mientras se mejora la arquitectura, se moderniza el código, se añaden nuevas características y se facilita el mantenimiento futuro.

## 2. Análisis del Estado Actual

### 2.1. Estructura del Proyecto Existente
```
squashfs-root/
├── AppRun                    # Script de lanzamiento
├── src/                      # Código fuente
│   ├── main/                 # Lógica principal
│   ├── qml/                  # Interfaz QML
│   ├── data/                 # Datos de la aplicación
│   └── docs/                 # Documentación
├── usr/_internal/           # Dependencias empaquetadas
└── *.desktop, *.png         # Archivos de integración
```

### 2.2. Tecnologías Identificadas
- **Backend:** Python 3.14, PyQt6, SQLite
- **Frontend:** QML (Qt Quick)
- **Dependencias:** rapidfuzz, python-Levenshtein, royalthai, charset-normalizer
- **Datos:** Base de datos SQLite con textos Pali, diccionarios en formato JSON

### 2.3. Puntos Críticos Identificados
1. **Monolito:** Todo el código en un solo módulo (`main/__init__.py`)
2. **Gestión de Dependencias:** Mecanismo básico de instalación
3. **Testing:** Estructura de pruebas básica o ausente
4. **Documentación:** Limitada al README
5. **Empaquetado:** Solo AppImage para Linux
6. **Arquitectura:** Acoplamiento alto entre componentes

## 3. Fases de Reconstrucción

### Fase 1: Análisis y Planificación (1-2 semanas)

#### 1.1. Auditoría Completa
- [ ] Análisis detallado de todos los módulos de código
- [ ] Mapeo de dependencias y versiones
- [ ] Evaluación de la base de datos SQLite (esquema, datos, relaciones)
- [ ] Análisis de archivos QML y su interacción con Python
- [ ] Identificación de código obsoleto o no utilizado

#### 1.2. Especificación de Requisitos
- [ ] Documentar todas las funcionalidades existentes
- [ ] Recopilar solicitudes de usuarios (si están disponibles)
- [ ] Definir mejoras prioritarias
- [ ] Establecer métricas de éxito

#### 1.3. Estándares de Calidad
- [ ] Definir guías de estilo de código (PEP 8, Black, Flake8)
- [ ] Establecer cobertura mínima de tests
- [ ] Definir proceso de revisión de código
- [ ] Establecer pipeline de CI/CD

### Fase 2: Arquitectura y Diseño (2-3 semanas)

#### 2.1. Nueva Arquitectura
```
tipitaka-browser/
├── src/
│   ├── core/                 # Lógica de negocio
│   │   ├── database/         # Acceso a datos
│   │   ├── search/           # Motor de búsqueda
│   │   ├── dictionary/       # Diccionario Pali
│   │   └── models/           # Modelos de datos
│   ├── ui/                   # Interfaz de usuario
│   │   ├── qml/             # Componentes QML
│   │   ├── viewmodels/      # ViewModels (MVVM)
│   │   └── themes/          # Temas y estilos
│   ├── services/            # Servicios externos
│   │   ├── export/          # Exportación de textos
│   │   ├── import/          # Importación de datos
│   │   └── analytics/       # Análisis de uso
│   ├── utils/               # Utilidades
│   └── main.py              # Punto de entrada
├── tests/                   # Tests automatizados
├── data/                    # Datos de la aplicación
├── docs/                    # Documentación
└── tools/                   # Herramientas de desarrollo
```

#### 2.2. Patrones de Diseño
- **MVVM (Model-View-ViewModel):** Separar lógica de presentación
- **Repository:** Abstracción del acceso a datos
- **Service Layer:** Lógica de negocio reutilizable
- **Dependency Injection:** Gestión de dependencias

#### 2.3. Tecnologías a Evaluar
- **ORM:** SQLAlchemy vs Django ORM vs Pony ORM
- **Testing:** pytest con pytest-qt
- **Logging:** Estructurado con JSON o formato extensible
- **Configuración:** TOML o YAML con validación
- **Internacionalización:** Sistema completo (i18n)

### Fase 3: Refactorización del Código (3-4 semanas)

#### 3.1. Separación de Responsabilidades
- [ ] Extraer lógica de base de datos a módulo dedicado
- [ ] Separar motor de búsqueda
- [ ] Aislar funcionalidad del diccionario
- [ ] Crear módulo de utilidades comunes

#### 3.2. Modernización de Python
- [ ] Actualizar sintaxis a Python 3.10+
- [ ] Implementar type hints completos
- [ ] Usar dataclasses y enums
- [ ] Aplicar principios SOLID

#### 3.3. Mejora de QML
- [ ] Componentizar elementos reutilizables
- [ ] Implementar temas intercambiables
- [ ] Mejorar responsividad
- [ ] Añadir soporte para accesibilidad

### Fase 4: Sistema de Datos (2-3 semanas)

#### 4.1. Base de Datos
- [ ] Diseñar esquema normalizado
- [ ] Implementar migraciones
- [ ] Crear sistema de backup/restore
- [ ] Optimizar consultas frecuentes

#### 4.2. Diccionario Pali
- [ ] Evaluar formato actual (¿JSON? ¿SQLite?)
- [ ] Diseñar esquema optimizado para búsquedas
- [ ] Implementar búsqueda fonética para Pali
- [ ] Añadir etimologías y ejemplos de uso

#### 4.3. Gestión de Textos
- [ ] Sistema de versionado de textos
- [ ] Soporte para múltiples ediciones simultáneas
- [ ] Marcadores y anotaciones persistentes
- [ ] Historial de navegación

### Fase 5: Interfaz de Usuario (3-4 semanas)

#### 5.1. Rediseño QML
- [ ] Diseñar sistema de componentes
- [ ] Implementar temas claro/oscuro
- [ ] Mejorar navegación y flujos de trabajo
- [ ] Añadir atajos de teclado configurables

#### 5.2. Características de UI
- [ ] Vista dividida para comparar ediciones
- [ ] Panel de diccionario integrado
- [ ] Sistema de pestañas para múltiples textos
- [ ] Modo lectura sin distracciones

#### 5.3. Experiencia de Usuario
- [ ] Tutorial interactivo
- [ ] Panel de bienvenida con textos destacados
- [ ] Búsqueda avanzada con filtros
- [ ] Exportación a múltiples formatos (PDF, HTML, EPUB)

### Fase 6: Testing y Calidad (2 semanas)

#### 6.1. Tests Unitarios
- [ ] Core: database, search, dictionary
- [ ] UI: ViewModels y lógica de presentación
- [ ] Utils: funciones auxiliares

#### 6.2. Tests de Integración
- [ ] Flujos completos de usuario
- [ ] Integración con base de datos
- [ ] Pruebas de rendimiento

#### 6.3. Tests de UI
- [ ] Pruebas de interfaz con pytest-qt
- [ ] Pruebas de regresión visual
- [ ] Pruebas de accesibilidad

#### 6.4. Calidad de Código
- [ ] CI con GitHub Actions/GitLab CI
- [ ] Análisis estático (mypy, pylint)
- [ ] Cobertura mínima del 80%
- [ ] Integración continua de dependencias

### Fase 7: Documentación (1-2 semanas)

#### 7.1. Documentación Técnica
- [ ] Documentación de arquitectura
- [ ] Guías de desarrollo
- [ ] API documentation (si aplica)
- [ ] Guía de contribución

#### 7.2. Documentación de Usuario
- [ ] Manual de usuario completo
- [ ] Tutoriales paso a paso
- [ ] FAQ y solución de problemas
- [ ] Guías específicas por funcionalidad

#### 7.3. Documentación de Datos
- [ ] Esquema de base de datos
- [ ] Formato de archivos de datos
- [ ] Proceso de actualización de datos
- [ ] Licencias y atribuciones

### Fase 8: Empaquetado y Distribución (2 semanas)

#### 8.1. Sistemas de Empaquetado
- **Linux:**
  - [ ] AppImage (actual)
  - [ ] Flatpak (nuevo)
  - [ ] Snap (opcional)
  - [ ] Paquetes nativos (.deb, .rpm)

- **Windows:**
  - [ ] Instalador NSIS
  - [ ] Portable ZIP
  - [ ] Microsoft Store (opcional)

- **macOS:**
  - [ ] DMG
  - [ ] App Bundle
  - [ ] Mac App Store (opcional)

#### 8.2. Gestión de Dependencias
- [ ] Usar Poetry o PDM para gestión de dependencias
- [ ] Definir entornos de desarrollo, testing y producción
- [ ] Gestionar dependencias del sistema (Qt, etc.)

#### 8.3. Automatización de Builds
- [ ] Scripts de build multiplataforma
- [ ] Integración con CI para releases automáticos
- [ ] Firmado de aplicaciones (seguridad)

### Fase 9: Características Adicionales (Opcional, 3-4 semanas)

#### 9.1. Funcionalidades Avanzadas
- [ ] Sincronización en la nube (opcional)
- [ ] Modo offline completo
- [ ] API REST para integraciones
- [ ] Plugins/extensions system

#### 9.2. Mejoras Académicas
- [ ] Análisis lingüístico de textos
- [ ] Comparación de traducciones
- [ ] Line numbering por edición
- [ ] Referencias cruzadas automáticas

#### 9.3. Colaboración
- [ ] Sistema de anotaciones compartidas
- [ ] Grupos de estudio
- [ ] Compartir marcadores
- [ ] Modo presentación/enseñanza

### Fase 10: Migración y Lanzamiento (1-2 semanas)

#### 10.1. Migración de Datos
- [ ] Scripts de migración desde versión anterior
- [ ] Validación de integridad de datos
- [ ] Sistema de rollback automático

#### 10.2. Lanzamiento Controlado
- [ ] Beta testing con usuarios existentes
- [ ] Recopilación de feedback
- [ ] Corrección de issues críticos
- [ ] Lanzamiento por fases

#### 10.3. Post-Lanzamiento
- [ ] Monitorización de errores (Sentry o similar)
- [ ] Análisis de uso (anónimo)
- [ ] Plan de mantenimiento
- [ ] Roadmap para futuras versiones

## 4. Cronograma Estimado

| Fase | Duración | Dependencias |
|------|----------|--------------|
| 1. Análisis | 2 semanas | - |
| 2. Arquitectura | 3 semanas | Fase 1 |
| 3. Refactorización | 4 semanas | Fase 2 |
| 4. Sistema de Datos | 3 semanas | Fase 3 |
| 5. Interfaz de Usuario | 4 semanas | Fase 3 |
| 6. Testing | 2 semanas | Fases 3-5 |
| 7. Documentación | 2 semanas | Fases 2-6 |
| 8. Empaquetado | 2 semanas | Fases 3-7 |
| 9. Características Extra | 4 semanas | Fases 3-8 (opcional) |
| 10. Lanzamiento | 2 semanas | Fases 1-9 |

**Total estimado:** 24-28 semanas (~6-7 meses)

## 5. Equipo y Recursos

### 5.1. Roles Necesarios
- **Desarrollador Backend Python:** 1-2 personas
- **Desarrollador Frontend QML:** 1 persona  
- **Diseñador UI/UX:** 0.5-1 persona
- **Especialista en Datos/Lingüística:** 0.5 persona
- **QA/Testing:** 0.5-1 persona

### 5.2. Recursos Técnicos
- **Hardware:** Máquinas para desarrollo multiplataforma
- **Software:** Licencias de desarrollo (si son necesarias)
- **Infraestructura:** CI/CD, repositorio de artefactos
- **Datos:** Espacio de almacenamiento para corpus de textos

## 6. Riesgos y Mitigación

### 6.1. Riesgos Técnicos
- **Compatibilidad con Qt6:** Ya está usando PyQt6, bajo riesgo
- **Migración de datos:** Scripts de migración exhaustivos
- **Rendimiento con grandes textos:** Optimización temprana, paginación

### 6.2. Riesgos de Proyecto
- **Alcance:** Definir MVP claramente, características opcionales para después
- **Tiempo:** Buffer del 20% en cronograma, hitos frecuentes
- **Calidad:** Testing desde el inicio, revisiones de código

### 6.3. Riesgos de Comunidad
- **Aceptación de cambios:** Comunicación clara, beta testing con usuarios actuales
- **Compatibilidad hacia atrás:** Mantener formatos de datos cuando sea posible
- **Soporte:** Documentación completa, sistema de issues organizado

## 7. Métricas de Éxito

### 7.1. Métricas Técnicas
- [ ] Cobertura de tests > 80%
- [ ] Tiempo de inicio < 3 segundos
- [ ] Uso de memoria < 500MB con textos cargados
- [ ] 0 bugs críticos en lanzamiento

### 7.2. Métricas de Usuario
- [ ] 90% de usuarios existentes migran satisfactoriamente
- [ ] Tiempo para completar tareas comunes reducido en 30%
- [ ] Puntuación de satisfacción > 4/5
- [ ] Tasa de retención > 80% después de 30 días

### 7.3. Métricas de Proyecto
- [ ] Todas las fases completadas dentro del +20% del tiempo estimado
- [ ] Presupuesto dentro del +15% del estimado
- [ ] Todas las funcionalidades del MVP implementadas

## 8. Próximos Pasos Inmediatos

1. **Semana 1:** Ejecutar análisis completo del código actual
2. **Semana 2:** Documentar todas las funcionalidades existentes  
3. **Semana 3:** Definir arquitectura detallada y stack tecnológico
4. **Semana 4:** Configurar entorno de desarrollo y CI básico
5. **Semana 5:** Comenzar refactorización del módulo principal

## 9. Consideraciones Éticas y Culturales

- **Sensibilidad religiosa:** Los textos tienen significado sagrado para muchos usuarios
- **Precisión:** Los textos deben presentarse sin errores de transcripción
- **Acceso abierto:** Mantener el espíritu de acceso libre al conocimiento
- **Atribución:** Reconocer adecuadamente las fuentes de los textos
- **Multilingüismo:** Soporte para interfaces en múltiples idiomas

## 10. Contacto y Responsables

**Líder Técnico:** [Por asignar]  
**Product Owner:** [Por asignar]  
**Coordinador de Comunidad:** [Por asignar]  
**Repositorio:** https://github.com/example/tipitaka-pts-browser

---

*Este plan es un documento vivo que debe actualizarse a medida que avanza el proyecto. Las estimaciones son aproximadas y deben refinarse después del análisis inicial.*

**Fecha de creación:** [Fecha actual]  
**Versión del plan:** 1.0  
**Próxima revisión:** Después de la Fase 1