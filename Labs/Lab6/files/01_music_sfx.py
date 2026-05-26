"""
════════════════════════════════════════════════════════════
 MODULE 6 — Script 03: Music & Sound Effects
════════════════════════════════════════════════════════════

 What this demonstrates:
   • pygame.mixer initialization and configuration
   • Generating sounds programmatically (no .wav files needed)
   • pygame.mixer.music for background music (streaming)
   • pygame.mixer.Sound for short sound effects
   • Volume control for music and SFX independently
   • Looping, stopping, pausing, and fading music
   • Playing sounds on specific channels

 NOTE: This script generates all audio with math — no files needed.

 Controls:
   • M:       toggle music on/off
   • P:       pause / unpause music
   • F:       fade out music (2 seconds)
   • UP/DOWN: music volume
   • 1-5:     play sound effect
   • Q/E:     SFX volume down/up
   • ESC:     quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import math
import random
import struct
import wave
import io

pygame.mixer.pre_init(44100, -16, 1, 512)   # freq, bit depth, mono, buffer
pygame.init()

WIDTH, HEIGHT = 900, 620
FPS = 60

BLACK    = (0,   0,   0)
WHITE    = (255, 255, 255)
GRAY     = (60,  60,  60)
GRAY_LT  = (150, 150, 150)
BLUE     = (50,  120, 220)
GREEN    = (50,  200, 100)
RED      = (220, 80,  70)
YELLOW   = (255, 220, 50)
ORANGE   = (255, 160, 30)
PURPLE   = (160, 90,  220)
CYAN     = (50,  200, 220)
DARK_BG  = (10,  10,  20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 6 — Music & Sound Effects")
clock  = pygame.time.Clock()

F_SMALL = pygame.font.SysFont("monospace", 13)
F_MED   = pygame.font.SysFont("monospace", 16)
F_LARGE = pygame.font.SysFont("monospace", 22, bold=True)

def blit(surf, txt, pos, color=WHITE, font=None):
    s = (font or F_MED).render(txt, True, color)
    surf.blit(s, pos)

def blit_c(surf, txt, y, color=WHITE, font=None):
    s = (font or F_MED).render(txt, True, color)
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))


# ══════════════════════════════════════════════════════════
# AUDIO GENERATION — create sounds purely with math
# In a real game: pygame.mixer.music.load("bg.mp3")
#                 sound = pygame.mixer.Sound("sfx/jump.wav")
# ══════════════════════════════════════════════════════════

SAMPLE_RATE = 44100

def generate_samples(samples):
    """Convert float samples [-1, 1] to 16-bit PCM bytes."""
    clamped = [max(-1.0, min(1.0, s)) for s in samples]
    data    = struct.pack(f"{len(clamped)}h",
                         *[int(s * 32767) for s in clamped])
    return data

def sine_wave(freq, duration, volume=0.5, sr=SAMPLE_RATE):
    n = int(sr * duration)
    return [volume * math.sin(2 * math.pi * freq * i / sr) for i in range(n)]

def make_sound(samples):
    """Wrap raw PCM bytes in a pygame.mixer.Sound."""
    data  = generate_samples(samples)
    sound = pygame.mixer.Sound(buffer=data)
    return sound

def make_jump_sfx():
    """Rising frequency sweep."""
    n   = int(SAMPLE_RATE * 0.2)
    out = []
    for i in range(n):
        t    = i / SAMPLE_RATE
        freq = 300 + 800 * (i / n)
        env  = 1.0 - i / n        # Fade out
        out.append(0.4 * env * math.sin(2 * math.pi * freq * t))
    return make_sound(out)

def make_collect_sfx():
    """Two-tone chime."""
    s1 = sine_wave(880, 0.08, 0.4)
    s2 = sine_wave(1320, 0.12, 0.4)
    n  = max(len(s1), len(s2))
    return make_sound([
        (s1[i] if i < len(s1) else 0.0) + (s2[i] if i < len(s2) else 0.0)
        for i in range(n)
    ])

def make_hit_sfx():
    """Noise burst with fast decay."""
    n   = int(SAMPLE_RATE * 0.15)
    out = []
    for i in range(n):
        env = (1 - i/n) ** 2
        out.append(0.5 * env * (random.random() * 2 - 1))
    return make_sound(out)

def make_shoot_sfx():
    """Short descending beep."""
    n   = int(SAMPLE_RATE * 0.12)
    out = []
    for i in range(n):
        t    = i / SAMPLE_RATE
        freq = 600 - 400 * (i / n)
        env  = (1 - i/n) ** 1.5
        out.append(0.35 * env * math.sin(2 * math.pi * freq * t))
    return make_sound(out)

def make_powerup_sfx():
    """Ascending arpeggio."""
    notes = [261, 329, 392, 523]
    out   = []
    for note in notes:
        n_samp = int(SAMPLE_RATE * 0.1)
        for i in range(n_samp):
            env = 1 - i / n_samp
            out.append(0.4 * env * math.sin(2 * math.pi * note * i / SAMPLE_RATE))
    return make_sound(out)

def make_music_loop():
    """Simple chiptune-style loop (2-second, 4/4 beat)."""
    dur    = 2.0
    n      = int(SAMPLE_RATE * dur)
    melody = [262, 294, 330, 349, 392, 349, 330, 294]  # C major scale
    bpm    = 120
    spb    = 60 / bpm  # seconds per beat
    out    = [0.0] * n

    for beat_i, note in enumerate(melody):
        start  = int(beat_i * spb / 2 * SAMPLE_RATE)
        length = int(spb / 2 * SAMPLE_RATE * 0.8)
        for i in range(length):
            if start + i >= n:
                break
            env        = 1 - i / length
            sample     = 0.25 * env * math.sin(2 * math.pi * note * i / SAMPLE_RATE)
            out[start + i] += sample

    # Bass drum pattern (every beat)
    for beat_i in range(4):
        start  = int(beat_i * spb * SAMPLE_RATE)
        length = int(0.1 * SAMPLE_RATE)
        for i in range(length):
            if start + i >= n:
                break
            env = (1 - i / length) ** 3
            out[start + i] += 0.3 * env * (random.random() * 2 - 1)

    return make_sound(out)

# Build all sounds
print("Generating audio... (first launch may take a moment)")
SFX = {
    "jump":    make_jump_sfx(),
    "collect": make_collect_sfx(),
    "hit":     make_hit_sfx(),
    "shoot":   make_shoot_sfx(),
    "powerup": make_powerup_sfx(),
}
MUSIC_SOUND = make_music_loop()
print("Audio ready.")


# ── CHANNELS ──────────────────────────────────────────────
# pygame.mixer has N channels (default 8).
# Sound effects play on any free channel automatically.
# You can reserve channels for specific categories.

pygame.mixer.set_num_channels(8)
CHANNEL_SFX   = pygame.mixer.Channel(0)
CHANNEL_VOICE = pygame.mixer.Channel(1)
# Channels 2-7 used automatically by .play()

# "Background music" via looping the music Sound
music_channel  = pygame.mixer.Channel(7)
music_channel.play(MUSIC_SOUND, loops=-1)   # -1 = infinite loop

# Volume state
music_vol = 0.5
sfx_vol   = 0.8
music_channel.set_volume(music_vol)
for sfx in SFX.values():
    sfx.set_volume(sfx_vol)

music_on    = True
music_paused= False

# SFX labels
SFX_KEYS = [
    ("1", "jump",    "Rising sweep",        BLUE),
    ("2", "collect", "Two-tone chime",       YELLOW),
    ("3", "hit",     "Noise burst",          RED),
    ("4", "shoot",   "Descending beep",      CYAN),
    ("5", "powerup", "Ascending arpeggio",   GREEN),
]

# VU meter history
vu_history = [0.0] * 60
t_global   = 0.0
flash_sfx  = {}   # sfx_name → timer


while True:
    dt = clock.tick(FPS) / 1000.0
    t_global += dt

    for name in list(flash_sfx):
        flash_sfx[name] -= dt
        if flash_sfx[name] <= 0:
            del flash_sfx[name]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            # Music controls
            if event.key == pygame.K_m:
                music_on = not music_on
                if music_on:
                    music_channel.play(MUSIC_SOUND, loops=-1)
                else:
                    music_channel.stop()

            if event.key == pygame.K_p:
                if music_paused:
                    music_channel.unpause()
                else:
                    music_channel.pause()
                music_paused = not music_paused

            if event.key == pygame.K_f:
                music_channel.fadeout(2000)   # 2000 ms fade
                music_on = False

            if event.key == pygame.K_UP:
                music_vol = min(1.0, music_vol + 0.1)
                music_channel.set_volume(music_vol)

            if event.key == pygame.K_DOWN:
                music_vol = max(0.0, music_vol - 0.1)
                music_channel.set_volume(music_vol)

            if event.key == pygame.K_q:
                sfx_vol = max(0.0, sfx_vol - 0.1)
                for sfx in SFX.values(): sfx.set_volume(sfx_vol)

            if event.key == pygame.K_e:
                sfx_vol = min(1.0, sfx_vol + 0.1)
                for sfx in SFX.values(): sfx.set_volume(sfx_vol)

            # SFX triggers
            for key_str, name, _, _ in SFX_KEYS:
                if event.key == getattr(pygame, f"K_{key_str}"):
                    SFX[name].play()
                    flash_sfx[name] = 0.3

    # ── RENDER ────────────────────────────────────────────
    screen.fill(DARK_BG)

    # Animated waveform (simulated)
    wave_y = HEIGHT // 2 - 40
    pts    = []
    for xi in range(WIDTH):
        base  = math.sin(xi * 0.04 + t_global * 3) * 0.4
        harm  = math.sin(xi * 0.09 + t_global * 5) * 0.2
        amp   = music_vol if music_on and not music_paused else 0.05
        y     = wave_y + int((base + harm) * 40 * amp)
        pts.append((xi, y))
    if len(pts) > 1:
        pygame.draw.lines(screen, (40, 100, 180), False, pts, 1)

    # Title
    status = "PLAYING" if music_on and not music_paused else ("PAUSED" if music_paused else "STOPPED")
    col_st = GREEN if status == "PLAYING" else (YELLOW if status == "PAUSED" else RED)
    blit_c(screen, "🔊  Module 6 — Music & Sound Effects", 20, WHITE, F_LARGE)

    # ── Music panel ───────────────────────────────────────
    my = 70
    pygame.draw.rect(screen, (15, 20, 15), (20, my, WIDTH - 40, 120), border_radius=8)
    pygame.draw.rect(screen, GREEN,        (20, my, WIDTH - 40, 120), 1, border_radius=8)

    blit(screen, "MUSIC (channel 7 — looping)", (36, my + 10), GREEN, F_LARGE)
    blit(screen, f"Status:  {status}", (36, my + 40), col_st, F_MED)
    blit(screen, f"Volume:  {music_vol:.1f}", (36, my + 60), WHITE, F_MED)

    # Volume bar
    bw = int(music_vol * 300)
    pygame.draw.rect(screen, GRAY,  (280, my + 62, 300, 14))
    pygame.draw.rect(screen, GREEN, (280, my + 62, bw,  14))

    blit(screen, "M: toggle  |  P: pause  |  F: fadeout  |  ↑↓: volume",
         (36, my + 84), GRAY_LT, F_SMALL)

    # ── SFX panel ─────────────────────────────────────────
    sy = 210
    pygame.draw.rect(screen, (15, 15, 22), (20, sy, WIDTH - 40, 250), border_radius=8)
    pygame.draw.rect(screen, BLUE,         (20, sy, WIDTH - 40, 250), 1, border_radius=8)

    blit(screen, "SOUND EFFECTS", (36, sy + 10), BLUE, F_LARGE)
    blit(screen, f"SFX Volume: {sfx_vol:.1f}   (Q/E to adjust)",
         (36, sy + 40), GRAY_LT, F_SMALL)

    sfx_bar_w = int(sfx_vol * 200)
    pygame.draw.rect(screen, GRAY, (240, sy + 42, 200, 10))
    pygame.draw.rect(screen, BLUE, (240, sy + 42, sfx_bar_w, 10))

    for i, (key_str, name, desc, color) in enumerate(SFX_KEYS):
        iy     = sy + 70 + i * 36
        active = name in flash_sfx
        bg_col = color if active else (25, 25, 35)
        pygame.draw.rect(screen, bg_col,  (36, iy, WIDTH - 76, 30), border_radius=6)
        pygame.draw.rect(screen, color,   (36, iy, WIDTH - 76, 30), 1 if not active else 0, border_radius=6)
        label_col = BLACK if active else WHITE
        blit(screen, f"[{key_str}]  {name:<10}  —  {desc}", (50, iy + 7),
             label_col if active else color, F_MED)

    # ── Channel inspector ─────────────────────────────────
    cy2 = 480
    pygame.draw.rect(screen, (18, 12, 20), (20, cy2, WIDTH - 40, 100), border_radius=8)
    pygame.draw.rect(screen, PURPLE,       (20, cy2, WIDTH - 40, 100), 1, border_radius=8)
    blit(screen, "CHANNEL INSPECTOR", (36, cy2 + 10), PURPLE, F_MED)

    for ch_i in range(8):
        ch    = pygame.mixer.Channel(ch_i)
        busy  = ch.get_busy()
        col   = GREEN if busy else GRAY
        cx    = 36 + ch_i * 106
        pygame.draw.rect(screen, col, (cx, cy2 + 38, 90, 22), 0 if busy else 1, border_radius=4)
        label = f"ch{ch_i}" + (" ▶" if busy else "")
        blit(screen, label, (cx + 6, cy2 + 42), BLACK if busy else GRAY, F_SMALL)

    blit(screen, "Each sound plays on a free channel automatically. "
         "Ch7 reserved for music.",
         (36, cy2 + 72), GRAY, F_SMALL)

    pygame.display.flip()
