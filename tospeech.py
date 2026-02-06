#!/usr/bin/env python3
import argparse
import json
import os
import sys
import tempfile
import traceback
import uuid

def ensure_output_directory():
    output_dir = "/tmp/tospeech"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def generate_unique_filename(extension):
    return f"{uuid.uuid4()}.{extension}"

def speak_with_edge_tts(text, args):
    import asyncio
    import edge_tts

    # voice = args.get("voice", "es-AR-ElenaNeural")
    # voice = args.get("voice", "es-UY-ValentinaNeural")  # Voz femenina de Uruguay
    voice = args.get("voice", "es-UY-MateoNeural")  # Voz masculina de Uruguay
    #rate = args.get("rate", "+10%")
    rate = args.get("rate", "+0%")
    pitch = args.get("pitch", "+0%")
    output_dir = ensure_output_directory()
    output = os.path.join(output_dir, generate_unique_filename("mp3"))

    async def synthesize():
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await communicate.save(output)
    asyncio.run(synthesize())
    return output

def speak_with_gtts(text, args):
    from gtts import gTTS

    lang = args.get("lang", "es")
    slow = args.get("slow", False)
    output_dir = ensure_output_directory()
    output = os.path.join(output_dir, generate_unique_filename("mp3"))

    tts = gTTS(text=text, lang=lang, slow=slow)
    tts.save(output)
    return output

def speak_with_pyttsx3(text, args):
    import pyttsx3

    output_dir = ensure_output_directory()
    output = os.path.join(output_dir, generate_unique_filename("wav"))
    voice_name = args.get("voice", None)
    engine = pyttsx3.init()
    if voice_name:
        voices = engine.getProperty("voices")
        for v in voices:
            if voice_name.lower() in v.name.lower():
                engine.setProperty("voice", v.id)
                break
    engine.save_to_file(text, output)
    engine.runAndWait()
    return output

def speak_with_espeak(text, args):
    voice = args.get("voice", "es")
    pitch = str(args.get("pitch", 45))
    speed = str(args.get("speed", 150))
    output_dir = ensure_output_directory()
    output = os.path.join(output_dir, generate_unique_filename("wav"))
    os.system(f'espeak "{text}" -v {voice} -p {pitch} -s {speed} --stdout > "{output}"')
    return output

ENGINES = {
    "edge-tts": speak_with_edge_tts,
    "gtts": speak_with_gtts,
    "pyttsx3": speak_with_pyttsx3,
    "espeak": speak_with_espeak,
}

def main():
    parser = argparse.ArgumentParser(description="Síntesis de voz desde la línea de comandos.")
    parser.add_argument("--message", help="Texto a sintetizar", type=str)
    parser.add_argument("--output", help="Archivo de audio a generar", type=str)
    parser.add_argument("--engine", help="Forzar un engine específico", choices=list(ENGINES.keys()))
    parser.add_argument("--engine-args", help="Parámetros específicos para el engine (JSON)", type=str)
    parser.add_argument("--test-engines", help="Probar todos los engines y generar un archivo por cada uno", action="store_true")
    args = parser.parse_args()

    if not args.message and not args.test_engines:
        # print("Debes especificar un mensaje con --message o usar --test-engines.")
        sys.exit(1)

    engine_args = {}
    if args.engine_args:
        try:
            engine_args = json.loads(args.engine_args)
        except Exception as e:
            # print("Error al parsear --engine-args:", e)
            sys.exit(1)

    if args.test_engines:
        # print("Probando todos los engines disponibles...\n")
        for engine_name, engine_func in ENGINES.items():
            try:
                # print(f"🔄 Probando: {engine_name}...")
                filename = f"test_{engine_name}.wav" if engine_name == "pyttsx3" or engine_name == "espeak" else f"test_{engine_name}.mp3"
                outpath = engine_func("Prueba de voz con el engine " + engine_name, {"output": filename})
                if os.path.exists(outpath):
                    pass
                # else:
                #     pass
            except Exception as e:
                pass
                # print(f"❌ {engine_name} falló:\n{traceback.format_exc()}")
            # print(filename)
            print(outpath)
            return

    engines_to_try = [args.engine] if args.engine else ENGINES.keys()
    for engine_name in engines_to_try:
        engine_func = ENGINES.get(engine_name)
        if not engine_func:
            continue
        try:
            # print(f"Usando engine: {engine_name}")
            outpath = engine_func(args.message, engine_args)
            # print(f"✅ Audio generado: {outpath}")
            print(outpath)
            return
        except Exception as e:
            pass
            # print(f"❌ Falló con {engine_name}: {str(e)}")
            continue

    pass
    # print("Ningún engine pudo sintetizar el mensaje.")

if __name__ == "__main__":
    main()
