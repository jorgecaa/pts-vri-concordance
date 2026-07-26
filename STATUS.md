# PTS Reference Concordance — Status Report
## KN — CATASTRO (2026-07-25): qué se puede validar y qué no

Antes de tocar nada de KN, la pregunta es de qué hay texto. La regla del proyecto es que las
**únicas fuentes válidas son PTS (la BD) y el CST (los XML de VRI)**, así que una fila sin texto en
la BD no es validable por este camino, por mucho que exista en otras ediciones.

**2.360 filas → 2.066 con texto en la BD (87,5 %) · 294 sin él (12,5 %).**

### Lo que SÍ tiene texto en la BD

| obra | filas | libro BD | pp. BD | pp. Excel | fichero VRI |
|---|--:|--:|---|---|---|
| Khuddakapāṭha | 9 | 22 | 1-9 | 1-8 | `s0501m` |
| Dhammapada | 26 | 23 | 1-120 | 1-108 | `s0502m` |
| Udāna | 80 | 24 | 1-94 | 1-93 | `s0503m` |
| Itivuttaka | 112 | 25 | 1-124 | 1-121 | `s0504m` |
| Suttanipāta | 73 | 26 | 1-223 | 1-219 | `s0505m` |
| Vimānavatthu | 85 | 27 | 1-135 | 1-134 | `s0506m` |
| Petavatthu | 51 | 28 | 1-95 | 1-94 | `s0507m` |
| Theragāthā | 264 | 29 | 1-174 | 1-109 | `s0508m` |
| Therīgāthā | 73 | 29 | *(mismo libro)* | 123-167 | `s0509m` |
| Jātaka | 547 | 30-35 | 6 vols. | 1-537 | `s0513m` `s0514m` |
| Thera-apadāna | 563 | 40 | 1-615 | 3-511 | `s0510m1` |
| Therī-apadāna | 40 | 40 | *(mismo libro)* | 513-614 | `s0510m2` |
| Buddhavaṃsa | 29 | 41 | 1-102 | 1-68 | `s0511m` |
| Cariyāpiṭaka | 34 | 42 | 1-37 | 73-101 | `s0512m` |
| Niddesa | 37+2 | 36, 37 | 510 + 73 | 1-445 | `s0515m` `s0516m` |
| Paṭisambhidāmagga | 22+9 | 38, 39 | 196 + 246 | 1-185 · 205-243 | `s0517m` |

### Lo que NO se puede validar — 294 filas

| obra | filas | por qué |
|---|--:|---|
| **Milindapañha** | **248** | **paracanónico**: no está en la BD, y el VRI lo tiene como `s0520m.**nrf**.xml` — *non-reference*, fuera del canon. Ni PTS ni CST lo dan como texto canónico |
| **Nettippakaraṇa** | 37 | no está en la BD. El CST **sí** lo tiene (`s0519m.mul.xml`), pero sin el lado PTS no hay par que cotejar |
| **Peṭakopadesa** | 9 | no está en la BD; el VRI lo tiene como `s0518m.**nrf**.xml` |

⚠️ **Las 248 del Milindapañha están escondidas bajo la etiqueta `Pet`** del Excel, junto a las 9 del
Peṭakopadesa: `PTS Vol = Pet` agrupa **dos obras distintas**, y una de ellas ni siquiera es canónica.
Cualquier recuento que trate `Pet` como una unidad está mezclando 248 filas invalidables con 9.

### Trabajo previo que el catastro deja a la vista

- **Tres etiquetas del Excel mezclan obras**: `Pet` = Milindapañha (248) + Peṭakopadesa (9);
  `Bv` = Buddhavaṃsa (29) + Cariyāpiṭaka (34); `Ap` = Thera-apadāna (563) + Therī-apadāna (40).
  Separarlas es requisito, no adorno: cada obra tiene su fichero VRI y su libro de la BD.
- **Desfase de paginación entre la BD y el Excel** en al menos una obra: el **Cariyāpiṭaka** va
  `1-37` en la BD y `73-101` en el Excel — **−72**, porque PTS lo pagina a continuación del
  Buddhavaṃsa y la BD le reinicia la cuenta. Sondado también en Therī-gāthā (+8) y Apadāna (−2),
  donde hace falta calibrar antes de emparejar nada.
- **627 filas sin `Sutta #`** (todo el Jātaka y el Niddesa, entre otras): no hay clave numérica, así
  que el emparejamiento tendrá que apoyarse en el nombre y el contenido desde el principio.
- **Ninguna fila de KN tiene `DPR Ref`** — no existe el atajo que resolvió A i.
- **Ninguna tiene `VRI Ref`**: el lado CST está entero por construir.
- **10 filas son encabezados de sección** (`Therāpadāna`, `Jātaka`, `Niddesa`, `Milindapañha`…) sin
  página ni referencia. No son suttas y no deberían contar como filas pendientes.

### Consecuencia para el recuento

El techo real de KN por este camino es **2.066 de 2.360** (87,5 %). Las otras 294 no son deuda de
método: son filas cuyo texto PTS **no está en la base de datos**, y tres de ellas apuntan a obras
que el propio CST clasifica fuera del canon. Antes de dar KN por cerrado habrá que decidir qué se
hace con ellas — igual que con las colas de AN.

---

## A i — ANÁLISIS CRÍTICO de la práctica editorial, y plan (2026-07-25)

A i lleva todo el proyecto declarado «sin abordar a propósito». La razón que se daba —«el CST no da
nombre por sutta y las tres ediciones cuentan unidades distintas»— es cierta pero **incompleta**, y
al medirla resulta que el problema no está donde se creía.

### 1. Lo que Morris hace, dicho por él mismo

La PTS publicó en 1883 una edición de los dos primeros nipātas que **retiró** «on account of the
numerous contractions used in the text»; la de 1885 es la buena y en ella «**only a few pe's or
.... have been employed**». Es decir: Morris **sabe** que el problema editorial de A i es la
compresión, y su edición es una reacción deliberada contra una compresión anterior excesiva. Aun
así, el Eka que imprime numera **272** suttas donde el CST numera **611**.

Esa proporción no es error de nadie. Es la política: **donde el canon repite una serie, Morris
imprime el patrón y numera el grupo**; el CST numera cada miembro. Las dos son decisiones
editoriales legítimas y el desfase es su consecuencia aritmética.

Morris además declara lo que no sabe. Sobre el Acelaka-vagga del Tika: «The Acelaka-vagga
**probably** included only suttas 151, 152…». Y sobre los uddāna: «The text of these Uddānas is
**corrupt in many places**, and though it has been compared with the vaggas themselves, it is still
not free from error», y el del Tika «does not go beyond the Maṅgala-vagga». Un editor que marca sus
propias conjeturas es un editor fiable; lo que no se puede es tratar sus conjeturas como datos.

### 2. Las tres coordenadas, medidas

| | Eka | Duka | Tika |
|---|--:|--:|--:|
| **PTS** — suttas numerados / vaggas | 272 / 21 | 212 / 17 | 163 / 16 |
| **CST** — paranums / `div` | 611 / 20 | 246 / 19 | 184 / 18 |
| **Excel** — filas | 159 | 111 | 165 |

Ni una sola de las tres cifras coincide con otra en ningún nipāta. Pero el desacuerdo **no está
repartido**:

**El Eka casa EXACTAMENTE en sus doce primeros vaggas** — `10, 10, 10, 10, 10, 10, 10, 10, 17, 42,
10, 20` en las dos ediciones, incluidos los dos números raros (17 y 42). Toda la divergencia del
Eka está de su vagga 13 en adelante: PTS `7, 7, 25, 1, 10, 17, 2, 12, 22` contra CST `18, 80, 28,
—, 70, 16, 181, 37, 12`.

**El Duka casa en sus quince primeros vaggas**, emparejados por nombre uno a uno
(`Kammakaraṇa ↔ Kammakaraṇavaggo`, …), con las cuentas idénticas salvo en los tres primeros. Toda
su divergencia está en la cola de peyyāla, donde PTS agrupa en dos vaggas lo que el CST reparte en
cuatro `-peyyālaṃ`.

Conclusión: **A i no es un volumen difuso, es un volumen con una mitad limpia y una cola dura.**
Tratarlo como un bloque homogéneo —que es lo que se venía haciendo al aplazarlo entero— es el
mismo error que la regla (6) prohíbe.

### 3. En la segunda mitad del Eka las dos ediciones ni siquiera nombran igual

| Morris | CST |
|---|---|
| XVII **Bīja** | 16. **Ekadhamma**pāḷi |
| XVIII **Makkhali** | 17. **Pasādakaradhamma**vaggo |
| XIX **Appamattaka** | 18. **Aparaaccharāsaṅghāta**vaggo |
| XX–XXI **Jhāna** | 19. Kāyagatāsativaggo · 20. Amatavaggo |

Y el CST marca dos de esas unidades como **`-pāḷi`, no `-vagga`** (`Aṭṭhānapāḷi`, `Ekadhammapāḷi`):
la propia edición está diciendo que ahí no tiene vaggas sino tiradas de texto. El emparejamiento
por nombre, que resuelve el Duka entero, **no sirve** en este tramo: hay que ir por contenido.

### 4. Lo que NO es divergencia editorial y hay que descontar antes de contar nada

- **Duka, vagga 1**: sus marcadores son `2, 3, …, 10` — **falta el `1.`**. No es que PTS funda dos
  suttas: es un marcador perdido, de la misma clase que el `64.` de A ii y el `XXXVII` de A v. El
  detector lo daba como «PTS funde 1» y es un defecto de lectura, no del impreso.
- **Marcadores no contiguos** en el Eka tardío: el vagga 15 salta del 13 al 17, el 20 va
  `1, 2, 10, 14, 18, 22, 32, 39, 47, 55, 63, 192`. Son **marcadores de rango**: PTS numera «10-13»
  con un solo `10.`. Contarlos como suttas sueltos falsea las dos columnas a la vez.

### 5. El hallazgo: la coordenada de PTS ya está en el Excel, sin usar

El `Sutta #` de A i es un número corrido (1..627) que **no** es el paranum del CST. Pero la columna
**`DPR Ref`** de A i tiene **tres niveles** —`AN 1.1.1`, `AN 2.14.1-12`— y esos tres niveles son
`nipāta.vagga.sutta`, que es **exactamente el sistema de coordenadas que PTS imprime**: numeral
romano de vagga + arábigo que reinicia dentro de él.

Contrastado contra los marcadores reales de la BD:

| | filas | el `(vagga, sutta)` del `DPR Ref` **existe** como marcador de PTS |
|---|--:|--:|
| Eka | 159 | **152** |
| Duka | 111 | **107** |

**259 de 270 filas de Eka y Duka traen ya escrita su referencia al impreso**, y nadie la había
usado porque el pipeline entero está construido sobre el paranum del CST. Las 11 que fallan son
identificables: 7 son del vagga 20 del Eka (el Jhāna, donde el DPR cuenta hasta 182 y PTS imprime
12 marcadores), 3 de la cola peyyāla del Duka, y `2.1` es el marcador perdido del punto 4.

⚠️ Esto **no** contradice la regla (5) —la clave canónica del lado CST sigue siendo el paranum del
VRI—. Lo que dice es que en A i hay **una segunda clave, del lado PTS**, que en los otros volúmenes
no existía porque allí el marcador lleva el nº corrido y basta con él.

### 6. Plan

**Fase A — descontar los defectos de lectura.** ✅ **HECHA** (2026-07-25)

- **El marcador perdido era uno solo y está explicado.** El Duka arranca en A i 47 con
  `DUKA-NIPĀTA.` + `I.` y el texto seguido: PTS **no numera el primer sutta del nipāta** porque lo
  abre el encabezado, y su primer arábigo es el `2.`. `an1_markers` lo emite ahora en el régimen
  `vagga_romano` cuando el primer arábigo del vagga es un `2` — el vagga pasa de 9 a **10**, que es
  lo que cuenta el CST. Es el único caso en los 38 vaggas de Eka y Duka, y los marcadores de
  A ii–A v no se mueven (270 · 272 · 124 · 80 · 90 · 100 · 218 · 22, idénticos).

- **Los «marcadores de rango» no eran rangos: son CABEZAS DE TIRADA.** El vagga 20 del Eka imprime
  `1, 2, 10, 14, 18, 22, 32, 39, 47, 55, 63, 192` y entre ellos va `…pe…`: PTS **numera los 192
  suttas del vagga en su propio sistema** y sólo escribe el número donde empieza cada tirada
  elidida. Contar los marcadores daba «12 suttas» y era leer mal la página.

- **Con eso, el lado PTS de A i queda resuelto por una regla de dos líneas**: la fila cuyo
  `DPR Ref` dice `(vagga v, sutta n)` cae en **el último marcador de v con número ≤ n**, que es
  exactamente como se cita el impreso.

  | | filas | resuelve | y la página coincide con el Excel (±1) |
  |---|--:|--:|--:|
  | Eka | 159 | **159** | **158** |
  | Duka | 111 | **110** | **110** |

  La única que falla es `2.19`, la fila fundida conocida (`Raw ID = «AN 2.19(*) + AN 3.29(*):
  Adhikaraṇa 9 + Andha»`), que es además una de las claves duplicadas que `check_integrity` lleva
  señalando desde el principio.

*Consecuencia*: **A i no está bloqueado por el lado de PTS.** Lo que queda por resolver es el lado
CST, y sólo en la cola.

**Fase B — el Duka entero y los doce primeros vaggas del Eka.** ✅ **HECHA** (2026-07-25).
**197 filas cerradas** (Eka 91/91, Duka 106/106) con `an1_eka_duka.py` + `reconcile_an1_ekaduka.py`,
y **cero llamadas a API**. A i pasa de 151/435 a **347/435**.

Tres comprobaciones independientes, ninguna usando lo que usan las otras: el marcador impreso por
la regla de la fase A; el paranum por posición en el `div` (y por **contenido** en los vaggas 2 y 3
del Duka, donde los recuentos no coinciden — ahí el marcador 10 se lleva el paranum 21 y el **20 se
queda sin marcador**, porque PTS imprime bajo un solo número el par `saddhammassa sammosāya` /
`ṭhitiyā` que el CST numera aparte); y la cobertura de contenido. Más la página.

⚠️ **La cobertura se mide sobre n-gramas de caracteres, no sobre palabras.** En pali la composición
es libre en la ortografía: PTS escribe `kodha vinayo ca upanaha vinayo` y el CST `kodhavinayo ca
upanahavinayo`. Es el mismo texto y por conjuntos de palabras daba **0,22** — bastaba para tirar
cuatro filas correctas. Sobre 4-gramas da 0,9.

**El umbral está medido, no elegido**: la cobertura real de las 197 va de **0,64 a 1,00** (mediana
0,97-0,99) y un control con pares de vaggas distintos da media **0,26** y máximo **0,48**. El
umbral (0,55) cae en el hueco.

Y una errata más del OCR reparada por continuidad: `210.` en A i 91,14 va entre el `9.` y el `11.`
y es el **`10.`** con un dígito de más — misma clase que el `2O` por `20` de S iv.

**Fase C — la cola del Eka.** ✅ **52 de 68** (2026-07-25), `an1_eka_cola.py`. A i → **399/435**.

