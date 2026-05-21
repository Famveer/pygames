"""
════════════════════════════════════════════════════════════
 MÓDULO 1 — Script 04: KEYDOWN vs get_pressed
════════════════════════════════════════════════════════════

 Qué demuestra este script:
   • Dos cuadrados moviéndose hacia la derecha:
       - El AZUL usa pygame.KEYDOWN (evento, una sola vez)
       - El VERDE usa pygame.key.get_pressed() (continuo)
   • El cuadrado azul se mueve apenas un paso y se detiene.
   • El cuadrado verde se mueve fluido mientras sostenés.
   • Esta es la confusión más común en principiantes.

 Controles:
   • Mantené D: mover ambos cuadrados
   • R: resetear posiciones
   • ESC o X: cerrar

 Ejecutar: python 04_keydown_vs_getpressed.py
════════════════════════════════════════════════════════════
"""

import pygame
import sys

pygame.init()

ANCHO, ALTO = 900, 500
NEGRO    = (0,   0,   0)
BLANCO   = (255, 255, 255)
AZUL     = (50,  120, 220)
VERDE    = (50,  200, 100)
GRIS     = (60,  60,  60)
GRIS_CLR = (150, 150, 150)
AMARILLO = (255, 230, 50)
ROJO     = (220, 80,  70)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 1 — KEYDOWN vs get_pressed")
clock = pygame.time.Clock()
FPS = 60

fuente       = pygame.font.SysFont("monospace", 16)
fuente_chica = pygame.font.SysFont("monospace", 13)
fuente_grande= pygame.font.SysFont("monospace", 20, bold=True)

TAM = 50
VEL = 5
INICIO_X = 40
Y_AZUL  = 160
Y_VERDE = 290

# Posiciones iniciales
x_azul  = INICIO_X
x_verde = INICIO_X

# Contadores de frames movidos
frames_azul  = 0
frames_verde = 0
key_sostenida = False

def texto(surf, txt, pos, color=BLANCO, f=None):
    f = f or fuente
    s = f.render(txt, True, color)
    surf.blit(s, pos)

def dibujar_cuadrado(surf, x, y, color, label):
    pygame.draw.rect(surf, color, (x, y, TAM, TAM))
    pygame.draw.rect(surf, BLANCO, (x, y, TAM, TAM), 1)

def barra_progreso(surf, x, y, w, h, valor, maximo, color):
    pygame.draw.rect(surf, GRIS, (x, y, w, h))
    pct = min(valor / maximo, 1.0)
    pygame.draw.rect(surf, color, (x, y, int(w * pct), h))
    pygame.draw.rect(surf, GRIS_CLR, (x, y, w, h), 1)

MAX_X = ANCHO - TAM - 20

