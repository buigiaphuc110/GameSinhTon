import pygame
import sys
import os
import random
import math
from player import Player
import weapon  # <-- KẾT NỐI VỚI HỆ THỐNG WEAPON
import special # <-- THÊM DÒNG NÀY ĐỂ KẾT NỐI VỚI HỆ THỐNG KỸ NĂNG (SPECIAL)

# --- CONSTANTS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60

# --- HELPERS ---
def is_on_screen(x, y, camera_x, camera_y, width, height, buffer=200):
    return (camera_x - buffer <= x <= camera_x + width + buffer) and \
           (camera_y - buffer <= y <= camera_y + height + buffer)

def get_valid_spawn_pos(camera_x, camera_y, width, height, player_x, player_y, existing_entities, existing_lavas, min_player_dist=400, min_entity_dist=250):
    """
    Tìm vị trí sinh ra vật thể mới, đảm bảo khoảng cách an toàn tuyệt đối 
    để không bị đè lên người chơi, lava và các vật thể đã tồn tại.
    """
    for _ in range(100): # Tăng số lần thử nghiệm để dễ tìm vị trí trống hơn
        x = random.randint(camera_x - 100, camera_x + width + 100)
        y = random.randint(camera_y - 100, camera_y + height + 100)
        
        # 1. Tránh xa người chơi
        if math.hypot(x - player_x, y - player_y) < min_player_dist:
            continue
            
        # 2. Tránh đè lên các Entity khác (skull, bone, driedtree, magma)
        overlap = False
        for ent in existing_entities:
            # Khoảng cách giữa 2 tâm vật thể phải lớn hơn min_entity_dist
            if math.hypot(x - ent.x, y - ent.y) < min_entity_dist:
                overlap = True
                break
        if overlap: continue
        
        # 3. Tránh đè lên Hồ Lava
        for lava in existing_lavas:
            # Cộng thêm radius của lava để đảm bảo an toàn tuyệt đối
            if math.hypot(x - lava.x, y - lava.y) < (min_entity_dist + lava.radius):
                overlap = True
                break
                
        if not overlap:
            return x, y
            
    # Fallback dự phòng nếu map lấp đầy không tìm được góc trống
    return player_x + random.choice([-600, 600]), player_y + random.choice([-600, 600])

def draw_text_with_shadow(text, font, color, surface, x, y):
    shadow_obj = font.render(text, True, BLACK)
    shadow_rect = shadow_obj.get_rect(center=(x + 3, y + 3))
    surface.blit(shadow_obj, shadow_rect)
    
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)

