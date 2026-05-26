"""
████████████████████████████████████████████████████████████
 SHADOW VAULT  ★  Module 10 — Alternate Final Project
████████████████████████████████████████████████████████████

 A dungeon platformer: collect 3 keys, open the vault door,
 escape without being caught by the guards.

  Module 1  → Game loop, delta time, event handling
  Module 2  → Sprites, Groups, SRCALPHA particles
  Module 3  → colliderect, spritecollide, LOS raycast
  Module 4  → Player animation FSM (idle/walk/jump/crouch/attack/hurt/die)
  Module 5  → SceneManager: Menu → Game → Pause → GameOver → Victory
  Module 6  → Generated ambient audio + 7 SFX (no files needed)
  Module 7  → Stone tilemap, Camera (smooth + shake), torch lighting
  Module 8  → Gravity, coyote time, jump buffering, variable jump
  Module 9  → Sentinel FSM (patrol→alert→chase→attack+stun),
               Archer (LOS + arrows), Captain boss (2 phases + axes)

 Controls:
   A / D     move left / right
   S         crouch  (quieter, smaller hitbox, guards less aware)
   SPACE     jump
   J         attack  (stuns guards / damages Captain)
   P         pause
   ESC       back to menu
████████████████████████████████████████████████████████████
"""

import pygame, sys, math, random, struct

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
JUMP_VY      = -460.0
COYOTE_F     = 8
JUMP_BUF_F   = 10
P_SPEED      = 200.0
P_CROUCH_SPD = 90.0
P_ACCEL      = 1700.0

# ── Colors (dungeon stone palette) ────────────────────────
BLACK    = (0,    0,   0)
WHITE    = (255, 255, 255)
DARK_BG  = (5,    5,  10)

STONE    = (38,  33,  28)
STONE_LT = (58,  53,  48)
STONE_HI = (80,  72,  64)
STONE_GL = (25,  22,  18)

TORCH_OR = (255, 160,  30)
TORCH_YE = (255, 220,  80)

SKIN     = (200, 170, 130)
LEATHER  = (90,   65,  40)
SWORD_C  = (185, 185, 205)

GOLD     = (255, 215,   0)
GOLD_DK  = (180, 140,   0)
RED_POT  = (200,  40,  40)
GREEN_DR = (30,  200,  80)

ARMOR_G  = (100, 110, 130)   # Sentinel gray armor
ARMOR_R  = (170,  35,  35)   # Captain red armor
LEATHER2 = (130,  95,  60)   # Archer leather

GRAY     = (55,   55,  70)
GRAY_LT  = (120, 120, 145)
ALERT_Y  = (255, 220,  40)
DANGER_R = (220,  50,  50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("★  SHADOW VAULT")
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
    c = [max(-1.0, min(1.0, s)) for s in samples]
    return struct.pack(f"{len(c)}h", *[int(s * 32767) for s in c])

def _make(samples): return pygame.mixer.Sound(buffer=_pack(samples))
def _sine(f, dur, vol=0.4):
    n = int(SR * dur)
    return [vol * math.sin(2*math.pi*f*i/SR) for i in range(n)]
def _sweep(f0, f1, dur, vol=0.38):
    n = int(SR * dur)
    return [vol*(1-i/n)*math.sin(2*math.pi*(f0+(f1-f0)*(i/n))*i/SR) for i in range(n)]
def _noise(dur, vol=0.35):
    n = int(SR * dur)
    return [vol*(random.random()*2-1)*(1-i/n)**2 for i in range(n)]
def _chord(freqs, dur, vol=0.18):
    n   = int(SR * dur)
    out = [0.0] * n
    for f in freqs:
        for i in range(n):
            out[i] += vol*(1-i/n)*math.sin(2*math.pi*f*i/SR)
    return out
def _mix(a, b):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0) for i in range(n)]

def build_audio():
    sfx = {}
    sfx["jump"]    = _make(_sweep(180, 380, 0.16, 0.28))
    sfx["attack"]  = _make(_mix(_sine(320, 0.06, 0.38), _sine(480, 0.05, 0.28)))
    sfx["key"]     = _make(_chord([523, 659, 784, 1047], 0.35, 0.20))
    sfx["alert"]   = _make(_sweep(220, 880, 0.45, 0.38))
    sfx["hurt"]    = _make(_noise(0.16, 0.50))
    sfx["stun"]    = _make(_sweep(800, 200, 0.25, 0.32))
    sfx["boss_hit"]= _make(_mix(_sine(90, 0.12, 0.40), _noise(0.10, 0.22)))
    sfx["exit_open"]=_make(_chord([392, 494, 587, 740, 988], 0.55, 0.22))
    # Ominous dungeon loop  (A-minor descent, 4 seconds)
    dur  = 4.0
    n    = int(SR * dur)
    ms   = [0.0] * n
    mel  = [440, 392, 349, 330, 294, 262, 220, 247]
    spb  = 60 / 72                  # 72 BPM
    for bi, note in enumerate(mel):
        st = int(bi * spb / 2 * SR)
        ln = int(spb / 2 * SR * 0.55)
        for i in range(ln):
            if st+i >= n: break
            env    = (1-i/ln)**1.5
            ms[st+i] += 0.12*env*math.sin(2*math.pi*note*i/SR)
            ms[st+i] += 0.08*env*math.sin(2*math.pi*(note/2)*i/SR)
    for i in range(n):
        t = i / SR
        ms[i] += 0.05*math.sin(2*math.pi*110*t)*(0.7+0.3*math.sin(2*math.pi*0.4*t))
    sfx["music"] = _make(ms)
    return sfx

print("Building audio…")
pygame.mixer.set_num_channels(14)
SFX = build_audio()
MUSIC_CH = pygame.mixer.Channel(13)
MUSIC_CH.play(SFX["music"], loops=-1)
MUSIC_CH.set_volume(0.30)

def play(name, vol=0.70):
    s = SFX.get(name)
    if s: s.set_volume(vol); s.play()


