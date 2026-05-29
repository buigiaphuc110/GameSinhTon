import pygame
import sys
import os
import random
import math
from player import Player
import weapon  
import special 
import score 

# --- CONSTANTS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60

# --- HELPERS (Giữ nguyên) ---
def is_on_screen(x, y, camera_x, camera_y, width, height, buffer=200):
    return (camera_x - buffer <= x <= camera_x + width + buffer) and (camera_y - buffer <= y <= camera_y + height + buffer)

def get_valid_spawn_pos(camera_x, camera_y, width, height, player_x, player_y, existing_entities, existing_lavas, min_player_dist=400, min_entity_dist=250):
    for _ in range(100): 
        x, y = random.randint(camera_x - 100, camera_x + width + 100), random.randint(camera_y - 100, camera_y + height + 100)
        if math.hypot(x - player_x, y - player_y) < min_player_dist: continue
        overlap = any(math.hypot(x - ent.x, y - ent.y) < min_entity_dist for ent in existing_entities)
        if overlap: continue
        overlap = any(math.hypot(x - lava.x, y - lava.y) < (min_entity_dist + lava.radius) for lava in existing_lavas)
        if not overlap: return x, y
    return player_x + random.choice([-600, 600]), player_y + random.choice([-600, 600])

def draw_text_with_shadow(text, font, color, surface, x, y):
    surface.blit(font.render(text, True, BLACK), font.render(text, True, BLACK).get_rect(center=(x + 3, y + 3)))
    surface.blit(font.render(text, True, color), font.render(text, True, color).get_rect(center=(x, y)))

