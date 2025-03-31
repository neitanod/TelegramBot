# playaudio.py
import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # Hide stupid welcome message
import pygame

if len(sys.argv) < 2:
    print("Uso: playaudio.py archivo.mp3|wav|ogg")
    sys.exit(1)

archivo = sys.argv[1]

if not os.path.isfile(archivo):
    print(f"Archivo no encontrado: {archivo}")
    sys.exit(1)

pygame.mixer.init()
pygame.mixer.music.load(archivo)
pygame.mixer.music.play()

#print(f"Reproduciendo: {archivo}")
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(1)
