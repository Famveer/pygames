"""
════════════════════════════════════════════════════════════
 MÓDULO 3 — Script 03: Colisiones Rect (AABB)
════════════════════════════════════════════════════════════

 Qué demuestra:
   • colliderect() — rect contra rect
   • collidepoint() — punto (mouse) dentro de rect
   • collidelist() — rect contra lista de rects
   • Visualización en tiempo real de la superposición
   • Área de intersección resaltada

 Controles:
   • Flechas: mover el cuadrado azul
   • WASD:    mover el cuadrado verde
   • Mouse:   ver collidepoint en tiempo real
   • ESC:     salir
════════════════════════════════════════════════════════════
"""

import pygame
import sys

pygame.init()

ANCHO, ALTO = 900, 620
FPS = 60
NEGRO   = (0,   0,   0)
BLANCO  = (255, 255, 255)
GRIS    = (60,  60,  60)
GRIS_CL = (140, 140, 140)
AZUL    = (50,  120, 220)
VERDE   = (50,  200, 100)
ROJO    = (220, 80,  70)
AMARILLO= (255, 220, 50)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 3 — Colisiones AABB")
clock = pygame.time.Clock()
fuente    = pygame.font.SysFont("monospace", 15)
fuente_ch = pygame.font.SysFont("monospace", 12)
fuente_gr = pygame.font.SysFont("monospace", 20, bold=True)

ZONA_JUEGO = pygame.Rect(0, 0, ANCHO, ALTO - 140)

def texto(txt, pos, color=BLANCO, f=None):
    s = (f or fuente).render(txt, True, color)
    pantalla.blit(s, pos)

# Obstáculos estáticos
obstaculos = [
    pygame.Rect(350, 150, 100, 80),
    pygame.Rect(200, 350, 80,  120),
    pygame.Rect(550, 300, 120, 70),
    pygame.Rect(700, 120, 80,  80),
]
colores_obs = [(180, 100, 50)] * len(obstaculos)

# Rectángulos móviles
rect_a = pygame.Rect(150, 200, 60, 60)   # Azul (flechas)
rect_b = pygame.Rect(620, 200, 60, 60)   # Verde (WASD)
VEL = 4

# Historial de colisiones para el log
log = []

