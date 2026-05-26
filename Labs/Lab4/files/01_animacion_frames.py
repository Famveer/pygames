"""
════════════════════════════════════════════════════════════
 MÓDULO 4 — Script 05: Animación por frames y Spritesheet
════════════════════════════════════════════════════════════

 Qué demuestra:
   • Generar un spritesheet programáticamente
   • Extraer frames con subsurface()
   • Timer de animación por frames (contador)
   • Timer de animación por milisegundos (más preciso)
   • Ajustar velocidad de animación en tiempo real
   • Ver el spritesheet completo

 Controles:
   • ARRIBA/ABAJO: aumentar/reducir velocidad de animación
   • 1 / 2: cambiar entre timer por frames y por ms
   • ESC: salir
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math

pygame.init()

ANCHO, ALTO = 900, 600
FPS = 60
NEGRO   = (0,   0,   0)
BLANCO  = (255, 255, 255)
GRIS    = (60,  60,  60)
GRIS_CL = (150, 150, 150)
AZUL    = (50,  120, 220)
AMARILLO= (255, 220, 50)
VERDE   = (50,  200, 100)
ROJO    = (220, 80,  70)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 4 — Animación por frames")
clock = pygame.time.Clock()
fuente    = pygame.font.SysFont("monospace", 15)
fuente_ch = pygame.font.SysFont("monospace", 12)
fuente_gr = pygame.font.SysFont("monospace", 18, bold=True)

def texto(txt, pos, color=BLANCO, f=None):
    s = (f or fuente).render(txt, True, color)
    pantalla.blit(s, pos)


# ════════════════════════════════════════════════════════
# GENERAR UN SPRITESHEET PROGRAMÁTICAMENTE
# En un juego real, cargarías: pygame.image.load("sheet.png")
# ════════════════════════════════════════════════════════

FRAME_W = 64
FRAME_H = 64
N_FRAMES = 8

# Crear la superficie del spritesheet (1 fila, N columnas)
spritesheet = pygame.Surface((FRAME_W * N_FRAMES, FRAME_H), pygame.SRCALPHA)

def dibujar_personaje(surf, x, y, frame, total_frames):
    """Dibuja un personaje simple en el frame dado."""
    t = frame / total_frames  # 0.0 a 1.0

    cx = x + FRAME_W // 2
    cy = y + FRAME_H // 2

    # Cuerpo (elipse que respira)
    escala = 1.0 + 0.06 * math.sin(t * math.pi * 2)
    cuerpo_w = int(22 * escala)
    cuerpo_h = int(28 * escala)
    pygame.draw.ellipse(surf, (50, 120, 220),
                        (cx - cuerpo_w, cy - cuerpo_h//2,
                         cuerpo_w * 2, cuerpo_h))

    # Cabeza (sube y baja levemente)
    head_y = cy - cuerpo_h//2 - 16 + int(2 * math.sin(t * math.pi * 2))
    pygame.draw.circle(surf, (255, 200, 150), (cx, head_y), 14)

    # Ojos
    ojo_abierto = not (0.45 < t < 0.55)  # Parpadeo
    if ojo_abierto:
        pygame.draw.circle(surf, NEGRO, (cx - 5, head_y - 2), 3)
        pygame.draw.circle(surf, NEGRO, (cx + 5, head_y - 2), 3)
        pygame.draw.circle(surf, BLANCO, (cx - 4, head_y - 3), 1)
        pygame.draw.circle(surf, BLANCO, (cx + 6, head_y - 3), 1)
    else:
        # Ojos cerrados
        pygame.draw.line(surf, NEGRO, (cx - 8, head_y - 2), (cx - 2, head_y - 2), 2)
        pygame.draw.line(surf, NEGRO, (cx + 2, head_y - 2), (cx + 8, head_y - 2), 2)

    # Brazos (oscilan)
    ang_brazo = 0.3 * math.sin(t * math.pi * 2)
    for lado in [-1, 1]:
        bx = cx + lado * cuerpo_w
        by = cy - 4
        ex = bx + lado * int(16 * math.cos(ang_brazo * lado))
        ey = by + int(16 * math.sin(abs(ang_brazo)))
        pygame.draw.line(surf, (50, 120, 220), (bx, by), (ex, ey), 4)

    # Piernas (caminando)
    ang_pierna = 0.5 * math.sin(t * math.pi * 2)
    for lado in [-1, 1]:
        px = cx + lado * 8
        py = cy + cuerpo_h // 2 - 4
        ex = px + lado * int(10 * math.sin(ang_pierna * lado))
        ey = py + 18
        pygame.draw.line(surf, (80, 80, 160), (px, py), (ex, ey), 5)
        pygame.draw.circle(surf, (80, 80, 160), (ex, ey), 4)  # Pie


# Dibujar todos los frames en el spritesheet
for i in range(N_FRAMES):
    dibujar_personaje(spritesheet, i * FRAME_W, 0, i, N_FRAMES)

# Extraer frames individuales con subsurface()
frames = []
for i in range(N_FRAMES):
    rect_frame = pygame.Rect(i * FRAME_W, 0, FRAME_W, FRAME_H)
    frame = spritesheet.subsurface(rect_frame).copy()
    frames.append(frame)


# ════════════════════════════════════════════════════════
# DOS ANIMADORES: por frames vs por milisegundos
# ════════════════════════════════════════════════════════

# Animador 1 — contador de frames
frame_a = 0
contador_a = 0
vel_frames = 6   # cambiar frame cada N frames del juego

# Animador 2 — milisegundos
frame_b = 0
ultimo_ms = pygame.time.get_ticks()
dur_ms = 100    # ms por frame

modo = 1   # 1 = ambos, solo para comparar


while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if ev.key == pygame.K_UP:
                vel_frames = max(1, vel_frames - 1)
                dur_ms = max(16, dur_ms - 10)
            if ev.key == pygame.K_DOWN:
                vel_frames = min(60, vel_frames + 1)
                dur_ms = min(500, dur_ms + 10)

    # ── TIMER 1: por contador de frames ───────────────────
    contador_a += 1
    if contador_a >= vel_frames:
        contador_a = 0
        frame_a = (frame_a + 1) % N_FRAMES

    # ── TIMER 2: por milisegundos ─────────────────────────
    ahora = pygame.time.get_ticks()
    if ahora - ultimo_ms >= dur_ms:
        ultimo_ms = ahora
        frame_b = (frame_b + 1) % N_FRAMES

    # ── RENDER ────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # ─ Mostrar spritesheet completo ───────────────────────
    sheet_x, sheet_y = 40, 30
    escala_sheet = 2
    for i in range(N_FRAMES):
        fx = sheet_x + i * (FRAME_W * escala_sheet + 4)
        # Fondo del frame
        pygame.draw.rect(pantalla, (20, 20, 20),
                         (fx - 2, sheet_y - 2,
                          FRAME_W * escala_sheet + 4,
                          FRAME_H * escala_sheet + 4))
        # Frame escalado
        surf_sc = pygame.transform.scale(frames[i],
                                         (FRAME_W * escala_sheet,
                                          FRAME_H * escala_sheet))
        pantalla.blit(surf_sc, (fx, sheet_y))
        # Resaltar frame activo A
        if i == frame_a:
            pygame.draw.rect(pantalla, VERDE,
                             (fx - 2, sheet_y - 2,
                              FRAME_W * escala_sheet + 4,
                              FRAME_H * escala_sheet + 4), 2)
        # Número de frame
        txt = fuente_ch.render(str(i), True, GRIS_CL)
        pantalla.blit(txt, (fx + FRAME_W - 10, sheet_y + FRAME_H * escala_sheet + 2))

    texto("Spritesheet completo (subsurface extrae cada frame):",
          (sheet_x, sheet_y - 22), GRIS_CL, fuente_ch)

    # ─ Animador 1 — por frames ───────────────────────────
    y1 = 220
    pygame.draw.rect(pantalla, (15, 25, 15), (20, y1 - 10, 420, 160))
    pygame.draw.rect(pantalla, VERDE, (20, y1 - 10, 420, 160), 1)
    texto("TIMER 1 — Contador de frames", (30, y1 - 6), VERDE, fuente_gr)

    # Personaje animado grande
    surf_a = pygame.transform.scale(frames[frame_a], (128, 128))
    pantalla.blit(surf_a, (30, y1 + 25))

    texto(f"vel_frames = {vel_frames}  (frames del juego por frame de anim)",
          (170, y1 + 20), GRIS_CL, fuente_ch)
    texto(f"contador   = {contador_a} / {vel_frames}", (170, y1 + 40), BLANCO, fuente_ch)
    texto(f"frame_a    = {frame_a}", (170, y1 + 60), AMARILLO, fuente_ch)
    fps_anim_a = FPS / vel_frames
    texto(f"FPS animación ≈ {fps_anim_a:.1f}", (170, y1 + 80), GRIS_CL, fuente_ch)
    texto("Problema: si el juego baja a 30 FPS,", (170, y1 + 100), ROJO, fuente_ch)
    texto("la animación también se hace más lenta.", (170, y1 + 116), ROJO, fuente_ch)

    # ─ Animador 2 — por milisegundos ─────────────────────
    y2 = 220
    pygame.draw.rect(pantalla, (15, 15, 25), (460, y2 - 10, 420, 160))
    pygame.draw.rect(pantalla, AZUL, (460, y2 - 10, 420, 160), 1)
    texto("TIMER 2 — Milisegundos (recomendado)", (470, y2 - 6), AZUL, fuente_gr)

    surf_b = pygame.transform.scale(frames[frame_b], (128, 128))
    pantalla.blit(surf_b, (470, y2 + 25))

    texto(f"dur_ms   = {dur_ms} ms por frame",
          (610, y2 + 20), GRIS_CL, fuente_ch)
    texto(f"último   = {ultimo_ms} ms", (610, y2 + 40), BLANCO, fuente_ch)
    texto(f"frame_b  = {frame_b}", (610, y2 + 60), AMARILLO, fuente_ch)
    fps_anim_b = 1000 / dur_ms
    texto(f"FPS animación ≈ {fps_anim_b:.1f}", (610, y2 + 80), GRIS_CL, fuente_ch)
    texto("Ventaja: independiente de los FPS del juego.", (610, y2 + 100), VERDE, fuente_ch)
    texto("Si el juego se lentifica, la anim sigue igual.", (610, y2 + 116), VERDE, fuente_ch)

    # ─ Panel inferior ─────────────────────────────────────
    py = ALTO - 90
    pygame.draw.rect(pantalla, (12, 12, 12), (0, py, ANCHO, 90))
    pygame.draw.line(pantalla, GRIS, (0, py), (ANCHO, py), 1)

    texto(f"vel_frames: {vel_frames} frames/cambio    dur_ms: {dur_ms} ms/frame",
          (20, py + 10), BLANCO)
    barra_w = 300
    # Barra vel_frames
    pct_f = vel_frames / 60
    pygame.draw.rect(pantalla, GRIS, (20, py + 35, barra_w, 14))
    pygame.draw.rect(pantalla, VERDE, (20, py + 35, int(barra_w * pct_f), 14))
    texto("Timer 1 (lentitud)", (20, py + 52), VERDE, fuente_ch)
    # Barra dur_ms
    pct_m = dur_ms / 500
    pygame.draw.rect(pantalla, GRIS, (350, py + 35, barra_w, 14))
    pygame.draw.rect(pantalla, AZUL, (350, py + 35, int(barra_w * pct_m), 14))
    texto("Timer 2 (ms por frame)", (350, py + 52), AZUL, fuente_ch)

    texto("↑↓: ajustar velocidad  |  ESC: salir",
          (700, py + 35), GRIS, fuente_ch)
    texto(f"FPS juego: {clock.get_fps():.0f}", (800, py + 70), GRIS_CL, fuente_ch)

    pygame.display.flip()
    clock.tick(FPS)
