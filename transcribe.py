import whisper
import sys
import os
import warnings

MODELS = [
    ("tiny", "39 MB", "Baja", "Multilingüe", "Rápido, baja calidad"),
    ("base", "74 MB", "Media-baja", "Multilingüe", "Liviano, general"),
    ("small", "244 MB", "Media", "Multilingüe", "Equilibrio entre calidad y velocidad"),
    ("medium", "769 MB", "Alta", "Multilingüe", "Buena calidad"),
    ("large", "1550 MB", "Muy alta", "Multilingüe", "Alta precisión, más lento"),
    ("large-v2", "1550 MB", "Muy alta +", "Multilingüe", "Más estable"),
    ("large-v3", "1550 MB", "Muy alta ++", "Multilingüe", "Última versión clásica"),
    ("large-v3-turbo", "1550 MB", "Muy alta ++", "Multilingüe", "Más rápida, igual precisión"),
]

def print_help():
    print("Uso: python transcribe.py <ruta_al_audio> [opciones]\n")
    print("Opciones:")
    print("  --plain               Muestra el texto sin formato")
    print("  --srt                 Muestra salida en formato .srt (subtítulos)")
    print("  --model <nombre>      Especifica el modelo Whisper a usar")
    print("  --help                Muestra esta ayuda\n")
    print("Modelos disponibles:\n")
    print(f"{'Modelo':<15}{'Tamaño':<10}{'Precisión':<15}{'Idioma':<15}{'Uso recomendado'}")
    print("-" * 70)
    for name, size, prec, lang, use in MODELS:
        print(f"{name:<15}{size:<10}{prec:<15}{lang:<15}{use}")
    print()

def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    # argumentos
    audio_path = sys.argv[1]
    mode = "--plain" if "--plain" in sys.argv else "--srt" if "--srt" in sys.argv else "default"
    model_name = "large-v3-turbo"

    if "--model" in sys.argv:
        try:
            model_name = sys.argv[sys.argv.index("--model") + 1]
        except IndexError:
            print("Error: falta el nombre del modelo después de --model.")
            sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"Error: el archivo '{audio_path}' no existe.")
        sys.exit(1)

    # advertencias de FP16
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

    print(f"Cargando modelo '{model_name}'...")
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)

    if mode == "--plain":
        print(result["text"])

    elif mode == "--srt":
        # parámetros de agrupación
        max_gap = 2.0         # segundos máximos entre segmentos para unir
        max_duration = 10.0   # duración máxima de un bloque combinado (segundos)
        max_chars_per_line = 80  # caracteres máximos por línea

        def fmt(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t * 1000) % 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        def split_text(text, max_chars):
            """Divide texto largo en líneas de máximo max_chars caracteres"""
            if len(text) <= max_chars:
                return text

            lines = []
            words = text.split()
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            # Limitar a máximo 2 líneas
            if len(lines) > 2:
                return "\n".join(lines[:2])
            return "\n".join(lines)

        merged = []
        current = {"start": None, "end": None, "text": ""}

        for seg in result["segments"]:
            start, end, text = seg["start"], seg["end"], seg["text"].strip()

            if current["start"] is None:
                current = {"start": start, "end": end, "text": text}
            else:
                # unir si el espacio es corto y no se pasa de max_duration
                if (start - current["end"] <= max_gap) and (end - current["start"] <= max_duration):
                    current["end"] = end
                    current["text"] += " " + text
                else:
                    merged.append(current)
                    current = {"start": start, "end": end, "text": text}
        if current["start"] is not None:
            merged.append(current)

        # imprimir subtítulos combinados
        for i, seg in enumerate(merged, start=1):
            print(f"{i}")
            print(f"{fmt(seg['start'])} --> {fmt(seg['end'])}")
            print(f"{split_text(seg['text'].strip(), max_chars_per_line)}\n")

    else:
        for segment in result["segments"]:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            print(f"[{start:6.2f} → {end:6.2f}] {text}")

if __name__ == "__main__":
    main()

