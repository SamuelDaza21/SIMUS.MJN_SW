import cv2
import mediapipe as mp
import pygame
import math
import sys
import time
import numpy as np
from collections import deque
from Variables_globales import *


class ManejoCamara:
    def __init__(self, ancho=1620, alto=900, usocam=None, modo_ocular=False):
        self.ancho = ancho
        self.alto = alto
        self.usocam = usocam
        self.modo_ocular = modo_ocular
        self.clic_sostenido = False
        self.tiempo_inicio_clic = 0
        self.tiempo_ultimo_parpadeo = 0
        self.duracion_clic_sostenido = 0.5  # 500ms de clic sostenido
        self.parpadeo_detectado = False

        # Inicializar cámara
        self.camara = self._inicializar_camara()

        # Inicializar detección de manos
        self.mp_manos = mp.solutions.hands
        self.manos = self.mp_manos.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # Inicializar detección de rostro y ojos
        self.mp_rostro = mp.solutions.face_mesh
        self.rostro = self.mp_rostro.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Variables de estado
        self.cursor_x = self.ancho // 2
        self.cursor_y = self.alto // 2
        self.clic_activo = False
        self.inactividad = 0
        self.umbral_clic = 0.02

        # Para suavizado del movimiento
        self.suavizado = 0.3

        # Control ocular - EAR (Relación de Aspecto del Ojo)
        self.parpadeo_activo = False
        self.ultimo_parpadeo = 0
        self.UMBRAL_EAR = 0.21
        self.TIEMPO_PARPADEO = 0.5

        # Índices de landmarks para EAR (Relación de Aspecto del Ojo)
        self.INDICES_OJO_IZQUIERDO = [33, 160, 158, 133, 153, 144]
        self.INDICES_OJO_DERECHO = [362, 385, 387, 263, 373, 380]

        # Para estabilización del EAR
        self.historial_ear = deque(maxlen=5)
        self.ear_suavizado = 0

        # Para el área restringida del puntero
        self.area_ancho = self.ancho * 0.8
        self.area_alto = self.alto * 0.8

        # Calibración y sensibilidad
        self.calibrado = False
        self.rango_cabeza_x = [0.3, 0.7]  # Rango inicial estimado
        self.rango_cabeza_y = [0.3, 0.7]  # Rango inicial estimado
        self.sensibilidad = 0.5  # Factor de sensibilidad
        self.centro_cabeza = [0.5, 0.5]  # Posición central de la cabeza

    def _inicializar_camara(self):
        """Inicializa y configura la cámara"""
        if self.usocam is not None:
            camara = cv2.VideoCapture(self.usocam)
        else:
            camara = self._detectar_camara_disponible()

        if not camara.isOpened():
            raise RuntimeError("No se pudo abrir la cámara")

        camara.set(cv2.CAP_PROP_FRAME_WIDTH, self.ancho)
        camara.set(cv2.CAP_PROP_FRAME_HEIGHT, self.alto)

        return camara

    def _detectar_camara_disponible(self, max_camaras=5):
        """Detecta la primera cámara disponible"""
        for i in range(max_camaras):
            camara = cv2.VideoCapture(i)
            if camara.isOpened():
                print(f"✅ Cámara encontrada en índice {i}")
                return camara
            camara.release()
        raise RuntimeError("No se encontró ninguna cámara disponible")

    def calibrar(self, duracion=3):
        """Calibra el rango de movimiento de la cabeza"""
        print("🔧 Calibrando... Por favor, mueve la cabeza en todas direcciones")

        tiempo_inicio = time.time()
        rangos_x = []
        rangos_y = []

        while time.time() - tiempo_inicio < duracion:
            ret, marco = self.camara.read()
            if not ret:
                continue

            marco_rgb = cv2.cvtColor(marco, cv2.COLOR_BGR2RGB)
            resultados = self.rostro.process(marco_rgb)

            if resultados.multi_face_landmarks:
                landmarks = resultados.multi_face_landmarks[0]
                nariz = landmarks.landmark[1]

                rangos_x.append(nariz.x)
                rangos_y.append(nariz.y)

            time.sleep(0.1)

        if rangos_x and rangos_y:
            self.rango_cabeza_x = [min(rangos_x), max(rangos_x)]
            self.rango_cabeza_y = [min(rangos_y), max(rangos_y)]
            self.centro_cabeza = [np.mean(rangos_x), np.mean(rangos_y)]
            self.calibrado = True
            print(f"✅ Calibración completada. Rango X: {self.rango_cabeza_x}, Rango Y: {self.rango_cabeza_y}")
        else:
            print("⚠️ No se detectó rostro durante la calibración. Usando valores por defecto.")

    def _calcular_ear(self, landmarks, indices):
        """Calcula la Relación de Aspecto del Ojo (EAR) para un ojo"""
        puntos = [landmarks.landmark[i] for i in indices]

        vertical1 = math.sqrt((puntos[1].x - puntos[5].x) ** 2 + (puntos[1].y - puntos[5].y) ** 2)
        vertical2 = math.sqrt((puntos[2].x - puntos[4].x) ** 2 + (puntos[2].y - puntos[4].y) ** 2)

        horizontal = math.sqrt((puntos[0].x - puntos[3].x) ** 2 + (puntos[0].y - puntos[3].y) ** 2)

        if horizontal == 0:
            return 0.0

        ear = (vertical1 + vertical2) / (2.0 * horizontal)
        return ear

    def _detectar_parpadeo_ear(self, landmarks):
        """Detecta parpadeos usando la Relación de Aspecto del Ojo"""
        ear_izquierdo = self._calcular_ear(landmarks, self.INDICES_OJO_IZQUIERDO)
        ear_derecho = self._calcular_ear(landmarks, self.INDICES_OJO_DERECHO)

        ear = (ear_izquierdo + ear_derecho) / 2.0

        self.historial_ear.append(ear)
        self.ear_suavizado = sum(self.historial_ear) / len(self.historial_ear) if self.historial_ear else ear

        tiempo_actual = time.time()
        parpadeo_actual = self.ear_suavizado < self.UMBRAL_EAR

        # Detectar inicio de parpadeo
        if parpadeo_actual and not self.parpadeo_detectado:
            self.parpadeo_detectado = True
            self.tiempo_inicio_clic = tiempo_actual
            self.clic_sostenido = True
            return True

        # Detectar fin de parpadeo
        elif not parpadeo_actual and self.parpadeo_detectado:
            self.parpadeo_detectado = False
            self.tiempo_ultimo_parpadeo = tiempo_actual

            # Mantener clic activo por un tiempo adicional
            tiempo_parpadeo = tiempo_actual - self.tiempo_inicio_clic
            if tiempo_parpadeo < 0.3:  # Parpadeo muy rápido
                self.clic_sostenido = False
            # Para parpadeos normales, el clic se mantiene hasta el tiempo programado

        # Controlar la duración del clic sostenido
        if self.clic_sostenido and (tiempo_actual - self.tiempo_inicio_clic) > self.duracion_clic_sostenido:
            self.clic_sostenido = False

        return self.clic_sostenido

    def _mapear_posicion(self, x, y):
        """Mapea la posición de la cabeza a las coordenadas de la pantalla"""
        if not self.calibrado:
            # Usar valores por defecto si no está calibrado
            rango_x = [0.3, 0.7]
            rango_y = [0.3, 0.7]
            centro_x = 0.5
            centro_y = 0.5
        else:
            rango_x = self.rango_cabeza_x
            rango_y = self.rango_cabeza_y
            centro_x = self.centro_cabeza[0]
            centro_y = self.centro_cabeza[1]

        # Calcular desviación desde el centro (normalizada entre -1 y 1)
        desviacion_x = (x - centro_x) / (rango_x[1] - rango_x[0]) * 2
        desviacion_y = (y - centro_y) / (rango_y[1] - rango_y[0]) * 2

        # Aplicar sensibilidad
        desviacion_x *= self.sensibilidad
        desviacion_y *= self.sensibilidad

        # Mapear a coordenadas de pantalla (INVERTIR EJE X con signo negativo)
        x_virtual = int(self.ancho * 0.5 - desviacion_x * self.ancho * 0.5)  # Cambio aquí: signo negativo
        y_virtual = int(self.alto * 0.5 + desviacion_y * self.alto * 0.5)  # Eje Y sin cambios
        # Limitar a los bordes de la pantalla
        x_virtual = max(0, min(self.ancho, x_virtual))
        y_virtual = max(0, min(self.alto, y_virtual))

        return x_virtual, y_virtual

    def _obtener_posicion_manos(self, marco_rgb):
        """Obtiene posición usando las manos"""
        resultados = self.manos.process(marco_rgb)
        clic_activo = False

        if resultados.multi_hand_landmarks:
            self.inactividad = 0
            landmarks = resultados.multi_hand_landmarks[0]

            indice = landmarks.landmark[8]
            pulgar = landmarks.landmark[4]

            x_promedio = (pulgar.x + indice.x) / 2
            y_promedio = (pulgar.y + indice.y) / 2

            x_virtual = int((1 - x_promedio) * self.ancho)
            y_virtual = int(y_promedio * self.alto)

            self.cursor_x = int(self.cursor_x * (1 - self.suavizado) + x_virtual * self.suavizado)
            self.cursor_y = int(self.cursor_y * (1 - self.suavizado) + y_virtual * self.suavizado)

            distancia = math.sqrt((indice.x - pulgar.x) ** 2 + (indice.y - pulgar.y) ** 2)
            clic_activo = distancia < self.umbral_clic
        else:
            self.inactividad += 1

        return self.cursor_x, self.cursor_y, clic_activo

    def _obtener_posicion_ojos(self, marco_rgb):
        """Obtiene posición usando los ojos"""
        resultados = self.rostro.process(marco_rgb)
        clic_activo = self.clic_sostenido  # Usar el estado de clic sostenido

        if resultados.multi_face_landmarks:
            self.inactividad = 0
            landmarks = resultados.multi_face_landmarks[0]

            nariz = landmarks.landmark[1]

            # Mapear la posición de la nariz a coordenadas de pantalla
            x_virtual, y_virtual = self._mapear_posicion(nariz.x, nariz.y)

            # Suavizar el movimiento
            self.cursor_x = int(self.cursor_x * (1 - self.suavizado) + x_virtual * self.suavizado)
            self.cursor_y = int(self.cursor_y * (1 - self.suavizado) + y_virtual * self.suavizado)

            # Actualizar detección de parpadeo (pero no cambiar clic_activo directamente)
            self._detectar_parpadeo_ear(landmarks)

        else:
            self.inactividad += 1
            # Si no se detecta rostro, desactivar clic sostenido después de un tiempo
            if time.time() - self.tiempo_ultimo_parpadeo > 1.0:
                self.clic_sostenido = False
                self.parpadeo_detectado = False

        return self.cursor_x, self.cursor_y, clic_activo

    def resetear_clic(self):
        """Fuerza el reset del estado de clic"""
        self.clic_sostenido = False
        self.parpadeo_detectado = False
        self.tiempo_inicio_clic = 0

    def obtener_posicion_y_clic(self):
        """Obtiene la posición del cursor y estado del clic"""
        ret, marco = self.camara.read()
        if not ret:
            return self.cursor_x, self.cursor_y, False

        marco_rgb = cv2.cvtColor(marco, cv2.COLOR_BGR2RGB)

        if self.modo_ocular:
            x, y, clic = self._obtener_posicion_ojos(marco_rgb)

            # Para debug: mostrar estado del clic
            if hasattr(self, 'debug') and self.debug:
                print(f"CLIC: {clic}, Sostenido: {self.clic_sostenido}, Parpadeo: {self.parpadeo_detectado}")

            return x, y, clic
        else:
            return self._obtener_posicion_manos(marco_rgb)

    def ajustar_sensibilidad(self, factor):
        """Ajusta la sensibilidad del movimiento ocular"""
        self.sensibilidad = max(0.5, min(5.0, self.sensibilidad * factor))
        print(f"🔧 Sensibilidad ajustada a: {self.sensibilidad:.2f}")

    def cambiar_modo(self):
        """Cambia entre modo mano y modo ocular"""
        self.modo_ocular = not self.modo_ocular
        modo = "OCULAR" if self.modo_ocular else "MANOS"
        print(f"🔁 Modo cambiado a: {modo}")

        # Calibrar automáticamente al cambiar a modo ocular
        if self.modo_ocular and not self.calibrado:
            self.calibrar()

        return self.modo_ocular

    def dibujar_puntero(self, pantalla, x, y):
        """Dibuja el puntero en la pantalla"""
        izquierda = (self.ancho - self.area_ancho) // 2
        derecha = izquierda + self.area_ancho
        arriba = (self.alto - self.area_alto) // 2
        abajo = arriba + self.area_alto

        x_restringido = max(0, min(x, ancho))
        y_restringido = max(0, min(y, alto))

        color = (0, 255, 255) if self.modo_ocular else (0, 255, 0)
        tamaño = 20
        grosor = 4

        pygame.draw.line(pantalla, color,
                         (x_restringido - tamaño, y_restringido),
                         (x_restringido + tamaño, y_restringido), grosor)
        pygame.draw.line(pantalla, color,
                         (x_restringido, y_restringido - tamaño),
                         (x_restringido, y_restringido + tamaño), grosor)

        pygame.draw.circle(pantalla, color, (x_restringido, y_restringido), tamaño, 2)

        return x_restringido, y_restringido

    def mostrar_estado(self, pantalla, fuente, x, y, clic, inactividad):
        """Muestra información de estado en pantalla"""
        texto_coords = fuente.render(f"X: {x} Y: {y}", True, BLANCO)
        pantalla.blit(texto_coords, (10, 10))

        estado_clic = "CLIC ACTIVADO" if clic else "CLIC INACTIVO"
        color_clic = VERDE if clic else ROJO
        texto_clic = fuente.render(estado_clic, True, color_clic)
        pantalla.blit(texto_clic, (10, 50))

        modo = "OJOS" if self.modo_ocular else "MANOS"
        texto_modo = fuente.render(f"Modo: {modo}", True, (255, 255, 0))
        pantalla.blit(texto_modo, (10, 90))

        texto_inact = fuente.render(f"Inactividad: {inactividad}", True, BLANCO)
        pantalla.blit(texto_inact, (10, 130))

        if self.modo_ocular:
            texto_ear = fuente.render(f"EAR: {self.ear_suavizado:.3f}", True, BLANCO)
            pantalla.blit(texto_ear, (10, 170))

            texto_sens = fuente.render(f"Sensibilidad: {self.sensibilidad:.2f}", True, BLANCO)
            pantalla.blit(texto_sens, (10, 210))

            calibrado = "SI" if self.calibrado else "NO"
            texto_cal = fuente.render(f"Calibrado: {calibrado}", True, BLANCO)
            pantalla.blit(texto_cal, (10, 250))

    def liberar_recursos(self):
        """Libera todos los recursos"""
        if hasattr(self, 'manos') and self.manos:
            self.manos.close()
        if hasattr(self, 'rostro') and self.rostro:
            self.rostro.close()
        if hasattr(self, 'camara') and self.camara.isOpened():
            self.camara.release()


