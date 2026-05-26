"""
════════════════════════════════════════════════════════════
 MODULE 9 — Script 03: AI Behaviors
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Patrol — move between waypoints
   • Chase  — steer toward a target using velocity
   • Flee   — steer away from a target
   • Seek   — smooth steering toward a point (arrival)
   • Line of Sight (LOS) — raycast against wall tiles
   • Vision cone — field-of-view check before chasing
   • Wander — random steering for idle movement
   • Debug visualization: vision cones, LOS rays, path lines

 Controls:
   • Move mouse:     move the player (target for AI)
   • 1:              spawn Patrol enemy
   • 2:              spawn Chase enemy
   • 3:              spawn Flee enemy
   • 4:              spawn Seek (arrival) enemy
   • C:              clear all enemies
   • W:              toggle wall obstacles
   • ESC:            quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 900, 620
FPS = 60

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (60,  60,  60)
GRAY_LT = (150, 150, 150)
BLUE    = (50,  120, 220)
GREEN   = (50,  200, 100)
RED     = (220, 80,  70)
YELLOW  = (255, 220, 50)
ORANGE  = (255, 160, 30)
PURPLE  = (160, 90,  220)
CYAN    = (50,  200, 220)
DARK_BG = (10,  10,  20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 9 — AI Behaviors")
clock  = pygame.time.Clock()

F_SM  = pygame.font.SysFont("monospace", 12)
F_MD  = pygame.font.SysFont("monospace", 15)
F_LG  = pygame.font.SysFont("monospace", 18, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MD).render(txt, True, color), pos)


# ══════════════════════════════════════════════════════════
# WALL OBSTACLES (for LOS)
# ══════════════════════════════════════════════════════════
WALL_RECTS = [
    pygame.Rect(200, 150, 20, 200),
    pygame.Rect(400, 80,  20, 180),
    pygame.Rect(600, 200, 20, 220),
    pygame.Rect(300, 380, 180, 20),
    pygame.Rect(550, 400, 20, 160),
    pygame.Rect(100, 350, 20, 150),
    pygame.Rect(720, 100, 20, 160),
]
show_walls = True


def line_of_sight(ax, ay, bx, by, walls):
    """
    Cast a ray from (ax, ay) to (bx, by).
    Returns True if the ray reaches B without hitting any wall.
    Uses the line–rect intersection algorithm.
    """
    dx = bx - ax
    dy = by - ay

    for wall in walls:
        # Check if either endpoint is inside the wall
        if wall.collidepoint(ax, ay) or wall.collidepoint(bx, by):
            return False

        # Parametric line-AABB intersection
        inv_dx = 1 / dx if dx != 0 else float('inf')
        inv_dy = 1 / dy if dy != 0 else float('inf')

        tx1 = (wall.left   - ax) * inv_dx
        tx2 = (wall.right  - ax) * inv_dx
        ty1 = (wall.top    - ay) * inv_dy
        ty2 = (wall.bottom - ay) * inv_dy

        tmin = max(min(tx1, tx2), min(ty1, ty2))
        tmax = min(max(tx1, tx2), max(ty1, ty2))

        if tmax >= 0 and tmin <= tmax and tmin <= 1:
            return False
    return True


def in_fov(ex, ey, angle, fov_deg, tx, ty):
    """Check if target (tx,ty) is within the enemy's field of view."""
    dx   = tx - ex
    dy   = ty - ey
    dist = math.hypot(dx, dy)
    if dist < 0.1:
        return True
    target_angle  = math.atan2(dy, dx)
    delta         = abs(math.atan2(math.sin(target_angle - angle),
                                    math.cos(target_angle - angle)))
    return delta <= math.radians(fov_deg / 2)


# ══════════════════════════════════════════════════════════
# STEERING BEHAVIORS
# ══════════════════════════════════════════════════════════

def seek(ex, ey, evx, evy, tx, ty, max_speed, max_force):
    """Steer toward target at full speed."""
    dx       = tx - ex
    dy       = ty - ey
    dist     = math.hypot(dx, dy)
    if dist < 0.1:
        return 0, 0
    desired_vx = (dx / dist) * max_speed
    desired_vy = (dy / dist) * max_speed
    fx = desired_vx - evx
    fy = desired_vy - evy
    # Clamp to max_force
    fmag = math.hypot(fx, fy)
    if fmag > max_force:
        fx = fx / fmag * max_force
        fy = fy / fmag * max_force
    return fx, fy