Lo que la fase descubre es **por qué** la cola era dura, y no es lo que se suponía: en la mitad
limpia el `Sutta #` **es** el paranum del CST (diferencia 0 en las 91 filas cerradas), y en la cola
**deriva** — `1.306` es el paranum 298, `1.394` el 382, `1.616-627` el 600. La deriva **crece**
(−8 en el vagga 17, −12 en el 20, −16 al final) y no es un desfase corregible con una resta: se
abre y se cierra según qué agrupa cada edición. Así que en la cola el `Sutta #` **no sirve de clave
del lado CST**, y hay que ir por contenido.

Lo que sí sigue valiendo es el lado PTS: el `DPR Ref` da el marcador y la página lo confirma. El
contenido sólo decide **cuál de los 611 paranums** es la contraparte — bloquear primero por
estructura, decidir después por contenido, como en el piloto de A ii.

Se acepta una fila con **cuatro señales**: cobertura ≥ 0,85; página del marcador ≡ la del Excel;
separación con el segundo candidato (filas individuales); y, en las de rango, **una de dos**:
o el paranum elegido cae **dentro** del rango que declara el `Sutta #` —las dos coordenadas se
confirman entre sí, que es lo que pasa en los vaggas 13-16, donde el Etadagga va `188-267` en las
dos ediciones—, o el **tramo hallado tiene tantos paranums como suttas declara la fila**
(`1.431-438` son ocho y el contenido da `419-426`, ocho: una coincidencia numérica que el contenido
no puede fabricar).

#### La cola del Eka se cierra entera con la PARTICIÓN FORZADA — y con ella salen dos errores míos

La pasada por contenido resuelve cada fila **por separado**, y donde varias comparten marcador eso
no puede funcionar: **falla en silencio**. Tres filas del bloque del marcador 63 se escribieron con
**la misma `VRI Ref`** (`483-492`), y la comprobación de cardinalidad no lo vio porque es *por
fila* — cada tramo tenía los diez paranums que su fila declara; lo que nadie miraba es que eran
**los mismos diez** tres veces. Y `1.378-393` se cerró con `378-393` solapando a `1.402-405`
(`390-393`), porque la regla «el ganador cae dentro del propio rango» se cumple por casualidad
cuando el rango es ancho y el desfase de doce.

Es el punto ciego en su forma más pura: **pares coherentes cada uno consigo mismo y mutuamente
incompatibles**. Lo que los caza no es el cotejo sino una comprobación global — **que ningún tramo
solape a otro**, que ahora se corre siempre.

El argumento que sí decide es la **partición forzada** (`an1_eka_particion.py`): cuando un bloque de
filas consecutivas cae entre dos anclas resueltas y lo que declaran suma **exactamente** los
paranums libres, sólo hay un reparto posible. En el bloque del marcador 63:

    `1.447-454` ocupa hasta el 442  →  el bloque empieza en 443
    las seis filas declaran 10+10+10+10+40+40 = 120
    443 + 120 − 1 = 562 = **el último paranum del `div` 18 del CST**

Que termine **al dígito** donde acaba el `div` no se puede ajustar: o cuadra o no. Cuatro bloques
cuadran así (443-562, 312-319, 402-418, 584-611) y un quinto (321-389) lo fijan los anclajes de
contenido, absorbiendo la diferencia el *Jambudīpapeyyāla*, que es justo la fila donde el CST
subdivide más fino que el Excel.

Tres filas más son **many-to-one** y el hueco entre sus vecinas lo dice sin ambigüedad: `1.296-305`
son diez suttas del Excel para **dos** paranums (296-297), y `1.586-590` son cinco para **uno**
(574). No es error de nadie: es la compresión de Morris otra vez.

⚠️ Y un tercer error de la misma familia en el Duka: `2.27`/`2.28`/`2.29` —cuyo `DPR Ref` lleva los
sufijos `8a`/`8b`/`8c`— habían recibido las tres el paranum 29. El marcador 8 (A i 60,25) cubre
**28, 29 y 30** (cobertura 0,99 · 1,00 · 0,89) y los sufijos describen exactamente ese reparto.
Corregidas. **Ya no queda ninguna `VRI Ref` repetida ni ningún tramo solapado en A i.**

**Fase D — el Tika.** ✅ **10 de 18** (2026-07-25), `reconcile_an1_tika_restos.py`. A i → **409/435**.

Se cierran seis filas de rango por **redundancia probada** (todos sus miembros ya CONFIRMADO con su
`VRI Ref`; ojo a que **no** coinciden con el `Sutta #`: el Tika va +1 desde el paranum 49, así que
`3.51-52` es `52-53` y `3.58-9` es `59-60`), los **tres `REVISAR`** —los tres rechazaban por lo
mismo, que **PTS imprime dos suttas del CST bajo un solo número** (el marcador 32 cubre el paranum
33; el 136 cubre el 139 y el 140), y el cotejo da **0,90** en los tres: es A ii 174 otra vez— y
`3.62 Bhaya`, que el alineador había dejado fuera y el contenido resuelve con 0,96 contra 0,60.

Las **8 anotadas** no son deuda de método:

- **`3.156`** empata entre los paranums 162 y 163 (0,97 los dos) y cae exactamente donde **Morris
  declara que conjetura**: «The Acelaka-vagga **probably** included only suttas 151, 152; so that
  the ten suttas 153-162 made a second vagga…». Con el editor diciendo que no lo sabe, resolverlo
  por cobertura sería inventar precisión que la fuente no tiene.
- **Siete filas cuya numeración excede a la del CST**: el Tika del Excel llega a 352 y `s0402m2`
  acaba en **184**; su Duka llega a 479 y `s0402m1` acaba en **246**. Mismo caso que `11.502-981` en
  A v, y misma salida: decisión editorial, no aritmética.

**Lo que NO se hará**: forzar una correspondencia 1:1 donde las ediciones no la tienen. El Eka
tardío es un caso en el que **PTS y el CST no editan la misma unidad de texto**, y la salida
correcta puede ser una fila con `VRI Ref` de rango, no una fila por paranum.

---

## 2026-07-25 — **A ii CERRADO 🔒 303/303**: el quinto régimen y el uddāna como detector

Cierra el Catukka entero. Las 35 filas que `validador_an2_catukka.py` dejaba fuera **por diseño**
se resolvieron **sin una sola llamada a API**, y ése es el punto de método: donde las dos ediciones
eliden no hay texto que cotejar, el REJECT de Gemini es un falso negativo por elisión, y lo que
firma la fila es **prueba mecánica o la lectura del impreso**.

### El quinto régimen de AN — `an_peyyala.py`

Los cuatro alineadores numerados suponen «un sutta ↔ un marcador ↔ un `subhead`». Al final de cada
nipāta ese supuesto **se acaba**, y de maneras distintas en cada volumen:

| tramo | PTS | CST |
|---|---|---|
| A ii 256-257 (`4.277-783`) | **un solo sutta numerado** (`271.`) con 4 párrafos | dos `<p>` de rango |
| A iii 271-278 | bloques separados por **ornamento** (`U+E0E0`), y uno cubre varios | `subhead` de rango |
| A iv 144-148 / 347-349 | bloques separados por **raya** de guiones | idem |
| A iv 462-465 | **marcador de RANGO romano** (`LXXIII-LXXXI.`) + uddāna | 73 individual, resto agrupado |
| A v 303-310 | 7 suttas numerados (`CCX.`…) | `div` **sin `subhead`** |
| A v 359-360 | **un** bloque para toda la serie | un `<p n="22-29">` |

La prueba que se exige ahí: **el término distintivo de cada fila aparece LITERALMENTE y EN ORDEN en
las dos ediciones**, y la aritmética del rango cuadra. En el *rāga-peyyāla* del Catukka, 25/25 con
página ±1 (27 = 9 × 3 para los nueve `-āya`; 480 = 16 × 30 para los dieciséis kilesa).

**Lo que esta prueba caza y el LLM no podía:** la serie de kilesa **falla en el último término**
porque el Excel escribía `Macchariya` donde el impreso y el CST leen `pamādassa`, y `Pamāda` donde
los dos leen `madassa`. Corregidos los dos nombres, las dieciséis casan. El mismo error se repite
en A iii (`5.1053-1102` / `5.1103-1152`), **aún sin corregir**.

### El uddāna: **detector**, no autoridad — `uddana.py` + `detector_uddana.py`

La estrofa que cierra cada vagga es, en el régimen numerado, **el único sitio donde PTS nombra sus
suttas** (el impreso no titula). Tiene gramática propia y se analiza con **pyparsing**: cabecera,
multiplicadores (`dve khatā` = *dos* suttas Khata), **ordinales de comprobación** (`anusotaṃ
pañcamaṃ` — el impreso verificándose a sí mismo), y fórmulas de cierre. Los **dvandvas** del verso
(`taṇhāyogena` = Taṇhā + Yoga) los deshace el **deconstructor de DPD**, con una regla dura: DPD
**propone**, el CST **decide** — la partición sólo se acepta si sus partes casan con títulos
consecutivos del CST, porque `bhattuddesena → bhatto + uddesena` es un compuesto de verdad y sin
embargo es UN solo sutta.

⚠️ **El uddāna NO es autoridad sobre la numeración de PTS, sólo sobre el contenido del vagga.**
Verificado contra el impreso en el *Sañcetaniya-vagga* (A ii 157-167): la estrofa se lee perfecta
—diez nombres, cada uno con un único título del CST, en orden, y el `pañcamaṃ` en su sitio— y aun
así «nombre k ↔ marcador k» es **falso**, porque PTS **parte** el `Cetanā` del CST en dos
marcadores (171 y 172, el segundo es el `cattāro attabhāvapaṭilābhā`) y **funde** el Mahākoṭṭhika y
el Ānanda en uno (174, que imprime los dos seguidos). Una división y una fusión que se compensan y
resincronizan en 175. Imponer el mapeo empeoraba el alineamiento (de 3 fallos a 10 en el piloto),
así que el uddāna **anota y no impone**.

**`detector_uddana.py` sobre AN entero**: 186 vaggas → **31 vaggas ordinarios donde PTS y el CST no
cuentan lo mismo** (A i 13, A ii 6, A iii 4, A iv 4, A v 4), más 24 tramos peyyāla. Cada uno es una
división o una fusión que el cotejo de contenido **no puede ver**. En 9 de ellos el uddāna además
declara quién tiene razón. Este mapa es requisito antes de tocar Eka/Duka y KN.

> ⚠️ Las cifras de **A i** en el detector son artefactos: en Eka y Duka el marcador numera *por
> vagga* y reinicia, así que el recuento por vagga no es comparable. A i necesita su propio
> tratamiento.

**Dos correcciones de método que salieron de la corrida y están en el código:** (a) quien decide si
hay asimetría es **PTS contra CST**, no el uddāna —si las dos ediciones coinciden y la estrofa no,
el sospechoso es la estrofa—; (b) `pp.ZeroOrMore` **se detiene** en el primer token que no entiende,
así que la `c` suelta de `c' eva` cortaba la estrofa entera (`Sambodhi nissayo c' eva Meghiyaṃ…`
daba dos nombres en vez de diez, y eso se leía como una fusión inexistente de ocho suttas).

### Normalización interna a la convención VRI — `pali_norm.py`

**Regla nueva: dentro del pipeline todo se compara en una sola ortografía, la del CST/VRI**, que es
la de las claves de DPD y la del lado que aporta los títulos. Las 7 reglas están **medidas sobre
los dos corpus completos** del Aṅguttara, no puestas de memoria: `m` final → `ṃ` (PTS 4.500 casos,
CST **0**), `vy` → `by` (841 vs 972), `viriy` → `vīriy`, `sañño` → `saṃyo`, y nasal homorgánica
**sólo ante oclusiva** (ante semivocal el CST conserva la niggahīta: `saṃyojana`, `saṃvāsa`).

Va cableada en `an_peyyala.fold()` —**antes** de plegar, porque las reglas necesitan los diacríticos
que el plegado ya borró— y en las consultas a DPD. Cobertura de DPD sobre el vocabulario de A ii:
**79 % → 82 %**. Todas las reglas **conservan la longitud en caracteres**, lo que permite
normalizar sin romper el mapa posición→(página, línea); hay una aserción que lo vigila.

De paso, `pali_morphology.VALID_CLUSTERS` pasa de 75 a 108 grupos, **todos por medición** sobre las
40.907 palabras distintas de las dos ediciones. `ṃy`, `yh`, `mbh` y `mph` estaban excluidos como
«no atestiguados» y están en `saṃyojana`, `mayhaṃ`, `ārambha` y `samphassa`. La **vacilación de VRI
con la niggahīta ante oclusiva** (`saṃkhaṃ` junto a `saṅkhāra`, en las dos ediciones) va en un
conjunto **aparte**: es pali válido, pero no normalizado, y son dos preguntas distintas.

### Estrategia «vagga primero, contenido después» — `piloto_hash_vagga.py`

Piloto sobre A ii con verdad-terreno (263 pares ya CONFIRMADO):

| capa | acierto | empates en cabeza |
|---|--:|--:|
| **1. bloqueo por vagga** (colofón PTS ↔ `<div>` CST) | 262/263 (**99,6 %**) | — |
| 2. firma de contenido, argmax independiente | 84,4 % | — |
| **2. + asignación MONÓTONA dentro del vagga** | 261/263 (**99,2 %**) | 36/270 |
| …y con el **texto completo** del CST (74 % que se descartaba) | 261/263 (99,2 %) | **0/270** |

> **Los empates eran un artefacto del texto truncado.** `an_peyyala.cst_unidades` sólo leía los
> `<p>` con atributo `n`, y el CST lo pone únicamente en el primero de cada sutta: se perdía el
> 74 % del cuerpo. Con el texto entero el vocabulario del Catukka pasa de 2.356 a 6.973 palabras y
> **los 36 empates desaparecen**, incluido el Kamma-vagga, que parecía indistinguible. El acierto
> no sube porque los dos fallos que quedan no son de firma: en `173` el contenido ahora acierta con
> holgura (0,80 contra 0,39) y es la **asignación** la que falla, porque PTS parte en dos marcadores
> (171 y 172) lo que el CST numera de una pieza. Dar **capacidad 2** a cada sutta del CST se probó
> y es peor —de 2 fallos a 4—: la asimetría real es rara y la holgura, cara.

La firma usa lo que la elisión no altera: cobertura de vocabulario **ponderada por idf** (0,60),
**progresión** —correlación de rangos del orden de primera aparición— (0,25) y **razón de cantidad
de palabras** (0,15). El idf es lo que rompe los empates de las series de repetición; la frecuencia
(tf) no aportó nada. Y la monotonía no es adorno: sin ella el mismo hash da 84 %.

⚠️ **La verdad-terreno es una RELACIÓN, no una función**: un marcador de PTS puede servir a varios
suttas del CST (el nº 174 imprime seguidos el Mahākoṭṭhika y el Ānanda, y el Excel los distingue por
línea). Leerla como diccionario contaba como fallo del piloto lo que era un acierto.

### Presupuesto por operación — `audit_tiempo.py`

