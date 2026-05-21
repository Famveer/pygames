"""
════════════════════════════════════════════════════════════
 MÓDULO 1 — Script 03: Eventos e Input
════════════════════════════════════════════════════════════

 Qué demuestra este script:
   • Visualización en tiempo real de TODOS los eventos
   • Diferencia entre eventos de teclado y mouse
   • Cómo acceder a los datos de cada evento (pos, key, button)
   • Log de eventos con timestamp

 Interactuá con la ventana para ver los eventos:
   • Presioná y soltá teclas
   • Mové y hacé click con el mouse
   • Usá el scroll
   • ESC o X: cerrar

 Ejecutar: python 03_eventos_input.py
════════════════════════════════════════════════════════════
"""

import pygame
import sys
import time

pygame.init()

ANCHO, ALTO = 900, 650
NEGRO    = (0,   0,   0)
BLANCO   = (255, 255, 255)
GRIS     = (60,  60,  60)
GRIS_CLR = (120, 120, 120)
AZUL     = (50,  120, 220)
VERDE    = (50,  200, 100)
AMARILLO = (255, 230, 50)
NARANJA  = (255, 160, 30)
ROJO     = (220, 70,  60)
VIOLETA  = (160, 90,  220)
CYAN     = (50,  200, 220)

# Colores por tipo de evento
COLORES_EVENTO = {
    'QUIT':            ROJO,
    'KEYDOWN':         VERDE,
    'KEYUP':           CYAN,
    'MOUSEBUTTONDOWN': AMARILLO,
    'MOUSEBUTTONUP':   NARANJA,
    'MOUSEMOTION':     AZUL,
    'MOUSEWHEEL':      VIOLETA,
}

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Módulo 1 — Visualizador de Eventos")
clock = pygame.time.Clock()

fuente       = pygame.font.SysFont("monospace", 15)
fuente_chica = pygame.font.SysFont("monospace", 13)
fuente_titulo= pygame.font.SysFont("monospace", 18, bold=True)

# Log de eventos (máx 18 para mostrar en pantalla)
log_eventos = []
MAX_LOG = 18

# Estado del mouse para visualización
mouse_pos    = (0, 0)
mouse_botones= [False, False, False]  # izq, medio, der
teclas_activas = set()

tiempo_inicio = time.time()

def nombre_evento(tipo):
    nombres = {
        pygame.QUIT:            "QUIT",
        pygame.KEYDOWN:         "KEYDOWN",
        pygame.KEYUP:           "KEYUP",
        pygame.MOUSEBUTTONDOWN: "MOUSEBUTTONDOWN",
        pygame.MOUSEBUTTONUP:   "MOUSEBUTTONUP",
        pygame.MOUSEMOTION:     "MOUSEMOTION",
        pygame.MOUSEWHEEL:      "MOUSEWHEEL",
    }
    return nombres.get(tipo, f"EVENTO_{tipo}")

def agregar_log(nombre, detalle, color):
    t = time.time() - tiempo_inicio
    log_eventos.append({
        'tiempo': f"{t:6.2f}s",
        'nombre': nombre,
        'detalle': detalle,
        'color': color,
    })
    if len(log_eventos) > MAX_LOG:
        log_eventos.pop(0)

def texto(surf, txt, pos, color=BLANCO, f=None):
    f = f or fuente
    s = f.render(txt, True, color)
    surf.blit(s, pos)

