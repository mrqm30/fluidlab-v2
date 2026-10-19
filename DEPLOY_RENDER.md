# Publicar FluidLab en Render (demo pública gratis)

Este paquete está adaptado para publicar la app desde GitHub a **Render**.
No incluye el PDF de los apuntes ni el enlace público al PDF. Si tienes derechos
para distribuirlo, puedes incorporarlo conscientemente en otra versión.

## Antes: probar en tu computadora

Requiere Python >= 3.10. Abre una terminal en esta carpeta:

```bash
python3 -m unittest discover -s tests -v
python3 app.py
```

Visita http://127.0.0.1:8000 y http://127.0.0.1:8000/api/health.

## Opción A: crear Web Service desde el Dashboard de Render

1. Crea un nuevo repositorio **GitHub** (público o privado) y sube **el contenido de esta carpeta**, incluyendo `app.py`, `physics.py`, `web/`, `tests/`, `.python-version` y `render.yaml`.
2. Ingresa a https://dashboard.render.com y elige **New > Web Service**.
3. Conecta tu repositorio. En configuración, selecciona **Python** y el plan **Free**.
4. `Root Directory`: deja vacío si subiste los archivos directamente a la raíz del repositorio.
5. `Build Command`: `python3 -m unittest discover -s tests -v`.
6. `Start Command`: `python3 app.py --host 0.0.0.0 --port $PORT`.
7. `Health Check Path`: `/api/health`.
8. Elige **Deploy Web Service**. Render te asignará una URL `https://...onrender.com`.

## Opción B: Render Blueprint

El archivo `render.yaml` se encuentra en la raíz. En Render elige **New > Blueprint**, vincula el repositorio y deja que Render lea esa configuración. Verifica que muestre `plan: free` antes de crear el servicio.

## Probar un cálculo con la aplicación ya publicada

Sustituye `https://TU-SERVICIO.onrender.com` por la URL que Render te entregue:

```bash
curl -s https://TU-SERVICIO.onrender.com/api/health
curl -sS -X POST https://TU-SERVICIO.onrender.com/api/calculate \
  -H 'Content-Type: application/json' \
  -d '{"module":"gas","gas_name":"air","temperature_C":20,"pressure":101325,"speed":0.5,"gap":0.002,"area":0.1}'
```

## Limitaciones importantes

- El servicio gratuito de Render se duerme tras 15 minutos sin visitas y puede tardar alrededor de un minuto en reactivarse. También tiene límites de uso.
- El servidor HTTP incluido es el de la biblioteca estándar de Python. Es adecuado para un prototipo educativo, **no** ofrece garantías de servicio, autenticación ni controles avanzados de abuso.
- Cualquiera que visite el enlace público puede introducir parámetros y llamar `/api/calculate`.
- Si planeas prestar un servicio comercial o con tráfico alto, añade un servidor WSGI/ASGI de producción, controles de abuso, observabilidad y hosting con SLA.
- Nunca subas credenciales, datos privados ni archivos con derechos de terceros sin autorización.
