import whisper
import sys
import os
import warnings

def main():
    if len(sys.argv) != 2:
        print("Uso: python transcribe.py <ruta_al_audio>")
        sys.exit(1)

    audio_path = sys.argv[1]

    if not os.path.exists(audio_path):
        print(f"Error: el archivo '{audio_path}' no existe.")
        sys.exit(1)

    # Ignorar el warning específico sobre FP16 en CPU
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

    # print("Cargando modelo...")
    model = whisper.load_model("medium")  # Cambiá a "small", "medium", etc. si querés más precisión

    # print("Transcribiendo audio...")
    result = model.transcribe(audio_path)

    # print("\n--- TRANSCRIPCIÓN ---\n")
    print(result["text"])

if __name__ == "__main__":
    main()
