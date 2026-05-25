"""
════════════════════════════════════════════════════════════
 MÓDULO 2 — Script 01: Sprite básico
════════════════════════════════════════════════════════════

 Qué demuestra:
   • Crear una clase que hereda de pygame.sprite.Sprite
   • self.image y self.rect obligatorios
   • Usar un Group para update() y draw() automáticos
   • Propiedades del rect: center, topleft, topright, etc.

 Controles:
   • Flechas: mover el sprite
   • WASD:    mover un segundo sprite
   • ESC:     salir
════════════════════════════════════════════════════════════
"""

import pygame
import sys

pygame.init()

ANCHO, ALTO = 900, 600
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
pygame.display.set_caption("Módulo 2 — Sprite básico")
clock = pygame.time.Clock()
fuente = pygame.font.SysFont("monospace", 14)
fuente_ch = pygame.font.SysFont("monospace", 12)


# ── CLASE SPRITE ─────────────────────────────────────────
class Jugador(pygame.sprite.Sprite):
    """
    Clase mínima de Sprite.
    Obligatorios: self.image y self.rect
    """
    def __init__(self, x, y, color, teclas, nombre):
        super().__init__()   # SIEMPRE llamar al __init__ del padre

        self.nombre = nombre
        self.color  = color
        self.vel    = 4

        # image: Surface con el dibujo del sprite
        self.image = pygame.Surface((48, 48))
        self.image.fill(color)
        # Borde blanco para distinguirlo
        pygame.draw.rect(self.image, BLANCO, self.image.get_rect(), 2)
        # Nombre adentro
        f = pygame.font.SysFont("monospace", 11, bold=True)
        txt = f.render(nombre, True, BLANCO)
        self.image.blit(txt, (2, 16))

        # rect: posición y tamaño en pantalla
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        self.teclas = teclas  # dict de teclas asignadas

    def update(self):
        t = pygame.key.get_pressed()
        if t[self.teclas['izq']]:  self.rect.x -= self.vel
        if t[self.teclas['der']]:  self.rect.x += self.vel
        if t[self.teclas['arr']]:  self.rect.y -= self.vel
        if t[self.teclas['aba']]:  self.rect.y += self.vel

        # Limitar a la zona de juego
        self.rect.clamp_ip(pygame.Rect(0, 0, ANCHO, ALTO - 120))

    def dibujar_info(self, surf):
        """Dibuja información del rect alrededor del sprite"""
        r = self.rect
        # Bounding box punteada
        pygame.draw.rect(surf, self.color, r, 1)
        # Punto central
        pygame.draw.circle(surf, AMARILLO, r.center, 3)
        # Etiqueta center
        t = fuente_ch.render(f"center={r.center}", True, AMARILLO)
        surf.blit(t, (r.centerx - t.get_width()//2, r.bottom + 4))
        # Etiqueta topleft
        t2 = fuente_ch.render(f"topleft={r.topleft}", True, GRIS_CL)
        surf.blit(t2, (r.left, r.top - 16))


# ── CREAR SPRITES ─────────────────────────────────────────
teclas_p1 = {'izq': pygame.K_LEFT, 'der': pygame.K_RIGHT,
              'arr': pygame.K_UP,   'aba': pygame.K_DOWN}
teclas_p2 = {'izq': pygame.K_a,    'der': pygame.K_d,
              'arr': pygame.K_w,    'aba': pygame.K_s}

p1 = Jugador(200, 250, AZUL,  teclas_p1, "P1")
p2 = Jugador(600, 250, VERDE, teclas_p2, "P2")

# Grupo que contiene todos los sprites
todos = pygame.sprite.Group(p1, p2)


def texto(txt, pos, color=BLANCO, f=None):
    s = (f or fuente).render(txt, True, color)
    pantalla.blit(s, pos)


while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

    # Un solo update() llama al update() de TODOS los sprites
    todos.update()

    # ── RENDER ────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # Cuadrícula de referencia
    for gx in range(0, ANCHO, 100):
        pygame.draw.line(pantalla, (20, 20, 20), (gx, 0), (gx, ALTO))
    for gy in range(0, ALTO - 120, 100):
        pygame.draw.line(pantalla, (20, 20, 20), (0, gy), (ANCHO, gy))

    # Info del rect de cada sprite (dibujada antes del sprite)
    p1.dibujar_info(pantalla)
    p2.dibujar_info(pantalla)

    # Un solo draw() dibuja TODOS los sprites del grupo
    todos.draw(pantalla)

    # ── Panel inferior ────────────────────────────────────
    pygame.draw.rect(pantalla, (15, 15, 15), (0, ALTO - 120, ANCHO, 120))
    pygame.draw.line(pantalla, GRIS, (0, ALTO - 120), (ANCHO, ALTO - 120), 1)

    # Info de P1
    texto("P1 (Azul — flechas)", (20, ALTO - 112), AZUL)
    attrs_p1 = [
        f"rect.x, y    = {p1.rect.x}, {p1.rect.y}",
        f"rect.center  = {p1.rect.center}",
        f"rect.topright= {p1.rect.topright}",
        f"rect.w, h    = {p1.rect.width}, {p1.rect.height}",
    ]
    for i, a in enumerate(attrs_p1):
        texto(a, (20, ALTO - 94 + i * 18), GRIS_CL, fuente_ch)

    # Info de P2
    texto("P2 (Verde — WASD)", (ANCHO // 2 + 20, ALTO - 112), VERDE)
    attrs_p2 = [
        f"rect.x, y    = {p2.rect.x}, {p2.rect.y}",
        f"rect.center  = {p2.rect.center}",
        f"rect.topright= {p2.rect.topright}",
        f"rect.w, h    = {p2.rect.width}, {p2.rect.height}",
    ]
    for i, a in enumerate(attrs_p2):
        texto(a, (ANCHO // 2 + 20, ALTO - 94 + i * 18), GRIS_CL, fuente_ch)

    # Sprites en el grupo
    texto(f"Sprites en grupo 'todos': {len(todos)}", (20, ALTO - 22), GRIS_CL, fuente_ch)
    texto(f"FPS: {clock.get_fps():.0f}  |  ESC: salir",
          (ANCHO - 200, ALTO - 22), GRIS, fuente_ch)

    pygame.display.flip()
    clock.tick(FPS)
