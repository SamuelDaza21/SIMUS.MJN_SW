import pygame
import sys
import os
import subprocess
import platform
from Variables_globales import *
from ManejoCamara import ManejoCamara


class SistemaTTS:
    """Gestor de Text-to-Speech usando comandos del sistema"""

    def __init__(self):
        self.sistema = platform.system()
        self.comando_tts = self.detectar_comando_tts()

    def detectar_comando_tts(self):
        """Detectar el comando de TTS apropiado para el sistema"""
        if self.sistema == "Darwin":  # macOS
            return "say"
        elif self.sistema == "Linux":
            # Verificar si espeak está instalado
            try:
                subprocess.run(["which", "espeak"], check=True, capture_output=True)
                return "espeak"
            except:
                try:
                    subprocess.run(["which", "spd-say"], check=True, capture_output=True)
                    return "spd-say"
                except:
                    return None
        elif self.sistema == "Windows":
            # Usar PowerShell para TTS en Windows
            return "powershell"
        return None

    def decir_texto(self, texto):
        """Decir texto usando el comando del sistema"""
        if not self.comando_tts:
            print("No se encontró un comando de TTS compatible en este sistema")
            return False

        try:
            if self.comando_tts == "say":  # macOS
                subprocess.Popen(["say", texto])
            elif self.comando_tts == "espeak":  # Linux con espeak
                subprocess.Popen(["espeak", "-v", "es", texto])
            elif self.comando_tts == "spd-say":  # Linux con speech-dispatcher
                subprocess.Popen(["spd-say", texto])
            elif self.comando_tts == "powershell":  # Windows
                # Escapar comillas para PowerShell
                texto_escapado = texto.replace('"', '`"')
                comando = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{texto_escapado}")'
                subprocess.Popen(["powershell", "-Command", comando])
            return True
        except Exception as e:
            print(f"Error ejecutando comando de TTS: {e}")
            return False


