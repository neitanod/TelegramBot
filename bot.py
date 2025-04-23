#!/usr/bin/python3

import os
import json
from dotenv import load_dotenv
import telebot
import requests
import os
import subprocess

load_dotenv()

API_KEY = str(os.getenv('API_KEY'))
PASSWORD = str(os.getenv('PASSWORD'))
SUDO_PASSWORD = str(os.getenv('SUDO_PASSWORD'))
DISPLAY = str(os.getenv('DISPLAY'))
DBUS = str(os.getenv('DBUS_SESSION_BUS_ADDRESS'))
VOICE_ES = str(os.getenv('VOICE_ES', 'es'))
VOICE_EN = str(os.getenv('VOICE_EN', 'en'))
authorized = []

# Prohibimos alias con estos nombres (creados por el usuario)
PROHIBITED_ALIAS_NAMES = {
    "alias", "describe", "exit", "quit", "logout",
    "reset", "restart", "sys", "sudo",
    "load_aliases", "help", "menu"
}

# Diccionario global de aliases predefinidos (sólo lectura)
builtin_aliases = {}
BUILTIN_ALIAS_FILE = "builtin_aliases.json"

# Diccionario global de aliases creados por el usuario
aliases = {}
ALIAS_FILE = "aliases.json"  # Almacenar en JSON

bot = telebot.TeleBot(API_KEY)