# Función principal de prueba
def main():
    pygame.init()

    ANCHO, ALTO = 1620, 900
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Control por Gestos - Seguimiento de Manos/Ojos")

    fuente = pygame.font.SysFont(None, 36)

    try:
        manejador = ManejoCamara(ancho=ANCHO, alto=ALTO, modo_ocular=True)
        print("✅ Cámara y detección inicializadas correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")
        pygame.quit()
        sys.exit()

    reloj = pygame.time.Clock()
    ejecutando = True

    print("🚀 Control por gestos activado. Presiona ESC para salir.")
    print("👆 Mueve tu mano frente a la cámara o tu cabeza para modo ocular")
    print("🤏 Junta pulgar e índice para hacer clic o parpadea en modo ocular")
    print("M: Cambiar entre modos")
    print("C: Calibrar modo ocular")
    print("+/-: Ajustar sensibilidad")

    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_m:
                    manejador.cambiar_modo()
                elif evento.key == pygame.K_c:
                    manejador.calibrar()
                elif evento.key == pygame.K_PLUS or evento.key == pygame.K_KP_PLUS:
                    manejador.ajustar_sensibilidad(1.2)
                elif evento.key == pygame.K_MINUS or evento.key == pygame.K_KP_MINUS:
                    manejador.ajustar_sensibilidad(0.8)

        pantalla.fill((50, 50, 50))

        try:
            x, y, clic = manejador.obtener_posicion_y_clic()
            x_final, y_final = manejador.dibujar_puntero(pantalla, x, y)
            manejador.mostrar_estado(pantalla, fuente, x_final, y_final, clic, manejador.inactividad)

        except Exception as e:
            print(f"Error durante la ejecución: {e}")

        pygame.display.flip()
        reloj.tick(30)

    manejador.liberar_recursos()
    pygame.quit()
    print("👋 Programa terminado correctamente")


if __name__ == "__main__":
    main()