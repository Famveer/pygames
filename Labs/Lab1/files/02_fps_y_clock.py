"""
════════════════════════════════════════════════════════════
 MÓDULO 1 — Script 02: FPS y el Clock
════════════════════════════════════════════════════════════

 Qué demuestra este script:
   • Dos cuadrados moviéndose a la misma velocidad LÓGICA
     pero con distintos FPS objetivo
   • Por qué sin Clock la velocidad dependería del hardware
   • FPS counter en tiempo real
   • Cambiar FPS con teclas para ver el efecto

 Controles:
   • ARRIBA / ABAJO: aumentar / reducir FPS objetivo
   • R: resetear a 60 FPS
   • ESC o X: cerrar

 Ejecutar: python 02_fps_y_clock.py
════════════════════════════════════════════════════════════
"""

import pygame
import sys

pygame.init()

ANCHO, ALTO = 800, 600
NEGRO   = (0,   0,   0)
BLANCO  = (255, 255, 255)
AZUL    = (50,  120, 220)
VERDE   = (50,  200, 100)
GRIS    = (80,  80,  80)
AMARILLO= (255, 230, 50)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 1 — FPS y Clock")
clock = pygame.time.Clock()

fuente_grande = pygame.font.SysFont("monospace", 22, bold=True)
fuente        = pygame.font.SysFont("monospace", 16)
fuente_chica  = pygame.font.SysFont("monospace", 13)

fps_objetivo = 60

# Cuadrado que rebota
x, y = 100, ALTO // 2 - 25
vel_x = 3
TAM = 50

# Historial de FPS para graficar
historial_fps = []
MAX_HIST = 200

def texto(surf, txt, pos, color=BLANCO, f=None):
    f = f or fuente
    s = f.render(txt, True, color)
    surf.blit(s, pos)

while True:
    # ─── INPUT ────────────────────────────────────────────────
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if evento.key == pygame.K_UP:
                fps_objetivo = min(fps_objetivo + 10, 360)
            if evento.key == pygame.K_DOWN:
                fps_objetivo = max(fps_objetivo - 10, 5)
            if evento.key == pygame.K_r:
                fps_objetivo = 60

    # ─── UPDATE ───────────────────────────────────────────────
    x += vel_x
    if x <= 0 or x >= ANCHO - TAM:
        vel_x *= -1
        x = max(0, min(x, ANCHO - TAM))

    fps_real = clock.get_fps()  # FPS real
    historial_fps.append(fps_real)
    if len(historial_fps) > MAX_HIST:
        historial_fps.pop(0)

    # ─── RENDER ───────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # Cuadrado rebotando
    pygame.draw.rect(pantalla, AZUL, (x, y, TAM, TAM))
    pygame.draw.rect(pantalla, BLANCO, (x, y, TAM, TAM), 1)

    # Panel de información
    pygame.draw.rect(pantalla, (20, 20, 20), (0, 0, ANCHO, 100))
    pygame.draw.line(pantalla, GRIS, (0, 100), (ANCHO, 100), 1)

    texto(pantalla, f"FPS objetivo: {fps_objetivo}", (20, 15), AMARILLO, fuente_grande)
    texto(pantalla, f"FPS real:     {fps_real:.1f}", (20, 45), VERDE, fuente_grande)
    texto(pantalla, "↑↓: cambiar FPS  |  R: resetear a 60  |  ESC: salir",
          (20, 78), GRIS, fuente_chica)

    # Velocidad teórica del cuadrado
    px_por_segundo = vel_x * fps_real
    texto(pantalla, f"Velocidad: {abs(vel_x)} px/frame = {abs(px_por_segundo):.0f} px/seg",
          (ANCHO // 2, 15), BLANCO, fuente_chica)
    texto(pantalla, "Sin Clock, este número variaría según el hardware.",
          (ANCHO // 2, 35), GRIS, fuente_chica)
    texto(pantalla, "Con Clock, la velocidad LÓGICA es constante.",
          (ANCHO // 2, 55), VERDE, fuente_chica)

    # Minigrafico de FPS
    if len(historial_fps) > 1:
        graf_x = 20
        graf_y = 130
        graf_w = ANCHO - 40
        graf_h = 80
        pygame.draw.rect(pantalla, (15, 15, 15), (graf_x, graf_y, graf_w, graf_h))
        pygame.draw.rect(pantalla, GRIS, (graf_x, graf_y, graf_w, graf_h), 1)
        texto(pantalla, "Historial de FPS", (graf_x + 4, graf_y + 2), GRIS, fuente_chica)

        max_fps = max(max(historial_fps), 1) # max del historico
        puntos = []
        for i, f in enumerate(historial_fps):
            px = graf_x + int(i * graf_w / MAX_HIST) # 0, 1, 2 
            py = graf_y + graf_h - int(f / max_fps * (graf_h - 10)) - 2
            puntos.append((px, py))
        if len(puntos) > 1:
            pygame.draw.lines(pantalla, VERDE, False, puntos, 1)

        # Línea objetivo
        ly = graf_y + graf_h - int(fps_objetivo / max_fps * (graf_h - 10)) - 2
        pygame.draw.line(pantalla, AMARILLO, (graf_x, ly), (graf_x + graf_w, ly), 1)
        texto(pantalla, f"obj: {fps_objetivo}", (graf_x + graf_w - 60, ly - 14),
              AMARILLO, fuente_chica)

    # Nota explicativa
    y_nota = ALTO - 70
    notas = [
        "clock.tick(N) duerme el proceso los ms necesarios para mantener N FPS.",
        f"A {fps_objetivo} FPS, cada frame dura {1000/fps_objetivo:.1f} ms.",
        "El cuadrado usa velocidad fija en px/frame — sin Clock, movería más rápido en PCs más potentes.",
    ]
    for i, n in enumerate(notas):
        texto(pantalla, n, (20, y_nota + i * 18), GRIS, fuente_chica)

    pygame.display.flip()
    clock.tick(fps_objetivo)
