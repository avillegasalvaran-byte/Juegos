import pygame
import math
import random
import json
import os

# --- Configuración Visual ---
WIDTH, HEIGHT = 900, 700
BLACK = (5, 5, 10)
NEON_CYAN = (0, 255, 200)
NEON_MAGENTA = (255, 0, 150)
NEON_RED = (255, 40, 40)
NEON_GOLD = (255, 215, 0)
WHITE = (220, 220, 255)
GRAY = (150, 150, 170)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neo-Nexus: V10.1 - TP Arreglado")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False) 

font_title = pygame.font.SysFont("Consolas", 60, bold=True)
font_main = pygame.font.SysFont("Consolas", 28, bold=True)
font_ui = pygame.font.SysFont("Consolas", 16)

# --- Sistema de Guardado ---
SCORE_FILE = "neonexus_score.json"

def load_high_score():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as file:
                return json.load(file).get("high_score", 1)
        except: return 1
    return 1

def save_high_score(score):
    with open(SCORE_FILE, "w") as file:
        json.dump({"high_score": score}, file)

high_score = load_high_score()

# --- Clases de Soporte ---
class Projectile:
    def __init__(self, pos, angle, is_wave):
        self.pos = pygame.Vector2(pos)
        self.is_wave = is_wave
        speed = 6 if is_wave else 14
        self.vel = pygame.Vector2(speed, 0).rotate(math.degrees(angle))
        self.life = 30 if is_wave else 60

    def update(self):
        self.pos += self.vel
        self.life -= 1

    def draw(self, surface):
        color = NEON_MAGENTA if self.is_wave else WHITE
        if self.is_wave:
            pygame.draw.circle(surface, color, (int(self.pos.x), int(self.pos.y)), 25, 1)
        else:
            pygame.draw.rect(surface, color, (self.pos.x-2, self.pos.y-2, 5, 5))