Auditor hermano de `check_integrity.py`, pero lo que vigila no es el dato sino **el coste de llegar
a él**. Toda operación declara su presupuesto (pasos y minutos) **antes** de empezar; al agotarse se
para, se informa de lo conseguido y de lo que falta, y se pide decisión. Ampliar el presupuesto es
decisión de Jorge, no del que ejecuta. `estado` devuelve código 1 cuando se agota, para que la
parada no dependa de que alguien lea la salida.

### Correcciones de dato en el Excel (A ii)

| fila | corrección | evidencia |
|---|---|---|
| `4.257 «Ājānīya 2»` | → **`4.260`** | llevaba el nº del DPR y **duplicaba la clave** de Māluṅkyāputta |
| `4.257 «Māluṅkyāputta»` | página **248**, no 251 | el sutta se imprime en A ii 248-249 |
| `4.724-753` | **Mada peyyāla** | la serie de kilesa del impreso y del CST |
| `4.754-783` | **Pamāda peyyāla** | idem; 30 paranums por kilesa desde 304 |

Y tres filas que sólo parecían rotas: `4.64` **no tiene marcador porque el `64.` se perdió en el
OCR** (A ii 71,1 sigue con el Niraya y la numeración se reanuda en `65.`, misma clase que el
`XXXVII` perdido de A v); `4.74`/`4.75` van al marcador **75** y **76** porque el nº74 del impreso
lo ocupa el *Vadhu*.

`check_integrity` pierde las dos incidencias de A ii: la clave duplicada y el salto de página hacia
atrás. Canon **3286/6098 (53,9 %)**.

---

## MEDIDA 2026-07-25 — la clave canónica del lado CST pasa a ser el **paranum del XML VRI**

Se abandona el **DPR como clave de unión** (no como etiqueta). Motivo acumulado: S ii desplazado
+7, S iv (SN 35) +17 y +47, AN +15 por **desdoblamientos de fila** (`3.32` del DPR se parte en
`3.32a`/`3.32b`), y en `massive.tsv` el `dpr_code` de AN tiene **138 códigos duplicados** con
asignaciones incoherentes entre sí (`AN3.2` → `an3.1.2.8` mientras `AN3.11` → `an3.1.2.11`).
Auditado **por nombre**, `massive` sólo concuerda con **66 de las 1738** filas de AN: allí no sirve
de puente. En todos esos casos el validador aprobaba un par correcto pero **ajeno a la fila**.

- **Columna nueva `VRI Ref`**, formato `«<fichero>:<paranum>»` (`s0303m:146`; rangos `s0304m:33-42`).
- **Rellenada en 1982 filas**: DN 34/34, MN 152/152, SN 1796/1814. AN y KN se harán con su alineador.
- **`Sutta #` NO se reescribe.** Su validación se hizo contra esas filas y `Raw ID` conserva el
  original de la fuente: se le quita el papel de clave, no se destruye.
- **Criterio de aceptación**: una fila sólo recibe clave si el **título CST recomputado coincide con
  el que se validó**. Saltaron 24 discrepancias en S iii — fallo del recomputo, que no reproducía el
  `ditthi_pairs` ni el fallback por título — y se resolvieron tomando el **título validado** como
  autoridad.
- Hallazgos estructurales del camino, útiles para AN/KN:
  - **La granularidad del `<div>` cambia por nikāya**: en DN un div es **un sutta**, en MN y AN un
    **vagga**, en SN un **saṃyutta**. DN se resuelve por div; MN por subhead filtrando los que son
    títulos de sutta (los encabezados de sección internos se llevaban los paranums: 118/152).
  - **El volumen de PTS no es el fichero del CST**: PTS «M i» abarca MN 1-76 pero `s0201m` es el
    Mūlapaṇṇāsa (MN 1-50). El fichero se elige por el **número de sutta**.
  - Normalizar títulos exige **colapsar letras dobles** (`acchariyābbhuta` ≡ `acchariya-abbhuta`) y
    recortar en el primer `suttaṃ` (las variantes se anotan entre llaves en un lado y sueltas en el
    otro).
- **18 filas de SN se quedan sin clave, a propósito**: son firmas humanas en bloque sin veredicto en
  el JSON (S ii `12.83-93`, peyyāla de S v). Se intentó apuntar `12.83-93` al bloque
  «1. Satthusuttaṃ» y **la comprobación de contenido lo desmintió** — ese bloque no contiene ninguno
  de los términos del peyyāla. Sólo `S v 46.87` tenía evidencia positiva (nombre y contenido) y se
  resolvió a mano.

---

## Date: 2026-07-21 (updated 2026-07-25 — SN ENTERO CERRADO 🔒 1814/1814)

---

## UPDATE 2026-07-24 — Cache↔Excel reconciliation (SN)

The master Excel had been regenerated (by `build_final_excel.py`) *after* the SN Helmer runs,
which **overwrote the SN HELMER marks back to `DB_VERIFIED`**. The DeepSeek verdicts still lived
in `helmer_ptscst_cache.json`, so they were reconciled back without any new API calls:

- **SN IV**: 106 exact-marker verdicts recovered from cache → re-written to Excel as
  **94 `HELMER_APPROVED` + 12 `HELMER_REJECT`** (previously all 106 were flat-marked
  `HELMER_APPROVED`, which hid the rejects). The 12 rejects are Feer-abbreviation / orthographic
  false positives — the sutta *names* match the CST titles exactly, so the page references are
  sound; only **SN 36.26** looks worth a manual look. The 238 peyyāla SN IV entries stay
  `DB_VERIFIED` (no individual marker → not CST-validatable).
- **SN V**: verdicts in cache are **NOT trustworthy** (36 APPROVE / 430 REJECT over 466 exact
  matches = 8%). This reflects a **broken saṃyutta-aware CST mapping** in `helmer_sn5_all.py`,
  not bad references (the pilot on 20 gave 85%). **Not volcado.** SN V still needs the CST mapping
  fixed and re-run. See PENDING below.
- **SN I/II/III**: never had a full Helmer pass (only a SN I pilot); they remain `DB_VERIFIED`.

Current SN validation state: 94 `HELMER_APPROVED`, 12 `HELMER_REJECT`, 1 `HELMER_FIXED`,
1699 `DB_VERIFIED` (of 1806). A timestamped Excel backup was made before the write
(`PTS_Reference_Complete_Canon.bak-*.xlsx`).

> **Where PTS↔CST concordance actually stands (Excel-reflected):** DN 34/34 ✅, MN 152/152 ✅,
> SN IV 94/106 ✅ (12 to review). SN I/II/III, SN V, AN, KN: not CST-validated in the Excel yet.

### `Estado` column (binary status) — added 2026-07-24

`PTS_Reference_Complete_Canon.xlsx` now carries an **`Estado`** column with exactly two values.
Use this terminology consistently across the project:

- **CONFIRMADO** — reference exact, verified and resolved by **Helmer (PTS↔CST) only**. Maps from
  `Validation` ∈ {`HELMER_APPROVED`, `HELMER_PTS_TRUNCATED`, `HELMER_FIXED`}.
  **Rule (2026-07-24): without Helmer, nothing can be CONFIRMADO** — DB/RTE/marker/incipit
  verification is *not* sufficient. (This supersedes the earlier "CST + BD" criterion; `DB_VERIFIED`
  is now PENDIENTE.)
- **PENDIENTE** — everything else: `DB_VERIFIED` (BD-verified but no CST), `HELMER_REJECT`
  (discrepancy), `OK` / `OK+RTE` / `OK_CONT`, `OK_HEAD`, `OK_NEAR`, `RTE_ONLY`, `VERSE_ONLY`,
  `EXTRA_CANON`, `UNVERIFIED` / `UNVERIF`. When evidence is insufficient → **PENDIENTE**.

| Nikāya | Entries | CONFIRMADO | PENDIENTE | % CONF |
|--------|--------:|-----------:|----------:|-------:|
| DN | 34 | 34 | 0 | 100.0% |
| MN | 152 | 152 | 0 | 100.0% |
| SN | 1814 | 1814 | 0 | 100.0% |
| **AN** | **1737** | **1737** | **0** | **100.0%** |
| KN | 2360 | 773 | 1587 | 32.8% |
| **TOTAL** | **6097** | **4510** | **1587** | **74.0%** |

> **KN empezado por el Khuddakapāṭha: 9/9** (`kn_khuddakapatha.py`). Es la obra más pequeña del
> nikāya y por eso es donde se fija el método. Por una vez **las tres fuentes cuentan lo mismo**:
> nueve secciones del impreso (numeral romano `I.`…`IX.` y colofón de cierre), nueve
> `<div rend="chapter">` del CST con los mismos nombres y en el mismo orden, y nueve filas. La
> cobertura de contenido va de **0,90 a 1,00**.
>
> ⚠️ **Pero la clave del lado CST no puede ser la de SN y AN**, y esto vale para todo KN: el `n` del
> CST **reinicia dentro de cada capítulo** —hay un `n=1` en el capítulo 2, otro en el 4, otro en el
> 5, 6, 7, 8 y 9— y dos capítulos (`Saraṇattayaṃ`, `Dvattiṃsākāro`) **no tienen `n` ninguno**. Un
> `s0501m:1` no identificaría nada. La forma nueva es **`<fichero>:c<capítulo>[.<item>]`**
> (`s0501m:c5`), y `check_integrity` la valida contra los `<div rend="chapter">` del fichero. Ver la
> regla (5-bis) de `CLAUDE.md`.
>
> **Dhammapada 26/26** (`kn_dhammapada.py`). Las tres fuentes coinciden **estrofa por estrofa**: el
> impreso numera cada verso al margen (`1.`, `21.`, `383.`), el `n` del CST **es** el número de
> estrofa —corrido de 1 a 423, aquí sí— y el Excel ya traía el rango en `PTS Alt/Verse`. Las 26
> cuadran (`1-20, 21-32, … 383-423`) y la página impresa de la estrofa inicial es **exactamente** la
> que declara el Excel en las 26. Cobertura 0,91-0,96.
>
> ⚠️ **Cambio de notación (regla (5-ter))**: en KN la referencia pasa a ser la **estrofa** o la
> **sección**, no la página — `Dhp 21-32`, `Khp 5`. `Dhp 21-32` identifica el Appamādavagga en
> cualquier edición; `Dh 7` sólo dice en qué página de PTS empieza. Reescritas las 26 del Dhp y las
> 9 del Khp; la página se conserva en su columna.
>
> ⚠️ Y la forma de la `VRI Ref` **no es la misma en todo KN**: en el Khuddakapāṭha el `n` reinicia
> por capítulo y hace falta la `c`; en el Dhammapada es corrido y vale la forma normal
> (`s0502m:1-20`). **Hay que mirar el fichero antes de elegir la forma.**
>
> **Itivuttaka 112/112** (`kn_itivuttaka.py`). PTS numera sus suttas de 1 a 112 de corrido y el CST
> usa **la misma numeración**; el impreso además escribe al lado la referencia relativa al nipāta
> (`112. (Cat.13)`), que es el `Sutta #` del Excel (`4.4.13`) — las dos referencias se confirman
> entre sí. **Y con él `check_integrity` pasa entero por primera vez**: las dos incidencias de
> `paginas_monotonas_por_volumen` que arrastrábamos eran justo dos páginas mal del Itivuttaka
> —`Iti 6` se imprime en It **3** y el Excel decía 5; `Iti 38` en It **31** y decía 21, donde no hay
> ningún marcador—, corregidas con la cobertura del par en 0,98 y 0,97.
>
> ⚠️ Dos defectos propios en el camino, los dos ya conocidos: **escribí un lector del CST nuevo en
> vez de usar `ap.cst_unidades`** y reintroduje el fallo de los `<p>` sin `n` — en el Itivuttaka eso
> deja a cada sutta con la fórmula `Vuttaṃ hetaṃ bhagavatā…`, **idéntica en los 112**, y el cotejo
> compara la misma frase consigo misma. Y la regex del marcador era demasiado estricta: el impreso
> escribe `90.* (Tik. V.1)`, `98 (Tik. V.9)` **sin punto** y `110. ** (Cat.11)`.
>
> **Udāna 80/80** (`kn_udana.py`), y aquí **el contenido NO es lo que decide**: sus suttas empiezan
> casi todos por `evaṃ me sutaṃ ekaṃ samayaṃ bhagavā sāvatthiyaṃ…`, así que el incipit —la sonda más
> discriminante en otras obras— sitúa 58 de 80 y falla justo porque no distingue. PTS tampoco titula
> los suttas en el cuerpo. Lo que decide es la **estructura, exacta por los dos lados** (8 vaggas de
> 10 en las dos ediciones ⇒ paranum = `(vagga−1)·10 + sutta`), comprobada con **la página dentro del
> vagga impreso y monótona (80/80)** y corroborada por el **uddāna** —`tayo ca bodhi, nigrodho te
> therā Kassapena ca…`, donde el `tayo ca bodhi` son los paranums 1-3 y el `te dasā` declara la
> cuenta— y por la cobertura (mediana 0,94 contra un control de 0,41-0,52).
>
> **Suttanipāta 73/73** (`kn_suttanipata.py`), con **la transcripción más sucia de KN**: 214 de sus
> 7.731 palabras distintas (2,8 %) no pasan la fonotáctica y son **truncamientos sin guion**
> (`adhivāsetv`, `anagāriy`), y **87 de los 1.149 números de verso no están en el texto**. Por eso el
> número de verso **no puede ser la clave**: el CST numera 1.155 y PTS 1.149, y el desfase se
> acumula hasta siete páginas en el Mahāvagga. Decide que **el CST tiene exactamente 73 suttas y el
> Excel 73 filas**, en el mismo orden y con el mismo reparto en cinco vaggas, comprobado por nombre
> (72/73) y por cobertura de **n-gramas de caracteres**, que resiste los truncamientos. Dos páginas
> **intercambiadas** en el Excel, corregidas contra el impreso (`5.4.1`→151, `5.4.2`→152: Sn 151
> abre `IV. AṬṬHAKAVAGGA. / 1. Kāmasutta.`).
>
> ⚠️ De aquí salió una regla de `pali_norm` **medida**: PTS escribe la niggahīta final como `ñ` de
> sandhi —`ahañ ca`, `kiñ ca`— **194 veces** y el CST siempre `ṃ` (0 contra 4.604). Sin la regla,
> esas 194 palabras eran discrepancias inventadas; con ella el residuo fonotáctico baja del 4,9 % al
> 2,8 %.
>
> ⚠️ Y la comparación de nombres de KN **no puede usar `an_names`**: está afinado para los nombres
> largos de AN y con los cortos se rompe —`cst_parts('Kāmasuttaṃ')` da `'k'` y
> `pts_variants('Kāma')` da **lista vacía**—. No se toca (lo usan cinco volúmenes cerrados): KN lleva
> su propia comparación.
>
> **Theragāthā 264/264 y Therīgāthā 73/73** (`kn_theragatha.py`, parametrizado para las dos: comparten
> el libro 29 de la BD y el mismo régimen). Aquí sí hay **rango de versos** en `PTS Alt/Verse`, así
> que hay **tres señales independientes** —nombre, rango y cobertura— y se firma con **dos de tres**.
> Thig invierte el reparto: el rango casa 66/73 y el nombre 73/73, mientras que en Thag el nombre
> falla 10 veces (erratas del Excel: `Jmbuka`, `Grimānanda`, `Vajaya`) y el rango salva la fila.
> Dos rangos **intercambiados** en Thig (`9.6.2`/`9.6.3`), corregidos contra el CST.
>
> ⚠️ La ventana de cobertura era **de una sola página** y partía los poemas cortos: el vagga de los
> Chakka mete tres en la 136 y el `Vāseṭṭhī` daba **0,47**; con dos páginas, **0,96**. No era un
> umbral que aflojar, era la ventana mal puesta — subió también Thag de 259 a 261.
>
> **Vimānavatthu 85/85** (`kn_vimanavatthu.py`), **en fichero propio** porque el régimen de prueba es
> otro (regla (6)): aquí **decide el nombre y el contenido sólo corrobora**. La obra está hecha de
> **pares repetidos a propósito** —`Paṭhamasuṇisā`/`Dutiyasuṇisā`, `Paṭhamakaraṇīya`/`Dutiya-`,
> `Paṭhamasūci`/`Dutiya-`— cuyo segundo miembro es el mismo poema con el donante cambiado, y en tres
> casos PTS **ni lo reimprime** (`anantaraṃ pañcavimānaṃ yathā kākatarasadāyakavimānaṃ tathā
> vitthāretabbaṃ`). Medido: la cobertura propia tiene mediana 0,94 pero la **ajena** 0,53, y **106 de
> 239** pares ajenos pasan de 0,55 — un umbral fijo no separa nada. Probando si el sutta propio es el
> que más puntúa de los 85, gana 75/85 y **las diez que pierden, pierden contra su propio gemelo**
> (0,95 contra 0,97). Lo que decide es el **nombre, 85/85**, única señal que ve el ordinal
> `Paṭhama-`/`Dutiya-`, sobre una **biyección completa y ordenada** (85 = 85, misma partición
> Itthi-/Purisavimāna, páginas monótonas 1→134). `PTS Ref` = `Vv <nº>`; el Excel no da rango de verso
> para esta obra.
>
> ⚠️ **Una ventana ancha que parecía arreglarlo todo y era vacua.** Las ocho filas de cobertura floja
> subían de 0,39 a 0,95 abriendo la ventana **dos páginas hacia atrás** — y con esa misma ventana los
> **vecinos** puntuaban igual o más (0,97 contra 0,95). Descartada. Es el punto ciego de siempre: una
> señal que sube para todos no es evidencia de nada, y sólo se ve con el **control contra el par
> ajeno**, nunca mirando la propia puntuación.
>
> **Petavatthu 51/51** (mismo fichero: es el Vimānavatthu con el signo cambiado y comparte régimen).
> Aquí apareció **una evidencia mejor que el nombre: el colofón impreso**. PTS cierra cada peta con
> su nombre y su **ordinal dentro del vagga** —`nandāpetavatthu tatiyaṃ`,
> `saṭṭhikūṭasahassapetavatthu soḷasamaṃ`—, un marcador del impreso del mismo tipo que fija el lado
> PTS en SN y AN. Se leen **48 de 51** y **los 48 nombran el peta que el CST pone en ese (vagga,
> ordinal)**; los tres que faltan quedan acotados entre sus vecinos.
>
> ⚠️ **Paré sin firmar y pedí presupuesto**, y con razón: tres filas (`7.2.5` 0,48, `7.4.2` 0,50,
> `7.4.4` 0,35) tenían el sutta **siguiente** del CST puntuando más alto que el propio sobre su
> ventana (0,89-0,95 contra 0,32-0,55) — la firma exacta de un desplazamiento +1. El colofón
> demostró que **no lo había**: `revatīpetavatthu` está impreso en p85 como cuarto del Mahāvagga,
> justo donde la fila dice. Lo que PTS no reimprime es el **texto** (`revatīpetavatthu se
> vimānavatthu no …`: lo remite al Vimānavatthu, y Serīsaka **es** `Vv 84`). La cobertura no puede
> distinguir «la fila está desplazada» de «PTS remite el texto a otra obra»; el marcador impreso sí.
>
> ⚠️ Tres defectos propios en el camino, los tres del mismo tipo — **inferir lo que el impreso dice**:
> (a) segmenté los vaggas por «dónde reinicia el ordinal» y, al faltar cuatro colofones, la
> inferencia arrastró un vagga entero de desfase (le daba a `7.4.3 Nandaka` el colofón de
> `Rathakāra`); se arregló leyendo los **encabezados impresos** (`URAGAVAGGO PAṬHAMO` p14,
> `III CŪḶAVAGGA` p47, `IV MAHĀVAGGA` p65). (b) `raiz` no contemplaba el femenino `-petivatthu`, así
> que `Sāriputtattheramātupetivatthu` no perdía su sufijo y no casaba con el `Mātu-` abreviado del
> impreso. (c) El Ubbarivagga trae **dos colofones marcados `tatiyaṃ`** y ninguno `catutthaṃ`: el
> ordinal está mal leído, no el orden. Como los colofones aparecen en orden de impresión, un ordinal
> que no avanza vale `anterior + 1` — pero **sin renumerar de corrido**, para que los cuatro huecos
> sigan siendo huecos.