# ══════════════════════════════════════════════════════════
# MODULE 2 — PARTICLES
# ══════════════════════════════════════════════════════════

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.color = color
        self.r     = random.randint(3, 9)
        self.px    = float(x); self.py = float(y)
        ang        = random.uniform(0, math.pi*2)
        spd        = random.uniform(50, 220)
        self.vx    = math.cos(ang)*spd
        self.vy    = math.sin(ang)*spd - random.uniform(10, 60)
        self.life  = random.uniform(150, 255)
        self.fade  = random.uniform(4, 8)
        t = self.r*2+2
        self.image = pygame.Surface((t, t), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(x), int(y)))
        self._draw()

    def _draw(self):
        self.image.fill((0,0,0,0))
        r = self.r; t = r*2+2; a = max(0, int(self.life))
        pygame.draw.circle(self.image, (*self.color, a//3), (r+1,r+1), r)
        if r > 3:
            pygame.draw.circle(self.image, (*self.color, a), (r+1,r+1), r-2)

    def update(self, dt):
        self.vy   += 350*dt
        self.px   += self.vx*dt; self.py += self.vy*dt
        self.life -= self.fade
        if self.life <= 0: self.kill(); return
        self._draw()
        self.rect.centerx = int(self.px); self.rect.centery = int(self.py)

particles = pygame.sprite.Group()

def explode(x, y, color, n=24, camera=None):
    for _ in range(n):
        sx, sy = camera.world_to_screen(x, y) if camera else (x, y)
        particles.add(Particle(sx, sy, color))

def spark(x, y, camera=None):
    for _ in range(6):
        sx, sy = camera.world_to_screen(x, y) if camera else (x, y)
        particles.add(Particle(sx, sy, ALERT_Y))


# ══════════════════════════════════════════════════════════
# MODULE 7 — TILEMAP, CAMERA & TORCH LIGHTING
# ══════════════════════════════════════════════════════════

_ = 0;  P = 1;  G = 2   # air / platform / ground-stone

LEVEL = [
# col  0         1         2         3         4
#      0123456789012345678901234567890123456789012345678 9
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],  # 0 ceiling
    [G,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G,_,_,_,_,_,G],  # 1
    [G,_,_,P,P,P,_,_,_,_,P,P,P,_,_,_,_,P,P,P,_,_,_,_,P,P,_,_,_,P,P,P,_,_,_,P,P,_,_,_,_,_,_,G,_,_,_,_,_,G],  # 2
    [G,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G,_,_,_,_,_,G],  # 3
    [G,P,P,_,_,_,P,P,P,_,_,_,_,_,P,P,_,_,_,_,_,P,P,P,_,_,_,_,P,P,_,_,_,P,P,P,_,_,_,P,P,_,_,G,_,_,_,_,_,G],  # 4
    [G,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G,_,_,_,_,_,G],  # 5
    [G,_,_,P,P,_,_,_,P,P,P,_,_,P,P,_,_,_,_,P,P,P,_,_,_,P,P,_,_,_,_,P,P,P,_,_,_,P,P,_,_,_,_,G,_,_,_,_,_,G],  # 6
    [G,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G,_,_,_,_,_,G],  # 7
    [G,P,P,_,_,P,P,P,_,_,_,P,P,_,_,_,P,P,P,_,_,_,_,P,P,_,_,_,P,P,P,_,_,_,P,P,_,_,_,_,P,P,_,G,_,_,_,_,_,G],  # 8
    [G,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G],  # 9
    [G,_,P,P,P,_,_,_,_,P,P,_,_,_,P,P,P,_,_,_,P,P,_,_,_,_,P,P,P,_,_,_,P,P,_,_,_,P,P,P,_,_,_,_,_,_,P,P,_,G],  # 10
    [G,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,G],  # 11
    [G,G,G,G,G,_,_,G,G,G,G,G,_,_,_,G,G,G,G,_,_,_,G,G,G,G,G,_,_,G,G,G,G,_,_,_,G,G,G,G,_,_,_,G,G,G,G,G,G,G],  # 12 ground w/gaps
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],  # 13
    [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],  # 14
]
LW = len(LEVEL[0]); LH = len(LEVEL)
WORLD_W = LW * TS;  WORLD_H = LH * TS

# Torch world-positions  (center of torch flame)
TORCHES = [
    (3*TS+20, 12*TS-4), (8*TS,    2*TS-4),  (15*TS,   8*TS-4),
    (22*TS,   4*TS-4),  (30*TS,   2*TS-4),  (36*TS,   8*TS-4),
    (43*TS+20, 11*TS-4),(46*TS+20, 2*TS-4),
]

# Key, potion and exit world positions
KEY_POSITIONS = [(8*TS+10, 7*TS), (22*TS+10, 3*TS), (37*TS+10, 5*TS)]
POTION_POS    = (17*TS, 7*TS)
EXIT_POS      = (46*TS+10, 11*TS)


