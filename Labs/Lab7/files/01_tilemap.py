"""
════════════════════════════════════════════════════════════
 MODULE 7 — Script 05: Tilemap & Level Design
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Tile-based level representation (2D list of ints)
   • TileMap class: render only visible tiles (culling)
   • Multiple tile types with procedural tile surfaces
   • Tile metadata: solid, passable, special
   • Placing/removing tiles with the mouse (basic editor)
   • Level serialization (print to console)

 Controls:
   • Arrows / WASD: scroll the camera
   • Left click:    place selected tile
   • Right click:   erase tile (set to air)
   • 1-6:           select tile type
   • P:             print level to console
   • ESC:           quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 900, 620
FPS = 60
TILE_SIZE = 40

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (60,  60,  60)
GRAY_LT = (150, 150, 150)
DARK_BG = (15,  15,  25)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 7 — Tilemap")
clock  = pygame.time.Clock()

F_SMALL = pygame.font.SysFont("monospace", 12)
F_MED   = pygame.font.SysFont("monospace", 15)
F_LARGE = pygame.font.SysFont("monospace", 20, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MED).render(txt, True, color), pos)


# ══════════════════════════════════════════════════════════
# TILE DEFINITIONS
# Each tile type has: name, color, solid, and a draw function
# In a real game these would come from a spritesheet.
# ══════════════════════════════════════════════════════════

def draw_grass(surf, rect):
    pygame.draw.rect(surf, (60,  130, 50),  rect)
    pygame.draw.rect(surf, (80,  170, 60),  rect, 2)
    # Grass blades
    for gx in range(rect.left + 4, rect.right, 8):
        h = random.randint(4, 10)
        pygame.draw.line(surf, (40, 160, 40),
                         (gx, rect.top), (gx + 2, rect.top - h), 2)

def draw_stone(surf, rect):
    pygame.draw.rect(surf, (90,  90,  100), rect)
    pygame.draw.rect(surf, (110, 110, 120), rect, 2)
    # Stone cracks
    cx, cy = rect.centerx, rect.centery
    pygame.draw.line(surf, (70, 70, 80), (cx - 8, cy - 5), (cx + 3, cy + 8), 1)
    pygame.draw.line(surf, (70, 70, 80), (cx + 6, cy - 8), (cx - 2, cy + 4), 1)

def draw_dirt(surf, rect):
    pygame.draw.rect(surf, (110, 75,  40),  rect)
    pygame.draw.rect(surf, (140, 95,  55),  rect, 2)
    for _ in range(6):
        px = rect.left + random.randint(4, TILE_SIZE - 4)
        py = rect.top  + random.randint(4, TILE_SIZE - 4)
        pygame.draw.circle(surf, (90, 60, 30), (px, py), 2)

def draw_water(surf, rect, t=0.0):
    pygame.draw.rect(surf, (30, 80, 180), rect)
    for wx in range(rect.left, rect.right, 6):
        wy = rect.top + int(4 * math.sin(wx * 0.3 + t * 2)) + TILE_SIZE // 2
        pygame.draw.line(surf, (60, 140, 220), (wx, wy), (wx + 4, wy), 2)

def draw_lava(surf, rect, t=0.0):
    pygame.draw.rect(surf, (180, 50, 10), rect)
    for lx in range(rect.left, rect.right, 6):
        ly = rect.top + int(4 * math.sin(lx * 0.4 + t * 3)) + TILE_SIZE // 2
        pygame.draw.line(surf, (255, 140, 30), (lx, ly), (lx + 4, ly), 2)

def draw_spike(surf, rect):
    pygame.draw.rect(surf, (50, 50, 60), rect)
    for sx in range(rect.left + 5, rect.right, 10):
        pts = [(sx, rect.bottom), (sx + 5, rect.top + 6), (sx + 10, rect.bottom)]
        pygame.draw.polygon(surf, (200, 200, 220), pts)


TILE_DEFS = {
    0: {"name": "Air",   "solid": False, "draw": None,         "color": (0,0,0,0)},
    1: {"name": "Grass", "solid": True,  "draw": draw_grass,   "color": (60, 130, 50)},
    2: {"name": "Stone", "solid": True,  "draw": draw_stone,   "color": (90, 90, 100)},
    3: {"name": "Dirt",  "solid": True,  "draw": draw_dirt,    "color": (110, 75, 40)},
    4: {"name": "Water", "solid": False, "draw": draw_water,   "color": (30, 80, 180)},
    5: {"name": "Lava",  "solid": False, "draw": draw_lava,    "color": (180, 50, 10)},
    6: {"name": "Spike", "solid": True,  "draw": draw_spike,   "color": (50, 50, 60)},
}


# ── PRE-RENDER STATIC TILES ────────────────────────────────
# Water and lava are animated; the rest are static.

tile_cache = {}

def get_tile_surf(tile_id, t=0.0):
    """Return a rendered tile surface, from cache if static."""
    if tile_id == 0:
        return None
    if tile_id in (4, 5):
        # Animated: render every call
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(BLACK)
        rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        TILE_DEFS[tile_id]["draw"](surf, rect, t)
        return surf
    if tile_id not in tile_cache:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(BLACK)
        rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        TILE_DEFS[tile_id]["draw"](surf, rect)
        tile_cache[tile_id] = surf
    return tile_cache[tile_id]


# ── LEVEL DATA ────────────────────────────────────────────
# 0=air 1=grass 2=stone 3=dirt 4=water 5=lava 6=spike

LEVEL_W = 30
LEVEL_H = 20

LEVEL = [
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,1,1,1,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,6,6,6,6,6,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,1, 1,1,2,2,2,2,2,1,1,1, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,1,1,1,0,0,0,0,0],
    [0,0,0,1,1,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0, 4,4,4,4,0,0,0,0,0,0, 5,5,5,5,0,0,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1, 2,2,2,2,1,1,1,1,1,1, 2,2,2,2,1,1,1,1,1,1],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
    [3,3,3,3,3,3,3,3,3,3, 3,3,3,3,3,3,3,3,3,3, 3,3,3,3,3,3,3,3,3,3],
    [3,3,3,3,3,3,3,3,3,3, 3,3,3,3,3,3,3,3,3,3, 3,3,3,3,3,3,3,3,3,3],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
    [2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2],
]


# ── TILEMAP CLASS ─────────────────────────────────────────

class TileMap:
    def __init__(self, level_data, tile_size):
        self.data      = [row[:] for row in level_data]  # Deep copy
        self.tile_size = tile_size
        self.rows      = len(self.data)
        self.cols      = len(self.data[0]) if self.data else 0

    @property
    def pixel_width(self):
        return self.cols * self.tile_size

    @property
    def pixel_height(self):
        return self.rows * self.tile_size

    def get_tile(self, col, row):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.data[row][col]
        return -1   # Out of bounds

    def set_tile(self, col, row, tile_id):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.data[row][col] = tile_id

    def draw(self, surface, camera_x, camera_y, t=0.0):
        """
        Render only the tiles visible in the viewport — CULLING.
        Without culling, we'd draw ALL tiles every frame even if off-screen.
        """
        ts = self.tile_size

        # Which tiles are visible?
        col_start = max(0, int(camera_x // ts))
        col_end   = min(self.cols, int((camera_x + WIDTH)  // ts) + 1)
        row_start = max(0, int(camera_y // ts))
        row_end   = min(self.rows, int((camera_y + HEIGHT - 80) // ts) + 1)

        tiles_drawn = 0
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                tile_id = self.data[row][col]
                if tile_id == 0:
                    continue
                screen_x = col * ts - int(camera_x)
                screen_y = row * ts - int(camera_y)
                surf     = get_tile_surf(tile_id, t)
                if surf:
                    surface.blit(surf, (screen_x, screen_y))
                tiles_drawn += 1

        return tiles_drawn, (col_end - col_start) * (row_end - row_start)

    def world_to_tile(self, world_x, world_y):
        return int(world_x // self.tile_size), int(world_y // self.tile_size)

    def serialize(self):
        return "\n".join(" ".join(str(t) for t in row) for row in self.data)


# ── GAME STATE ────────────────────────────────────────────

tilemap    = TileMap(LEVEL, TILE_SIZE)
camera_x   = 0.0
camera_y   = 0.0
cam_speed  = 280.0  # px/s
selected   = 1
t_global   = 0.0

# HUD panel height
HUD_H = 80


while True:
    dt = clock.tick(FPS) / 1000.0
    t_global += dt

    mouse_pos  = pygame.mouse.get_pos()
    mouse_btns = pygame.mouse.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_p:
                print("=== LEVEL DATA ===")
                print(tilemap.serialize())
            for n in range(1, 7):
                if event.key == getattr(pygame, f"K_{n}"):
                    selected = n

    # Camera scroll
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]  or keys[pygame.K_a]: camera_x -= cam_speed * dt
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: camera_x += cam_speed * dt
    if keys[pygame.K_UP]    or keys[pygame.K_w]: camera_y -= cam_speed * dt
    if keys[pygame.K_DOWN]  or keys[pygame.K_s]: camera_y += cam_speed * dt

    # Clamp camera
    camera_x = max(0, min(camera_x, tilemap.pixel_width  - WIDTH))
    camera_y = max(0, min(camera_y, tilemap.pixel_height - (HEIGHT - HUD_H)))

    # Tile placement
    if mouse_pos[1] < HEIGHT - HUD_H:
        world_x  = mouse_pos[0] + camera_x
        world_y  = mouse_pos[1] + camera_y
        tile_col, tile_row = tilemap.world_to_tile(world_x, world_y)

        if mouse_btns[0]:   # Left: place
            tilemap.set_tile(tile_col, tile_row, selected)
        if mouse_btns[2]:   # Right: erase
            tilemap.set_tile(tile_col, tile_row, 0)

    # ── DRAW ────────────────────────────────────────────────
    screen.fill(DARK_BG)

    drawn, total = tilemap.draw(screen, camera_x, camera_y, t_global)

    # Tile grid overlay
    col_start = int(camera_x // TILE_SIZE)
    row_start = int(camera_y // TILE_SIZE)
    for col in range(col_start, col_start + WIDTH // TILE_SIZE + 2):
        sx = col * TILE_SIZE - int(camera_x)
        pygame.draw.line(screen, (25, 25, 35), (sx, 0), (sx, HEIGHT - HUD_H), 1)
    for row in range(row_start, row_start + HEIGHT // TILE_SIZE + 2):
        sy = row * TILE_SIZE - int(camera_y)
        pygame.draw.line(screen, (25, 25, 35), (0, sy), (WIDTH, sy), 1)

    # Mouse tile highlight
    if mouse_pos[1] < HEIGHT - HUD_H:
        world_x  = mouse_pos[0] + camera_x
        world_y  = mouse_pos[1] + camera_y
        tc, tr   = tilemap.world_to_tile(world_x, world_y)
        hx = tc * TILE_SIZE - int(camera_x)
        hy = tr * TILE_SIZE - int(camera_y)
        col_h = TILE_DEFS.get(selected, {}).get("color", WHITE)
        pygame.draw.rect(screen, col_h, (hx, hy, TILE_SIZE, TILE_SIZE), 2)
        preview = get_tile_surf(selected)
        if preview:
            ps = preview.copy()
            ps.set_alpha(120)
            screen.blit(ps, (hx, hy))

    # ── HUD ────────────────────────────────────────────────
    hud_y = HEIGHT - HUD_H
    pygame.draw.rect(screen, (12, 12, 20), (0, hud_y, WIDTH, HUD_H))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

    # Camera info
    blit(screen, f"Camera: ({int(camera_x)}, {int(camera_y)})",
         (20, hud_y + 6), GRAY_LT, F_SMALL)
    blit(screen, f"Tiles drawn: {drawn} / {total} (culling active)",
         (20, hud_y + 22), GRAY_LT, F_SMALL)
    blit(screen, "Arrows/WASD: scroll  |  LMB: place  |  RMB: erase  |  P: export  |  ESC: quit",
         (20, hud_y + 40), GRAY, F_SMALL)

    # Tile palette
    pal_x = WIDTH - 320
    blit(screen, "Palette:", (pal_x, hud_y + 6), GRAY_LT, F_SMALL)
    for tid in range(1, 7):
        px = pal_x + (tid - 1) * 46
        py = hud_y + 22
        col = TILE_DEFS[tid]["color"]
        border = 3 if tid == selected else 1
        pygame.draw.rect(screen, col,   (px, py, 38, 38))
        pygame.draw.rect(screen, WHITE, (px, py, 38, 38), border)
        blit(screen, str(tid), (px + 14, py + 12), WHITE, F_SMALL)
        blit(screen, TILE_DEFS[tid]["name"][:4], (px, py + 40), GRAY_LT, F_SMALL)

    # Selected label
    blit(screen, f"[{selected}] {TILE_DEFS[selected]['name']}",
         (pal_x, hud_y + 58), TILE_DEFS[selected]["color"], F_SMALL)

    pygame.display.flip()