> Desglose de AN (2026-07-25): **A ii 303/303, A iii 457/457, A iv 298/298 y A v 245/245 —
> los cinco CERRADOS 🔒**. **AN ENTERO CERRADO: 1737/1737.**
>
> La última fila era `«Adhikaraṇa 9 + Andha»`, con `Raw ID = «AN 2.19(*) + AN 3.29(*)»`. Se fue a
> partir en dos, como parecía pedir su nombre, y **el dato dijo que no había nada que partir**: sus
> dos supuestos componentes ya existían como filas propias —`2.19 «Adhikaraṇa 9»` en A i 58,15
> (marcador 9, paranum 19, cobertura 0,98) y `3.29 «Andha»` en A i 128 (`s0402m2:29`), ésta
> CONFIRMADO desde el Tika— y la fila fundida apuntaba a **A i 58,37**, que es el marcador 10 =
> paranums 20-21, o sea **el mismo sutta que `2.20 «Adhikaraṇa 10»`**. No era una fusión de dos
> suttas sino un **duplicado de `2.20`** con el nombre concatenado por la fuente. **Borrada**
> (decisión de Jorge), como se hizo con `12.74` en S ii: el total pasa de 6098 a **6097** filas y la
> columna `#` se renumeró.
>
> Con eso `check_integrity` pierde su última clave duplicada: **`clave_sutta_no_duplicada` pasa**,
> y lo único que queda en todo el fichero son dos saltos de página en KN.
>
> **Las colas del Duka y del Tika se anclaron al tramo del CST por decisión de Jorge**
> (`reconcile_an1_colas_cst.py`). Resultó inmediato de verificar porque ahí **el nombre de la fila
> es el nombre del `div`**: `2.180-229 «Kodha [Kodhapeyyāla]»` ↔ `1. Kodhapeyyālaṃ` (181-190),
> `2.310-479 «Rāgapeyyāla»` ↔ `4. Rāgapeyyālaṃ` (231-246), `3.163-182 «Kammapathapeyyāla»` ↔
> `7. Kammapathapeyyālaṃ` (164-183, y la fila declara 20 suttas donde el div tiene 20 paranums).
> El Excel numera 170 donde el CST tiene 16: es la compresión de Morris llevada al extremo.
>
> Y el **Acelaka-vagga se resolvió de paso, sin tocar la conjetura de Morris**: su duda es sobre
> *cuántos vaggas* forma ese material, no sobre qué texto es cada fila. `3.155` cierra en el
> paranum 156 (último del Maṅgalavaggo) y el Acelakavaggo es el div 157-163, **siete** paranums
> para las **siete** filas `3.156` + `3.157-162`: sólo hay un reparto posible. Eka y Duka
> (284 filas) siguen sin abordar a propósito.
>
> ⚠️ **`11.502-981` cierra por decisión editorial de Jorge**: PTS imprime el símil del gopālaka
> dos veces —`abhabbo` (A v 359) y `bhabbo` (A v 360 §§4-6)— y el CST **sólo numera la mitad
> negativa** (`<p n="22-29">` dice `abhabbo` diez veces y `bhabbo` ninguna; sus paranums del
> *sāmañña-vagga* son 22-501 = 480, y el Excel cuenta 960 = 480 × 2). La fila apunta a **la misma
> `VRI Ref` que su mitad gemela**, `s0404m4:22-501`: la clave deja de ser biyectiva en ese punto y
> pasa a decir la verdad —*ahí* está el texto—, que es preferible a inventarle una clave o a borrar
> una fila que el impreso tiene delante.

> Cifras al **2026-07-25**. **SN entero pasado por el validador: 1810/1815.** Desglose:
> **S i 271/271, S ii 257/257, S iii 332/332, S iv 344/344, S v 610/610 — los cinco CERRADOS 🔒**. Ya no queda ningún
> `HELMER_*` en SN: los 94 `HELMER_APPROVED` y 12 `HELMER_REJECT` de S iv se re-validaron y se
> sobrescribieron. Las 5 PENDIENTE de SN son desacuerdos gate/Gemini a arbitraje humano.
> El total pasó de 6090 a **6099 filas**: −1 (`12.74`, división solo-CST borrada) y +10 (la
> expansión de `12.75` en los 11 suttas que PTS numera). La columna `#` se renumeró.

> MN 14/38/64 (antes `OK+RTE`/PENDIENTE por errores de API transitorios) fueron re-corridos por
> Helmer DeepSeek el 2026-07-24 → **3/3 APPROVE** → `HELMER_APPROVED`/CONFIRMADO (cacheados).

> The `Validation` column is kept as the fine-grained provenance; `Estado` is the binary rollup.
> The `Summary` sheet is aligned to these counts.

---

## COMPLETED (DO NOT MODIFY)

### DN — Digha Nikaya — 34 suttas — CERRADO 🔒
- Excel: `HELMER_APPROVED`
- DeepSeek PTS↔CST: 34/34 APPROVE
- RTE cross-ref: 32/34 confirmed
- DB content: 34/34 verified
- Source files: `helmer_dn_all.py`

### MN — Majjhima Nikaya — 152 suttas — CERRADO 🔒
- Excel: `HELMER_APPROVED` (138) + `HELMER_PTS_TRUNCATED` (14)
- DeepSeek PTS↔CST: 135/149 APPROVE
- 14 PTS_TRUNCATED: suttas where PTS abbreviates text (e.g., MN 98 = Sn 35)
- MN 14, 38, 64: were transient API errors (`OK+RTE`); Helmer DeepSeek re-run on 2026-07-24 →
  3/3 APPROVE → `HELMER_APPROVED`. All 152 now CONFIRMADO.
- DB content: 152/152 verified
- Source files: `audit_mn_final.py`, `add_mn_lines.py`, cached in `helmer_ptscst_cache.json`

### SN I — Samyutta Nikaya vol 1 (S i) — 271 suttas — CERRADO 🔒 271/271
- **Estado 2026-07-25: 271/271 CONFIRMADO** (`VALIDADOR`, concordancia VRI ∧ Gemini APPROVE).
  Antes eran 270 `DB_VERIFIED` + 1 `HELMER_FIXED` (todo PENDIENTE salvo uno).
- **El front matter de Feer (`samyutta-vol-I-info.txt`) fija el lado PTS sin LLM.** Su índice y su
  introducción dan la verdad-terreno estructural: 11 saṃyuttas, **28 vaggas, 271 suttas** y la
  **página de arranque de cada vagga**. La estructura hallada en la BD cuadra al 100% con ella, y
  el recuento por saṃyutta del Excel (81/30/25/25/10/15/22/12/14/12/25) coincide exacto.
- **Marcadores `§ N. Nombre.`, numerados POR VAGGA** (reinician) — un cuarto sistema de
  coordenadas. Gramática nueva en **`sn1_markers.py` (pyparsing**, documentada en
  `docs/grammar.md`). Dos variantes, sin las cuales se pierden **6 de los 271**:
  - **marcador «desnudo»**: el `§` se perdió en el OCR y queda `4. Nandano.` (S i 23, 52, 56, 73,
    124). Se discrimina del nº de párrafo (margen izquierdo) y del pada de gāthā (lleva `║`) por
    sangría ≥ 8, ausencia de `║`, longitud ≤ 48 y mayúscula inicial.
  - **rango con coma**: `§§ 4,5. Saṅgāme dve vuttāni.` (S i 82) — un encabezado, dos suttas. El
    bloque se parte por los **submarcadores** internos (`4.`/`5.` centrados a solas); sin partirlo
    ambos suttas comparten todo el texto y Gemini rechaza con razón (son dos batallas con
    desenlaces opuestos). Era el único REJECT de la tanda: 270/271 → 271/271.
  - **agrupación en vaggas**: dentro de un vagga el `§` crece estrictamente, así que un número que
    no crece abre vagga nuevo. Es la única regla fiable, porque el `§1` de arranque es justamente
    uno de los que el OCR puede haberse comido.
- **Alineación POSICIONAL** (Excel canónico ↔ marcadores en orden de lectura), no difusa, con dos
  comprobaciones cruzadas independientes: el nombre del marcador ≡ título CST en **231/271 (85%)**
  — el resto son los títulos variantes que Feer mismo advierte («los MSS no concuerdan»; imprime
  el de B) — y la página del marcador ≡ **`cst_p_page`** del concordance en **271/271 (100%)**.
- **XML VRI del Sagāthāvagga** (`romn/s0301m.mul.xml`): el nº de párrafo lo llevan `bodytext`
  **y `hangnum`** (223+48=271 — los suttas solo-verso usan `hangnum`) y el texto vive en los
  `gatha1/2/3/gathalast`. El índice de SN V (solo `bodytext`) se queda en 223.
- ⚠️ **Ojo con `cst_p_page`**: es `vol.pppp` (`1.0001` = vol I p. 1) pero guardado como DECIMAL, así
  que los ceros de cola se perdieron — `1.004` es la p. **40** y `1.01` la p. **100**. Hay que
  rellenar la fracción a 4 dígitos (`_pts_page`); leerla tal cual da 25 falsos desacuerdos.
- **Líneas calibradas: 201 corregidas → 271/271 exactas** (`calibrate_sn1_lines.py`). 162 filas no
  traían línea y solo 66 de las 266 con línea acertaban.
- **4 errores de PÁGINA corregidos** con doble evidencia independiente (marcador `§` en la BD *y*
  ancla `cst_p_page`, ambos contra el Excel, cuya página además contenía el marcador de otro
  sutta): **SN 4.3** p105→104, **4.5** p106→105, **6.8** p149→148, **11.10** p226→227.
- SN 3.1 (el viejo `HELMER_FIXED`, p70→68 corregida a mano) queda **confirmado por partida doble**:
  el marcador `§1 Daharo.` está en p68 L3 y el título CST casa.
- Fuentes: `sn1_markers.py`, `validador_sn1.py`, `reconcile_sn1.py`, `calibrate_sn1_lines.py`,
  `samyutta-vol-I-info.txt`. Los viejos `parse_sn_grammar.py` / `helmer_sn1_pilot.py` quedan
  SUPERADOS.

### SN II — Samyutta Nikaya vol 2 (S ii) — 257 filas / 286 suttas — CERRADO 🔒 257/257
- **Estado 2026-07-25: 257/257 CONFIRMADO** — 246 `VALIDADOR` + 11 `VALIDADOR_HUMANO`
  (el *antara-peyyālaṃ*, ver abajo).
  Antes: 255 filas todas `DB_VERIFIED` → PENDIENTE.