def draw_health_bar(surface, x, y, health, max_health, font, shield=0, max_shield=0):
    total_width, bar_height, tag_width = 180, 22, 34
    pygame.draw.rect(surface, (25, 25, 25), (x + 3, y + 3, total_width, bar_height))
    pygame.draw.rect(surface, BLACK, (x, y, total_width, bar_height), width=2)
    pygame.draw.rect(surface, (40, 40, 45), (x + 2, y + 2, total_width - 4, bar_height - 4))
    pygame.draw.rect(surface, (170, 35, 35), (x + 2, y + 2, tag_width, bar_height - 4))
    pygame.draw.rect(surface, BLACK, (x + 2 + tag_width, y, 2, bar_height))
    surface.blit(font.render("HP", True, WHITE), font.render("HP", True, WHITE).get_rect(center=(x + 2 + tag_width // 2, y + bar_height // 2)))
    
    gauge_x, gauge_width, gauge_height = x + 2 + tag_width + 2, total_width - tag_width - 6, bar_height - 4
    pygame.draw.rect(surface, (75, 20, 20), (gauge_x, y + 2, gauge_width, gauge_height))
    
    if health > 0:
        health_ratio = max(0.0, min(1.0, health / max_health))
        cw = int(gauge_width * health_ratio)
        main_color = (45, 200, 45) if health_ratio > 0.5 else ((230, 165, 30) if health_ratio > 0.2 else (215, 35, 35))
        pygame.draw.rect(surface, main_color, (gauge_x, y + 2, cw, gauge_height))
    
    if shield > 0 and max_shield > 0:
        shield_ratio = max(0.0, min(1.0, shield / max_shield))
        sw = int(gauge_width * shield_ratio)
        pygame.draw.rect(surface, (100, 200, 255), (gauge_x, y + 2, sw, gauge_height))

    stat_str = f"{int(health)}/{int(max_health)}" + (f" [+ {int(shield)}]" if shield > 0 else "")
    surface.blit(font.render(stat_str, True, BLACK), (x + total_width + 12, y + 2))
    surface.blit(font.render(stat_str, True, WHITE), (x + total_width + 10, y))

# --- ENTITIES THIÊN NHIÊN ---
class DangerExplosion:
    def __init__(self, x, y, alarm_img, explosion_frames):
        self.x, self.y, self.alarm_img, self.frames = x, y, alarm_img, explosion_frames
        self.state, self.start_timer, self.warning_duration = "WARNING", pygame.time.get_ticks(), 1500
        self.frame_index, self.frame_rate, self.last_frame_time = 0, 50, pygame.time.get_ticks()
        self.has_dealt_damage, self.hitbox_radius = False, 130 

    def update(self, player, width, height, mode_name, player_shield=0):
        current_time = pygame.time.get_ticks()
        if self.state == "WARNING":
            if current_time - self.start_timer > self.warning_duration:
                self.state, self.last_frame_time = "EXPLODING", current_time
        elif self.state == "EXPLODING":
            if current_time - self.last_frame_time > self.frame_rate:
                self.frame_index += 1
                self.last_frame_time = current_time
                if self.frame_index >= len(self.frames):
                    self.state = "DONE"
                    return
            if self.frame_index == 3 and not self.has_dealt_damage:
                if math.hypot(player.x - self.x, player.y - self.y) < self.hitbox_radius + player.radius:
                    dmg = 20
                    if player_shield > 0: return dmg 
                    else: player.take_damage_and_knockback(dmg, self.x, self.y, 25, width, height, mode_name)
                    self.has_dealt_damage = True
        return 0

    def draw(self, screen, camera_x=0, camera_y=0):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        if self.state == "WARNING":
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                screen.blit(self.alarm_img, self.alarm_img.get_rect(center=(draw_x, draw_y)))
        elif self.state == "EXPLODING":
            if self.frame_index < len(self.frames):
                img = self.frames[self.frame_index]
                screen.blit(img, img.get_rect(center=(draw_x, draw_y)))

class LavaPool:
    def __init__(self, x, y, lava_img, shadow_image=None):
        self.x, self.y, self.image, self.shadow_image = x, y, lava_img, shadow_image
        self.state, self.radius = "ACTIVE", int(110 / 2.25) 

    def update(self, camera_x, camera_y, width, height):
        if not is_on_screen(self.x, self.y, camera_x, camera_y, width, height, buffer=200): self.state = "DONE"

    def draw_shadow(self, screen, camera_x, camera_y):
        if self.shadow_image: screen.blit(self.shadow_image, self.shadow_image.get_rect(center=(int(self.x - camera_x + 2), int(self.y - camera_y + 4))))

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, self.image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))

class EndlessEntity:
    def __init__(self, x, y, image, type_name, shadow_image=None):
        self.x, self.y, self.type_name, self.image, self.shadow_image = x, y, type_name, image, shadow_image
        self.rect = self.image.get_rect(center=(x, y))
        self.radius = max(self.rect.width, self.rect.height) // 2
        self.state = "ACTIVE"

    def update(self, camera_x, camera_y, width, height):
        if not is_on_screen(self.x, self.y, camera_x, camera_y, width, height, buffer=200): self.state = "DONE"

    def draw_shadow(self, screen, camera_x, camera_y):
        if self.shadow_image:
            draw_img = self.shadow_image
            if self.type_name == 'driedtree':
                alpha_val = max(0, min(255, int(20 + 2 * math.sin(pygame.time.get_ticks() / 200.0))))
                draw_img = self.shadow_image.copy()
                draw_img.fill((255, 255, 255, alpha_val), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(draw_img, draw_img.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y + self.rect.height//3))))

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, self.image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))

# ==========================================
# QUÁI VẬT & HIỆU ỨNG TỪ QUÁI
# ==========================================
class EnemyNor:
    def __init__(self, x, y, frames):
        self.x, self.y = float(x), float(y)
        self.type = 'normal'
        self.frames = [pygame.transform.scale(f, (int(f.get_width() / 1.65), int(f.get_height() / 1.4))) for f in frames]
        self.frame_index, self.frame_rate, self.last_frame_time = 0, 100, pygame.time.get_ticks()
        self.speed, self.radius = 35, 20 
        self.damage_cooldown, self.last_damage_time = 1000, 0
        self.angle, self.max_health = 0, 100  
        self.health, self.base_damage = self.max_health, 5
        self.score_value = 10
        self.rect = pygame.Rect(0, 0, self.frames[0].get_width(), self.frames[0].get_height()) if self.frames else pygame.Rect(0, 0, 32, 32)

    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0 

    def update(self, player, dt, width, height, mode_name, player_shield=0):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
            self.angle = math.degrees(math.atan2(-dy, dx)) 
        self.rect.center = (int(self.x), int(self.y))
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_time > self.frame_rate:
            if self.frames: self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_frame_time = current_time

        if dist < self.radius + player.radius:
            if current_time - self.last_damage_time > self.damage_cooldown:
                self.last_damage_time = current_time
                if player_shield > 0: return self.base_damage
                if hasattr(player, 'take_damage_and_knockback'):
                    player.take_damage_and_knockback(self.base_damage, self.x, self.y, 10, width, height, mode_name)
                else: player.health -= self.base_damage
        return 0

    def draw(self, screen, camera_x, camera_y):
        if not self.frames: return
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        rotated_img = pygame.transform.rotate(self.frames[self.frame_index], self.angle)
        screen.blit(rotated_img, rotated_img.get_rect(center=(draw_x, draw_y)))
        if self.health < self.max_health: 
            bx, by = draw_x - 10, draw_y - 20
            pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, 22, 5))
            pygame.draw.rect(screen, (50, 15, 15), (bx, by, 20, 3))
            if self.health > 0: pygame.draw.rect(screen, (60, 230, 60), (bx, by, int(20 * (self.health / self.max_health)), 3))