def solid_rects_near(wx, wy):
    c = int(wx // TS); r = int(wy // TS)
    rects = []
    for dr in range(-2, 4):
        for dc in range(-2, 4):
            rc = c+dc; rr = r+dr
            if 0 <= rr < LH and 0 <= rc < LW and LEVEL[rr][rc] != 0:
                rects.append(pygame.Rect(rc*TS, rr*TS, TS, TS))
    return rects


def line_of_sight(ax, ay, bx, by):
    """Ray–AABB test: True if no solid tile blocks the line."""
    dx = bx - ax; dy = by - ay
    if abs(dx) < 0.01 and abs(dy) < 0.01:
        return True
    steps = max(int(math.hypot(dx, dy) / (TS//2)), 1)
    for s in range(1, steps):
        tx = ax + dx * s / steps
        ty = ay + dy * s / steps
        c  = int(tx // TS); r = int(ty // TS)
        if 0 <= r < LH and 0 <= c < LW and LEVEL[r][c] != 0:
            return False
    return True


class Camera:
    def __init__(self):
        self.x = 0.0; self.y = 0.0
        self.smooth = 7.0
        self.dead   = pygame.Rect(WIDTH//2-110, HEIGHT//2-90, 220, 180)
        self._shake = 0.0; self._sstr = 0.0; self._off = (0, 0)

    def world_to_screen(self, wx, wy):
        return (int(wx - self.x + self._off[0]),
                int(wy - self.y + self._off[1]))

    def follow(self, wx, wy, dt):
        tsx = wx - self.x; tsy = wy - self.y
        if tsx < self.dead.left:    self.x += (wx - self.dead.left   - self.x) * self.smooth * dt
        elif tsx > self.dead.right: self.x += (wx - self.dead.right  - self.x) * self.smooth * dt
        if tsy < self.dead.top:     self.y += (wy - self.dead.top    - self.y) * self.smooth * dt
        elif tsy > self.dead.bottom:self.y += (wy - self.dead.bottom - self.y) * self.smooth * dt
        self.x = max(0, min(self.x, WORLD_W - WIDTH))
        self.y = max(0, min(self.y, WORLD_H - HEIGHT))
        if self._shake > 0:
            self._shake -= dt; p = self._shake / 0.3
            self._off = (random.uniform(-1,1)*self._sstr*p,
                         random.uniform(-1,1)*self._sstr*p)
        else: self._off = (0, 0)

    def shake(self, s=6.0): self._shake = 0.3; self._sstr = s


def draw_tilemap(surf, camera):
    cx, cy = camera.x, camera.y
    cs = max(0, int(cx//TS)); ce = min(LW, int((cx+WIDTH)//TS)+1)
    rs = max(0, int(cy//TS)); re = min(LH, int((cy+HEIGHT)//TS)+1)
    for r in range(rs, re):
        for c in range(cs, ce):
            t = LEVEL[r][c]
            if t == 0: continue
            sx, sy = camera.world_to_screen(c*TS, r*TS)
            pygame.draw.rect(surf, STONE,    (sx, sy, TS, TS))
            pygame.draw.rect(surf, STONE_GL, (sx, sy, TS, TS), 1)
            pygame.draw.line(surf, STONE_HI,
                             (sx+1, sy+1), (sx+TS-2, sy+1), 1)
            if t == P:
                pygame.draw.line(surf, STONE_LT,
                                 (sx, sy), (sx+TS, sy), 2)


def draw_torches(surf, camera, t_global):
    for wx, wy in TORCHES:
        sx, sy = camera.world_to_screen(wx, wy)
        if -20 < sx < WIDTH+20 and -20 < sy < HEIGHT+20:
            bob = int(3 * math.sin(t_global * 6 + wx))
            pygame.draw.polygon(surf, STONE_LT,
                [(sx-4, sy+8), (sx+4, sy+8), (sx+2, sy+14), (sx-2, sy+14)])
            pygame.draw.circle(surf, TORCH_OR, (sx, sy+bob), 7)
            pygame.draw.circle(surf, TORCH_YE, (sx, sy+bob-3), 4)


def apply_lighting(surf, camera, t_global):
    """Atmospheric darkness with warm torch cutouts."""
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 8, 215))
    for wx, wy in TORCHES:
        sx, sy = camera.world_to_screen(wx, wy)
        flicker = int(10 * math.sin(t_global * 7 + wx * 0.3))
        for radius, alpha in [(190+flicker, 215), (140, 185),
                               (95,  145), (60, 95), (35, 50)]:
            circ = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circ, (0, 0, 0, alpha), (radius, radius), radius)
            dark.blit(circ, (sx-radius, sy-radius),
                      special_flags=pygame.BLEND_RGBA_SUB)
    surf.blit(dark, (0, 0))


def draw_background(surf, camera):
    surf.fill(DARK_BG)
    # Subtle far-background stone texture lines
    for y in range(0, HEIGHT, 80):
        pygame.draw.line(surf, (12, 10, 9), (0, y), (WIDTH, y), 1)
    for x in range(0, WIDTH, 80):
        pygame.draw.line(surf, (12, 10, 9), (x, 0), (x, HEIGHT), 1)


# ══════════════════════════════════════════════════════════
# COLLECTIBLES
# ══════════════════════════════════════════════════════════

class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.wx = float(x); self.wy = float(y)
        self.t  = random.uniform(0, math.pi*2)
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(x), int(y)))
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        pygame.draw.circle(s, GOLD,    (8, 8), 7)
        pygame.draw.circle(s, GOLD_DK, (8, 8), 7, 2)
        pygame.draw.circle(s, BLACK,   (8, 8), 4)
        pygame.draw.rect(s,  GOLD,    (14, 6, 8, 4))
        pygame.draw.rect(s,  GOLD,    (18, 10, 4, 4))
        pygame.draw.rect(s,  GOLD,    (14, 14, 6, 4))

    def update(self, dt):
        self.t += dt * 2.5
        self.wy_draw = self.wy + math.sin(self.t) * 5

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.wx, self.wy_draw)
        # Glow
        for r, a in [(18, 30), (12, 60), (8, 100)]:
            g = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(g, (*GOLD, a), (r, r), r)
            surf.blit(g, (sx - r + 4, sy - r + 4))
        surf.blit(self.image, (sx - 12, sy - 12))


class HealthPotion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.wx = float(x); self.wy = float(y)
        self.t  = 0.0
        self.image = pygame.Surface((20, 24), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(x), int(y)))
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        pygame.draw.rect(s, (80, 40, 30), (6, 0, 8, 5))
        pygame.draw.ellipse(s, RED_POT,   (2, 5, 16, 18))
        pygame.draw.ellipse(s, (240, 80, 80), (4, 7, 12, 14))
        pygame.draw.line(s, WHITE, (8, 12), (12, 12), 2)
        pygame.draw.line(s, WHITE, (10, 10), (10, 14), 2)

    def update(self, dt):
        self.t += dt * 2
        self.wy_draw = self.wy + math.sin(self.t) * 4

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.wx, self.wy_draw)
        surf.blit(self.image, (sx - 10, sy - 12))


class ExitDoor(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.wx    = float(x); self.wy = float(y)
        self.open  = False
        self.t     = 0.0
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(bottomleft=(int(x), int(y)+60))

    def update(self, dt, keys_collected, keys_total):
        self.open = (keys_collected >= keys_total)
        self.t   += dt

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        frame_col = GREEN_DR if self.open else (80, 60, 40)
        wood_col  = (55, 38, 22) if not self.open else (40, 90, 50)
        # Frame
        pygame.draw.rect(s, frame_col, (0, 0, 40, 60), 3)
        # Door panels
        pygame.draw.rect(s, wood_col, (3, 3, 34, 54))
        pygame.draw.line(s, frame_col, (3, 30), (37, 30), 1)
        pygame.draw.line(s, frame_col, (20, 3), (20, 57), 1)
        # Knob
        pygame.draw.circle(s, GOLD if self.open else STONE_LT, (28, 32), 4)
        if self.open:
            pulse = abs(math.sin(self.t * 4))
            for r in [18, 24]:
                g = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(g, (0, 255, 100, int(50*pulse)), (r,r), r)
                self.image.blit(g, (20-r, 30-r))

    def draw(self, surf, camera):
        self._draw()
        sx, sy = camera.world_to_screen(self.wx, self.wy)
        surf.blit(self.image, (sx, sy))
        status = "EXIT  [OPEN]" if self.open else "EXIT  [LOCKED]"
        col    = GREEN_DR if self.open else GRAY_LT
        blit(surf, status, (sx - 10, sy - 18), col, F_SM)

    @property
    def world_rect(self):
        return pygame.Rect(int(self.wx), int(self.wy), 40, 60)


# ══════════════════════════════════════════════════════════
# PROJECTILES
# ══════════════════════════════════════════════════════════

class Arrow(pygame.sprite.Sprite):
    def __init__(self, x, y, vx):
        super().__init__()
        self.px = float(x); self.py = float(y)
        self.vx = vx; self.vy = 0.0
        self.life = 3.0
        self.image = pygame.Surface((20, 6), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (140,100,60),
                            [(0,3),(16,0),(20,3),(16,6)])
        pygame.draw.rect(self.image, (180,160,120), (0,2,14,2))
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self, dt):
        self.vy += 120*dt
        self.px += self.vx*dt; self.py += self.vy*dt
        self.life -= dt
        self.rect.center = (int(self.px), int(self.py))
        for r in solid_rects_near(self.px, self.py):
            if self.rect.colliderect(r): self.kill(); return
        if self.life <= 0: self.kill()

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.px, self.py)
        angle  = math.degrees(math.atan2(self.vy, self.vx))
        rot    = pygame.transform.rotate(self.image, -angle)
        surf.blit(rot, rot.get_rect(center=(sx, sy)))


class Axe(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy):
        super().__init__()
        self.px = float(x); self.py = float(y)
        self.vx = vx; self.vy = vy
        self.life = 3.5; self.spin = 0.0
        self.image = pygame.Surface((22, 22), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(x), int(y)))

    def _draw_axe(self):
        s = self.image; s.fill((0,0,0,0))
        pygame.draw.circle(s, ARMOR_G,    (11, 11), 9)
        pygame.draw.circle(s, STONE_HI,   (11, 11), 9, 2)
        pygame.draw.polygon(s, (160,140,120),
                            [(11, 2),(19, 8),(15, 16),(7, 16),(3, 8)])

    def update(self, dt):
        self.vy  += 200*dt
        self.px  += self.vx*dt; self.py += self.vy*dt
        self.spin+= 6*dt
        self.life -= dt
        self._draw_axe()
        self.rect.center = (int(self.px), int(self.py))
        for r in solid_rects_near(self.px, self.py):
            if self.rect.colliderect(r): self.kill(); return
        if self.life <= 0: self.kill()

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.px, self.py)
        rot    = pygame.transform.rotate(self.image,
                                         math.degrees(self.spin))
        surf.blit(rot, rot.get_rect(center=(sx, sy)))


# ══════════════════════════════════════════════════════════
# MODULE 8 + 4 — PLAYER
# ══════════════════════════════════════════════════════════