class Inicio:
    def __init__(self, camara=None, music_manager=None, cambiar_pantalla=None):
        # Configuración de la pantalla
        self.ANCHO, self.ALTO = ANCHO, ALTO
        self.pantalla = pantalla
        pygame.display.set_caption("SIMUS.MJN - Comunicación Aumentativa")

        # Colores
        self.COLOR_FONDO = (244, 202, 161)  # #f4caa1
        self.COLOR_BARRA_INFERIOR = (221, 162, 105)  # #dda269
        self.COLOR_BLANCO = (255, 255, 255)
        self.COLOR_AZUL = (12, 0, 255)  # #0c00ff

        # Colores de los cuadros
        self.COLOR_SOCIALES = (213, 247, 206)  # #d5f7ce
        self.COLOR_NECESIDADES = (245, 210, 210)  # #f5d2d2
        self.COLOR_EMOCIONES = (254, 255, 195)  # #feffc3
        self.COLOR_CONTROL = (197, 201, 254)  # #c5c9fe
        self.COLOR_PERSONAS = (245, 219, 253)  # #f5dbfd
        self.COLOR_ACTIVIDADES = (255, 221, 174)  # #ffddae

        # Inicializar cámara
        self.camara = camara if camara else ManejoCamara(ancho=self.ANCHO, alto=self.ALTO, modo_ocular=False)

        # Gestión de música
        self.music_manager = music_manager

        # Callback para cambiar de pantalla
        self.cambiar_pantalla = cambiar_pantalla

        # Control de clic
        self.control_clic = False

        # Inicializar gestor de TTS del sistema
        self.tts_sistema = SistemaTTS()

        # Cargar imágenes
        self.cargar_iconos()

        # Crear elementos de la interfaz
        self.cuadros = self.crear_cuadros()
        self.botones_barra = self.crear_botones_barra()
        self.botones_comunicacion = self.crear_botones_comunicacion()

    def decir_texto(self, texto):
        """Decir texto usando el sistema de TTS del sistema operativo"""
        self.tts_sistema.decir_texto(texto)

    def cargar_iconos(self):
        """Cargar y preparar los iconos de la aplicación"""
        self.iconos = {}
        iconos_info = [
            # Botones de barra inferior
            {"nombre": "instrucciones", "archivo": "icono-12.png", "texto": "Instrucciones"},
            {"nombre": "configuracion", "archivo": "icono-10.png", "texto": "Configuración"},
            {"nombre": "salir", "archivo": "icono-26.png", "texto": "Salir"},
            {"nombre": "info", "archivo": "icono-14.png", "texto": "Información"},
            {"nombre": "jugar", "archivo": "icono-3.png", "texto": "Jugar"},
            {"nombre": "inicio", "archivo": "icono-24.png", "texto": "Inicio"},

            # Iconos de comunicación - Sociales
            {"nombre": "hola", "archivo": "icono-adios.png", "texto": "Hola"},
            {"nombre": "adios", "archivo": "icono-adios-2.png", "texto": "Adiós"},
            {"nombre": "gracias", "archivo": "icono-gracias.png", "texto": "Gracias"},
            {"nombre": "porfavor", "archivo": "icono-porfavor.png", "texto": "Por favor"},
            {"nombre": "si", "archivo": "icono-si.png", "texto": "Sí"},
            {"nombre": "no", "archivo": "icono-no.png", "texto": "No"},

            # Iconos de comunicación - Necesidades
            {"nombre": "hambre", "archivo": "icono-hambre.png", "texto": "Hambre"},
            {"nombre": "incomodo", "archivo": "icono-incomodo.png", "texto": "Incomodo"},
            {"nombre": "bano", "archivo": "icono-ba-o.png", "texto": "Baño"},
            {"nombre": "sed", "archivo": "icono-SED.png", "texto": "Sed"},
            {"nombre": "cansado", "archivo": "icono-cansado.png", "texto": "Cansado"},
            {"nombre": "dolor", "archivo": "icono-dolor.png", "texto": "Dolor"},

            # Iconos de comunicación - Emociones
            {"nombre": "feliz", "archivo": "icono-18.png", "texto": "Feliz"},
            {"nombre": "triste", "archivo": "icono-9.png", "texto": "Triste"},
            {"nombre": "enojado", "archivo": "icono-2.png", "texto": "Enojado"},
            {"nombre": "miedo", "archivo": "icono-20.png", "texto": "Miedo"},
            {"nombre": "nervioso", "archivo": "icono-5.png", "texto": "Nervioso"},
            {"nombre": "calma", "archivo": "icono-16.png", "texto": "Calma"},

            # Iconos de comunicación - Control
            {"nombre": "ayuda", "archivo": "icono-8.png", "texto": "Ayuda"},
            {"nombre": "no-quiero", "archivo": "icono-15.png", "texto": "No quiero"},
            {"nombre": "mas", "archivo": "icono-28.png", "texto": "Más"},
            {"nombre": "quiero", "archivo": "icono-4.png", "texto": "Quiero"},
            {"nombre": "basta", "archivo": "icono-25.png", "texto": "Basta"},
            {"nombre": "espera", "archivo": "cono.png", "texto": "Espera"},

            # Iconos de comunicación - Personas
            {"nombre": "mama", "archivo": "icono-11.png", "texto": "Mamá"},
            {"nombre": "enfermera", "archivo": "icono-6.png", "texto": "Enfermera"},
            {"nombre": "hermano", "archivo": "icono-23.png", "texto": "Hermano"},
            {"nombre": "papa", "archivo": "icono-21.png", "texto": "Papá"},
            {"nombre": "maestra", "archivo": "icono-19.png", "texto": "Maestra"},
            {"nombre": "amigo", "archivo": "icono-22.png", "texto": "Amigo"},

            # Iconos de comunicación - Actividades
            {"nombre": "jugar-act", "archivo": "icono-13.png", "texto": "Jugar"},
            {"nombre": "salir-act", "archivo": "icono-7.png", "texto": "Salir"},
            {"nombre": "musica", "archivo": "image.png", "texto": "Música"},
            {"nombre": "television", "archivo": "icono-27.png", "texto": "Televisión"},
            {"nombre": "dormir", "archivo": "icono.png", "texto": "Dormir"},
            {"nombre": "libro", "archivo": "icono-17.png", "texto": "Libro"},
        ]

        for icono_info in iconos_info:
            try:
                ruta = os.path.join("img", icono_info["archivo"])
                if os.path.exists(ruta):
                    imagen = pygame.image.load(ruta)
                    self.iconos[icono_info["nombre"]] = {
                        "imagen": pygame.transform.scale(imagen, (70, 70)),
                        "texto": icono_info["texto"]
                    }
                else:
                    # Crear placeholder si no existe la imagen
                    superficie = pygame.Surface((70, 70), pygame.SRCALPHA)
                    pygame.draw.circle(superficie, (100, 100, 200), (35, 35), 30)
                    self.iconos[icono_info["nombre"]] = {
                        "imagen": superficie,
                        "texto": icono_info["texto"]
                    }
            except Exception as e:
                print(f"Error cargando icono {icono_info['nombre']}: {e}")
                # Crear placeholder en caso de error
                superficie = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(superficie, (200, 100, 100), (35, 35), 30)
                self.iconos[icono_info["nombre"]] = {
                    "imagen": superficie,
                    "texto": icono_info["texto"]
                }

    def crear_cuadros(self):
        """Crear los cuadros de diálogo de la interfaz"""
        cuadros = [
            {"rect": pygame.Rect(29, 26, 400, 400), "color": self.COLOR_SOCIALES, "titulo": "SOCIALES"},
            {"rect": pygame.Rect(29 + 472, 26, 400, 400), "color": self.COLOR_NECESIDADES, "titulo": "NECESIDADES"},
            {"rect": pygame.Rect(29 + 944, 26, 400, 400), "color": self.COLOR_EMOCIONES, "titulo": "EMOCIONES"},
            {"rect": pygame.Rect(29, 26 + 436, 400, 400), "color": self.COLOR_CONTROL, "titulo": "CONTROL"},
            {"rect": pygame.Rect(29 + 472, 26 + 436, 400, 400), "color": self.COLOR_PERSONAS, "titulo": "PERSONAS"},
            {"rect": pygame.Rect(29 + 944, 26 + 436, 400, 400), "color": self.COLOR_ACTIVIDADES,
             "titulo": "ACTIVIDADES"}
        ]
        return cuadros

    def crear_botones_barra(self):
        """Crear los botones de la barra inferior"""
        botones = [
            {"rect": pygame.Rect(107, self.ALTO - 119 + 10, 120, 100), "icono": "instrucciones",
             "accion": self.ir_instrucciones},
            {"rect": pygame.Rect(342, self.ALTO - 119 + 10, 120, 100), "icono": "configuracion",
             "accion": self.ir_configuracion},
            {"rect": pygame.Rect(588, self.ALTO - 119 + 10, 120, 100), "icono": "inicio", "accion": self.ir_inicio},
            {"rect": pygame.Rect(833, self.ALTO - 119 + 10, 120, 100), "icono": "jugar", "accion": self.ir_juegos},
            {"rect": pygame.Rect(1076, self.ALTO - 119 + 10, 120, 100), "icono": "info", "accion": self.mostrar_info},
            {"rect": pygame.Rect(1319, self.ALTO - 119 + 10, 120, 100), "icono": "salir", "accion": self.salir}
        ]
        return botones

    def crear_botones_comunicacion(self):
        """Crear los botones de comunicación aumentativa para todas las categorías"""
        botones = []

        # Configuración de la cuadrícula para cada categoría
        categorias = [
            {
                "nombre": "sociales",
                "posicion": (29, 26),
                "botones": ["hola", "adios", "gracias", "porfavor", "si", "no"]
            },
            {
                "nombre": "necesidades",
                "posicion": (29 + 472, 26),
                "botones": ["hambre", "incomodo", "bano", "sed", "cansado", "dolor"]
            },
            {
                "nombre": "emociones",
                "posicion": (29 + 944, 26),
                "botones": ["feliz", "triste", "enojado", "miedo", "nervioso", "calma"]
            },
            {
                "nombre": "control",
                "posicion": (29, 26 + 436),
                "botones": ["ayuda", "no-quiero", "mas", "quiero", "basta", "espera"]
            },
            {
                "nombre": "personas",
                "posicion": (29 + 472, 26 + 436),
                "botones": ["mama", "enfermera", "hermano", "papa", "maestra", "amigo"]
            },
            {
                "nombre": "actividades",
                "posicion": (29 + 944, 26 + 436),
                "botones": ["jugar-act", "salir-act", "musica", "television", "dormir", "libro"]
            }
        ]

        # Crear botones para cada categoría
        for categoria in categorias:
            base_x, base_y = categoria["posicion"]
            botones_categoria = categoria["botones"]

            for i, nombre_icono in enumerate(botones_categoria):
                fila = i // 3  # 3 columnas
                columna = i % 3  # 3 filas

                x = base_x + 20 + columna * 120
                y = base_y + 80 + fila * 120
                rect = pygame.Rect(x, y, 100, 100)

                if nombre_icono in self.iconos:
                    botones.append({
                        "rect": rect,
                        "icono": nombre_icono,
                        "texto": self.iconos[nombre_icono]["texto"]
                    })

        return botones

    def ir_instrucciones(self):
        if self.cambiar_pantalla:
            self.cambiar_pantalla("instrucciones")

    def ir_configuracion(self):
        if self.cambiar_pantalla:
            self.cambiar_pantalla("configuracion")

    def ir_juegos(self):
        if self.cambiar_pantalla:
            self.cambiar_pantalla("juegos")

    def ir_inicio(self):
        if self.cambiar_pantalla:
            self.cambiar_pantalla("inicio")

    def mostrar_info(self):
        self.decir_texto("SIMUS.MJN es un sistema de comunicación aumentativa y alternativa")

    def salir(self):
        pygame.quit()
        sys.exit()

    def dibujar_cuadro(self, cuadro):
        """Dibuja un cuadro de comunicación"""
        # Dibujar cuadro con bordes redondeados
        pygame.draw.rect(self.pantalla, cuadro["color"], cuadro["rect"], border_radius=20)

        # Dibujar borde azul
        pygame.draw.rect(self.pantalla, self.COLOR_AZUL, cuadro["rect"], width=3, border_radius=20)

        # Dibujar título
        if "titulo" in cuadro:
            fuente = pygame.font.SysFont("Arial", 36, bold=True)
            texto = fuente.render(cuadro["titulo"], True, NEGRO)
            texto_rect = texto.get_rect(center=(cuadro["rect"].centerx, cuadro["rect"].y + 30))
            self.pantalla.blit(texto, texto_rect)

    def dibujar_boton_barra(self, boton_info, mouse_pos):
        """Dibuja un botón de la barra inferior"""
        boton_rect = boton_info["rect"]
        icono_data = self.iconos.get(boton_info["icono"], None)

        if not icono_data:
            return

        # Cambiar color si el mouse está encima
        color = (200, 150, 100) if boton_rect.collidepoint(mouse_pos) else self.COLOR_BARRA_INFERIOR

        # Dibujar fondo del botón
        pygame.draw.rect(self.pantalla, color, boton_rect, border_radius=10)

        # Dibujar sombra
        pygame.draw.rect(self.pantalla, (0, 0, 0, 100),
                         pygame.Rect(boton_rect.x, boton_rect.y + 4, boton_rect.width, boton_rect.height),
                         border_radius=10, width=0)

        # Dibujar icono centrado
        icono_rect = icono_data["imagen"].get_rect(center=boton_rect.center)
        self.pantalla.blit(icono_data["imagen"], icono_rect)

    def dibujar_boton_comunicacion(self, boton_info, mouse_pos):
        """Dibuja un botón de comunicación"""
        boton_rect = boton_info["rect"]
        icono_data = self.iconos.get(boton_info["icono"], None)

        if not icono_data:
            return

        # Cambiar color si el mouse está encima
        color = (200, 200, 200) if boton_rect.collidepoint(mouse_pos) else BLANCO

        # Dibujar fondo del botón
        pygame.draw.rect(self.pantalla, color, boton_rect, border_radius=15)

        # Dibujar borde
        pygame.draw.rect(self.pantalla, NEGRO, boton_rect, width=2, border_radius=15)

        # Dibujar icono centrado
        icono_rect = icono_data["imagen"].get_rect(center=boton_rect.center)
        self.pantalla.blit(icono_data["imagen"], icono_rect)

        # Dibujar texto debajo del icono
        if "texto" in boton_info:
            fuente = pygame.font.SysFont("Arial", 16)
            texto = fuente.render(boton_info["texto"], True, NEGRO)
            texto_rect = texto.get_rect(center=(boton_rect.centerx, boton_rect.bottom + 15))
            self.pantalla.blit(texto, texto_rect)

    def ejecutar(self):
        """Bucle principal de la aplicación"""
        reloj = pygame.time.Clock()
        ejecutando = True

        while ejecutando:
            # Obtener posición del cursor y estado del clic desde la cámara
            try:
                cursor_x, cursor_y, clic_camara = self.camara.obtener_posicion_y_clic()
                if clic_camara and not self.control_clic:
                    clic_activo = True
                    self.control_clic = True
                elif not clic_camara:
                    self.control_clic = False
                    clic_activo = False
            except Exception as e:
                print(f"Error cámara: {e}")
                cursor_x, cursor_y = pygame.mouse.get_pos()
                clic_activo = pygame.mouse.get_pressed()[0]

            # Manejar eventos
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        ejecutando = False

            # Dibujar fondo
            self.pantalla.fill(self.COLOR_FONDO)

            # Dibujar cuadro principal blanco con borde azul
            cuadro_principal = pygame.Rect(29, 26, 1383, 879)
            pygame.draw.rect(self.pantalla, self.COLOR_BLANCO, cuadro_principal, border_radius=58)
            pygame.draw.rect(self.pantalla, self.COLOR_AZUL, cuadro_principal, width=3, border_radius=58)

            # Dibujar cuadros de comunicación
            for cuadro in self.cuadros:
                self.dibujar_cuadro(cuadro)

            # Dibujar botones de comunicación
            for boton in self.botones_comunicacion:
                self.dibujar_boton_comunicacion(boton, (cursor_x, cursor_y))

                # Manejar clics en botones de comunicación
                if boton["rect"].collidepoint(cursor_x, cursor_y) and clic_activo:
                    if "texto" in boton:
                        self.decir_texto(boton["texto"])
                    pygame.time.delay(200)  # Pequeña pausa para feedback

            # Dibujar barra inferior
            barra_inferior = pygame.Rect(0, self.ALTO - 119, self.ANCHO, 119)
            pygame.draw.rect(self.pantalla, self.COLOR_BARRA_INFERIOR, barra_inferior)
            pygame.draw.rect(self.pantalla, NEGRO, barra_inferior, width=1)

            # Dibujar botones de la barra
            for boton in self.botones_barra:
                self.dibujar_boton_barra(boton, (cursor_x, cursor_y))

                # Manejar clics en botones de la barra
                if boton["rect"].collidepoint(cursor_x, cursor_y) and clic_activo:
                    boton["accion"]()
                    pygame.time.delay(200)  # Pequeña pausa para feedback

            # Dibujar cursor de la cámara
            try:
                x_final, y_final = self.camara.dibujar_puntero(self.pantalla, cursor_x, cursor_y)
                pygame.draw.circle(self.pantalla, ROJO, (x_final, y_final), 8, 2)
            except Exception as e:
                print(f"Error dibujando cursor: {e}")
                pygame.draw.circle(self.pantalla, ROJO, (cursor_x, cursor_y), 10, 2)
                pygame.draw.line(self.pantalla, ROJO, (cursor_x - 15, cursor_y), (cursor_x + 15, cursor_y), 2)
                pygame.draw.line(self.pantalla, ROJO, (cursor_x, cursor_y - 15), (cursor_x, cursor_y + 15), 2)

            # Actualizar pantalla
            pygame.display.flip()
            reloj.tick(60)

        # Liberar recursos al salir
        self.camara.liberar_recursos()


# Ejecutar la aplicación
if __name__ == "__main__":
    inicio = Inicio()
    inicio.ejecutar()
    pygame.quit()
    sys.exit()