class EnemyNorBig(EnemyNor):
    def __init__(self, x, y, frames):
        super().__init__(x, y, frames)
        self.type = 'big'
        self.frames = [pygame.transform.scale(f, (f.get_width() * 2, f.get_height() * 2)) for f in self.frames]
        self.speed, self.radius = 45, 60 / 1.4 
        self.max_health = 300
        self.health, self.base_damage = self.max_health, 15
        self.score_value = 30
        self.rect = pygame.Rect(0, 0, self.frames[0].get_size()[0], self.frames[0].get_size()[1]) if self.frames else pygame.Rect(0, 0, 64, 64)

    def draw(self, screen, camera_x, camera_y):
        super().draw(screen, camera_x, camera_y)
        if self.health < self.max_health: 
            bx, by = int(self.x - camera_x) - 20, int(self.y - camera_y) - 40
            pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, 42, 6))
            pygame.draw.rect(screen, (50, 15, 15), (bx, by, 40, 4))
            if self.health > 0: pygame.draw.rect(screen, (60, 230, 60), (bx, by, int(40 * (self.health / self.max_health)), 4))

class PoisonBullet:
    def __init__(self, x, y, target_x, target_y):
        self.x, self.y = x, y
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        speed = 8.0
        self.vx = (dx / dist) * speed if dist > 0 else speed
        self.vy = (dy / dist) * speed if dist > 0 else 0
        self.radius, self.life = 8, 100

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(screen, (50, 255, 50), (int(self.x - camera_x), int(self.y - camera_y)), self.radius)
        pygame.draw.circle(screen, (200, 255, 200), (int(self.x - camera_x), int(self.y - camera_y)), self.radius // 2)

class EnemyNorGreen(EnemyNor):
    def __init__(self, x, y, frames):
        super().__init__(x, y, frames)
        self.type = 'green'
        self.speed, self.max_health = 25, 80
        self.health, self.score_value = self.max_health, 20
        self.fire_rate, self.last_shot_time = 2000, pygame.time.get_ticks()
        
        colored_frames = []
        for f in self.frames:
            new_f = f.copy()
            tint = pygame.Surface(new_f.get_size(), pygame.SRCALPHA)
            tint.fill((0, 200, 0, 120))
            new_f.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            colored_frames.append(new_f)
        self.frames = colored_frames

    def update(self, player, dt, width, height, mode_name, active_projectiles):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        self.angle = math.degrees(math.atan2(-dy, dx))
        
        if dist > 250:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
        elif dist < 200: 
            self.x -= (dx / dist) * self.speed * dt
            self.y -= (dy / dist) * self.speed * dt

        self.rect.center = (int(self.x), int(self.y))
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_time > self.frame_rate:
            if self.frames: self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_frame_time = current_time

        if dist < 400 and current_time - self.last_shot_time > self.fire_rate:
            active_projectiles.append(PoisonBullet(self.x, self.y, player.x, player.y))
            self.last_shot_time = current_time

class EnemyNorOrange(EnemyNor):
    def __init__(self, x, y, frames):
        super().__init__(x, y, frames)
        self.type = 'orange'
        self.speed, self.max_health = 45, 60
        self.health, self.score_value = self.max_health, 15
        
        colored_frames = []
        for f in self.frames:
            new_f = f.copy()
            tint = pygame.Surface(new_f.get_size(), pygame.SRCALPHA)
            tint.fill((255, 120, 0, 120))
            new_f.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            colored_frames.append(new_f)
        self.frames = colored_frames

class OrangeExplosion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius, self.max_radius, self.life = 5, 80, 255
        self.has_dealt_damage = False

    def update(self, player):
        self.radius += 8
        self.life -= 15
        if self.radius >= self.max_radius and self.life > 0 and not self.has_dealt_damage:
            if math.hypot(player.x - self.x, player.y - self.y) < self.max_radius:
                self.has_dealt_damage = True
                return True 
        return False

    def draw(self, screen, camera_x, camera_y):
        if self.life > 0:
            surf = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 120, 0, max(0, self.life)), (self.max_radius, self.max_radius), int(self.radius))
            screen.blit(surf, (int(self.x - camera_x - self.max_radius), int(self.y - camera_y - self.max_radius)))

