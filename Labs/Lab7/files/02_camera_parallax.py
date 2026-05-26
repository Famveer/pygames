"""
════════════════════════════════════════════════════════════
 MODULE 7 — Script 06: Camera, Scrolling & Parallax
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Camera class that follows a player with smoothing
   • Converting world coordinates ↔ screen coordinates
   • Parallax background layers (scroll at different speeds)
   • Camera dead zone (player moves freely before cam follows)
   • Camera shake effect on hit
   • Rendering world-space objects correctly through camera

 Controls:
   • A / D:     move left / right
   • SPACE:     jump
   • H:         trigger camera shake
   • +/-:       zoom in/out
   • ESC:       quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 900, 600
FPS = 60
TS  = 40   # Tile size

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (60,  60,  60)
GRAY_LT = (150, 150, 150)
BLUE    = (50,  120, 220)
GREEN   = (50,  200, 100)
RED     = (220, 80,  70)
YELLOW  = (255, 220, 50)
DARK_BG = (8,   8,   18)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 7 — Camera & Parallax")
clock  = pygame.time.Clock()

F_SMALL = pygame.font.SysFont("monospace", 12)
F_MED   = pygame.font.SysFont("monospace", 15)
F_LARGE = pygame.font.SysFont("monospace", 20, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MED).render(txt, True, color), pos)


# ══════════════════════════════════════════════════════════
# CAMERA
# ══════════════════════════════════════════════════════════

class Camera:
    """
    Tracks a target in world space and exposes world→screen
    coordinate conversion. Supports:
      - Smooth follow (lerp)
      - Dead zone (slack region where camera doesn't move)
      - Camera shake
      - Zoom
    """

    def __init__(self, view_w, view_h):
        self.view_w    = view_w
        self.view_h    = view_h
        self.x         = 0.0    # Camera top-left in world space
        self.y         = 0.0
        self.zoom      = 1.0
        self.smoothing = 6.0    # Higher = snappier follow
        # Dead zone: rect around screen center where cam doesn't move
        self.dead_zone = pygame.Rect(view_w//2 - 80, view_h//2 - 60, 160, 120)
        # Shake
        self._shake_timer    = 0.0
        self._shake_strength = 0.0
        self._shake_offset   = (0, 0)

    def world_to_screen(self, wx, wy):
        """Convert world coordinates to screen pixels."""
        sx = (wx - self.x) * self.zoom + self._shake_offset[0]
        sy = (wy - self.y) * self.zoom + self._shake_offset[1]
        return int(sx), int(sy)

    def screen_to_world(self, sx, sy):
        """Convert screen pixels to world coordinates."""
        wx = (sx - self._shake_offset[0]) / self.zoom + self.x
        wy = (sy - self._shake_offset[1]) / self.zoom + self.y
        return wx, wy

    def shake(self, strength=8.0, duration=0.4):
        self._shake_strength = strength
        self._shake_timer    = duration

    def follow(self, target_wx, target_wy, dt, world_w, world_h):
        """
        Smoothly move the camera to keep the target visible.
        Dead zone: if target is within the dead zone on screen, don't move.
        """
        # Target screen position if camera didn't move
        target_sx = (target_wx - self.x) * self.zoom
        target_sy = (target_wy - self.y) * self.zoom

        # Desired camera position (world units)
        desired_x = self.x
        desired_y = self.y

        if target_sx < self.dead_zone.left:
            desired_x = target_wx - self.dead_zone.left / self.zoom
        elif target_sx > self.dead_zone.right:
            desired_x = target_wx - self.dead_zone.right / self.zoom

        if target_sy < self.dead_zone.top:
            desired_y = target_wy - self.dead_zone.top / self.zoom
        elif target_sy > self.dead_zone.bottom:
            desired_y = target_wy - self.dead_zone.bottom / self.zoom

        # Lerp toward desired position
        self.x += (desired_x - self.x) * self.smoothing * dt
        self.y += (desired_y - self.y) * self.smoothing * dt

        # Clamp camera to world bounds
        max_cam_x = world_w - self.view_w / self.zoom
        max_cam_y = world_h - self.view_h / self.zoom
        self.x = max(0, min(self.x, max_cam_x))
        self.y = max(0, min(self.y, max_cam_y))

        # Update shake
        if self._shake_timer > 0:
            self._shake_timer -= dt
            pct = self._shake_timer / 0.4
            ox  = random.uniform(-1, 1) * self._shake_strength * pct
            oy  = random.uniform(-1, 1) * self._shake_strength * pct
            self._shake_offset = (ox, oy)
        else:
            self._shake_offset = (0, 0)

    def draw_debug(self, surface):
        """Draw dead zone and camera info."""
        pygame.draw.rect(surface, (60, 60, 0), self.dead_zone, 1)
        blit(surface, "dead zone", (self.dead_zone.x, self.dead_zone.y - 16),
             (100, 100, 40), F_SMALL)


# ══════════════════════════════════════════════════════════
# PARALLAX BACKGROUND
# ══════════════════════════════════════════════════════════

class ParallaxLayer:
    """
    A background layer that scrolls at `factor` of the camera speed.
    factor=0.0 → stationary, factor=1.0 → moves with world.
    """
    def __init__(self, color, factor, element_count, element_type):
        self.color        = color
        self.factor       = factor
        self.element_type = element_type
        self.elements     = []
        self._generate(element_count)

    def _generate(self, n):
        for _ in range(n):
            if self.element_type == "star":
                self.elements.append({
                    "x": random.randint(0, WIDTH * 3),
                    "y": random.randint(0, HEIGHT),
                    "r": random.randint(1, 3),
                })
            elif self.element_type == "cloud":
                self.elements.append({
                    "x": random.randint(-200, WIDTH * 3),
                    "y": random.randint(20, 180),
                    "w": random.randint(60, 180),
                    "h": random.randint(25, 55),
                })
            elif self.element_type == "mountain":
                bx = random.randint(0, WIDTH * 3)
                self.elements.append({
                    "x": bx,
                    "y": HEIGHT - random.randint(120, 280),
                    "w": random.randint(80, 200),
                })

    def draw(self, surface, camera_x):
        """
        The parallax offset = camera_x * factor.
        Slower layers (small factor) scroll less than the camera → feel far away.
        """
        offset_x = int(camera_x * self.factor)

        for e in self.elements:
            sx = e["x"] - offset_x
            # Wrap horizontally (seamless loop)
            sx = sx % (WIDTH * 3 + 400) - 200

            if self.element_type == "star":
                pygame.draw.circle(surface, self.color, (sx, e["y"]), e["r"])

            elif self.element_type == "cloud":
                pygame.draw.ellipse(surface, self.color,
                                    (sx, e["y"], e["w"], e["h"]))

            elif self.element_type == "mountain":
                pts = [(sx, HEIGHT - 80),
                       (sx + e["w"] // 2, e["y"]),
                       (sx + e["w"], HEIGHT - 80)]
                pygame.draw.polygon(surface, self.color, pts)


# ── LEVEL ──────────────────────────────────────────────────
LEVEL_W_TILES = 40
LEVEL_H_TILES = 15
WORLD_W = LEVEL_W_TILES * TS
WORLD_H = LEVEL_H_TILES * TS

LEVEL = [
    [0]*40,
    [0]*40,
    [0]*40,
    [0]*40,
    [0,0,0,0,0,0,0,0,1,1, 0,0,0,0,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,1,1, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0, 0,0,0,0,1,1,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,1,1,1,0],
    [0]*40,
    [0]*40,
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [1,1,1,1,1,1,1,0,0,1, 1,1,1,1,1,0,0,0,1,1, 1,1,1,1,1,1,0,0,1,1, 1,1,1,1,1,1,1,1,1,1],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
]

TILE_COLORS = {1: (60, 130, 50), 2: (90, 90, 100)}

def draw_level(surface, camera, level):
    for row_i, row in enumerate(level):
        for col_i, tile in enumerate(row):
            if tile == 0:
                continue
            wx = col_i * TS
            wy = row_i * TS
            sx, sy = camera.world_to_screen(wx, wy)
            if -TS < sx < WIDTH + TS and -TS < sy < HEIGHT + TS:
                col = TILE_COLORS.get(tile, WHITE)
                pygame.draw.rect(surface, col, (sx, sy, TS, TS))
                pygame.draw.rect(surface, (col[0]+30, col[1]+30, col[2]+30),
                                 (sx, sy, TS, TS), 1)

def get_solid_rects(level):
    rects = []
    for r, row in enumerate(level):
        for c, tile in enumerate(row):
            if tile != 0:
                rects.append(pygame.Rect(c*TS, r*TS, TS, TS))
    return rects

solid_rects = get_solid_rects(LEVEL)


# ── PLAYER ─────────────────────────────────────────────────
class Player:
    W, H = 28, 36
    COLOR = (50, 120, 220)

    def __init__(self, x, y):
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = 0.0
        self.vy    = 0.0
        self.on_ground = False
        self.facing    = 1

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        speed = 220.0
        if keys[pygame.K_a]: self.vx = -speed; self.facing = -1
        elif keys[pygame.K_d]: self.vx = speed; self.facing = 1
        else: self.vx *= 0.75

        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -500
            self.on_ground = False

        self.vy += 900 * dt   # Gravity

        self.x += self.vx * dt
        for r in solid_rects:
            if self.rect.colliderect(r):
                if self.vx > 0: self.x = r.left - self.W
                elif self.vx < 0: self.x = r.right
                self.vx = 0

        self.y += self.vy * dt
        self.on_ground = False
        for r in solid_rects:
            if self.rect.colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.H
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = r.bottom
                self.vy = 0

        self.x = max(0, min(self.x, WORLD_W - self.W))
        self.y = max(0, min(self.y, WORLD_H - self.H))

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        zoom   = camera.zoom
        w = int(self.W * zoom)
        h = int(self.H * zoom)
        # Body
        pygame.draw.rect(surface, self.COLOR, (sx, sy, w, h), border_radius=4)
        pygame.draw.rect(surface, WHITE,      (sx, sy, w, h), 1, border_radius=4)
        # Eyes
        ex = sx + (w - 8 if self.facing > 0 else 4)
        pygame.draw.circle(surface, WHITE, (ex, sy + 10), 4)
        pygame.draw.circle(surface, BLACK, (ex + self.facing * 1, sy + 10), 2)


# ── PARALLAX LAYERS ────────────────────────────────────────
bg_layers = [
    ParallaxLayer((20, 20, 60),      0.05, 120, "star"),
    ParallaxLayer((30, 30, 80),      0.08, 60,  "star"),
    ParallaxLayer((40, 35, 55),      0.15, 8,   "mountain"),
    ParallaxLayer((55, 50, 70),      0.25, 6,   "mountain"),
    ParallaxLayer((200, 210, 230),   0.30, 10,  "cloud"),
    ParallaxLayer((180, 190, 220),   0.50, 6,   "cloud"),
]

camera = Camera(WIDTH, HEIGHT)
player = Player(3 * TS, 9 * TS - 36)
t_global = 0.0
show_debug = True

while True:
    dt = clock.tick(FPS) / 1000.0
    t_global += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_h:
                camera.shake(10, 0.5)
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                camera.zoom = min(3.0, camera.zoom + 0.1)
            if event.key == pygame.K_MINUS:
                camera.zoom = max(0.3, camera.zoom - 0.1)
            if event.key == pygame.K_F1:
                show_debug = not show_debug

    player.update(dt)
    camera.follow(player.x + player.W/2, player.y + player.H/2,
                  dt, WORLD_W, WORLD_H)

    # ── DRAW ─────────────────────────────────────────────────
    screen.fill(DARK_BG)

    # Parallax backgrounds
    for layer in bg_layers:
        layer.draw(screen, camera.x)

    # World
    draw_level(screen, camera, LEVEL)
    player.draw(screen, camera)

    # World bounds indicator
    rx0, ry0 = camera.world_to_screen(0, 0)
    rx1, ry1 = camera.world_to_screen(WORLD_W, WORLD_H)
    pygame.draw.rect(screen, (40, 40, 60),
                     (rx0, ry0, rx1 - rx0, ry1 - ry0), 1)

    if show_debug:
        camera.draw_debug(screen)

    # ── HUD ─────────────────────────────────────────────────
    hud_y = HEIGHT - 70
    pygame.draw.rect(screen, (10, 10, 18), (0, hud_y, WIDTH, 70))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

    blit(screen, f"Camera world pos:  ({camera.x:.0f}, {camera.y:.0f})",
         (20, hud_y + 6), GRAY_LT, F_SMALL)
    blit(screen, f"Player world pos:  ({player.x:.0f}, {player.y:.0f})",
         (20, hud_y + 22), GRAY_LT, F_SMALL)
    px_s, py_s = camera.world_to_screen(player.x, player.y)
    blit(screen, f"Player screen pos: ({px_s}, {py_s})   zoom: {camera.zoom:.1f}",
         (20, hud_y + 38), GRAY_LT, F_SMALL)

    blit(screen,
         "A/D: move  |  SPACE: jump  |  H: shake  |  +/-: zoom  |  F1: debug  |  ESC: quit",
         (20, hud_y + 54), GRAY, F_SMALL)

    # Parallax speed indicators
    px2 = WIDTH - 300
    blit(screen, "Parallax layers:", (px2, hud_y + 6), GRAY_LT, F_SMALL)
    layer_names = ["Stars far", "Stars near", "Mtn far", "Mtn near", "Cloud far", "Cloud near"]
    for i, (layer, name) in enumerate(zip(bg_layers, layer_names)):
        col  = i % 3
        row2 = i // 3
        lx   = px2 + col * 98
        ly   = hud_y + 22 + row2 * 18
        blit(screen, f"{name[:8]}: {layer.factor:.2f}", (lx, ly), GRAY, F_SMALL)

    pygame.display.flip()