- **El front matter de Feer (`samyutta-vol-II-info.txt`) fija el lado PTS sin LLM**: 10 saṃyuttas
  (numerados **XII–XXI** en la notación corrida), **27 vaggas, 286 suttas**
  (93/11/39/20/13/43/22/21/12/12) y la página de arranque de cada uno. La estructura hallada en la
  BD cuadra al 100%. Feer explica ahí mismo las dos numeraciones (sección/saṃyutta/vagga/sutta vs
  **saṃyutta/sutta**, «XII. 25. 4») y que prefiere la segunda — que es la del `Sutta #` del Excel.
- **248 filas cubren los 286 suttas**: los grupos peyyāla van en **una sola fila de nombre
  colectivo** (`Jātisuttādidasakaṃ` = PTS 72–81, `Suvaṇṇanikkhasuttādiaṭṭhakaṃ` = 17.13–20,
  `Pitusuttādichakkaṃ` = 17.38–43, `Sikkhāsuttādipeyyālaekādasakaṃ` = 12.83–93), igual convención
  que en SN V. **No faltan filas** (un primer diagnóstico dijo «faltan 38» y era falso: eran los
  miembros de esos grupos).
- **Gramática nueva `sn2_markers.py` (pyparsing)** — marcador `N (M) Nombre` **sin puntos**, ajeno
  al `§ N.` de S i y al `N. (M)` de S iv–v. Detalle y las tres reglas no evidentes (el recuento lo
  manda el rango; la sangría mínima depende de la forma; un rango puede ser solo el encabezado de un
  grupo cuyos miembros se reimprimen) en `docs/grammar.md`.
- ⚠️ **21 `Sutta #` ERRÓNEOS corregidos** (`reid_sn2.py`). En SN 17 la numeración del Excel iba
  **desplazada +7** desde 17.14 (la fila que se llamaba `17.21` se titula *Chavi*, está en la p. 237
  y es el sutta **17.28** en PTS y en DPR/CST), y en SN 18 +8 en las dos últimas. Se detectó por la
  comprobación cruzada de nombres (82%, con los fallos agrupados en SN 17), **no por el LLM**: al
  emparejar por el `Sutta #` malo se comparaba un par PTS↔CST correcto entre sí pero ajeno a la
  fila, y Gemini aprobaba. Los 21 veredictos mal adjudicados se descartaron y se re-validaron con la
  identidad corregida (22/22 APPROVE); la concordancia de nombres subió a 85%.
  **Lección: sin una comprobación cruzada independiente de la clave de emparejamiento, un APPROVE
  no dice nada sobre la fila.** La identidad verdadera de una fila la dan `Sutta Name` + `PTS Page`
  (concuerdan entre sí y con las dos fuentes); el `Sutta #` es el campo que se corrompió.
- **7 filas con el VOLUMEN mal puesto** (`fix_sn2_vol_labels.py`): SN 22.153–159 estaban como
  «S ii» y son **S iii** (SN 22 = Khandha abre el vol. III, como dice Feer). Evidencia:
  `cst_p_page = 3.0183…3.0187` (vol 3, mismas páginas), los títulos CST casan uno a uno, S ii 183
  habla de *kappā* (Anamatagga) mientras S iii 183 trata de rūpaṃ/attā, y 152+7 = **159**, el total
  canónico de SN 22.
- **Líneas: 39 corregidas → 254/254 exactas**; y **14 páginas** corregidas con doble evidencia
  (marcador + ancla `cst_p_page` de acuerdo entre sí y contra el Excel): 12.14, 12.24, 12.25, 12.42,
  12.43, 12.55, 13.5, 13.11, 14.7, 14.8, 14.27, 14.31, 18.3, 21.2 (`calibrate_sn2_lines.py`).
- Fuentes: `sn2_markers.py`, `validador_sn2.py`, `reid_sn2.py`, `reconcile_sn2.py`,
  `calibrate_sn2_lines.py`, `fix_sn2_vol_labels.py`, `fix_sn2_antarapeyyala.py`,
  `samyutta-vol-II-info.txt`. `audit_sn2.py` queda SUPERADO.

### El *antara-peyyālaṃ* de SN 12 (S ii 130–133) — verificado contra el impreso

Dos filas venían con la forma del **CST**, no la de PTS. Se resolvió leyendo lo que PTS declara
(`fix_sn2_antarapeyyala.py`, decisión de Jorge 2026-07-25):

- **`12.74 «Dutiyasatthusuttādidasakaṃ»` BORRADA — no es un sutta en PTS.** El CST parte el sutta
  PTS 82 «Satthā» en `1. Satthusuttaṃ` (ítem jarāmaraṇa) + `2-11. Dutiyasatthusuttādidasakaṃ`
  (ítems jāti…saṅkhāra). PTS imprime todo como UN sutta y lo dice literalmente: tras el §1 escribe
  **`Suttanto eko`** («un solo sutta», S ii 130 L28) y sigue con `Sabbesam evam peyyālo` y los
  §§2–11 (S ii 131 L1–28). Su uddāna remata: «Satthā Sikkhā … **Appamādena dvādasāti**» = **doce**
  suttas, y «Pare te dvādasa honti, suttā dvattiṃsasatāni» = doce (o 132 contando por ítem). Sin
  referencia PTS propia, la fila no pertenece a una concordancia de PTS.
  > ⚠️ **No era una elisión** — el texto SÍ está en PTS; lo que no existe es la división en suttas.
  > Una nota anterior de este documento decía «PTS elide el grupo Dutiyasatthu entero» y era falsa
  > en las dos mitades. **Distinto del caso de SN V**, donde PTS sí numera los suttas
  > (`122--132. (2--12)`, `143--154. (1--12)`) y elide solo el *texto* con `vitthāretabbo`: ahí las
  > 8 filas siguen bien.
- **`12.75 «Sikkhāsuttādipeyyālaekādasakaṃ»` EXPANDIDA a 11 filas (12.83–12.93).** Aquí el CST
  agrupa pero **PTS numera**: `83 (2) Sikkhā`, `84 (3) Yogo`, … `93 (12) Appamādo`, cada uno con su
  marcador (a diferencia de 12.72, 17.13 o 17.38, donde PTS sí imprime rango). Las 11 llevan su
  página y línea reales.
- **Las 11 son `VALIDADOR_HUMANO` por evidencia MECÁNICA, no por LLM**: el nº de ítem del grupo CST
  **es** la posición `(M)` del marcador PTS, y la palabra clave del marcador aparece **literal** en
  su ítem (11/11 verificado: sikkhā, yogo, chando, ussoḷhī, appaṭivāni, ātappa, viriya, sātacca,
  sati, sampajañña, appamāda). El texto PTS son 4 tokens (`ºyogo karaṇīyo ║ (1-11)`), así que
  Gemini no tiene qué cotejar y sus 7 REJECT son falsos negativos por elisión. El emparejamiento
  lo hace `build_cst_group_items` + `CST_GROUP` en `validador_sn2.py`, **fijando el grupo por
  título**: hay varios grupos con los mismos nºs de ítem y buscarlo por parecido de texto elige el
  equivocado (se comprobó: daba `Dutiyasatthu…` y `Jāti…`).

### SN IV — Samyutta Nikaya vol 4 (S iv) — 344 suttas — CERRADO 🔒
- Excel (as of 2026-07-24 reconciliation): `HELMER_APPROVED` (94) + `HELMER_REJECT` (12) +
  `DB_VERIFIED` (238 peyyāla). See "UPDATE 2026-07-24" at top.
- DeepSeek PTS↔CST: 94/106 APPROVE (89%)
- 12 REJECT: false positives (Feer abbreviation / orthographic; names match CST). Review SN 36.26.
- 238 PEYYALA: no individual markers (abbreviated suttas)
- Marker format: `N (M) Name` or `N. (M) Name`
- CST file: s4m.xml (344 suttas, perfect match)
- Method: exact gid match on stated page → sutta-bounded text → DeepSeek
- Source files: `helmer_sn4_pilot20.py`, `helmer_sn4_v3.py`, cached in `helmer_ptscst_cache.json`

### SN V — Samyutta Nikaya vol 5 (S v) — 610 suttas — CERRADO 🔒 610/610
- **Estado 2026-07-25 (3ª pasada): 610/610 CONFIRMADO.** 571 `VALIDADOR` (concordancia VRI ∧
  Gemini APPROVE) + 39 `VALIDADOR_HUMANO` (18 desacuerdos arbitrados antes + las 21 peyyāla
  elididas, dispuestas en bloque por Jorge el 2026-07-25 vía
  `reconcile_sn5.py --humano firmas_sn5_peyyala.json`).
- Alineado por el **pipeline VRI por concordancia** (definitivo): Excel(DPR) → `massive.tsv`
  (`cst_paranum`) → XML VRI (`/tmp/tipitaka-xml/romn/s0305m.mul.xml`) → texto CST exacto; lado
  PTS por marcadores DB (libro 16). Validador Modelo B con `concordant=True` (concordancia
  exacta ∧ Gemini; el gate de cobertura sobra). Drivers: `validador_sn5_vri.py` + `validador_sn5.py`
  (parser de marcadores: `(M)`, rangos `103--108. (1--6)`, grupo profundo `89--98.1--10.`,
  centrado simple `5. Bhikkhu.`, y fallback a página). Reconciliación: `reconcile_sn5.py`.
  Los viejos `helmer_sn5_*.py` quedan SUPERADOS.
- **580 → 589: 9 de las 30 "peyyāla" NO lo eran** — eran fallos del resolvedor PTS, ahora
  corregidos en `validador_sn5.py` (auditados con un diff de texto PTS viejo↔nuevo sobre las 602
  entradas, sin gastar API, para garantizar que ninguna de las ya CONFIRMADO se degradaba):
  1. **Marcador perdido por OCR** — `4O. (10) Nandiya.` en S v 397 lleva letra `O` por cero, así
     que el parser no veía la línea y caía al texto de página entera (`_fix_ocr_num`; es el único
     caso del volumen). SN 55.40 ✅.
  2. **Off-by-one de PÁGINA** — `pts_for` solo miraba la página declarada; el marcador está a
     veces en la siguiente (ahora busca ±1). Recupera 55.56, 56.22, 46.36, 51.19, 54.16, 48.72/73,
     51.34, 56.102/104…
  3. **`_stem` no quitaba `-suttaṃ`** — colapsaba las consonantes dobles ANTES de recortar el
     sufijo, así que `suttaṃ`→`sutam` ya no casaba con el patrón. Corregido el orden.
  4. **Nombre laxo vs nº corrido** — la contención de nombres NO distingue los pares
     paṭhama/dutiya de las series peyyāla (el marcador PTS los llama igual, `Pathavī1./Pathavī2.`),
     así que el nombre solo se antepone al nº cuando la coincidencia es fuerte, o cuando es
     inequívoca y el título CST no lleva ordinal (`name!`: recupera 45.112 `Nivaraṇāni`, que es el
     177 en PTS y el 178 en DPR). Empate → marcador de más arriba (antes ganaba el de más abajo,
     que se llevaba el sutta siguiente).
  5. **Fragmento sin cuerpo** — dos marcadores de rango consecutivos dejaban un "sutta" de 1 token;
     `MIN_PTS_TOKENS=3` lo descarta y sigue la cadena (ojo: los peyyāla PTS legítimos tienen 4
     tokens, un umbral alto degrada decenas de filas).
- **21 PENDIENTE = clase peyyāla** (concordancia VRI exacta, texto ELIDIDO en PTS y/o CST → sin
  texto que Gemini pueda cotejar; su REJECT es falso-negativo por elisión, no desalineación).
  Desglose: 13 `DB_VERIFIED` (grupos `Esanādi/Oghādi/Tathāgatādi/Balādi/Pācīnādi/Chedanādi`,
  donde PTS imprime solo el uddāna) + 8 `REF_ERROR_DPR` **verificados: NO son error de DPR** —
  son los grupos de repetición "Puna-" (46.130/131/143/153/165/175, 49.13, 50.13), elididos
  SIMÉTRICAMENTE en ambas ediciones con `...rāgavasena vitthāretabbo` (solo uddāna; análogo
  inverso del `PTS_CROSSREF_SN`). Disposición PENDIENTE de decisión de Jorge (valor nuevo
  `VALIDADOR_PEYYALA` vs `VALIDADOR_HUMANO` en bloque) — dejado abierto a propósito.
  Excepción dentro de las 21: **45.113 Upādānakkhandha** no es peyyāla sino ambigüedad de nombre
  (el marcador PTS `Khandā.` gid 178 es el correcto, pero `Upādānam.` gid 173 es prefijo del
  título CST `Upādānakkhandhasuttaṃ` y gana; ninguna regla de nombre lo desempata) → arbitraje.
- ⚠️ **6 filas CONFIRMADO con evidencia superada** (`Validation=VALIDADOR` en el Excel pero el
  veredicto vigente en `validador_sn5_vri.json` es REJECT): **45.71, 50.3, 52.18, 55.67, 55.69,
  55.71**. `reconcile_sn5.py` no degrada por diseño (protege la procedencia), así que siguen
  marcadas. 45.71 y 50.3 rechazan con el texto MEJOR alineado de esta pasada (su APPROVE previo
  se apoyaba en el texto de página entera); 52.18/55.67/55.69/55.71 ya rechazaban antes. Decisión
  de Jorge: degradar a PENDIENTE (→ 583/610 real) o arbitrar a mano.

- **Líneas calibradas (2026-07-25)** — `calibrate_sn5_lines.py`. La línea de `PTS Ref`
  (`S v <pág>,<línea>`) es la del **marcador centrado** del sutta, y el dato del Excel venía
  MEZCLADO: solo 75/546 coincidían; el resto se agolpaba en 2–8 sobre páginas de ~29 líneas
  (distribución imposible para posiciones reales — no eran líneas, y 144 filas no traían ninguna).
  Recalculadas contra el texto de la BD (libro 16) reusando la cadena de resolución del pipeline
  VRI: **471 corregidas → 546/546 exactas**. Auditoría independiente antes de escribir: el nombre
  del *Excel* contra el nombre del *marcador* (señal que el resolvedor no usó, pues casa por título
  CST) → 441/546 casan; las 105 que no son variantes abreviadas de Feer (`Araham1.` =
  `Paṭhamārahanta`, `Bodhanā.` = `Bodhāya`) donde el marcador sí concuerda con el título CST.
- **2 residuos deliberados en las líneas** (no se tocan, a arbitraje contra el impreso):
  - **45 filas con la página en disputa** — el marcador está en la página vecina, no en la que
    declara el Excel. Reescribir la *página* es una afirmación mayor que la línea y queda fuera del
    alcance de la calibración; `calibrate_sn5_lines.py` las lista.
  - **19 sin marcador resoluble** (45.75/76, 46.58, 46.87–92, 48.74, 49.2/5, 50.2/5/6,
    56.99–101, 56.109): grupos peyyāla sin marcador propio → línea intacta.
