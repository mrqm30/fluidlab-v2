# FluidLab v2 — Laboratorio interactivo de mecánica de fluidos

Aplicación **Python + HTML + CSS + JavaScript** para resolver problemas de flujo laminar y propiedades viscosas. Esta edición para despliegue público **no distribuye el PDF original**. Contiene modelos físicos derivados de los apuntes y ampliaciones identificadas en el software.

## Iniciar

Requiere **Python 3.10 o posterior**, sin paquetes externos ni conexión a internet.

```bash
cd FluidLab
python3 app.py
```

Abre **http://127.0.0.1:8000** en el navegador. Para otro puerto: `python3 app.py --port 8080`. Detén con `Ctrl+C`. El servidor solo escucha en localhost por defecto.

> Es necesario arrancar `app.py`; abrir `web/index.html` directamente no conecta al motor de Python.

## Los nueve módulos

| Módulo | Modelo y principales resultados | Procedencia |
| --- | --- | --- |
| Película descendente | Perfil parabólico, velocidad, caudal, τ, Re y fuerza | PDF pp. 14–24 |
| Tubería circular | Hagen–Poiseuille, caudal, tensión en pared, Re | PDF pp. 25–38 |
| Placas paralelas estacionarias | Poiseuille plano; ambas placas fijas, separación `2δ` | PDF pp. 39–43 |
| Viscosidad general | Ley de Newton, μ/ν y Couette con una placa fija | Ampliación |
| Tubos concéntricos | Flujo anular entre cilindros concéntricos | Ampliación |
| **Dos placas móviles** | Couette–Poiseuille con velocidades independientes `U₀`, `U₁` y `ΔP`; perfiles, esfuerzo y fuerzas | Ampliación |
| **Viscosidad de gases** | Sutherland `μ(T)`, gas ideal `ρ(p,T)`, ν, esfuerzo y fuerza | Ampliación |
| **Metales líquidos** | Datos de referencia de mercurio, galio o sodio fundidos; μ, ν, τ; dependencia `μ(T)` opcional mediante Arrhenius calibrado | Ampliación |
| **Mezclas binarias** | Líquidos miscibles: logaritmo ponderado por **fracción volumétrica**; gases diluidos: **Wilke** con fracción **molar** | Ampliación |

Cada módulo incluye ejemplos editables, conversión de propiedades cuando aplica, fórmulas, procedimiento, gráfica interactiva y CSV. Las gráficas de propiedades muestran temperatura/composición cuando corresponde, no perfiles ficticios de velocidad.

### Viscosidad de gases

- Entradas: gas (aire, N₂, O₂ o CO₂), temperatura °C, presión absoluta Pa, velocidad relativa, separación, área.
- `μ(T) = μ₀ (T/T₀)^(3/2) (T₀+S)/(T+S)` (Sutherland), `ρ = p M/(RT)` (gas ideal), `ν = μ/ρ`.
- Ejemplo a 20 °C y 101325 Pa: aire con `μ ≈ 1.81 × 10⁻⁵ Pa·s` y `ρ ≈ 1.20 kg/m³`.
- **Alcance**: gases diluidos e intervalos aproximados; los coeficientes son referenciales y la presión no modifica μ en este modelo. No extrapolar cerca de la saturación ni a presión elevada.

### Metales líquidos — no metales sólidos

- Los materiales ejemplificados son mercurio líquido (20 °C), galio líquido (35 °C) y sodio líquido (120 °C).
- Se suministra `μref`, `ρref` y `Tref`. Sin dato térmico (`Ea = 0`), solo se permite calcular a `Tref`.
- Para un `Ea` **medido o calibrado**: `μ(T) = μref exp[(Ea/R)(1/T − 1/Tref)]`, donde T está en kelvin. **No** se proporcionan valores inventados de `Ea`.
- Una propiedad viscosa de *flujo newtoniano de metal fundido* no modela deformación plástica o fluencia de metal sólido. Densidad constante y valores de catálogo orientativos.

### Viscosidad de mezclas binarias

**Líquidos:** `ln(μmix) = φ₁ ln(μ₁) + (1 − φ₁) ln(μ₂)` y `ρmix = φ₁ρ₁ + (1 − φ₁)ρ₂` con fracción **volumétrica**. Es una **regla de estimación**, no una ley exacta: para soluciones no ideales como agua-glicerina la discrepancia puede ser grande; se recomiendan datos experimentales.

**Gases:** aproximación de **Wilke**, con fracciones **molares** y coeficientes de viscosidad calculados con Sutherland. Permite N₂/O₂/CO₂ puros; el aire no se trata como especie pura en este módulo. Mezclas reactivas, alta presión o más de dos especies requieren otro modelo.

### Dos placas separadas — Couette–Poiseuille

Con `0 ≤ y ≤ h`, velocidad de placa inferior `U₀`, superior `U₁`, viscosidad `μ`, presión `ΔP = p_entrada − p_salida`, longitud `L` y ancho `W`:

```text
v(y) = U₀ + (U₁ − U₀)y/h + [ΔP/(2μL)] y(h−y)
v_media = (U₀+U₁)/2 + ΔP h²/(12μL)
τ(y) = μ (U₁−U₀)/h + (ΔP/L)(h/2 − y)
Q = W h v_media
```

`ΔP=0` permite Couette puro; `U₀=U₁=0` da Poiseuille entre paredes inmóviles. Se muestra el signo de las fuerzas del fluido sobre ambas placas.

## Precauciones científicas

- Unidades SI; comprobar convenciones de signo, geometría y propiedades de referencia.
- Los **primeros módulos** suponen fluido newtoniano y régimen laminar, estacionario y totalmente desarrollado.
- Las **nuevas correlaciones** de propiedades (gas, metal, mezclas) tienen hipótesis particulares: no son fórmulas universales ni validaciones de fase/estado termodinámico completas.
- En el PDF, la sección titulada «tubo concéntrico» utiliza `r=0` y desarrolla en realidad la solución para **tubería circular**. La geometría anular se resuelve por separado.
- Las correlaciones no sustituyen mediciones, datos termofísicos confiables, validación de regímenes o un modelo reológico apropiado.

## Carpetas

```text
FluidLab/
├── app.py                     # servidor local / API REST (stdlib)
├── physics.py                 # los nueve modelos y validaciones
├── web/
│   ├── index.html             # dashboard
│   ├── styles.css             # diseño adaptable
│   └── app.js                 # UI y gráficas SVG
├── tests/
│   └── test_physics.py        # pruebas de resultados numéricos
├── render.yaml                # configuración para Render
└── DEPLOY_RENDER.md           # instrucciones de despliegue
```

Pruebas: `python3 -m unittest discover -s tests -v`.

API de ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/calculate \
  -H 'Content-Type: application/json' \
  -d '{"module":"gas","gas_name":"air","temperature_C":20,"pressure":101325,"speed":0.5,"gap":0.002,"area":0.1}'
```

También puedes abrir directamente un módulo en el navegador con `?module=gas`, `?module=metal`, `?module=mixture` o `?module=couette`.

## Despliegue público

Para publicar en Render, sigue [`DEPLOY_RENDER.md`](DEPLOY_RENDER.md). No incluyas apuntes de terceros o archivos privados sin autorización.
