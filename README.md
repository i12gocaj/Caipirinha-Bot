# 🥥 Caipirinha Bot — Trading automático en Revolut X (proyecto demostrativo)

> **Estado: archivado / no mantenido**. Este proyecto documenta un experimento personal para operar en **Revolut X** sin API pública. Funcionó durante unos meses en 2025, pero desde entonces la plataforma cambia con demasiada frecuencia y **no se garantizan ni soporte ni beneficios**.

---

## ✨ Por qué existe

Revolut X ofrecía *spreads* atractivos en pares cripto‑fiat (sobre todo **USDT‑EUR**). La falta de API oficial impedía automatizar estrategias de *market‑making* pasivas; Caipirinha Bot cubrió ese hueco controlando la interfaz web con **Selenium**.

> **Nota sobre ingresos**: Con la prohibición de USDT para usuarios europeos (abril 2025) la liquidez cayó en picado y los resultados se deterioraron. Hoy el bot sirve únicamente como referencia técnica.

---

## 🛠️ Instalación mínima

No hay `requirements.txt`. Instala manualmente los paquetes:

```bash
python -m venv .venv && source .venv/bin/activate
pip install selenium webdriver-manager pyTelegramBotAPI python-dotenv requests
```

Asegúrate de descargar **ChromeDriver** que coincida con tu versión de Chrome y exporta `CHROMEDRIVER_PATH` en tu `.env`.

### Variables de entorno básicas (`.env`)

| Clave               | Descripción                           |
| ------------------- | ------------------------------------- |
| `TELEGRAM_TOKEN`    | Token de tu bot de Telegram           |
| `TELEGRAM_CHAT_ID`  | Donde enviar alertas                  |
| `CHROMEDRIVER_PATH` | Ruta absoluta a chromedriver          |
| `HEADLESS`          | `true`/`false` para modo sin interfaz |

---

## 🧠 Cómo opera la estrategia

Caipirinha Bot **no** implementa una cuadrícula clásica. Su meta es mantener la **primera posición en el libro de órdenes** (*top‑of‑book*) con un *tick* mínimo de 0.0001 por delante del mejor competidor.

1. **Pares admitidos** — definidos en `PAIRS_URLS` (`USDC‑EUR` por defecto).
2. **Mirroring top‑of‑book**

   * **Buy**: lee el mejor precio y volumen (`obtener_top_buy`, `obtener_valor_top_buy`). Si el volumen rival supera un umbral dinámico (`500 × diferencia_en_ticks`) sube la puja en +0.0001; si no, se sitúa detrás del segundo mejor nivel para no sobrepagar.
   * **Sell**: lógica espejo usando `obtener_bottom_sell`.
3. **Una orden por lado**: `memoria_ordenes` asegura que solo exista 1 Buy y 1 Sell simultáneas. Cuando una se ejecuta, `detectar_ordenes_ejecutadas` llama a `reposicionar_orden` para reemplazarla.
4. **Sanity‑check externo**: consulta Kraken/Binance cada 5 s y si la desviación supera 0,4 % bloquea el envío de órdenes.
5. **Cola de pendientes**: fallos de saldo o interfaz se almacenan en `ordenes_pendientes` y se reintentan periódicamente.
6. **Precisión**: se usa `decimal.Decimal` con 4 decimales y redondeo `ROUND_DOWN`.

Resultado: un *market‑making* pasivo para capturar céntimos en movimientos ligeros, **sin** arbitraje ni cuadrícula.

## 🤖 `telegram_bot.py`

Script auxiliar basado en **pyTelegramBotAPI** que permite **control remoto** y monitorización del proceso principal:

| Comando     | Acción                                                     |
| ----------- | ---------------------------------------------------------- |
| `/play`     | Lanza `caipiriña_bot.py` como sub‑proceso.                 |
| `/stop`     | Envía `SIGINT` al proceso y espera su cierre.              |
| `/reset`    | Reinicia el proceso (stop → play).                         |
| `/price`    | Devuelve precios actuales de los pares vía Binance/Kraken. |
| `/ganancia` | Lee `ganancia.txt` (creado por el bot) y muestra la cifra. |

No coloca órdenes; solo envía alertas y gestiona el *worker*. Maneja excepciones de red (`ReadTimeout`) y reintenta cada 15 s.

> **Importante:** cuando Revolut X cambia el DOM y el bot falla, `/reset` es útil tras aplicar parches.

## 🔧 Mantenimiento (el gran dolor de cabeza)

* Revolut X cambia etiquetas y clases CSS **cada semana** ⇒ hay que actualizar los *XPaths* de elementos críticos.
* Cambios menores (nuevos banners o *pop‑ups*) bloquean la automatización.
* ChromeDriver se desincroniza con el navegador obligando a actualizar binarios.

Consecuencia: **dedicación semanal** para que el bot siga corriendo.

---

## 🗂️ Estructura del repositorio

```
caipirinha‑bot/
├── caipirinha_bot.py    # núcleo Selenium + estrategia grid
├── telegram_bot.py      # alertas y control remoto
└── README.md            # este documento
```

---

## ⚠️ Descargo de responsabilidad

Esto es **software experimental**. No es asesoramiento financiero. Úsalo bajo tu propio riesgo, revisa el código e invierte sólo lo que estés dispuesto a perder.

---

**Fin del README**
