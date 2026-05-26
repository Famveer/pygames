"""
════════════════════════════════════════════════════════════
 MODULE 6 — Script 04: Spatial Audio & Dynamic Mixing
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Stereo panning based on position (spatial sound)
   • Distance-based volume attenuation
   • Dynamic mixing: layering sounds by game state
   • Sound cooldown to avoid overlap spam
   • pygame.mixer.Channel.set_volume(left, right) for stereo

 Controls:
   • Move mouse to change listener position
   • Click to spawn a sound source
   • SPACE: add ambient layer
   • ESC: quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random
import struct

pygame.mixer.pre_init(44100, -16, 2, 1024)   # stereo (2 channels)
pygame.init()

WIDTH, HEIGHT = 900, 600
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
DARK_BG = (10,  10,  20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 6 — Spatial Audio")
clock  = pygame.time.Clock()

F_SMALL = pygame.font.SysFont("monospace", 12)
F_MED   = pygame.font.SysFont("monospace", 15)
F_LARGE = pygame.font.SysFont("monospace", 20, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    surf.blit((font or F_MED).render(txt, True, color), pos)

SAMPLE_RATE = 44100

def gen_stereo_samples(left_samples, right_samples):
    """Interleave L and R samples into stereo PCM bytes."""
    n    = min(len(left_samples), len(right_samples))
    data = []
    for i in range(n):
        l = max(-1.0, min(1.0, left_samples[i]))
        r = max(-1.0, min(1.0, right_samples[i]))
        data.append(int(l * 32767))
        data.append(int(r * 32767))
    return struct.pack(f"{len(data)}h", *data)

def make_stereo_sound(freq, duration, vol=0.5):
    """Sine wave, identical L and R (panning done at runtime)."""
    n    = int(SAMPLE_RATE * duration)
    mono = [vol * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            * (1 - i / n) for i in range(n)]
    data = gen_stereo_samples(mono, mono)
    return pygame.mixer.Sound(buffer=data)

def make_noise_stereo(duration, vol=0.3):
    n    = int(SAMPLE_RATE * duration)
    mono = [vol * (random.random() * 2 - 1) * (1 - i / n) ** 2 for i in range(n)]
    data = gen_stereo_samples(mono, mono)
    return pygame.mixer.Sound(buffer=data)

def make_ambient(freq, duration, vol=0.15):
    n   = int(SAMPLE_RATE * duration)
    out = []
    for i in range(n):
        t   = i / SAMPLE_RATE
        env = 0.5 + 0.5 * math.sin(math.pi * i / n)
        out.append(vol * env * (math.sin(2*math.pi*freq*t) +
                                 0.3*math.sin(2*math.pi*freq*1.5*t)))
    data = gen_stereo_samples(out, out)
    return pygame.mixer.Sound(buffer=data)

print("Generating stereo audio...")
pygame.mixer.set_num_channels(16)

SOUNDS = {
    "ping":     make_stereo_sound(440, 0.4),
    "low":      make_stereo_sound(220, 0.5),
    "high":     make_stereo_sound(880, 0.3),
    "noise":    make_noise_stereo(0.3),
    "ambient":  make_ambient(130, 2.0),
}
print("Ready.")

MAX_DIST = 400.0   # Beyond this distance, sound is inaudible

class SoundSource:
    """A point in the world that emits sound."""
    COLOR_MAP = {"ping": YELLOW, "low": BLUE, "high": GREEN, "noise": RED}

    def __init__(self, x, y, kind):
        self.x    = x
        self.y    = y
        self.kind = kind
        self.color= self.COLOR_MAP.get(kind, WHITE)
        self.t    = 0.0
        self.channel = None
        self.alive = True

    def update_spatial(self, listener_x, listener_y, dt):
        self.t += dt
        dx   = self.x - listener_x
        dy   = self.y - listener_y
        dist = math.hypot(dx, dy)

        # Distance attenuation (linear falloff)
        vol = max(0.0, 1.0 - dist / MAX_DIST)

        # Stereo panning: normalize x position in screen
        pan   = (self.x / WIDTH) * 2 - 1   # -1 (left) to +1 (right)
        left  = vol * (1.0 - max(0, pan))
        right = vol * (1.0 + min(0, pan))
        left  = max(0.0, min(1.0, left))
        right = max(0.0, min(1.0, right))

        if self.channel and self.channel.get_busy():
            self.channel.set_volume(left, right)

        # Auto-remove after 3 seconds
        if self.t > 3.0:
            if self.channel:
                self.channel.stop()
            self.alive = False

    def play(self):
        sound      = SOUNDS.get(self.kind, SOUNDS["ping"])
        self.channel = sound.play(loops=2)
        if self.channel:
            self.channel.set_volume(0.5, 0.5)

    def draw(self, surface, listener_x, listener_y):
        if not self.alive:
            return
        dx   = self.x - listener_x
        dy   = self.y - listener_y
        dist = math.hypot(dx, dy)
        vol  = max(0.0, 1.0 - dist / MAX_DIST)

        # Draw ripple rings
        rings = 3
        for r in range(rings):
            phase = (self.t * 120 + r * 40) % 120
            ring_r= int(phase * (1 + vol))
            alpha = max(0, int(180 * (1 - phase / 120) * vol))
            if ring_r > 0 and alpha > 0:
                ring_surf = pygame.Surface((ring_r*2+2, ring_r*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*self.color, alpha),
                                   (ring_r+1, ring_r+1), ring_r, 1)
                surface.blit(ring_surf, (int(self.x)-ring_r-1, int(self.y)-ring_r-1))

        # Core dot
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 8)
        pygame.draw.circle(surface, WHITE,      (int(self.x), int(self.y)), 8, 1)

        # Volume bar above
        bar_w = int(vol * 60)
        pygame.draw.rect(surface, GRAY,       (int(self.x)-30, int(self.y)-24, 60, 6))
        pygame.draw.rect(surface, self.color, (int(self.x)-30, int(self.y)-24, bar_w, 6))
        label = F_SMALL.render(f"{self.kind} {vol:.2f}", True, self.color)
        surface.blit(label, (int(self.x)-30, int(self.y)-38))


sources        = []
ambient_channel= None
t_global       = 0.0
click_cooldown = 0.0
KINDS          = ["ping", "low", "high", "noise"]
kind_idx       = 0

while True:
    dt = clock.tick(FPS) / 1000.0
    t_global      += dt
    click_cooldown = max(0, click_cooldown - dt)

    listener_x, listener_y = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_SPACE:
                # Toggle ambient layer
                if ambient_channel and ambient_channel.get_busy():
                    ambient_channel.fadeout(500)
                    ambient_channel = None
                else:
                    ambient_channel = SOUNDS["ambient"].play(loops=-1)
                    if ambient_channel:
                        ambient_channel.set_volume(0.15, 0.15)
            if event.key == pygame.K_TAB:
                kind_idx = (kind_idx + 1) % len(KINDS)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if click_cooldown <= 0:
                src = SoundSource(event.pos[0], event.pos[1], KINDS[kind_idx])
                src.play()
                sources.append(src)
                click_cooldown = 0.2

    # Update sources
    for src in sources:
        src.update_spatial(listener_x, listener_y, dt)
    sources = [s for s in sources if s.alive]

    # ── DRAW ────────────────────────────────────────────────
    screen.fill(DARK_BG)

    # Grid
    for gx in range(0, WIDTH, 80):
        pygame.draw.line(screen, (16, 16, 26), (gx, 0), (gx, HEIGHT))
    for gy in range(0, HEIGHT, 80):
        pygame.draw.line(screen, (16, 16, 26), (0, gy), (WIDTH, gy))

    # Max-distance circle around listener
    pygame.draw.circle(screen, (30, 30, 50),
                       (listener_x, listener_y), int(MAX_DIST), 1)

    # Sources
    for src in sources:
        src.draw(screen, listener_x, listener_y)

    # Listener (ear icon)
    pygame.draw.circle(screen, WHITE, (listener_x, listener_y), 12)
    pygame.draw.circle(screen, BLUE,  (listener_x, listener_y), 12, 2)
    lbl = F_SMALL.render("👂", True, WHITE)
    screen.blit(lbl, (listener_x - 6, listener_y - 8))

    # Line from listener to each source
    for src in sources:
        dx   = src.x - listener_x
        dy   = src.y - listener_y
        dist = math.hypot(dx, dy)
        vol  = max(0.0, 1.0 - dist / MAX_DIST)
        if vol > 0.05:
            pygame.draw.line(screen, (*src.color, int(vol * 80)),
                             (listener_x, listener_y), (int(src.x), int(src.y)), 1)

    # ── HUD ────────────────────────────────────────────────
    hud_y = HEIGHT - 80
    pygame.draw.rect(screen, (12, 12, 20), (0, hud_y, WIDTH, 80))
    pygame.draw.line(screen, GRAY, (0, hud_y), (WIDTH, hud_y), 1)

    blit(screen, f"Selected sound:  {KINDS[kind_idx]}   (TAB to cycle)",
         (20, hud_y + 8), YELLOW, F_MED)
    blit(screen, f"Active sources:  {len(sources)}   "
         f"|   Ambient: {'ON' if ambient_channel and ambient_channel.get_busy() else 'OFF'}",
         (20, hud_y + 30), GRAY_LT, F_SMALL)
    blit(screen, "CLICK: spawn source  |  SPACE: ambient  |  TAB: change sound  |  ESC: quit",
         (20, hud_y + 48), GRAY, F_SMALL)

    # Stereo meter
    pan_x = listener_x / WIDTH
    blit(screen, "L", (WIDTH - 220, hud_y + 8), GRAY_LT, F_SMALL)
    pygame.draw.rect(screen, GRAY,  (WIDTH - 200, hud_y + 12, 180, 10))
    pygame.draw.rect(screen, BLUE,
                     (WIDTH - 200, hud_y + 12, int(180 * pan_x), 10))
    blit(screen, "R", (WIDTH - 16, hud_y + 8), GRAY_LT, F_SMALL)
    blit(screen, f"pan {pan_x:.2f}", (WIDTH - 200, hud_y + 28), GRAY, F_SMALL)

    pygame.display.flip()