def seek_with_arrival(ex, ey, evx, evy, tx, ty, max_speed, max_force, slow_radius=80):
    """Seek but slow down as approaching the target."""
    dx   = tx - ex
    dy   = ty - ey
    dist = math.hypot(dx, dy)
    if dist < 0.1:
        return -evx * 10, -evy * 10   # Brake
    speed = max_speed if dist > slow_radius else max_speed * (dist / slow_radius)
    desired_vx = (dx / dist) * speed
    desired_vy = (dy / dist) * speed
    fx = desired_vx - evx
    fy = desired_vy - evy
    fmag = math.hypot(fx, fy)
    if fmag > max_force:
        fx = fx / fmag * max_force
        fy = fy / fmag * max_force
    return fx, fy


def flee(ex, ey, evx, evy, tx, ty, max_speed, max_force):
    """Steer away from target."""
    return seek(ex, ey, evx, evy, tx - (tx - ex) * 2, ty - (ty - ey) * 2,
                max_speed, max_force)


def wander(evx, evy, wander_angle, max_speed, max_force):
    """Random wandering using a projected circle ahead."""
    wander_angle += random.uniform(-0.4, 0.4)
    speed         = math.hypot(evx, evy)
    if speed < 1:
        heading = wander_angle
    else:
        heading = math.atan2(evy, evx)
    # Project circle ahead
    circle_x = math.cos(heading) * 50
    circle_y = math.sin(heading) * 50
    # Displacement on circle
    disp_x   = math.cos(wander_angle) * 30
    disp_y   = math.sin(wander_angle) * 30
    fx = (circle_x + disp_x)
    fy = (circle_y + disp_y)
    fmag = math.hypot(fx, fy)
    if fmag > max_force:
        fx = fx / fmag * max_force
        fy = fy / fmag * max_force
    return fx, fy, wander_angle


# ══════════════════════════════════════════════════════════
# ENEMY CLASSES
# ══════════════════════════════════════════════════════════

class Enemy:
    RADIUS = 14

    def __init__(self, x, y, color, label):
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = 0.0
        self.vy    = 0.0
        self.color = color
        self.label = label
        self.facing_angle = 0.0
        self.wander_angle = random.uniform(0, math.pi * 2)
        self.max_speed = 120.0
        self.max_force = 400.0
        self.has_los   = False
        self.in_fov_flag = False
        self.status    = "idle"

    def update(self, dt, tx, ty, walls):
        raise NotImplementedError

    def _apply_force(self, fx, fy, dt):
        self.vx += fx * dt
        self.vy += fy * dt
        speed    = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx = self.vx / speed * self.max_speed
            self.vy = self.vy / speed * self.max_speed
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Update facing angle
        if speed > 5:
            self.facing_angle = math.atan2(self.vy, self.vx)
        # Wrap around screen
        self.x = self.x % WIDTH
        self.y = self.y % (HEIGHT - 80)

    def draw(self, surf):
        ix, iy = int(self.x), int(self.y)
        r      = self.RADIUS
        pygame.draw.circle(surf, self.color, (ix, iy), r)
        pygame.draw.circle(surf, WHITE,      (ix, iy), r, 2)
        # Facing direction
        ex = ix + int(math.cos(self.facing_angle) * r)
        ey = iy + int(math.sin(self.facing_angle) * r)
        pygame.draw.line(surf, WHITE, (ix, iy), (ex, ey), 2)
        # Label
        blit(surf, self.label, (ix - 10, iy - r - 14), self.color, F_SM)
        # Status
        blit(surf, self.status, (ix - 16, iy + r + 2), GRAY_LT, F_SM)

    def draw_vision(self, surf, fov_deg, view_dist):
        """Draw vision cone."""
        ix, iy = int(self.x), int(self.y)
        steps  = 20
        pts    = [(ix, iy)]
        for i in range(steps + 1):
            a   = self.facing_angle - math.radians(fov_deg / 2) + \
                  i * math.radians(fov_deg) / steps
            px  = ix + math.cos(a) * view_dist
            py  = iy + math.sin(a) * view_dist
            pts.append((int(px), int(py)))
        col  = self.color if self.in_fov_flag else GRAY
        alpha= 60 if self.in_fov_flag else 20
        s    = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*col, alpha), pts)
        surf.blit(s, (0, 0))
        pygame.draw.lines(surf, (*col, 120), False,
                          [pts[0], pts[1], pts[-1], pts[0]], 1)


