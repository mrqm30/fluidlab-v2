"""Cálculos de flujo laminar, con unidades SI. Solo biblioteca estándar.

Basado en Capítulo II (PDF proporcionado), con extensiones explícitas para
flujo anular y viscosidad por Couette.
"""
from __future__ import annotations

import math
from typing import Any

G = 9.80665  # m/s²
N_SAMPLES = 241


class PhysicsError(ValueError):
    """Entrada inválida o fuera del ámbito de un modelo."""


def field(d: dict, name: str, *, positive: bool = False, minimum=None,
          maximum=None, default=None) -> float:
    raw = d.get(name, default)
    if raw is None or isinstance(raw, bool):
        raise PhysicsError(f"Falta el parámetro «{name}».")
    try:
        value = float(raw)
    except (ValueError, TypeError):
        raise PhysicsError(f"«{name}» debe ser un número.") from None
    if not math.isfinite(value):
        raise PhysicsError(f"«{name}» debe ser finito.")
    if positive and value <= 0:
        raise PhysicsError(f"«{name}» debe ser mayor que cero.")
    if minimum is not None and value < minimum:
        raise PhysicsError(f"«{name}» debe ser ≥ {minimum}.")
    if maximum is not None and value > maximum:
        raise PhysicsError(f"«{name}» debe ser ≤ {maximum}.")
    return value


def numerical(value: float, digits: int = 6) -> str:
    return f"{value:.{digits}g}"


def metrics(*values):
    return [dict(label=title, value=value, unit=unit, note=note)
            for title, value, unit, note in values]


def samples(fn, begin: float, end: float, n=N_SAMPLES, scale=1.0):
    return [[(begin + (end - begin) * i / (n - 1)) * scale,
             fn(begin + (end - begin) * i / (n - 1))] for i in range(n)]


def profile(points, x_label, x_unit, y_label, y_unit):
    return dict(points=points, x_label=x_label, x_unit=x_unit,
                y_label=y_label, y_unit=y_unit)


def warning_regime(re, kind):
    if kind == 'film':
        if re < 4:
            return dict(title="Película laminar lisa", tone="success",
                        detail="Re < 4: zona conservadora de flujo sin ondulaciones.")
        if re < 25:
            return dict(title="Posible inicio de ondulaciones", tone="warning",
                        detail="En los apuntes, el umbral de ondulación varía aproximadamente entre Re = 4 y 25; comprobar el perfil ideal.")
        if re < 1000:
            return dict(title="Película probablemente ondulada", tone="warning",
                        detail="Modelo parabólico ideal: puede no describir ondas en la superficie libre.")
        return dict(title="Modelo laminar posiblemente inválido", tone="danger",
                    detail="Los apuntes sitúan la transición turbulenta aproximadamente entre Re = 1000 y 2000. No extrapolar el perfil laminar.")
    if re < 2100:
        return dict(title="Régimen laminar estimado", tone="success",
                    detail="Re < 2100. La solución está dentro del criterio orientativo para un tubo circular; para otras geometrías es solo una referencia.")
    if re < 4000:
        return dict(title="Zona de transición / criterio indicativo", tone="warning",
                    detail="El perfil laminar podría dejar de representar el flujo real. Los umbrales dependen de la geometría y perturbaciones.")
    return dict(title="Atención: posible flujo turbulento", tone="danger",
                detail="La solución presentada supone flujo laminar. Para este Reynolds es necesario otro modelo.")


def common(d: dict):
    rho = field(d, 'rho', positive=True, maximum=1e7)
    viscosity_kind = d.get('viscosity_kind', 'dynamic')
    viscosity_value = field(d, 'viscosity_value', positive=True, maximum=1e9)
    if viscosity_kind == 'dynamic':
        mu = viscosity_value
        nu = mu / rho
    elif viscosity_kind == 'kinematic':
        nu = viscosity_value
        mu = nu * rho
    else:
        raise PhysicsError("El tipo de viscosidad debe ser dinámica o cinemática.")
    if not math.isfinite(mu) or mu <= 0:
        raise PhysicsError("La viscosidad dinámica derivada no es válida.")
    return rho, mu, nu


