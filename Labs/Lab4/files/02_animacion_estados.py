"""
════════════════════════════════════════════════════════════
 MÓDULO 4 — Script 06: Máquina de estados de animación
════════════════════════════════════════════════════════════

 Qué demuestra:
   • Máquina de estados completa: idle / walk / jump / attack
   • Transiciones automáticas entre estados
   • Reinicio del frame al cambiar de estado
   • Flip horizontal según dirección
   • Visualización del estado y frame actual en pantalla
   • Plataformas simples con física básica (gravedad)

 Controles:
   • A / D:     mover izquierda / derecha
   • ESPACIO:   saltar
   • F:         atacar
   • ESC:       salir
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math

pygame.init()

ANCHO, ALTO = 900, 620
FPS = 60
NEGRO   = (0,   0,   0)
BLANCO  = (255, 255, 255)
GRIS    = (60,  60,  60)
GRIS_CL = (150, 150, 150)
AZUL    = (50,  120, 220)
AMARILLO= (255, 220, 50)
VERDE   = (50,  200, 100)
ROJO    = (220, 80,  70)
NARANJA = (255, 160, 30)
VIOLETA = (160, 90,  220)
MARRON  = (100, 70,  40)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 4 — Máquina de estados de animación")
clock = pygame.time.Clock()
fuente    = pygame.font.SysFont("monospace", 14)
fuente_ch = pygame.font.SysFont("monospace", 12)
fuente_gr = pygame.font.SysFont("monospace", 17, bold=True)

def texto(txt, pos, color=BLANCO, f=None):
    s = (f or fuente).render(txt, True, color)
    pantalla.blit(s, pos)


# ════════════════════════════════════════════════════════
# GENERADOR DE FRAMES POR ESTADO
# En un juego real: cargar desde spritesheet PNG
# ════════════════════════════════════════════════════════

FW, FH = 56, 64

def crear_frame_idle(i, total):
    surf = pygame.Surface((FW, FH), pygame.SRCALPHA)
    t = i / total
    cx, cy = FW // 2, FH // 2

    # Cuerpo
    respira = 1.0 + 0.04 * math.sin(t * math.pi * 2)
    pygame.draw.ellipse(surf, AZUL,
                        (cx - int(16 * respira), cy - 10,
                         int(32 * respira), 28))
    # Cabeza
    hy = cy - 22 + int(1.5 * math.sin(t * math.pi * 2))
    pygame.draw.circle(surf, (255, 200, 150), (cx, hy), 14)
    # Ojos
    abierto = not (0.45 < t < 0.55)
    if abierto:
        pygame.draw.circle(surf, NEGRO, (cx - 4, hy - 2), 3)
        pygame.draw.circle(surf, NEGRO, (cx + 4, hy - 2), 3)
    else:
        pygame.draw.line(surf, NEGRO, (cx - 7, hy - 2), (cx - 1, hy - 2), 2)
        pygame.draw.line(surf, NEGRO, (cx + 1, hy - 2), (cx + 7, hy - 2), 2)
    # Piernas quietas
    pygame.draw.line(surf, (80, 80, 160), (cx - 7, cy + 14), (cx - 7, cy + 28), 5)
    pygame.draw.line(surf, (80, 80, 160), (cx + 7, cy + 14), (cx + 7, cy + 28), 5)
    return surf

def crear_frame_walk(i, total):
    surf = pygame.Surface((FW, FH), pygame.SRCALPHA)
    t = i / total
    cx, cy = FW // 2, FH // 2

    # Cuerpo inclina levemente
    inc = int(2 * math.sin(t * math.pi * 2))
    pygame.draw.ellipse(surf, AZUL, (cx - 16, cy - 10 + inc, 32, 28))
    # Cabeza
    hy = cy - 22 + inc
    pygame.draw.circle(surf, (255, 200, 150), (cx, hy), 14)
    pygame.draw.circle(surf, NEGRO, (cx - 4, hy - 2), 3)
    pygame.draw.circle(surf, NEGRO, (cx + 4, hy - 2), 3)
    # Brazos
    ang = 0.6 * math.sin(t * math.pi * 2)
    bx_l, by_l = cx - 16, cy - 4 + inc
    bx_r, by_r = cx + 16, cy - 4 + inc
    pygame.draw.line(surf, AZUL, (bx_l, by_l),
                     (bx_l - int(12 * math.cos(ang)), by_l + int(10 * abs(math.sin(ang)))), 4)
    pygame.draw.line(surf, AZUL, (bx_r, by_r),
                     (bx_r + int(12 * math.cos(ang)), by_r + int(10 * abs(math.sin(-ang)))), 4)
    # Piernas caminando
    ang_p = 0.8 * math.sin(t * math.pi * 2)
    for lado, s in [(-1, 1), (1, -1)]:
        px = cx + lado * 7
        py = cy + 14 + inc
        ex = px + lado * int(10 * math.sin(ang_p * s))
        ey = py + 18
        pygame.draw.line(surf, (80, 80, 160), (px, py), (ex, ey), 5)
        pygame.draw.circle(surf, (60, 60, 130), (ex, ey), 4)
    return surf

def crear_frame_jump(i, total):
    surf = pygame.Surface((FW, FH), pygame.SRCALPHA)
    t = i / total
    cx, cy = FW // 2, FH // 2

    # Estiramiento en salto
    estirado = t < 0.5
    body_h = 32 if estirado else 24
    pygame.draw.ellipse(surf, AZUL, (cx - 14, cy - 12, 28, body_h))
    # Cabeza
    hy = cy - 22 if estirado else cy - 18
    pygame.draw.circle(surf, (255, 200, 150), (cx, hy), 14)
    pygame.draw.circle(surf, NEGRO, (cx - 4, hy - 2), 3)
    pygame.draw.circle(surf, NEGRO, (cx + 4, hy - 2), 3)
    # Piernas dobladas
    ang_rod = 0.8 if not estirado else 0.2
    for lado in [-1, 1]:
        px = cx + lado * 7
        py = cy + 14
        kx = px + lado * int(12 * math.sin(ang_rod))
        ky = py + int(10 * math.cos(ang_rod))
        pygame.draw.line(surf, (80, 80, 160), (px, py), (kx, ky), 5)
        pygame.draw.line(surf, (60, 60, 130), (kx, ky),
                         (kx + lado * 8, ky + 4), 5)
    return surf

def crear_frame_attack(i, total):
    surf = pygame.Surface((FW, FH), pygame.SRCALPHA)
    t = i / total
    cx, cy = FW // 2, FH // 2

    pygame.draw.ellipse(surf, AZUL, (cx - 16, cy - 10, 32, 28))
    hy = cy - 22
    pygame.draw.circle(surf, (255, 200, 150), (cx, hy), 14)
    pygame.draw.circle(surf, NEGRO, (cx - 4, hy - 2), 3)
    pygame.draw.circle(surf, NEGRO, (cx + 4, hy - 2), 3)
    # Piernas
    pygame.draw.line(surf, (80, 80, 160), (cx - 7, cy + 14), (cx - 7, cy + 28), 5)
    pygame.draw.line(surf, (80, 80, 160), (cx + 7, cy + 14), (cx + 7, cy + 28), 5)
    # Brazo golpeando
    ext = math.sin(t * math.pi)
    bx = cx + 16
    by = cy - 4
    ex = bx + int(24 * ext)
    ey = by - int(6 * ext)
    pygame.draw.line(surf, AZUL, (bx, by), (ex, ey), 5)
    # Efecto de golpe
    if t > 0.5:
        pygame.draw.circle(surf, AMARILLO, (ex, ey), int(8 * (t - 0.5) * 2), 2)
    return surf

# Generar frames para cada estado
N = {'idle': 6, 'walk': 8, 'jump': 4, 'attack': 5}
animaciones = {
    'idle':   [crear_frame_idle(i, N['idle'])   for i in range(N['idle'])],
    'walk':   [crear_frame_walk(i, N['walk'])   for i in range(N['walk'])],
    'jump':   [crear_frame_jump(i, N['jump'])   for i in range(N['jump'])],
    'attack': [crear_frame_attack(i, N['attack']) for i in range(N['attack'])],
}

COLORES_ESTADO = {
    'idle': GRIS_CL, 'walk': VERDE, 'jump': AZUL, 'attack': ROJO
}


# ════════════════════════════════════════════════════════
# SPRITE CON MÁQUINA DE ESTADOS
# ════════════════════════════════════════════════════════

class Jugador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.estado       = 'idle'
        self.frame_actual = 0
        self.ultimo_ms    = pygame.time.get_ticks()
        self.dur_frame    = {'idle': 130, 'walk': 80, 'jump': 120, 'attack': 90}
        self.image        = animaciones['idle'][0]
        self.rect         = self.image.get_rect(center=(ANCHO // 2, 380))

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.en_suelo = False
        self.direccion = 1   # 1=derecha, -1=izquierda
        self.atacando = False
        self.t_ataque = 0

        # Para el diagrama de estados
        self.historial_estados = ['idle']
        self.MAX_HIST = 8

    def cambiar_estado(self, nuevo):
        """Solo cambia si el estado es diferente. Reinicia el frame."""
        if self.estado != nuevo:
            if len(self.historial_estados) > self.MAX_HIST:
                self.historial_estados.pop(0)
            self.historial_estados.append(nuevo)
            self.estado = nuevo
            self.frame_actual = 0
            self.ultimo_ms = pygame.time.get_ticks()

    def update(self, plataformas):
        t = pygame.key.get_pressed()

        # Input de movimiento (si no está atacando)
        if not self.atacando:
            if t[pygame.K_a]:
                self.vel_x = -4
                self.direccion = -1
            elif t[pygame.K_d]:
                self.vel_x = 4
                self.direccion = 1
            else:
                self.vel_x *= 0.75   # Fricción

            if t[pygame.K_SPACE] and self.en_suelo:
                self.vel_y = -13
                self.en_suelo = False

        # Ataque (prioridad alta)
        if t[pygame.K_f] and not self.atacando and self.en_suelo:
            self.atacando = True
            self.t_ataque = 0
            self.vel_x = 0

        if self.atacando:
            self.t_ataque += 1
            total_frames = N['attack']
            dur = self.dur_frame['attack']
            if self.t_ataque > total_frames * (dur / (1000 / FPS)):
                self.atacando = False

        # Física
        self.vel_y += 0.55   # Gravedad
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)

        # Colisión con plataformas
        self.en_suelo = False
        for plat in plataformas:
            if self.rect.colliderect(plat) and self.vel_y > 0:
                self.rect.bottom = plat.top
                self.vel_y = 0
                self.en_suelo = True

        # Bordes laterales
        self.rect.x = max(0, min(self.rect.x, ANCHO - FW))

        # ── Determinar estado ─────────────────────────────
        if self.atacando:
            self.cambiar_estado('attack')
        elif not self.en_suelo:
            self.cambiar_estado('jump')
        elif abs(self.vel_x) > 0.5:
            self.cambiar_estado('walk')
        else:
            self.cambiar_estado('idle')

        # ── Animar ────────────────────────────────────────
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_ms >= self.dur_frame[self.estado]:
            self.ultimo_ms = ahora
            frames = animaciones[self.estado]
            # attack: no loopear, quedarse en último frame
            if self.estado == 'attack':
                self.frame_actual = min(self.frame_actual + 1, len(frames) - 1)
            else:
                self.frame_actual = (self.frame_actual + 1) % len(frames)

        frame = animaciones[self.estado][self.frame_actual]
        # Flip según dirección
        if self.direccion == -1:
            self.image = pygame.transform.flip(frame, True, False)
        else:
            self.image = frame


# ── PLATAFORMAS ───────────────────────────────────────────
plataformas = [
    pygame.Rect(0,   480, ANCHO, 20),   # Suelo
    pygame.Rect(150, 370, 180,  15),
    pygame.Rect(400, 300, 200,  15),
    pygame.Rect(650, 370, 180,  15),
    pygame.Rect(280, 220, 150,  15),
]

jugador = Jugador()
grupo = pygame.sprite.GroupSingle(jugador)


while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

    jugador.update(plataformas)

    # ── RENDER ────────────────────────────────────────────
    pantalla.fill((10, 10, 20))

    # Plataformas
    for plat in plataformas:
        pygame.draw.rect(pantalla, MARRON, plat)
        pygame.draw.rect(pantalla, (150, 110, 60), plat, 2)

    # Sombra del jugador
    sx = jugador.rect.centerx
    for p in plataformas:
        if p.top > jugador.rect.bottom and p.left < sx < p.right:
            sombra_y = p.top
            dist = sombra_y - jugador.rect.bottom
            alpha = max(0, 180 - dist)
            ancho_s = max(4, 40 - dist // 4)
            surf_s = pygame.Surface((ancho_s, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(surf_s, (0, 0, 0, alpha), (0, 0, ancho_s, 8))
            pantalla.blit(surf_s, (sx - ancho_s // 2, sombra_y - 4))
            break

    grupo.draw(pantalla)

    # ── Panel lateral derecho ─────────────────────────────
    px = ANCHO - 240
    pygame.draw.rect(pantalla, (12, 12, 20), (px - 10, 0, 250, ALTO))
    pygame.draw.line(pantalla, GRIS, (px - 10, 0), (px - 10, ALTO), 1)

    texto("ESTADO ACTUAL", (px, 15), GRIS_CL, fuente_gr)
    col_est = COLORES_ESTADO.get(jugador.estado, BLANCO)
    texto(f"► {jugador.estado.upper()}", (px, 42), col_est, fuente_gr)

    texto(f"frame: {jugador.frame_actual} / {N[jugador.estado] - 1}",
          (px, 72), GRIS_CL, fuente_ch)
    texto(f"dir:   {'→' if jugador.direccion == 1 else '←'}",
          (px, 90), GRIS_CL, fuente_ch)
    texto(f"suelo: {jugador.en_suelo}", (px, 108), GRIS_CL, fuente_ch)
    texto(f"vel_x: {jugador.vel_x:.1f}", (px, 126), GRIS_CL, fuente_ch)
    texto(f"vel_y: {jugador.vel_y:.1f}", (px, 144), GRIS_CL, fuente_ch)

    # Diagrama de estados
    texto("HISTORIAL", (px, 178), GRIS_CL, fuente_ch)
    for i, est in enumerate(jugador.historial_estados[-6:]):
        col = COLORES_ESTADO.get(est, GRIS_CL)
        txt = f"{'→ ' if i > 0 else '   '}{est}"
        texto(txt, (px, 196 + i * 18), col, fuente_ch)

    # Frames del estado actual (miniaturas)
    texto("FRAMES", (px, 330), GRIS_CL, fuente_ch)
    frames_est = animaciones[jugador.estado]
    mini = 28
    for i, fr in enumerate(frames_est):
        fx = px + i * (mini + 3)
        fy = 350
        if i >= 8: break  # Máx 8 por fila
        surf_m = pygame.transform.scale(fr, (mini, mini))
        # Fondo
        col_bg = (30, 50, 30) if i == jugador.frame_actual else (20, 20, 20)
        pygame.draw.rect(pantalla, col_bg, (fx - 1, fy - 1, mini + 2, mini + 2))
        pantalla.blit(surf_m, (fx, fy))
        if i == jugador.frame_actual:
            pygame.draw.rect(pantalla, VERDE, (fx - 1, fy - 1, mini + 2, mini + 2), 1)

    # Controles
    texto("CONTROLES", (px, 400), GRIS_CL, fuente_ch)
    controles = ["A / D  : mover", "ESPACIO: saltar", "F      : atacar", "ESC    : salir"]
    for i, c in enumerate(controles):
        texto(c, (px, 418 + i * 18), GRIS, fuente_ch)

    texto(f"FPS: {clock.get_fps():.0f}", (px, ALTO - 20), GRIS, fuente_ch)

    pygame.display.flip()
    clock.tick(FPS)