class PatrolEnemy(Enemy):
    """Moves between a list of waypoints. Chases if player in sight."""
    def __init__(self, x, y):
        super().__init__(x, y, ORANGE, "Patrol")
        self.waypoints    = [(x, y),
                             (x + random.randint(150, 280), y + random.randint(-60, 60)),
                             (x + random.randint(50, 150),  y + random.randint(80, 160))]
        self.wp_idx       = 0
        self.view_dist    = 180
        self.fov_deg      = 90

    def update(self, dt, tx, ty, walls):
        self.in_fov_flag = in_fov(self.x, self.y, self.facing_angle,
                                   self.fov_deg, tx, ty)
        self.has_los     = line_of_sight(self.x, self.y, tx, ty, walls)

        if self.in_fov_flag and self.has_los and \
                math.hypot(tx - self.x, ty - self.y) < self.view_dist:
            # Chase!
            fx, fy   = seek(self.x, self.y, self.vx, self.vy,
                            tx, ty, self.max_speed, self.max_force)
            self.status = "chase!"
        else:
            # Patrol waypoints
            wp          = self.waypoints[self.wp_idx]
            dist_wp     = math.hypot(wp[0] - self.x, wp[1] - self.y)
            if dist_wp < 20:
                self.wp_idx = (self.wp_idx + 1) % len(self.waypoints)
                wp          = self.waypoints[self.wp_idx]
            fx, fy      = seek_with_arrival(self.x, self.y, self.vx, self.vy,
                                            wp[0], wp[1], self.max_speed * 0.6,
                                            self.max_force * 0.5)
            self.status = f"patrol→{self.wp_idx}"
        self._apply_force(fx, fy, dt)

    def draw(self, surf):
        super().draw(surf)
        self.draw_vision(surf, self.fov_deg, self.view_dist)
        # Draw waypoint path
        for i, wp in enumerate(self.waypoints):
            col = ORANGE if i == self.wp_idx else GRAY
            pygame.draw.circle(surf, col, (int(wp[0]), int(wp[1])), 5, 1)
            next_wp = self.waypoints[(i + 1) % len(self.waypoints)]
            pygame.draw.line(surf, (*ORANGE, 40) if False else GRAY,
                             (int(wp[0]), int(wp[1])),
                             (int(next_wp[0]), int(next_wp[1])), 1)


class ChaseEnemy(Enemy):
    """Always chases if player is within view distance and in LOS."""
    def __init__(self, x, y):
        super().__init__(x, y, RED, "Chase")
        self.view_dist = 250
        self.fov_deg   = 130
        self.max_speed = 150.0

    def update(self, dt, tx, ty, walls):
        dist             = math.hypot(tx - self.x, ty - self.y)
        self.has_los     = line_of_sight(self.x, self.y, tx, ty, walls)
        self.in_fov_flag = in_fov(self.x, self.y, self.facing_angle,
                                   self.fov_deg, tx, ty)

        if self.has_los and self.in_fov_flag and dist < self.view_dist:
            fx, fy      = seek(self.x, self.y, self.vx, self.vy,
                               tx, ty, self.max_speed, self.max_force)
            self.status = "CHASE"
        else:
            fx, fy, self.wander_angle = wander(self.vx, self.vy, self.wander_angle,
                                                self.max_speed * 0.4, self.max_force * 0.3)
            self.status = "wander"
        self._apply_force(fx, fy, dt)

    def draw(self, surf):
        # LOS ray
        if self.has_los:
            pygame.draw.line(surf, (*RED, 80) if False else RED,
                             (int(self.x), int(self.y)),
                             pygame.mouse.get_pos(), 1)
        super().draw(surf)
        self.draw_vision(surf, self.fov_deg, self.view_dist)


class FleeEnemy(Enemy):
    """Runs away from the player."""
    def __init__(self, x, y):
        super().__init__(x, y, GREEN, "Flee")
        self.flee_dist  = 200
        self.max_speed  = 180.0
        self.fov_deg    = 200   # Wide FOV (almost eyes in the back)

    def update(self, dt, tx, ty, walls):
        dist             = math.hypot(tx - self.x, ty - self.y)
        self.has_los     = line_of_sight(self.x, self.y, tx, ty, walls)
        self.in_fov_flag = dist < self.flee_dist

        if dist < self.flee_dist:
            fx, fy      = flee(self.x, self.y, self.vx, self.vy,
                               tx, ty, self.max_speed, self.max_force)
            self.status = "FLEE!"
        else:
            fx, fy, self.wander_angle = wander(self.vx, self.vy, self.wander_angle,
                                                self.max_speed * 0.3, self.max_force * 0.3)
            self.status = "calm"
        self._apply_force(fx, fy, dt)

    def draw(self, surf):
        pygame.draw.circle(surf, (*GREEN, 40) if False else (20, 60, 30),
                           (int(self.x), int(self.y)), self.flee_dist, 1)
        super().draw(surf)