def film(d, rho, mu, nu):
    delta = field(d, 'delta', positive=True, maximum=100)
    width = field(d, 'width', positive=True, maximum=1e5)
    length = field(d, 'length', positive=True, maximum=1e6)
    beta = field(d, 'beta', minimum=0, maximum=89.999)
    projection = G * math.cos(math.radians(beta))
    vmax = rho * projection * delta**2 / (2*mu)
    mean = 2*vmax / 3
    Q = mean * width * delta
    tauw = rho * projection * delta
    Re = 4 * rho * mean * delta / mu
    force = tauw * width * length
    vel = lambda x: vmax * (1 - (x/delta)**2)
    tau = lambda x: rho * projection * x
    return dict(
        name="Película descendente", module="film", source="Apuntes, pp. 14–24; ecs. (2.7)–(2.11)",
        metrics=metrics(("Velocidad máxima", vmax, "m/s", "En la superficie libre"),
                        ("Velocidad media", mean, "m/s", "2/3 de la velocidad máxima"),
                        ("Caudal volumétrico", Q, "m³/s", f"{Q*1000:.4g} L/s"),
                        ("Esfuerzo en pared", tauw, "Pa", "Magnitud τw"),
                        ("Fuerza viscosa", force, "N", "Magnitud sobre área L × W"),
                        ("Reynolds de película", Re, "—", "Re = 4ρδv̄/μ")),
        profile=profile(samples(vel, 0, delta, scale=1000), "Distancia desde superficie libre x", "mm", "Velocidad v(x)", "m/s"),
        stress=profile(samples(tau, 0, delta, scale=1000), "Distancia desde superficie libre x", "mm", "Esfuerzo τ(x)", "Pa"),
        regime=warning_regime(Re, 'film'),
        equations=[{"label":"Perfil de velocidad · (2.7)","formula":"v(x) = [ρ g cos(β) / (2 μ)] · (δ² − x²)"},
                   {"label":"Velocidad media · (2.8)","formula":"v̄ = ρ g δ² cos(β) / (3 μ)"},
                   {"label":"Caudal · (2.9)","formula":"Q = ρ g W δ³ cos(β) / (3 μ)"},
                   {"label":"Esfuerzo · (2.4)","formula":"τ(x) = ρ g x cos(β)"}],
        steps=[{"title":"1. Componente de la gravedad", "detail":f"g · cos({beta:g}°) = {numerical(projection)} m/s²"},
               {"title":"2. Balance y condiciones límite", "detail":"dτ/dx = ρg cos(β); τ(0) = 0; v(δ) = 0."},
               {"title":"3. Velocidad máxima", "detail":f"ρg cos(β)δ²/(2μ) = {numerical(vmax)} m/s"},
               {"title":"4. Integración del perfil", "detail":f"Q = v̄ W δ = {numerical(mean)} × {numerical(width)} × {numerical(delta)} = {numerical(Q)} m³/s"}],
        observations=["El ángulo β se mide desde la vertical, tal como en los apuntes.",
                      "Se desprecia el esfuerzo cortante del gas sobre la superficie libre.",
                      "Re alto u ondas superficiales invalidan la aproximación de perfil liso."])


def pipe(d, rho, mu, nu):
    radius = field(d, 'radius', positive=True, maximum=1e4)
    length = field(d, 'length', positive=True, maximum=1e7)
    dp = field(d, 'dp', minimum=0, maximum=1e12)
    orientation = d.get('orientation', 'horizontal')
    gfactors = {'horizontal': 0, 'down': 1, 'up': -1}
    if orientation not in gfactors:
        raise PhysicsError("Orientación desconocida.")
    gradient = dp / length + rho * G * gfactors[orientation]
    if gradient <= 0:
        raise PhysicsError("La fuerza impulsora neta es ≤ 0 en el sentido elegido. Aumenta ΔP o cambia la orientación.")
    vmax = gradient*radius**2/(4*mu)
    mean = vmax/2
    Q = math.pi*radius**2*mean
    Re = 2*radius*rho*mean/mu
    tauw = gradient*radius/2
    dp_visc = gradient*length
    vel=lambda r: vmax*(1-(r/radius)**2)
    tau=lambda r: gradient*r/2
    return dict(name="Tubería circular · Poiseuille", module="pipe", source="Apuntes, pp. 25–38; ecs. (2.17)–(2.21)",
        metrics=metrics(("Velocidad máxima",vmax,"m/s","En el eje r = 0"),
                        ("Velocidad media",mean,"m/s","La mitad de vₘáx"),
                        ("Caudal volumétrico",Q,"m³/s",f"{Q*1000:.4g} L/s"),
                        ("Esfuerzo en pared",tauw,"Pa","Magnitud τw"),
                        ("ΔP viscoso equivalente",dp_visc,"Pa","Incluye aporte gravitatorio si aplica"),
                        ("Número de Reynolds",Re,"—","Re = 2Rρv̄/μ")),
        profile=profile(samples(vel,0,radius,scale=1000),"Radio r (eje → pared)","mm","Velocidad v(r)","m/s"),
        stress=profile(samples(tau,0,radius,scale=1000),"Radio r (eje → pared)","mm","|τ(r)|","Pa"),
        regime=warning_regime(Re,'pipe'),
        equations=[{"label":"Perfil de velocidad · (2.17)","formula":"v(r) = [G R² / (4 μ)] · [1 − (r/R)²]"},
                   {"label":"Velocidad media · (2.19)","formula":"v̄ = G R² / (8 μ)"},
                   {"label":"Hagen–Poiseuille · (2.20)","formula":"Q = π G R⁴ / (8 μ)"},
                   {"label":"Gradiente impulsor","formula":"G = ΔP/L + ρgₛ ; gₛ = 0, +g o −g"}],
        steps=[{"title":"1. Gradiente impulsor neto", "detail":f"G = ΔP/L + ρgₛ = {numerical(gradient)} Pa/m"},
               {"title":"2. Condiciones de frontera", "detail":"v(R) = 0 y gradiente radial dv/dr = 0 en r = 0."},
               {"title":"3. Perfil parabólico", "detail":f"v(0) = G R²/(4μ) = {numerical(vmax)} m/s"},
               {"title":"4. Integración sobre la sección", "detail":f"Q = πR²v̄ = {numerical(Q)} m³/s; Re = {numerical(Re)}"}],
        observations=["La tubería es circular y llena, no un anillo; en el PDF aparece también bajo «tubo concéntrico».",
                      "∆P introducida es p_entrada − p_salida; el flujo se define positivo en el sentido especificado.",
                      "El régimen laminar requiere flujo estacionario y completamente desarrollado."])


