"""
════════════════════════════════════════════════════════════
 MODULE 8 — Script 02: Advanced Platformer Physics
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Separate X and Y collision resolution (essential pattern)
   • One-way platforms (pass through from below, land from above)
   • Moving platforms (player inherits velocity)
   • Wall sliding and wall jumping
   • Acceleration-based movement (not instant velocity)
   • Air control vs ground control

 Controls:
   • A / D:        move
   • SPACE:        jump / wall jump
   • S + SPACE:    drop through one-way platform
   • R:            reset
   • ESC:          quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 900, 620
FPS  = 60

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (60,  60,  60)
GRAY_LT = (150, 150, 150)
BLUE    = (50,  120, 220)
GREEN   = (50,  200, 100)
RED     = (220, 80,  70)
YELLOW  = (255, 220, 50)
ORANGE  = (255, 160, 30)
CYAN    = (50,  200, 220)
PURPLE  = (160, 90,  220)
DARK_BG = (10,  10,  20)
TEAL    = (30,  180, 160)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 8 — Advanced Platformer Physics")
clock  = pygame.time.Clock()

F_SM  = pygame.font.SysFont("monospace", 12)
F_MD  = pygame.font.SysFont("monospace", 15)
F_LG  = pygame.font.SysFont("monospace", 19, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MD).render(txt, True, color), pos)

def blit_c(surf, txt, y, color=WHITE, font=None):
    s = (font or F_MD).render(txt, True, color)
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))


# ══════════════════════════════════════════════════════════
# PLATFORM TYPES
# ══════════════════════════════════════════════════════════

class Platform:
    """Standard solid platform."""
    def __init__(self, x, y, w, h, color=(70, 100, 55)):
        self.rect  = pygame.Rect(x, y, w, h)
        self.color = color
        self.one_way = False

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)
        brighter = tuple(min(255, c + 30) for c in self.color)
        pygame.draw.rect(surf, brighter, self.rect, 2)
        highlight = tuple(min(255, c + 50) for c in self.color)
        pygame.draw.line(surf, highlight,
                         self.rect.topleft, self.rect.topright, 2)

    def update(self, dt): pass

    @property
    def vel_x(self): return 0.0
    @property
    def vel_y(self): return 0.0


class OneWayPlatform(Platform):
    """Only solid from the top — player can jump through from below."""
    def __init__(self, x, y, w):
        super().__init__(x, y, w, 10, (80, 160, 100))
        self.one_way = True

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)
        # Dashed line to show it's one-way
        for dx in range(0, self.rect.w, 14):
            pygame.draw.line(surf, (120, 220, 140),
                             (self.rect.x + dx, self.rect.y),
                             (self.rect.x + dx + 8, self.rect.y), 2)
        blit(surf, "↕", (self.rect.centerx - 6, self.rect.y - 14), GREEN, F_SM)


class MovingPlatform(Platform):
    """Moves back and forth; player inherits its velocity."""
    def __init__(self, x, y, w, x_min, x_max, speed, color=(100, 80, 180)):
        super().__init__(x, y, w, 16, color)
        self.x_min  = x_min
        self.x_max  = x_max
        self.speed  = speed
        self._dir   = 1
        self._vx    = 0.0

    def update(self, dt):
        prev_x    = self.rect.x
        self.rect.x += self._dir * self.speed * dt
        if self.rect.x <= self.x_min:
            self.rect.x = self.x_min
            self._dir   = 1
        elif self.rect.x >= self.x_max:
            self.rect.x = self.x_max
            self._dir   = -1
        self._vx = (self.rect.x - prev_x) / dt if dt > 0 else 0

    @property
    def vel_x(self): return self._vx

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)
        pygame.draw.rect(surf, PURPLE, self.rect, 2)
        # Arrow showing direction
        arrow = "→" if self._dir > 0 else "←"
        blit(surf, arrow, (self.rect.centerx - 6, self.rect.y - 14), PURPLE, F_SM)


# ── LEVEL ──────────────────────────────────────────────────
solid_platforms = [
    Platform(0, 570, WIDTH, 50),          # Ground
    Platform(0, 0, 16, HEIGHT),           # Left wall
    Platform(WIDTH - 16, 0, 16, HEIGHT),  # Right wall
    Platform(100, 440, 140, 16),
    Platform(600, 440, 140, 16),
    Platform(340, 360, 120, 16),
    Platform(100, 280, 100, 16),
    Platform(680, 290, 100, 16),
    Platform(300, 200, 80,  16),
    Platform(500, 150, 80,  16),
]

one_way_platforms = [
    OneWayPlatform(220, 490, 120),
    OneWayPlatform(450, 410, 100),
    OneWayPlatform(160, 340, 80),
    OneWayPlatform(560, 330, 100),
    OneWayPlatform(380, 250, 90),
]

moving_platforms = [
    MovingPlatform(250, 480, 100, 230, 420, 120),
    MovingPlatform(450, 300, 90,  440, 600, 90),
    MovingPlatform(200, 150, 80,  180, 380, 70, color=(80, 130, 160)),
]

all_platforms = solid_platforms + one_way_platforms + moving_platforms


# ══════════════════════════════════════════════════════════
# PLAYER
# ══════════════════════════════════════════════════════════
GRAVITY       = 900.0
TERMINAL_VEL  = 850.0
MOVE_ACCEL    = 1800.0    # Acceleration px/s²
AIR_ACCEL     = 900.0     # Less control in air
MAX_VX        = 240.0
JUMP_VY       = -460.0
WALL_JUMP_VX  = 280.0
WALL_JUMP_VY  = -400.0
WALL_SLIDE_VY = 80.0      # Slow fall when wall sliding
COYOTE_T      = 8
JUMP_BUF_T    = 10


class Player:
    W, H = 26, 36

    def __init__(self):
        self.reset()

    def reset(self):
        self.x           = 80.0
        self.y           = 520.0
        self.vx          = 0.0
        self.vy          = 0.0
        self.on_ground   = False
        self.on_platform = None   # Which platform we're standing on
        self.wall_contact= 0      # -1=left wall, 0=none, 1=right wall
        self.wall_sliding= False
        self.facing      = 1
        self.coyote      = 0
        self.jump_buf    = 0
        self.drop_timer  = 0      # Ignore one-way collision for N frames

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, dt):
        keys = pygame.key.get_pressed()

        # Drop through one-way: hold S + SPACE
        if keys[pygame.K_s] and self.on_ground:
            if self.on_platform and self.on_platform.one_way:
                self.drop_timer = 8
                self.on_ground  = False

        if self.drop_timer > 0:
            self.drop_timer -= 1

        # ── Horizontal acceleration ───────────────────────
        target_vx = 0.0
        if keys[pygame.K_a]: target_vx = -MAX_VX; self.facing = -1
        if keys[pygame.K_d]: target_vx =  MAX_VX; self.facing =  1

        accel = MOVE_ACCEL if self.on_ground else AIR_ACCEL
        if target_vx != 0:
            self.vx += (target_vx - self.vx) * (accel / MAX_VX) * dt
        else:
            # Decelerate
            decel = MOVE_ACCEL * dt
            if abs(self.vx) <= decel:
                self.vx = 0
            else:
                self.vx -= math.copysign(decel, self.vx)

        self.vx = max(-MAX_VX, min(self.vx, MAX_VX))

        # ── Coyote and jump buffer ────────────────────────
        if self.on_ground:
            self.coyote = COYOTE_T
        elif self.coyote > 0:
            self.coyote -= 1

        if self.jump_buf > 0:
            self.jump_buf -= 1

        can_jump = self.on_ground or self.coyote > 0

        # ── Jump ─────────────────────────────────────────
        if self.jump_buf > 0 and can_jump:
            self.vy          = JUMP_VY
            self.jump_buf    = 0
            self.coyote      = 0
            self.on_ground   = False

        # Wall jump
        elif self.jump_buf > 0 and self.wall_contact != 0 and not self.on_ground:
            self.vx          = -self.wall_contact * WALL_JUMP_VX
            self.vy          = WALL_JUMP_VY
            self.jump_buf    = 0
            self.wall_contact= 0

        # ── Wall slide ────────────────────────────────────
        self.wall_sliding = (self.wall_contact != 0 and not self.on_ground
                             and self.vy > 0 and
                             ((self.wall_contact == -1 and keys[pygame.K_a]) or
                              (self.wall_contact ==  1 and keys[pygame.K_d])))

        # ── Gravity ───────────────────────────────────────
        if self.wall_sliding:
            # Slow fall when sliding
            self.vy = min(self.vy + GRAVITY * dt, WALL_SLIDE_VY)
        else:
            self.vy = min(self.vy + GRAVITY * dt, TERMINAL_VEL)

        # ── Moving platform velocity inheritance ──────────
        if self.on_ground and self.on_platform:
            self.x += self.on_platform.vel_x * dt

        # ── Move X, resolve ───────────────────────────────
        self.x += self.vx * dt
        self.wall_contact = 0
        self._resolve_x()

        # ── Move Y, resolve ───────────────────────────────
        prev_ground      = self.on_ground
        self.on_ground   = False
        self.on_platform = None
        self.y          += self.vy * dt
        self._resolve_y()

        if self.y > HEIGHT + 100:
            self.reset()

    def _resolve_x(self):
        r = self.rect
        for p in all_platforms:
            if p.one_way:
                continue
            if r.colliderect(p.rect):
                if self.vx > 0:
                    self.x           = p.rect.left - self.W
                    self.wall_contact = 1
                elif self.vx < 0:
                    self.x           = p.rect.right
                    self.wall_contact = -1
                self.vx = 0

    def _resolve_y(self):
        r = self.rect
        for p in all_platforms:
            if not r.colliderect(p.rect):
                continue
            if p.one_way:
                if self.drop_timer > 0:
                    continue
                if self.vy > 0 and (self.y + self.H - self.vy * (1/FPS)) <= p.rect.top + 2:
                    self.y           = p.rect.top - self.H
                    self.vy          = 0
                    self.on_ground   = True
                    self.on_platform = p
            else:
                if self.vy > 0:
                    self.y           = p.rect.top - self.H
                    self.vy          = 0
                    self.on_ground   = True
                    self.on_platform = p
                elif self.vy < 0:
                    self.y  = p.rect.bottom
                    self.vy = 0

    def draw(self, surf):
        sx, sy = int(self.x), int(self.y)

        # Wall slide trail
        if self.wall_sliding:
            for i in range(4):
                a = max(0, 180 - i * 40)
                s = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 200, 50, a), (3, 3), 3)
                surf.blit(s, (sx + (self.W if self.wall_contact > 0 else -6),
                              sy + i * 10))

        # Body
        col = CYAN if self.wall_sliding else BLUE
        pygame.draw.rect(surf, col, (sx, sy, self.W, self.H), border_radius=5)
        pygame.draw.rect(surf, WHITE, (sx, sy, self.W, self.H), 1, border_radius=5)

        # Eyes
        ex = sx + (self.W - 9 if self.facing > 0 else 5)
        pygame.draw.circle(surf, WHITE, (ex, sy + 11), 4)
        pygame.draw.circle(surf, BLACK, (ex + self.facing, sy + 11), 2)

        # Wall slide indicator
        if self.wall_sliding:
            blit(surf, "↕slide", (sx - 4, sy - 16), CYAN, F_SM)

        # Drop hint above one-way platforms
        if self.on_ground and self.on_platform and self.on_platform.one_way:
            blit(surf, "S+SPACE to drop", (sx - 20, sy - 18), GREEN, F_SM)


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
player   = Player()
t_global = 0.0

while True:
    dt = clock.tick(FPS) / 1000.0
    t_global += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_r:
                player.reset()
            if event.key == pygame.K_SPACE:
                player.jump_buf = JUMP_BUF_T

    for p in moving_platforms:
        p.update(dt)

    player.update(dt)

    # ── DRAW ─────────────────────────────────────────────────
    screen.fill(DARK_BG)

    for gx in range(0, WIDTH, 80):
        pygame.draw.line(screen, (15, 15, 25), (gx, 0), (gx, HEIGHT))
    for gy in range(0, HEIGHT, 80):
        pygame.draw.line(screen, (15, 15, 25), (0, gy), (WIDTH, gy))

    for p in solid_platforms: p.draw(screen)
    for p in one_way_platforms: p.draw(screen)
    for p in moving_platforms: p.draw(screen)

    player.draw(screen)

    # ── HUD ──────────────────────────────────────────────────
    hud_y = HEIGHT - 76
    pygame.draw.rect(screen, (10, 10, 18), (0, hud_y, WIDTH, 76))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

    # Left: state
    states = [
        (f"vx: {player.vx:+.1f}", BLUE),
        (f"vy: {player.vy:+.1f}", GREEN),
        (f"on_ground: {player.on_ground}", YELLOW),
        (f"wall:  {player.wall_contact:+d}",  CYAN),
    ]
    for i, (txt, col) in enumerate(states):
        blit(screen, txt, (20 + (i % 2) * 180, hud_y + 8 + (i // 2) * 22), col, F_SM)

    # Legend
    legend = [
        ("■ Solid",      (70, 100, 55)),
        ("↕ One-way",    GREEN),
        ("■ Moving",     PURPLE),
    ]
    for i, (lbl, col) in enumerate(legend):
        blit(screen, lbl, (420 + i * 130, hud_y + 8), col, F_SM)

    blit(screen, "A/D: move  |  SPACE: jump  |  Wall: push toward wall + SPACE  |  S+SPACE: drop  |  R: reset",
         (20, hud_y + 54), GRAY, F_SM)

    # Platform type explanation
    pygame.draw.rect(screen, (12, 30, 12), (0, 0, WIDTH, 24))
    blit_c(screen,
           "One-way (green dashed) = jump through from below  |  "
           "Purple = moving (inherit velocity)  |  "
           "Wall slide + wall jump available",
           4, GRAY_LT, F_SM)

    pygame.display.flip()
