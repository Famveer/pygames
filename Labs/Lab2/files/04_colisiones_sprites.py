"""
════════════════════════════════════════════════════════════
 MÓDULO 3 — Script 04: spritecollide y groupcollide
════════════════════════════════════════════════════════════

 Qué demuestra:
   • spritecollide() — jugador contra grupo de ítems
   • groupcollide()  — balas contra enemigos
   • Respuesta a colisión: recoger ítems, eliminar enemigos
   • Puntaje y vidas como consecuencia de las colisiones
   • collide_circle como alternativa a AABB
   • Efecto de partículas (SRCALPHA + fade) al morir la nave

 Controles:
   • Flechas: mover jugador
   • ESPACIO: disparar bala
   • R: resetear
   • ESC: salir
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import random
import math

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
NARANJA = (255, 160, 30)
VIOLETA = (160, 90,  220)

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 3 — spritecollide / groupcollide")
clock = pygame.time.Clock()
fuente    = pygame.font.SysFont("monospace", 15)
fuente_ch = pygame.font.SysFont("monospace", 12)
fuente_gr = pygame.font.SysFont("monospace", 19, bold=True)
fuente_game_over = pygame.font.SysFont("monospace", 52, bold=True)

ZONA = pygame.Rect(0, 0, ANCHO, ALTO - 110)

def texto(txt, pos, color=BLANCO, f=None):
    s = (f or fuente).render(txt, True, color)
    pantalla.blit(s, pos)


# ── PARTÍCULA (del script 02, adaptada para la nave) ──────
class Particula(pygame.sprite.Sprite):
    """
    Partícula con SRCALPHA: alpha por pixel.
    Se desvanece durante su vida y sigue física simple.
    Colores: azul/blanco/naranja simulando la explosión de la nave.
    """
    COLORES_NAVE = [AZUL, BLANCO, NARANJA, (180, 220, 255), AMARILLO]

    def __init__(self, x, y):
        super().__init__()
        self.color  = random.choice(self.COLORES_NAVE)
        self.radio  = random.randint(4, 18)
        self.vida   = random.randint(180, 255)   # Alpha inicial (varía para más variedad)
        ang         = random.uniform(0, math.pi * 2)
        speed       = random.uniform(1.0, 5.5)
        self.vel_x  = math.cos(ang) * speed
        self.vel_y  = math.sin(ang) * speed - random.uniform(0.5, 2.0)  # Más hacia arriba
        self.grav   = random.uniform(0.04, 0.12)
        self.fade   = random.uniform(3.0, 6.0)   # Velocidad de desvanecimiento
        self.pos_x  = float(x)
        self.pos_y  = float(y)

        tam = self.radio * 2 + 4
        self.image = pygame.Surface((tam, tam), pygame.SRCALPHA)
        self._redibujar()
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def _redibujar(self):
        self.image.fill((0, 0, 0, 0))
        r   = self.radio
        tam = r * 2 + 4
        cx  = cy = tam // 2
        a   = max(0, int(self.vida))
        # Halo exterior semitransparente
        pygame.draw.circle(self.image, (*self.color, a // 3), (cx, cy), r)
        # Núcleo sólido
        if r > 4:
            pygame.draw.circle(self.image, (*self.color, a), (cx, cy), r - 3)

    def update(self):
        self.vel_y += self.grav
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        self.vida  -= self.fade

        if self.vida <= 0:
            self.kill()
            return

        self._redibujar()
        self.rect.centerx = int(self.pos_x)
        self.rect.centery  = int(self.pos_y)


def explosion_nave(x, y, cantidad=60):
    """Genera una explosión de partículas en la posición dada."""
    nuevas = []
    for _ in range(cantidad):
        p = Particula(x, y)
        nuevas.append(p)
    return nuevas


# ── SPRITES ───────────────────────────────────────────────
class Jugador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, AZUL,
                            [(22, 0), (44, 44), (22, 34), (0, 44)])
        pygame.draw.polygon(self.image, BLANCO,
                            [(22, 0), (44, 44), (22, 34), (0, 44)], 1)
        self.rect   = self.image.get_rect(center=(ANCHO // 2, ALTO - 160))
        self.radius = 18
        self.vel    = 5

    def update(self):
        t = pygame.key.get_pressed()
        if t[pygame.K_LEFT]:  self.rect.x -= self.vel
        if t[pygame.K_RIGHT]: self.rect.x += self.vel
        if t[pygame.K_UP]:    self.rect.y -= self.vel
        if t[pygame.K_DOWN]:  self.rect.y += self.vel
        self.rect.clamp_ip(ZONA)


class Bala(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 18), pygame.SRCALPHA)
        pygame.draw.rect(self.image, AMARILLO, (1, 0, 4, 18), border_radius=2)
        self.rect   = self.image.get_rect(centerx=x, bottom=y)
        self.radius = 4
        self.vel    = 9

    def update(self):
        self.rect.y -= self.vel
        if self.rect.bottom < 0:
            self.kill()


class Enemigo(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        tam = random.randint(30, 52)
        self.image = pygame.Surface((tam, tam), pygame.SRCALPHA)
        self.color = random.choice([ROJO, NARANJA, VIOLETA])
        pygame.draw.polygon(self.image, self.color, [
            (tam//2, 0), (tam, tam*2//3), (tam*3//4, tam),
            (tam//4, tam), (0, tam*2//3)
        ])
        pygame.draw.polygon(self.image, BLANCO, [
            (tam//2, 0), (tam, tam*2//3), (tam*3//4, tam),
            (tam//4, tam), (0, tam*2//3)
        ], 1)
        self.rect   = self.image.get_rect(
            x=random.randint(10, ANCHO - 60),
            y=random.randint(-80, -20)
        )
        self.radius = tam // 2
        self.vel    = random.uniform(1.0, 2.8)

    def update(self):
        self.rect.y += self.vel
        if self.rect.top > ALTO - 110:
            self.rect.y = random.randint(-80, -20)
            self.rect.x = random.randint(10, ANCHO - 60)


class Item(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        cx, cy, r_ext, r_int = 12, 12, 12, 5
        puntos = []
        for i in range(10):
            ang = math.radians(i * 36 - 90)
            r   = r_ext if i % 2 == 0 else r_int
            puntos.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        pygame.draw.polygon(self.image, AMARILLO, puntos)
        pygame.draw.polygon(self.image, BLANCO, puntos, 1)
        self.rect   = self.image.get_rect(
            x=random.randint(20, ANCHO - 40),
            y=random.randint(30, ALTO - 200)
        )
        self.radius = 12
        self.t      = random.uniform(0, math.pi * 2)
        self.base_y = float(self.rect.y)

    def update(self):
        self.t      += 0.04
        self.rect.y  = int(self.base_y + math.sin(self.t) * 6)


# ── ESTADO DEL JUEGO ──────────────────────────────────────
def crear_juego():
    jugador  = Jugador()
    enemigos = pygame.sprite.Group(*[Enemigo() for _ in range(8)])
    items    = pygame.sprite.Group(*[Item()    for _ in range(6)])
    balas    = pygame.sprite.Group()
    particulas = pygame.sprite.Group()
    todos    = pygame.sprite.Group(jugador, *enemigos, *items)
    return jugador, enemigos, items, balas, particulas, todos

jugador, enemigos, items, balas, particulas, todos = crear_juego()

puntaje        = 0
vidas          = 3
cd_bala        = 0
log_colisiones = []
MAX_LOG        = 6

# Estado de muerte
nave_muerta      = False
timer_respawn    = 0
FRAMES_RESPAWN   = 150   # ~2.5 segundos a 60 FPS
pos_explosion    = (ANCHO // 2, ALTO - 160)

def agregar_log(msg, color):
    log_colisiones.append((msg, color))
    if len(log_colisiones) > MAX_LOG:
        log_colisiones.pop(0)

def matar_nave():
    """Elimina la nave, genera explosión y activa el estado de muerte."""
    global nave_muerta, timer_respawn, pos_explosion
    pos_explosion = jugador.rect.center
    jugador.kill()   # Sacar del grupo de sprites
    # Crear partículas y agregarlas a ambos grupos
    nuevas = explosion_nave(*pos_explosion, cantidad=70)
    particulas.add(*nuevas)
    todos.add(*nuevas)
    nave_muerta   = True
    timer_respawn = FRAMES_RESPAWN
    agregar_log("💥 NAVE DESTRUIDA — explosión de partículas!", ROJO)

def respawnear_nave():
    """Reaparece la nave en el centro luego del timer."""
    global nave_muerta, jugador
    nave_muerta = False
    jugador     = Jugador()
    todos.add(jugador)


# ── GAME LOOP ─────────────────────────────────────────────
while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if ev.key == pygame.K_r:
                jugador, enemigos, items, balas, particulas, todos = crear_juego()
                puntaje = 0; vidas = 3
                nave_muerta = False
                log_colisiones.clear()

    # ── INPUT solo si la nave está viva ───────────────────
    if not nave_muerta:
        t = pygame.key.get_pressed()
        if t[pygame.K_SPACE] and cd_bala <= 0:
            b = Bala(jugador.rect.centerx, jugador.rect.top)
            balas.add(b)
            todos.add(b)
            cd_bala = 15
    if cd_bala > 0:
        cd_bala -= 1

    todos.update()

    # ── Timer de respawn ──────────────────────────────────
    if nave_muerta:
        timer_respawn -= 1
        if timer_respawn <= 0 and vidas > 0:
            respawnear_nave()
    else:
        # ── COLISIONES solo si la nave está viva ──────────

        # 1. Jugador recoge ítems
        recogidos = pygame.sprite.spritecollide(
            jugador, items, True,
            collided=pygame.sprite.collide_circle
        )
        for _ in recogidos:
            puntaje += 10
            agregar_log("spritecollide → ítem recogido +10pts", AMARILLO)
            if len(items) < 3:
                nuevo = Item()
                items.add(nuevo); todos.add(nuevo)

        # 2. Jugador golpeado por enemigo
        golpeado = pygame.sprite.spritecollide(
            jugador, enemigos, False,
            collided=pygame.sprite.collide_circle
        )
        if golpeado:
            vidas -= 1
            agregar_log(f"spritecollide → jugador golpeado! vidas={vidas}", ROJO)
            for e in golpeado:
                e.rect.y = random.randint(-200, -50)
            # ► Activar explosión de partículas
            matar_nave()

        # 3. Balas destruyen enemigos
        impactos = pygame.sprite.groupcollide(
            balas, enemigos, True, True,
            collided=pygame.sprite.collide_circle
        )
        for bala, enems in impactos.items():
            puntaje += len(enems) * 20
            agregar_log(f"groupcollide → {len(enems)} enemigo(s) +{len(enems)*20}pts", VERDE)
            for _ in enems:
                nuevo_e = Enemigo()
                enemigos.add(nuevo_e); todos.add(nuevo_e)

    # ── RENDER ────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # Fondo estrellado
    for _ in range(2):
        sx = random.randint(0, ANCHO)
        sy = random.randint(0, ALTO - 110)
        pygame.draw.circle(pantalla, (40, 40, 40), (sx, sy), 1)

    todos.draw(pantalla)

    # Círculos de colisión (solo si la nave está viva)
    if not nave_muerta:
        pygame.draw.circle(pantalla, AZUL,
                           jugador.rect.center, jugador.radius, 1)
    for e in enemigos:
        pygame.draw.circle(pantalla, (100, 40, 40), e.rect.center, e.radius, 1)
    for it in items:
        pygame.draw.circle(pantalla, (100, 100, 0), it.rect.center, it.radius, 1)

    # ── Overlay de muerte / respawn ───────────────────────
    if nave_muerta and vidas > 0:
        pct = timer_respawn / FRAMES_RESPAWN
        # Texto de respawn con fade
        alpha_txt = int(255 * abs(math.sin(timer_respawn * 0.08)))
        msg = f"Reapareciendo en {math.ceil(timer_respawn / FPS)}s..."
        s = fuente_gr.render(msg, True, NARANJA)
        s.set_alpha(alpha_txt)
        pantalla.blit(s, (ANCHO // 2 - s.get_width() // 2, ALTO // 2 - 60))

    elif nave_muerta and vidas <= 0:
        # GAME OVER con partículas aún activas de fondo
        overlay = pygame.Surface((ANCHO, ALTO - 110), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        pantalla.blit(overlay, (0, 0))

        s = fuente_game_over.render("GAME OVER", True, ROJO)
        pantalla.blit(s, (ANCHO // 2 - s.get_width() // 2, ALTO // 2 - 80))
        s2 = fuente_gr.render(f"Puntaje final: {puntaje}", True, AMARILLO)
        pantalla.blit(s2, (ANCHO // 2 - s2.get_width() // 2, ALTO // 2 - 10))
        s3 = fuente.render("Presioná R para reiniciar", True, GRIS_CL)
        pantalla.blit(s3, (ANCHO // 2 - s3.get_width() // 2, ALTO // 2 + 40))

    # ── Panel inferior ────────────────────────────────────
    py = ALTO - 110
    pygame.draw.rect(pantalla, (10, 10, 10), (0, py, ANCHO, 110))
    pygame.draw.line(pantalla, GRIS, (0, py), (ANCHO, py), 1)

    texto(f"Puntaje: {puntaje}", (20, py + 8), AMARILLO, fuente_gr)
    texto(f"Vidas: {'♥ ' * max(vidas, 0)}", (220, py + 8), ROJO, fuente_gr)
    texto(f"Partículas: {len(particulas)}  Balas: {len(balas)}  Enemigos: {len(enemigos)}",
          (500, py + 12), GRIS_CL, fuente_ch)

    for i, (msg, col) in enumerate(log_colisiones):
        texto(msg, (20, py + 38 + i * 16),
              tuple(max(0, c - i * 30) for c in col), fuente_ch)

    texto("Flechas: mover  |  ESPACIO: disparar  |  R: resetear  |  ESC: salir",
          (20, ALTO - 18), GRIS, fuente_ch)
    texto("Círculos = radio de collide_circle", (ANCHO - 290, py + 8), GRIS, fuente_ch)

    pygame.display.flip()
    clock.tick(FPS)