def plates(d, rho, mu, nu):
    half_gap = field(d,'half_gap',positive=True,maximum=100)
    width = field(d,'width',positive=True,maximum=1e5)
    length = field(d,'length',positive=True,maximum=1e7)
    dp = field(d,'dp',positive=True,maximum=1e12)
    grad=dp/length
    vmax=grad*half_gap**2/(2*mu)
    mean=2*vmax/3
    Q=mean*2*half_gap*width
    tauw=grad*half_gap
    Dh=4*half_gap*width/(width+2*half_gap)
    Re=rho*mean*Dh/mu
    vel=lambda y: grad*(half_gap**2-y**2)/(2*mu)
    tau=lambda y: grad*y
    reg=warning_regime(Re,'general')
    reg['detail'] += " Re usa el diámetro hidráulico; el criterio para tubería no es un umbral universal para placas."
    return dict(name="Flujo entre placas paralelas", module="plates",source="Apuntes, pp. 39–43; ecs. (2.24)–(2.28)",
        metrics=metrics(("Velocidad máxima",vmax,"m/s","En el plano medio y = 0"),
                        ("Velocidad media",mean,"m/s","2/3 de vₘáx"),
                        ("Caudal volumétrico",Q,"m³/s",f"{Q*1000:.4g} L/s"),
                        ("Esfuerzo en pared",tauw,"Pa","Magnitud en y = ±δ"),
                        ("Diámetro hidráulico",Dh,"m","Basado en ancho W y separación 2δ"),
                        ("Reynolds indicativo",Re,"—","Diámetro hidráulico")),
        profile=profile(samples(vel,-half_gap,half_gap,scale=1000),"Posición y (pared → pared)","mm","Velocidad v(y)","m/s"),
        stress=profile(samples(tau,-half_gap,half_gap,scale=1000),"Posición y","mm","Esfuerzo τ(y)","Pa"),
        regime=reg,
        equations=[{"label":"Velocidad · (2.25)","formula":"v(y) = [ΔP/(2 μ L)] · (δ² − y²)"},
                   {"label":"Velocidad media · (2.27)","formula":"v̄ = ΔP δ² / (3 μ L)"},
                   {"label":"Caudal · (2.28)","formula":"Q = 2 W ΔP δ³ / (3 μ L)"},
                   {"label":"Esfuerzo · (2.24)","formula":"τ(y) = (ΔP/L) · y"}],
        steps=[{"title":"1. Geometría", "detail":f"Separación total entre placas = 2δ = {numerical(2*half_gap)} m."},
               {"title":"2. Ecuación y condiciones límite", "detail":"τ(0) = 0; v(−δ) = v(+δ) = 0."},
               {"title":"3. Velocidad en el centro", "detail":f"v(0) = ΔPδ²/(2μL) = {numerical(vmax)} m/s."},
               {"title":"4. Integración", "detail":f"Q = 2Wδv̄ = {numerical(Q)} m³/s."}],
        observations=["Ambas placas están inmóviles; flujo inducido por diferencia de presión.",
                      "δ es la SEMI-separación; la separación completa es 2δ.",
                      "No se incluyen efectos laterales de las paredes ni de entrada/salida."])


def annulus(d, rho, mu, nu):
    ri=field(d,'inner_radius',positive=True,maximum=1e4)
    ro=field(d,'outer_radius',positive=True,maximum=1e4)
    if ro<=ri:
        raise PhysicsError("El radio exterior debe ser mayor que el radio interior.")
    if (ro-ri)/ri < 0.001:
        raise PhysicsError("La separación anular es menor que 0.1 % del radio interno; este cálculo puede sufrir cancelación numérica. Usa un modelo de ranura delgada.")
    length=field(d,'length',positive=True,maximum=1e7)
    dp=field(d,'dp',positive=True,maximum=1e12)
    grad=dp/length
    ln=math.log(ro/ri)
    a=(ro**2-ri**2)/ln
    def vel(r):
        return grad/(4*mu)*(ro**2-r**2-a*math.log(ro/r))
    def tau(r):
        return grad/4*(2*r-a/r)
    rmax=math.sqrt(a/2)
    vmax=vel(rmax)
    # Stable and physically valid for the normal engineering range.
    Q=math.pi*grad/(8*mu)*(ro**4-ri**4-(ro**2-ri**2)**2/ln)
    if Q<=0 or vmax<=0:
        raise PhysicsError("La geometría anular es demasiado estrecha para la precisión numérica de este modelo.")
    area=math.pi*(ro**2-ri**2)
    mean=Q/area
    Dh=2*(ro-ri)
    Re=rho*mean*Dh/mu
    reg=warning_regime(Re,'general')
    reg['detail'] += " Para anillos concéntricos, el límite depende de la razón de radios."
    return dict(name="Anillo entre tubos concéntricos",module="annulus",source="Extensión: solución analítica de Poiseuille anular (no desarrollada en los apuntes)",
        metrics=metrics(("Velocidad máxima",vmax,"m/s",f"En r = {rmax*1000:.4g} mm"),
                        ("Velocidad media",mean,"m/s","Q dividido entre área anular"),
                        ("Caudal volumétrico",Q,"m³/s",f"{Q*1000:.4g} L/s"),
                        ("Esfuerzo pared interna",abs(tau(ri)),"Pa","Magnitud"),
                        ("Esfuerzo pared externa",abs(tau(ro)),"Pa","Magnitud"),
                        ("Reynolds indicativo",Re,"—","Dh = 2(Rₑ − Rᵢ)")),
        profile=profile(samples(vel,ri,ro,scale=1000),"Radio r (pared interior → exterior)","mm","Velocidad v(r)","m/s"),
        stress=profile(samples(tau,ri,ro,scale=1000),"Radio r","mm","Esfuerzo viscoso τ(r)","Pa"),
        regime=reg,
        equations=[{"label":"Perfil anular", "formula":"v(r) = [G/(4μ)] · [Rₑ² − r² − A ln(Rₑ/r)]"},
                   {"label":"Factor geométrico", "formula":"A = (Rₑ² − Rᵢ²) / ln(Rₑ/Rᵢ)"},
                   {"label":"Caudal anular", "formula":"Q = πG/(8μ) · [Rₑ⁴ − Rᵢ⁴ − (Rₑ² − Rᵢ²)²/ln(Rₑ/Rᵢ)]"},
                   {"label":"Ubicación de velocidad máxima", "formula":"rₘₐₓ = √(A/2) ; G = ΔP/L"}],
        steps=[{"title":"1. Dominio radial", "detail":f"Radio interno {numerical(ri)} m < r < radio externo {numerical(ro)} m."},
               {"title":"2. Condiciones de frontera", "detail":"No deslizamiento: v(Rᵢ) = 0 y v(Rₑ) = 0."},
               {"title":"3. Perfil logarítmico-parabólico", "detail":f"La velocidad máxima es {numerical(vmax)} m/s en r = {numerical(rmax)} m."},
               {"title":"4. Integración anular", "detail":f"Q = ∫2πrv(r)dr = {numerical(Q)} m³/s."}],
        observations=["Esta solución es una ampliación: los apuntes no derivan el anillo entre dos paredes.",
                      "Ambas paredes son fijas y el fluido newtoniano; sin gradiente gravitatorio axial.",
                      "Anillos extremadamente delgados requieren un tratamiento numérico más estable."])