# ==========================================
# CÁC KỸ NĂNG TỪ BUFF (MAGIC, KABOOM...)
# ==========================================
class MagicOrb:
    def __init__(self):
        self.angle, self.radius, self.damage = 0, 120, 10

    def update_and_draw(self, player, enemies, screen, cx, cy, level):
        if level <= 0: return
        self.angle = (self.angle + 4 + level*2) % 360
        
        for i in range(level):
            offset_angle = (self.angle + i * (360 / level)) % 360
            ox = player.x + math.cos(math.radians(offset_angle)) * self.radius
            oy = player.y + math.sin(math.radians(offset_angle)) * self.radius
            
            pygame.draw.circle(screen, (150, 50, 255), (int(ox - cx), int(oy - cy)), 12 + level*2)
            pygame.draw.circle(screen, (200, 150, 255), (int(ox - cx), int(oy - cy)), 6 + level)

            for e in enemies:
                if math.hypot(e.x - ox, e.y - oy) < 30:
                    e.take_damage(self.damage * level)
                    e.speed = max(10, e.speed - 15)

class KaboomExplosion:
    def __init__(self, x, y, level):
        self.x, self.y = x, y
        self.radius, self.max_radius, self.life = 5, 100 + (level * 30), 255
        self.level, self.damage = level, 30 * level
        self.has_dealt_damage = False

    def update(self, enemies):
        self.radius += 12
        self.life -= 15
        if self.radius >= self.max_radius and self.life > 0 and not self.has_dealt_damage:
            self.has_dealt_damage = True
            for e in enemies:
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist < self.max_radius:
                    e.take_damage(self.damage)
                    if dist > 0:
                        e.x += ((e.x - self.x) / dist) * 40
                        e.y += ((e.y - self.y) / dist) * 40

    def draw(self, screen, camera_x, camera_y):
        if self.life > 0:
            surf = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 50, 50, max(0, self.life)), (self.max_radius, self.max_radius), int(self.radius))
            pygame.draw.circle(surf, (255, 200, 50, max(0, self.life)), (self.max_radius, self.max_radius), int(self.radius*0.6))
            screen.blit(surf, (int(self.x - camera_x - self.max_radius), int(self.y - camera_y - self.max_radius)))