while True:
    # ─── INPUT ────────────────────────────────────────────────
    keydown_d = False   # Señal del evento (dispara UNA vez)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if evento.key == pygame.K_r:
                x_azul = INICIO_X
                x_verde = INICIO_X
                frames_azul = 0
                frames_verde = 0
            if evento.key == pygame.K_d:
                keydown_d = True  # Solo se activa UNA vez

    # get_pressed: activo CADA frame mientras D esté sostenida
    teclas = pygame.key.get_pressed()
    get_pressed_d = teclas[pygame.K_d]
    key_sostenida = get_pressed_d

    # ─── UPDATE ───────────────────────────────────────────────
    # Cuadrado AZUL: solo se mueve cuando llega el evento KEYDOWN
    if keydown_d and x_azul < MAX_X:
        x_azul += VEL
        frames_azul += 1

    # Cuadrado VERDE: se mueve cada frame mientras D esté presionada
    if get_pressed_d and x_verde < MAX_X:
        x_verde += VEL
        frames_verde += 1

    # ─── RENDER ───────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # Línea de inicio
    pygame.draw.line(pantalla, GRIS, (INICIO_X + TAM, 100),
                     (INICIO_X + TAM, ALTO - 80), 1)
    texto(pantalla, "inicio", (INICIO_X + TAM - 20, 85), GRIS_CLR, fuente_chica)

    # Línea de llegada
    pygame.draw.line(pantalla, GRIS, (MAX_X, 100), (MAX_X, ALTO - 80), 1)
    texto(pantalla, "meta", (MAX_X - 15, 85), GRIS_CLR, fuente_chica)

    # ── Cuadrado AZUL ────────────────────────────────────────
    label_azul = "KEYDOWN (evento)"
    color_estado = VERDE if keydown_d else ROJO
    estado_txt   = "DISPARÓ" if keydown_d else "sin evento"

    pygame.draw.rect(pantalla, (15, 20, 40), (0, Y_AZUL - 30, ANCHO, 110))
    texto(pantalla, f"AZUL — {label_azul}", (12, Y_AZUL - 26), AZUL, fuente_grande)
    texto(pantalla, f"Evento: {estado_txt}  |  frames movido: {frames_azul}  |  x: {x_azul}",
          (12, Y_AZUL - 6), GRIS_CLR, fuente_chica)

    dibujar_cuadrado(pantalla, x_azul, Y_AZUL, AZUL, "")

    barra_progreso(pantalla, INICIO_X + TAM + 2, Y_AZUL + TAM + 8,
                   MAX_X - INICIO_X - TAM - 4, 10,
                   x_azul - INICIO_X, MAX_X - INICIO_X, AZUL)

    # ── Cuadrado VERDE ───────────────────────────────────────
    label_verde = "get_pressed() (continuo)"
    estado_verde = "ACTIVO cada frame" if get_pressed_d else "inactivo"

    pygame.draw.rect(pantalla, (15, 35, 20), (0, Y_VERDE - 30, ANCHO, 110))
    texto(pantalla, f"VERDE — {label_verde}", (12, Y_VERDE - 26), VERDE, fuente_grande)
    texto(pantalla, f"Estado: {estado_verde}  |  frames movido: {frames_verde}  |  x: {x_verde}",
          (12, Y_VERDE - 6), GRIS_CLR, fuente_chica)

    dibujar_cuadrado(pantalla, x_verde, Y_VERDE, VERDE, "")

    barra_progreso(pantalla, INICIO_X + TAM + 2, Y_VERDE + TAM + 8,
                   MAX_X - INICIO_X - TAM - 4, 10,
                   x_verde - INICIO_X, MAX_X - INICIO_X, VERDE)

    # ── Indicador de tecla ───────────────────────────────────
    pygame.draw.rect(pantalla, (30, 30, 30), (0, ALTO - 80, ANCHO, 80))
    pygame.draw.line(pantalla, GRIS, (0, ALTO - 80), (ANCHO, ALTO - 80), 1)

    color_d = AMARILLO if key_sostenida else GRIS
    pygame.draw.rect(pantalla, color_d if key_sostenida else GRIS,
                     (ANCHO // 2 - 25, ALTO - 65, 50, 45),
                     0 if key_sostenida else 2)

    texto(pantalla, "D", (ANCHO // 2 - 8, ALTO - 50),
          NEGRO if key_sostenida else color_d, fuente_grande)

    instrucciones = "Mantené  D  para mover     |     R para resetear     |     ESC para salir"
    s = fuente_chica.render(instrucciones, True, GRIS_CLR)
    pantalla.blit(s, (ANCHO // 2 - s.get_width() // 2, ALTO - 18))

    # Conclusión visual cuando alguno llega a la meta
    if x_verde >= MAX_X and x_azul < MAX_X - 50:
        msg = "El VERDE llegó primero — get_pressed es mejor para movimiento continuo"
        s = fuente.render(msg, True, AMARILLO)
        pantalla.blit(s, (ANCHO // 2 - s.get_width() // 2, 45))

    fps_real = clock.get_fps()
    texto(pantalla, f"FPS: {fps_real:.0f}", (ANCHO - 80, 10), GRIS, fuente_chica)

    pygame.display.flip()
    clock.tick(FPS)