def viscosity(d, rho, mu, nu):
    U=field(d,'speed',minimum=-1e6,maximum=1e6)
    gap=field(d,'gap',positive=True,maximum=1e5)
    area=field(d,'area',positive=True,maximum=1e9)
    shear=U/gap
    tau=mu*shear
    force=tau*area
    vel=lambda y: U*y/gap
    stress=lambda y:tau
    return dict(name="Viscosidad · Ley de Newton / Couette",module="viscosity",source="Ampliación del concepto de viscosidad (pp. 3, 8 y 17)",
        metrics=metrics(("Viscosidad dinámica μ",mu,"Pa·s","Propiedad de entrada o derivada"),
                        ("Viscosidad cinemática ν",nu,"m²/s",f"{nu*1e6:.5g} mm²/s (cSt)"),
                        ("Tasa de corte γ̇",shear,"s⁻¹","U / h"),
                        ("Esfuerzo cortante τ",tau,"Pa","Valor con signo"),
                        ("Fuerza tangencial F",force,"N","τ × A"),
                        ("Velocidad pared móvil",U,"m/s","Flujo de Couette ideal")),
        profile=profile(samples(vel,0,gap,scale=1000),"Distancia a pared fija y","mm","Velocidad v(y)","m/s"),
        stress=profile(samples(stress,0,gap,scale=1000),"Distancia a pared fija y","mm","τ(y)","Pa"),
        regime=dict(title="Fluido newtoniano · modelo ideal",tone="neutral",detail="Se supone viscosidad constante, régimen estacionario, sin deslizamiento y flujo inducido solo por una placa móvil; no se evalúa transición de régimen."),
        equations=[{"label":"Ley de Newton", "formula":"τ = μ · (dv/dy) = μU/h"},
                   {"label":"Viscosidad cinemática", "formula":"ν = μ/ρ ; μ = ρν"},
                   {"label":"Fuerza tangencial", "formula":"F = τ A"},
                   {"label":"Perfil de Couette", "formula":"v(y) = U · y/h"}],
        steps=[{"title":"1. Relación de viscosidades", "detail":f"ν = μ/ρ = {numerical(mu)}/{numerical(rho)} = {numerical(nu)} m²/s."},
               {"title":"2. Gradiente de velocidad", "detail":f"γ̇ = U/h = {numerical(U)}/{numerical(gap)} = {numerical(shear)} s⁻¹."},
               {"title":"3. Ley constitutiva", "detail":f"τ = μγ̇ = {numerical(tau)} Pa."},
               {"title":"4. Fuerza sobre la placa", "detail":f"F = τA = {numerical(force)} N."}],
        observations=["La placa inferior está quieta y la superior se desplaza a velocidad U.",
                      "Las propiedades precargadas de los fluidos son solo valores orientativos alrededor de 20 °C.",
                      "Los líquidos no newtonianos requieren otros modelos reológicos."])


# Los módulos siguientes son ampliaciones: NO están derivados del PDF original.
R_UNIVERSAL = 8.31446261815324  # J/(mol K)
GAS_DATA = {
    # M (kg/mol), viscosidad de referencia (Pa s), T0(K), Sutherland S(K)
    # Parámetros didácticos aproximados; comparar con datos tabulados para diseño.
    'air': ('Aire seco', .0289652, 1.716e-5, 273.15, 110.4),
    'nitrogen': ('Nitrógeno', .0280134, 1.663e-5, 273.15, 107.0),
    'oxygen': ('Oxígeno', .0319988, 1.919e-5, 273.15, 127.0),
    'co2': ('Dióxido de carbono', .0440095, 1.37e-5, 273.15, 240.0),
}
METAL_DATA = {
    # Referencias informativas de metal LÍQUIDO, no sólido.
    # viscosidad y densidad son orientativas a la temperatura especificada.
    'mercury': ('Mercurio líquido', 20., .001526, 13546., -38.83),
    'gallium': ('Galio líquido', 35., .0019, 6095., 29.7646),
    'sodium': ('Sodio líquido', 120., .00065, 927., 97.79),
}