def load_builtin_aliases():
    """Carga los aliases inmutables desde el archivo builtin_aliases.json (si existe)."""
    global builtin_aliases
    if not os.path.exists(BUILTIN_ALIAS_FILE):
        print(f"No se encontró archivo {BUILTIN_ALIAS_FILE}. Se usará un diccionario vacío.")
        builtin_aliases = {}
        return
    try:
        with open(BUILTIN_ALIAS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                builtin_aliases = data
            else:
                print("Formato de aliases inmutables inválido.")
    except Exception as e:
        print(f"Error cargando aliases inmutables: {str(e)}")
        builtin_aliases = {}


def load_aliases():
    global aliases
    if not os.path.exists(ALIAS_FILE):
        aliases = {}
        return
    try:
        with open(ALIAS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                aliases = data
            else:
                print("Formato de alias inválido en JSON.")
    except Exception as e:
        print(f"Error cargando aliases: {str(e)}")


def save_aliases():
    try:
        with open(ALIAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(aliases, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando aliases: {str(e)}")

def ask_ai(chat_id, query):
    try:
        cmd = f"TELEGRAM_BOT_USER_ID=\"{chat_id}\" TELEGRAM_BOT_CHAT_ID=\"{chat_id}\" ./ask_ai \"{query}\""
        print(f"{cmd} 2>&1");
        response = os.popen(cmd + " 2>&1").read()
        return response
    except Exception as e:
        print(f"Error asking AI: {str(e)}")
        return f"Lo siento, ha ocurrido un error: {str(e)}."

def apply_aliases(message_text):
    """
    - Primero busca el comando en `builtin_aliases` (read-only),
      si no lo encuentra, busca en `aliases` (editables).
    - Si se encuentra un alias, reemplaza `?` por los argumentos.
    """
    tokens = message_text.strip().split()
    if not tokens:
        return message_text

    command = tokens[0]
    args = tokens[1:]

    # 1) ¿Está en los aliases predefinidos inmutables?
    if command.lower() in builtin_aliases:
        alias_replacement = builtin_aliases[command.lower()].get('command', '')
    # 2) Si no, ¿está en los aliases creados por el usuario?
    elif command.lower() in aliases:
        alias_replacement = aliases[command.lower()].get('command', '')
    else:
        # No es alias, se devuelve tal cual
        return message_text

    # Reemplazar '${*}'
    if '${*}' in alias_replacement:
        final_command = alias_replacement.replace('${*}', ' '.join(args))
    else:
        final_command = alias_replacement
        if args:
            final_command += ' ' + ' '.join(args)
    return final_command.strip()


@bot.message_handler(commands=['menu','help'])
def menu(message):
    if message.chat.id in authorized:
        help_content = ""
        if os.path.exists("help"):
            with open("help", "r", encoding="utf-8") as hf:
                help_content = hf.read()

        # En este nuevo modelo, mostramos todos los aliases como "comandos"
        # sin incluir el comando real, únicamente su nombre y su descripción.
        # 1) primero los predefinidos
        if builtin_aliases:
            for alias_name, alias_data in builtin_aliases.items():
                desc = alias_data.get('description', '')
                help_content += f"- *{alias_name}*    "
                if desc:
                    help_content += f"  {desc}\n"

        # 2) luego los del usuario
        if aliases:
            help_content += "\n**Comandos definidos por el usuario:**\n"
            for alias_name, alias_data in aliases.items():
                desc = alias_data.get('description', '')
                help_content += f"- *{alias_name}*    "
                if desc:
                    help_content += f"  {desc}\n"

        if not help_content:
            help_content = "No hay ayuda disponible."
        bot.reply_to(message, help_content, parse_mode="Markdown")
    else:
        bot.reply_to(message, "Just say hi")


@bot.message_handler(commands=['aliases'])
def list_aliases(message):
    if message.chat.id not in authorized:
        bot.reply_to(message, "No estás autorizado.")
        return

    # Construimos la respuesta
    builtin_text = ""
    user_text = ""

    # Bloque aliases integrados
    if builtin_aliases:
        builtin_text += "**Aliases integrados (solo lectura):**\n"
        for aname, adata in builtin_aliases.items():
            cmd = adata.get('command', '')
            desc = adata.get('description', '')
            builtin_text += f"\n- *{aname}* => `{cmd}`"
            if desc:
                builtin_text += f"\n  {desc}"
        builtin_text += "\n"
    else:
        builtin_text = "No hay aliases integrados predefinidos.\n\n"

    # Bloque aliases de usuario
    if aliases:
        user_text += "**Aliases de usuario:**\n"
        for aname, adata in aliases.items():
            cmd = adata.get('command', '')
            desc = adata.get('description', '')
            user_text += f"\n- *{aname}* => `{cmd}`"
            if desc:
                user_text += f"\n  {desc}"
        user_text += "\n"
    else:
        user_text = "No hay aliases de usuario.\n"

    final_msg = builtin_text + "\n" + user_text
    bot.reply_to(message, final_msg, parse_mode="Markdown")


@bot.message_handler()
def process_message(message):
    this_chat_id = message.chat.id
    try:
        if not message.text:
            return

        # Forzamos el texto a minúscula para chequear los startswith:
        text_lower = message.text.lower().strip()

        # Ayuda
        if text_lower in ["help", "ayuda", "menu"]:
            menu(message)
            return

        # Manejo básico de autenticación y sesión
        if text_lower == "hi":
            if this_chat_id in authorized:
                username = os.popen("whoami 2>&1").read()
                bot.send_message(this_chat_id, "Hi " + username)
            else:
                bot.send_message(this_chat_id, "Hi there")
            return

        elif text_lower.startswith("id ") or text_lower.startswith("login "):
            # Verificamos en crudo contra la password
            # (Podemos ignorar mayúsculas/minúsculas o no, depende de la preferencia)
            if remove_prefix(message.text, "id ") == PASSWORD or remove_prefix(message.text, "login ") == PASSWORD:
                authorized.append(this_chat_id)
                persist_chat_ids()
                bot.send_message(this_chat_id, "Authorized")
                return

        elif text_lower in ["exit", "quit", "logout"]:
            if this_chat_id in authorized:
                authorized.remove(this_chat_id)
                persist_chat_ids()
                bot.reply_to(message, "Logged out.")
            else:
                bot.reply_to(message, "No estás autorizado.")
            return

        elif text_lower in ["restart"]:
            authorized.clear()
            bot.reply_to(message, "Restarting bot.")
            bot.stop_polling()
            return

        elif text_lower in ["reset"]:
            bot.reply_to(message, "Saving session summary and starting a new session.")
            cmd = f"TELEGRAM_BOT_USER_ID=\"{this_chat_id}\" TELEGRAM_BOT_CHAT_ID=\"{this_chat_id}\" ./ask_ai_reset"
            print(f"{cmd} 2>&1");
            response = os.popen(cmd + " 2>&1").read()
            return

        elif text_lower in ["forget", "discard"]:
            bot.reply_to(message, "Session discarded. New session started.")
            cmd = f"TELEGRAM_BOT_USER_ID=\"{this_chat_id}\" TELEGRAM_BOT_CHAT_ID=\"{this_chat_id}\" ./ask_ai_discard"
            print(f"{cmd} 2>&1");
            response = os.popen(cmd + " 2>&1").read()
            return

        # Aquí sólo entran usuarios autorizados
        if this_chat_id in authorized:
            if text_lower in ["aliases"]:
                list_aliases(message)  # ¡Llamamos a la misma función!
                return
            # Crear/actualizar alias
            if text_lower.startswith("alias "):
                # parts en crudo
                parts = remove_prefix(message.text, "alias ").strip().split(None, 1)
                # Nota: parted a 2, aunque sea
                if len(parts) < 2:
                    bot.reply_to(message, "Uso: alias <nombre> <comando con o sin '?'>")
                    return
                alias_name = parts[0].strip()
                alias_command = parts[1].strip()

                # Validamos si alias_name está en la lista prohibida
                if alias_name.lower() in PROHIBITED_ALIAS_NAMES:
                    bot.reply_to(message, f"No se permite crear un alias con el nombre '{alias_name}'")
                    return

                # Si ya existe, conservamos la descripción
                old_description = ''
                if alias_name.lower() in aliases:
                    old_description = aliases[alias_name.lower()].get('description', '')

                aliases[alias_name.lower()] = {
                    'command': alias_command,
                    'description': old_description
                }
                save_aliases()
                bot.reply_to(message, f"Alias '{alias_name}' registrado/actualizado.")
                return

            # Describir alias existente
            if text_lower.startswith("describe alias "):
                parts = remove_prefix(message.text, "describe alias ").strip().split(None, 1)
                if len(parts) < 2:
                    bot.reply_to(message, "Uso: describe alias <nombre> <descripcion>")
                    return
                alias_name = parts[0].strip().lower()
                alias_desc = parts[1].strip()
                if alias_name not in aliases:
                    bot.reply_to(message, f"El alias '{alias_name}' no existe.")
                    return
                aliases[alias_name]['description'] = alias_desc
                save_aliases()
                bot.reply_to(message, f"Descripción del alias '{alias_name}' actualizada.")
                return

            if text_lower.startswith("load_aliases"):
                load_aliases()
                bot.reply_to(message, "Aliases cargados desde archivo.")
                return

            # Aplicamos alias si corresponde
            user_input = apply_aliases(message.text)
            user_input_lower = user_input.lower().strip()

            # Bloque para sys <comando>
            if user_input_lower.startswith("sys "):
                cmd = f"TELEGRAM_BOT_CHAT_ID={this_chat_id} " + remove_prefix(user_input, "sys ")
                response = os.popen(cmd + " 2>&1").read()
                if not response:
                    response = "Done."
                bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower.startswith("ssys "):
                cmd = f"TELEGRAM_BOT_CHAT_ID={this_chat_id} " + remove_prefix(user_input, "ssys ")
                response = os.popen(cmd + " 2>&1").read()
                if response:
                    bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower.startswith("sudo "):
                if SUDO_PASSWORD is None:
                    bot.reply_to(message, "SUDO_PASSWORD is not set.")
                    return
                cmd = f"TELEGRAM_BOT_CHAT_ID={this_chat_id} " + remove_prefix(user_input, "sudo ")
                response = os.popen(
                    "echo " + SUDO_PASSWORD + " | sudo -S -p \"\" " + cmd + " 2>&1"
                ).read()
                if not response:
                    response = "Done."
                bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower in ["reboot"]:
                if SUDO_PASSWORD is None:
                    bot.reply_to(message, "SUDO_PASSWORD is not set.")
                    return
                response = os.popen(
                    "echo " + SUDO_PASSWORD + " | sudo -S -p '' shutdown -r now 2>&1"
                ).read()
                if not response:
                    response = "Done."
                bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower in ["shutdown"]:
                if SUDO_PASSWORD is None:
                    bot.reply_to(message, "SUDO_PASSWORD is not set.")
                    return
                response = os.popen(
                    "echo " + SUDO_PASSWORD + " | sudo -S -p '' shutdown now 2>&1"
                ).read()
                if not response:
                    response = "Done."
                bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower in ["lock"]:
                if SUDO_PASSWORD is None:
                    bot.reply_to(message, "SUDO_PASSWORD is not set.")
                    return
                response = os.popen(
                    "echo " + SUDO_PASSWORD + " | sudo -S -p '' loginctl lock-sessions 2>&1"
                ).read()
                if not response:
                    response = "Done."
                bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower in ["unlock"]:
                if SUDO_PASSWORD is None:
                    bot.reply_to(message, "SUDO_PASSWORD is not set.")
                    return
                response = os.popen(
                    "echo " + SUDO_PASSWORD + " | sudo -S -p '' loginctl unlock-sessions 2>&1"
                ).read()
                if not response:
                    response = "Done."
                bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower.startswith("notify "):
                if DBUS == "None":
                    bot.reply_to(message, "DBUS_SESSION_BUS_ADDRESS is not set.")
                else:
                    response = os.popen('notify-send "'+remove_prefix(user_input, "notify ")+'" 2>&1').read()
                    if not response:
                        response = "Done."
                    bot.reply_to(message, truncate(response, 2500))

            elif user_input_lower in ["picture","photo","foto"]:
                try:
                    response = str(os.popen('rm data/foto0*.jpeg').read())
                    response = str(os.popen('export DISPLAY=:0.0;streamer -t 4 -r 2 -o data/foto00.jpeg').read())
                    photo = open("data/foto03.jpeg", "rb")
                    bot.send_photo(this_chat_id, photo)
                    if not response:
                        response = "Done."
                except Exception as e:
                    bot.reply_to(message, str(e))

            elif user_input_lower in ["screen", "screenshot", "pantalla", "captura"]:
                try:
                    if DISPLAY is None:
                        bot.reply_to(message, "DISPLAY is not set.")
                    os.popen('xhost +local: 2>&1').read()
                    # Borramos las capturas previas
                    os.popen('rm data/screen.png data/screen.jpg 2>&1').read()
                    # Tomamos la nueva captura, guardamos en data
                    os.popen('import -window root data/screen.png && convert data/screen.png data/screen.jpg 2>&1').read()
                    with open("data/screen.jpg", "rb") as screen:
                        bot.send_photo(this_chat_id, screen)
                except Exception as e:
                    bot.reply_to(message, str(e))
            else:
                # Si está autorizado pero no coincide con ningún comando, ejecutamos el script ask_ai
                response = ask_ai(message.chat.id, message.text)
                bot.send_message(message.chat.id, truncate(response, 2500))
        else:
            # Si NO está autorizado y escribe algo distinto a hi/login/etc.
            bot.reply_to(message, "Comando desconocido. Use 'help' para ver la ayuda.")

    except Exception as e:
        bot.send_message(this_chat_id, "Error: "+str(e))


# @bot.message_handler(content_types=['voice'])
# def handle_voice_message(message):
#     if message.chat.id not in authorized:
#         bot.reply_to(message, "No estás autorizado para enviar mensajes de audio.")
#         return
#
#     try:
#         # Crear la carpeta si no existe
#         audio_folder = '/tmp/telegrambot/'
#         if not os.path.exists(audio_folder):
#             os.makedirs(audio_folder)
#
#         # Obtener el archivo de audio
#         file_info = bot.get_file(message.voice.file_id)
#         file_path = file_info.file_path
#         file_url = f"https://api.telegram.org/file/bot{API_KEY}/{file_path}"
#
#         # Descargar el archivo de audio
#         response = requests.get(file_url)
#         if response.status_code == 200:
#             audio_file_path = os.path.join(audio_folder, f"{message.voice.file_id}.ogg")
#             with open(audio_file_path, 'wb') as audio_file:
#                 audio_file.write(response.content)
#             bot.reply_to(message, f"Audio guardado en {audio_file_path}")
#         else:
#             bot.reply_to(message, "Error al descargar el archivo de audio.")
#     except Exception as e:
#         bot.reply_to(message, f"Error al procesar el mensaje de audio: {str(e)}")


@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    if message.chat.id not in authorized:
        bot.reply_to(message, "No estás autorizado para enviar mensajes de audio.")
        return

    try:
        this_chat_id = message.chat.id
        # Crear la carpeta si no existe
        audio_folder = '/tmp/telegrambot/'
        if not os.path.exists(audio_folder):
            os.makedirs(audio_folder)

        # Obtener el archivo de audio
        file_info = bot.get_file(message.voice.file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{API_KEY}/{file_path}"

        # Descargar el archivo de audio
        response = requests.get(file_url)
        if response.status_code == 200:
            input_path = os.path.join(audio_folder, f"{message.voice.file_id}_original.ogg")
            output_path = os.path.join(audio_folder, f"{message.voice.file_id}.ogg")

            # Guardar el archivo original
            with open(input_path, 'wb') as audio_file:
                audio_file.write(response.content)

            # Convertir a Ogg Vorbis usando ffmpeg
            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-c:a', 'libvorbis', output_path
            ], check=True)

            # Borrar el original si querés
            os.remove(input_path)

            cmd = f"TELEGRAM_BOT_CHAT_ID={this_chat_id} ./transcribe {output_path}"
            transcription = os.popen(cmd + " 2>&1").read()
            bot.reply_to(message, f"Entendí: {transcription}")
            ai_response = ask_ai(message.chat.id, transcription)
            # bot.send_message(this_chat_id, f"{truncate(ai_response, 2500)}")
            cmd = f"TELEGRAM_BOT_CHAT_ID={this_chat_id} ./botsay \"{ai_response}\""
            botsay_response = os.popen(cmd + " 2>&1").read()

        else:
            bot.reply_to(message, "Error al descargar el archivo de audio.")
    except Exception as e:
        bot.reply_to(message, f"Error al procesar el mensaje de audio: {str(e)}")


def remove_prefix(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):]
    return text


def last_chat_ids():
    if not os.path.exists("last_admin_chat_ids"):
        return []
    with open("last_admin_chat_ids", "r") as f:
        ids_str = f.read()
        if not ids_str:
            return []
    return list(map(int, ids_str.split(',')))


def persist_chat_ids():
    with open("last_admin_chat_ids", "w") as f:
        f.write(','.join(map(str, authorized)))


def truncate(message, max_bytes):
    encoded_message = message.encode('utf-8')
    if len(encoded_message) > max_bytes:
        return encoded_message[:max_bytes].decode('utf-8', 'ignore')
    else:
        return message


def create_folder(folder):
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
            print(f"Carpeta '{folder}' creada exitosamente.")
        except Exception as e:
            print(f"Error al crear carpeta '{folder}': {str(e)}")

# Llamamos a la función para crear la carpeta 'data' si no existe
create_folder('data')

# Cargamos el último chat ID que estaba autorizado antes (si lo hubiera)
last_chat_ids_list = last_chat_ids()
authorized.extend(last_chat_ids_list)

# 1) Carga los aliases predefinidos (read-only)
load_builtin_aliases()

# 2) Cargamos los aliases del usuario
load_aliases()

# Iniciamos el bot
bot.polling()

# Actualizamos last_chat_id
last_chat_id_int = last_chat_id()
