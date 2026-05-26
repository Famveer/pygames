"""
════════════════════════════════════════════════════════════
 MODULE 9 — Script 04: Enemy Finite State Machine
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Full enemy FSM with 6 states and clear transitions
   • Each state has: enter(), update(), exit() hooks
   • State timer — time spent in current state
   • Memory — enemy remembers last seen player position
   • Health system — enemy flees when low on health
   • Visual HUD showing the full state diagram live

 States:
   IDLE → PATROL → ALERT → CHASE → ATTACK → FLEE
          ↑                              ↓
          └──────────────────────────────┘

 Controls:
   • Move mouse:       control the player
   • CLICK:           deal damage to nearest enemy
   • SPACE:           spawn new enemy
   • R:               reset all enemies
   • ESC:             quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 1000, 660
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
pygame.display.set_caption("Module 9 — Enemy FSM")
clock  = pygame.time.Clock()

F_SM  = pygame.font.SysFont("monospace", 12)
F_MD  = pygame.font.SysFont("monospace", 14)
F_LG  = pygame.font.SysFont("monospace", 18, bold=True)
F_TIT = pygame.font.SysFont("monospace", 22, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MD).render(txt, True, color), pos)


# ══════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════
DETECT_RADIUS   = 200
ATTACK_RADIUS   = 40
FLEE_HEALTH_PCT = 0.25    # Flee when HP < 25%
PATROL_SPEED    = 60.0
CHASE_SPEED     = 160.0
FLEE_SPEED      = 190.0
ALERT_DURATION  = 1.5     # seconds in ALERT before chasing
IDLE_DURATION   = 2.0     # seconds idle before patrolling
ATTACK_COOLDOWN = 0.8     # seconds between attacks
MEMORY_DURATION = 3.0     # seconds to remember player position

STATE_COLORS = {
    "IDLE":    GRAY_LT,
    "PATROL":  BLUE,
    "ALERT":   YELLOW,
    "CHASE":   ORANGE,
    "ATTACK":  RED,
    "FLEE":    PURPLE,
}


# ══════════════════════════════════════════════════════════
# FSM ENEMY
# ══════════════════════════════════════════════════════════

class EnemyFSM:
    RADIUS = 16
    MAX_HP = 100

    def __init__(self, x, y):
        self.x           = float(x)
        self.y           = float(y)
        self.vx          = 0.0
        self.vy          = 0.0
        self.hp          = self.MAX_HP
        self.facing      = 0.0   # angle in radians

        # Patrol waypoints
        self.waypoints   = self._gen_waypoints()
        self.wp_idx      = 0

        # Memory
        self.last_seen_x = None
        self.last_seen_y = None
        self.memory_timer= 0.0

        # FSM
        self.state        = "IDLE"
        self.state_timer  = 0.0   # Time in current state
        self.attack_cd    = 0.0
        self.damage_done  = 0

        # History for the diagram
        self.state_history = ["IDLE"]
        self.transitions   = []   # (from, to, time)

        # Flash on hit
        self.hit_flash    = 0.0

    def _gen_waypoints(self):
        base = [(self.x, self.y)]
        for _ in range(3):
            px = random.randint(60, WIDTH - 280)
            py = random.randint(60, HEIGHT - 120)
            base.append((px, py))
        return base

    # ── State machine transition ──────────────────────────
    def _transition(self, new_state):
        if new_state == self.state:
            return
        self.transitions.append((self.state, new_state))
        if len(self.transitions) > 8:
            self.transitions.pop(0)
        self.state_history.append(new_state)
        if len(self.state_history) > 6:
            self.state_history.pop(0)

        # on_exit hooks
        if self.state == "ATTACK":
            self.attack_cd = ATTACK_COOLDOWN

        self.state       = new_state
        self.state_timer = 0.0

        # on_enter hooks
        if new_state == "ALERT":
            self.vx = 0; self.vy = 0   # Stop momentarily
        if new_state == "IDLE":
            self.vx = 0; self.vy = 0

    # ── Per-state update ──────────────────────────────────
    def update(self, dt, tx, ty):
        self.state_timer += dt
        self.attack_cd    = max(0, self.attack_cd - dt)
        if self.hit_flash > 0:
            self.hit_flash -= dt

        # Update memory
        dist = math.hypot(tx - self.x, ty - self.y)
        if dist < DETECT_RADIUS:
            self.last_seen_x  = tx
            self.last_seen_y  = ty
            self.memory_timer = MEMORY_DURATION
        elif self.memory_timer > 0:
            self.memory_timer -= dt

        # ── Global transitions (any state) ────────────────
        if self.hp <= 0:
            self.hp = 1   # Don't die for demo purposes

        # Low HP → flee (from any combat state)
        if self.hp / self.MAX_HP < FLEE_HEALTH_PCT and self.state in ("CHASE", "ATTACK"):
            self._transition("FLEE")

        # ── State-specific logic ──────────────────────────
        if self.state == "IDLE":
            self._update_idle(dt, dist)

        elif self.state == "PATROL":
            self._update_patrol(dt, dist)

        elif self.state == "ALERT":
            self._update_alert(dt, dist)

        elif self.state == "CHASE":
            self._update_chase(dt, tx, ty, dist)

        elif self.state == "ATTACK":
            self._update_attack(dt, tx, ty, dist)

        elif self.state == "FLEE":
            self._update_flee(dt, tx, ty, dist)

        # Integrate position
        self.x = max(self.RADIUS, min(self.x + self.vx * dt, WIDTH - 280 - self.RADIUS))
        self.y = max(self.RADIUS, min(self.y + self.vy * dt, HEIGHT - 120 - self.RADIUS))
        if math.hypot(self.vx, self.vy) > 5:
            self.facing = math.atan2(self.vy, self.vx)

    def _steer_toward(self, tx, ty, speed):
        dx   = tx - self.x
        dy   = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        self.vx = (dx / dist) * speed
        self.vy = (dy / dist) * speed

    def _steer_away(self, tx, ty, speed):
        self._steer_toward(tx - (tx - self.x) * 2,
                           ty - (ty - self.y) * 2, speed)

    def _update_idle(self, dt, dist):
        # Slowly drift to zero
        self.vx *= 0.9; self.vy *= 0.9
        if dist < DETECT_RADIUS:
            self._transition("ALERT")
        elif self.state_timer > IDLE_DURATION:
            self._transition("PATROL")

    def _update_patrol(self, dt, dist):
        wp = self.waypoints[self.wp_idx]
        self._steer_toward(wp[0], wp[1], PATROL_SPEED)
        if math.hypot(wp[0] - self.x, wp[1] - self.y) < 24:
            self.wp_idx = (self.wp_idx + 1) % len(self.waypoints)
        if dist < DETECT_RADIUS:
            self._transition("ALERT")

    def _update_alert(self, dt, dist):
        if self.state_timer > ALERT_DURATION:
            if dist < DETECT_RADIUS:
                self._transition("CHASE")
            else:
                self._transition("PATROL")

    def _update_chase(self, dt, tx, ty, dist):
        if dist < ATTACK_RADIUS:
            self._transition("ATTACK")
        elif dist > DETECT_RADIUS * 1.3 and self.memory_timer <= 0:
            self._transition("PATROL")
        elif self.last_seen_x is not None and dist > DETECT_RADIUS:
            # Move to last seen position
            self._steer_toward(self.last_seen_x, self.last_seen_y, CHASE_SPEED * 0.7)
        else:
            self._steer_toward(tx, ty, CHASE_SPEED)

    def _update_attack(self, dt, tx, ty, dist):
        self.vx *= 0.8; self.vy *= 0.8   # Stop while attacking
        if dist > ATTACK_RADIUS * 1.5:
            self._transition("CHASE")
        elif self.attack_cd <= 0:
            self.damage_done += 10
            self.attack_cd    = ATTACK_COOLDOWN
        # Recover HP slowly
        self.hp = min(self.MAX_HP, self.hp + 0.5)

    def _update_flee(self, dt, tx, ty, dist):
        self._steer_away(tx, ty, FLEE_SPEED)
        # Recover HP while fleeing
        self.hp = min(self.MAX_HP, self.hp + 2)
        if self.hp / self.MAX_HP > 0.5 or dist > DETECT_RADIUS * 1.5:
            self._transition("PATROL")

    def take_damage(self, amount):
        self.hp       -= amount
        self.hit_flash = 0.2
        if self.state in ("IDLE", "PATROL"):
            self._transition("ALERT")

    # ── Drawing ───────────────────────────────────────────
    def draw(self, surf):
        ix, iy   = int(self.x), int(self.y)
        r        = self.RADIUS
        state_col= STATE_COLORS.get(self.state, WHITE)

        # Detection / attack radius
        if self.state in ("PATROL", "IDLE"):
            pygame.draw.circle(surf, (30, 40, 50), (ix, iy), DETECT_RADIUS, 1)
        if self.state == "ATTACK":
            pygame.draw.circle(surf, (*RED, 60) if False else (60, 20, 20),
                               (ix, iy), ATTACK_RADIUS, 1)

        # Memory trail
        if self.last_seen_x and self.memory_timer > 0:
            alpha = int(255 * self.memory_timer / MEMORY_DURATION)
            pygame.draw.circle(surf, YELLOW,
                               (int(self.last_seen_x), int(self.last_seen_y)), 6, 1)
            pygame.draw.line(surf, GRAY,
                             (ix, iy),
                             (int(self.last_seen_x), int(self.last_seen_y)), 1)
            blit(surf, f"mem {self.memory_timer:.1f}s",
                 (int(self.last_seen_x) + 8, int(self.last_seen_y)), GRAY, F_SM)

        # Body (flashes white on hit)
        body_col = WHITE if self.hit_flash > 0 else state_col
        pygame.draw.circle(surf, body_col, (ix, iy), r)
        pygame.draw.circle(surf, WHITE,    (ix, iy), r, 2)

        # Facing arrow
        ex = ix + int(math.cos(self.facing) * r)
        ey = iy + int(math.sin(self.facing) * r)
        pygame.draw.line(surf, WHITE, (ix, iy), (ex, ey), 2)

        # Attack flash ring
        if self.state == "ATTACK" and self.attack_cd > ATTACK_COOLDOWN * 0.5:
            pulse_r = int(r + 8 * (1 - self.attack_cd / ATTACK_COOLDOWN))
            pygame.draw.circle(surf, RED, (ix, iy), pulse_r, 2)

        # HP bar
        hp_pct = max(0, self.hp / self.MAX_HP)
        bar_w  = r * 2 + 4
        bar_x  = ix - r - 2
        bar_y  = iy - r - 10
        pygame.draw.rect(surf, GRAY,  (bar_x, bar_y, bar_w, 5))
        hp_col = GREEN if hp_pct > 0.5 else (YELLOW if hp_pct > 0.25 else RED)
        pygame.draw.rect(surf, hp_col, (bar_x, bar_y, int(bar_w * hp_pct), 5))

        # State label
        blit(surf, self.state, (ix - 20, iy + r + 4), state_col, F_SM)
        blit(surf, f"{self.state_timer:.1f}s", (ix - 10, iy + r + 16), GRAY_LT, F_SM)


# ══════════════════════════════════════════════════════════
# FSM DIAGRAM (right panel)
# ══════════════════════════════════════════════════════════

DIAGRAM_STATES = {
    "IDLE":   (850, 120),
    "PATROL": (850, 220),
    "ALERT":  (850, 320),
    "CHASE":  (850, 420),
    "ATTACK": (850, 490),
    "FLEE":   (850, 570),
}

DIAGRAM_TRANSITIONS = [
    ("IDLE",   "PATROL", "timer"),
    ("IDLE",   "ALERT",  "detect"),
    ("PATROL", "ALERT",  "detect"),
    ("ALERT",  "CHASE",  "timer"),
    ("ALERT",  "PATROL", "lost"),
    ("CHASE",  "ATTACK", "close"),
    ("CHASE",  "PATROL", "lost"),
    ("ATTACK", "CHASE",  "far"),
    ("ATTACK", "FLEE",   "low HP"),
    ("CHASE",  "FLEE",   "low HP"),
    ("FLEE",   "PATROL", "safe"),
]


def draw_fsm_diagram(surf, enemy):
    px = WIDTH - 200
    pygame.draw.rect(surf, (12, 12, 22), (px - 20, 0, 220, HEIGHT))
    pygame.draw.line(surf, GRAY, (px - 20, 0), (px - 20, HEIGHT), 1)

    blit(surf, "FSM DIAGRAM", (px - 10, 10), CYAN, F_LG)

    # Draw states
    for state, (sx, sy) in DIAGRAM_STATES.items():
        col    = STATE_COLORS[state]
        active = (enemy is not None and enemy.state == state)
        r      = 14 if not active else 18
        pygame.draw.circle(surf, col if active else GRAY, (sx, sy), r,
                           0 if active else 2)
        blit(surf, state[:6], (sx - 22, sy - 6), WHITE if active else col, F_SM)

    # Draw transitions (simplified vertical arrows)
    for (s1, s2, label) in DIAGRAM_TRANSITIONS:
        x1, y1 = DIAGRAM_STATES[s1]
        x2, y2 = DIAGRAM_STATES[s2]
        col = GRAY
        if enemy and (enemy.state_history[-1] if enemy.state_history else "") == s2 and \
                (enemy.state_history[-2] if len(enemy.state_history) > 1 else "") == s1:
            col = YELLOW
        pygame.draw.line(surf, col, (x1, y1), (x2, y2), 1)

    # History
    if enemy:
        blit(surf, "History:", (px - 10, HEIGHT - 140), GRAY_LT, F_SM)
        for i, s in enumerate(enemy.state_history[-5:]):
            col = STATE_COLORS.get(s, GRAY_LT)
            blit(surf, f"→ {s}", (px - 10, HEIGHT - 120 + i * 18), col, F_SM)


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def spawn_enemy():
    x = random.randint(60, WIDTH - 280)
    y = random.randint(60, HEIGHT - 120)
    return EnemyFSM(x, y)

enemies  = [spawn_enemy() for _ in range(3)]
selected = 0   # Which enemy to show in diagram
t_global = 0.0

while True:
    dt = clock.tick(FPS) / 1000.0
    t_global += dt

    tx, ty = pygame.mouse.get_pos()
    tx = min(tx, WIDTH - 220)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_SPACE:
                enemies.append(spawn_enemy())
            if event.key == pygame.K_r:
                enemies = [spawn_enemy() for _ in range(3)]
                selected = 0
            if event.key == pygame.K_TAB:
                selected = (selected + 1) % len(enemies)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if tx < WIDTH - 220:
                # Damage nearest enemy
                if enemies:
                    nearest = min(enemies,
                                  key=lambda e: math.hypot(e.x - tx, e.y - ty))
                    nearest.take_damage(30)

    for e in enemies:
        e.update(dt, tx, ty)

    # ── DRAW ─────────────────────────────────────────────────
    screen.fill(DARK_BG)

    for gx in range(0, WIDTH - 220, 80):
        pygame.draw.line(screen, (16, 16, 26), (gx, 0), (gx, HEIGHT))
    for gy in range(0, HEIGHT, 80):
        pygame.draw.line(screen, (16, 16, 26), (0, gy), (WIDTH - 220, gy))

    for e in enemies:
        e.draw(screen)

    # Player cursor
    pygame.draw.circle(screen, YELLOW, (tx, ty), 12)
    pygame.draw.circle(screen, WHITE,  (tx, ty), 12, 2)
    blit(screen, "YOU", (tx + 14, ty - 8), YELLOW, F_SM)

    # FSM panel
    sel_enemy = enemies[selected] if enemies else None
    draw_fsm_diagram(screen, sel_enemy)

    # Select indicator
    if sel_enemy:
        pygame.draw.circle(screen, WHITE,
                           (int(sel_enemy.x), int(sel_enemy.y)),
                           sel_enemy.RADIUS + 4, 1)

    # ── HUD ──────────────────────────────────────────────────
    hud_y = HEIGHT - 54
    pygame.draw.rect(screen, (10, 10, 18), (0, hud_y, WIDTH - 220, 54))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH - 220, hud_y), 1)

    blit(screen, f"Enemies: {len(enemies)}", (20, hud_y + 8), WHITE, F_LG)

    # State legend
    for i, (state, col) in enumerate(STATE_COLORS.items()):
        blit(screen, f"■ {state}", (200 + i * 120, hud_y + 10), col, F_SM)

    blit(screen,
         "MOVE mouse = player  |  CLICK = deal 30 dmg  |  SPACE = spawn  |  TAB = select  |  R = reset",
         (20, hud_y + 32), GRAY, F_SM)

    pygame.display.flip()