def k_from_c(c):
    return c + 273.15


def sutherland(gas: str, temperature: float) -> float:
    if gas not in GAS_DATA:
        raise PhysicsError('Selecciona un gas disponible.')
    _, _, mu0, t0, s = GAS_DATA[gas]
    return mu0 * (temperature/t0)**1.5 * (t0+s)/(temperature+s)


def gas_density(gas, temp_k, pressure):
    return pressure * GAS_DATA[gas][1] / (R_UNIVERSAL*temp_k)


def shear_inputs(d):
    u = field(d, 'speed', minimum=-1e5, maximum=1e5)
    h = field(d, 'gap', positive=True, maximum=1e5)
    area = field(d, 'area', positive=True, maximum=1e8)
    return u, h, area


def gas_properties(d):
    gas = d.get('gas_name', 'air')
    if gas not in GAS_DATA:
        raise PhysicsError('Gas no reconocido.')
    tc = field(d, 'temperature_C', minimum=-60, maximum=500)
    pressure = field(d, 'pressure', positive=True, maximum=1e6)
    temp = k_from_c(tc)
    mu = sutherland(gas, temp)
    rho = gas_density(gas, temp, pressure)
    nu = mu/rho
    u, h, area = shear_inputs(d)
    grad = u/h
    shear = mu*grad
    name = GAS_DATA[gas][0]
    left = max(-60., tc-55)
    right = min(500., tc+55)
    calc = lambda c: sutherland(gas, k_from_c(c))
    nu_at = lambda c: calc(c)/gas_density(gas,k_from_c(c),pressure)
    return dict(
        name='Viscosidad de gases · '+name, module='gas',
        source='Ampliación: ley de Sutherland + gas ideal (no incluida en el PDF)',
        properties={'rho':rho,'mu':mu,'nu':nu},
        metrics=metrics(('Viscosidad dinámica μ',mu,'Pa·s','Modelo de Sutherland'),
                        ('Viscosidad cinemática ν',nu,'m²/s','μ/ρ'),
                        ('Densidad del gas ρ',rho,'kg/m³','Ley del gas ideal'),
                        ('Gradiente de velocidad',grad,'s⁻¹','U/h'),
                        ('Esfuerzo cortante τ',shear,'Pa','μU/h'),
                        ('Fuerza tangencial',shear*area,'N','τA')),
        profile=profile(samples(calc,left,right),'Temperatura','°C','Viscosidad dinámica μ','Pa·s'),
        stress=profile(samples(nu_at,left,right),'Temperatura','°C','Viscosidad cinemática ν','m²/s'),
        chart_labels=('μ frente a temperatura','ν frente a temperatura'),
        regime=dict(title='Gas diluido · correlación aproximada',tone='neutral',detail='Sutherland aproxima μ(T) de gases puros; ρ se calculó como gas ideal. No aplicar cerca de condensación, alta presión o mezclas sin otro modelo.'),
        equations=[{'label':'Ley de Sutherland','formula':'μ(T) = μ₀ (T/T₀)^(3/2) (T₀+S)/(T+S)'},
                   {'label':'Densidad · gas ideal','formula':'ρ = p M / (R T)'},
                   {'label':'Viscosidad cinemática','formula':'ν = μ/ρ'},
                   {'label':'Ley de Newton','formula':'τ = μ · U/h ; F = τ A'}],
        steps=[{'title':'1. Temperatura absoluta','detail':f'T = {numerical(tc)} + 273.15 = {numerical(temp)} K.'},
               {'title':'2. Viscosidad del gas','detail':f'Sutherland para {name}: μ = {numerical(mu)} Pa·s.'},
               {'title':'3. Densidad y cinemática','detail':f'ρ = {numerical(rho)} kg/m³; ν = {numerical(nu)} m²/s.'},
               {'title':'4. Esfuerzo entre superficies','detail':f'τ = μU/h = {numerical(shear)} Pa; F = {numerical(shear*area)} N.'}],
        observations=['Los coeficientes de Sutherland de referencia son aproximados, no reemplazan tablas de propiedades.',
                      'La presión modifica aquí la densidad, pero no μ: aproximación de gas diluido.',
                      'El esfuerzo cortante representa un gradiente lineal de ejemplo entre placas; no es un campo de flujo de gas compresible.'])