- ⚠️ **6 filas CONFIRMADO con evidencia superada** (`VALIDADOR` en el Excel pero el veredicto
  vigente en `validador_sn5_vri.json` es REJECT): **45.71, 50.3, 52.18, 55.67, 55.69, 55.71**.
  `reconcile_sn5.py` no degrada por diseño (protege la procedencia). Jorge decidió (2026-07-25)
  **dejarlas y revisarlas a mano** contra el impreso/CST — cola de arbitraje abierta, no un
  pendiente del pipeline. Nótese que 45.71 y 50.3 también aparecen en las 45 con página en disputa.

---

## PENDING

### SN III — Samyutta Nikaya vol 3 (S iii) — 332 filas — CERRADO 🔒 332/332
- **Estado 2026-07-25 (5ª pasada): 332/332 CONFIRMADO** (316 `VALIDADOR` + 16 `VALIDADOR_HUMANO`). Antes: 326 filas
  `DB_VERIFIED` (+7 que llegaron de S ii al corregir su volumen) → todo PENDIENTE.
- **Front matter de Feer (`samyutta-vol-III-info.txt`)**: 13 saṃyuttas **XXII–XXXIV**, y la página
  de arranque de cada uno **cuadra al 100%**. Feer distingue **títulos** de **suttantas** (Nāga son
  14 títulos = 50 suttantas; Gandhabba 10 = 112), y el nº de suttantas cuadra en **12 de 13**:
  158/46/·/10/10/10/10/50/46/112/57/55/55.
  - El 13º, **Diṭṭhi (XXIV)**, lo explica Feer mismo: cuenta 114 (18 + 4 gamana × 26) pero
    **confiesa haber omitido del texto los primeros 18 de la 2ª gamana**, así que el volumen imprime
    **96**; y de esos 96 solo **72 llevan marcador**, porque los 72–95 de la 4ª gamana van elididos
    (PTS salta de `71 (1)` a `96 (26)`). Total impreso del volumen: **691 marcadores / 715 suttantas
    reckoned**, y el 733 de Feer = 715 + los 18 que él omitió. Todo conciliado.
- **Gramática nueva `sn3_markers.py` (pyparsing)** — misma familia que S ii (`N (M) Nombre` sin
  puntos) más tres formas propias: **nombre entre paréntesis** (`11 (Samāpatti-ṭhiti)`), **rango con
  posición-rango** (`140-142 (5-7) Dukkhena (1-3)`) y **prefijo de subdivisión** (`(3)11-15
  Anabhisamayā (1-5)`), que es el *gamana* en el Diṭṭhi y el **nº de título** en el Vacchagotta
  (11 títulos × 5 khandhas = 55 suttantas). Ese prefijo abre saṃyutta solo si vale 1 — `(27)1-4`
  (SN 34) es una combinación interna. La sangría mínima de la forma sin paréntesis baja a **12**
  (el `1 Samādhi-samāpatti` que abre SN 34 está a 14; el umbral 20 de S ii se lo comía), a cambio
  de descartar las cabeceras de uddāna y de *gamana* en versal.
- ⚠️ **La clave `(saṃyutta, nº)` NO sirve en este volumen** — y aquí el desajuste es al revés que en
  S ii: **el Excel y el concordance concuerdan entre sí** y es la numeración PTS la que difiere,
  porque PTS imprime **158** suttas en el Khandha-saṃyutta y el CST/DPR cuenta **159**, con lo que
  se desfasa +1 en la cola. El lado PTS se resuelve por **nombre del marcador sobre la página que
  ancla `cst_p_page`** (`resolve_pts`): las 333 filas resolvieron por nombre (234) o por clave con
  el ancla de acuerdo (99), **sin fallbacks**.
- **Pares `Dutiya-`**: Feer no escribe el ordinal — imprime dos veces el mismo nombre —, así que hay
  que tomar el **k-ésimo homónimo en orden de lectura** o se coteja el sutta contiguo. Era la causa
  de la mayoría de los REJECT del primer pase (22.52, 22.158, 29.4, 29.5…).
- **Líneas**: 75 + 35 corregidas → **316/316 exactas**; **7 páginas** con doble evidencia
  (22.15, 22.42, 22.52, 22.114, 22.121, 23.25, 28.2).
#### Cómo se resolvieron las 24 pendientes (2ª pasada)

Tres causas, ninguna resoluble por el LLM; el cruce de nombres subió de **63% a 88%**.

1. **`massive.tsv` colapsa los rangos** — el TSV da un solo `cst_paranum` por grupo (el del primer
   miembro), así que los 17 miembros de `SN24.19-35` se cotejaban contra el sutta 1 del saṃyutta.
   **`massive.tsv` NO se modifica**: el arreglo va en el lector, `massive_reader.py`, que expande
   `para + (k−a)` **con compuerta** — solo si TODOS los paranum resultantes existen en el XML, que
   es lo que ocurre cuando el destino cae en el bloque elidido del CST (`225-240`, `251-274`,
   `277-300`). Si algún paranum no existe se deja colapsado: nunca se inventa una referencia.
2. **El Diṭṭhi-saṃyutta (SN 24) no sigue ninguna numeración** — sus 32 filas van `24.1`…`24.32`, un
   índice corrido que no es DPR (`24.21 «Rūpīattā»` es DPR `SN24.37`) ni PTS. Pero las tres fuentes
   listan **los mismos 32 suttas EXPLÍCITOS** (los que no caen en bloque elidido) y en el mismo
   orden, así que se alinean por posición (`ditthi_pairs`): **32/32 con el nombre coincidiendo**.
   Los bloques elididos quedan fuera en ambas ediciones y las dos lo dicen — el CST con
   `(Purimavagge viya aṭṭhārasa veyyākaraṇāni vitthāretabbānī)`, PTS con `20--35 (2--17)` y el salto
   de `71 (1)` a `96 (26)`.
3. **PTS agrupa donde el CST numera** — en S iii 179 PTS imprime TRES suttas
   (`146-148 Kulaputtena dukkhā (1)(2)(3)`) donde el CST tiene CUATRO, y de ahí el último vagga
   corre con **PTS = CST − 1**. `calibrate_offsets` prueba desplazamientos pequeños y acepta el
   tramo **solo si con él casan TODOS los nombres** hasta el final del saṃyutta (en el Khandha,
   10/10). Nada se adivina.

- Efecto colateral controlado: la lectura nueva cambia el texto CST bajo filas ya validadas, así que
  se **re-validaron** las afectadas en vez de heredar el veredicto (58 + 33 en S iii, 20 en S v).
  En S v el resultado se sostiene (610/610): 8 de los 9 rechazos nuevos ya eran `VALIDADOR_HUMANO`
  de la clase peyyāla, y **50.3** se reclasificó a `VALIDADOR_HUMANO` junto a sus hermanas 48.74,
  49.5, 50.4 y 53.2 (PTS imprime solo el uddāna del grupo).
- **16 `VALIDADOR_HUMANO`** — peyyāla donde una edición agrupa lo que la otra numera, con el par ya
  identificado; se firman por **prueba mecánica**, no por LLM: las palabras clave del nombre
  aparecen literalmente en el texto de su contraparte (16/17 verificado).
- **El Jhāna-saṃyutta, resuelto por TÍTULO.** Sus 10 series van colapsadas en el CST y el
  concordance mandaba varias filas al bloque de la serie «ṭhiti-». Pero el **título del subhead
  nombra la serie** y es casi idéntico al `Sutta Name` del Excel
  (`Kallitamūlakaārammaṇasuttādichakkaṃ` = `n=696-701`), así que `build_cst_by_title` lo resuelve.
  La regla se aplica **solo si el título del paranum no tiene NADA que ver** (score 0) **y** el
  título candidato coincide **exactamente** (score 100): con un umbral laxo se disparaba en 43 filas
  cuyo paranum era correcto y empeoraba el resultado.
- **1 PENDIENTE — `30.5 «Aṇḍajadānūpakārasuttadasakaṃ»`**: el título CST coincide exacto y el lado
  PTS es su marcador de rango («Dānupakārā»), pero la palabra clave `aṇḍaja` no aparece literalmente
  en el bloque elidido de PTS, así que no supera la prueba mecánica. Queda a criterio humano.
- **Líneas: 317/317 exactas**; ninguna fila queda sin nº de línea.

#### Tres fallos de resolución corregidos en la 3ª pasada

Los detectó revisar «¿está terminado?» fila a fila, no el LLM:

- **Nombres compuestos `X-mūlaka-Y`** (Jhāna-saṃyutta): el marcador correcto es el **compuesto** de
  PTS («Kallita -- ārammaṇa», «Gocara-Abhinīhāra»), no el simple. Buscar por afinidad suelta elegía
  «Kallita» o «Gocara», que son otros suttas (`_MULAKA` en `resolve_pts`).
- **La contención de nombres se medía tras recortar la terminación de caso**, con lo que «Saññā»
  quedaba en «san» —por debajo del mínimo— y su compuesto «Rūpasaññā» casaba con «Rūpa» de la página
  vecina (S iii 25.6). Ahora se mide antes del recorte.
- ⚠️ **Una corrección de página previa era ERRÓNEA**: `22.15 «Yadanicca»` se había pasado de p22 a
  p21 apoyándose en una resolución equivocada. El sutta arranca en «15 (4) Yad anicca (1)», **S iii
  22 L1**; revertida. Las otras seis correcciones de página de S iii se re-verificaron y son buenas.
- Fuentes: `sn3_markers.py`, `validador_sn3.py`, `reid_sn3.py`, `reconcile_sn3.py`,
  `calibrate_sn3_lines.py`, `samyutta-vol-III-info.txt`. `parse_sn_grammar.py` queda SUPERADO.

### AN — Anguttara Nikaya — 1,738 filas — **1447/1738 (83,3 %)** ⏳
- **A ii (Catukka) 303/303 — CERRADO 🔒** · **A iv 298/298 — CERRADO 🔒** (2026-07-25).
- **A iii 452/457** y **A v 243/245**: las 7 que faltan tienen el motivo en `Detail` y son de dato:
  `5.270`/`5.271` (PTS abrevia la segunda tanda de jhānas), `5.282` (el impreso escribe
  `Sāṭiyagāhāpako` y el Excel `Sāṭikagāhāpaka`), **`5.291`** (PTS **no imprime** ese miembro: su
  lista salta de `sāmaṇerā` a `upāsikā`), `5.300`, y `11.502-981`/`11.982-1151` (el Excel numera la
  cola del Ekādasaka hasta 1151 y el CST acaba en 671).
- A i 151/435: sólo el Tika. **Eka y Duka siguen sin abordar a propósito** — allí el CST no da
  nombre por sutta y las tres ediciones cuentan unidades distintas; antes hay que tener el mapa de
  divisiones y fusiones (`detector_uddana.py`), y el suyo aún no es fiable (ver aviso arriba).

#### Lo que enseñaron los cuatro barridos (A ii → A v)

- **La premisa «`Sutta #` ≡ paranum del VRI» NO es universal.** Se cumple sin excepción en las
  1099 filas CONFIRMADO del cuerpo de A ii–A v, y **se rompe en las colas**: la del Aṭṭhaka va
  **+1** desde el grupo *Upāsikā* (`<p n="91-116">` del CST contra `8.91-117` del Excel), y las del
  Ekādasaka y el Pañcaka **sobrepasan** el último paranum del CST (1151 contra 671; 1152 contra
  1151). Antes de escribir una `VRI Ref` aritmética en una cola, **comprobar los límites del grupo
  del CST**.
- **La prueba mecánica es asimétrica a propósito**: el lado CST no necesita prueba léxica (su ancla
  es el paranum, la clave canónica), el lado PTS sí (el impreso no numera esos suttas).
- **La sonda tiene que ser la RARA, no la larga.** En el Navaka las nueve filas casaban con el
  mismo `sammappadhāna` en posiciones sucesivas: monótono y vacío. Y hace falta un **tope de salto**
  (`MAX_SALTO`), porque una fila cuyo término no está en el impreso casa lejos y se lleva por
  delante a todas las siguientes.
- **Hay elisión SIMÉTRICA**: en el Navaka (`9.74-81`, `9.84-91`) ninguna de las dos ediciones
  imprime los suttas — las dos remiten al vagga anterior. Lo único que identifica la fila es que
  los límites del rango coincidan en las tres fuentes.
- **Tres defectos de nombre desmentidos por la estructura**, todos del mismo tipo (una serie
  canónica que el Excel altera): `Mada`/`Pamāda` en A ii y en A iii, y `Nīvaraṇa`/`Kāmaguṇa`
  invertidos en `9.74`/`9.75` (el vagga de referencia y la serie paralela del *iddhipāda* los dan
  en el orden contrario).

### KN — Khuddaka Nikaya — 2,360 entries ⏳
- 254 off-by-one corrections applied
- 624 vol/page fields repaired
- Line numbers added for 93.7% of canon entries
- No Helmer validation yet
- Thag 100%, Ud 100%, Sn 100% marker coverage

---

## METHOD: cómo validar lo que queda (AN/KN) — pipeline VRI + validador

> **Histórico:** lo que había aquí describía el pase **DeepSeek "Helmer"** (RETIRADO: no
> determinista a `temperature=0`) y un mapeo CST `frontera[saṃyutta] + (inner-1)` que se demostró
> **roto** (dio 8% de APPROVE en SN V). No usar ninguno de los dos. El método vigente es el que
> cerró SN V 610/610.

### Flujo (probado en SN V, directamente portable a AN/KN)
1. **Alinear por CONCORDANCIA, no por contenido ni por número.** El `Sutta #` del Excel está en
   notación **DPR**; `massive.tsv` (raíz del repo) enlaza `dpr_code` → `cst_paranum` + `cst_sutta`.
2. **Texto CST** desde el **XML VRI** (`/tmp/tipitaka-xml/romn/*.mul.xml`), por `<p rend="bodytext"
   n="N">` con `N = cst_paranum` (los `n` pueden ser rangos, `"42-47"`).
3. **Texto PTS** desde la BD (`pages`, `edition='mula'`) localizando el **marcador centrado** del
   sutta. Prioridad que funciona: **nombre fuerte** (idéntico/prefijo del título CST) → **nº
   corrido** (el único que separa los pares paṭhama/dutiya de las series peyyāla) → **nombre laxo
   inequívoco** → contenido → página. Buscar siempre la página declarada **±1**.
4. **Validar** con `validador.validate_pair(..., concordant=True)`: con alineación exacta,
   CONFIRMADO = concordancia ∧ Gemini APPROVE (el gate de cobertura sobra).
5. **Volcar** con un reconciliador que NO degrade la procedencia humana y haga backup del Excel.

### Antes de gastar API: auditar el resolvedor con un diff de texto
Cualquier cambio en el resolvedor PTS se audita **sin llamadas a la API** comparando el texto que
devuelve el resolvedor viejo contra el nuevo, entrada por entrada. Así se ve de inmediato si una
"mejora" degrada filas ya CONFIRMADO — así se encontraron los 5 fallos que subieron SN V de 580 a
610. Umbrales: cuidado con los mínimos de longitud, los peyyāla PTS legítimos tienen 4 tokens.

### Líneas de `PTS Ref`
La línea es la del **marcador centrado** del sutta en la página. Los valores del Excel vienen
mezclados y en su mayoría no son líneas (ver SN V): recalcular con el mismo resolvedor
(`calibrate_sn5_lines.py` como plantilla) y **no reescribir la página**, solo la línea.

