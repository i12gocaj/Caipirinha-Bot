import telebot
import os
import json
import time
import requests
import subprocess
import signal
from dotenv import load_dotenv
from requests.exceptions import ReadTimeout
from selenium.common.exceptions import TimeoutException  # En caso de que lo necesites

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Variable global para gestionar el proceso de caipiriña_bot9.py
bot_process = None

# Diccionario de pares y sus URLs (el mismo que usas en el bot principal)
PAIRS_URLS = {
    "USDT-EUR": "https://exchange.revolut.com/trade/USDT-EUR",
    "USDC-EUR": "https://exchange.revolut.com/trade/USDC-EUR",
    "USDT-GBP": "https://exchange.revolut.com/trade/USDT-GBP",
    "USDC-GBP": "https://exchange.revolut.com/trade/USDC-GBP",
}

def obtener_precio_actual(pair: str):
    """
    Consulta la API directamente para obtener el precio actual según el par.
    - Para USDT-EUR y USDC-EUR se usan endpoints de Binance.
    - Para USDT-GBP y USDC-GBP se usa Kraken.
    Devuelve un valor float redondeado a 4 decimales.
    """
    try:
        if pair == "USDT-EUR":
            response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT")
            response.raise_for_status()
            precio = float(response.json()['price'])
            inversa = 1 / precio if precio != 0 else 0.0
            return round(inversa, 4)

        elif pair == "USDC-EUR":
            res_usdc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDCUSDT")
            res_eur = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT")
            res_usdc.raise_for_status()
            res_eur.raise_for_status()
            usdc_usdt = float(res_usdc.json()['price'])
            eur_usdt = float(res_eur.json()['price'])
            inversa = (usdc_usdt / eur_usdt) if eur_usdt != 0 else 0.0
            return round(inversa, 4)

        elif pair == "USDT-GBP":
            response = requests.get("https://api.kraken.com/0/public/Ticker?pair=USDTGBP")
            response.raise_for_status()
            data = response.json()
            if 'result' not in data:
                raise ValueError("La respuesta de Kraken no contiene la clave 'result'.")
            result_key = list(data['result'].keys())[0]
            price = float(data['result'][result_key]['c'][0])
            return round(price, 4)

        elif pair == "USDC-GBP":
            response = requests.get("https://api.kraken.com/0/public/Ticker?pair=USDCGBP")
            response.raise_for_status()
            data = response.json()
            if 'result' not in data:
                raise ValueError("La respuesta de Kraken no contiene la clave 'result'.")
            result_key = list(data['result'].keys())[0]
            price = float(data['result'][result_key]['c'][0])
            return round(price, 4)

        else:
            return 0.0

    except Exception as e:
        # En caso de error, puedes registrar el error o devolver 0.0
        return 0.0

# ----------------------------------------------------------------------
# Comando /price que consulta la API en lugar de leer el fichero de texto
# ----------------------------------------------------------------------
@bot.message_handler(commands=["price"])
def price_command(message):
    try:
        response_msg = "Precios:\n"
        for pair in PAIRS_URLS.keys():
            price = obtener_precio_actual(pair)
            response_msg += f"{pair}: {price:.4f}\n"
        bot.reply_to(message, response_msg)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Comando /ganancia (se mantiene igual)
@bot.message_handler(commands=["ganancia"])
def ganancia_command(message):
    try:
        with open("ganancia.txt", "r") as f:
            ganancia = float(f.read().strip())
            javi_ganancia = ganancia / 4
            alfonso_ganancia = ganancia * 3 / 4
            response = (
                f"💰 Ganancia actual: €{ganancia:.2f}\n"
                f"Javi: €{javi_ganancia:.2f}\n"
                f"Alfonso: €{alfonso_ganancia:.2f}"
            )
            bot.reply_to(message, response)
    except FileNotFoundError:
        bot.reply_to(message, "Esperando datos... Ejecuta primero el bot de monitoreo.")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# ----------------------------------------------------------------------
# Comandos para controlar el bot caipiriña_bot9.py
# ----------------------------------------------------------------------

def start_worker():
    global bot_process
    # Inicia el proceso si no existe o ya terminó
    if bot_process is None or bot_process.poll() is not None:
        if os.name == 'nt':
            bot_process = subprocess.Popen(["python", "caipiriña_bot.py"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            bot_process = subprocess.Popen(["python", "caipiriña_bot.py"])
        print("Bot iniciado")
    else:
        print("El bot ya se encuentra en ejecución.")


def stop_worker():
    global bot_process
    # Envía la señal para simular Ctrl+C y detener el proceso
    if bot_process is not None and bot_process.poll() is None:
        if os.name == 'nt':
            bot_process.send_signal(signal.CTRL_C_EVENT)
        else:
            bot_process.send_signal(signal.SIGINT)
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()  # Forzar la finalización si no se cierra en 5 segundos
            bot_process.wait()
        print("Bot detenido.")
        bot_process = None  # Se resetea la variable para evitar duplicados
    else:
        print("El bot no se está ejecutando.")


def reset_worker():
    # Reinicia el proceso: se detiene y se vuelve a iniciar
    stop_worker()
    time.sleep(1)  # Pequeña espera para asegurar que se ha detenido
    start_worker()
    print("Bot reiniciado.")

@bot.message_handler(commands=["play"])
def play_command(message):
    start_worker()
    bot.reply_to(message, "Comando /play ejecutado: Bot iniciado.")

@bot.message_handler(commands=["stop"])
def stop_command(message):
    stop_worker()
    bot.reply_to(message, "Comando /stop ejecutado: Bot detenido.")

@bot.message_handler(commands=["reset"])
def reset_command(message):
    reset_worker()
    bot.reply_to(message, "Comando /reset ejecutado: Bot reiniciado.")

print("Bot de Telegram iniciado.")

# Polling con reinicio en caso de timeout u otros errores
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except ReadTimeout:
        print("Read timeout detectado. Reiniciando polling en 5 segundos...")
        time.sleep(5)
    except Exception as e:
        print(f"Error inesperado: {e}. Reiniciando polling en 5 segundos...")
        time.sleep(5)