def molten_metal(d):
    metal = d.get('metal_name','mercury')
    if metal not in (*METAL_DATA.keys(), 'custom'):
        raise PhysicsError('Metal no reconocido.')
    t = field(d,'temperature_C',minimum=-200,maximum=2000)
    t0 = field(d,'reference_C',minimum=-200,maximum=2000)
    ref_mu = field(d,'reference_mu',positive=True,maximum=1e5)
    rho = field(d,'reference_rho',positive=True,maximum=1e6)
    Ea = field(d,'activation_energy',minimum=0,maximum=1e6)
    if metal in METAL_DATA and t <= METAL_DATA[metal][4]:
        raise PhysicsError('El metal seleccionado debe estar en fase líquida por encima de su punto de fusión.')
    if Ea == 0 and abs(t-t0) > 1e-9:
        raise PhysicsError('Sin energía de activación calibrada, calcula a la temperatura de referencia.')
    if t0 < -273.14 or t < -273.14:
        raise PhysicsError('Temperatura absoluta inválida.')
    def at(c):
        return ref_mu*math.exp(Ea/R_UNIVERSAL*(1/k_from_c(c)-1/k_from_c(t0)))
    mu=at(t)
    nu=mu/rho
    u,h,area=shear_inputs(d)
    grad=u/h
    tau=mu*grad
    if metal in METAL_DATA:
        name=METAL_DATA[metal][0]
        tmin=max(METAL_DATA[metal][4]+.05,t-40)
    else:
        name='Metal líquido personalizado'
        tmin=max(-200,t-40)
    tmax=min(2000,t+40)
    if Ea == 0:  # No simular una dependencia con temperatura que no se especificó.
        main=profile(samples(lambda r: mu*r,0,max(abs(grad)*2, 1)),'Tasa de corte γ̇','s⁻¹','Esfuerzo τ','Pa')
        second=profile(samples(lambda r: mu,0,max(abs(grad)*2, 1)),'Tasa de corte γ̇','s⁻¹','Viscosidad dinámica μ','Pa·s')
        labels=('τ frente a tasa de corte','μ constante en régimen newtoniano')
    else:
        main=profile(samples(at,tmin,tmax),'Temperatura','°C','Viscosidad dinámica μ','Pa·s')
        second=profile(samples(lambda c: at(c)/rho,tmin,tmax),'Temperatura','°C','Viscosidad cinemática ν','m²/s')
        labels=('μ frente a temperatura','ν frente a temperatura')
    return dict(name='Viscosidad de metal fundido · '+name,module='metal',
        source='Ampliación: propiedades de metales líquidos / Arrhenius opcional (no aparece en el PDF)',
        properties={'rho':rho,'mu':mu,'nu':nu},
        metrics=metrics(('Viscosidad dinámica μ',mu,'Pa·s','Metal en fase líquida'),
                        ('Viscosidad cinemática ν',nu,'m²/s','μ/ρ'),
                        ('Densidad usada ρ',rho,'kg/m³','Constante de referencia'),
                        ('Tasa de corte γ̇',grad,'s⁻¹','U/h'),
                        ('Esfuerzo cortante τ',tau,'Pa','μU/h'),
                        ('Fuerza tangencial',tau*area,'N','τA')),
        profile=main,stress=second,chart_labels=labels,
        regime=dict(title='Metal líquido, no sólido',tone='warning',detail='La viscosidad dinámica de fluido aquí solo se aplica al METAL FUNDIDO. La densidad se mantiene fija. Arrhenius requiere una energía de activación medida/calibrada.'),
        equations=[{'label':'Viscosidad newtoniana','formula':'τ = μ(T) · dv/dy'},
                   {'label':'Relación dinámica/cinemática','formula':'ν = μ/ρ'},
                   {'label':'Dependencia térmica opcional','formula':'μ(T) = μref exp[(Ea/R)(1/T − 1/Tref)]'},
                   {'label':'Fuerza tangencial','formula':'F = μ (U/h) A'}],
        steps=[{'title':'1. Verificación de fase','detail':f'Metal: {name}, temperatura {numerical(t)} °C.'},
               {'title':'2. Modelo viscoso','detail':('Viscosidad tomada en Tref; sin extrapolación térmica.' if Ea==0 else f'Arrhenius con Ea = {numerical(Ea)} J/mol.')},
               {'title':'3. Propiedades de trabajo','detail':f'μ = {numerical(mu)} Pa·s; ρ ≈ {numerical(rho)} kg/m³.'},
               {'title':'4. Ley de Newton','detail':f'γ̇ = {numerical(grad)} s⁻¹; τ = {numerical(tau)} Pa.'}],
        observations=['Un metal sólido se modela con mecánica de sólidos, viscoelasticidad o plasticidad, no con esta μ de fluidos.',
                      'Los ejemplos de metales líquidos son valores aproximados; usa datos tabulados para el caso real.',
                      'Ea = 0 limita el cálculo a Tref. Si introduces Ea, el perfil térmico es solo una extrapolación local.',
                      'No se modela variación de densidad con temperatura, solidificación ni transferencia de calor.'])


def wilke_viscosity(x, gas_a, gas_b, temp_k):
    mu1 = sutherland(gas_a,temp_k)
    mu2 = sutherland(gas_b,temp_k)
    m1 = GAS_DATA[gas_a][1]
    m2 = GAS_DATA[gas_b][1]
    phi12=(1+math.sqrt(mu1/mu2)*(m2/m1)**.25)**2 / math.sqrt(8*(1+m1/m2))
    phi21=(1+math.sqrt(mu2/mu1)*(m1/m2)**.25)**2 / math.sqrt(8*(1+m2/m1))
    return x*mu1/(x+(1-x)*phi12) + (1-x)*mu2/((1-x)+x*phi21)


