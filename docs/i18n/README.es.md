# Local MOD Browser

[简体中文](../../README.md) · [English](../../README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)

Estas opciones de idioma traducen el README, no la interfaz de la aplicación ni todas las guías enlazadas.

**Estado de la versión (2026-10-20):** La próxima versión está en pruebas de aceptación independientes y todavía no se ha publicado. La versión pública actual sigue siendo `v2.5.2` (contrato de API `2.5.0`); los pasos de instalación, las funciones y los límites de seguridad que se describen a continuación corresponden a esa versión pública. Las funciones nuevas de la versión candidata o de las capturas del entorno local de los usuarios no deben considerarse disponibles en la versión pública.

<p align="center"><img src="../../docs/assets/logo-small.png" alt="Logotipo de Local MOD Browser" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Licencia](https://img.shields.io/badge/license-MIT-2ea44f)
![Contrato de API](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **Tu biblioteca de MODs debería ser algo más que una pila de carpetas cada vez mayor.**
>
> Pasa de «recuerdo que tenía ese MOD» a «puedo encontrarlo, comprobarlo y seguir trabajando en segundos» con un espacio de trabajo local, consultable y recuperable que permite colaborar con IA.
>
> **¿Has descargado un MOD y luego olvidado para qué lo querías o qué hace?** Los resúmenes, las descripciones de funciones y las etiquetas existentes ayudan a recuperar ese contexto. Puedes anotar manualmente planes futuros en las notas de las selecciones (loadouts); el navegador no deduce automáticamente los motivos originales por los que descargaste algo.

[Primeros pasos](#five-minute-quick-start) · [Descargar v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [IA y CLI](#ai-and-cli) · [Límites de seguridad](#privacy-and-security) · [Abrir una incidencia](https://github.com/son-gladyso/Local-Mod-Browser/issues)

<a id="turn-scattered-mods-into-a-useful-personal-catalog"></a>

## Convierte MODs dispersos en un catálogo personal útil

Local MOD Browser es un navegador de catálogos locales de MODs para Windows, un entorno de mantenimiento de metadatos y una plataforma de colaboración con IA. En lugar de descargar más contenido, convierte los metadatos de directorios que posees, mantienes o tienes autorización explícita para utilizar en un sistema local donde puedes buscar, filtrar, comparar, marcar favoritos, editar, traducir y mantener la información a lo largo del tiempo.

Es para ti si te resulta familiar alguno de estos problemas:

- Los MODs están repartidos entre unidades, juegos y carpetas de copias de seguridad, y encontrar un archivo lleva demasiado tiempo.
- Descargaste MODs, pero ya no recuerdas qué hace cada uno o para qué lo querías. Los resúmenes, las descripciones de funciones y las etiquetas que ya existen en el catálogo ayudan a relacionar de nuevo los archivos con su propósito.
- Es difícil comparar varias versiones o copias y no quieres sobrescribir un original por error.
- Los favoritos, el progreso de traducción, la información de los autores y las listas de archivos están separados y son difíciles de recuperar después de reinstalar.
- Quieres ayuda de IA para organizarte sin que el servicio suba tus rutas locales, inventario o base de datos a un tercero. Cualquier cliente de IA externo tiene su propio comportamiento de intercambio de datos.
- Las ediciones o traducciones por lotes interrumpidas no deberían dejar registros escritos a medias, envíos duplicados o estados sin explicación.

Ofrece un flujo de trabajo local claro:

```text
Your directory metadata → index and search → details / tags / file comparison → favorites / loadouts
                                                      ↓
                                     revisions / translation jobs / resumable batches
                                                      ↓
                                     browser, CLI and MCP over one local API
```

El código actual admite notas en las selecciones y campos de MOD editables como `function`, `details` y `tags`. Esto no significa que exista un campo de notas específico por MOD para «por qué lo descargué». Recuperar el contexto depende de la información que ya exista o que añadas tú; la intención original que falta no se reconstruye automáticamente.

<a id="see-the-product-before-installing"></a>

## Conoce el producto antes de instalarlo

Estas capturas proceden de los **ocho registros Demo completamente ficticios** del repositorio. No contienen MODs reales, recursos de juegos ni datos de sitios de terceros. Muestran la compilación pública real después de iniciarse, no una maqueta de diseño:

![Catálogo de demostración pública con filtros](../../docs/assets/demo-browse.png)

![Panel de detalles de la demostración pública](../../docs/assets/demo-detail.png)

![Búsqueda por palabras clave en la demostración pública](../../docs/assets/demo-search.png)

![Diseño para pantallas estrechas de la demostración pública](../../docs/assets/demo-mobile.png)

Consulta el recorrido reproducible completo en [`docs/demo-walkthrough.md`](../../docs/demo-walkthrough.md).

<a id="user-supplied-screenshots-from-actual-use"></a>

### Capturas de uso real aportadas por el usuario

Estas imágenes muestran la biblioteca local del propio usuario, con navegación, filtros y detalles de una colección más grande. No son datos incluidos con el programa ni la demostración reproducible de ocho registros anterior. Los recuentos de elementos y juegos y las miniaturas reflejan el entorno del usuario en el momento de la captura, no contenido incluido en la instalación.

![Uso real: biblioteca de MODs de varios juegos](../../docs/assets/real-use/library-overview.png)

*Navegación mediante tarjetas por la biblioteca multijuego del usuario.*

![Uso real: filtrar por propósito](../../docs/assets/real-use/purpose-filters.png)

*Filtrado por propósito manteniendo visibles las tarjetas y el contexto de los filtros.*

![Uso real: panel de detalles de un MOD](../../docs/assets/real-use/mod-detail-panel.png)

*Inspecciona una entrada junto a la vista actual del catálogo.*

Las otras tres imágenes: [archivos y variantes](../../docs/assets/real-use/files-and-variants.png), [Centro de IA y tareas](../../docs/assets/real-use/ai-task-center.png) y [Centro de descargas](../../docs/assets/real-use/download-center.png).

Consulta la [galería de uso real](../../docs/real-use-gallery.md#english) para ver las seis imágenes y las notas sobre sus estados. Las imágenes del Centro de IA y tareas y del Centro de descargas solo registran estados visibles en la interfaz local del usuario. No demuestran que una tarea o descarga haya terminado correctamente ni que esas mismas funciones estén incluidas en el código público o la versión publicada actuales.

Los nombres y las miniaturas de juegos y MODs pueden estar sujetos a derechos de terceros. No pasan a tener licencia MIT por aparecer en este repositorio. La galería no distribuye los MODs subyacentes, los recursos de los juegos ni la biblioteca original, y no concede permiso para reutilizar contenido de terceros.

<a id="decide-in-30-seconds-whether-it-fits"></a>

### Decide en 30 segundos si encaja contigo

| Si quieres… | La respuesta de Local MOD Browser |
| --- | --- |
| Buscar MODs de varios juegos y unidades en un solo lugar | Configurar varias fuentes locales con un índice unificado que se puede consultar |
| Recordar para qué sirve un MOD descargado | Revisar los resúmenes, las descripciones de funciones y las etiquetas existentes; anotar planes manualmente en las notas de las selecciones |
| Seleccionar un archivo exacto de un MOD | Comparación y selección explícita de archivos; no se añade un conjunto entero a una selección de forma predeterminada |
| Pausar y reanudar traducciones o trabajo de catalogación | Tareas segmentadas, concesiones temporales, recibos, cursores de eventos y recuperación |
| Usar IA sin que el servicio suba tu inventario privado | HTTP / CLI / MCP locales con un contrato compartido y escucha solo en la interfaz de bucle local de forma predeterminada |
| Recuperar trabajo después de una migración o actualización | Copias de seguridad emparejadas, diario de restauración, historial de versiones e identidades de recursos estables |

<a id="who-is-it-for"></a>

### ¿Para quién es?

- Jugadores con varios juegos, fuentes de MODs o años de archivos acumulados.
- Creadores y responsables de mantenimiento que buscan, comparan, traducen y organizan información de MODs de forma habitual.
- Personas que quieren asistencia de IA manteniendo el control de los datos en su propio ordenador.
- Cualquiera que prefiera una automatización reproducible, inspeccionable y recuperable a hacer clic y esperar que salga bien.

<a id="what-is-it-not"></a>

### ¿Qué no es?

No es un sitio de descarga de MODs, un instalador, una herramienta para eludir protecciones ni un servicio de alojamiento remoto. No decide si un MOD es seguro, compatible o tiene una licencia que permita tu uso. Organiza información que ya posees y tienes autorización para utilizar, haciendo cada cambio más visible y controlable. No descarga, redistribuye, instala ni ejecuta archivos de MODs.

![Antes y después: las carpetas dispersas se convierten en un catálogo local](../../docs/assets/before-after.svg)

<a id="what-you-get"></a>

## Qué ofrece

<a id="a-mod-browser-built-for-long-term-use"></a>

### Un navegador de MODs pensado para el uso a largo plazo

- Filtra rápidamente por juego, palabras clave, etiquetas combinadas, estado de traducción, autor, fecha e información de archivos.
- Mantén una navegación estable entre listas, detalles e historial sin volver a las carpetas para recuperar el contexto.
- Consulta imágenes, textos de autores, listas de archivos y enlaces de origen; compara copias concretas de archivos, no solo nombres de MODs.
- Marca entradas importantes como favoritas y guarda selecciones importables y exportables para continuar después de reinstalar o mover directorios.
- Utiliza pantallas anchas o estrechas; los filtros complejos se contraen y los resultados importantes siguen siendo destacados.

<a id="a-metadata-maintenance-workbench"></a>

### Un entorno de mantenimiento de metadatos

- Revisa los cambios con `preview` antes de `apply`, reduciendo ediciones accidentales y riesgos de operaciones por lotes.
- Gestiona traducciones por campo y segmento, con lotes, progreso, controles de calidad, detención y reanudación, y repetición idempotente.
- Los trabajos en segundo plano admiten concesiones temporales, renovación, transferencia y cursores de eventos para que otra IA o una página reabierta puedan continuar.
- Las escrituras importantes tienen claves de idempotencia estables y recibos autoritativos. Tras una interrupción de red, comprueba el resultado antes de decidir si reintentar.
- SQLite utiliza WAL y sincronización FULL, junto con un diario de restauración y copias de seguridad emparejadas para priorizar la integridad de los datos.

<a id="a-local-platform-ai-can-use-correctly"></a>

### Una plataforma local que la IA puede utilizar correctamente

- El navegador, la CLI y el MCP opcional comparten un contrato, por lo que la IA no necesita simular clics en el navegador.
- 70 operaciones estables cubren búsquedas, detalles, revisiones, favoritos, selecciones, traducciones y gestión de trabajos.
- Cinco flujos de trabajo deterministas guían a la IA para buscar, comprobar, modificar, volver a leer y comunicar resultados.
- La API local escucha en `127.0.0.1` de forma predeterminada. El servicio no llama a un modelo de propósito general ni envía datos automáticamente a la nube.
- Ante excepciones, los clientes solo reciben un identificador de solicitud. Los registros de diagnóstico locales se almacenan por separado para evitar filtrar rutas y trazas de pila a quienes llaman al servicio.

<a id="core-capabilities"></a>

## Capacidades principales

| Escenario | Capacidades | Problema que resuelve |
| --- | --- | --- |
| Encontrar información | Búsqueda de texto completo, paginación, etiquetas combinadas, filtros de autor/fecha/estado de traducción | «Lo recuerdo más o menos, pero no sé dónde está» |
| Inspeccionar detalles | Detalles, imágenes, enlaces de origen, listas de archivos, historial de revisiones | «¿Qué cambió en esta versión?» |
| Hacer una selección | Comparación exacta de archivos, favoritos, importación/exportación de selecciones | «Necesito esta copia, no todo el conjunto por error» |
| Editar metadatos | Vista previa/aplicación, control de versiones, listas de campos permitidos, restauración del historial | «La limpieza por lotes debe seguir siendo reversible» |
| Traducir | Tareas segmentadas, controles de calidad, pausa/reanudación, recibos idempotentes | «Un texto largo interrumpido no debería empezar de nuevo» |
| Colaborar con IA | HTTP, CLI, MCP, concesiones temporales, transferencia, cursores de eventos | «Que distintos asistentes puedan continuar de forma segura» |
| Proteger los datos | WAL/FULL, copias de seguridad emparejadas, diario de restauración, bloqueos del ciclo de vida | «Recuperarse después de una actualización o un fallo» |

<a id="privacy-and-security"></a>

## Privacidad y seguridad

Local MOD Browser tiene límites explícitos:

- **Solo se indexan los metadatos que proporcionas.** El repositorio no incluye bibliotecas de MODs originales de usuarios, archivos comprimidos, bases de datos, copias de seguridad, exportaciones ni tokens de ejecución. Las capturas seleccionadas aportadas por usuarios son documentación independiente, no datos de prueba ni descargas de contenido.
- **No descarga, redistribuye, instala ni ejecuta MODs.** Es un gestor de metadatos, no un descargador ni un instalador.
- **Escucha localmente de forma predeterminada.** El servicio se vincula a `127.0.0.1` y no está diseñado como servicio de red local ni público.
- **No se necesita ninguna cuenta de terceros.** El MCP opcional es únicamente un punto de entrada de protocolo local y no llama automáticamente a un modelo remoto. Un cliente de IA externo puede enviar los datos recuperados a su proveedor; revisa la configuración del cliente y el alcance de la autorización antes de conectarlo.
- **Eres responsable de contar con autorización para los datos de terceros.** Respeta los términos, la política de API y la licencia de contenido de cada sitio o servicio.

Lee la [política de seguridad](../../SECURITY.md), la [guía de contribución](../../CONTRIBUTING.md) y los [avisos de terceros](../../THIRD_PARTY_NOTICES.md). Las rutas predeterminadas del entorno de ejecución, base de datos, tokens, diagnósticos, exportaciones y artefactos de prueba están en `.gitignore` para reducir los commits accidentales. Esto no protege archivos ya bajo seguimiento, archivos añadidos a la fuerza ni datos en otras ubicaciones. Revisa siempre los cambios preparados antes de hacer un commit.

<a id="supported-platform"></a>

## Plataforma compatible

- Windows 10/11 x64.
- Entorno de ejecución fijado: CPython 3.13.15 x64 y SQLite 3.53.4.
- La primera configuración necesita acceso a la red para descargar y verificar el entorno fijado; un Python del sistema ejecuta el script de preparación.
- Las fuentes, los hashes y las licencias del entorno de ejecución están en [`runtime-lock.json`](../../runtime-lock.json).
- Linux y macOS no son compatibles actualmente. El servicio principal utiliza la biblioteca estándar de Python sin un framework de backend adicional.

<a id="five-minute-quick-start"></a>

## Inicio rápido en cinco minutos

<a id="1-get-the-code-and-prepare-local-configuration"></a>

### 1. Obtén el código y prepara la configuración local

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

<a id="2-install-the-pinned-runtime-and-launch"></a>

### 2. Instala el entorno de ejecución fijado e inicia la aplicación

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

También puedes hacer doble clic en `启动MOD浏览器.cmd` dentro del repositorio. El lanzador muestra una URL local; ábrela para explorar el catálogo de demostración ficticio y el flujo de trabajo de una biblioteca vacía. No necesitas una biblioteca real de MODs para el primer inicio.

Para descargar directamente el código público, utiliza `Local-Mod-Browser-2.5.2-source.zip` de la [versión v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2). El archivo `SHA256SUMS.txt` que lo acompaña permite verificar la integridad del archivo comprimido.

<a id="3-connect-your-own-catalog"></a>

### 3. Conecta tu propio catálogo

Edita `data\sources.json`, que Git ignora:

```json
[
  {
    "key": "mygame",
    "title": "My Game",
    "root": "D:\\Mods\\My Game",
    "outputDir": "D:\\Mods\\My Game\\catalog"
  }
]
```

Coloca un `catalog-data.json` en cada `outputDir`. Las rutas relativas se resuelven desde el directorio que contiene `sources.json`; también puedes apuntar `LOCAL_MOD_BROWSER_SOURCES` a otra configuración. Consulta [`config/sources.example.json`](../../config/sources.example.json) y [`examples/demo-game/catalog-data.json`](../../examples/demo-game/catalog-data.json).

<a id="4-check-the-service-and-local-api"></a>

### 4. Comprueba el servicio y la API local

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

Abre `/api/docs` para consultar el contrato legible por máquinas y `/api/health` para comprobar el estado del entorno de ejecución, la base de datos y el servicio.

<a id="what-does-a-first-successful-run-look-like"></a>

## ¿Cómo es una primera ejecución satisfactoria?

Empieza con los registros ficticios incluidos, sin importar tu biblioteca: inicia el servicio → abre la URL local → busca un ejemplo → abre sus detalles → vuelve a la lista. Este pequeño recorrido comprueba la navegación y la búsqueda antes de organizar una unidad entera.

Prepara Windows 10/11 x64, un Python del sistema capaz de ejecutar el script de preparación y acceso a la red para la primera descarga del entorno de ejecución. El uso habitual no requiere IA ni MCP; las dependencias de pruebas para desarrolladores están en la [guía de contribución](../../CONTRIBUTING.md).

**Una ejecución satisfactoria significa:** el catálogo ficticio es visible, la búsqueda y los detalles se pueden utilizar, y puedes inspeccionar los resultados de `ai.py doctor`. Cargar una página por sí solo no verifica la configuración de tus propias fuentes, el comportamiento de recuperación ni todas las operaciones de la plataforma.

<a id="common-questions"></a>

## Preguntas frecuentes

**¿Por qué no aparece la gran biblioteca de las capturas después de descargarlo?** Son capturas de uso real aportadas por el usuario, no datos distribuidos. El repositorio incluye ocho registros Demo ficticios; configura tus propias fuentes por separado.

**¿Escanea y comprende automáticamente todos los MODs de mis unidades?** No. La entrada es la configuración de fuentes y el `catalog-data.json` de cada `outputDir`, no una interpretación universal de carpetas arbitrarias. Comprueba las rutas y los metadatos con el [ejemplo de configuración](../../config/sources.example.json).

**¿Puede recordar por qué descargué un MOD?** Los resúmenes, las descripciones de funciones y las etiquetas existentes ayudan a revisar su propósito; puedes editar metadatos y escribir planes manualmente en las notas de las selecciones. No puede deducir una intención original olvidada a partir de los archivos, y este README no promete un campo separado por MOD para el motivo de descarga.

**¿Por qué está vacía la lista?** Comprueba que `data\sources.json` sea válido, desde qué directorio de configuración se resuelven las rutas relativas y que cada `outputDir` de destino contenga `catalog-data.json`. Después sigue la [guía de usuario](../../docs/user-guide.md). No publiques una base de datos privada en una incidencia.

**¿Tengo que conectar una IA para navegar?** No. El navegador y la CLI funcionan directamente. El MCP opcional es una interfaz local, no un interruptor automático para modelos en la nube; el cliente externo que elijas tiene sus propios límites de datos.

**¿El Centro de descargas de uso real demuestra que la versión pública descarga MODs?** No. Registra la interfaz local de un usuario con una lista de descargas vacía y Nexus desconectado. La versión pública sigue descrita como una aplicación que no descarga, instala ni ejecuta MODs.

**¿Puedo acceder desde otros dispositivos o desde internet?** Escucha en `127.0.0.1` de forma predeterminada; no lo despliegues como servicio de red local ni público. Actualmente tampoco se admiten plataformas distintas de Windows.

<a id="find-the-code-for-your-change"></a>

### Encuentra el código para tu cambio

- Navegación e interacción: empieza en `static/`; verifica listas, detalles, estados vacíos y de error, y el comportamiento en pantallas estrechas.
- Fuentes y búsqueda: empieza en `catalog.py` y los ejemplos de configuración; prueba entradas válidas e inválidas con catálogos sintéticos.
- Operaciones de la plataforma: lee `contracts.py`, `platform_api.py` y las pruebas relacionadas de forma conjunta para mantener alineados HTTP, CLI y MCP.
- Persistencia o trabajos en segundo plano: lee primero la [guía de arquitectura](../../docs/architecture.md); cubre interrupción, reintento y recuperación sin sacrificar durabilidad por velocidad.

Los comandos y requisitos de las PR están en la [guía de contribución](../../CONTRIBUTING.md); las tareas iniciales aparecen en [Hoja de ruta y contribuciones](#roadmap-and-contributing).

<a id="ai-and-cli"></a>

## IA y CLI

La CLI es un punto de entrada estable para scripts e IA sin operaciones de ratón simuladas:

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

Flujo de trabajo seguro recomendado:

1. Lee las capacidades y la documentación de interfaces para comprobar las operaciones admitidas por esta versión.
2. Busca y lee los recursos antes de enviar `preview`; no adivines la identidad de un archivo por su posición en una matriz.
3. Comprueba los identificadores de recursos, las versiones y las diferencias en la vista previa y, después, aplica los cambios con una `idempotencyKey` estable.
4. Espera los estados finales reales de los trabajos en segundo plano, verificando los resultados mediante una nueva lectura de los datos de negocio y los recibos autoritativos. `queued` no significa terminado.
5. Tras una interrupción, comprueba los recibos y los cursores de eventos antes de continuar, transferir el trabajo o reintentar.

Consulta [`docs/user-guide.md`](../../docs/user-guide.md), [`docs/ai-platform-guide.md`](../../docs/ai-platform-guide.md) y [`docs/architecture.md`](../../docs/architecture.md).

<a id="verification-and-quality-gates"></a>

## Verificación y controles de calidad

Iniciar correctamente no basta para considerar completo el proyecto. La versión pública mantiene scripts reproducibles de aceptación con datos sintéticos:

```powershell
# Python regression
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v

# Startup, collaboration and contract
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture

# Frontend syntax
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

La aceptación mediante navegador requiere además `npm install` y los navegadores de Playwright. La CI de Windows instala automáticamente el entorno de ejecución fijado y ejecuta regresiones de Python, auditoría de contrato y comprobaciones de JavaScript. Consulta la [guía de contribución](../../CONTRIBUTING.md).

<a id="project-map"></a>

## Mapa del proyecto

```text
Local-Mod-Browser/
├─ server.py                    local HTTP service and unified error boundary
├─ platform_api.py              70 platform operations and business rules
├─ contracts.py                 shared HTTP/CLI/MCP contract and schemas
├─ catalog.py                   source configuration, indexing, and query projections
├─ ai.py                        CLI for scripts and AI
├─ mcp_adapter.py               optional local MCP entry point
├─ static/                      browser interface
├─ tests/                       regression, contract, startup, collaboration, performance and soak checks
├─ tools/bootstrap_runtime.py   pinned runtime installation and verification
└─ docs/                        user, AI platform, and architecture guides
```

<a id="roadmap-and-contributing"></a>

## Hoja de ruta y contribuciones

La versión pública actual es `v2.5.2` y el contrato de API es `2.5.0`. Las prioridades son:

- Agilizar el trabajo con metadatos locales y facilitar su revisión, sin ampliar la recogida de datos.
- Mantener coherente el comportamiento de API, CLI y MCP, con fallos explicables y recuperables.
- Proteger los datos mediante pruebas sintéticas y aceptación reproducible; nunca utilizar inventarios privados como datos públicos de prueba.
- Ampliar los adaptadores de fuentes únicamente con una autorización de contenido clara y respetando los términos de terceros.

Consulta [`ROADMAP.md`](../../ROADMAP.md) para conocer la dirección actual. La documentación, las pruebas reproducibles, la accesibilidad y las pequeñas mejoras en la configuración de fuentes son buenas primeras contribuciones.

Se agradecen las incidencias, las mejoras de documentación y los Pull Requests. Lee primero [CONTRIBUTING.md](../../CONTRIBUTING.md). No envíes rutas personales, inventarios, bases de datos, tokens visibles en capturas ni contenido de terceros no autorizado. Los cambios externos se revisan; antes de fusionar en `main` se requieren CI, aprobación del responsable del código, conversaciones resueltas, controles de privacidad y pruebas específicas.

Si resuelve un problema real, dale una Star, compártelo con alguien cuyas carpetas de MODs se estén descontrolando o envía una incidencia concreta. Los comentarios claros y reproducibles ayudan más que un «qué bonito» o una petición vaga; las mejoras aceptadas siguen siendo revisables en el historial público.

<a id="start-with-one-small-improvement"></a>

### Empieza con una mejora pequeña

Para una primera contribución, elige una tarea existente:

- [Preguntas frecuentes del primer inicio (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3): añade solución de problemas de instalación del entorno de ejecución, configuración de fuentes y archivos de catálogo ausentes, con pasos de verificación.
- [Documentación y validación de la configuración de fuentes (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2): explica los campos y las rutas relativas, y cubre errores con configuraciones sintéticas.
- [Estados vacíos y de error accesibles (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1): ayuda a quienes utilizan teclado y lector de pantalla a entender la siguiente acción.

Comprueba la discusión y el estado actuales de la incidencia antes de definir tu alcance. Las correcciones pequeñas de documentación pueden ir directamente a una PR; discute primero las funciones más amplias, los cambios del modelo de datos y los adaptadores de fuentes, siguiendo la guía de contribución. No necesitas aportar tu propia biblioteca de MODs para contribuir.

<a id="license"></a>

## Licencia

El código del proyecto utiliza la [licencia MIT](../../LICENSE). Los avisos de terceros sobre el entorno de ejecución y las dependencias opcionales están en [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md). MIT no concede derechos sobre MODs, recursos de juegos, datos de sitios, textos de autores ni ningún otro contenido de terceros.