class SeekEnemy(Enemy):
    """Seeks target with smooth arrival (slows down near target)."""
    def __init__(self, x, y):
        super().__init__(x, y, CYAN, "Seek")
        self.max_speed = 200.0
        self.fov_deg   = 360

    def update(self, dt, tx, ty, walls):
        self.has_los     = line_of_sight(self.x, self.y, tx, ty, walls)
        self.in_fov_flag = True
        fx, fy           = seek_with_arrival(self.x, self.y, self.vx, self.vy,
                                              tx, ty, self.max_speed, self.max_force)
        dist = math.hypot(tx - self.x, ty - self.y)
        self.status = f"arrive d={dist:.0f}"
        self._apply_force(fx, fy, dt)

    def draw(self, surf):
        # Arrival slow radius
        pygame.draw.circle(surf, GRAY, (int(self.x), int(self.y)), 80, 1)
        blit(surf, "slow", (int(self.x) + 82, int(self.y) - 6), GRAY, F_SM)
        super().draw(surf)


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
enemies  = []
t_global = 0.0

while True:
    dt = clock.tick(FPS) / 1000.0
    t_global += dt

    tx, ty = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_1:
                rx = random.randint(50, WIDTH - 50)
                ry = random.randint(50, HEIGHT - 130)
                enemies.append(PatrolEnemy(rx, ry))
            if event.key == pygame.K_2:
                enemies.append(ChaseEnemy(random.randint(50, WIDTH-50),
                                          random.randint(50, HEIGHT-130)))
            if event.key == pygame.K_3:
                enemies.append(FleeEnemy(random.randint(50, WIDTH-50),
                                         random.randint(50, HEIGHT-130)))
            if event.key == pygame.K_4:
                enemies.append(SeekEnemy(random.randint(50, WIDTH-50),
                                         random.randint(50, HEIGHT-130)))
            if event.key == pygame.K_c:
                enemies.clear()
            if event.key == pygame.K_w:
                show_walls = not show_walls

    walls = WALL_RECTS if show_walls else []
    for e in enemies:
        e.update(dt, tx, ty, walls)

    # ── DRAW ─────────────────────────────────────────────────
    screen.fill(DARK_BG)

    for gx in range(0, WIDTH, 80):
        pygame.draw.line(screen, (16, 16, 26), (gx, 0), (gx, HEIGHT))
    for gy in range(0, HEIGHT, 80):
        pygame.draw.line(screen, (16, 16, 26), (0, gy), (WIDTH, gy))

    # Walls
    if show_walls:
        for w in WALL_RECTS:
            pygame.draw.rect(screen, (60, 50, 40), w)
            pygame.draw.rect(screen, (90, 75, 60), w, 1)

    for e in enemies:
        e.draw(screen)

    # Player cursor (mouse)
    pygame.draw.circle(screen, YELLOW, (tx, ty), 10)
    pygame.draw.circle(screen, WHITE,  (tx, ty), 10, 2)
    blit(screen, "YOU", (tx + 12, ty - 8), YELLOW, F_SM)

    # ── HUD ──────────────────────────────────────────────────
    hud_y = HEIGHT - 76
    pygame.draw.rect(screen, (10, 10, 18), (0, hud_y, WIDTH, 76))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

    blit(screen, f"Enemies: {len(enemies)}", (20, hud_y + 8), WHITE, F_LG)

    palette = [
        ("1: Patrol", ORANGE), ("2: Chase", RED),
        ("3: Flee",   GREEN),  ("4: Seek",  CYAN),
        ("C: Clear",  GRAY_LT),("W: Walls", GRAY_LT),
    ]
    for i, (lbl, col) in enumerate(palette):
        blit(screen, lbl, (200 + i * 115, hud_y + 12), col, F_SM)

    blit(screen,
         "Vision cones show FOV. Shaded = player detected. "
         "Solid walls block line of sight.",
         (20, hud_y + 46), GRAY, F_SM)
    blit(screen, "Move MOUSE to control the player target.",
         (20, hud_y + 60), GRAY_LT, F_SM)

    pygame.display.flip()
