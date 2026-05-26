"""
═══════════════════════════════════════════════════════════════
 NEON RUNNER  ★  Module 10 — Final Project
═══════════════════════════════════════════════════════════════

 A complete 2D platformer unifying all course concepts:

  Module 1  → Game loop, delta time, event handling
  Module 2  → Sprites, Groups, SRCALPHA particles, kill()
  Module 3  → spritecollide, groupcollide, collide_circle
  Module 4  → Animation FSM: idle/run/jump/fall/attack/hurt/die
  Module 5  → SceneManager: Menu → Game → Pause → GameOver → Victory
  Module 6  → Generated music loop + 6 SFX (no files needed)
  Module 7  → TileMap, Camera (smooth follow, dead zone), 4-layer parallax
  Module 8  → Gravity, terminal vel, coyote time, jump buffering, variable jump
  Module 9  → Runner FSM (patrol→alert→chase→attack), Flyer (seek),
               Boss with 2 phases + projectiles

 Controls:
   A / D     move
   SPACE     jump (hold for higher)
   J         attack
   P         pause
   ESC       back to menu / quit
═══════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random
import struct

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
WIDTH, HEIGHT = 900, 620
FPS  = 60
TS   = 40        # Tile size in pixels
SR   = 44100     # Audio sample rate

# Physics
GRAVITY      = 920.0
TERM_VEL     = 820.0
JUMP_VY      = -465.0
COYOTE_F     = 8
JUMP_BUF_F   = 10
P_SPEED      = 220.0
P_ACCEL      = 1800.0

# ── Colors (neon palette) ──────────────────────────────────
BLACK    = (0,    0,   0)
WHITE    = (255, 255, 255)
DARK_BG  = (8,    8,  18)
NC       = (0,  220, 255)   # Cyan     — player
NP       = (180,   0, 255)   # Purple   — flyer
NR       = (255,  40,  40)   # Red      — runner
NM       = (255,   0, 180)   # Magenta  — boss
NG       = (0,   255, 120)   # Green    — health / safe
NY       = (255, 220,   0)   # Yellow   — score / items
NO       = (255, 140,   0)   # Orange   — warning
GRAY     = (50,   50,  70)
GRAY_LT  = (110, 110, 140)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("★  NEON RUNNER")
clock  = pygame.time.Clock()

F_SM  = pygame.font.SysFont("monospace", 12)
F_MD  = pygame.font.SysFont("monospace", 16)
F_LG  = pygame.font.SysFont("monospace", 22, bold=True)
F_TIT = pygame.font.SysFont("monospace", 52, bold=True)
F_SUB = pygame.font.SysFont("monospace", 26, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MD).render(txt, True, color), pos)

def blit_c(surf, txt, y, color=WHITE, font=None):
    s = (font or F_MD).render(txt, True, color)
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))


# ══════════════════════════════════════════════════════════
# MODULE 6 — AUDIO  (all generated with math)
# ══════════════════════════════════════════════════════════

def _pack(samples):
    clamped = [max(-1.0, min(1.0, s)) for s in samples]
    return struct.pack(f"{len(clamped)}h", *[int(s * 32767) for s in clamped])

def _sine(freq, dur, vol=0.45):
    n = int(SR * dur)
    return [vol * math.sin(2 * math.pi * freq * i / SR) for i in range(n)]

def _make(samples):
    return pygame.mixer.Sound(buffer=_pack(samples))

def _sweep(f0, f1, dur, vol=0.4):
    n = int(SR * dur)
    return [vol * (1 - i/n) * math.sin(2 * math.pi * (f0 + (f1-f0)*(i/n)) * i / SR)
            for i in range(n)]

def _noise(dur, vol=0.35):
    n = int(SR * dur)
    return [vol * (random.random()*2-1) * (1-i/n)**2 for i in range(n)]

def _chord(freqs, dur, vol=0.2):
    n  = int(SR * dur)
    out= [0.0] * n
    for f in freqs:
        for i in range(n):
            env = 1 - i/n
            out[i] += vol * env * math.sin(2 * math.pi * f * i / SR)
    return out

def build_audio():
    sfx = {}
    sfx["jump"]    = _make(_sweep(260, 600, 0.18, 0.38))
    sfx["attack"]  = _make(_sweep(500, 200, 0.12, 0.42))
    sfx["hurt"]    = _make(_noise(0.18, 0.50))
    sfx["die"]     = _make(_sweep(440, 60, 0.5, 0.40))
    sfx["kill"]    = _make(_chord([523, 659, 784], 0.18, 0.22))
    sfx["boss_hit"]= _make(_chord([220, 277], 0.25, 0.28))

    # Music: simple 2-bar chiptune loop
    dur = 2.0
    n   = int(SR * dur)
    music_s = [0.0] * n
    melody  = [262, 294, 330, 294, 262, 220, 262, 294]
    bpm     = 140
    spb     = 60 / bpm
    for bi, note in enumerate(melody):
        st = int(bi * spb / 2 * SR)
        ln = int(spb / 2 * SR * 0.75)
        for i in range(ln):
            if st + i >= n: break
            env = 1 - i / ln
            music_s[st + i] += 0.18 * env * math.sin(2*math.pi*note*i/SR)
    # Bass pulse every beat
    for bi in range(4):
        st = int(bi * spb * SR)
        ln = int(0.12 * SR)
        for i in range(ln):
            if st + i >= n: break
            env = (1 - i/ln)**3
            music_s[st + i] += 0.22 * env * (random.random()*2-1)
    sfx["music"] = _make(music_s)
    return sfx

print("Building audio…")
pygame.mixer.set_num_channels(12)
SFX = build_audio()
MUSIC_CH = pygame.mixer.Channel(11)
MUSIC_CH.play(SFX["music"], loops=-1)
MUSIC_CH.set_volume(0.35)

def play(name, vol=0.7):
    s = SFX.get(name)
    if s:
        s.set_volume(vol)
        s.play()


# ══════════════════════════════════════════════════════════
# MODULE 2 — PARTICLES
# ══════════════════════════════════════════════════════════

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, vx=None, vy=None):
        super().__init__()
        self.color = color
        self.r     = random.randint(3, 10)
        self.pos_x = float(x)
        self.pos_y = float(y)
        ang        = random.uniform(0, math.pi*2)
        spd        = random.uniform(60, 280)
        self.vx    = vx if vx is not None else math.cos(ang)*spd
        self.vy    = vy if vy is not None else math.sin(ang)*spd - random.uniform(20, 80)
        self.life  = random.uniform(160, 255)
        self.fade  = random.uniform(4, 8)
        tam        = self.r*2+2
        self.image = pygame.Surface((tam, tam), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(x), int(y)))
        self._draw()

    def _draw(self):
        self.image.fill((0,0,0,0))
        r   = self.r
        tam = r*2+2
        a   = max(0, int(self.life))
        pygame.draw.circle(self.image, (*self.color, a//3), (r+1, r+1), r)
        if r > 3:
            pygame.draw.circle(self.image, (*self.color, a), (r+1, r+1), r-2)

    def update(self, dt):
        self.vy    += 400 * dt
        self.pos_x += self.vx * dt
        self.pos_y += self.vy * dt
        self.life  -= self.fade
        if self.life <= 0:
            self.kill(); return
        self._draw()
        self.rect.centerx = int(self.pos_x)
        self.rect.centery  = int(self.pos_y)

particles = pygame.sprite.Group()

def explode(x, y, color, n=30, camera=None):
    for _ in range(n):
        sx, sy = (camera.world_to_screen(x, y) if camera else (x, y))
        particles.add(Particle(sx, sy, color))

def dust(x, y, camera=None):
    for _ in range(8):
        sx, sy = (camera.world_to_screen(x, y) if camera else (x, y))
        particles.add(Particle(sx, sy, GRAY_LT,
                               vx=random.uniform(-60, 60),
                               vy=random.uniform(-80, -20)))


# ══════════════════════════════════════════════════════════
# MODULE 7 — PARALLAX BACKGROUND
# ══════════════════════════════════════════════════════════

class ParallaxLayer:
    def __init__(self, color, factor, kind, count):
        self.color  = color
        self.factor = factor
        self.kind   = kind
        self.items  = [self._gen() for _ in range(count)]

    def _gen(self):
        if self.kind == "star":
            return [random.randint(0, WIDTH*3), random.randint(0, HEIGHT), random.randint(1,2)]
        if self.kind == "building":
            x = random.randint(0, WIDTH*3)
            h = random.randint(80, 280)
            w = random.randint(40, 100)
            return [x, HEIGHT - h, w, h]
        if self.kind == "line":
            return [random.randint(0, WIDTH*3), random.randint(30, HEIGHT-80), random.randint(40, 120)]

    def draw(self, surf, cam_x):
        ox = int(cam_x * self.factor)
        for item in self.items:
            sx = (item[0] - ox) % (WIDTH*3 + 400) - 200
            if self.kind == "star":
                pygame.draw.circle(surf, self.color, (int(sx), item[1]), item[2])
            elif self.kind == "building":
                c = self.color
                pygame.draw.rect(surf, c, (int(sx), item[1], item[2], item[3]))
                # Windows
                for wy in range(item[1]+10, item[1]+item[3]-10, 18):
                    for wx in range(int(sx)+6, int(sx)+item[2]-6, 14):
                        if random.random() > 0.4:
                            wc = (min(255,c[0]+80), min(255,c[1]+80), min(255,c[2]+80))
                            pygame.draw.rect(surf, wc, (wx, wy, 8, 10))
            elif self.kind == "line":
                pygame.draw.line(surf, self.color, (int(sx), item[1]),
                                 (int(sx)+item[2], item[1]+4), 1)

BG_LAYERS = [
    ParallaxLayer((15, 15, 35),     0.04, "star",     140),
    ParallaxLayer((22, 22, 55),     0.08, "star",      60),
    ParallaxLayer((18, 10, 40),     0.12, "building",  12),
    ParallaxLayer((25, 15, 55),     0.22, "building",   8),
    ParallaxLayer((0,  40, 80),     0.35, "line",      20),
]

def draw_parallax(surf, cam_x):
    surf.fill(DARK_BG)
    for layer in BG_LAYERS:
        layer.draw(surf, cam_x)


# ══════════════════════════════════════════════════════════
# MODULE 7 — TILEMAP & CAMERA
# ══════════════════════════════════════════════════════════

_  = 0   # air
P  = 1   # neon platform
G  = 2   # ground

LEVEL = [
# col: 0         1         2         3         4
#      0123456789012345678901234567890123456789012345678901
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,P,_,_,_,_,_,_,_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,P,P,P,_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,_,_,P,P,_,_,_,_,_,_,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,G,G,G,G,G,G,G,G],
    [_,_,_,P,P,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G,_,_,_,_,_,_,G],
    [_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,P,_,_,_,_,_,_,_,G,_,_,_,_,_,_,G],
    [P,P,P,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,P,P,P,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G,_,_,_,_,_,_,G],
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
]
LEVEL_COLS = len(LEVEL[0])
LEVEL_ROWS = len(LEVEL)
WORLD_W    = LEVEL_COLS * TS
WORLD_H    = LEVEL_ROWS * TS

# Pre-build all solid rects
ALL_SOLID = []
for _r, _row in enumerate(LEVEL):
    for _c, _t in enumerate(_row):
        if _t != 0:
            ALL_SOLID.append(pygame.Rect(_c*TS, _r*TS, TS, TS))


class Camera:
    def __init__(self):
        self.x = 0.0; self.y = 0.0
        self.smooth = 7.0
        self.dead   = pygame.Rect(WIDTH//2-100, HEIGHT//2-80, 200, 160)
        self._shake = 0.0; self._sstr = 0.0
        self._off   = (0, 0)

    def world_to_screen(self, wx, wy):
        return (int((wx - self.x) + self._off[0]),
                int((wy - self.y) + self._off[1]))

    def follow(self, wx, wy, dt):
        tsx = (wx - self.x)
        tsy = (wy - self.y)
        if tsx < self.dead.left:   self.x += (wx - self.dead.left  - self.x) * self.smooth * dt
        elif tsx > self.dead.right: self.x += (wx - self.dead.right - self.x) * self.smooth * dt
        if tsy < self.dead.top:    self.y += (wy - self.dead.top   - self.y) * self.smooth * dt
        elif tsy > self.dead.bottom: self.y += (wy - self.dead.bottom- self.y) * self.smooth * dt
        self.x = max(0, min(self.x, WORLD_W - WIDTH))
        self.y = max(0, min(self.y, WORLD_H - HEIGHT))
        if self._shake > 0:
            self._shake -= dt
            p = self._shake / 0.3
            self._off = (random.uniform(-1,1)*self._sstr*p,
                         random.uniform(-1,1)*self._sstr*p)
        else:
            self._off = (0, 0)

    def shake(self, strength=6.0):
        self._shake = 0.3; self._sstr = strength


def draw_tilemap(surf, camera):
    cx, cy = camera.x, camera.y
    cs = max(0, int(cx // TS))
    ce = min(LEVEL_COLS, int((cx + WIDTH) // TS) + 1)
    rs = max(0, int(cy // TS))
    re = min(LEVEL_ROWS, int((cy + HEIGHT) // TS) + 1)
    for r in range(rs, re):
        for c in range(cs, ce):
            t = LEVEL[r][c]
            if t == 0: continue
            sx, sy = camera.world_to_screen(c*TS, r*TS)
            col  = (20, 20, 35) if t == G else (15, 15, 28)
            glow = (0, 70, 120) if t == P else (50, 0, 90)
            pygame.draw.rect(surf, col,  (sx, sy, TS, TS))
            pygame.draw.rect(surf, glow, (sx, sy, TS, TS), 1)
            # Top edge glow
            top_col = NC if t == P else NP
            pygame.draw.line(surf, top_col, (sx, sy), (sx+TS, sy), 1)


def solid_rects_near(wx, wy):
    c = int(wx // TS); r = int(wy // TS)
    rects = []
    for dr in range(-2, 4):
        for dc in range(-2, 4):
            rc = c+dc; rr = r+dr
            if 0 <= rr < LEVEL_ROWS and 0 <= rc < LEVEL_COLS:
                if LEVEL[rr][rc] != 0:
                    rects.append(pygame.Rect(rc*TS, rr*TS, TS, TS))
    return rects


# ══════════════════════════════════════════════════════════
# MODULE 8 + 4 — PLAYER
# ══════════════════════════════════════════════════════════

class Player(pygame.sprite.Sprite):
    W, H   = 26, 36
    MAX_HP = 5

    def __init__(self):
        super().__init__()
        self.image  = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect   = self.image.get_rect()
        self.reset()

    def reset(self):
        self.x = 2.5 * TS; self.y = 9.5 * TS
        self.vx = 0.0;      self.vy = 0.0
        self.on_ground  = False
        self.facing     = 1
        self.coyote     = 0
        self.jump_buf   = 0
        self.jumping    = False
        self.jump_frames= 0
        self.hp         = self.MAX_HP
        self.score      = 0
        self.invincible = 0.0   # seconds of invincibility after hurt
        self.state      = "IDLE"
        self.anim_t     = 0.0
        self.attack_box = None  # pygame.Rect or None
        self.attack_timer = 0.0
        self.hurt_flash = 0.0
        self.alive      = True
        self.rect.topleft = (int(self.x), int(self.y))

    def take_damage(self, camera=None):
        if self.invincible > 0 or not self.alive:
            return
        self.hp        -= 1
        self.invincible = 1.2
        self.hurt_flash = 0.3
        self.state      = "HURT"
        play("hurt")
        if camera: camera.shake(8)
        if self.hp <= 0:
            self.state = "DIE"
            self.alive = False
            play("die")

    def update(self, dt, keys_held, jump_pressed, attack_pressed, camera=None):
        if not self.alive:
            self.anim_t += dt
            self._draw()
            return

        self.anim_t      += dt
        self.invincible   = max(0, self.invincible - dt)
        self.hurt_flash   = max(0, self.hurt_flash - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        if self.attack_timer <= 0:
            self.attack_box = None

        # ── Attack ───────────────────────────────────────
        if attack_pressed and self.attack_timer <= 0:
            self.attack_timer = 0.25
            ax = self.x + (self.W if self.facing > 0 else -36)
            self.attack_box = pygame.Rect(int(ax), int(self.y+4), 36, 28)
            self.state      = "ATTACK"
            play("attack", 0.5)

        # ── Horizontal movement ───────────────────────────
        target = 0.0
        if keys_held[pygame.K_a]: target = -P_SPEED; self.facing = -1
        if keys_held[pygame.K_d]: target =  P_SPEED; self.facing =  1
        step = P_ACCEL * dt
        if target != 0:
            self.vx += math.copysign(min(abs(target - self.vx), step), target - self.vx)
        else:
            dec = min(abs(self.vx), step)
            self.vx -= math.copysign(dec, self.vx) if self.vx else 0

        # ── Coyote & jump buffer ──────────────────────────
        self.coyote   = COYOTE_F if self.on_ground else max(0, self.coyote - 1)
        self.jump_buf = max(0, self.jump_buf - 1)
        if jump_pressed:
            self.jump_buf = JUMP_BUF_F

        can_jump = self.on_ground or self.coyote > 0
        if self.jump_buf > 0 and can_jump:
            self.vy        = JUMP_VY
            self.jumping   = True
            self.jump_frames = 0
            self.jump_buf  = 0
            self.coyote    = 0
            self.on_ground = False
            play("jump", 0.55)
            dust(self.x + self.W//2, self.y + self.H, camera)

        # Variable jump
        if self.jumping:
            self.jump_frames += 1
            if (not keys_held[pygame.K_SPACE] and self.jump_frames > 6) or self.jump_frames > 20:
                self.jumping = False
        grav_mult = 0.38 if self.jumping else 1.0
        self.vy = min(self.vy + GRAVITY * grav_mult * dt, TERM_VEL)

        # ── Move X ───────────────────────────────────────
        self.x += self.vx * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                self.x = r.right if self.vx < 0 else r.left - self.W
                self.vx = 0

        # ── Move Y ───────────────────────────────────────
        self.on_ground = False
        self.y += self.vy * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.H
                    self.vy = 0
                    was_falling = self.state == "FALL"
                    self.on_ground = True
                    self.jumping   = False
                    if was_falling:
                        dust(self.x + self.W//2, self.y + self.H, camera)
                elif self.vy < 0:
                    self.y = r.bottom; self.vy = 0

        self.x = max(0, min(self.x, WORLD_W - self.W))
        if self.y > WORLD_H + 100:
            self.take_damage(camera)
            self.x = 2.5*TS; self.y = 9.5*TS; self.vy = 0

        # ── Determine animation state ─────────────────────
        if self.hurt_flash > 0:          self.state = "HURT"
        elif self.attack_timer > 0:      self.state = "ATTACK"
        elif not self.on_ground and self.vy < 0: self.state = "JUMP"
        elif not self.on_ground:         self.state = "FALL"
        elif abs(self.vx) > 10:          self.state = "RUN"
        else:                            self.state = "IDLE"

        self.rect.topleft = (int(self.x), int(self.y))
        self._draw()

    def _draw(self):
        surf = self.image
        surf.fill((0,0,0,0))
        t   = self.anim_t
        w, h= self.W, self.H
        st  = self.state

        # Choose body color
        if st == "HURT":       body = WHITE
        elif st == "ATTACK":   body = (180, 240, 255)
        elif not self.alive:   body = GRAY
        else:                  body = NC

        # Body
        bob = int(2*math.sin(t*4)) if st == "IDLE" else 0
        pygame.draw.rect(surf, body, (2, 2+bob, w-4, h-4), border_radius=5)
        pygame.draw.rect(surf, WHITE, (2, 2+bob, w-4, h-4), 1, border_radius=5)

        # Eyes (flip direction via facing handled at draw-time)
        ex = w-10 if self.facing > 0 else 6
        if self.alive:
            pygame.draw.circle(surf, WHITE, (ex, 12+bob), 5)
            pygame.draw.circle(surf, BLACK, (ex+self.facing, 12+bob), 3)
        else:
            # Dead eyes (X)
            pygame.draw.line(surf, RED, (ex-3, 9+bob), (ex+3, 15+bob), 2)
            pygame.draw.line(surf, RED, (ex+3, 9+bob), (ex-3, 15+bob), 2)

        # Run legs
        if st == "RUN":
            for leg, side in [(0, -1), (1, 1)]:
                ang  = math.sin(t*10 + leg*math.pi) * 0.5
                lx   = w//2 + side*6
                ly   = h - 6
                ex2  = lx + int(math.sin(ang)*8)
                ey2  = ly + int(math.cos(abs(ang))*8)
                pygame.draw.line(surf, NC, (lx, ly), (ex2, ey2), 3)

        # Attack fist
        if st == "ATTACK":
            fx = w-2 if self.facing > 0 else 2
            pygame.draw.circle(surf, NY, (fx, h//2), 7)
            pygame.draw.circle(surf, WHITE, (fx, h//2), 7, 1)

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        # Attack hitbox debug
        if self.attack_box:
            asx, asy = camera.world_to_screen(self.attack_box.x, self.attack_box.y)
            dsurf = pygame.Surface((self.attack_box.w, self.attack_box.h), pygame.SRCALPHA)
            dsurf.fill((*NY, 60))
            surf.blit(dsurf, (asx, asy))
        # Invincibility flicker
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            ds = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ds.fill((255,255,255,80))
            surf.blit(ds, (sx, sy))


# ══════════════════════════════════════════════════════════
# MODULE 3 — PROJECTILE
# ══════════════════════════════════════════════════════════

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, color=NM):
        super().__init__()
        self.pos_x = float(x); self.pos_y = float(y)
        self.vx = vx; self.vy = vy; self.color = color
        self.radius = 8
        self.image  = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (10,10), 8)
        pygame.draw.circle(self.image, WHITE, (10,10), 8, 1)
        self.rect   = self.image.get_rect(center=(int(x), int(y)))
        self.life   = 4.0

    def update(self, dt):
        self.pos_x += self.vx * dt
        self.pos_y += self.vy * dt
        self.life  -= dt
        self.rect.center = (int(self.pos_x), int(self.pos_y))
        for r in solid_rects_near(self.pos_x, self.pos_y):
            if self.rect.colliderect(r):
                self.kill(); return
        if self.life <= 0 or not (0 < self.pos_x < WORLD_W):
            self.kill()

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.pos_x, self.pos_y)
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, self.color, (10,10), 8)
        pygame.draw.circle(s, WHITE, (10,10), 8, 1)
        surf.blit(s, (sx-10, sy-10))


# ══════════════════════════════════════════════════════════
# MODULE 9 — ENEMIES
# ══════════════════════════════════════════════════════════

class RunnerEnemy(pygame.sprite.Sprite):
    """FSM: PATROL → ALERT → CHASE → ATTACK"""
    W, H   = 28, 32
    MAX_HP = 3
    RADIUS = 16

    def __init__(self, x, y):
        super().__init__()
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.hp    = self.MAX_HP
        self.state = "PATROL"
        self.state_t = 0.0
        self.facing  = 1
        self.patrol_dir = random.choice([-1, 1])
        self.anim_t  = 0.0
        self.alive   = True
        self.image   = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect    = self.image.get_rect(topleft=(int(x), int(y)))

    @property
    def center(self): return (self.x + self.W//2, self.y + self.H//2)

    def take_damage(self, camera=None):
        self.hp -= 1
        play("kill", 0.5)
        return self.hp <= 0

    def update(self, dt, px, py, camera=None):
        if not self.alive: return
        self.anim_t  += dt
        self.state_t += dt
        cx, cy = self.center
        dist   = math.hypot(px - cx, py - cy)

        # ── FSM transitions ───────────────────────────────
        if self.state == "PATROL":
            if dist < 180: self._go("ALERT")
        elif self.state == "ALERT":
            if self.state_t > 0.8:
                self._go("CHASE" if dist < 200 else "PATROL")
        elif self.state == "CHASE":
            if dist < 34: self._go("ATTACK")
            elif dist > 240 and self.state_t > 2: self._go("PATROL")
        elif self.state == "ATTACK":
            if dist > 50: self._go("CHASE")

        # ── Per-state movement ────────────────────────────
        if self.state == "PATROL":
            self.vx = self.patrol_dir * 60.0
            self.facing = int(math.copysign(1, self.vx))
        elif self.state == "CHASE":
            self.vx = math.copysign(120.0, px - cx)
            self.facing = int(math.copysign(1, self.vx))
        elif self.state in ("ALERT", "ATTACK"):
            self.vx *= 0.8

        # ── Physics ───────────────────────────────────────
        self.vy = min(self.vy + GRAVITY * dt, TERM_VEL)
        self.x += self.vx * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                self.patrol_dir *= -1
                self.vx = 0; break
        self.on_ground = False
        self.y += self.vy * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.H; self.vy = 0; self.on_ground = True
                elif self.vy < 0:
                    self.y = r.bottom; self.vy = 0
        self.x = max(0, min(self.x, WORLD_W - self.W))
        self.rect.topleft = (int(self.x), int(self.y))
        self._draw()

    def _go(self, s):
        self.state = s; self.state_t = 0.0

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        t = self.anim_t
        col = WHITE if self.state == "ALERT" else NR
        bob = int(2*math.sin(t*8)) if self.state == "CHASE" else 0
        pygame.draw.ellipse(s, col, (2, 2+bob, self.W-4, self.H-4))
        pygame.draw.ellipse(s, WHITE, (2, 2+bob, self.W-4, self.H-4), 1)
        ex = self.W-9 if self.facing > 0 else 5
        pygame.draw.circle(s, BLACK, (ex, 12+bob), 4)
        pygame.draw.circle(s, WHITE, (ex, 12+bob), 4, 1)
        pygame.draw.circle(s, BLACK, (ex+self.facing, 12+bob), 2)
        # HP pip
        for i in range(self.hp):
            pygame.draw.rect(s, NG, (2+i*8, 0, 6, 3))

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        sc = STATE_COLORS_E.get(self.state, GRAY_LT)
        blit(surf, self.state, (sx, sy - 14), sc, F_SM)

STATE_COLORS_E = {"PATROL": NC, "ALERT": NY, "CHASE": NO, "ATTACK": NR}


class FlyerEnemy(pygame.sprite.Sprite):
    """Seeks player from the air, always hovering."""
    RADIUS = 14
    MAX_HP = 2

    def __init__(self, x, y):
        super().__init__()
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.hp     = self.MAX_HP
        self.alive  = True
        self.anim_t = 0.0
        self.state  = "SEEK"
        self.image  = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect   = self.image.get_rect(center=(int(x), int(y)))

    @property
    def center(self): return (self.x, self.y)

    def take_damage(self, camera=None):
        self.hp -= 1
        play("kill", 0.5)
        return self.hp <= 0

    def update(self, dt, px, py, camera=None):
        if not self.alive: return
        self.anim_t += dt
        dx  = px - self.x; dy = py - self.y
        dist= math.hypot(dx, dy)
        # Seek with arrival
        spd = min(140.0, dist * 1.5)
        if dist > 1:
            fx = (dx/dist)*spd - self.vx
            fy = (dy/dist)*spd - self.vy
            fmag = math.hypot(fx, fy)
            if fmag > 300:
                fx = fx/fmag*300; fy = fy/fmag*300
            self.vx += fx * dt; self.vy += fy * dt
        self.x += self.vx * dt; self.y += self.vy * dt
        self.x = max(0, min(self.x, WORLD_W)); self.y = max(10, min(self.y, WORLD_H-40))
        self.rect.center = (int(self.x), int(self.y))
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        t = self.anim_t
        bob = int(4*math.sin(t*4))
        pts = [(15, 2+bob), (28, 15+bob), (15, 28+bob), (2, 15+bob)]
        pygame.draw.polygon(s, NP, pts)
        pygame.draw.polygon(s, WHITE, pts, 1)
        for i in range(self.hp):
            pygame.draw.rect(s, NG, (4+i*10, 0, 8, 3))

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x - 15, self.y - 15)
        surf.blit(self.image, (sx, sy))


# ══════════════════════════════════════════════════════════
# MODULE 9 — BOSS  (2 phases)
# ══════════════════════════════════════════════════════════

class Boss(pygame.sprite.Sprite):
    W, H   = 64, 72
    MAX_HP = 200
    RADIUS = 34

    def __init__(self, x, y):
        super().__init__()
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.hp       = self.MAX_HP
        self.alive    = True
        self.phase    = 1
        self.dir      = 1
        self.shoot_cd = 0.0
        self.anim_t   = 0.0
        self.hurt_t   = 0.0
        self.projectiles = pygame.sprite.Group()
        self.image    = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect     = self.image.get_rect(topleft=(int(x), int(y)))

    def take_damage(self):
        self.hp    -= 20
        self.hurt_t = 0.2
        play("boss_hit", 0.6)
        if self.hp <= self.MAX_HP // 2 and self.phase == 1:
            self.phase = 2
            play("hurt", 0.8)
        return self.hp <= 0

    def update(self, dt, px, py, camera=None):
        if not self.alive: return
        self.anim_t  += dt
        self.hurt_t   = max(0, self.hurt_t - dt)
        self.shoot_cd = max(0, self.shoot_cd - dt)

        spd = 80.0 if self.phase == 1 else 130.0
        self.vx = self.dir * spd
        self.x += self.vx * dt
        # Bounce in boss arena (cols 42-49)
        if self.x < 42*TS + 4:
            self.x = 42*TS + 4; self.dir = 1
        if self.x > 48*TS - self.W:
            self.x = 48*TS - self.W; self.dir = -1

        # Gravity
        self.vy = min(self.vy + GRAVITY * dt, TERM_VEL)
        self.y += self.vy * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                if self.vy > 0: self.y = r.top - self.H; self.vy = 0
                elif self.vy < 0: self.y = r.bottom; self.vy = 0

        # Shoot
        interval = 2.0 if self.phase == 1 else 1.1
        if self.shoot_cd <= 0:
            self.shoot_cd = interval
            cx = self.x + self.W//2; cy = self.y + self.H//2
            shots = 3 if self.phase == 1 else 5
            for i in range(shots):
                ang = math.atan2(py - cy, px - cx) + (i-(shots//2)) * 0.25
                spd2 = 200.0
                self.projectiles.add(
                    Projectile(cx, cy, math.cos(ang)*spd2, math.sin(ang)*spd2))

        self.projectiles.update(dt)
        self.rect.topleft = (int(self.x), int(self.y))
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        t = self.anim_t
        col = WHITE if self.hurt_t > 0 else (NM if self.phase == 1 else NR)
        bob = int(3*math.sin(t*3))
        pygame.draw.rect(s, col, (4, 4+bob, self.W-8, self.H-8), border_radius=8)
        pygame.draw.rect(s, WHITE, (4, 4+bob, self.W-8, self.H-8), 2, border_radius=8)
        # Eyes
        for ex in [16, self.W-20]:
            pygame.draw.circle(s, WHITE, (ex, 20+bob), 8)
            pygame.draw.circle(s, BLACK, (ex+self.dir*2, 20+bob), 5)
            pygame.draw.circle(s, (255,50,50), (ex+self.dir*2, 20+bob), 2)
        # Mouth
        pygame.draw.arc(s, WHITE, (14, 34+bob, self.W-28, 18), math.pi, 0, 2)
        # HP bar above
        hpw = int((self.W - 8) * max(0, self.hp / self.MAX_HP))
        pygame.draw.rect(s, GRAY, (4, 0, self.W-8, 5))
        c = NG if self.hp > self.MAX_HP//2 else NR
        pygame.draw.rect(s, c, (4, 0, hpw, 5))
        # Phase 2 indicator
        if self.phase == 2:
            pygame.draw.rect(s, NR, (4, 0, self.W-8, 5), 1)

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        phase_col = NM if self.phase == 1 else NR
        blit(surf, f"BOSS  Phase {self.phase}", (sx, sy-16), phase_col, F_SM)
        for p in self.projectiles:
            p.draw(surf, camera)


# ══════════════════════════════════════════════════════════
# MODULE 5 — SCENE MANAGER
# ══════════════════════════════════════════════════════════

class Scene:
    def __init__(self, mgr): self.mgr = mgr
    def enter(self):          pass
    def exit(self):           pass
    def handle_event(self, ev): pass
    def update(self, dt):     pass
    def draw(self, surf):     pass

class SceneManager:
    def __init__(self):
        self._stack  = []
        self.running = True
        self.shared  = {}

    @property
    def current(self): return self._stack[-1] if self._stack else None

    def push(self, scene):
        if self._stack: self._stack[-1].exit()
        self._stack.append(scene); scene.enter()

    def pop(self):
        self._stack.pop().exit()
        if self._stack: self._stack[-1].enter()

    def replace(self, scene):
        if self._stack: self._stack.pop().exit()
        self._stack.append(scene); scene.enter()

    def run(self):
        while self.running and self.current:
            dt = clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                self.current.handle_event(ev)
            self.current.update(dt)
            self.current.draw(screen)
            pygame.display.flip()
        pygame.quit(); sys.exit()


# ══════════════════════════════════════════════════════════
# SCENE: MENU
# ══════════════════════════════════════════════════════════

class MenuScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.t = 0.0

    def enter(self):
        MUSIC_CH.set_volume(0.35)
        pygame.display.set_caption("★  NEON RUNNER")

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                self.mgr.replace(GameScene(self.mgr))
            if ev.key == pygame.K_ESCAPE:
                self.mgr.running = False

    def update(self, dt): self.t += dt

    def draw(self, surf):
        draw_parallax(surf, self.t * 40)
        # Title glow effect
        pulse = abs(math.sin(self.t * 1.8))
        tc = (int(0 + 220*pulse), int(180+75*pulse), 255)
        blit_c(surf, "★  NEON RUNNER  ★", 160, tc, F_TIT)
        blit_c(surf, "A complete pygame platformer", 240, GRAY_LT, F_MD)

        # Controls list
        items = [
            ("A / D",    "Move"),
            ("SPACE",    "Jump  (hold = higher)"),
            ("J",        "Attack"),
            ("P",        "Pause"),
        ]
        blit_c(surf, "Controls", 310, NC, F_LG)
        for i, (key, desc) in enumerate(items):
            blit_c(surf, f"[{key}]  {desc}", 342 + i*28, GRAY_LT, F_MD)

        # Blinking ENTER
        if int(self.t * 2) % 2 == 0:
            blit_c(surf, "PRESS  ENTER  TO  START", 510, NY, F_LG)
        blit_c(surf, "ESC: quit", 552, GRAY, F_SM)

        # Module credits strip
        pygame.draw.rect(surf, (12, 12, 25), (0, HEIGHT-34, WIDTH, 34))
        pygame.draw.line(surf, GRAY, (0, HEIGHT-34), (WIDTH, HEIGHT-34), 1)
        blit_c(surf,
               "Modules 1-9: game loop · sprites · collisions · animations · "
               "scenes · audio · tilemap · physics · AI",
               HEIGHT-20, GRAY, F_SM)


# ══════════════════════════════════════════════════════════
# SCENE: GAME
# ══════════════════════════════════════════════════════════

ENEMY_SPAWNS = [
    ("runner", 8,  10), ("runner", 19, 10), ("runner", 31,  9),
    ("flyer",  14,  6), ("flyer",  35,  5),
]
BOSS_SPAWN = (45.5 * TS, 9 * TS)

class GameScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr)
        self._jump_pressed   = False
        self._attack_pressed = False
        self._keys           = {}

    def enter(self):
        pygame.display.set_caption("★  NEON RUNNER")
        MUSIC_CH.set_volume(0.35)
        particles.empty()
        self.camera   = Camera()
        self.player   = Player()
        self.runners  = pygame.sprite.Group()
        self.flyers   = pygame.sprite.Group()
        self.enemies  = pygame.sprite.Group()   # All enemies combined
        self.boss           = None
        self.boss_triggered = False
        self.victory_timer  = 0.0

        for kind, c, r in ENEMY_SPAWNS:
            if kind == "runner":
                e = RunnerEnemy(c*TS, r*TS - 32)
                self.runners.add(e); self.enemies.add(e)
            else:
                e = FlyerEnemy(c*TS, r*TS)
                self.flyers.add(e); self.enemies.add(e)

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.mgr.replace(MenuScene(self.mgr))
            if ev.key == pygame.K_p:
                self.mgr.push(PauseScene(self.mgr))
            if ev.key == pygame.K_SPACE:
                self._jump_pressed = True
            if ev.key == pygame.K_j:
                self._attack_pressed = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self._jump_pressed,
                           self._attack_pressed, self.camera)
        self._jump_pressed   = False
        self._attack_pressed = False

        px = self.player.x + self.player.W//2
        py = self.player.y + self.player.H//2

        # Spawn boss when player enters arena
        if px > 41 * TS and not self.boss_triggered:
            self.boss_triggered = True
            self.boss = Boss(*BOSS_SPAWN)
            MUSIC_CH.set_volume(0.55)

        for e in list(self.runners):
            e.update(dt, px, py, self.camera)
        for e in list(self.flyers):
            e.update(dt, px, py, self.camera)
        if self.boss and self.boss.alive:
            self.boss.update(dt, px, py, self.camera)

        particles.update(dt)
        self.camera.follow(px, py, dt)

        # ── MODULE 3: Collisions ───────────────────────────

        # Player attack hits runners
        if self.player.attack_box:
            ab = self.player.attack_box
            for e in list(self.runners):
                if ab.colliderect(pygame.Rect(int(e.x), int(e.y), e.W, e.H)):
                    dead = e.take_damage(self.camera)
                    explode(e.x + e.W//2, e.y + e.H//2, NR, 20, self.camera)
                    if dead:
                        e.kill()
                        self.player.score += 10
            for e in list(self.flyers):
                er = pygame.Rect(int(e.x-14), int(e.y-14), 28, 28)
                if ab.colliderect(er):
                    dead = e.take_damage(self.camera)
                    explode(e.x, e.y, NP, 20, self.camera)
                    if dead:
                        e.kill()
                        self.player.score += 20
            if self.boss and self.boss.alive:
                br = pygame.Rect(int(self.boss.x), int(self.boss.y),
                                 self.boss.W, self.boss.H)
                if ab.colliderect(br):
                    dead = self.boss.take_damage()
                    explode(self.boss.x + self.boss.W//2,
                            self.boss.y + self.boss.H//2, NM, 15, self.camera)
                    if dead:
                        self.boss.alive = False
                        explode(self.boss.x + self.boss.W//2,
                                self.boss.y + self.boss.H//2, NM, 60, self.camera)
                        self.mgr.shared["score"] = self.player.score + 100
                        self.victory_timer = 0.001   # start countdown

        # Victory countdown (replaces unreliable USEREVENT approach)
        if self.victory_timer > 0:
            self.victory_timer += dt
            if self.victory_timer >= 2.0:
                self.mgr.replace(VictoryScene(self.mgr))
                return

        # Enemy bodies hurt player
        if self.player.alive:
            pr = pygame.Rect(int(self.player.x), int(self.player.y),
                             self.player.W, self.player.H)
            for e in list(self.runners):
                if e.state == "ATTACK":
                    if pr.colliderect(pygame.Rect(int(e.x), int(e.y), e.W, e.H)):
                        self.player.take_damage(self.camera)
            for e in list(self.flyers):
                er = pygame.Rect(int(e.x-14), int(e.y-14), 28, 28)
                if pr.colliderect(er):
                    self.player.take_damage(self.camera)
            if self.boss and self.boss.alive:
                br = pygame.Rect(int(self.boss.x), int(self.boss.y),
                                 self.boss.W, self.boss.H)
                if pr.colliderect(br):
                    self.player.take_damage(self.camera)
                # Boss projectiles
                for proj in list(self.boss.projectiles):
                    projr = pygame.Rect(int(proj.pos_x)-8, int(proj.pos_y)-8, 16, 16)
                    if pr.colliderect(projr):
                        self.player.take_damage(self.camera)
                        proj.kill()
                        explode(proj.pos_x, proj.pos_y, NM, 10, self.camera)

        # Check game over
        if not self.player.alive and self.player.state == "DIE":
            if self.player.anim_t > 1.5:
                self.mgr.shared["score"] = self.player.score
                self.mgr.replace(GameOverScene(self.mgr))

    def draw(self, surf):
        draw_parallax(surf, self.camera.x)
        draw_tilemap(surf, self.camera)

        # Draw enemies
        for e in self.runners: e.draw(surf, self.camera)
        for e in self.flyers:  e.draw(surf, self.camera)
        if self.boss and self.boss.alive:
            self.boss.draw(surf, self.camera)

        self.player.draw(surf, self.camera)
        particles.draw(surf)

        # ── HUD ─────────────────────────────────────────────
        hud_y = HEIGHT - 48
        pygame.draw.rect(surf, (8, 8, 18), (0, hud_y, WIDTH, 48))
        pygame.draw.line(surf, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

        # HP hearts
        for i in range(self.player.MAX_HP):
            col = NG if i < self.player.hp else GRAY
            pygame.draw.circle(surf, col, (26 + i*28, hud_y+16), 10)
            pygame.draw.circle(surf, WHITE, (26 + i*28, hud_y+16), 10, 1)
        blit(surf, "HP", (14, hud_y+30), GRAY, F_SM)

        # Score
        blit(surf, f"SCORE  {self.player.score:04d}", (200, hud_y+12), NY, F_LG)

        # Enemy count
        alive_e = len([e for e in self.runners if e.alive]) + \
                  len([e for e in self.flyers if e.alive])
        blit(surf, f"Enemies: {alive_e}", (440, hud_y+12), NR, F_MD)

        # Boss HP bar
        if self.boss and self.boss.alive:
            bw = int(300 * self.boss.hp / self.boss.MAX_HP)
            pygame.draw.rect(surf, GRAY, (WIDTH//2-150, hud_y+8, 300, 14))
            c2 = NG if self.boss.phase == 1 else NR
            pygame.draw.rect(surf, c2, (WIDTH//2-150, hud_y+8, bw, 14))
            pygame.draw.rect(surf, WHITE, (WIDTH//2-150, hud_y+8, 300, 14), 1)
            p2 = f"BOSS  Phase {self.boss.phase}  HP: {self.boss.hp}/{self.boss.MAX_HP}"
            blit_c(surf, p2, hud_y+28, NM if self.boss.phase==1 else NR, F_SM)

        blit(surf, "A/D: move  SPACE: jump  J: attack  P: pause",
             (WIDTH-340, hud_y+32), GRAY, F_SM)

        # Arrow toward boss if not triggered
        if not self.boss_triggered:
            ax = WIDTH - 60
            blit(surf, "BOSS →", (ax-50, hud_y-20), NM, F_SM)


# ══════════════════════════════════════════════════════════
# SCENE: PAUSE
# ══════════════════════════════════════════════════════════

class PauseScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.bg = screen.copy()

    def enter(self): MUSIC_CH.set_volume(0.1)
    def exit(self):  MUSIC_CH.set_volume(0.35)

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_p, pygame.K_RETURN):
                self.mgr.pop()
            if ev.key == pygame.K_ESCAPE:
                self.mgr.replace(MenuScene(self.mgr))

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160)); surf.blit(ov, (0, 0))
        blit_c(surf, "⏸  PAUSED", HEIGHT//2 - 80, NC, F_TIT)
        blit_c(surf, "ENTER / P  →  Resume",  HEIGHT//2,     NG, F_LG)
        blit_c(surf, "ESC        →  Main Menu", HEIGHT//2+46, NR, F_MD)


# ══════════════════════════════════════════════════════════
# SCENE: GAME OVER
# ══════════════════════════════════════════════════════════

class GameOverScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.t = 0.0
        self.score = mgr.shared.get("score", 0)

    def enter(self): MUSIC_CH.set_volume(0.15)

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                self.mgr.replace(GameScene(self.mgr))
            if ev.key == pygame.K_ESCAPE:
                self.mgr.replace(MenuScene(self.mgr))

    def update(self, dt):
        self.t += dt
        particles.update(dt)

    def draw(self, surf):
        draw_parallax(surf, self.t * 20)
        particles.draw(surf)
        pulse = abs(math.sin(self.t * 2.5))
        col   = (int(200+55*pulse), int(30+10*pulse), int(30+10*pulse))
        blit_c(surf, "GAME  OVER", HEIGHT//2 - 100, col, F_TIT)
        blit_c(surf, f"Score: {self.score}", HEIGHT//2 - 10, NY, F_SUB)
        blit_c(surf, "ENTER  →  Try Again", HEIGHT//2 + 60, NG, F_LG)
        blit_c(surf, "ESC    →  Main Menu",  HEIGHT//2 + 104, GRAY_LT, F_MD)


# ══════════════════════════════════════════════════════════
# SCENE: VICTORY
# ══════════════════════════════════════════════════════════

class VictoryScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.t = 0.0
        self.score = mgr.shared.get("score", 0)

    def enter(self):
        MUSIC_CH.set_volume(0.55)
        # Fireworks burst
        for _ in range(8):
            x = random.randint(100, WIDTH-100)
            y = random.randint(80, HEIGHT-100)
            col = random.choice([NC, NP, NG, NY, NM, NR])
            particles.add(*[Particle(x, y, col) for _ in range(20)])

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                self.mgr.replace(GameScene(self.mgr))
            if ev.key == pygame.K_ESCAPE:
                self.mgr.replace(MenuScene(self.mgr))

    def update(self, dt):
        self.t += dt
        particles.update(dt)
        if random.random() < 0.06:
            x = random.randint(60, WIDTH-60)
            y = random.randint(60, HEIGHT-60)
            col = random.choice([NC, NP, NG, NY, NM])
            for _ in range(12):
                particles.add(Particle(x, y, col))

    def draw(self, surf):
        draw_parallax(surf, self.t * 30)
        particles.draw(surf)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100)); surf.blit(ov, (0, 0))
        pulse = abs(math.sin(self.t * 3))
        col   = (int(0+255*pulse), int(200+55*pulse), 255)
        blit_c(surf, "★  VICTORY  ★", HEIGHT//2 - 110, col, F_TIT)
        blit_c(surf, "You defeated the BOSS!", HEIGHT//2 - 20, NC, F_SUB)
        blit_c(surf, f"Final Score: {self.score}", HEIGHT//2 + 30, NY, F_SUB)
        blit_c(surf, "ENTER  →  Play Again", HEIGHT//2 + 90, NG, F_LG)
        blit_c(surf, "ESC    →  Main Menu",  HEIGHT//2+130, GRAY_LT, F_MD)


# ══════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    mgr = SceneManager()
    mgr.push(MenuScene(mgr))
    mgr.run()
