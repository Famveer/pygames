"""
════════════════════════════════════════════════════════════
 MODULE 5 — Script 01: Scene Manager
════════════════════════════════════════════════════════════

 What this demonstrates:
   • Scene base class with enter() / update() / draw() / exit()
   • SceneManager that owns the scene stack
   • Four scenes: Menu → Game → Pause → GameOver
   • Pushing / popping scenes (pause overlays the game)
   • Passing data between scenes (final score)

 Controls:
   • Menu:  ENTER to start, ESC to quit
   • Game:  Arrows to move, P to pause, ESC to go back to menu
   • Pause: R to resume, Q to quit to menu
   • GameOver: ENTER to restart, ESC to quit
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import random
import math

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
DARK_BG = (10,  10,  20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Module 5 — Scene Manager")
clock  = pygame.time.Clock()

F_SMALL  = pygame.font.SysFont("monospace", 13)
F_MED    = pygame.font.SysFont("monospace", 18)
F_LARGE  = pygame.font.SysFont("monospace", 28, bold=True)
F_TITLE  = pygame.font.SysFont("monospace", 48, bold=True)

def blit_text(surf, txt, pos, color=WHITE, font=None):
    s = (font or F_MED).render(txt, True, color)
    surf.blit(s, pos)

def blit_centered(surf, txt, y, color=WHITE, font=None):
    s = (font or F_MED).render(txt, True, color)
    surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))


# ═══════════════════════════════════════════════════════════
# SCENE BASE CLASS
# Every scene must implement these four methods.
# ═══════════════════════════════════════════════════════════

class Scene:
    """
    Abstract base class for all scenes.
    The SceneManager calls these methods in order every frame.
    """
    def __init__(self, manager):
        self.manager = manager   # Reference to the SceneManager

    def enter(self):
        """Called once when the scene becomes active."""
        pass

    def exit(self):
        """Called once when the scene is deactivated."""
        pass

    def handle_event(self, event):
        """Process a single pygame event."""
        pass

    def update(self, dt):
        """Update game logic. dt = delta time in seconds."""
        pass

    def draw(self, surface):
        """Draw everything to surface."""
        pass


# ═══════════════════════════════════════════════════════════
# SCENE MANAGER
# Owns a STACK of scenes. The top of the stack is active.
# push() overlays a new scene; pop() returns to the previous.
# ═══════════════════════════════════════════════════════════

class SceneManager:
    def __init__(self):
        self._stack  = []        # Stack of Scene objects
        self.running = True
        self.shared  = {}        # Shared data between scenes (score, etc.)

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def push(self, scene):
        """Push a new scene on top (previous stays in memory)."""
        if self._stack:
            self._stack[-1].exit()
        self._stack.append(scene)
        scene.enter()

    def pop(self):
        """Remove the top scene and return to the previous one."""
        if self._stack:
            self._stack.pop().exit()
        if self._stack:
            self._stack[-1].enter()

    def replace(self, scene):
        """Replace the current scene entirely (no going back)."""
        if self._stack:
            self._stack.pop().exit()
        self._stack.append(scene)
        scene.enter()

    def run(self):
        while self.running and self.current:
            dt = clock.tick(FPS) / 1000.0   # Delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.current.handle_event(event)

            self.current.update(dt)
            self.current.draw(screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ═══════════════════════════════════════════════════════════
# SCENE: MENU
# ═══════════════════════════════════════════════════════════

class MenuScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.t       = 0.0
        self.stars   = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                         random.uniform(0.5, 2.0)) for _ in range(120)]

    def enter(self):
        pygame.display.set_caption("Module 5 — Main Menu")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.manager.push(GameScene(self.manager))
            if event.key == pygame.K_ESCAPE:
                self.manager.running = False

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        surface.fill(DARK_BG)

        # Scrolling starfield
        for sx, sy, speed in self.stars:
            brightness = int(80 + 60 * math.sin(self.t * speed))
            pygame.draw.circle(surface, (brightness,) * 3, (sx, int(sy)), 1)

        # Title pulse
        pulse = abs(math.sin(self.t * 1.5))
        color = (int(50 + 200 * pulse), int(120 + 100 * pulse), 220)
        blit_centered(surface, "🎮  PYGAME COURSE", 140, color, F_TITLE)
        blit_centered(surface, "Scenes & State Management", 210, GRAY_LT, F_MED)

        # Menu options
        blit_centered(surface, "ENTER  →  Start Game",  320, GREEN,    F_LARGE)
        blit_centered(surface, "ESC    →  Quit",         380, RED,      F_MED)

        # Diagram of scene stack
        self._draw_stack_diagram(surface)

        # Footer
        blit_centered(surface, "Current scene: MenuScene   (top of stack)", HEIGHT - 30,
                      GRAY, F_SMALL)

    def _draw_stack_diagram(self, surface):
        dx, dy = 60, 440
        blit_text(surface, "Scene Stack:", (dx, dy - 20), GRAY_LT, F_SMALL)
        boxes = [("MenuScene", BLUE, True)]
        for i, (label, color, active) in enumerate(reversed(boxes)):
            bx = dx + i * 160
            pygame.draw.rect(surface, color, (bx, dy, 140, 36), 0 if active else 2)
            blit_text(surface, label, (bx + 8, dy + 10),
                      BLACK if active else color, F_SMALL)
        blit_text(surface, "← active", (dx + 148, dy + 10), GRAY_LT, F_SMALL)


# ═══════════════════════════════════════════════════════════
# SCENE: GAME
# ═══════════════════════════════════════════════════════════

class GameScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.reset()

    def reset(self):
        self.player_x    = WIDTH  // 2
        self.player_y    = HEIGHT // 2
        self.speed       = 200    # px per second
        self.score       = 0
        self.t           = 0.0
        self.enemies     = [self._new_enemy() for _ in range(5)]
        self.items       = [self._new_item()  for _ in range(4)]
        self.flash_timer = 0.0

    def _new_enemy(self):
        side = random.randint(0, 3)
        if side == 0: return [random.randint(0, WIDTH), -30, random.uniform(60, 120)]
        if side == 1: return [WIDTH + 30, random.randint(0, HEIGHT), random.uniform(60, 120)]
        if side == 2: return [random.randint(0, WIDTH), HEIGHT + 30, random.uniform(60, 120)]
        return [-30, random.randint(0, HEIGHT), random.uniform(60, 120)]

    def _new_item(self):
        return [random.randint(40, WIDTH - 40), random.randint(40, HEIGHT - 80)]

    def enter(self):
        pygame.display.set_caption("Module 5 — Game")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.manager.push(PauseScene(self.manager))   # PUSH pause on top
            if event.key == pygame.K_ESCAPE:
                self.manager.replace(MenuScene(self.manager))

    def update(self, dt):
        self.t += dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]:  dx = -1
        if keys[pygame.K_RIGHT]: dx =  1
        if keys[pygame.K_UP]:    dy = -1
        if keys[pygame.K_DOWN]:  dy =  1
        # Normalize diagonal
        if dx and dy:
            dx *= 0.707; dy *= 0.707
        self.player_x = max(20, min(self.player_x + dx * self.speed * dt, WIDTH  - 20))
        self.player_y = max(20, min(self.player_y + dy * self.speed * dt, HEIGHT - 80))

        # Move enemies toward player
        for e in self.enemies:
            angle = math.atan2(self.player_y - e[1], self.player_x - e[0])
            e[0] += math.cos(angle) * e[2] * dt
            e[1] += math.sin(angle) * e[2] * dt
            dist  = math.hypot(self.player_x - e[0], self.player_y - e[1])
            if dist < 22:
                self.manager.shared['score'] = self.score
                self.manager.replace(GameOverScene(self.manager))
                return

        # Check item pickups
        for item in self.items[:]:
            if math.hypot(self.player_x - item[0], self.player_y - item[1]) < 24:
                self.items.remove(item)
                self.items.append(self._new_item())
                self.score      += 10
                self.flash_timer = 0.3

    def draw(self, surface):
        surface.fill(DARK_BG)

        # Grid
        for gx in range(0, WIDTH, 80):
            pygame.draw.line(surface, (18, 18, 28), (gx, 0), (gx, HEIGHT - 60))
        for gy in range(0, HEIGHT - 60, 80):
            pygame.draw.line(surface, (18, 18, 28), (0, gy), (WIDTH, gy))

        # Items (stars)
        for item in self.items:
            pulse = abs(math.sin(self.t * 3 + item[0]))
            r     = int(6 + 4 * pulse)
            pygame.draw.circle(surface, YELLOW, (int(item[0]), int(item[1])), r)
            pygame.draw.circle(surface, WHITE,  (int(item[0]), int(item[1])), r, 1)

        # Enemies
        for e in self.enemies:
            pygame.draw.circle(surface, RED,   (int(e[0]), int(e[1])), 14)
            pygame.draw.circle(surface, WHITE, (int(e[0]), int(e[1])), 14, 1)

        # Player
        px, py = int(self.player_x), int(self.player_y)
        color_p = WHITE if self.flash_timer > 0 else BLUE
        pygame.draw.polygon(surface, color_p,
                            [(px, py - 18), (px + 12, py + 12),
                             (px, py + 6),  (px - 12, py + 12)])
        pygame.draw.polygon(surface, WHITE,
                            [(px, py - 18), (px + 12, py + 12),
                             (px, py + 6),  (px - 12, py + 12)], 1)

        # HUD
        panel_y = HEIGHT - 60
        pygame.draw.rect(surface, (12, 12, 20), (0, panel_y, WIDTH, 60))
        pygame.draw.line(surface, GRAY, (0, panel_y), (WIDTH, panel_y), 1)
        blit_text(surface, f"Score: {self.score}", (20, panel_y + 10), YELLOW, F_LARGE)
        blit_text(surface, "Arrows: move  |  P: pause  |  ESC: menu",
                  (320, panel_y + 18), GRAY, F_SMALL)
        blit_text(surface, "Current scene: GameScene", (680, panel_y + 18), BLUE, F_SMALL)

    def _draw_stack_diagram(self, surface):
        pass


# ═══════════════════════════════════════════════════════════
# SCENE: PAUSE  (pushed ON TOP of GameScene)
# ═══════════════════════════════════════════════════════════

class PauseScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        # Snapshot of game screen for the blurred background
        self.bg = screen.copy()

    def enter(self):
        pygame.display.set_caption("Module 5 — Paused")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_p, pygame.K_r):
                self.manager.pop()   # POP pause → GameScene is revealed
            if event.key == pygame.K_q:
                self.manager.replace(MenuScene(self.manager))

    def update(self, dt):
        pass   # Game logic is FROZEN — GameScene.update() is not called

    def draw(self, surface):
        # Draw the frozen game behind the overlay
        surface.blit(self.bg, (0, 0))

        # Dark semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Pause box
        box_w, box_h = 420, 220
        bx = WIDTH  // 2 - box_w // 2
        by = HEIGHT // 2 - box_h // 2
        pygame.draw.rect(surface, (20, 20, 40), (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(surface, PURPLE,       (bx, by, box_w, box_h), 2, border_radius=12)

        blit_centered(surface, "⏸  PAUSED",           by + 30,  PURPLE, F_TITLE)
        blit_centered(surface, "R  →  Resume",         by + 110, GREEN,  F_LARGE)
        blit_centered(surface, "Q  →  Quit to Menu",   by + 160, RED,    F_MED)

        blit_centered(surface, "Stack: [MenuScene | GameScene | PauseScene ← active]",
                      HEIGHT - 25, GRAY, F_SMALL)


# ═══════════════════════════════════════════════════════════
# SCENE: GAME OVER
# ═══════════════════════════════════════════════════════════

class GameOverScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.t     = 0.0
        self.score = manager.shared.get('score', 0)

    def enter(self):
        pygame.display.set_caption("Module 5 — Game Over")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.manager.replace(GameScene(self.manager))
            if event.key == pygame.K_ESCAPE:
                self.manager.replace(MenuScene(self.manager))

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        surface.fill(DARK_BG)

        pulse = abs(math.sin(self.t * 2))
        color = (int(180 + 75 * pulse), int(40 + 40 * pulse), int(40 + 30 * pulse))
        blit_centered(surface, "GAME OVER",         200, color,  F_TITLE)
        blit_centered(surface, f"Score: {self.score}", 290, YELLOW, F_LARGE)

        blit_centered(surface, "ENTER  →  Play Again", 390, GREEN, F_LARGE)
        blit_centered(surface, "ESC    →  Main Menu",  450, GRAY_LT, F_MED)

        # Show data passed between scenes
        blit_centered(surface, f"Data passed via manager.shared['score'] = {self.score}",
                      HEIGHT - 50, GRAY, F_SMALL)
        blit_centered(surface, "Current scene: GameOverScene   (replaced GameScene)",
                      HEIGHT - 28, RED, F_SMALL)


# ── RUN ───────────────────────────────────────────────────
manager = SceneManager()
manager.push(MenuScene(manager))
manager.run()