def draw_health_bar(surface, x, y, health, max_health, font):
    total_width, bar_height, tag_width = 180, 22, 34
    
    # Background & Borders
    pygame.draw.rect(surface, (25, 25, 25), (x + 3, y + 3, total_width, bar_height))
    pygame.draw.rect(surface, BLACK, (x, y, total_width, bar_height), width=2)
    pygame.draw.rect(surface, (40, 40, 45), (x + 2, y + 2, total_width - 4, bar_height - 4))
    
    # HP Tag
    pygame.draw.rect(surface, (170, 35, 35), (x + 2, y + 2, tag_width, bar_height - 4))
    pygame.draw.rect(surface, BLACK, (x + 2 + tag_width, y, 2, bar_height))
    hp_label = font.render("HP", True, WHITE)
    hp_label_rect = hp_label.get_rect(center=(x + 2 + tag_width // 2, y + bar_height // 2))
    surface.blit(hp_label, hp_label_rect)
    
    # Gauge
    gauge_x = x + 2 + tag_width + 2
    gauge_width = total_width - tag_width - 6
    gauge_height = bar_height - 4
    pygame.draw.rect(surface, (75, 20, 20), (gauge_x, y + 2, gauge_width, gauge_height))
    
    if health > 0:
        health_ratio = max(0.0, min(1.0, health / max_health))
        current_gauge_w = int(gauge_width * health_ratio)
        
        if health_ratio > 0.5: main_color, light_color = (45, 200, 45), (140, 245, 140)
        elif health_ratio > 0.2: main_color, light_color = (230, 165, 30), (255, 225, 130)
        else: main_color, light_color = (215, 35, 35), (255, 130, 130)
            
        pygame.draw.rect(surface, main_color, (gauge_x, y + 2, current_gauge_w, gauge_height))
        pygame.draw.rect(surface, light_color, (gauge_x, y + 2, current_gauge_w, 2))
        
        num_segments = 4
        for i in range(1, num_segments):
            seg_x = gauge_x + int((gauge_width / num_segments) * i)
            if seg_x < gauge_x + current_gauge_w:
                pygame.draw.line(surface, BLACK, (seg_x, y + 2), (seg_x, y + 1 + gauge_height), 1)
                
    # Status Text
    stat_str = f"{int(health)}/{max_health}"
    stat_text = font.render(stat_str, True, WHITE)
    stat_shadow = font.render(stat_str, True, BLACK)
    stat_x = x + total_width + 10
    stat_y = y + (bar_height // 2) - (stat_text.get_height() // 2)
    surface.blit(stat_shadow, (stat_x + 2, stat_y + 2))
    surface.blit(stat_text, (stat_x, stat_y))

# --- ENTITY CLASSES ---
class DangerExplosion:
    def __init__(self, x, y, alarm_img, explosion_frames):
        self.x, self.y = x, y
        self.alarm_img = alarm_img
        self.frames = explosion_frames
        
        self.state = "WARNING"
        self.start_timer = pygame.time.get_ticks()
        self.warning_duration = 1500
        
        self.frame_index = 0
        self.frame_rate = 50 
        self.last_frame_time = pygame.time.get_ticks()
        
        self.has_dealt_damage = False
        self.hitbox_radius = 130 

    def update(self, player, width, height, mode_name):
        current_time = pygame.time.get_ticks()
        if self.state == "WARNING":
            if current_time - self.start_timer > self.warning_duration:
                self.state = "EXPLODING"
                self.last_frame_time = current_time
        elif self.state == "EXPLODING":
            if current_time - self.last_frame_time > self.frame_rate:
                self.frame_index += 1
                self.last_frame_time = current_time
                
                if self.frame_index >= len(self.frames):
                    self.state = "DONE"
                    return
                    
            if self.frame_index == 3 and not self.has_dealt_damage:
                dist = math.hypot(player.x - self.x, player.y - self.y)
                if dist < self.hitbox_radius + player.radius:
                    player.take_damage_and_knockback(20, self.x, self.y, 25, width, height, mode_name)
                    self.has_dealt_damage = True

    def draw(self, screen, camera_x=0, camera_y=0):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        if self.state == "WARNING":
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                rect = self.alarm_img.get_rect(center=(draw_x, draw_y))
                screen.blit(self.alarm_img, rect)
        elif self.state == "EXPLODING":
            if self.frame_index < len(self.frames):
                img = self.frames[self.frame_index]
                rect = img.get_rect(center=(draw_x, draw_y))
                screen.blit(img, rect)

class LavaPool:
    def __init__(self, x, y, lava_img, shadow_image=None):
        self.x, self.y = x, y
        self.image = lava_img
        self.shadow_image = shadow_image
        self.state = "ACTIVE"
        self.radius = int(110 / 2.25) 

    def update(self, camera_x, camera_y, width, height):
        if not is_on_screen(self.x, self.y, camera_x, camera_y, width, height, buffer=200):
            self.state = "DONE"

    def draw_shadow(self, screen, camera_x, camera_y):
        if self.shadow_image:
            shadow_rect = self.shadow_image.get_rect(center=(int(self.x - camera_x + 2), int(self.y - camera_y + 4)))
            screen.blit(self.shadow_image, shadow_rect)

    def draw(self, screen, camera_x, camera_y):
        rect = self.image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        screen.blit(self.image, rect)

class EndlessEntity:
    def __init__(self, x, y, image, type_name, shadow_image=None):
        self.x, self.y = x, y
        self.type_name = type_name
        self.image = image
        self.shadow_image = shadow_image
        self.rect = self.image.get_rect(center=(x, y))
        self.radius = max(self.rect.width, self.rect.height) // 2
        self.state = "ACTIVE"

    def update(self, camera_x, camera_y, width, height):
        if not is_on_screen(self.x, self.y, camera_x, camera_y, width, height, buffer=200):
            self.state = "DONE"

    def draw_shadow(self, screen, camera_x, camera_y):
        if self.shadow_image:
            draw_img = self.shadow_image
            # Hiệu ứng mờ nhấp nháy cho DriedTree xung quanh alpha 20
            if self.type_name == 'driedtree':
                alpha_val = int(20 + 2 * math.sin(pygame.time.get_ticks() / 200.0))
                alpha_val = max(0, min(255, alpha_val))
                draw_img = self.shadow_image.copy()
                draw_img.fill((255, 255, 255, alpha_val), special_flags=pygame.BLEND_RGBA_MULT)

            shadow_rect = draw_img.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y + self.rect.height//3)))
            screen.blit(draw_img, shadow_rect)

    def draw(self, screen, camera_x, camera_y):
        rect = self.image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        screen.blit(self.image, rect)

class EnemyNor:
    def __init__(self, x, y, frames):
        self.x, self.y = x, y
        self.frames = frames
        self.frame_index = 0
        self.frame_rate = 100 
        self.last_frame_time = pygame.time.get_ticks()
        
        self.speed = 25 
        self.radius = 25 
        self.damage_cooldown = 1000 
        self.last_damage_time = 0

    def update(self, player, dt, width, height, mode_name):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_time > self.frame_rate and self.frames:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_frame_time = current_time

        if dist < self.radius + player.radius:
            if current_time - self.last_damage_time > self.damage_cooldown:
                if hasattr(player, 'take_damage_and_knockback'):
                    player.take_damage_and_knockback(5, self.x, self.y, 10, width, height, mode_name)
                else:
                    player.health -= 5
                self.last_damage_time = current_time

    def draw(self, screen, camera_x, camera_y):
        if not self.frames: return
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        img = self.frames[self.frame_index]
        rect = img.get_rect(center=(draw_x, draw_y))
        screen.blit(img, rect)

# --- ASSET LOADING ---
def load_game_entities(game_assets):
    configs = {
        'dirt':  {'path': 'entity/dirt.png', 'scale': 3.7375, 'fb_size': (13,13), 'fb_draw': lambda s: pygame.draw.circle(s, (110,75,45), (6,6), 6), 'shadow_scale': (0.7, 0.25), 'shadow_alpha': 60},
        'rock':  {'path': 'entity/rock.png', 'scale': 3.7375 / 1.5, 'fb_size': (19,19), 'fb_draw': lambda s: pygame.draw.circle(s, (130,130,130), (9,9), 9), 'shadow_scale': (0.55, 0.2), 'shadow_alpha': 15},
        'tree':  {'path': 'entity/tree.png', 'scale': 3.7375 / (1.5/1.3), 'fb_size': (22,22), 'fb_draw': lambda s: pygame.draw.circle(s, (34,139,34), (11,11), 11), 'shadow_scale': (0.7, 0.25), 'shadow_alpha': 25},
        'grass': {'path': 'entity/grass.png', 'scale': 3.5 / 2.2, 'fb_size': (35,35), 'fb_draw': lambda s: pygame.draw.ellipse(s, (35,140,35,178), (2,2,31,33)), 'shadow_scale': (0.65, 0.2), 'shadow_alpha': 10}
    }
    
    for key, cfg in configs.items():
        if key not in game_assets:
            if os.path.exists(cfg['path']):
                img = pygame.image.load(cfg['path']).convert_alpha()
                w, h = max(1, int(img.get_width() / cfg['scale'])), max(1, int(img.get_height() / cfg['scale']))
                game_assets[key] = pygame.transform.scale(img, (w, h))
                if key == 'grass': game_assets[key].set_alpha(178)
            else:
                dummy = pygame.Surface(cfg['fb_size'], pygame.SRCALPHA)
                cfg['fb_draw'](dummy)
                game_assets[key] = dummy
            
            w, h = game_assets[key].get_size()
            sh_w, sh_h = max(4, int(w * cfg['shadow_scale'][0])), max(3, int(h * cfg['shadow_scale'][1]))
            shadow = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, cfg['shadow_alpha']), (0, 0, sh_w, sh_h))
            game_assets[f'{key}_shadow'] = shadow
            
    if 'alarm' not in game_assets:
        path = os.path.join('dangerentity', 'alarm.png')
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            game_assets['alarm'] = pygame.transform.scale(img, (max(1, int(img.get_width() / 3.45)), max(1, int(img.get_height() / 3.45))))
        else:
            dummy = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(dummy, (255, 0, 0), (15, 15), 15)
            game_assets['alarm'] = dummy

    if 'explosion_frames' not in game_assets:
        path = os.path.join('dangerentity', 'ex.png')
        frames = []
        if os.path.exists(path):
            sheet = pygame.image.load(path).convert_alpha()
            fw, fh, margin = sheet.get_width() // 4, sheet.get_height() // 4, 6
            for row in range(4):
                for col in range(4):
                    rect = pygame.Rect(col * fw + margin, row * fh + margin, fw - 2*margin, fh - 2*margin)
                    frame_img = pygame.transform.scale(sheet.subsurface(rect), (int((fw - 2*margin) * 2.2), int((fh - 2*margin) * 2.2)))
                    frames.append(frame_img)
            game_assets['explosion_frames'] = frames[:15]
        else:
            for i in range(15):
                dummy = pygame.Surface((260, 260), pygame.SRCALPHA)
                pygame.draw.circle(dummy, (255, 50 + i*10, 0), (130, 130), 33 + i*6)
                frames.append(dummy)
            game_assets['explosion_frames'] = frames

    if 'lava' not in game_assets:
        path = os.path.join('dangerentity', 'lava.png')
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            w, h = max(1, int(img.get_width() / 2.25)), max(1, int(img.get_height() / 2.25))
            game_assets['lava'] = pygame.transform.smoothscale(img, (w, h))
            shadow = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 20), (0, 0, w + 10, h + 10))
            game_assets['lava_shadow'] = shadow
        else:
            dummy = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(dummy, (240, 60, 10, 210), (80, 80), 62)
            game_assets['lava'] = dummy

    if 'nor_frames' not in game_assets:
        path = os.path.join('opp', 'nor.png')
        nor_frames = []
        if os.path.exists(path):
            sheet = pygame.image.load(path).convert_alpha()
            fw, fh = sheet.get_width() // 3, sheet.get_height() // 3
            for row in range(3):
                for col in range(3):
                    rect = pygame.Rect(col * fw, row * fh, fw, fh)
                    nor_frames.append(pygame.transform.smoothscale(sheet.subsurface(rect), (60, 60)))
        else:
            for _ in range(9):
                dummy = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(dummy, (150, 0, 150), (30, 30), 30)
                nor_frames.append(dummy)
        game_assets['nor_frames'] = nor_frames
        
    # Load Endless Entities
    new_entities = {
        'driedtree': {'fb_col': (70,50,40), 'fb_size': (45,65), 'shadow': True, 's_alpha': 20},
        'bone':      {'fb_col': (220,220,200), 'fb_size': (25,12), 'shadow': False},
        'skull':     {'fb_col': (240,240,230), 'fb_size': (18,18), 'shadow': True, 's_alpha': 10}, 
        'magma':     {'fb_col': (210,50,5), 'fb_size': (55,55), 'shadow': True, 's_alpha': 20} 
    }
    for key, conf in new_entities.items():
        if key not in game_assets:
            path = os.path.join('entity', f'{key}.png')
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                sf = 2.25 * 1.5 if key == 'skull' else 2.25
                game_assets[key] = pygame.transform.smoothscale(img, (max(1, int(img.get_width()/sf)), max(1, int(img.get_height()/sf))))
            else:
                dummy = pygame.Surface(conf['fb_size'], pygame.SRCALPHA)
                dummy.fill(conf['fb_col']) 
                game_assets[key] = dummy

            if conf['shadow']:
                w, h = game_assets[key].get_size()
                shadow = pygame.Surface((w, max(1, h // 2)), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, conf.get('s_alpha', 20)), (0, 0, w, max(1, h // 2)))
                game_assets[f'{key}_shadow'] = shadow

# --- MAIN LOOP ---
def run_game_mode(screen, clock, WIDTH, HEIGHT, game_assets, transition_func, mode_name, ground_key):
    load_game_entities(game_assets)
    
    # Initialize basic elements
    dirts, rocks, grasses, trees = [], [], [], []
    dirt_w, dirt_h = game_assets['dirt'].get_size()
    rock_w, rock_h = game_assets['rock'].get_size()
    grass_w, grass_h = game_assets['grass'].get_size()
    tree_w, tree_h = game_assets['tree'].get_size()

    # Layout generation
    if mode_name == 'EASY':
        dirts = [pygame.Rect(x, y, dirt_w, dirt_h) for x,y in [(140, 160), (640, 130), (200, 450), (580, 420)]]
        rocks = [pygame.Rect(x, y, rock_w, rock_h) for x,y in [(320, 110), (120, 310), (660, 460)]]
        grasses = [pygame.Rect(x, y, grass_w, grass_h) for x,y in [(110, 200), (460, 150), (160, 500), (560, 480)]]
    elif mode_name == 'MEDIUM':
        dirts = [pygame.Rect(x, y, dirt_w, dirt_h) for x,y in [(110, 360), (670, 310), (160, 480)]]
        rocks = [pygame.Rect(x, y, rock_w, rock_h) for x,y in [(220, 230), (550, 220), (520, 410)]]
        grasses = [pygame.Rect(x, y, grass_w, grass_h) for x,y in [(10, 300), (WIDTH - grass_w - 10, 300)]]
    elif mode_name == 'HARD':
        rocks = [pygame.Rect(x, y, rock_w, rock_h) for x,y in [(120, 80), (360, 140), (200, 260), (60, 500)]]
        trees = [pygame.Rect(x, y, tree_w, tree_h) for x,y in [(10, 190), (150, 320), (300, 350), (380, 420)]]

    all_obstacles = dirts + rocks + trees
    player = Player(WIDTH // 2, HEIGHT // 2)
    
    # ---------------------------------------------------------
    # SETUP WEAPON HỆ THỐNG MỚI TỪ WEAPON.PY
    # ---------------------------------------------------------
    weapon_img_path = f"weapon/{weapon.SELECTED_WEAPON}.png"
    if os.path.exists(weapon_img_path):
        w_img = pygame.image.load(weapon_img_path).convert_alpha()
    else:
        # Dự phòng nếu vũ khí load lỗi
        w_img = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.line(w_img, (200, 200, 200), (5, 35), (35, 5), 5)
        
    player_weapon = weapon.WeaponEntity(pygame.transform.scale(w_img, (50, 50)))

    # ---------------------------------------------------------
    # SETUP SPECIAL HỆ THỐNG MỚI TỪ SPECIAL.PY
    # ---------------------------------------------------------
    player_special = special.SpecialSkill()
    
    # State tracking
    active_dangers, active_lavas, active_endless_entities, active_enemies = [], [], [], []
    danger_spawn_timer, lava_spawn_timer, enemy_spawn_timer = 3.0, 0.0, 5.0
    player_in_lava = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0 
        
        # Calculate camera offset here (needed for mouse clicks)
        camera_x, camera_y = (int(player.x) - WIDTH // 2, int(player.y) - HEIGHT // 2) if mode_name == 'ENDLESS' else (0, 0)
        
        # 1. EVENT HANDLING
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                running = False
                
            # SỰ KIỆN NÉM VŨ KHÍ (CHUỘT TRÁI):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                target_x = mx + camera_x
                target_y = my + camera_y
                
                # 🌟 THAY ĐỔI QUAN TRỌNG: Gắn hook kiểm tra kỹ năng đặc biệt
                # Gọi kỹ năng, truyền tên vũ khí hiện tại. Hàm sẽ đếm hoặc kích hoạt kỹ năng.
                is_special = player_special.on_player_throw_weapon(weapon.SELECTED_WEAPON, target_x, target_y, player.x, player.y)
                
                # Nếu hàm trả về False (chưa đủ điều kiện, ví dụ chưa ném đủ 3 lần) -> ném vũ khí thường
                if not is_special:
                    player_weapon.throw(target_x, target_y, player.x, player.y)

            # ---------------------------------------------------------
            # SỰ KIỆN KÍCH HOẠT KỸ NĂNG ĐẶC BIỆT (CHUỘT PHẢI)
            # ---------------------------------------------------------
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                player_special.trigger(player.x, player.y)

        if not player.update_environment_logic(mode_name, WIDTH, HEIGHT):
            running = False

        # 2. UPDATES
        current_obstacles = [ent.rect for ent in active_endless_entities] if mode_name == 'ENDLESS' else all_obstacles
        player.handle_movement(pygame.key.get_pressed(), current_obstacles, grasses, mode_name, WIDTH, HEIGHT)

        draw_player_x, draw_player_y = (WIDTH // 2, HEIGHT // 2) if mode_name == 'ENDLESS' else (int(player.x), int(player.y))

        # Enemy Spawning & Logic
        enemy_spawn_timer -= dt
        if enemy_spawn_timer <= 0:
            cx, cy = (camera_x, camera_y) if mode_name == 'ENDLESS' else (0, 0)
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':      sx, sy = random.randint(cx - 50, cx + WIDTH + 50), cy - 60
            elif side == 'bottom': sx, sy = random.randint(cx - 50, cx + WIDTH + 50), cy + HEIGHT + 60
            elif side == 'left':   sx, sy = cx - 60, random.randint(cy - 50, cy + HEIGHT + 50)
            else:                  sx, sy = cx + WIDTH + 60, random.randint(cy - 50, cy + HEIGHT + 50)
            active_enemies.append(EnemyNor(sx, sy, game_assets['nor_frames']))
            enemy_spawn_timer = 5.0 
        
        for enemy in active_enemies: enemy.update(player, dt, WIDTH, HEIGHT, mode_name)

        # Danger/Lava/Endless Logic
        if mode_name == 'MEDIUM':
            danger_spawn_timer -= dt
            if danger_spawn_timer <= 0:
                roll = random.random()
                spawn_count = 5 if roll < 0.05 else (2 if roll < 0.45 else 1)
                for _ in range(spawn_count):
                    active_dangers.append(DangerExplosion(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), game_assets['alarm'], game_assets['explosion_frames']))
                danger_spawn_timer = 3.0 
            
            for danger in active_dangers[:]:
                danger.update(player, WIDTH, HEIGHT, mode_name)
                if danger.state == "DONE": active_dangers.remove(danger)
                
        elif mode_name == 'ENDLESS':
            player_in_lava = False
            lavas_on_screen, ents_on_screen = 0, 0
            
            for lava in active_lavas[:]:
                lava.update(camera_x, camera_y, WIDTH, HEIGHT)
                if lava.state == "DONE": active_lavas.remove(lava); continue
                if math.hypot(player.x - lava.x, player.y - lava.y) < lava.radius + player.radius: player_in_lava = True
                if is_on_screen(lava.x, lava.y, camera_x, camera_y, WIDTH, HEIGHT, buffer=0): lavas_on_screen += 1
            
            for ent in active_endless_entities[:]:
                ent.update(camera_x, camera_y, WIDTH, HEIGHT)
                if ent.state == "DONE": active_endless_entities.remove(ent)
                elif is_on_screen(ent.x, ent.y, camera_x, camera_y, WIDTH, HEIGHT, buffer=0): ents_on_screen += 1

            if lavas_on_screen < 1: lava_spawn_timer -= dt
            
            if ents_on_screen < 4 or (lavas_on_screen < 1 and lava_spawn_timer <= 0):
                # Sử dụng hàm get_valid_spawn_pos với min_entity_dist đã tăng
                spawn_x, spawn_y = get_valid_spawn_pos(
                    camera_x, camera_y, WIDTH, HEIGHT, 
                    player.x, player.y, 
                    active_endless_entities, active_lavas
                )
                
                if lavas_on_screen < 1 and lava_spawn_timer <= 0:
                    active_lavas.append(LavaPool(spawn_x, spawn_y, game_assets['lava'], game_assets.get('lava_shadow')))
                    lava_spawn_timer = 8.0
                elif ents_on_screen < 4:
                    entity_types = ['driedtree', 'bone', 'skull', 'magma']
                    chosen_type = random.choices(entity_types, weights=[35, 30, 20, 15], k=1)[0]
                    active_endless_entities.append(EndlessEntity(spawn_x, spawn_y, game_assets[chosen_type], chosen_type, game_assets.get(f'{chosen_type}_shadow')))

            player.in_lava = player_in_lava
            player.update_lava_logic(dt)

        # ---------------------------------------------------------
        # UPDATE LOGIC VŨ KHÍ 
        # ---------------------------------------------------------
        # Tổng hợp các chướng ngại vật (rects) để vũ khí bật lại khi va chạm
        weapon_colliders = []
        if mode_name == 'ENDLESS':
            weapon_colliders.extend([ent.rect for ent in active_endless_entities])
        else:
            weapon_colliders.extend(all_obstacles)
            
        player_weapon.update(player.x, player.y, weapon_colliders)
        
        # Kiểm tra va chạm giữa vũ khí và quái vật (EnemyNor) để gây sát thương
        if player_weapon.state in ['thrown', 'returning']:
            for enemy in active_enemies[:]:
                # Tạo rect ảo bao quanh enemy
                enemy_rect = pygame.Rect(enemy.x - enemy.radius, enemy.y - enemy.radius, enemy.radius*2, enemy.radius*2)
                if player_weapon.rect.colliderect(enemy_rect):
                    # Tiêu diệt quái
                    active_enemies.remove(enemy)
                    # Sau khi chém trúng quái, vũ khí thu hồi về
                    player_weapon.state = 'returning'

        # ---------------------------------------------------------
        # UPDATE LOGIC KỸ NĂNG ĐẶC BIỆT
        # ---------------------------------------------------------
        player_special.update(player.x, player.y, active_enemies)

        # 3. DRAWING
        if game_assets.get(ground_key):
            if mode_name == 'ENDLESS':
                bg_img, (bg_w, bg_h) = game_assets[ground_key], game_assets[ground_key].get_size()
                for x in range(int(-(camera_x % bg_w)) - bg_w, WIDTH + bg_w, bg_w):
                    for y in range(int(-(camera_y % bg_h)) - bg_h, HEIGHT + bg_h, bg_h):
                        screen.blit(bg_img, (x, y))
            else:
                screen.blit(game_assets[ground_key], (0, 0))
        else:
            screen.fill({'EASY': (60, 75, 65), 'MEDIUM': (75, 65, 50), 'HARD': (45, 40, 50), 'ENDLESS': (70, 30, 30)}.get(mode_name, (50, 50, 50)))
            
        # Draw Entities
        if mode_name in ['EASY', 'MEDIUM', 'HARD']:
            all_rects = dirts + rocks + grasses + trees
            all_keys = ['dirt']*len(dirts) + ['rock']*len(rocks) + ['grass']*len(grasses) + ['tree']*len(trees)
            
            for obs, key in zip(all_rects, all_keys):
                shadow_key = f'{key}_shadow'
                if game_assets.get(shadow_key):
                    sh_img = game_assets[shadow_key]
                    sh_rect = sh_img.get_rect(center=(obs.centerx, obs.bottom - 2))
                    screen.blit(sh_img, sh_rect)
                
            for obs, key in zip(all_rects, all_keys):
                screen.blit(game_assets[key], obs.topleft)
                
        if mode_name == 'MEDIUM':
            for danger in active_dangers: danger.draw(screen, camera_x, camera_y)
        elif mode_name == 'ENDLESS':
            for lava in active_lavas: lava.draw_shadow(screen, camera_x, camera_y)
            for lava in active_lavas: lava.draw(screen, camera_x, camera_y)
            for ent in active_endless_entities: ent.draw_shadow(screen, camera_x, camera_y)
            for ent in active_endless_entities: ent.draw(screen, camera_x, camera_y)

        # Draw Characters
        for enemy in active_enemies: enemy.draw(screen, camera_x, camera_y)
        player.draw(screen, draw_player_x, draw_player_y, game_assets['font_level_diff'])
        
        # ---------------------------------------------------------
        # VẼ VŨ KHÍ VÀ KỸ NĂNG ĐẶC BIỆT LÊN MÀN HÌNH
        # ---------------------------------------------------------
        player_weapon.draw(screen, camera_x, camera_y)
        player_special.draw(screen, camera_x, camera_y)
        
        # Draw Overlays
        if mode_name == 'ENDLESS' and player_in_lava and (pygame.time.get_ticks() // 100) % 2 == 0:  
            orange_flash = pygame.Surface((player.radius * 2, player.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(orange_flash, (255, 110, 0, 150), (player.radius, player.radius), player.radius)
            screen.blit(orange_flash, (draw_player_x - player.radius, draw_player_y - player.radius))
        
        draw_health_bar(screen, 20, 20, player.health, player.max_health, game_assets['font_level_diff'])
        if mode_name == 'HARD' and player.water_timer > 0: 
            draw_text_with_shadow(f"OXYGEN: {max(0, int(15.0 - player.water_timer))}s", game_assets['font_level_diff'], (100, 200, 255), screen, WIDTH // 2, 30)
        draw_text_with_shadow(f"{mode_name} MODE - PRESS ESC TO RETURN", game_assets['font_level_diff'], (220, 220, 220), screen, WIDTH // 2, HEIGHT - 25)
        
        pygame.display.update()

    transition_func(clock)