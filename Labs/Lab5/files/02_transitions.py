"""
════════════════════════════════════════════════════════════
 MODULE 5 — Script 02: Scene Transitions
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Transition layer that runs independently of scenes
   • Fade-out → swap scene → fade-in
   • Slide transition (left/right wipe)
   • Crossfade between scene snapshots
   • How to keep scenes decoupled from transition logic

 Controls:
   • 1 / 2 / 3: switch scene (fade)
   • LEFT / RIGHT arrows: slide transition
   • F: crossfade transition
   • ESC: quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 900, 600
FPS = 60

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (80,  80,  80)
GRAY_LT = (160, 160, 160)
DARK_BG = (10,  10,  20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 5 — Scene Transitions")
clock  = pygame.time.Clock()

F_SMALL = pygame.font.SysFont("monospace", 13)
F_MED   = pygame.font.SysFont("monospace", 17)
F_LARGE = pygame.font.SysFont("monospace", 26, bold=True)
F_TITLE = pygame.font.SysFont("monospace", 44, bold=True)

def blit_centered(surf, txt, y, color=WHITE, font=None):
    s = (font or F_MED).render(txt, True, color)
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))

def blit_text(surf, txt, pos, color=WHITE, font=None):
    s = (font or F_MED).render(txt, True, color)
    surf.blit(s, pos)


# ── SCENE DEFINITIONS ─────────────────────────────────────

SCENES_DATA = [
    {"title": "Scene 1 — Menu",     "bg": (15, 10, 30),  "accent": (120, 80, 220),  "icon": "🏠"},
    {"title": "Scene 2 — Gameplay", "bg": (10, 20, 15),  "accent": (50, 200, 100),  "icon": "🎮"},
    {"title": "Scene 3 — Settings", "bg": (25, 15, 10),  "accent": (220, 150, 50),  "icon": "⚙️"},
]


def render_scene(index, t=0.0):
    """Render a scene to an offscreen surface."""
    data   = SCENES_DATA[index % len(SCENES_DATA)]
    surf   = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(data["bg"])

    # Background pattern
    accent = data["accent"]
    for i in range(8):
        ang  = t + i * math.pi / 4
        cx   = int(WIDTH  // 2 + math.cos(ang) * 160)
        cy   = int(HEIGHT // 2 + math.sin(ang) * 100)
        r    = int(30 + 20 * math.sin(t * 2 + i))
        pygame.draw.circle(surf, (*accent, 40) if False else accent, (cx, cy), r, 2)

    blit_centered(surf, data["title"], HEIGHT // 2 - 40, WHITE, F_TITLE)
    blit_centered(surf, f"Scene index: {index}", HEIGHT // 2 + 30, accent, F_LARGE)
    return surf


# ── TRANSITION ENGINE ──────────────────────────────────────

class TransitionEngine:
    """
    Manages transitions between scene renders.
    The current and next scene are pre-rendered to surfaces,
    then blended over `duration` seconds using the chosen mode.
    """

    FADE      = "fade"
    SLIDE_L   = "slide_left"
    SLIDE_R   = "slide_right"
    CROSSFADE = "crossfade"

    def __init__(self):
        self.active       = False
        self.mode         = self.FADE
        self.progress     = 0.0        # 0.0 → 1.0
        self.duration     = 0.5        # seconds
        self.surf_from    = None
        self.surf_to      = None
        self.on_complete  = None       # callback when done

    def start(self, surf_from, surf_to, mode=FADE, duration=0.5, on_complete=None):
        self.surf_from   = surf_from.copy()
        self.surf_to     = surf_to.copy()
        self.mode        = mode
        self.duration    = duration
        self.progress    = 0.0
        self.active      = True
        self.on_complete = on_complete

    def update(self, dt):
        if not self.active:
            return
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = 1.0
            self.active   = False
            if self.on_complete:
                self.on_complete()

    def draw(self, surface):
        p = self.progress
        # Ease in-out cubic
        p_ease = p * p * (3 - 2 * p)

        if self.mode == self.FADE:
            # Fade through black
            if p_ease < 0.5:
                # First half: fade out current
                alpha_out = int(255 * (1 - p_ease * 2))
                self.surf_from.set_alpha(alpha_out)
                surface.fill(BLACK)
                surface.blit(self.surf_from, (0, 0))
            else:
                # Second half: fade in next
                alpha_in = int(255 * ((p_ease - 0.5) * 2))
                self.surf_to.set_alpha(alpha_in)
                surface.fill(BLACK)
                surface.blit(self.surf_to, (0, 0))

        elif self.mode == self.CROSSFADE:
            # Blend both surfaces simultaneously
            surface.blit(self.surf_from, (0, 0))
            overlay = self.surf_to.copy()
            overlay.set_alpha(int(255 * p_ease))
            surface.blit(overlay, (0, 0))

        elif self.mode == self.SLIDE_L:
            # New scene slides in from the right
            offset = int((1 - p_ease) * WIDTH)
            surface.blit(self.surf_from, (-offset, 0))
            surface.blit(self.surf_to,   (WIDTH - offset, 0))

        elif self.mode == self.SLIDE_R:
            # New scene slides in from the left
            offset = int((1 - p_ease) * WIDTH)
            surface.blit(self.surf_from, (offset, 0))
            surface.blit(self.surf_to,   (offset - WIDTH, 0))


# ── MAIN LOOP ─────────────────────────────────────────────

engine       = TransitionEngine()
current_idx  = 0
t            = 0.0
log          = []
MAX_LOG      = 5

def do_transition(next_idx, mode, duration=0.5):
    global current_idx
    if engine.active:
        return
    surf_from = render_scene(current_idx, t)
    surf_to   = render_scene(next_idx,   t)

    def on_done():
        global current_idx
        current_idx = next_idx
        log.append(f"→ Scene {next_idx}  [{mode}]")
        if len(log) > MAX_LOG:
            log.pop(0)

    engine.start(surf_from, surf_to, mode=mode, duration=duration, on_complete=on_done)


while True:
    dt = clock.tick(FPS) / 1000.0
    t += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            # Number keys → fade to that scene
            if event.key == pygame.K_1:
                do_transition(0, TransitionEngine.FADE)
            if event.key == pygame.K_2:
                do_transition(1, TransitionEngine.FADE)
            if event.key == pygame.K_3:
                do_transition(2, TransitionEngine.FADE)
            # Arrow keys → slide
            if event.key == pygame.K_LEFT:
                do_transition((current_idx - 1) % 3, TransitionEngine.SLIDE_R)
            if event.key == pygame.K_RIGHT:
                do_transition((current_idx + 1) % 3, TransitionEngine.SLIDE_L)
            # F → crossfade
            if event.key == pygame.K_f:
                do_transition((current_idx + 1) % 3, TransitionEngine.CROSSFADE, 0.8)

    engine.update(dt)

    # ── Draw ────────────────────────────────────────────────
    if engine.active:
        engine.draw(screen)
    else:
        screen.blit(render_scene(current_idx, t), (0, 0))

    # ── HUD overlay ─────────────────────────────────────────
    hud = pygame.Surface((WIDTH, 110), pygame.SRCALPHA)
    hud.fill((0, 0, 0, 180))
    screen.blit(hud, (0, HEIGHT - 110))
    pygame.draw.line(screen, GRAY, (0, HEIGHT - 110), (WIDTH, HEIGHT - 110), 1)

    blit_text(screen, f"Current: {current_idx}  |  Transitioning: {engine.active}  "
              f"|  Progress: {engine.progress:.2f}",
              (20, HEIGHT - 104), GRAY_LT, F_SMALL)

    controls = "1/2/3: fade  |  ←→: slide  |  F: crossfade  |  ESC: quit"
    blit_text(screen, controls, (20, HEIGHT - 82), GRAY, F_SMALL)

    # Log
    for i, entry in enumerate(log):
        blit_text(screen, entry, (20, HEIGHT - 60 + i * 16),
                  (200 - i * 30,) * 3, F_SMALL)

    # Progress bar
    bar_w = int(engine.progress * (WIDTH - 40))
    pygame.draw.rect(screen, GRAY,    (20, HEIGHT - 18, WIDTH - 40, 8))
    pygame.draw.rect(screen, (100, 180, 255), (20, HEIGHT - 18, bar_w, 8))

    # Mode label
    if engine.active:
        blit_text(screen, f"MODE: {engine.mode.upper()}", (WIDTH - 220, HEIGHT - 104),
                  (100, 180, 255), F_SMALL)

    pygame.display.flip()