class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)
        self.stability = 8
        self.max_stability = 8
        self.nexus_charge = 100.0
        self.charge_rate = 0.4
        self.speed_mult = 1.0
        self.is_wave_form = False
        self.mode = "FOCUS"
        self.invulnerable_timer = 0 
        self.tp_effect_timer = 0 
        
        self.transition_max = 120 
        self.combat_tp_charges = 0 

    def handle_input(self):
        keys = pygame.key.get_pressed()
        acc = pygame.Vector2(0, 0)
        speed = 0.5 * self.speed_mult
        
        if keys[pygame.K_LSHIFT] and self.nexus_charge > 0.7:
            self.is_wave_form = True
            self.nexus_charge -= 0.7
            speed *= 1.8
        else:
            self.is_wave_form = False

        if keys[pygame.K_a]: acc.x = -speed
        if keys[pygame.K_d]: acc.x = speed
        if keys[pygame.K_w]: acc.y = -speed
        if keys[pygame.K_s]: acc.y = speed

        self.vel += acc
        self.vel *= 0.92
        self.pos += self.vel
        
        if self.tp_effect_timer > 0: self.tp_effect_timer -= 1

    def draw(self, surface):
        if self.tp_effect_timer > 0:
            radius = (15 - self.tp_effect_timer) * 4
            color = NEON_GOLD if (len(enemies) > 0 and self.combat_tp_charges >= 0) else NEON_CYAN
            pygame.draw.circle(surface, WHITE, (int(self.pos.x), int(self.pos.y)), radius, 2)
            pygame.draw.circle(surface, color, (int(self.pos.x), int(self.pos.y)), radius - 5, 1)

        if self.is_wave_form:
            for i in range(3):
                r = 10 + (pygame.time.get_ticks() * 0.1 + i * 15) % 40
                pygame.draw.circle(surface, (0, 150, 200), (int(self.pos.x), int(self.pos.y)), int(r), 1)
        else:
            for i in range(self.stability):
                t = pygame.time.get_ticks() * 0.005 + (i * (math.pi * 2 / self.stability))
                cx, cy = self.pos.x + math.cos(t)*35, self.pos.y + math.sin(t)*35
                pygame.draw.rect(surface, NEON_CYAN, (cx-2, cy-2, 5, 5))
            
            pygame.draw.circle(surface, WHITE, (int(self.pos.x), int(self.pos.y)), 15, 2)
            if self.invulnerable_timer > 0:
                if (pygame.time.get_ticks() // 100) % 2 == 0: 
                    pygame.draw.circle(surface, NEON_CYAN, (int(self.pos.x), int(self.pos.y)), 22, 2)

class Upgrade:
    def __init__(self, name, desc, effect, rarity, x):
        self.name = name
        self.desc = desc
        self.effect = effect
        self.rarity = rarity
        self.rect = pygame.Rect(x, 300, 230, 120)
    
    def apply(self, p):
        if self.effect == "CHARGE": p.charge_rate += 0.3
        elif self.effect == "SPEED": p.speed_mult += 0.2
        elif self.effect == "STABILITY": p.max_stability += 2; p.stability = p.max_stability
        elif self.effect == "TIME": p.transition_max += 60 
        elif self.effect == "MYTHIC_TP": p.combat_tp_charges += 3

# --- Variables Globales ---
player = Player()
projectiles = []
enemies = []
upgrades = []
cycle = 1
game_state = "MENU"
transition_timer = 120 

def start_cycle(c):
    return [{'pos': pygame.Vector2(random.choice([-50, WIDTH+50]), random.randint(0, HEIGHT)), 'hp': 2 + (c//4)} for _ in range(5 + c*2)]

def draw_crosshair(surface, x, y):
    pygame.draw.circle(surface, NEON_CYAN, (x, y), 8, 1)
    pygame.draw.line(surface, NEON_CYAN, (x-12, y), (x-4, y), 1)
    pygame.draw.line(surface, NEON_CYAN, (x+4, y), (x+12, y), 1)
    pygame.draw.line(surface, NEON_CYAN, (x, y-12), (x, y-4), 1)
    pygame.draw.line(surface, NEON_CYAN, (x, y+4), (x, y+12), 1)

# --- Loop Principal ---
running = True
while running:
    screen.fill(BLACK)
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        
        if event.type == pygame.KEYDOWN:
            if game_state == "MENU" and event.key == pygame.K_RETURN:
                player.reset()
                cycle = 1
                transition_timer = player.transition_max
                enemies = start_cycle(cycle)
                game_state = "PLAYING"
                player.invulnerable_timer = 60 
            elif game_state == "GAMEOVER" and event.key == pygame.K_r:
                game_state = "MENU"
            elif game_state == "PLAYING":
                if event.key == pygame.K_q:
                    player.mode = "WAVE" if player.mode == "FOCUS" else "FOCUS"
                
                # --- NUEVA LÓGICA DE TELETRANSPORTE ARREGLADA ---
                if event.key == pygame.K_SPACE:
                    if len(enemies) == 0:
                        # TP de Transición: 100% Gratis para reposicionarse
                        player.pos = pygame.Vector2(mx, my)
                        player.vel = pygame.Vector2(0, 0)
                        player.tp_effect_timer = 15
                    else:
                        # TP de Combate
                        if player.combat_tp_charges > 0:
                            # Usa carga mítica (Gratis en energía)
                            player.pos = pygame.Vector2(mx, my)
                            player.vel = pygame.Vector2(0, 0)
                            player.combat_tp_charges -= 1
                            player.tp_effect_timer = 15
                        else:
                            # TP de Emergencia (Cuesta 50% de carga)
                            tp_cost = 50
                            if player.nexus_charge >= tp_cost:
                                player.pos = pygame.Vector2(mx, my)
                                player.vel = pygame.Vector2(0, 0)
                                player.nexus_charge -= tp_cost
                                player.tp_effect_timer = 15

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "PLAYING" and not player.is_wave_form:
                cost = 35 if player.mode == "WAVE" else 10
                if player.nexus_charge >= cost:
                    angle = math.atan2(my - player.pos.y, mx - player.pos.x)
                    projectiles.append(Projectile(player.pos, angle, player.mode == "WAVE"))
                    player.nexus_charge -= cost
            elif game_state == "UPGRADING":
                for up in upgrades:
                    if up.rect.collidepoint(event.pos):
                        up.apply(player)
                        cycle += 1
                        enemies = start_cycle(cycle)
                        transition_timer = player.transition_max 
                        game_state = "PLAYING"
                        player.invulnerable_timer = 60 
                        break

    # --- Lógica de Estados ---
    if game_state == "PLAYING":
        player.handle_input()
        if player.invulnerable_timer > 0: player.invulnerable_timer -= 1
            
        if not player.is_wave_form: player.nexus_charge = min(100.0, player.nexus_charge + player.charge_rate)
        player.nexus_charge = max(0.0, player.nexus_charge)
        
        for p in projectiles[:]:
            p.update()
            if p.life <= 0: projectiles.remove(p)
            for e in enemies[:]:
                if p.pos.distance_to(e['pos']) < (30 if p.is_wave else 15):
                    e['hp'] -= 1 if p.is_wave else 1
                    if not p.is_wave and p in projectiles: projectiles.remove(p)
                    if e['hp'] <= 0: enemies.remove(e)

        for e in enemies[:]:
            dir_vec = player.pos - e['pos']
            if dir_vec.length() > 0:
                e['pos'] += dir_vec.normalize() * (1.5 + cycle * 0.2)
            pygame.draw.rect(screen, NEON_RED, (e['pos'].x-10, e['pos'].y-10, 20, 20), 1)
            
            if player.pos.distance_to(e['pos']) < 25:
                if player.invulnerable_timer == 0: 
                    if not player.is_wave_form:
                        player.stability -= 1
                        enemies.remove(e)
                    elif player.nexus_charge < 1:
                        player.stability -= 2
                        enemies.remove(e)
                        
                    if player.stability <= 0:
                        if cycle > high_score: high_score = cycle; save_high_score(high_score)
                        game_state = "GAMEOVER"

        if not enemies:
            if transition_timer > 0:
                transition_timer -= 1
            else:
                game_state = "UPGRADING"
                pool_comun = [
                    {"n": "NEXO ACELERADO", "d": "+ Vel. Recarga", "e": "CHARGE"},
                    {"n": "MOTOR DE FLUJO", "d": "+ Vel. Movimiento", "e": "SPEED"},
                    {"n": "NÚCLEO EXTRA", "d": "+2 Estabilidad Max", "e": "STABILITY"},
                    {"n": "DILATACIÓN TEMP.", "d": "+1s TP en Vacío", "e": "TIME"}
                ]
                seleccion = random.sample(pool_comun, 3)
                upgrades = []
                start_x = WIDTH//2 - (230*3 + 40)//2 
                
                if random.random() < 0.15:
                    upgrades.append(Upgrade("SALTO PARADÓJICO", "+3 TP Gratis en Combate", "MYTHIC_TP", "MYTHIC", start_x))
                else:
                    upgrades.append(Upgrade(seleccion[0]["n"], seleccion[0]["d"], seleccion[0]["e"], "COMMON", start_x))
                
                upgrades.append(Upgrade(seleccion[1]["n"], seleccion[1]["d"], seleccion[1]["e"], "COMMON", start_x + 250))
                upgrades.append(Upgrade(seleccion[2]["n"], seleccion[2]["d"], seleccion[2]["e"], "COMMON", start_x + 500))

    # --- Dibujado de Pantallas ---
    if game_state == "MENU":
        title = font_title.render("NEO-NEXUS", True, NEON_CYAN)
        score_txt = font_main.render(f"RÉCORD ACTUAL: CICLO {high_score}", True, NEON_MAGENTA)
        hint = font_main.render("> PRESIONA ENTER PARA INICIAR <", True, WHITE)
        
        ctrl_title = font_ui.render("--- PANEL DE CONTROL ---", True, GRAY)
        c1 = font_ui.render("[W A S D]    : Mover Nave", True, GRAY)
        c2 = font_ui.render("[CLICK IZQ]  : Disparar Materia", True, GRAY)
        c3 = font_ui.render("[ Q ]        : Cambiar Modo de Disparo", True, GRAY)
        c4 = font_ui.render("[SHIFT IZQ]  : Efecto Túnel (Atravesar enemigos)", True, GRAY)
        c5 = font_ui.render("[ESPACIO]    : TP Vacío (Gratis) | TP Combate (50% o Carga Mítica)", True, GRAY)

        screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))
        screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 220))
        
        start_y = 350
        screen.blit(ctrl_title, (WIDTH//2 - ctrl_title.get_width()//2, start_y))
        screen.blit(c1, (WIDTH//2 - 200, start_y + 40))
        screen.blit(c2, (WIDTH//2 - 200, start_y + 70))
        screen.blit(c3, (WIDTH//2 - 200, start_y + 100))
        screen.blit(c4, (WIDTH//2 - 200, start_y + 130))
        screen.blit(c5, (WIDTH//2 - 200, start_y + 160))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 580))

    elif game_state == "PLAYING" or game_state == "UPGRADING":
        for p in projectiles: p.draw(screen)
        player.draw(screen)
        
        pygame.draw.rect(screen, (30,30,50), (20, HEIGHT-30, 200, 10))
        pygame.draw.rect(screen, NEON_MAGENTA, (20, HEIGHT-30, player.nexus_charge*2, 10))
        estado_txt = "ONDA INTANGIBLE" if player.is_wave_form else ("ONDA DE DISPERSIÓN" if player.mode == "WAVE" else "DISPARO FOCALIZADO")
        screen.blit(font_ui.render(estado_txt, True, NEON_CYAN), (20, 20))
        screen.blit(font_ui.render(f"CARGA: {int(player.nexus_charge)}% | CICLO: {cycle}", True, WHITE), (20, HEIGHT-60))
        
        if player.combat_tp_charges > 0:
            screen.blit(font_main.render(f"CARGAS DE SALTO: {player.combat_tp_charges}", True, NEON_GOLD), (20, HEIGHT-100))

        vacuum = len(enemies) == 0
        if vacuum and game_state == "PLAYING":
            tiempo_restante = transition_timer / 60.0
            msg = font_main.render(f"REPOSICIONAMIENTO TÁCTICO: {tiempo_restante:.1f}s", True, NEON_CYAN)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 100))

        if game_state == "UPGRADING":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,190)); screen.blit(overlay, (0,0))
            titulo = font_main.render("FASE DE RECONFIGURACIÓN", True, NEON_CYAN)
            screen.blit(titulo, (WIDTH//2 - titulo.get_width()//2, 200))
            
            for up in upgrades:
                box_color = NEON_GOLD if up.rarity == "MYTHIC" else NEON_CYAN
                text_color = NEON_GOLD if up.rarity == "MYTHIC" else WHITE
                
                pygame.draw.rect(screen, (20,20,30), up.rect)
                pygame.draw.rect(screen, box_color, up.rect, 2)
                
                if up.rarity == "MYTHIC":
                    screen.blit(font_ui.render("[MÍTICO]", True, NEON_GOLD), (up.rect.x+15, up.rect.y+15))
                    screen.blit(font_ui.render(up.name, True, WHITE), (up.rect.x+15, up.rect.y+40))
                    screen.blit(font_ui.render(up.desc, True, WHITE), (up.rect.x+15, up.rect.y+75))
                else:
                    screen.blit(font_ui.render(up.name, True, text_color), (up.rect.x+15, up.rect.y+35))
                    screen.blit(font_ui.render(up.desc, True, NEON_MAGENTA), (up.rect.x+15, up.rect.y+70))

    elif game_state == "GAMEOVER":
        msg = font_title.render("COLAPSO CUÁNTICO", True, NEON_RED)
        score_msg = font_main.render(f"LLEGASTE AL CICLO: {cycle}", True, NEON_CYAN)
        retry = font_main.render("PRESIONA 'R' PARA REINTENTAR", True, WHITE)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 200))
        screen.blit(score_msg, (WIDTH//2 - score_msg.get_width()//2, 300))
        screen.blit(retry, (WIDTH//2 - retry.get_width()//2, 450))

    draw_crosshair(screen, mx, my)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()