def mixture(d):
    mode=d.get('mix_type','liquid')
    if mode not in ('gas','liquid'):
        raise PhysicsError('La mezcla debe ser gas o líquido.')
    frac=field(d,'fraction',minimum=0,maximum=1)
    if mode=='liquid':
        mu1=field(d,'mu1',positive=True,maximum=1e8)
        mu2=field(d,'mu2',positive=True,maximum=1e8)
        rho1=field(d,'rho1',positive=True,maximum=1e7)
        rho2=field(d,'rho2',positive=True,maximum=1e7)
        mu_at=lambda f: math.exp(f*math.log(mu1)+(1-f)*math.log(mu2))
        rho_at=lambda f: f*rho1+(1-f)*rho2
        method='Regla logarítmica ideal de mezcla (volumen)'
        fraction_label='Fracción volumétrica de componente 1 φ₁'
        specific_equations=[{'label':'Regla logarítmica (estimación)','formula':'ln μmix = φ₁ ln μ₁ + (1 − φ₁) ln μ₂'},
                            {'label':'Densidad aproximada','formula':'ρmix = φ₁ρ₁ + (1 − φ₁)ρ₂'}]
        caveats=['Se supone miscibilidad, mezcla homogénea, comportamiento newtoniano y volúmenes aditivos.',
                 'La regla logarítmica NO es universal: mezclas agua-glicerol u otras soluciones no ideales pueden apartarse considerablemente.',
                 'Los μ y ρ de los componentes deben corresponder a una misma temperatura.']
    else:
        ga=d.get('gas_a','nitrogen')
        gb=d.get('gas_b','oxygen')
        if ga not in ('nitrogen','oxygen','co2') or gb not in ('nitrogen','oxygen','co2'):
            raise PhysicsError('Para Wilke utiliza componentes puros: N₂, O₂ o CO₂. Aire es una mezcla multicomponente.')
        temp_c=field(d,'temperature_C',minimum=-60,maximum=500)
        pressure=field(d,'pressure',positive=True,maximum=1e6)
        t=k_from_c(temp_c)
        m1=GAS_DATA[ga][1];m2=GAS_DATA[gb][1]
        mu_at=lambda f: wilke_viscosity(f,ga,gb,t)
        rho_at=lambda f: pressure*(f*m1+(1-f)*m2)/(R_UNIVERSAL*t)
        method='Regla de Wilke · mezcla binaria de gases diluidos'
        fraction_label='Fracción molar del gas 1 x₁'
        specific_equations=[{'label':'Mezcla de Wilke','formula':'μmix = Σᵢ[xᵢ μᵢ / Σⱼ(xⱼ Φᵢⱼ)]'},
                            {'label':'Factor de interacción de Wilke','formula':'Φᵢⱼ = [1 + √(μᵢ/μⱼ)(Mⱼ/Mᵢ)^¼]² / √[8(1 + Mᵢ/Mⱼ)]'},
                            {'label':'Densidad · gas ideal','formula':'ρmix = p[x₁M₁ + (1−x₁)M₂]/(RT)'}]
        caveats=['Wilke es una aproximación para mezcla binaria de gases diluidos, sin reacciones químicas.',
                 'Las viscosidades de los gases puros se estiman con Sutherland; presiones elevadas y condensación requieren otros modelos.',
                 'La proporción en este caso es MOLAR; para líquidos se usa VOLUMÉTRICA.']
    mu=mu_at(frac)
    rho=rho_at(frac)
    nu=mu/rho
    return dict(name='Viscosidad de mezcla '+('de líquidos' if mode=='liquid' else 'de gases'),module='mixture',
        source='Ampliación: regla logarítmica / correlación de Wilke (no desarrolladas en el PDF)',
        properties={'rho':rho,'mu':mu,'nu':nu},
        metrics=metrics(('Viscosidad de mezcla μ',mu,'Pa·s',method),
                        ('Densidad de mezcla ρ',rho,'kg/m³','Modelo simplificado'),
                        ('Viscosidad cinemática ν',nu,'m²/s','μmix/ρmix'),
                        ('Componente 1',frac*100,'%','Fracción '+('volumétrica' if mode=='liquid' else 'molar')),
                        ('Componente 2',(1-frac)*100,'%','Fracción complementaria'),
                        ('Viscosidad rel. al componente 1',mu/mu_at(1),'—','μmix/μ₁')),
        profile=profile(samples(mu_at,0,1),fraction_label,'0–1','Viscosidad dinámica μ','Pa·s'),
        stress=profile(samples(rho_at,0,1),fraction_label,'0–1','Densidad ρ','kg/m³'),
        chart_labels=('Viscosidad vs composición','Densidad vs composición'),
        regime=dict(title='Regla de mezcla aproximada',tone='warning',detail=method+'. No modela interacciones complejas; comparar contra propiedades experimentales.'),
        equations=specific_equations+[{'label':'Viscosidad cinemática','formula':'νmix = μmix / ρmix'}],
        steps=[{'title':'1. Tipo de mezcla','detail':method+'.'},
               {'title':'2. Composición','detail':f'Fracción componente 1: {numerical(frac)}; componente 2: {numerical(1-frac)}.'},
               {'title':'3. Viscosidad combinada','detail':f'μmix = {numerical(mu)} Pa·s.'},
               {'title':'4. Densidad y viscosidad cinemática','detail':f'ρmix = {numerical(rho)} kg/m³; νmix = {numerical(nu)} m²/s.'}],
        observations=caveats)