class Player(pygame.sprite.Sprite):
    W = 26; H = 36; MAX_HP = 5

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((self.W, self.H+4), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()
        self.reset()

    def reset(self):
        self.x = 2.5*TS; self.y = 10*TS
        self.vx = 0.0;    self.vy = 0.0
        self.on_ground  = False
        self.facing     = 1
        self.crouching  = False
        self.coyote     = 0
        self.jump_buf   = 0
        self.jumping    = False
        self.jump_frames= 0
        self.hp         = self.MAX_HP
        self.invincible = 0.0
        self.hurt_flash = 0.0
        self.attack_timer = 0.0
        self.attack_box   = None
        self.state      = "IDLE"
        self.anim_t     = 0.0
        self.alive      = True
        self.rect.topleft = (int(self.x), int(self.y))

    @property
    def hitbox_h(self): return 20 if self.crouching else self.H

    @property
    def center(self): return (self.x + self.W//2, self.y + self.hitbox_h//2)

    def take_damage(self, camera=None):
        if self.invincible > 0 or not self.alive: return
        self.hp -= 1; self.invincible = 1.4; self.hurt_flash = 0.3
        self.state = "HURT"; play("hurt")
        if camera: camera.shake(7)
        if self.hp <= 0:
            self.state = "DIE"; self.alive = False; play("hurt", 0.8)

    def update(self, dt, keys_held, jump_pressed, attack_pressed, crouch_held, camera=None):
        if not self.alive:
            self.anim_t += dt; self._draw(); return

        self.anim_t      += dt
        self.invincible   = max(0, self.invincible - dt)
        self.hurt_flash   = max(0, self.hurt_flash - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        if self.attack_timer <= 0: self.attack_box = None

        self.crouching = crouch_held and self.on_ground

        # ── Attack ───────────────────────────────────────
        if attack_pressed and self.attack_timer <= 0 and not self.crouching:
            self.attack_timer = 0.22
            ax = self.x + (self.W if self.facing > 0 else -38)
            self.attack_box = pygame.Rect(int(ax), int(self.y+6), 38, 24)
            self.state = "ATTACK"; play("attack", 0.55)

        # ── Horizontal ───────────────────────────────────
        spd    = P_CROUCH_SPD if self.crouching else P_SPEED
        target = 0.0
        if keys_held[pygame.K_a]: target = -spd; self.facing = -1
        if keys_held[pygame.K_d]: target =  spd; self.facing =  1
        step   = P_ACCEL * dt
        if target != 0:
            self.vx += math.copysign(min(abs(target-self.vx), step), target-self.vx)
        else:
            dec = min(abs(self.vx), step*0.8)
            self.vx -= math.copysign(dec, self.vx) if self.vx else 0

        # ── Coyote & buffer ──────────────────────────────
        self.coyote   = COYOTE_F if self.on_ground else max(0, self.coyote-1)
        self.jump_buf = max(0, self.jump_buf-1)
        if jump_pressed: self.jump_buf = JUMP_BUF_F

        if self.jump_buf > 0 and (self.on_ground or self.coyote > 0) and not self.crouching:
            self.vy = JUMP_VY; self.jumping = True; self.jump_frames = 0
            self.jump_buf = 0; self.coyote = 0; self.on_ground = False
            play("jump", 0.50)

        if self.jumping:
            self.jump_frames += 1
            if (not keys_held[pygame.K_SPACE] and self.jump_frames > 6) or self.jump_frames > 20:
                self.jumping = False
        grav_mult = 0.38 if self.jumping else 1.0
        self.vy = min(self.vy + GRAVITY*grav_mult*dt, TERM_VEL)

        # ── Move X ───────────────────────────────────────
        self.x += self.vx * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.hitbox_h)
            if pr.colliderect(r):
                self.x = r.right if self.vx < 0 else r.left - self.W; self.vx = 0

        # ── Move Y ───────────────────────────────────────
        self.on_ground = False
        self.y += self.vy * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.hitbox_h)
            if pr.colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.hitbox_h; self.vy = 0
                    self.on_ground = True; self.jumping = False
                elif self.vy < 0:
                    self.y = r.bottom; self.vy = 0

        self.x = max(0, min(self.x, WORLD_W - self.W))
        if self.y > WORLD_H + 80: self.take_damage(camera); self.x=2.5*TS; self.y=10*TS; self.vy=0

        # ── State ────────────────────────────────────────
        if   self.hurt_flash > 0:              self.state = "HURT"
        elif self.attack_timer > 0:            self.state = "ATTACK"
        elif self.crouching:                   self.state = "CROUCH"
        elif not self.on_ground and self.vy<0: self.state = "JUMP"
        elif not self.on_ground:               self.state = "FALL"
        elif abs(self.vx) > 10:               self.state = "WALK"
        else:                                  self.state = "IDLE"

        self.rect.topleft = (int(self.x), int(self.y))
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        t  = self.anim_t; st = self.state
        h  = 20 if st == "CROUCH" else self.H
        w  = self.W
        body = WHITE if self.hurt_flash > 0 else LEATHER
        bob  = int(2*math.sin(t*3)) if st == "IDLE" else 0
        # Body
        pygame.draw.rect(s, body, (2, 4+bob+(self.H-h), w-4, h-8), border_radius=4)
        pygame.draw.rect(s, STONE_LT, (2, 4+bob+(self.H-h), w-4, h-8), 1, border_radius=4)
        # Head
        hy = 1+bob if st != "CROUCH" else 10
        pygame.draw.ellipse(s, SKIN, (4, hy, w-8, 14))
        # Eyes
        ex = w-12 if self.facing > 0 else 8
        if self.alive:
            pygame.draw.circle(s, BLACK, (ex, hy+6), 3)
            pygame.draw.circle(s, WHITE, (ex-self.facing, hy+5), 1)
        else:
            pygame.draw.line(s, DANGER_R,(ex-3,hy+4),(ex+3,hy+8),1)
            pygame.draw.line(s, DANGER_R,(ex+3,hy+4),(ex-3,hy+8),1)
        # Sword in hand
        if st == "ATTACK":
            sx2 = w if self.facing > 0 else -14
            pygame.draw.rect(s, SWORD_C, (sx2, hy+6, 14, 3))
            pygame.draw.rect(s, GOLD,    (sx2+10, hy+4, 3, 7))
        # Legs (walk anim)
        if st == "WALK":
            for i, side in [(0, -1), (1, 1)]:
                ang = math.sin(t*9 + i*math.pi)*0.5
                lx  = w//2 + side*5
                ly  = self.H - 6 + bob
                ex2 = lx + int(math.sin(ang)*7)
                ey2 = ly + int(math.cos(abs(ang))*7)
                pygame.draw.line(s, LEATHER, (lx, ly), (ex2, ey2), 3)

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        if self.attack_box:
            asx, asy = camera.world_to_screen(self.attack_box.x, self.attack_box.y)
            ds = pygame.Surface((self.attack_box.w, self.attack_box.h), pygame.SRCALPHA)
            ds.fill((*SWORD_C, 50)); surf.blit(ds, (asx, asy))
        if self.invincible > 0 and int(self.invincible*10)%2==0:
            ds2 = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ds2.fill((255,255,255,70)); surf.blit(ds2, (sx, sy))


# ══════════════════════════════════════════════════════════
# MODULE 9 — ENEMIES
# ══════════════════════════════════════════════════════════

class Sentinel(pygame.sprite.Sprite):
    """FSM: PATROL → ALERT → CHASE → ATTACK.  Can be stunned."""
    W = 30; H = 38; MAX_HP = 3; RADIUS = 16

    def __init__(self, x, y, patrol_min, patrol_max):
        super().__init__()
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.hp         = self.MAX_HP
        self.state      = "PATROL"
        self.state_t    = 0.0
        self.facing     = 1
        self.patrol_dir = 1
        self.patrol_min = patrol_min; self.patrol_max = patrol_max
        self.stun_t     = 0.0
        self.detect_r   = 180
        self.anim_t     = 0.0
        self.alive      = True
        self.alerted    = False
        self.image      = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect       = self.image.get_rect(topleft=(int(x), int(y)))

    @property
    def center(self): return (self.x + self.W//2, self.y + self.H//2)

    def take_damage(self, camera=None):
        if self.stun_t > 0: return False
        self.hp -= 1; play("stun", 0.5)
        self.stun_t = 1.8
        explode(*self.center, ARMOR_G, 14, camera)
        return self.hp <= 0

    def _go(self, s): self.state = s; self.state_t = 0.0

    def update(self, dt, px, py, crouching=False, camera=None):
        if not self.alive: return
        self.anim_t += dt; self.state_t += dt
        self.stun_t  = max(0, self.stun_t - dt)

        if self.stun_t > 0:
            self.vx *= 0.7; self._physics(dt); self._draw(); return

        cx, cy   = self.center
        dist     = math.hypot(px-cx, py-cy)
        # Crouching reduces effective detection by 45%
        eff_r    = self.detect_r * (0.55 if crouching else 1.0)
        has_los  = line_of_sight(cx, cy, px, py)
        spotted  = (dist < eff_r and has_los)

        if self.state == "PATROL":
            if spotted: self._go("ALERT"); play("alert", 0.40)
            else:
                self.vx = self.patrol_dir * 55
                if self.x <= self.patrol_min: self.patrol_dir = 1
                if self.x >= self.patrol_max: self.patrol_dir = -1
                self.facing = self.patrol_dir

        elif self.state == "ALERT":
            self.vx *= 0.8
            if self.state_t > 0.9:
                self._go("CHASE" if spotted else "PATROL")

        elif self.state == "CHASE":
            if dist < 38: self._go("ATTACK")
            elif not spotted and self.state_t > 2.5: self._go("PATROL")
            else:
                self.vx = math.copysign(115, px - cx); self.facing = int(math.copysign(1, self.vx))

        elif self.state == "ATTACK":
            self.vx *= 0.7
            if dist > 55: self._go("CHASE")

        self._physics(dt); self._draw()

    def _physics(self, dt):
        self.vy = min(self.vy + GRAVITY*dt, TERM_VEL)
        self.x += self.vx * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                self.patrol_dir *= -1; self.vx = 0; break
        self.on_ground = False
        self.y += self.vy * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                if self.vy > 0: self.y = r.top-self.H; self.vy = 0; self.on_ground = True
                elif self.vy < 0: self.y = r.bottom; self.vy = 0
        self.x = max(0, min(self.x, WORLD_W-self.W))
        self.rect.topleft = (int(self.x), int(self.y))

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        stunned = self.stun_t > 0
        col     = STONE_HI if stunned else ARMOR_G
        bob     = int(2*math.sin(self.anim_t*8)) if self.state=="CHASE" else 0
        pygame.draw.rect(s, col, (2, 4+bob, self.W-4, self.H-8), border_radius=4)
        pygame.draw.rect(s, STONE_LT, (2, 4+bob, self.W-4, self.H-8), 1, border_radius=4)
        # Helmet
        pygame.draw.ellipse(s, STONE_LT, (4, bob, self.W-8, 14))
        # Eye slit
        eye_x = self.W-10 if self.facing > 0 else 6
        eye_c  = DANGER_R if (self.state in ("CHASE","ATTACK") and not stunned) else BLACK
        pygame.draw.rect(s, eye_c, (eye_x-3, 6+bob, 8, 3))
        # HP
        for i in range(self.hp):
            pygame.draw.rect(s, DANGER_R, (2+i*9, 0, 7, 3))
        if stunned:
            blit(s, "zzz", (4, self.H-14), ALERT_Y, F_SM)

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        col = {"PATROL": GRAY_LT, "ALERT": ALERT_Y,
               "CHASE": NO_STUB, "ATTACK": DANGER_R}.get(self.state, GRAY_LT)
        blit(surf, self.state, (sx, sy-14), col, F_SM)

NO_STUB = (255, 140, 30)   # orange for CHASE


class Archer(pygame.sprite.Sprite):
    """Stationary guard with LOS check; fires arrows."""
    W = 26; H = 34; MAX_HP = 2; RADIUS = 14

    def __init__(self, x, y):
        super().__init__()
        self.x = float(x); self.y = float(y)
        self.vy = 0.0; self.vx = 0.0
        self.hp       = self.MAX_HP
        self.alive    = True
        self.shoot_cd = random.uniform(2.0, 4.0)
        self.facing   = -1
        self.stun_t   = 0.0
        self.anim_t   = 0.0
        self.arrows   = pygame.sprite.Group()
        self.image    = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect     = self.image.get_rect(topleft=(int(x), int(y)))

    @property
    def center(self): return (self.x + self.W//2, self.y + self.H//2)

    def take_damage(self, camera=None):
        if self.stun_t > 0: return False
        self.hp -= 1; self.stun_t = 1.5; play("stun", 0.5)
        explode(*self.center, LEATHER2, 12, camera)
        return self.hp <= 0

    def update(self, dt, px, py, crouching=False, camera=None):
        if not self.alive: return
        self.anim_t  += dt
        self.stun_t   = max(0, self.stun_t - dt)
        self.shoot_cd = max(0, self.shoot_cd - dt)

        # Stay on ground
        self.vy = min(self.vy + GRAVITY*dt, TERM_VEL)
        self.y += self.vy * dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                if self.vy > 0: self.y = r.top-self.H; self.vy = 0
                elif self.vy < 0: self.y = r.bottom; self.vy = 0
        self.rect.topleft = (int(self.x), int(self.y))

        cx, cy = self.center
        dist   = math.hypot(px-cx, py-cy)
        self.facing = 1 if px > cx else -1
        eff_r = 280 * (0.5 if crouching else 1.0)

        if (not self.stun_t > 0 and dist < eff_r
                and line_of_sight(cx, cy, px, py)
                and self.shoot_cd <= 0):
            speed = 260.0
            self.arrows.add(Arrow(cx, cy, self.facing * speed))
            self.shoot_cd = 2.8; play("attack", 0.35)

        self.arrows.update(dt)
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        bob  = int(2*math.sin(self.anim_t*2))
        col  = STONE_HI if self.stun_t > 0 else LEATHER2
        pygame.draw.rect(s, col, (2, 4+bob, self.W-4, self.H-8), border_radius=3)
        pygame.draw.rect(s, STONE_LT, (2, 4+bob, self.W-4, self.H-8), 1, border_radius=3)
        pygame.draw.ellipse(s, SKIN, (4, bob, self.W-8, 12))
        ex = self.W-8 if self.facing > 0 else 4
        pygame.draw.circle(s, BLACK, (ex, 6+bob), 2)
        # Bow
        bx = 0 if self.facing > 0 else self.W
        pygame.draw.arc(s, (120,90,55),
                        pygame.Rect(bx-8, 10+bob, 16, 16),
                        math.pi*0.25, math.pi*1.75, 3)
        for i in range(self.hp):
            pygame.draw.rect(s, DANGER_R, (2+i*10, 0, 8, 3))

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        for arrow in self.arrows:
            arrow.draw(surf, camera)


class Captain(pygame.sprite.Sprite):
    """Boss guard: 2 phases, throws axes."""
    W = 50; H = 58; MAX_HP = 180; RADIUS = 28

    def __init__(self, x, y):
        super().__init__()
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.hp       = self.MAX_HP
        self.alive    = True
        self.phase    = 1
        self.dir      = -1
        self.throw_cd = 2.5
        self.anim_t   = 0.0
        self.hurt_t   = 0.0
        self.axes     = pygame.sprite.Group()
        self.image    = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.rect     = self.image.get_rect(topleft=(int(x), int(y)))

    def take_damage(self):
        self.hp -= 25; self.hurt_t = 0.2; play("boss_hit", 0.55)
        if self.phase == 1 and self.hp <= self.MAX_HP//2:
            self.phase = 2; play("alert", 0.7)
        return self.hp <= 0

    def update(self, dt, px, py, camera=None):
        if not self.alive: return
        self.anim_t  += dt
        self.hurt_t   = max(0, self.hurt_t - dt)
        self.throw_cd = max(0, self.throw_cd - dt)

        spd = 70 if self.phase == 1 else 115
        self.vx = self.dir * spd
        self.dir = 1 if self.x < 43*TS+4 else (-1 if self.x > 48*TS-self.W else self.dir)

        self.vy = min(self.vy + GRAVITY*dt, TERM_VEL)
        self.x += self.vx*dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r): self.vx = 0; break
        self.y += self.vy*dt
        for r in solid_rects_near(self.x, self.y):
            pr = pygame.Rect(int(self.x), int(self.y), self.W, self.H)
            if pr.colliderect(r):
                if self.vy > 0: self.y = r.top-self.H; self.vy = 0
                elif self.vy < 0: self.y = r.bottom; self.vy = 0
        self.rect.topleft = (int(self.x), int(self.y))

        interval = 2.0 if self.phase == 1 else 1.1
        if self.throw_cd <= 0:
            self.throw_cd = interval
            cx = self.x+self.W//2; cy = self.y+self.H//3
            throws = 2 if self.phase == 1 else 4
            for i in range(throws):
                ang = math.atan2(py-cy, px-cx) + (i-(throws//2))*0.3
                spd2= 220.0
                self.axes.add(Axe(cx, cy, math.cos(ang)*spd2, math.sin(ang)*spd2))

        self.axes.update(dt)
        self._draw()

    def _draw(self):
        s = self.image; s.fill((0,0,0,0))
        t   = self.anim_t
        col = WHITE if self.hurt_t > 0 else (ARMOR_R if self.phase==1 else (200, 20, 20))
        bob = int(3*math.sin(t*2.5))
        pygame.draw.rect(s, col, (4, 6+bob, self.W-8, self.H-12), border_radius=6)
        pygame.draw.rect(s, STONE_HI, (4, 6+bob, self.W-8, self.H-12), 2, border_radius=6)
        # Helmet
        pygame.draw.rect(s, STONE_LT, (4, 1+bob, self.W-8, 16), border_radius=4)
        pygame.draw.rect(s, ARMOR_R,  (4, 1+bob, self.W-8, 16), 1, border_radius=4)
        # Eye slits
        for ex in [12, self.W-18]:
            pygame.draw.rect(s, DANGER_R, (ex, 8+bob, 10, 4))
        # HP bar
        hpw = int((self.W-8)*max(0, self.hp/self.MAX_HP))
        pygame.draw.rect(s, GRAY,    (4, 0, self.W-8, 5))
        c2  = (50,200,100) if self.hp > self.MAX_HP//2 else DANGER_R
        pygame.draw.rect(s, c2, (4, 0, hpw, 5))
        if self.phase == 2:
            pygame.draw.rect(s, (255,80,80), (4, 0, self.W-8, 5), 1)

    def draw(self, surf, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        surf.blit(self.image, (sx, sy))
        col = ARMOR_R if self.phase==1 else DANGER_R
        blit(surf, f"CAPTAIN  Phase {self.phase}", (sx, sy-16), col, F_SM)
        for axe in self.axes: axe.draw(surf, camera)

    @property
    def body_rect(self): return pygame.Rect(int(self.x), int(self.y), self.W, self.H)


# ══════════════════════════════════════════════════════════
# MODULE 5 — SCENE MANAGER
# ══════════════════════════════════════════════════════════

class Scene:
    def __init__(self, mgr): self.mgr = mgr
    def enter(self): pass
    def exit(self):  pass
    def handle_event(self, ev): pass
    def update(self, dt): pass
    def draw(self, surf): pass

class SceneManager:
    def __init__(self):
        self._stack = []; self.running = True; self.shared = {}

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
                if ev.type == pygame.QUIT: self.running = False
                self.current.handle_event(ev)
            self.current.update(dt)
            self.current.draw(screen)
            pygame.display.flip()
        pygame.quit(); sys.exit()


# ══════════════════════════════════════════════════════════
# SCENE: MENU
# ══════════════════════════════════════════════════════════

class MenuScene(Scene):
    def __init__(self, mgr): super().__init__(mgr); self.t = 0.0

    def enter(self):
        MUSIC_CH.set_volume(0.30)
        pygame.display.set_caption("★  SHADOW VAULT")

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN: self.mgr.replace(GameScene(self.mgr))
            if ev.key == pygame.K_ESCAPE: self.mgr.running = False

    def update(self, dt): self.t += dt

    def draw(self, surf):
        surf.fill(DARK_BG)
        # Stone texture
        for y in range(0, HEIGHT, TS):
            for x in range(0, WIDTH, TS):
                shade = random.randint(30, 42)
                pygame.draw.rect(surf, (shade, shade-5, shade-10),
                                 (x, y, TS, TS))
                pygame.draw.rect(surf, (20,17,14), (x, y, TS, TS), 1)

        # Torch flickers
        for tx, ty in [(150, 200), (750, 200), (150, 450), (750, 450)]:
            flicker = int(8*math.sin(self.t*7 + tx))
            for r, a in [(80+flicker,50),(55,80),(35,110),(18,140)]:
                g = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
                pygame.draw.circle(g, (*TORCH_OR, a), (r,r), r)
                surf.blit(g, (tx-r, ty-r))
            pygame.draw.circle(surf, TORCH_YE, (tx, ty), 10)

        # Title
        pulse = abs(math.sin(self.t*1.5))
        tc    = (int(200+55*pulse), int(160+60*pulse), int(100+30*pulse))
        blit_c(surf, "★  SHADOW VAULT  ★", 130, tc, F_TIT)
        blit_c(surf, "A dungeon platformer", 210, GRAY_LT, F_MD)

        # Story text
        story = [
            "The vault holds untold treasures... and deadly guardians.",
            "Collect all 3 KEYS  •  Reach the EXIT  •  Escape alive.",
        ]
        for i, line in enumerate(story):
            blit_c(surf, line, 270 + i*26, STONE_HI, F_MD)

        # Controls
        blit_c(surf, "Controls", 345, TORCH_OR, F_LG)
        ctrl = [("A/D","Move"), ("S","Crouch (stealth)"),
                ("SPACE","Jump"), ("J","Attack / stun guards"), ("P","Pause")]
        for i, (k, v) in enumerate(ctrl):
            blit_c(surf, f"[{k}]  {v}", 375 + i*26, GRAY_LT, F_MD)

        if int(self.t*2)%2 == 0:
            blit_c(surf, "PRESS  ENTER  TO  ENTER  THE  VAULT", 520, GOLD, F_LG)
        blit_c(surf, "ESC: quit", 554, GRAY, F_SM)

        pygame.draw.rect(surf, STONE_GL, (0, HEIGHT-30, WIDTH, 30))
        blit_c(surf, "Modules 1-9 integrated  •  No external assets  •  Python + Pygame",
               HEIGHT-20, GRAY, F_SM)


# ══════════════════════════════════════════════════════════
# SCENE: GAME
# ══════════════════════════════════════════════════════════

SENTINEL_DEFS = [
    (10*TS, 11*TS,  7*TS, 14*TS),   # early dungeon
    (28*TS, 11*TS, 22*TS, 35*TS),   # mid dungeon
]
ARCHER_DEFS = [
    (19*TS, 5*TS),
    (36*TS, 5*TS),
]
CAPTAIN_POS = (45*TS, 11*TS)

class GameScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr)
        self._jump_p = False; self._attack_p = False

    def enter(self):
        particles.empty()
        pygame.display.set_caption("★  SHADOW VAULT")
        MUSIC_CH.set_volume(0.30)
        self.camera   = Camera()
        self.player   = Player()
        self.sentinels= pygame.sprite.Group()
        self.archers  = pygame.sprite.Group()
        self.captain  = None; self.cap_triggered = False

        for x, y, pmin, pmax in SENTINEL_DEFS:
            self.sentinels.add(Sentinel(x, y, pmin, pmax))
        for x, y in ARCHER_DEFS:
            self.archers.add(Archer(x, y))

        self.keys_group = pygame.sprite.Group()
        for kx, ky in KEY_POSITIONS:
            self.keys_group.add(Key(kx, ky))

        self.potion = HealthPotion(*POTION_POS)
        self.exit_door   = ExitDoor(*EXIT_POS)
        self.total_keys = len(KEY_POSITIONS)
        self.keys_got   = 0
        self.t_global   = 0.0

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE: self.mgr.replace(MenuScene(self.mgr))
            if ev.key == pygame.K_p:      self.mgr.push(PauseScene(self.mgr))
            if ev.key == pygame.K_SPACE:  self._jump_p = True
            if ev.key == pygame.K_j:      self._attack_p = True

    def update(self, dt):
        self.t_global += dt
        keys = pygame.key.get_pressed()
        crouch = keys[pygame.K_s]
        self.player.update(dt, keys, self._jump_p, self._attack_p, crouch, self.camera)
        self._jump_p = False; self._attack_p = False

        px, py = self.player.center

        # Spawn Captain when player reaches boss area
        if px > 42*TS and not self.cap_triggered:
            self.cap_triggered = True
            self.captain = Captain(*CAPTAIN_POS)
            MUSIC_CH.set_volume(0.55)

        # Update enemies
        for s in list(self.sentinels):
            s.update(dt, px, py, crouch, self.camera)
        for a in list(self.archers):
            a.update(dt, px, py, crouch, self.camera)
        if self.captain and self.captain.alive:
            self.captain.update(dt, px, py, self.camera)

        # Update collectibles
        for k in list(self.keys_group): k.update(dt)
        self.potion.update(dt)
        self.exit_door.update(dt, self.keys_got, self.total_keys)
        particles.update(dt)
        self.camera.follow(px, py, dt)

        # ── MODULE 3: Collisions ──────────────────────────

        # Player picks up keys
        pr = pygame.Rect(int(self.player.x), int(self.player.y),
                         self.player.W, self.player.hitbox_h)
        for k in list(self.keys_group):
            kr = pygame.Rect(int(k.wx)-10, int(k.wy)-10, 20, 20)
            if pr.colliderect(kr):
                k.kill(); self.keys_got += 1; play("key", 0.65)
                explode(k.wx, k.wy, GOLD, 18, self.camera)

        # Player picks up potion
        porect = pygame.Rect(int(self.potion.wx)-8, int(self.potion.wy)-10, 16, 24)
        if pr.colliderect(porect) and self.player.alive:
            if self.player.hp < self.player.MAX_HP:
                self.player.hp = min(self.player.MAX_HP, self.player.hp+2)
                explode(self.potion.wx, self.potion.wy, RED_POT, 14, self.camera)
                self.potion.wx = -999   # remove

        # Player reaches exit
        if (self.exit_door.open and self.player.alive
                and pr.colliderect(self.exit_door.world_rect)):
            self.mgr.shared["keys"] = self.keys_got
            self.mgr.replace(VictoryScene(self.mgr))
            return

        # Player attack hits sentinels
        if self.player.attack_box:
            ab = self.player.attack_box
            for s in list(self.sentinels):
                if ab.colliderect(pygame.Rect(int(s.x), int(s.y), s.W, s.H)):
                    dead = s.take_damage(self.camera)
                    if dead: s.kill()
            for a in list(self.archers):
                if ab.colliderect(pygame.Rect(int(a.x), int(a.y), a.W, a.H)):
                    dead = a.take_damage(self.camera)
                    if dead: a.kill()
            if self.captain and self.captain.alive:
                if ab.colliderect(self.captain.body_rect):
                    dead = self.captain.take_damage()
                    if dead:
                        self.captain.alive = False
                        explode(self.captain.x+self.captain.W//2,
                                self.captain.y+self.captain.H//2, ARMOR_R, 50, self.camera)
                        play("exit_open", 0.70)

        # Guard bodies / attack contact
        if self.player.alive:
            for s in list(self.sentinels):
                if s.state == "ATTACK" and s.stun_t <= 0:
                    if pr.colliderect(pygame.Rect(int(s.x), int(s.y), s.W, s.H)):
                        self.player.take_damage(self.camera)
            for a in list(self.archers):
                for arrow in list(a.arrows):
                    arr = pygame.Rect(int(arrow.px)-6, int(arrow.py)-4, 12, 8)
                    if pr.colliderect(arr):
                        self.player.take_damage(self.camera)
                        arrow.kill()
            if self.captain and self.captain.alive:
                if pr.colliderect(self.captain.body_rect):
                    self.player.take_damage(self.camera)
                for axe in list(self.captain.axes):
                    ar = pygame.Rect(int(axe.px)-8, int(axe.py)-8, 16, 16)
                    if pr.colliderect(ar):
                        self.player.take_damage(self.camera)
                        axe.kill(); explode(axe.px, axe.py, ARMOR_G, 10, self.camera)

        # Game over
        if not self.player.alive and self.player.anim_t > 1.5:
            self.mgr.shared["keys"] = self.keys_got
            self.mgr.replace(GameOverScene(self.mgr))

    def draw(self, surf):
        draw_background(surf, self.camera)
        draw_tilemap(surf, self.camera)
        draw_torches(surf, self.camera, self.t_global)

        for k in self.keys_group: k.draw(surf, self.camera)
        self.potion.draw(surf, self.camera)
        self.exit_door.draw(surf, self.camera)

        for s in self.sentinels: s.draw(surf, self.camera)
        for a in self.archers:   a.draw(surf, self.camera)
        if self.captain and self.captain.alive:
            self.captain.draw(surf, self.camera)

        self.player.draw(surf, self.camera)
        particles.draw(surf)

        # Torch lighting overlay (Module 7 atmosphere)
        apply_lighting(surf, self.camera, self.t_global)

        # ── HUD ─────────────────────────────────────────────
        hud_y = HEIGHT - 50
        pygame.draw.rect(surf, (5, 5, 12), (0, hud_y, WIDTH, 50))
        pygame.draw.line(surf, STONE_GL, (0, hud_y), (WIDTH, hud_y), 1)

        # HP
        for i in range(self.player.MAX_HP):
            col = (180,30,30) if i < self.player.hp else GRAY
            pygame.draw.polygon(surf, col, self._heart(20+i*26, hud_y+18))
        blit(surf, "HP", (12, hud_y+28), GRAY, F_SM)

        # Keys
        kx = 175
        blit(surf, f"Keys: {self.keys_got}/{self.total_keys}", (kx, hud_y+10), GOLD, F_LG)
        for i in range(self.total_keys):
            col = GOLD if i < self.keys_got else GRAY
            pygame.draw.circle(surf, col, (kx+170+i*22, hud_y+24), 7)
            pygame.draw.circle(surf, WHITE, (kx+170+i*22, hud_y+24), 7, 1)

        # Exit status
        ex_col = GREEN_DR if self.exit_door.open else GRAY
        blit(surf, "EXIT: OPEN" if self.exit_door.open else "EXIT: LOCKED",
             (420, hud_y+10), ex_col, F_MD)

        # Crouch indicator
        if self.player.crouching:
            blit(surf, "[CROUCH  —  stealth active]", (420, hud_y+30), TORCH_OR, F_SM)

        # Boss HP bar
        if self.captain and self.captain.alive:
            bw = int(280 * self.captain.hp / self.captain.MAX_HP)
            pygame.draw.rect(surf, GRAY,    (WIDTH//2-140, hud_y+8, 280, 14))
            c2 = (50,200,80) if self.captain.phase==1 else DANGER_R
            pygame.draw.rect(surf, c2,      (WIDTH//2-140, hud_y+8, bw, 14))
            pygame.draw.rect(surf, WHITE,   (WIDTH//2-140, hud_y+8, 280, 14), 1)
            blit_c(surf, f"CAPTAIN  Phase {self.captain.phase}  HP {self.captain.hp}/{self.captain.MAX_HP}",
                   hud_y+28, ARMOR_R if self.captain.phase==1 else DANGER_R, F_SM)

        blit(surf, "A/D:move  S:crouch  SPACE:jump  J:attack  P:pause",
             (WIDTH-380, hud_y+34), GRAY, F_SM)

    @staticmethod
    def _heart(cx, cy):
        pts = []
        for a in range(360):
            r  = math.radians(a)
            hx = cx + 9*(math.sin(r)**3)
            hy = cy - 9*(0.8125*math.cos(r) - 0.3125*math.cos(2*r)
                         - 0.125*math.cos(3*r) - 0.0625*math.cos(4*r))
            pts.append((int(hx), int(hy)))
        return pts


# ══════════════════════════════════════════════════════════
# SCENE: PAUSE
# ══════════════════════════════════════════════════════════

class PauseScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr); self.bg = screen.copy()

    def enter(self):  MUSIC_CH.set_volume(0.10)
    def exit(self):   MUSIC_CH.set_volume(0.30)

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_p, pygame.K_RETURN): self.mgr.pop()
            if ev.key == pygame.K_ESCAPE: self.mgr.replace(MenuScene(self.mgr))

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170)); surf.blit(ov, (0,0))
        blit_c(surf, "—  PAUSED  —",         HEIGHT//2-80, TORCH_OR, F_TIT)
        blit_c(surf, "ENTER / P  →  Resume", HEIGHT//2+10, GREEN_DR, F_LG)
        blit_c(surf, "ESC        →  Menu",   HEIGHT//2+54, DANGER_R, F_MD)


# ══════════════════════════════════════════════════════════
# SCENE: GAME OVER
# ══════════════════════════════════════════════════════════

class GameOverScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr); self.t = 0.0
        self.keys = mgr.shared.get("keys", 0)

    def enter(self): MUSIC_CH.set_volume(0.12)

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN: self.mgr.replace(GameScene(self.mgr))
            if ev.key == pygame.K_ESCAPE: self.mgr.replace(MenuScene(self.mgr))

    def update(self, dt): self.t += dt; particles.update(dt)

    def draw(self, surf):
        surf.fill(DARK_BG)
        particles.draw(surf)
        pulse = abs(math.sin(self.t*2))
        blit_c(surf, "YOU FELL IN THE VAULT",  HEIGHT//2-110,
               (int(180+75*pulse), int(30+20*pulse), 30), F_TIT)
        blit_c(surf, f"Keys collected: {self.keys} / {len(KEY_POSITIONS)}",
               HEIGHT//2-10, GOLD, F_SUB)
        blit_c(surf, "ENTER  →  Try Again",  HEIGHT//2+60,  GREEN_DR, F_LG)
        blit_c(surf, "ESC    →  Main Menu",   HEIGHT//2+100, GRAY_LT,  F_MD)


# ══════════════════════════════════════════════════════════
# SCENE: VICTORY
# ══════════════════════════════════════════════════════════

class VictoryScene(Scene):
    def __init__(self, mgr):
        super().__init__(mgr); self.t = 0.0
        self.keys = mgr.shared.get("keys", 0)

    def enter(self):
        MUSIC_CH.set_volume(0.55)
        for _ in range(10):
            x = random.randint(80, WIDTH-80); y = random.randint(80, HEIGHT-80)
            for _ in range(18): particles.add(Particle(x, y, random.choice([GOLD, TORCH_OR, GREEN_DR, WHITE])))

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN: self.mgr.replace(GameScene(self.mgr))
            if ev.key == pygame.K_ESCAPE: self.mgr.replace(MenuScene(self.mgr))

    def update(self, dt):
        self.t += dt; particles.update(dt)
        if random.random() < 0.05:
            x = random.randint(60, WIDTH-60); y = random.randint(60, HEIGHT-60)
            for _ in range(10): particles.add(Particle(x, y, random.choice([GOLD, TORCH_YE, GREEN_DR])))

    def draw(self, surf):
        surf.fill(DARK_BG); particles.draw(surf)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,80)); surf.blit(ov, (0,0))
        pulse = abs(math.sin(self.t*2.5))
        blit_c(surf, "★  VAULT ESCAPED  ★", HEIGHT//2-110,
               (int(200+55*pulse), int(180+50*pulse), 30), F_TIT)
        blit_c(surf, f"All {self.keys} keys collected. Freedom!",
               HEIGHT//2-10, GREEN_DR, F_SUB)
        blit_c(surf, "ENTER  →  Play Again", HEIGHT//2+60, GOLD,    F_LG)
        blit_c(surf, "ESC    →  Main Menu",   HEIGHT//2+100, GRAY_LT, F_MD)


# ══════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    mgr = SceneManager()
    mgr.push(MenuScene(mgr))
    mgr.run()