### Key files:
- `PTS_Reference_Complete_Canon.xlsx` — master output (3 hojas; `Estado` = rollup binario)
- `validador.py` — el juez (Modelo B), nikāya-agnóstico
- `validador_sn5.py` / `validador_sn5_vri.py` / `reconcile_sn5.py` / `calibrate_sn5_lines.py`
  — driver SN V completo, la plantilla a copiar para AN/KN
- `massive.tsv` — concordancia dpd/cst/dpr/sc/bjt con `cst_paranum` y páginas VRI
- `/tmp/tipitaka-xml/romn/*.mul.xml` — texto CST (VRI)
- `src/data/tipitaka.sqlite` — edición PTS (`edition='mula'`)
- `/dev/shm/dpd.db` — DPD
- `helmer_*.py`, `helmer_ptscst_cache.json` — **legado del pase DeepSeek retirado**

Herramientas nuevas (2026-07-25), todas sin API:
- `an_peyyala.py` — **quinto régimen**: tramos donde una edición elide lo que la otra numera.
  Expande los `<p n="a-b">` del CST por paranum y prueba el término distintivo literal y en orden
- `validador_an_peyyala.py` — barrido de las colas peyyāla de A ii–A v (`--dry` no toca nada)
- `reconcile_an2_cierre.py` — el volcado de A ii, con el porqué de cada fila en `Detail`
- `uddana.py` — gramática **pyparsing** de la estrofa + dvandvas con el deconstructor de DPD
- `detector_uddana.py` — mapa de divisiones y fusiones PTS↔CST, vagga por vagga, en AN entero
- `pali_norm.py` — normalización interna a la convención VRI (reglas medidas sobre los dos corpus)
- `piloto_hash_vagga.py` — estrategia de tres capas, con verdad-terreno sobre A ii
- `audit_tiempo.py` — presupuesto por operación (`abrir` / `paso` / `estado` / `cerrar` / `informe`)

### Pitfalls:
- La numeración SN resetea por saṃyutta — usar el nº corrido (gid), no la posición en la vagga
- Peyyāla: suttas sin marcador propio, con el texto ELIDIDO en PTS y/o CST. El REJECT del LLM ahí
  es un falso negativo por elisión, no una desalineación → arbitraje, no PENDIENTE automático
- Los ficheros CST traen más saṃyuttas que el Excel (s5m.xml llega a SN 112)
- SN I usa marcadores `§ N.`; SN II–V, `N (M) Nombre` (y rangos, y centrados sin paréntesis)
- Feer abrevia más que el CST — contar con ~10% de REJECT falsos
- **El OCR de la BD mete letras por dígitos en los marcadores** (`4O. (10)` en S v 397): un
  marcador "ausente" puede ser esto, no una laguna del texto
- El nombre del marcador PTS puede ser una variante de Feer (`Araham1.` = `Paṭhamārahanta`): casar
  por nombre contra el título CST, y usar el nombre del Excel solo como señal de auditoría

---

## RULES (from README)
- ⚠️ NADA se cierra sin el **validador** (Modelo B: gate local ∧ Gemini, PTS↔CST). El pase
  DeepSeek "Helmer" está RETIRADO (no fiable); sus marcas `HELMER_*` son CONFIRMADO provisional
- ⚠️ La única fuente de verdad es `tipitaka.sqlite` (edición 'mula')
- ⚠️ NO HAY HOMOGENEIDAD entre Nikayas — cada uno requiere su propio parser

---

## PLAN DE REMEDIACIÓN Y CIERRE (2026-07-25)

### El defecto que lo motiva

La resolución del lado PTS se hace **fila a fila y no es inyectiva**: dos filas del Excel pueden
acabar en el mismo marcador, con lo que una de ellas se valida contra el locus de su vecino. El
validador no puede detectarlo — compara un par PTS↔CST correcto *entre sí* pero ajeno a la fila —
y por eso pasó los controles. Es la misma familia de error que los 21 `Sutta #` desplazados de S ii.

Alcance medido (marcadores compartidos / filas implicadas):

| Volumen | Cómo resuelve el lado PTS | Estado |
|---|---|---|
| **S i** | posicional (1:1 por construcción) | **limpio** — 0 |
| **S ii** | clave exacta `(saṃyutta, nº corrido)` | **limpio** — 0 |
| **S iii** | por nombre sobre la página del ancla | **16 marcadores / 38 filas**; 22 filas sin marcador propio pudiendo tenerlo |
| **S v** | nombre → nº → nombre laxo, con fallbacks | **16 marcadores / 36 filas** |
| **S iv** | — | sin hacer; heredaría el defecto |

### Estado de ejecución (2026-07-25)

- **Fase 0 — HECHA.** `audit_injectivity.py`. Línea base: S i 0, S ii 0, S iii 12, S v 12 (total 24).
  **Tras la fase 1: 0 en los cuatro volúmenes.**
- **Fase 1 — HECHA.** `align_rows.py` (alineamiento monótono con capacidad por DP, probado en
  aislamiento) enchufado a S iii y S v. Antes hubo que arreglar un defecto anterior que lo impedía:
  > **`build_pts_suttas` perdía 4 marcadores.** Indexaba por `(saṃyutta, nº)` y en el Jhāna-saṃyutta
  > las claves de *gamana* (`(27)1-4`) machacaban los números 1–4 reales, así que
  > `1 Samādhi-samāpatti` (S iii 263), `2 Ṭhiti`, `3 Vuṭṭhāna` y `4 Kallavā` nunca llegaban al
  > resolvedor — la razón de fondo de que `34.1` apuntara a S iii 273 desde el primer pase. Ahora
  > cada registro lleva su posición de lectura (`ord`) como identidad única, el índice por
  > `(saṃyutta, nº)` da preferencia al registro sin gamana y `pts_records()` expone el inventario
  > completo. SN 34 pasa a mapear 1:1 (34.1→`Samādhi-samāpatti` … 34.10→`Sappāyam`).
  En S v la asignación va sobre **todo el volumen**, no por saṃyutta: por partes, dos filas de
  saṃyuttas contiguos reclamaban el mismo marcador en la frontera (S v 305: 52.21 y 53.1).
- **Fase 2 — HECHA en S iii; S v se deja como está (decisión de Jorge).**
  - **S iii**: 33 pares cambiaron, se re-validaron (30 APPROVE) y se volcaron; líneas recalibradas
    con la misma asignación → **316/316 exactas**. Sigue en **332/333**.
- **Fase 2bis (2026-07-25) — el alineador no devolvía el óptimo.** Al mirar S iii 30.5 salió a la luz
  que `main()` de `validador_sn3.py` seguía llamando al resolvedor fila a fila (la conexión de
  `assign_volume` se había perdido en un `git checkout`), y al reconectarlo aparecieron **24 pares
  distintos**, 21 APPROVE. Pero el tramo 22.146-149 seguía mal, y la causa era un **defecto de
  `align_rows.assign`**: el estado «fila saltada» era un escalar sin memoria de la posición del
  marcador, así que sólo se admitía cuando superaba el máximo global — y se perdía el óptimo justo
  donde importa, en una fila del CST que PTS **no imprime** en mitad de una serie. Reescrito: el
  salto conserva el estado `(marcador, racha)`, que además es lo correcto filológicamente (si a un
  marcador de rango le falta uno de los suttas del CST, sus vecinos siguen cayendo en él). Ahora es
  **óptimo demostrado**: 400/400 casos aleatorios contra fuerza bruta, con monotonía y capacidad.
  Se añadió también al score el **solapamiento léxico CST↔marcador**, única evidencia que discrimina
  cuando PTS numera una serie `(1)(2)(3)` bajo un título común.
  - **Efecto**: en S v, **ninguna** asignación cambia; en S iii cambian sólo `22.148` y `22.149`.
  - **Hallazgo**: PTS **no imprime** `22.148 Dukkhānupassī`. Los tres marcadores «Kulaputtena dukkhā
    (1)(2)(3)» de S iii 179-180 rezan *nibbidā-bahulaṃ* (146), *aniccānupassī* (147) y
    *anattānupassī* (148); el dukkhānupassī del CST cae dentro del «pa» de elisión al final del
    nº 147. Es la fusión 4→3 que ya detectaba `calibrate_offsets` (de ahí `PTS = CST − 1` a partir
    de 150), pero hasta ahora se le quitaba el marcador al sutta equivocado (149 en vez de 148).
  - **`22.148 Dukkhānupassī`: fila BORRADA (arbitraje de Jorge, 2026-07-25).** PTS **no numera**
    ese sutta —su cuenta corre 146, 147, 148 para tres, cuyos cuerpos rezan *nibbidā-bahulaṃ*,
    *aniccānupassī* y *anattānupassī*— y **el uddāna nunca cuenta cuatro**: PTS y CST transmiten el
    MISMO verso, «…kulaputtena **dve** dukāti» (dos), con la nota de Feer *«So all the MSS.; it
    ought to be tayo»*; él enmienda a tres e imprime tres, y el CST imprime cuatro. La cuenta de
    suttas *Kulaputtena* es inestable en la tradición (2 transmitido / 3 Feer / 4 CST). Es por tanto
    una división **sólo del CST**, sin referencia PTS: mismo criterio que zanjó `12.74` («Suttanto
    eko», S ii 130). En contra jugaba el `║ pa ║` al final del nº147, que cae donde va el
    *dukkhānupassī* en la serie *anicca→dukkha→anatta*: PTS conoce la continuación y la abrevia,
    pero no la numera. **Canon: 6098 filas** (la columna `#` se renumeró).

### SN 34 (Jhāna-saṃyutta): NO HAY HOMOGENEIDAD NI DENTRO DE UN SAṂYUTTA

Corregido 2026-07-25 tras la observación de Jorge («deberías crear dos analizadores»). SN 34 se
imprime bajo **dos convenciones opuestas** y una sola regla se equivocaba en una de ellas:

| parte | CST | marcador PTS | qué nombra la abreviatura |
|---|---|---|---|
| **1-19** individuales | `3. Samādhimūlakavuṭṭhānasuttaṃ` | «Vuṭṭhāna» | el **segundo** elemento (la raíz es constante y se da por sabida) |
| **20-55** grupos | `46-49. Gocaramūlakaabhinīhārasuttādicatukkaṃ` | «Gocara-Abhinīhāra» / «Ārammaṇa **--**» | el **par**, o sólo la **raíz** si va truncado con guiones |

- La regla única premiaba el *segundo* elemento también en el tramo de grupos, así que **cada fila
  se emparejaba con el grupo siguiente**: 34.22 (`35-40`) caía en el marcador nº41, 34.23 (`41-45`)
  en el nº47, 34.24 (`46-49`) en el nº50 y 34.25 (`50-52`) en el nº51. **Tres de las cuatro estaban
  ya CONFIRMADO** y una firmada a mano: el validador no puede verlo, porque el par PTS↔CST que
  recibe es coherente consigo mismo, y aquí además todo el saṃyutta repite la misma fórmula con los
  términos permutados, así que Gemini tampoco distingue.
- **Causa raíz de la invisibilidad**: `sn3_markers._clean` borraba los guiones, y el `--` es
  justamente lo que separa los dos regímenes. Ahora el registro conserva el nombre en bruto
  (`rec['raw']`).
- **Solución**: `sn34_series.py` — gramática `pyparsing` de la forma del nombre
  (`pair` / `trunc` / `plain`) y **dos analizadores**, `score_individual` y `score_grouped`, cada uno
  aplicado a su parte. El desempate definitivo del régimen de grupos **no es el nombre sino el
  número**: el subhead del CST declara su rango («46-49.») y el marcador PTS su nº corrido (46) —
  misma numeración en ambas ediciones, así que la cabeza del rango *debe* ser el nº del marcador.
- **Verificación independiente**: de las 16 firmas humanas de S iii, **15 coinciden ahora con la
  alineación calculada**, incluida `34.23`, que Jorge había firmado bien y el resolvedor tenía mal.
  La única discrepancia que queda, `23.24` (firma p198,25 vs marcador p199,16), es una **disputa de
  página**, que la calibración de líneas no toca por diseño.
  - Líneas recalibradas: **318/324 exactas (98%)**, 6 corregidas. Auditoría de inyectividad: **hueco
    0** en los cuatro volúmenes contrastados.
  - **S v**: 69 pares cambiaron y las asignaciones nuevas son **mejores** (`45.12 Dutiyavihāra`→
    `Vihāra2.`, `45.28 Samādhi`→`Samādhi.`, con los textos coincidiendo), pero al ceñirse el texto
    al marcador **cae la cobertura del gate local**: 72 desacuerdos son `gate=REJECT /
    gemini=APPROVE` con cobertura mediana 0.40 frente al umbral 0.55, calibrado sobre textos laxos.
    > **Decisión (Jorge, 2026-07-25): no reabrir.** Si el par ya está verificado y Gemini aprueba,
    > no tiene sentido re-revisarlo para llegar al mismo resultado. S v se queda en 610/610 y el
    > Excel no se toca; `reconcile_sn5.py --dry` confirma que no habría degradación (538 filas
    > reescribirían el mismo valor, 40 protegidas). El umbral del gate **no se recalibra**: se deja
    > documentado que en régimen de texto ceñido su cobertura baja, para no volver a tropezar.

### S v contrastado con su front matter (2026-07-25) — CERRADO

`pts_samyutta_v_layout.txt` (12 saṃyuttas XLV–LVI, 103 vaggas, 1208 suttas) nunca se había usado.
Contrastado ahora, **todo queda explicado**; el volumen no tenía ningún defecto de datos.

> ⚠️ El layout **no trae páginas de arranque**, solo vaggas y suttas. Una nota anterior decía que
> «las páginas de arranque salen correctas»: era circular, porque esas páginas las había tomado de
> mi propia segmentación. Las reales, leídas de los encabezados del texto, son
> 1, 63, 141, 193, 244, 249, 254, 294, 307, 311, 342, 414.

- **Vaggas: 103/103 exactos**, saṃyutta por saṃyutta (contados por las líneas `CHAPTER`).
- **`LVI Sacca = 181` es un error de OCR del fichero; son 131.** Lo prueba la aritmética de la
  propia tabla: 180+187+103+185+54+110+86+24+54+20+74+**131** = **1208**, el total impreso (con 181
  daría 1258). Y el texto numera hasta `131. (30) Pañcagati` (S v 477). El «3» se leyó como «8».
- **`LIV Ānāpāna` daba 33 en vez de 20 por un defecto de mi parser**, ya corregido
  (`_drop_paragraph_runs`): en S v 328, dentro del sutta 54.12 Kaṅkheyya, hay párrafos numerados con
  la misma forma que un marcador (`7 (1). Ekam idāham āvuso Mahānāma…`). En todo el volumen solo 9
  marcadores caen en la banda del margen (sangría 4–7) y **uno solo es genuino** — el rango peyyāla
  de S v 134, que lleva la fórmula de elisión `vitthāretabba` —, así que en esa banda se exige la
  fórmula. **Ninguna fila del Excel estaba asignada a los marcadores espurios**, así que el dato
  nunca estuvo contaminado; SN 54 mapea 1:1 (54.1→p311 L4 … 54.20→p340 L19).

