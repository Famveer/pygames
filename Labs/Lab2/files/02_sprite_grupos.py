"""
════════════════════════════════════════════════════════════
 MÓDULO 2 — Script 02: Grupos, kill() y transparencia
════════════════════════════════════════════════════════════

 Qué demuestra:
   • Múltiples grupos (un sprite puede estar en varios)
   • kill() para eliminar sprites del juego
   • set_alpha() para transparencia global de una Surface
   • Surface con SRCALPHA (alpha por pixel)
   • Sprite que parpadea (fade) usando set_alpha

 Controles:
   • CLIC IZQUIERDO en un sprite: lo elimina (kill)
   • ESPACIO: spawnear nuevo sprite
   • R: resetear todos
   • ESC: salir
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import random
import math

pygame.init()

ANCHO, ALTO = 900, 600
FPS = 60
NEGRO   = (0,   0,   0)
BLANCO  = (255, 255, 255)
GRIS    = (60,  60,  60)
GRIS_CL = (140, 140, 140)
AMARILLO= (255, 220, 50)

PALETA = [
    (220, 80,  70),   # rojo
    (50,  120, 220),  # azul
    (50,  200, 100),  # verde
    (220, 150, 50),   # naranja
    (160, 90,  220),  # violeta
    (50,  200, 220),  # cyan
]

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 2 — Grupos, kill() y transparencia")
clock = pygame.time.Clock()
fuente    = pygame.font.SysFont("monospace", 14)
fuente_ch = pygame.font.SysFont("monospace", 12)


# ── SPRITE CON TRANSPARENCIA ──────────────────────────────
class Particula(pygame.sprite.Sprite):
    """
    Sprite con SRCALPHA: alpha por pixel.
    Dibuja un círculo suave con borde transparente.
    Desvanece (fade) durante su vida.
    """
    def __init__(self, x, y, color):
        super().__init__()
        self.color  = color
        self.radio  = random.randint(18, 36)
        self.vida   = 255          # Alpha inicial
        self.vel_x  = random.uniform(-2, 2)
        self.vel_y  = random.uniform(-3, -0.5)
        self.grav   = 0.08
        self.pos_x  = float(x)
        self.pos_y  = float(y)

        tam = self.radio * 2 + 4
        # SRCALPHA permite alpha por pixel en la Surface
        self.image = pygame.Surface((tam, tam), pygame.SRCALPHA)
        self._redibujar()
        self.rect = self.image.get_rect(center=(x, y))

    def _redibujar(self):
        self.image.fill((0, 0, 0, 0))  # Limpiar con transparente
        r = self.radio
        tam = r * 2 + 4
        cx, cy = tam // 2, tam // 2
        alpha = int(self.vida)
        # Círculo exterior semitransparente
        pygame.draw.circle(self.image, (*self.color, alpha // 3), (cx, cy), r)
        # Círculo interior sólido
        pygame.draw.circle(self.image, (*self.color, alpha), (cx, cy), r - 4)

    def update(self):
        self.vel_y += self.grav
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        self.vida  -= 3.5

        if self.vida <= 0:
            self.kill()   # Eliminar de todos los grupos cuando se desvanece
            return

        self._redibujar()
        self.rect.centerx = int(self.pos_x)
        self.rect.centery  = int(self.pos_y)


class SpriteSolido(pygame.sprite.Sprite):
    """
    Sprite sólido con set_alpha global.
    Pulsa su transparencia con una onda seno.
    """
    def __init__(self, x, y, color, idx):
        super().__init__()
        self.color = color
        self.idx   = idx
        self.t     = idx * 0.5   # Desfase de fase

        tam = 56
        self.image = pygame.Surface((tam, tam))
        self.image.fill(color)
        pygame.draw.rect(self.image, BLANCO, self.image.get_rect(), 2)

        f = pygame.font.SysFont("monospace", 11, bold=True)
        txt = f.render(f"#{idx}", True, BLANCO)
        self.image.blit(txt, (tam // 2 - txt.get_width() // 2,
                               tam // 2 - txt.get_height() // 2))

        self.rect = self.image.get_rect(center=(x, y))
        self.muerto = False

    def update(self):
        self.t += 0.05
        # Pulso de alpha usando seno
        alpha = int(128 + 127 * math.sin(self.t))
        self.image.set_alpha(alpha)

    def al_hacer_click(self, pos):
        if self.rect.collidepoint(pos):
            self.kill()
            return True
        return False


# ── GRUPOS ────────────────────────────────────────────────
# Un sprite puede pertenecer a MÚLTIPLES grupos
solidos   = pygame.sprite.Group()
particulas = pygame.sprite.Group()
todos     = pygame.sprite.Group()  # Contiene ambos tipos

# Contador para IDs
contador_id = [0]

def crear_solido():
    x = random.randint(80, ANCHO - 80)
    y = random.randint(80, ALTO - 180)
    color = random.choice(PALETA)
    contador_id[0] += 1
    s = SpriteSolido(x, y, color, contador_id[0])
    solidos.add(s)    # Al grupo específico
    todos.add(s)      # Al grupo general

def crear_particulas(x, y, color, n=20):
    for _ in range(n):
        p = Particula(x, y, color)
        particulas.add(p)
        todos.add(p)

def resetear():
    todos.empty()
    solidos.empty()
    particulas.empty()
    contador_id[0] = 0
    for _ in range(6):
        crear_solido()

resetear()


def texto(txt, pos, color=BLANCO, f=None):
    s = (f or fuente).render(txt, True, color)
    pantalla.blit(s, pos)


while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if ev.key == pygame.K_r:
                resetear()
            if ev.key == pygame.K_SPACE:
                crear_solido()

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # Revisar si se hizo click en algún sólido
            for sprite in list(solidos):
                if sprite.rect.collidepoint(ev.pos):
                    # Explotar en partículas antes de morir
                    crear_particulas(sprite.rect.centerx,
                                     sprite.rect.centery,
                                     sprite.color, n=25)
                    sprite.kill()  # Lo elimina de TODOS sus grupos
                    break

    todos.update()

    # ── RENDER ────────────────────────────────────────────
    pantalla.fill(NEGRO)

    todos.draw(pantalla)

    # Etiquetas sobre cada sólido
    for sp in solidos:
        txt = fuente_ch.render("click para matar", True, GRIS_CL)
        pantalla.blit(txt, (sp.rect.centerx - txt.get_width() // 2,
                            sp.rect.bottom + 3))

    # Panel
    pygame.draw.rect(pantalla, (15, 15, 15), (0, ALTO - 90, ANCHO, 90))
    pygame.draw.line(pantalla, GRIS, (0, ALTO - 90), (ANCHO, ALTO - 90), 1)

    texto("GRUPOS", (20, ALTO - 82), GRIS_CL)
    texto(f"todos    ({len(todos):>2} sprites) ← contiene sólidos + partículas",
          (20, ALTO - 62), BLANCO, fuente_ch)
    texto(f"solidos  ({len(solidos):>2} sprites) ← solo los cuadrados pulsantes",
          (20, ALTO - 44), AMARILLO, fuente_ch)
    texto(f"particulas({len(particulas):>2} sprites) ← se auto-eliminan al desvanecerse",
          (20, ALTO - 26), (180, 220, 255), fuente_ch)

    texto("CLIC: matar sprite   |   ESPACIO: nuevo   |   R: resetear   |   ESC: salir",
          (ANCHO - 560, ALTO - 18), GRIS, fuente_ch)

    pygame.display.flip()
    clock.tick(FPS)
