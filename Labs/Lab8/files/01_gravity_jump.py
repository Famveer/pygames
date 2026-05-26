"""
════════════════════════════════════════════════════════════
 MODULE 8 — Script 01: Gravity, Velocity & Jumping
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Velocity and acceleration as vectors updated each frame
   • Gravity as constant downward acceleration
   • Variable jump height (short tap vs hold)
   • Coyote time  — jump grace period after walking off a ledge
   • Jump buffering — input registered slightly before landing
   • Terminal velocity — cap on falling speed
   • Debug panel showing all physics values live

 Controls:
   • A / D:       move left / right
   • SPACE:       jump (hold for higher jump)
   • G:           toggle gravity on/off
   • +/-:         increase / decrease gravity strength
   • F1:          toggle debug overlay
   • R:           reset player
   • ESC:         quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 900, 620
FPS   = 60
TS    = 40

BLACK    = (0,   0,   0)
WHITE    = (255, 255, 255)
GRAY     = (60,  60,  60)
GRAY_LT  = (150, 150, 150)
BLUE     = (50,  120, 220)
BLUE_LT  = (100, 160, 255)
GREEN    = (50,  200, 100)
RED      = (220, 80,  70)
YELLOW   = (255, 220, 50)
ORANGE   = (255, 160, 30)
PURPLE   = (160, 90,  220)
CYAN     = (50,  200, 220)
DARK_BG  = (10,  10,  20)
MAROON   = (100, 55,  30)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 8 — Gravity & Jumping")
clock  = pygame.time.Clock()

F_SM  = pygame.font.SysFont("monospace", 12)
F_MD  = pygame.font.SysFont("monospace", 15)
F_LG  = pygame.font.SysFont("monospace", 20, bold=True)
F_TIT = pygame.font.SysFont("monospace", 26, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MD).render(txt, True, color), pos)

def blit_c(surf, txt, y, color=WHITE, font=None):
    s = (font or F_MD).render(txt, True, color)
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))

def bar(surf, x, y, w, h, value, vmin, vmax, color, label=""):
    """Draw a value bar from vmin to vmax."""
    pygame.draw.rect(surf, GRAY, (x, y, w, h))
    pct   = (value - vmin) / (vmax - vmin)
    pct   = max(0.0, min(1.0, pct))
    fill_w= int(w * pct)
    pygame.draw.rect(surf, color, (x, y, fill_w, h))
    pygame.draw.rect(surf, GRAY_LT, (x, y, w, h), 1)
    # Center line (zero)
    if vmin < 0 < vmax:
        zx = x + int(w * (-vmin) / (vmax - vmin))
        pygame.draw.line(surf, WHITE, (zx, y), (zx, y + h), 1)
    if label:
        blit(surf, label, (x + w + 6, y - 1), GRAY_LT, F_SM)


# ══════════════════════════════════════════════════════════
# PLATFORM LAYOUT
# ══════════════════════════════════════════════════════════
PLATFORMS = [
    pygame.Rect(0,    560, WIDTH, 60),   # Ground
    pygame.Rect(100,  440, 160,  16),
    pygame.Rect(320,  380, 120,  16),
    pygame.Rect(500,  300, 180,  16),
    pygame.Rect(700,  400, 140,  16),
    pygame.Rect(200,  260, 100,  16),
    pygame.Rect(580,  200, 120,  16),
    pygame.Rect(50,   170, 80,   16),
]

def draw_platforms(surf):
    for p in PLATFORMS:
        pygame.draw.rect(surf, (70, 100, 55), p)
        pygame.draw.rect(surf, (90, 140, 70), p, 2)
        # Top edge highlight
        pygame.draw.line(surf, (110, 170, 85), p.topleft, p.topright, 2)


# ══════════════════════════════════════════════════════════
# PHYSICS CONSTANTS  (all tweakable with +/-)
# ══════════════════════════════════════════════════════════
GRAVITY_DEFAULT  = 900.0    # px/s²
JUMP_VELOCITY    = -480.0   # px/s  (negative = upward)
MOVE_SPEED       = 220.0    # px/s  horizontal
FRICTION         = 0.78     # multiplied each frame when no key held
TERMINAL_VEL     = 900.0    # max falling speed px/s

COYOTE_FRAMES    = 8        # frames of grace after walking off ledge
JUMP_BUFFER_FRAMES = 10     # frames jump input is remembered before landing

# Variable jump: hold SPACE for full jump, release early for short jump
MIN_JUMP_FRAMES  = 6        # minimum frames gravity is reduced while jumping
MAX_JUMP_FRAMES  = 20       # maximum frames of reduced gravity


# ══════════════════════════════════════════════════════════
# PLAYER
# ══════════════════════════════════════════════════════════
class Player:
    W, H = 28, 38

    def __init__(self):
        self.reset()

    def reset(self):
        self.x        = 60.0
        self.y        = 510.0
        self.vx       = 0.0
        self.vy       = 0.0
        self.on_ground= False
        self.facing   = 1

        # Coyote time
        self.coyote_timer = 0

        # Jump buffer
        self.jump_buffer  = 0

        # Variable jump state
        self.jumping       = False
        self.jump_frames   = 0

        # Stats for HUD
        self.max_vy        = 0.0
        self.jumps_done    = 0
        self.coyote_used   = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, dt, gravity, gravity_on):
        keys = pygame.key.get_pressed()

        # ── Horizontal movement ───────────────────────────
        if keys[pygame.K_a]:
            self.vx   = -MOVE_SPEED
            self.facing = -1
        elif keys[pygame.K_d]:
            self.vx   =  MOVE_SPEED
            self.facing =  1
        else:
            self.vx  *= FRICTION   # Friction deceleration

        if abs(self.vx) < 1:
            self.vx = 0

        # ── Coyote time counter ───────────────────────────
        if self.on_ground:
            self.coyote_timer = COYOTE_FRAMES
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        # ── Jump buffer counter ───────────────────────────
        if self.jump_buffer > 0:
            self.jump_buffer -= 1

        # ── Can we jump? ──────────────────────────────────
        can_jump = self.on_ground or self.coyote_timer > 0

        if self.jump_buffer > 0 and can_jump:
            was_coyote     = not self.on_ground and self.coyote_timer > 0
            self.vy        = JUMP_VELOCITY
            self.jumping   = True
            self.jump_frames = 0
            self.jump_buffer = 0
            self.coyote_timer= 0
            self.jumps_done += 1
            if was_coyote:
                self.coyote_used += 1

        # ── Variable jump: reduce gravity while holding ───
        if self.jumping:
            self.jump_frames += 1
            if not keys[pygame.K_SPACE] and self.jump_frames > MIN_JUMP_FRAMES:
                self.jumping = False   # Cut jump short
            if self.jump_frames >= MAX_JUMP_FRAMES:
                self.jumping = False

        # ── Apply gravity ─────────────────────────────────
        if gravity_on:
            grav_mult = 0.4 if self.jumping else 1.0   # Reduced during jump hold
            self.vy  += gravity * grav_mult * dt
            self.vy   = min(self.vy, TERMINAL_VEL)

        self.max_vy = max(self.max_vy, abs(self.vy))

        # ── Integrate position ────────────────────────────
        # Move X, resolve collisions
        self.x += self.vx * dt
        self._resolve_x()

        # Move Y, resolve collisions
        prev_on_ground = self.on_ground
        self.on_ground = False
        self.y += self.vy * dt
        self._resolve_y()

        # Clamp to screen
        self.x = max(0, min(self.x, WIDTH - self.W))
        if self.y > HEIGHT:
            self.reset()

    def _resolve_x(self):
        r = self.rect
        for p in PLATFORMS:
            if r.colliderect(p):
                if self.vx > 0:
                    self.x = p.left - self.W
                elif self.vx < 0:
                    self.x = p.right
                self.vx = 0

    def _resolve_y(self):
        r = self.rect
        for p in PLATFORMS:
            if r.colliderect(p):
                if self.vy > 0:
                    self.y      = p.top - self.H
                    self.vy     = 0
                    self.on_ground = True
                    self.jumping   = False
                elif self.vy < 0:
                    self.y  = p.bottom
                    self.vy = 0

    def draw(self, surf):
        sx, sy = int(self.x), int(self.y)

        # Shadow
        if self.on_ground:
            pygame.draw.ellipse(surf, (0, 0, 0),
                                (sx + 2, sy + self.H - 4, self.W - 4, 8))

        # Body
        col = BLUE_LT if self.jumping else BLUE
        pygame.draw.rect(surf, col, (sx, sy, self.W, self.H), border_radius=5)
        pygame.draw.rect(surf, WHITE, (sx, sy, self.W, self.H), 1, border_radius=5)

        # Eyes
        ex = sx + (self.W - 10 if self.facing > 0 else 6)
        pygame.draw.circle(surf, WHITE, (ex, sy + 12), 5)
        pygame.draw.circle(surf, BLACK, (ex + self.facing, sy + 12), 3)

        # Velocity vector arrow
        scale = 0.12
        cx    = sx + self.W // 2
        cy    = sy + self.H // 2
        ex2   = cx + int(self.vx * scale)
        ey2   = cy + int(self.vy * scale)
        if abs(self.vx) > 5 or abs(self.vy) > 5:
            pygame.draw.line(surf, YELLOW, (cx, cy), (ex2, ey2), 2)
            pygame.draw.circle(surf, YELLOW, (ex2, ey2), 3)

    def draw_debug(self, surf):
        # Coyote timer bar
        if self.coyote_timer > 0:
            pct = self.coyote_timer / COYOTE_FRAMES
            bx  = int(self.x) - 5
            pygame.draw.rect(surf, ORANGE,
                             (bx, int(self.y) - 10, int(38 * pct), 5))
            blit(surf, "coyote", (bx, int(self.y) - 22), ORANGE, F_SM)

        # Jump buffer bar
        if self.jump_buffer > 0:
            pct = self.jump_buffer / JUMP_BUFFER_FRAMES
            bx  = int(self.x) - 5
            pygame.draw.rect(surf, CYAN,
                             (bx, int(self.y) - 6, int(38 * pct), 4))


# ══════════════════════════════════════════════════════════
# VELOCITY TRAIL
# ══════════════════════════════════════════════════════════
trail = []  # list of (x, y, age)

def update_trail(player):
    trail.append([player.x + player.W/2, player.y + player.H/2, 1.0])
    for t in trail:
        t[2] -= 0.04
    trail[:] = [t for t in trail if t[2] > 0]

def draw_trail(surf):
    for t in trail:
        alpha = int(t[2] * 120)
        r     = int(t[2] * 5)
        if r > 0:
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 160, 255, alpha), (r, r), r)
            surf.blit(s, (int(t[0])-r, int(t[1])-r))


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
player      = Player()
gravity_val = GRAVITY_DEFAULT
gravity_on  = True
show_debug  = True
t_global    = 0.0

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
                player.reset(); trail.clear()
            if event.key == pygame.K_g:
                gravity_on = not gravity_on
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                gravity_val = min(2400, gravity_val + 100)
            if event.key == pygame.K_MINUS:
                gravity_val = max(100, gravity_val - 100)
            if event.key == pygame.K_F1:
                show_debug = not show_debug
            # Register jump buffer on keydown
            if event.key == pygame.K_SPACE:
                player.jump_buffer = JUMP_BUFFER_FRAMES

    player.update(dt, gravity_val, gravity_on)
    update_trail(player)

    # ── DRAW ─────────────────────────────────────────────────
    screen.fill(DARK_BG)

    # Background grid
    for gx in range(0, WIDTH, 80):
        pygame.draw.line(screen, (16, 16, 26), (gx, 0), (gx, HEIGHT))
    for gy in range(0, HEIGHT, 80):
        pygame.draw.line(screen, (16, 16, 26), (0, gy), (WIDTH, gy))

    draw_trail(screen)
    draw_platforms(screen)

    if show_debug:
        player.draw_debug(screen)
    player.draw(screen)

    # ── Physics Debug Panel ───────────────────────────────────
    panel_w = 280
    px      = WIDTH - panel_w - 10
    py      = 10
    ph      = 380
    pygame.draw.rect(screen, (12, 12, 22), (px, py, panel_w, ph), border_radius=8)
    pygame.draw.rect(screen, GRAY,         (px, py, panel_w, ph), 1, border_radius=8)

    blit(screen, "PHYSICS DEBUG", (px + 10, py + 10), CYAN, F_LG)
    pygame.draw.line(screen, GRAY, (px + 10, py + 36), (px + panel_w - 10, py + 36), 1)

    rows = [
        ("vx",         f"{player.vx:+.1f} px/s",   BLUE,   player.vx,   -MOVE_SPEED, MOVE_SPEED),
        ("vy",         f"{player.vy:+.1f} px/s",   GREEN,  player.vy,   JUMP_VELOCITY, TERMINAL_VEL),
        ("gravity",    f"{gravity_val:.0f} px/s²",  YELLOW, gravity_val, 100, 2400),
        ("coyote",     f"{player.coyote_timer} / {COYOTE_FRAMES} fr", ORANGE,
                       player.coyote_timer, 0, COYOTE_FRAMES),
        ("jump buf",   f"{player.jump_buffer} / {JUMP_BUFFER_FRAMES} fr", CYAN,
                       player.jump_buffer, 0, JUMP_BUFFER_FRAMES),
    ]

    for i, (label, val_txt, color, val, vmin, vmax) in enumerate(rows):
        ry = py + 48 + i * 54
        blit(screen, label,   (px + 10,  ry),      GRAY_LT, F_SM)
        blit(screen, val_txt, (px + 80,  ry),      color,   F_SM)
        bar(screen, px + 10, ry + 16, panel_w - 24, 12,
            val, vmin, vmax, color)

    # Flags
    fy = py + 48 + len(rows) * 54
    flags = [
        ("on_ground",  player.on_ground,  GREEN),
        ("jumping",    player.jumping,    BLUE_LT),
        ("gravity_on", gravity_on,        YELLOW),
    ]
    for i, (name, state, color) in enumerate(flags):
        fx = px + 10 + i * 86
        col_bg = color if state else GRAY
        pygame.draw.rect(screen, col_bg, (fx, fy, 78, 22), 0 if state else 1, border_radius=4)
        blit(screen, name[:8], (fx + 3, fy + 4), BLACK if state else GRAY_LT, F_SM)

    # Counters
    cy2 = fy + 32
    blit(screen, f"Jumps:  {player.jumps_done}",    (px + 10, cy2),      WHITE,  F_SM)
    blit(screen, f"Coyote: {player.coyote_used}",   (px + 10, cy2 + 16), ORANGE, F_SM)
    blit(screen, f"Max vy: {player.max_vy:.0f}",    (px + 10, cy2 + 32), GREEN,  F_SM)

    # ── Controls HUD ─────────────────────────────────────────
    hud_y = HEIGHT - 52
    pygame.draw.rect(screen, (10, 10, 18), (0, hud_y, WIDTH, 52))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

    ctrl = [
        "A/D: move",  "SPACE: jump (hold=higher)",
        "G: gravity", "+/-: gravity strength",
        "F1: debug",  "R: reset  |  ESC: quit",
    ]
    for i, c in enumerate(ctrl):
        col2 = i % 2
        row2 = i // 2
        blit(screen, c, (20 + col2 * 320, hud_y + 8 + row2 * 18), GRAY, F_SM)

    # Physics formula display
    blit(screen, "vy += gravity × dt   |   y += vy × dt   |   vx × friction",
         (20, hud_y + 36), GRAY_LT, F_SM)

    pygame.display.flip()