# ==========================================
# CẤU HÌNH WAVE VÀ BUFF UI
# ==========================================
def get_wave_enemies(mode_name, wave_num):
    multiplier = 1.5 if mode_name == 'MEDIUM' else (2.0 if mode_name == 'HARD' else 1.0)
    if mode_name == 'ENDLESS': multiplier = 1.0 + (wave_num * 0.2)
    normal_count = int((5 + wave_num * 3) * multiplier)
    green_count = int((wave_num // 2) * 1.5 * multiplier) 
    big_count = int((wave_num // 3) * 1.2 * multiplier)   
    orange_count = int((wave_num // 2) * 2 * multiplier) 
    
    enemies_list = ['normal'] * normal_count + ['green'] * green_count + ['big'] * big_count + ['orange'] * orange_count
    random.shuffle(enemies_list)
    return enemies_list

BUFF_TYPES = ['dame', 'health', 'speed', 'kaboom', 'x2', 'coin', 'shield', 'magic']
BUFF_DESCS = {
    'dame': "+30% Damage Multiplier",
    'health': "+50 Max HP and Regen",
    'speed': "+Move Speed, -Weapon CD",
    'kaboom': "Throws trigger Explosion",
    'x2': "Multiply orbit weapons",
    'coin': "+50% Score gained",
    'shield': "+50 Shield, +5% Dmg Resist",
    'magic': "Magic orbs orbit & slow enemies"
}

def draw_buff_card(screen, font, title, desc, rect, is_hover, level, buff_images):
    bg_color = (60, 60, 80) if not is_hover else (80, 80, 100)
    pygame.draw.rect(screen, bg_color, rect, border_radius=10)
    pygame.draw.rect(screen, (200, 200, 50), rect, width=3, border_radius=10)
    
    draw_text_with_shadow(title.upper(), font, (255, 215, 0), screen, rect.centerx, rect.y + 30)
    draw_text_with_shadow(f"Level: {level+1}/3", font, WHITE, screen, rect.centerx, rect.y + 60)
    
    if title in buff_images and buff_images[title]:
        screen.blit(buff_images[title], buff_images[title].get_rect(center=(rect.centerx, rect.y + 110)))
    
    words = desc.split(' ')
    y_offset, line = 160, ""
    for w in words:
        if font.size(line + w)[0] < rect.width - 20: line += w + " "
        else:
            draw_text_with_shadow(line, font, (200, 220, 255), screen, rect.centerx, rect.y + y_offset)
            line, y_offset = w + " ", y_offset + 25
    draw_text_with_shadow(line, font, (200, 220, 255), screen, rect.centerx, rect.y + y_offset)

def load_buff_images():
    images = {}
    for b in BUFF_TYPES:
        path = os.path.join('buff', f'{b}.png')
        if os.path.exists(path):
            try: images[b] = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (60, 60))
            except: images[b] = None
        else: images[b] = None
    return images

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
    buff_images = load_buff_images()
    
    dirts, rocks, grasses, trees = [], [], [], []
    dirt_w, dirt_h = game_assets['dirt'].get_size()
    rock_w, rock_h = game_assets['rock'].get_size()
    grass_w, grass_h = game_assets['grass'].get_size()
    tree_w, tree_h = game_assets['tree'].get_size()

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
    
    # Hàm load ảnh vũ khí dùng cho MULTI-WEAPON X2 BUFF
    def get_weapon_image():
        path = f"weapon/{weapon.SELECTED_WEAPON}.png"
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            if weapon.SELECTED_WEAPON in ['gun', 'bomb', 'flower']:
                return pygame.transform.scale(img, (int(70/1.2), int(70/1.2)))
            return pygame.transform.scale(img, (50, 50))
        w_img = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.line(w_img, (200, 200, 200), (5, 35), (35, 5), 5)
        return w_img

    # HỆ THỐNG DANH SÁCH VŨ KHÍ (Mặc định 1 cái)
    player_weapons = [weapon.WeaponEntity(get_weapon_image())]
    player_special = special.SpecialSkill()
    
    score.game_score.reset_score()
    
    active_dangers, active_lavas, active_endless_entities = [], [], []
    danger_spawn_timer, lava_spawn_timer = 3.0, 0.0
    player_in_lava = False

    # --- WAVE SYSTEM & BUFF VARIABLES ---
    current_wave = 1
    max_waves = 10 if mode_name != 'ENDLESS' else 999999
    enemies_to_spawn = get_wave_enemies(mode_name, current_wave)
    active_enemies = []
    enemy_projectiles = []
    enemy_spawn_timer = 0.5
    game_state = "PLAYING" # PLAYING, CHOOSING_BUFF, WAVE_TRANSITION, WON
    transition_timer = 0

    player_buffs = {b: 0 for b in BUFF_TYPES}
    buff_choices = [] 
    
    base_max_health = player.max_health
    shield_hp = 0
    kaboom_throws = 0
    orange_explosions = []
    kaboom_explosions = []
    magic_orb = MagicOrb()
    
    weapon_cooldown_timer = 0
    player_poison_time_left, player_last_poison_tick = 0, 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0 
        camera_x, camera_y = (int(player.x) - WIDTH // 2, int(player.y) - HEIGHT // 2) if mode_name == 'ENDLESS' else (0, 0)
        current_time = pygame.time.get_ticks()

        # EVENT HANDLING
        click_x, click_y = -1, -1
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                running = False
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "PLAYING" and current_time - weapon_cooldown_timer > max(50, 300 - player_buffs['speed']*60):
                    mx, my = pygame.mouse.get_pos()
                    target_x, target_y = mx + camera_x, my + camera_y
                    
                    is_special = player_special.on_player_throw_weapon(weapon.SELECTED_WEAPON, target_x, target_y, player.x, player.y)
                    if not is_special:
                        # CHỈNH SỬA: Ném tất cả vũ khí cùng lúc lan tỏa (Spread shot)
                        spread_angles = [0, -15, 15, -30, 30, -45, 45]
                        orbiting_weapons = [pw for pw in player_weapons if pw.state == 'orbit']
                        
                        for i, pw in enumerate(orbiting_weapons):
                            spread = spread_angles[i] if i < len(spread_angles) else random.randint(-30, 30)
                            dx, dy = target_x - player.x, target_y - player.y
                            angle_rad = math.radians(spread)
                            nx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
                            ny = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
                            pw.throw(player.x + nx, player.y + ny, player.x, player.y)
                        
                        weapon_cooldown_timer = current_time
                        
                        # Logic Kaboom Buff
                        if player_buffs['kaboom'] > 0:
                            kaboom_throws += 1
                            required_throws = max(2, 6 - player_buffs['kaboom'])
                            if kaboom_throws >= required_throws:
                                kaboom_throws = 0
                                kaboom_explosions.append(KaboomExplosion(player.x, player.y, player_buffs['kaboom']))

                elif game_state == "CHOOSING_BUFF":
                    click_x, click_y = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and game_state == "PLAYING":
                player_special.trigger(player.x, player.y)

        if not player.update_environment_logic(mode_name, WIDTH, HEIGHT):
            running = False

        if player_poison_time_left > 0:
            if current_time - player_last_poison_tick >= 1000:
                player.health -= 1
                player_last_poison_tick = current_time
                player_poison_time_left -= 1
                if player.health <= 0: running = False

        # 2. UPDATES
        if game_state == "PLAYING":
            current_obstacles = [ent.rect for ent in active_endless_entities] if mode_name == 'ENDLESS' else all_obstacles
            player.handle_movement(pygame.key.get_pressed(), current_obstacles, grasses, mode_name, WIDTH, HEIGHT)

            # CẬP NHẬT SỐ LƯỢNG VŨ KHÍ TỪ X2 BUFF
            target_weapon_count = 1 + player_buffs['x2']
            if len(player_weapons) < target_weapon_count:
                while len(player_weapons) < target_weapon_count:
                    player_weapons.append(weapon.WeaponEntity(get_weapon_image()))
                for i, pw in enumerate(player_weapons):
                    pw.angle = i * (360 / target_weapon_count) # Phân bố đều góc quay quanh người

            if player_buffs['health'] > 0 and current_time % max(100, 1000 - player_buffs['health']*200) < 20:
                player.health = min(player.max_health, player.health + 1)

            if len(enemies_to_spawn) > 0:
                enemy_spawn_timer -= dt
                if enemy_spawn_timer <= 0:
                    cx, cy = (camera_x, camera_y) if mode_name == 'ENDLESS' else (0, 0)
                    side = random.choice(['top', 'bottom', 'left', 'right'])
                    if side == 'top':      sx, sy = random.randint(cx - 50, cx + WIDTH + 50), cy - 60
                    elif side == 'bottom': sx, sy = random.randint(cx - 50, cx + WIDTH + 50), cy + HEIGHT + 60
                    elif side == 'left':   sx, sy = cx - 60, random.randint(cy - 50, cy + HEIGHT + 50)
                    else:                  sx, sy = cx + WIDTH + 60, random.randint(cy - 50, cy + HEIGHT + 50)
                    
                    e_type = enemies_to_spawn.pop()
                    if e_type == 'big': active_enemies.append(EnemyNorBig(sx, sy, game_assets['nor_frames']))
                    elif e_type == 'green': active_enemies.append(EnemyNorGreen(sx, sy, game_assets['nor_frames']))
                    elif e_type == 'orange': active_enemies.append(EnemyNorOrange(sx, sy, game_assets['nor_frames']))
                    else: active_enemies.append(EnemyNor(sx, sy, game_assets['nor_frames']))
                    
                    enemy_spawn_timer = max(0.2, 1.0 - (current_wave * 0.05))
            
            elif len(enemies_to_spawn) == 0 and len(active_enemies) == 0:
                if current_wave >= max_waves: game_state = "WON"
                else:
                    current_wave += 1
                    game_state = "CHOOSING_BUFF"
                    available = [b for b in BUFF_TYPES if player_buffs[b] < 3]
                    if len(available) >= 3: buff_choices = random.sample(available, 3)
                    else: buff_choices = available + random.sample(BUFF_TYPES, 3 - len(available))
                    
        elif game_state == "WAVE_TRANSITION":
            if current_time - transition_timer > 2000:
                game_state = "PLAYING"

        draw_player_x, draw_player_y = (WIDTH // 2, HEIGHT // 2) if mode_name == 'ENDLESS' else (int(player.x), int(player.y))
        
        for enemy in active_enemies: 
            dmg_taken = enemy.update(player, dt, WIDTH, HEIGHT, mode_name, player_buffs['shield'])
            if dmg_taken > 0:
                if shield_hp > 0: shield_hp -= dmg_taken
                else: player.take_damage_and_knockback(dmg_taken, enemy.x, enemy.y, 10, WIDTH, HEIGHT, mode_name)

        for proj in enemy_projectiles[:]:
            if not proj.update(): enemy_projectiles.remove(proj)
            elif math.hypot(player.x - proj.x, player.y - proj.y) < proj.radius + player.radius:
                dmg = 1
                if shield_hp > 0: shield_hp -= dmg
                else: player.health -= dmg
                player_poison_time_left = 3
                player_last_poison_tick = current_time
                if proj in enemy_projectiles: enemy_projectiles.remove(proj)

        if mode_name == 'MEDIUM':
            danger_spawn_timer -= dt
            if danger_spawn_timer <= 0:
                roll = random.random()
                spawn_count = 5 if roll < 0.05 else (2 if roll < 0.45 else 1)
                for _ in range(spawn_count):
                    active_dangers.append(DangerExplosion(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), game_assets['alarm'], game_assets['explosion_frames']))
                danger_spawn_timer = 3.0 
            
            for danger in active_dangers[:]:
                dmg_taken = danger.update(player, WIDTH, HEIGHT, mode_name, player_buffs['shield'])
                if dmg_taken > 0:
                    if shield_hp > 0: shield_hp -= dmg_taken
                    else: player.take_damage_and_knockback(dmg_taken, danger.x, danger.y, 25, WIDTH, HEIGHT, mode_name)
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
                spawn_x, spawn_y = get_valid_spawn_pos(camera_x, camera_y, WIDTH, HEIGHT, player.x, player.y, active_endless_entities, active_lavas)
                if lavas_on_screen < 1 and lava_spawn_timer <= 0:
                    active_lavas.append(LavaPool(spawn_x, spawn_y, game_assets['lava'], game_assets.get('lava_shadow')))
                    lava_spawn_timer = 8.0
                elif ents_on_screen < 4:
                    entity_types = ['driedtree', 'bone', 'skull', 'magma']
                    chosen_type = random.choices(entity_types, weights=[35, 30, 20, 15], k=1)[0]
                    active_endless_entities.append(EndlessEntity(spawn_x, spawn_y, game_assets[chosen_type], chosen_type, game_assets.get(f'{chosen_type}_shadow')))

            player.in_lava = player_in_lava
            player.update_lava_logic(dt)

        weapon_colliders = []
        if mode_name == 'ENDLESS':
            weapon_colliders.extend([ent.rect for ent in active_endless_entities])
        else:
            weapon_colliders.extend(all_obstacles)
            
        # LOGIC GÂY DAME VÀ SỰ KIỆN TỪ VŨ KHÍ
        damage_multiplier = 1.0 + (0.3 * player_buffs['dame'])
        
        for pw in player_weapons:
            pw.update(player.x, player.y, weapon_colliders)
            
            for enemy in active_enemies[:]:
                is_dead = False
                
                if pw.state == 'thrown' and pw.rect.colliderect(enemy.rect):
                    is_dead = enemy.take_damage(40 * damage_multiplier) 
                    pw.state = 'disappeared'
                    pw.action_time = current_time
                    pw.rect.center = (-9999, -9999) 
                    pw.explosion = weapon.WeaponExplosion(pw.x, pw.y, weapon.SELECTED_WEAPON)
                    
                    if weapon.SELECTED_WEAPON in ['bomb', 'bomb1'] and random.random() < 0.20:
                        player_special.particle_sys.spawn_bomb2_explosion(pw.x, pw.y)
                        player_special.active_toxic_clouds.append(special.ToxicCloudEntity(pw.x, pw.y))
                    
                    if weapon.SELECTED_WEAPON == 'wrench' and len(player_special.active_tanks) < 2:
                        player_special.active_tanks.append(special.TankEntity(pw.x, pw.y, player_special))
                        
                elif pw.state == 'shooting' and pw.active_bullet:
                    bullet_rect = pygame.Rect(0, 0, 10, 10)
                    bullet_rect.center = (int(pw.active_bullet['x']), int(pw.active_bullet['y']))
                    if bullet_rect.colliderect(enemy.rect):
                        is_dead = enemy.take_damage(30 * damage_multiplier) 
                        pw.explosion = weapon.WeaponExplosion(pw.active_bullet['x'], pw.active_bullet['y'], 'gun')
                        pw.active_bullet = None
                        pw.state = 'orbit'
                        
                if is_dead or enemy.health <= 0:
                    if enemy.type == 'orange':
                        orange_explosions.append(OrangeExplosion(enemy.x, enemy.y))
                    if enemy in active_enemies: 
                        active_enemies.remove(enemy)
                    score_mult = 1.0 + (0.5 * player_buffs['coin'])
                    score.game_score.add_points(int(enemy.score_value * score_mult))

        for ex in orange_explosions[:]:
            if ex.update(player):
                dmg = 20 * (0.95 ** player_buffs['shield']) 
                if shield_hp > 0: shield_hp -= dmg
                else: player.health -= dmg
            if ex.life <= 0: orange_explosions.remove(ex)
            
        for kex in kaboom_explosions[:]:
            kex.update(active_enemies)
            if kex.life <= 0: kaboom_explosions.remove(kex)

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

        for enemy in active_enemies: enemy.draw(screen, camera_x, camera_y)
        for proj in enemy_projectiles: proj.draw(screen, camera_x, camera_y)
        for ex in orange_explosions: ex.draw(screen, camera_x, camera_y)
        for kex in kaboom_explosions: kex.draw(screen, camera_x, camera_y)
        
        if game_state == "PLAYING" and player_buffs['magic'] > 0:
            magic_orb.update_and_draw(player, active_enemies, screen, camera_x, camera_y, player_buffs['magic'])

        player.draw(screen, draw_player_x, draw_player_y, game_assets['font_level_diff'])
        if player_poison_time_left > 0 and (current_time // 100) % 2 == 0:
            poison_flash = pygame.Surface((player.radius * 2.5, player.radius * 2.5), pygame.SRCALPHA)
            pygame.draw.circle(poison_flash, (0, 255, 0, 100), (player.radius*1.25, player.radius*1.25), player.radius*1.25)
            screen.blit(poison_flash, (draw_player_x - player.radius*1.25, draw_player_y - player.radius*1.25))

        # --- VẼ DANH SÁCH VŨ KHÍ ---
        for pw in player_weapons: pw.draw(screen, camera_x, camera_y)
        player_special.draw(screen, camera_x, camera_y)
        
        if mode_name == 'ENDLESS' and player_in_lava and (pygame.time.get_ticks() // 100) % 2 == 0:  
            orange_flash = pygame.Surface((player.radius * 2, player.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(orange_flash, (255, 110, 0, 150), (player.radius, player.radius), player.radius)
            screen.blit(orange_flash, (draw_player_x - player.radius, draw_player_y - player.radius))
        
        draw_health_bar(screen, 20, 20, player.health, player.max_health, game_assets['font_level_diff'], shield_hp, 50 * player_buffs['shield'])
        score.game_score.draw_in_game(screen, game_assets['font_level_diff'], 20, 60)
        
        # --- UI CHỌN BUFF VÀ THÔNG BÁO MÀN ---
        if game_state == "CHOOSING_BUFF":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            draw_text_with_shadow("LEVEL UP! CHOOSE A BUFF", game_assets['font_level_title'], (255, 215, 0), screen, WIDTH // 2, 100)
            
            mx, my = pygame.mouse.get_pos()
            card_w, card_h, gap = 200, 300, 30
            start_x = (WIDTH - (3 * card_w + 2 * gap)) // 2
            
            for i, buff_name in enumerate(buff_choices):
                rect = pygame.Rect(start_x + i * (card_w + gap), 180, card_w, card_h)
                draw_buff_card(screen, game_assets['font_level_diff'], buff_name, BUFF_DESCS[buff_name], rect, rect.collidepoint(mx, my), player_buffs[buff_name], buff_images)
                
                if click_x != -1 and rect.collidepoint(click_x, click_y):
                    if player_buffs[buff_name] < 3: player_buffs[buff_name] += 1
                    
                    if buff_name == 'health': 
                        player.max_health = base_max_health + (50 * player_buffs['health'])
                        player.health = player.max_health
                    elif buff_name == 'speed': player.speed = 250 + (30 * player_buffs['speed'])
                    elif buff_name == 'shield': shield_hp = 50 * player_buffs['shield']
                    
                    game_state = "WAVE_TRANSITION"
                    transition_timer = current_time
                    enemies_to_spawn = get_wave_enemies(mode_name, current_wave)
                    click_x = -1

        elif game_state == "WAVE_TRANSITION":
            draw_text_with_shadow(f"WAVE {current_wave}", game_assets['font_level_title'], (255, 100, 100), screen, WIDTH // 2, HEIGHT // 2)
        elif game_state == "WON":
            draw_text_with_shadow(f"YOU WIN!", game_assets['font_title'], (255, 215, 0), screen, WIDTH // 2, HEIGHT // 2 - 30)
            draw_text_with_shadow(f"PRESS ESC TO RETURN", game_assets['font_level_txt'], WHITE, screen, WIDTH // 2, HEIGHT // 2 + 30)
        else:
            wave_text = f"WAVE {current_wave}/{max_waves}" if mode_name != 'ENDLESS' else f"WAVE {current_wave} (ENDLESS)"
            draw_text_with_shadow(wave_text, game_assets['font_level_diff'], (200, 200, 255), screen, WIDTH - 80, 30)
            draw_text_with_shadow(f"Enemies Left: {len(active_enemies) + len(enemies_to_spawn)}", game_assets['font_level_diff'], WHITE, screen, WIDTH - 80, 60)

        if mode_name == 'HARD' and player.water_timer > 0: 
            draw_text_with_shadow(f"OXYGEN: {max(0, int(15.0 - player.water_timer))}s", game_assets['font_level_diff'], (100, 200, 255), screen, WIDTH // 2, 30)
        draw_text_with_shadow(f"{mode_name} MODE - PRESS ESC TO RETURN", game_assets['font_level_diff'], (220, 220, 220), screen, WIDTH // 2, HEIGHT - 25)
        
        pygame.display.update()

    score.game_score.save_high_score()
    transition_func(clock)