Los cinco desvíos restantes son **irregularidades del propio impreso**, no del pipeline, y suman
exactamente la diferencia (1190 frente a 1208 = −18):

| saṃyutta | dif | causa |
|---|---:|---|
| XLV Magga | +1 | el nº **170 se imprime dos veces**: S v 57 `170. (10) Taṇhā (vivekaº)` y S v 58 `170. (11) Tasinā (Rāgavinayaº)` |
| XLVI Bojjhaṅga | −10 | **errata que Feer documenta** en su propia nota: S v 135 imprime `99--100` donde debía decir `99--110`, y por eso el saṃyutta cierra en `175` (S v 139) en vez de 185 |
| XLVII Satipaṭṭhāna | +1 | **rangos solapados** en S v 191: `83--93. (1--11)` y `93--102. (1--9)` comparten el 93 |
| XLVIII Indriya | −9 | los números **119–127 no llevan marcador** (elididos) |
| LI Iddhipāda | −1 | el número **78 no lleva marcador** |

**Conclusión: S v queda contrastado con el impreso** — vaggas exactos, recuento explicado hasta el
último número, y el inventario de marcadores corregido sin que cambie ninguna asignación (610/610
asignadas, hueco de inyectividad 0).

**Excel actualizado (2026-07-25).** `calibrate_sn5_lines.py` pasa a usar la misma asignación global
que el validador (antes repetía la cadena de heurísticas por fila, que no es inyectiva): **41 líneas
corregidas → 577/577 exactas**. Estado de las líneas en los cuatro volúmenes contrastados:

| | S i | S ii | S iii | S v |
|---|---|---|---|---|
| líneas exactas | 271/271 | 254/254 | 316/316 | 577/577 |
| sin nº de línea | 0 | 1 | 0 | 1 |

Las 2 filas sin línea (`S ii 15.18 Putta`, `S v 46.66 Uddhumātaka`) caen en el bucket de **página en
disputa** que la calibración no toca por diseño: la primera es miembro de un marcador de rango y en
la segunda el nombre del marcador no casa. No son un residuo del pipeline, sino la política de no
reescribir una página apoyándose solo en la línea.

### Fase 0 — prueba de aceptación común (sin API)

`audit_injectivity.py`: para un volumen dado, lista los marcadores compartidos y calcula el
**hueco de inyectividad** (filas − marcadores distintos usados), descontando los miembros legítimos
de un marcador de rango (su capacidad es el nº de suttas que cubre). **Criterio de cierre de
cualquier volumen: hueco = 0.** Se corre antes y después de cada fase.

### Fase 1 — resolvedor inyectivo y monótono (sin API)

Sustituir la resolución fila-a-fila por una **asignación por saṃyutta**: filas en orden canónico
contra marcadores en orden de lectura, maximizando la suma de las puntuaciones que ya existen
(nombre + proximidad al ancla) con dos restricciones:

- **monotonía** — si la fila *i* va al marcador *j*, la fila *i+1* va a *j* o posterior (las dos
  secuencias están ordenadas: es alineamiento de secuencias, DP O(m·n), exacto y barato);
- **capacidad** — un marcador de rango admite tantas filas como suttas cubre; uno individual, una.

Es la generalización de lo que ya funciona en S i (posicional) y en el Diṭṭhi (`ditthi_pairs`).

### Fase 2 — aplicar a S iii y S v, y re-validar

Re-validar **solo** las filas cuyo par cambie (≈40 en S iii, ≈36 en S v), descartando su veredicto
previo — nunca heredarlo. Recalibrar líneas. Cierre esperado: S iii 333/333 y S v revalidado.

### Fase 3 — S iv — ✅ **CERRADO 🔒 344/344** (2026-07-25). Con él, **SN entero cerrado (1814/1814)**

Los 94 `HELMER_APPROVED` son del pase DeepSeek retirado: se re-validan las 344, no se hereda nada.

**Estructura (`samyutta-vol-IV-info.txt`, front matter de Feer).** 10 saṃyuttas XXXV-XLIV, 33
vaggos, 391 suttas. Las **10 cabeceras de libro caen en la página exacta** que declara Feer y **9
de los 10 recuentos son exactos**, con numeración contigua 1..N. El único desajuste, SN 39
Sāmaṇḍaka (PTS 2, Feer 16), lo explica él: *«All the MSS give only the beginning and the end»* —
se imprimen el nº1 y el nº16. (La tabla resumen de Feer suma 394, pero sus columnas dan 391 y la
prosa confirma 29 y 34: la tabla se equivoca.)

**Lo que cazó la auditoría previa a gastar API** — sin ella, ~120 filas se habrían cotejado contra
otro sutta:

1. **El `Sutta #` NO es la numeración del CST en SN 35.** Es la cuenta **reducida de Feer** (207)
   mientras `massive.tsv` usa la del CST. Los desfases (+17 en p29; +27/+37/+47 en pp. 151-155)
   caen donde Feer explica que comprimió: los 19 suttas de `Jātidhammādi…`+`Aniccādi…` que el Excel
   lleva como **2 filas**, y el **`satthi peyyala`**, donde «reduce» 60 suttantas a 20.
   → El lado CST se resuelve por **POSICIÓN**: los bloques de subhead del XML y las filas del Excel
   se corresponden **1:1 en los 10 saṃyuttas** (344=344) y la comprobación por nombre da **344/344**.
   `massive.tsv` queda sólo para la página de cotejo. Es la regla de siempre: la identidad de una
   fila la dan `Sutta Name` + `PTS Page`, no el `Sutta #`.
2. **Una gāthā tomada por sutta.** `13 Pittaṃ semhaṃ ca vāto ca` (S iv 231) es un verso numerado
   como párrafo; el alineador lo tomaba por marcador y desplazaba `36.22` en adelante. Lo descarta
   la **continuidad de la secuencia** (un nº de párrafo queda POR DEBAJO del esperado; una elisión
   salta hacia delante), que además preserva el `5 Daṭṭhabbena` (p207, marcador legítimo sin
   posición) y el `16 Dukkaram` (p262, salto de elisión de Sāmaṇḍaka).
3. **El `saṭṭhi-peyyāla` es un tercer régimen de marcador**: `(2) Chandena2`, con el **nº corrido
   elidido**. Exigir dígito inicial dejaba 12 filas sin marcador.
4. **Las capacidades se MIDEN en el texto, no se adivinan por el nombre.** Feer junta a veces dos
   suttas del CST bajo un marcador y el título no siempre lo dice: «Agayha» (S iv 126) imprime los
   dos Rūpārāma sin nombrar ninguno, mientras «Devadahakhaṇo» *parece* doble y no lo es — el Khaṇa
   del CST es el marcador siguiente (su texto es el del nº135 «Saṅgayha»). Contar raíces del nombre
   acertaba en tres casos y fallaba en dos; el solapamiento léxico acierta en los cinco.

**Resultado: 340 `VALIDADOR` + 4 `VALIDADOR_HUMANO`.** Los `HELMER_*` de `36.1` y `37.14` se
degradaron primero a PENDIENTE —heredarlos habría dejado como CONFIRMADO justo lo que el validador
vigente rechazaba— y luego Jorge arbitró las cuatro (2026-07-25) tras cotejar el impreso:

| fila | por qué el REJECT era falso negativo |
|---|---|
| `37.14 Pañcavera` | los textos son **idénticos palabra por palabra**; la cobertura 0.33 sale de que el bloque CST arrastra el `Tassuddānaṃ` del vagga, que PTS imprime aparte |
| `36.1 Samādhi` | la prosa es literal en ambos; PTS **añade una gāthā** que el CST no imprime (es lo que vio Gemini, y es cierto, pero es una adición, no otro sutta) |
| `36.30 Suddhika` | el marcador `29 (9) Suddhikaṃ nirāmisam` cubre dos suttas y los imprime seguidos: CST 278 → líneas 2-4, CST 279 (`36.31`) → líneas 5-11, ambos literales. **Gemini aprobó `36.31` contra ESE MISMO marcador y rechazó `36.30`** |
| `35.41 Anusayapahāna` | el marcador es un **rango**, `58-59 (6-7) Anusayā1-2`, y abre con las dos preguntas (`pahiyyanti` / `samugghātam`); el CST 58 es una línea de diez palabras con `…pe…` |

**Patrón común: elisión asimétrica.** Un lado abrevia (`…pe…`, `║ la ║`) y el otro imprime completo,
y el gate mide `|CST ∩ PTS| / |CST|`, que se hunde cuando el CST es una línea. Es el falso negativo
característico de este pipeline y conviene reconocerlo de vista.

Líneas: 260/337 ya exactas, **77 corregidas**; 7 páginas en disputa quedan a arbitraje (no se tocan).

**Gemini cazó un desfase real, no un falso negativo.** Rechazó `35.146/35.147` diciendo «PTS habla
de *dukkha* donde el CST habla de *anattā*»: el tramo Koṭṭhika iba corrido un puesto porque mi
estimación de capacidad había inflado el nº160 — en S iv 144 dos suttas casi idénticas del
Jīvakambavana empatan su máximo de solapamiento por 0.02 (0.65 frente a 0.63). De ahí la regla
definitiva: **la capacidad no se estima a priori, la demuestra el alineamiento**. Se resuelve con
la capacidad natural y sólo las filas que quedan huérfanas prueban que un encabezado cubre más de
uno. Los **tres** dobles reales de S iv quedan declarados uno a uno en `audit_injectivity.SN4_DOBLES`
(«Agayha» = los dos Rūpārāma; «Pubbeñāṇam»; «Suddhikaṃ nirāmisam»), porque son afirmaciones
filológicas y deben poder auditarse a mano.

**Estado del alineador:** 344/344 alineadas, **hueco de inyectividad 0**, página del marcador ≡
`cst_p_page` 343/344 (100 %), ordinal `paṭhama`/`dutiya` 52/53 (98 %), solapamiento léxico mediano
0.70 (sólo 6 filas < 0.30, y 5 de ellas con el nombre casado: la cobertura baja porque un lado
elide). Módulos nuevos: `sn4_markers.py` (gramática pyparsing, 3 regímenes), `sn4_names.py`
(Feer nombra con el término en instrumental y el ordinal como dígito volado), `validador_sn4.py`.

### Fase 4 — deuda de DN/MN — ✅ **HECHA** (verificado 2026-07-25)

**Revisión de los 10 arbitrajes humanos (2026-07-25).** Se revisaron a raíz del defecto del
apóstrofo, sospechando que fueran falsos negativos suyos. **No lo eran** — la hipótesis se
descartó. Sus causas reales, leídas del `gate` guardado en `validador_dnmn.json`:

| causa | nº | detalle |
|---|---|---|
| **el sutta tiene DOS nombres aceptados** | **7** | `MN 26` Ariyapariyesana ≡ **Pāsarāsi**; `MN 10` Satipaṭṭhāna ≡ **Mahā**satipaṭṭhāna; `DN 8` Kassapasīhanāda ≡ **Mahā**sīhanāda; y variantes ortográficas: `MN 69` Gulissāni/Goliyāni, `MN 83` Makhādeva/Maghadeva, `MN 124` Bakkula/Bākula, `DN 24` Pāṭika/Pāthika |
| Jaccard del incipit al borde | 2 | `DN 18` 0.28 y `DN 31` 0.29 contra un umbral de **0.30** |
| objeción real de Gemini | 1 | `DN 19` Mahāgovinda: «texts diverge into different suttas (Mahāgovinda vs. **Sakka-pañha**)» |

O sea: **9 de los 10 fueron arbitrajes casi triviales** —el gate de DN/MN comprobaba la igualdad
del título y no sabe de nombres alternativos, que en el Majjhima están documentados desde siempre—
y sólo `DN 19` exigió criterio de verdad. El arbitraje de Jorge se sostiene en los 10.

⚠️ Nota de método: el gate de DN/MN **no es el de SN/AN**. Usa `título ∧ Jaccard-de-incipit ≥ 0.30`,
no la cobertura léxica ≥ 0.55. Comparar los números de un volumen con los de otro es un error.
Un analizador de variantes como `an_names` habría resuelto automáticamente 7 de los 10.

Las 186 filas que venían del pase DeepSeek retirado **ya se re-validaron con el validador**:
`validador_dnmn.json` = 186 filas, **176 CONFIRMADO** (174 `VALIDADOR` + 2 `PTS_CROSSREF_SN`) y 10
desacuerdos que Jorge arbitró a mano → `VALIDADOR_HUMANO` (5 en DN, 5 en MN). En el Excel no queda
**ningún** `HELMER_*` en DN/MN. DN 34/34 y MN 152/152 descansan por tanto en la fuente vigente.

### AN I — Tika-nipāta — ✅ **151/154** con el validador (2026-07-25)

Primer trozo de AN que pasa por el validador. `an1_markers.py` + `an_names.py` +
`validador_an1_tika.py` + `reconcile_an1_tika.py`.

- **Estructura 16/16** contra el índice de Morris (`anguttara-vol-I-info.txt`): el marcador nº 10k+1
  cae siempre en la página de arranque de vagga que él declara, y los nº corridos van **1..163 sin
  un solo hueco**. El lado PTS más limpio del proyecto.
- **El lado PTS no va por posición**: 163 marcadores para 156 filas. El ancla es la **`DPR Ref`**
  recuperada del `Raw ID`, que describe los desdoblamientos (`3.32 Ānanda` → `AN 3.32a`,
  `3.33 Sāriputta` → `AN 3.32b`) y las fusiones (`3.39` → `AN 3.38-9`); los sufijos `a`/`b` exigen
  capacidad 2. Sin el re-parseo previo, este volumen no se alineaba.
- **Primeras filas de AN con `VRI Ref`** (`s0402m2:N`), la clave canónica — y **no** vía
  `massive.tsv`, que en AN no sirve de puente.
- Los valores legados (`OK+RTE`, `RTE_ONLY`, `UNVERIFIED`) son del pase RTE/BUDSIR, fuera de
  alcance: se sobrescribieron, no se heredaron.
- **3 a arbitraje**: `3.33 Sāriputta` (comparte el nº32 con `3.32`), `3.138 Sampadā` y
  `3.139 Vuddhi` (comparten el nº136). Más las **9 filas de rango**, redundantes con individuales
  que ya existen.

⚠️ **Eka y Duka NO se abordan todavía**, y no por dificultad: allí el CST **no da nombre por sutta**
(sólo párrafos numerados bajo el vagga), así que no hay cotejo por nombre que sirva de red, y las
tres ediciones cuentan unidades distintas (Eka: PTS 272 / Excel 159 / CST 323). Montar un alineador
ahí produciría emparejamientos que ni el validador ni nadie podría desmentir.

### Fase 5 — AN y KN (4.098 filas, el 67% de lo que queda)

Los XML VRI existen (`s04*`, `s05*`) y `massive.tsv` cubre 1.508 de AN y 2.054 de KN. **Falta la
verdad-terreno estructural**: los front matter por volumen (AN I–V; KN por obra), que en los cuatro
volúmenes de SN han sido lo que permite fijar el lado PTS sin conjeturas. Sin ellos no se empieza.

### Orden recomendado

**0 → 1 → 2 → 3 → 4 → 5.** Las fases 0–2 no gastan API salvo la re-validación de ~76 filas; la 3 y
la 4 son el grueso del coste; la 5 depende de que lleguen los OCR.
