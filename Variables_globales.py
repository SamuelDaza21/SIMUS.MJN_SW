import os
import pygame
pygame.init()
carpeta_img=os.path.join("IMG")
BLANCO = (255, 255, 255)
COLOR_TEXTO = (255, 255, 255)
TEXTO = (255, 255, 255)
NEGRO = (0, 0, 0)  # Color negro.
COLOR_FONDO= (135, 206, 235)  # Azul cielo para el fondo.
COLOR_FONDO_B= (204, 130, 76)  # #cc824c
FONDO_BOTON= (204, 130, 76)
COLOR_BORDE = (221, 162, 105)  # #dda269
BORDE_BOTON = (221, 162, 105)  # #dda269
AZUL= (100, 149, 237)
CAMBIO_COLOR_SOBRE_DE = (230, 160, 100)
COLORES = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 105, 180), (0, 255, 255), (0, 0, 0)]
BARRA = (100, 200, 100)  # Verde
pantalla=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
ANCHO,ALTO=pantalla.get_size()
ancho,alto=ANCHO,ALTO
SOMBRA= (180, 180, 220)
VERDE = (0, 255, 0)
ROJO = (255, 0, 0)
Fuente=pygame.font.SysFont('comicsans', 30)
HOVER=(221, 162, 105)
RELOJ=pygame.time.Clock()
SAVE_BG=FONDO_BOTON
SAVE_BORDER=COLOR_BORDE