def two_moving_plates(d,rho,mu,nu):
    h=field(d,'gap',positive=True,maximum=100)
    lower=field(d,'speed_lower',minimum=-1e6,maximum=1e6)
    upper=field(d,'speed_upper',minimum=-1e6,maximum=1e6)
    dp=field(d,'dp',minimum=-1e12,maximum=1e12)
    length=field(d,'length',positive=True,maximum=1e7)
    width=field(d,'width',positive=True,maximum=1e7)
    grad=dp/length
    slope=(upper-lower)/h
    def vel(y): return lower+(upper-lower)*y/h + grad*y*(h-y)/(2*mu)
    def tau(y): return mu*slope+grad*(h/2-y)
    mean=(lower+upper)/2+grad*h*h/(12*mu)
    Q=mean*h*width
    fbot=tau(0)*width*length
    ftop=-tau(h)*width*length
    extrema=[vel(0),vel(h)]
    if grad:
        ycrit=h/2+mu*(upper-lower)/(grad*h)
        if 0<ycrit<h:extrema.append(vel(ycrit))
    vmax=max(extrema)
    vmin=min(extrema)
    return dict(name='Dos placas separadas · Couette–Poiseuille',module='couette',
        source='Ampliación: dos paredes móviles + gradiente de presión; contrasta con placas fijas de pp. 39–43',
        metrics=metrics(('Velocidad media v̄',mean,'m/s','Incluye arrastre y presión'),
                        ('Caudal neto Q',Q,'m³/s','Con signo'),
                        ('Velocidad máxima',vmax,'m/s','Máximo algebraico del perfil'),
                        ('Velocidad mínima',vmin,'m/s','Posible contraflujo'),
                        ('Esfuerzo placa inferior',tau(0),'Pa','Signo de μ dv/dy'),
                        ('Esfuerzo placa superior',tau(h),'Pa','Signo de μ dv/dy'),
                        ('Fuerza sobre placa inferior',fbot,'N','Del fluido sobre la placa'),
                        ('Fuerza sobre placa superior',ftop,'N','Del fluido sobre la placa'),
                        ('Densidad usada ρ',rho,'kg/m³','Dada por el usuario')),
        profile=profile(samples(vel,0,h,scale=1000),'Separación y desde placa inferior','mm','Velocidad v(y)','m/s'),
        stress=profile(samples(tau,0,h,scale=1000),'Separación y desde placa inferior','mm','Esfuerzo μ dv/dy','Pa'),
        chart_labels=('Perfil de velocidad','Esfuerzo cortante'),
        regime=dict(title='Couette–Poiseuille · laminar ideal',tone='neutral',detail='Placas infinitas en anchura efectiva, propiedades constantes, flujo estacionario y plenamente desarrollado. Un perfil calculado no garantiza estabilidad laminar.'),
        equations=[{'label':'Velocidad entre dos placas','formula':'v(y) = U₀ + (U₁−U₀)y/h + (ΔP/2μL)y(h−y)'},
                   {'label':'Velocidad media','formula':'v̄ = (U₀+U₁)/2 + ΔP h²/(12 μ L)'},
                   {'label':'Esfuerzo cortante','formula':'τ(y) = μ(U₁−U₀)/h + (ΔP/L)(h/2−y)'},
                   {'label':'Caudal y fuerzas','formula':'Q = W h v̄; F₀ = τ(0)WL; F₁ = −τ(h)WL'}],
        steps=[{'title':'1. Condiciones en cada superficie','detail':f'v(0) = U₀ = {numerical(lower)} m/s; v(h) = U₁ = {numerical(upper)} m/s.'},
               {'title':'2. Arrastre de placas y presión','detail':f'ΔP/L = {numerical(grad)} Pa/m; (U₁−U₀)/h = {numerical(slope)} s⁻¹.'},
               {'title':'3. Integración entre las paredes','detail':f'v̄ = {numerical(mean)} m/s; Q = {numerical(Q)} m³/s.'},
               {'title':'4. Fuerzas viscosas','detail':f'F inferior = {numerical(fbot)} N; F superior = {numerical(ftop)} N.'}],
        observations=['Las placas pueden moverse independientemente, incluso en sentidos opuestos.',
                      'Si ΔP = 0 se obtiene Couette puro; si U₀=U₁=0, Poiseuille plano.',
                      'El ancho W es suficientemente grande para despreciar efectos de bordes y el área mojada es W×L.',
                      'El sentido de las fuerzas corresponde al esfuerzo ejercido POR el fluido SOBRE cada placa.'])


SOLVERS = {'film':film, 'pipe':pipe, 'plates':plates, 'annulus':annulus, 'viscosity':viscosity, 'couette':two_moving_plates}
PROPERTY_SOLVERS = {'gas':gas_properties, 'metal':molten_metal, 'mixture':mixture}


def calculate(payload: dict[str, Any]) -> dict:
    if not isinstance(payload, dict):
        raise PhysicsError("Se esperaba un objeto JSON.")
    kind = payload.get('module', 'film')
    if kind in PROPERTY_SOLVERS:
        result = PROPERTY_SOLVERS[kind](payload)
    elif kind in SOLVERS:
        rho, mu, nu = common(payload)
        result = SOLVERS[kind](payload,rho,mu,nu)
        result['properties'] = {'rho':rho,'mu':mu,'nu':nu}
    else:
        raise PhysicsError('Módulo no reconocido.')
    result['model_notice'] = 'Modelo educativo con hipótesis específicas por módulo. Las correlaciones y propiedades aproximadas no sustituyen datos experimentales ni validación de ingeniería.'
    # Check overflow anywhere before serialization.
    def check(obj):
        if isinstance(obj,float) and not math.isfinite(obj):
            raise PhysicsError("La combinación de parámetros desborda la capacidad numérica.")
        if isinstance(obj,dict):
            for v in obj.values():check(v)
        if isinstance(obj,list):
            for v in obj:check(v)
    check(result)
    return result
