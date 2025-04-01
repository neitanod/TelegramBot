#!/usr/bin/env python

import argparse
import os
from dotenv import load_dotenv
import telebot
import mimetypes
from telebot.apihelper import ApiTelegramException
import sys

load_dotenv()

API_KEY = os.getenv('API_KEY')

def last_chat_ids():
    if not os.path.exists("last_admin_chat_ids"):
        return []
    with open("last_admin_chat_ids", "r") as f:
        ids_str = f.read()
        if not ids_str:
            return []
    return list(map(int, ids_str.split(',')))

CHAT_IDS = last_chat_ids()

if not API_KEY or not CHAT_IDS:
    print("Faltan API_KEY o CHAT_IDS en el entorno.")
    sys.exit(1)

bot = telebot.TeleBot(API_KEY)

parser = argparse.ArgumentParser(description="Enviar mensajes o archivos por Telegram desde línea de comandos.")

parser.add_argument('--message', help='Texto del mensaje a enviar. Si no se proporciona, se puede recibir desde stdin.')
parser.add_argument('--audio', help='Archivo de audio (ogg, mp3, wav)')
parser.add_argument('--image', help='Archivo de imagen (jpg, png, etc)')
parser.add_argument('--attach', help='Cualquier archivo para enviar como documento')
parser.add_argument('--voice', help='Nota de voz (ogg, wav, etc) enviada como mensaje de voz de Telegram')
parser.add_argument('--chat-id', help='Chat ID para enviar el mensaje. Si no se proporciona, se usarán todos los IDs de usuarios conectados.')

args = parser.parse_args()

# Determinar los chat IDs a usar
env_chat_id = os.getenv('TELEGRAM_BOT_CHAT_ID')
if args.chat_id:
    target_chat_ids = [int(args.chat_id)]
elif env_chat_id:
    target_chat_ids = [int(env_chat_id)]
else:
    target_chat_ids = CHAT_IDS

# Envío de mensaje de texto
try:
    if args.message:
        for chat_id in target_chat_ids:
            bot.send_message(chat_id, args.message)
    elif not sys.stdin.isatty():
        # Leer de stdin si hay datos disponibles
        stdin_message = sys.stdin.read().strip()
        if stdin_message:
            for chat_id in target_chat_ids:
                bot.send_message(chat_id, stdin_message)

    # Envío de audio
    if args.audio:
        if not os.path.isfile(args.audio):
            print(f"Archivo de audio no encontrado: {args.audio}")
            sys.exit(1)
        with open(args.audio, 'rb') as audio:
            for chat_id in target_chat_ids:
                bot.send_audio(chat_id, audio)

    # Envío de imagen
    if args.image:
        if not os.path.isfile(args.image):
            print(f"Imagen no encontrada: {args.image}")
            sys.exit(1)
        with open(args.image, 'rb') as img:
            for chat_id in target_chat_ids:
                bot.send_photo(chat_id, img)

    # Envío de cualquier archivo
    if args.attach:
        if not os.path.isfile(args.attach):
            print(f"Archivo no encontrado: {args.attach}")
            sys.exit(1)
        with open(args.attach, 'rb') as doc:
            for chat_id in target_chat_ids:
                bot.send_document(chat_id, doc)

    # Envío de nota de voz (mensaje de voz)
    if args.voice:
        if not os.path.isfile(args.voice):
            print(f"Archivo de voz no encontrado: {args.voice}")
            sys.exit(1)
        with open(args.voice, 'rb') as voice:
            for chat_id in target_chat_ids:
                bot.send_voice(chat_id, voice)
except ApiTelegramException as e:
    print(f"Error al enviar mensaje: {e}")
    sys.exit(1)