while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

    # ── INPUT ─────────────────────────────────────────────
    t = pygame.key.get_pressed()
    if t[pygame.K_LEFT]:  rect_a.x -= VEL
    if t[pygame.K_RIGHT]: rect_a.x += VEL
    if t[pygame.K_UP]:    rect_a.y -= VEL
    if t[pygame.K_DOWN]:  rect_a.y += VEL

    if t[pygame.K_a]: rect_b.x -= VEL
    if t[pygame.K_d]: rect_b.x += VEL
    if t[pygame.K_w]: rect_b.y -= VEL
    if t[pygame.K_s]: rect_b.y += VEL

    rect_a.clamp_ip(ZONA_JUEGO)
    rect_b.clamp_ip(ZONA_JUEGO)

    mouse_pos = pygame.mouse.get_pos()

    # ── DETECCIÓN ─────────────────────────────────────────
    # 1. colliderect — A contra B
    col_ab = rect_a.colliderect(rect_b)

    # 2. collidepoint — cada rect contra el mouse
    col_a_mouse = rect_a.collidepoint(mouse_pos)
    col_b_mouse = rect_b.collidepoint(mouse_pos)

    # 3. collidelist — A contra obstáculos
    idx_obs_a = rect_a.collidelist(obstaculos)   # -1 si no colisiona
    idx_obs_b = rect_b.collidelist(obstaculos)

    # Calcular rectángulo de intersección entre A y B
    interseccion = rect_a.clip(rect_b)  # Rect vacío si no hay colisión

    # ── RENDER ────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # Cuadrícula
    for gx in range(0, ANCHO, 80):
        pygame.draw.line(pantalla, (15, 15, 15), (gx, 0), (gx, ALTO - 140))
    for gy in range(0, ALTO - 140, 80):
        pygame.draw.line(pantalla, (15, 15, 15), (0, gy), (ANCHO, gy))

    # Obstáculos
    for i, obs in enumerate(obstaculos):
        esta_col = (idx_obs_a == i or idx_obs_b == i)
        color_ob = ROJO if esta_col else (180, 100, 50)
        pygame.draw.rect(pantalla, color_ob, obs)
        pygame.draw.rect(pantalla, BLANCO, obs, 1)
        txt = fuente_ch.render(f"obs[{i}]", True, BLANCO)
        pantalla.blit(txt, (obs.centerx - txt.get_width()//2,
                             obs.centery - txt.get_height()//2))

    # Área de intersección A-B
    if interseccion.width > 0 and interseccion.height > 0:
        surf_inter = pygame.Surface((interseccion.w, interseccion.h), pygame.SRCALPHA)
        surf_inter.fill((255, 255, 0, 90))
        pantalla.blit(surf_inter, interseccion.topleft)
        txt = fuente_ch.render(f"inter={interseccion.w}x{interseccion.h}", True, AMARILLO)
        pantalla.blit(txt, (interseccion.centerx - txt.get_width()//2,
                             interseccion.centery - txt.get_height()//2))

    # Rect A
    color_a = ROJO if (col_ab or idx_obs_a >= 0) else AZUL
    pygame.draw.rect(pantalla, color_a, rect_a)
    pygame.draw.rect(pantalla, BLANCO, rect_a, 2)
    texto("A", (rect_a.centerx - 5, rect_a.centery - 8), BLANCO)
    if col_a_mouse:
        pygame.draw.rect(pantalla, AMARILLO, rect_a, 3)

    # Rect B
    color_b = ROJO if (col_ab or idx_obs_b >= 0) else VERDE
    pygame.draw.rect(pantalla, color_b, rect_b)
    pygame.draw.rect(pantalla, BLANCO, rect_b, 2)
    texto("B", (rect_b.centerx - 5, rect_b.centery - 8), BLANCO)
    if col_b_mouse:
        pygame.draw.rect(pantalla, AMARILLO, rect_b, 3)

    # Cruz en la posición del mouse
    mx, my = mouse_pos
    if ZONA_JUEGO.collidepoint(mouse_pos):
        pygame.draw.line(pantalla, (60, 60, 60), (mx - 10, my), (mx + 10, my), 1)
        pygame.draw.line(pantalla, (60, 60, 60), (mx, my - 10), (mx, my + 10), 1)

    # ── Panel inferior ────────────────────────────────────
    py = ALTO - 140
    pygame.draw.rect(pantalla, (12, 12, 12), (0, py, ANCHO, 140))
    pygame.draw.line(pantalla, GRIS, (0, py), (ANCHO, py), 1)

    col_color = ROJO if col_ab else VERDE
    col_txt   = "COLISIÓN" if col_ab else "sin colisión"
    texto(f"A ↔ B: {col_txt}", (20, py + 10), col_color, fuente_gr)

    # Columna izquierda
    lineas_a = [
        f"rect_a = ({rect_a.x}, {rect_a.y}, {rect_a.w}, {rect_a.h})",
        f"colliderect(B)   → {col_ab}",
        f"collidepoint(mouse) → {col_a_mouse}",
        f"collidelist(obs) → índice {idx_obs_a} {'✓' if idx_obs_a >= 0 else ''}",
    ]
    for i, l in enumerate(lineas_a):
        c = ROJO if ('True' in l or '✓' in l) else GRIS_CL
        texto(l, (20, py + 48 + i * 20), c, fuente_ch)

    # Columna derecha
    lineas_b = [
        f"rect_b = ({rect_b.x}, {rect_b.y}, {rect_b.w}, {rect_b.h})",
        f"colliderect(A)   → {col_ab}",
        f"collidepoint(mouse) → {col_b_mouse}",
        f"collidelist(obs) → índice {idx_obs_b} {'✓' if idx_obs_b >= 0 else ''}",
    ]
    for i, l in enumerate(lineas_b):
        c = ROJO if ('True' in l or '✓' in l) else GRIS_CL
        texto(l, (ANCHO // 2 + 20, py + 48 + i * 20), c, fuente_ch)

    texto("Flechas: mover A  |  WASD: mover B  |  Mouse: ver collidepoint  |  ESC: salir",
          (20, ALTO - 18), GRIS, fuente_ch)

    pygame.display.flip()
    clock.tick(FPS)
