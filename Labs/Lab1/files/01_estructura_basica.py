"""
════════════════════════════════════════════════════════════
 MÓDULO 1 — Script 01: Estructura básica del Game Loop
════════════════════════════════════════════════════════════

 Qué demuestra este script:
   • Inicialización de pygame
   • Las tres fases del Game Loop: Input → Update → Render
   • Control de FPS con Clock
   • Movimiento de un objeto con teclas de flechas
   • Limitar el movimiento dentro de los bordes de pantalla

 Controles:
   • Flechas: mover el cuadrado
   • ESC o X: cerrar

 Ejecutar: python 01_estructura_basica.py
════════════════════════════════════════════════════════════
"""

import pygame
import sys

# ── BLOQUE 1: Inicialización ──────────────────────────────────
pygame.init()

ANCHO, ALTO = 800, 600
FPS = 60

# Colores como tuplas (R, G, B)
NEGRO  = (0,   0,   0)
BLANCO = (255, 255, 255)
AZUL   = (50,  120, 220)
GRIS   = (40,  40,  40)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 1 — Game Loop básico")
clock = pygame.time.Clock()

fuente = pygame.font.SysFont("monospace", 16)

# ── BLOQUE 2: Estado inicial del juego ───────────────────────
x = ANCHO // 2 - 20   # Centrado horizontalmente
y = ALTO  // 2 - 20   # Centrado verticalmente
TAM = 40
velocidad = 4

# ── BLOQUE 3: Game Loop ───────────────────────────────────────
while True:

    # ─── FASE 1: INPUT ────────────────────────────────────────
    # La cola de eventos DEBE vaciarse cada frame.
    # Sin esto, la ventana se congela.
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    # get_pressed() devuelve estado de todas las teclas AHORA.
    # Ideal para movimiento fluido (se consulta cada frame).
    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_LEFT]:  x -= velocidad
    if teclas[pygame.K_RIGHT]: x += velocidad
    if teclas[pygame.K_UP]:    y -= velocidad
    if teclas[pygame.K_DOWN]:  y += velocidad

    # ─── FASE 2: UPDATE ───────────────────────────────────────
    # Limitar el cuadrado dentro de los bordes de pantalla
    x = max(0, min(x, ANCHO - TAM))
    y = max(0, min(y, ALTO  - TAM))

    # ─── FASE 3: RENDER ───────────────────────────────────────
    # Paso 1: borrar la pantalla (sin esto quedan estelas)
    pantalla.fill(NEGRO)

    # Dibujar guía de bordes
    pygame.draw.rect(pantalla, GRIS, (0, 0, ANCHO, ALTO), 2)

    # Paso 2: dibujar objetos
    pygame.draw.rect(pantalla, AZUL, (x, y, TAM, TAM))

    # Mostrar información en pantalla
    fps_real = clock.get_fps()
    info_lines = [
        f"FPS: {fps_real:.0f}",
        f"Pos: ({x}, {y})",
        f"Flechas: mover  |  ESC: salir",
    ]
    for i, linea in enumerate(info_lines):
        surf = fuente.render(linea, True, BLANCO)
        pantalla.blit(surf, (10, 10 + i * 22))

    # Paso 3: mostrar el frame (double buffering)
    pygame.display.flip()

    # ─── CONTROL DE FPS ───────────────────────────────────────
    # clock.tick(FPS) duerme el proceso los ms necesarios
    # para mantener exactamente 60 iteraciones por segundo.
    clock.tick(FPS)