while True:
    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            agregar_log("QUIT", "Ventana cerrada", ROJO)
            pygame.quit(); sys.exit()

        elif evento.type == pygame.KEYDOWN:
            nombre_tecla = pygame.key.name(evento.key)
            teclas_activas.add(nombre_tecla)
            detalle = f"key='{nombre_tecla}'  mod={evento.mod}"
            agregar_log("KEYDOWN", detalle, VERDE)
            if evento.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        elif evento.type == pygame.KEYUP:
            nombre_tecla = pygame.key.name(evento.key)
            teclas_activas.discard(nombre_tecla)
            agregar_log("KEYUP", f"key='{nombre_tecla}'", CYAN)

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            nombres_boton = {1: 'izquierdo', 2: 'medio', 3: 'derecho',
                            4: 'scroll↑', 5: 'scroll↓'}
            nb = nombres_boton.get(evento.button, str(evento.button))
            agregar_log("MOUSEBUTTONDOWN",
                       f"pos={evento.pos}  botón={nb}({evento.button})", AMARILLO)

        elif evento.type == pygame.MOUSEBUTTONUP:
            agregar_log("MOUSEBUTTONUP",
                       f"pos={evento.pos}  botón={evento.button}", NARANJA)

        elif evento.type == pygame.MOUSEMOTION:
            # Solo logueamos si hubo movimiento significativo
            if abs(evento.rel[0]) > 5 or abs(evento.rel[1]) > 5:
                agregar_log("MOUSEMOTION",
                           f"pos={evento.pos}  rel={evento.rel}", AZUL)

        elif evento.type == pygame.MOUSEWHEEL:
            agregar_log("MOUSEWHEEL",
                       f"x={evento.x}  y={evento.y}", VIOLETA)

    # Update: actualizar estado del mouse
    mouse_pos = pygame.mouse.get_pos()
    mb = pygame.mouse.get_pressed()
    mouse_botones = list(mb)

    # ─── RENDER ───────────────────────────────────────────────
    pantalla.fill(NEGRO)

    # ── Panel izquierdo: Log de eventos ──────────────────────
    ancho_panel = 560
    pygame.draw.rect(pantalla, (12, 12, 12), (0, 0, ancho_panel, ALTO))
    pygame.draw.line(pantalla, GRIS, (ancho_panel, 0), (ancho_panel, ALTO), 1)

    texto(pantalla, "LOG DE EVENTOS", (12, 12), GRIS_CLR, fuente_titulo)
    texto(pantalla, "tiempo   tipo               detalle",
          (12, 38), GRIS, fuente_chica)
    pygame.draw.line(pantalla, GRIS, (12, 55), (ancho_panel - 12, 55), 1)

    for i, ev in enumerate(log_eventos): # 18 eventos historico
        y_ev = 62 + i * 28 # 18 rectangulitos de tamaño 28 px
        color = ev['color']
        # Fondo sutil para la fila
        if i % 2 == 0:
            pygame.draw.rect(pantalla, (20, 20, 20), (4, y_ev - 2, ancho_panel - 8, 24))
        texto(pantalla, ev['tiempo'],  (12,  y_ev), GRIS_CLR, fuente_chica)
        texto(pantalla, ev['nombre'], (85,  y_ev), color, fuente_chica)
        texto(pantalla, ev['detalle'][:52], (270, y_ev), BLANCO, fuente_chica)

    # ── Panel derecho: Estado actual ─────────────────────────
    px = ancho_panel + 12

    texto(pantalla, "ESTADO ACTUAL", (px, 12), GRIS_CLR, fuente_titulo)
    pygame.draw.line(pantalla, GRIS, (px, 40), (ANCHO - 12, 40), 1)

    # Mouse position
    texto(pantalla, "Mouse", (px, 50), GRIS_CLR, fuente)
    texto(pantalla, f"pos: {mouse_pos}", (px, 72), BLANCO, fuente_chica)

    # Visualización del cursor en miniatura
    mini_x = px + 180
    mini_y = 55
    mini_w = 80
    mini_h = 60
    pygame.draw.rect(pantalla, GRIS, (mini_x, mini_y, mini_w, mini_h), 1)
    cx = mini_x + int(mouse_pos[0] / ANCHO * mini_w)
    cy = mini_y + int(mouse_pos[1] / ALTO  * mini_h)
    # no se sobrepase de nuestro rectangulito
    cx = max(mini_x + 2, min(cx, mini_x + mini_w - 2))
    cy = max(mini_y + 2, min(cy, mini_y + mini_h - 2))
    pygame.draw.circle(pantalla, AZUL, (cx, cy), 3)

    # Botones del mouse
    texto(pantalla, "Botones:", (px, 125), GRIS_CLR, fuente_chica)
    nombres_btn = ["Izq (1)", "Medio (2)", "Der (3)"]
    
    # 0, iz
    # 1, medio
    # 2, der
    
    for i, (presionado, nombre) in enumerate(zip(mouse_botones, nombres_btn)):
        color_btn = AMARILLO if presionado else GRIS
        pygame.draw.rect(pantalla, color_btn,
                        (px + i * 95, 143, 88, 28), 0 if presionado else 1)
        texto(pantalla, nombre,
              (px + i * 95 + 6, 150), NEGRO if presionado else color_btn, fuente_chica)

    # Teclas activas
    texto(pantalla, "Teclas presionadas ahora:", (px, 195), GRIS_CLR, fuente)
    if teclas_activas:
        for i, tecla in enumerate(sorted(teclas_activas)):
            bx = px + (i % 3) * 95
            by = 218 + (i // 3) * 34
            pygame.draw.rect(pantalla, VERDE, (bx, by, 86, 26))
            texto(pantalla, tecla[:10], (bx + 5, by + 6), NEGRO, fuente_chica)
    else:
        texto(pantalla, "(ninguna)", (px, 220), GRIS, fuente_chica)

    # Leyenda de colores
    pygame.draw.line(pantalla, GRIS, (px, ALTO - 190), (ANCHO - 12, ALTO - 190), 1)
    texto(pantalla, "Colores por tipo:", (px, ALTO - 180), GRIS_CLR, fuente_chica)
    for i, (nombre_ev, color) in enumerate(COLORES_EVENTO.items()):
        fila = i // 2
        col  = i % 2
        bx = px + col * 155
        by = ALTO - 162 + fila * 22
        pygame.draw.circle(pantalla, color, (bx + 6, by + 7), 5)
        texto(pantalla, nombre_ev, (bx + 15, by), color, fuente_chica)

    # FPS
    fps_real = clock.get_fps()
    texto(pantalla, f"FPS: {fps_real:.0f}", (px, ALTO - 24), GRIS_CLR, fuente_chica)

    pygame.display.flip()
    clock.tick(60)
