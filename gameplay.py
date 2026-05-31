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

# --- HELPERS ---
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
                    return 0
            if self.frame_index == 3 and not self.has_dealt_damage:
                if math.hypot(player.x - self.x, player.y - self.y) < self.hitbox_radius + player.radius:
                    self.has_dealt_damage = True
                    return 20 
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
# CÁC DẠNG ĐẠN/VŨ KHÍ QUÁI VẬT
# ==========================================
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

class ChainProjectile:
    def __init__(self, x, y, target_x, target_y, owner):
        self.x, self.y = x, y
        self.owner = owner
        self.is_chain = True
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        self.vx = (dx / dist) * 15 if dist > 0 else 0
        self.vy = (dy / dist) * 15 if dist > 0 else 0
        self.radius, self.life = 8, 45

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.line(screen, (130, 130, 130), (int(self.owner.x - camera_x), int(self.owner.y - camera_y)), (int(self.x - camera_x), int(self.y - camera_y)), 5)
        pygame.draw.circle(screen, (180, 180, 180), (int(self.x - camera_x), int(self.y - camera_y)), self.radius)

class CannonballProjectile:
    def __init__(self, x, y, target_x, target_y):
        self.x, self.y = x, y
        self.is_cannon = True
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        self.vx = (dx / dist) * 4.5 if dist > 0 else 0
        self.vy = (dy / dist) * 4.5 if dist > 0 else 0
        self.radius, self.life = 14, 120

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.circle(screen, (40, 40, 40), (int(self.x - camera_x), int(self.y - camera_y)), self.radius)
        pygame.draw.circle(screen, (255, 100, 0), (int(self.x - camera_x), int(self.y - camera_y)), self.radius // 2)

# ==========================================
# QUÁI VẬT
# ==========================================
class EnemyNor:
    def __init__(self, x, y, frames, wave=1):
        self.x, self.y = float(x), float(y)
        self.type = 'normal'
        self.frames = [pygame.transform.scale(f, (int(f.get_width() / 1.65), int(f.get_height() / 1.4))) for f in frames]
        self.frame_index, self.frame_rate, self.last_frame_time = 0, 100, pygame.time.get_ticks()
        
        stat_mult = 1.0 + max(0, (wave - 3) // 2) * 0.20 if wave >= 5 else 1.0
        
        self.speed, self.radius = 35 * stat_mult, 20 
        self.damage_cooldown, self.last_damage_time = 1000, 0
        self.angle, self.max_health = 0, int(100 * stat_mult)
        self.health, self.base_damage = self.max_health, int(5 * stat_mult)
        self.score_value = 10
        self.rect = pygame.Rect(0, 0, self.frames[0].get_width(), self.frames[0].get_height()) if self.frames else pygame.Rect(0, 0, 32, 32)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        return self.health <= 0 

    def update(self, player, dt, width, height, mode_name, player_shield, active_projectiles, all_obstacles=None):
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
                return self.base_damage
        return 0

    def draw(self, screen, camera_x, camera_y):
        if not self.frames: return
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        rotated_img = pygame.transform.rotate(self.frames[self.frame_index], self.angle)
        screen.blit(rotated_img, rotated_img.get_rect(center=(draw_x, draw_y)))
        
        if self.health < self.max_health and self.health > 0: 
            bx, by = draw_x - 10, draw_y - 20
            pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, 22, 5))
            pygame.draw.rect(screen, (50, 15, 15), (bx, by, 20, 3))
            pygame.draw.rect(screen, (60, 230, 60), (bx, by, max(0, int(20 * (self.health / self.max_health))), 3))

class EnemyNorBig(EnemyNor):
    def __init__(self, x, y, frames, wave=1):
        super().__init__(x, y, frames, wave)
        self.type = 'big'
        self.frames = [pygame.transform.scale(f, (f.get_width() * 2, f.get_height() * 2)) for f in self.frames]
        
        stat_mult = 1.0 + max(0, (wave - 3) // 2) * 0.20 if wave >= 5 else 1.0
        self.speed, self.radius = 45 * stat_mult, 60 / 1.4 
        self.max_health = int(300 * stat_mult)
        self.health, self.base_damage = self.max_health, int(15 * stat_mult)
        self.score_value = 30
        self.rect = pygame.Rect(0, 0, self.frames[0].get_size()[0], self.frames[0].get_size()[1]) if self.frames else pygame.Rect(0, 0, 64, 64)

    def draw(self, screen, camera_x, camera_y):
        super().draw(screen, camera_x, camera_y)
        if self.health < self.max_health and self.health > 0: 
            bx, by = int(self.x - camera_x) - 20, int(self.y - camera_y) - 40
            pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, 42, 6))
            pygame.draw.rect(screen, (50, 15, 15), (bx, by, 40, 4))
            pygame.draw.rect(screen, (60, 230, 60), (bx, by, max(0, int(40 * (self.health / self.max_health))), 4))

class EnemyNorGreen(EnemyNor):
    def __init__(self, x, y, frames, wave=1):
        super().__init__(x, y, frames, wave)
        self.type = 'green'
        self.wave = wave 
        
        stat_mult = 1.0 + max(0, (wave - 3) // 2) * 0.20 if wave >= 5 else 1.0
        self.speed, self.max_health = 25 * stat_mult, int(80 * stat_mult)
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

    def update(self, player, dt, width, height, mode_name, player_shield, active_projectiles, all_obstacles=None):
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
            if self.wave >= 5:
                angle_rad = math.atan2(player.y - self.y, player.x - self.x)
                spread_angle = 0.25 
                target_x2 = self.x + math.cos(angle_rad + spread_angle) * dist
                target_y2 = self.y + math.sin(angle_rad + spread_angle) * dist
                active_projectiles.append(PoisonBullet(self.x, self.y, target_x2, target_y2))
                
            self.last_shot_time = current_time
            
        if dist < self.radius + player.radius:
            if current_time - self.last_damage_time > self.damage_cooldown:
                self.last_damage_time = current_time
                return self.base_damage
        return 0

class EnemyNorOrange(EnemyNor):
    def __init__(self, x, y, frames, wave=1):
        super().__init__(x, y, frames, wave)
        self.type = 'orange'
        
        stat_mult = 1.0 + max(0, (wave - 3) // 2) * 0.20 if wave >= 5 else 1.0
        self.speed, self.max_health = 45 * stat_mult, int(60 * stat_mult)
        self.health, self.score_value = self.max_health, 15
        
        colored_frames = []
        for f in self.frames:
            new_f = f.copy()
            tint = pygame.Surface(new_f.get_size(), pygame.SRCALPHA)
            tint.fill((255, 120, 0, 120))
            new_f.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            colored_frames.append(new_f)
        self.frames = colored_frames

class EnemySpec(EnemyNor):
    def __init__(self, x, y, frames, wave=1):
        super().__init__(x, y, frames, wave)
        self.type = 'spec'
        stat_mult = 1.0 + max(0, (wave - 3) // 2) * 0.20 if wave >= 5 else 1.0
        self.max_health = int(130 * stat_mult) 
        self.health = self.max_health
        self.speed = 30 * stat_mult
        self.score_value = 25
        self.chain_cooldown = 4000
        self.last_chain_time = pygame.time.get_ticks()

    def update(self, player, dt, width, height, mode_name, player_shield, active_projectiles, all_obstacles=None):
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

        if dist < 450 and current_time - self.last_chain_time > self.chain_cooldown:
            active_projectiles.append(ChainProjectile(self.x, self.y, player.x, player.y, self))
            self.last_chain_time = current_time

        if dist < self.radius + player.radius:
            if current_time - self.last_damage_time > self.damage_cooldown:
                self.last_damage_time = current_time
                return self.base_damage
        return 0

class EnemyShip:
    def __init__(self, x, y, image, wave=1):
        self.x, self.y = float(x), float(y)
        self.type = 'ship'
        self.image = pygame.transform.scale(image, (80, 80))
        
        stat_mult = 1.0 + max(0, (wave - 3) // 2) * 0.20 if wave >= 5 else 1.0
        self.max_health = int(300 * stat_mult) 
        self.health = self.max_health
        self.speed = 20 * stat_mult 
        self.score_value = 40
        self.fire_rate = 3500
        self.last_shot_time = pygame.time.get_ticks()
        
        self.radius = 30
        self.angle = 0
        self.rect = pygame.Rect(0, 0, 80, 80)
        self.damage_cooldown = 1000
        self.last_damage_time = 0
        self.base_damage = int(15 * stat_mult)

    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0

    def update(self, player, dt, width, height, mode_name, player_shield, active_projectiles, all_obstacles=None):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            nx = self.x + (dx / dist) * self.speed * dt
            ny = self.y + (dy / dist) * self.speed * dt
            
            dummy_rect = self.rect.copy()
            dummy_rect.center = (int(nx), int(ny))
            hit_obstacle = False
            if all_obstacles:
                hit_obstacle = any(dummy_rect.colliderect(obs) for obs in all_obstacles)
                
            if not hit_obstacle and dist > 150:
                if 40 < nx < width - 40 and 40 < ny < height - 40:
                    self.x = nx
                    self.y = ny
            
            self.angle = math.degrees(math.atan2(-dy, dx))
            
        self.rect.center = (int(self.x), int(self.y))
        
        current_time = pygame.time.get_ticks()

        if dist < 650 and current_time - self.last_shot_time > self.fire_rate:
            active_projectiles.append(CannonballProjectile(self.x, self.y, player.x, player.y))
            self.last_shot_time = current_time
            
        if dist < self.radius + player.radius:
            if current_time - self.last_damage_time > self.damage_cooldown:
                self.last_damage_time = current_time
                return self.base_damage
        return 0

    def draw(self, screen, camera_x, camera_y):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        rotated_img = pygame.transform.rotate(self.image, self.angle)
        screen.blit(rotated_img, rotated_img.get_rect(center=(draw_x, draw_y)))
        
        if self.health < self.max_health and self.health > 0: 
            bx, by = draw_x - 15, draw_y - 40
            pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, 32, 6))
            pygame.draw.rect(screen, (50, 15, 15), (bx, by, 30, 4))
            pygame.draw.rect(screen, (60, 230, 60), (bx, by, max(0, int(30 * (self.health / self.max_health))), 4))

# ----------------- SMOOTH EXPLOSIONS -----------------
class OrangeExplosion:
    def __init__(self, x, y, wave=1):
        self.x, self.y = x, y
        self.radius = 5
        self.max_radius = 130 if wave >= 5 else 80
        self.life = 255
        self.has_dealt_damage = False

    def update(self, player):
        self.radius += (self.max_radius - self.radius) * 0.15 + 2
        self.life -= 12
        if self.radius >= self.max_radius * 0.75 and self.life > 0 and not self.has_dealt_damage:
            if math.hypot(player.x - self.x, player.y - self.y) < self.max_radius:
                self.has_dealt_damage = True
                return True 
        return False

    def draw(self, screen, camera_x, camera_y):
        if self.life > 0:
            surf = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 150, 50, max(0, self.life)), (self.max_radius, self.max_radius), int(self.radius * 0.6))
            pygame.draw.circle(surf, (255, 80, 0, max(0, int(self.life*0.6))), (self.max_radius, self.max_radius), int(self.radius), 4)
            screen.blit(surf, (int(self.x - camera_x - self.max_radius), int(self.y - camera_y - self.max_radius)))

class KaboomExplosion:
    def __init__(self, x, y, level, multiplier=1.0):
        self.x, self.y = x, y
        self.radius = 5
        if level >= 3:
            self.max_radius = 999999
        else:
            self.max_radius = 160 if level == 1 else 300
            
        self.life = 255
        self.level = level
        
        base_damage = 75 + (level * 12)
        self.damage = base_damage * multiplier
        
        self.has_dealt_damage = False

    def update(self, enemies):
        self.radius += (self.max_radius - self.radius) * 0.25 + 3
        self.life -= 15
        if self.radius >= self.max_radius * 0.6 and not self.has_dealt_damage:
            self.has_dealt_damage = True
            for e in enemies:
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if self.max_radius >= 999999 or dist < self.max_radius:
                    e.take_damage(self.damage)
                    if dist > 0 and self.max_radius < 999999:
                        e.x += ((e.x - self.x) / dist) * 40
                        e.y += ((e.y - self.y) / dist) * 40

    def draw(self, screen, camera_x, camera_y):
        if self.life > 0:
            if self.max_radius >= 999999:
                overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                overlay.fill((255, 200, 50, max(0, int(self.life * 0.4))))
                screen.blit(overlay, (0, 0))
            else:
                surf = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (200, 50, 50, max(0, int(self.life*0.5))), (self.max_radius, self.max_radius), int(self.radius))
                pygame.draw.circle(surf, (255, 200, 50, max(0, self.life)), (self.max_radius, self.max_radius), int(self.radius*0.7))
                pygame.draw.circle(surf, (255, 255, 200, max(0, self.life)), (self.max_radius, self.max_radius), int(self.radius), 3)
                screen.blit(surf, (int(self.x - camera_x - self.max_radius), int(self.y - camera_y - self.max_radius)))

# ==========================================
# CÁC KỸ NĂNG TỪ BUFF
# ==========================================
class MagicOrb:
    def __init__(self):
        self.angle, self.radius, self.base_damage = 0, 120, 10

    def update_and_draw(self, player, enemies, screen, cx, cy, level, dmg_multiplier):
        if level <= 0: return
        self.angle = (self.angle + 4 + level*2) % 360
        
        final_damage = (self.base_damage * level) * dmg_multiplier
        
        for i in range(level):
            offset_angle = (self.angle + i * (360 / level)) % 360
            ox = player.x + math.cos(math.radians(offset_angle)) * self.radius
            oy = player.y + math.sin(math.radians(offset_angle)) * self.radius
            
            pygame.draw.circle(screen, (150, 50, 255), (int(ox - cx), int(oy - cy)), 12 + level*2)
            pygame.draw.circle(screen, (200, 150, 255), (int(ox - cx), int(oy - cy)), 6 + level)

            for e in enemies:
                if math.hypot(e.x - ox, e.y - oy) < 30:
                    e.take_damage(final_damage)
                    e.speed = max(10, e.speed - 15)

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
    
    spec_count = int((wave_num // 2) * 1.5 * multiplier) if mode_name in ['MEDIUM', 'ENDLESS'] else 0
    ship_count = int((wave_num // 2) * 1.2 * multiplier) if mode_name == 'HARD' else 0
    
    enemies_list = ['normal'] * normal_count + ['green'] * green_count + ['big'] * big_count + ['orange'] * orange_count + ['spec'] * spec_count + ['ship'] * ship_count
    random.shuffle(enemies_list)
    return enemies_list

BUFF_TYPES = ['dame', 'health', 'speed', 'kaboom', 'x2', 'coin', 'shield', 'magic']
BUFF_DESCS = {
    'dame': "+30% Dmg/lv, +0.25%/Kill",
    'health': "+50 Max HP and Regen",
    'speed': "+Move Spd, Gun ++Bullets, -CD",
    'kaboom': "Throws trigger Explosion",
    'x2': "Multiply orbit weapons",
    'coin': "+50% Score gained",
    'shield': "+50 Shield, Lv2+: Spikes knockback",
    'magic': "Magic orbs orbit & slow enemies"
}

def draw_buff_card(screen, font, title, desc, rect, is_hover, level, buff_images):
    card_rect = rect.inflate(10, 10) if is_hover else rect
    shape_surf = pygame.Surface(card_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, (40, 40, 60, 230), shape_surf.get_rect(), border_radius=15)
    
    if level == 0:
        border_col = (200, 200, 200) # Trắng bạc (Lv0 -> Lv1)
        glow_col = (200, 200, 200, 60)
        title_col = (255, 255, 255) if is_hover else (200, 200, 200)
    elif level == 1:
        border_col = (255, 215, 0) # Vàng Kim (Lv1 -> Lv2)
        glow_col = (255, 215, 0, 60)
        title_col = (255, 215, 0) if is_hover else (200, 180, 0)
    else:
        border_col = (0, 255, 255) # Kim Cương Xanh (Lv2 -> Lv3)
        glow_col = (0, 255, 255, 60)
        title_col = (0, 255, 255) if is_hover else (0, 200, 200)
    
    if is_hover:
        pygame.draw.rect(shape_surf, border_col, shape_surf.get_rect(), width=4, border_radius=15)
        glow = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow, glow_col, glow.get_rect(), border_radius=15)
        shape_surf.blit(glow, (0, 0))
    else:
        muted = (max(0, border_col[0]-80), max(0, border_col[1]-80), max(0, border_col[2]-80))
        pygame.draw.rect(shape_surf, muted, shape_surf.get_rect(), width=2, border_radius=15)
        
    screen.blit(shape_surf, card_rect.topleft)
    draw_text_with_shadow(title.upper(), font, title_col, screen, card_rect.centerx, card_rect.y + 30)
    
    draw_text_with_shadow(f"Lv: {level} -> {level+1}", font, border_col, screen, card_rect.centerx, card_rect.y + 60)
    
    if title in buff_images and buff_images[title]:
        img = pygame.transform.scale(buff_images[title], (80, 80))
        screen.blit(img, img.get_rect(center=(card_rect.centerx, card_rect.y + 130)))
    
    words = desc.split(' ')
    y_offset, line = 190, ""
    for w in words:
        if font.size(line + w)[0] < card_rect.width - 30: line += w + " "
        else:
            draw_text_with_shadow(line, font, (220, 230, 255), screen, card_rect.centerx, card_rect.y + y_offset)
            line, y_offset = w + " ", y_offset + 25
    draw_text_with_shadow(line, font, (220, 230, 255), screen, card_rect.centerx, card_rect.y + y_offset)

def load_buff_images():
    images = {}
    colors = [(255,100,100), (100,255,100), (100,100,255), (255,200,50), (255,100,255), (100,255,255), (200,200,200), (150,150,150)]
    for i, b in enumerate(BUFF_TYPES):
        loaded = False
        for ext in ['.png', '.PNG', '.jpg', '.JPG']:
            for name_variant in [b, b.capitalize(), b.upper()]:
                path = os.path.join('buff', f'{name_variant}{ext}')
                if os.path.exists(path):
                    try: 
                        images[b] = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (60, 60))
                        loaded = True
                        break
                    except: pass
            if loaded: break
            
        if not loaded: 
            dummy = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(dummy, colors[i%len(colors)], (30,30), 25)
            font_small = pygame.font.SysFont(None, 28, bold=True)
            text = font_small.render(b[:2].upper(), True, BLACK)
            dummy.blit(text, text.get_rect(center=(30, 30)))
            images[b] = dummy
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
        
    if 'spec_frames' not in game_assets:
        path = os.path.join('opp', 'spec.png')
        frames = []
        if os.path.exists(path):
            sheet = pygame.image.load(path).convert_alpha()
            fw, fh = sheet.get_width() // 3, sheet.get_height() // 3
            for row in range(3):
                for col in range(3):
                    rect = pygame.Rect(col * fw, row * fh, fw, fh)
                    frames.append(pygame.transform.smoothscale(sheet.subsurface(rect), (60, 60)))
        else:
            for _ in range(9):
                dummy = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(dummy, (150, 150, 150), (30, 30), 30)
                frames.append(dummy)
        game_assets['spec_frames'] = frames

    if 'ship_img' not in game_assets:
        path = os.path.join('opp', 'ship.png')
        if os.path.exists(path):
            game_assets['ship_img'] = pygame.image.load(path).convert_alpha()
        else:
            dummy = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.polygon(dummy, (80, 80, 120), [(40,0), (80,40), (40,80), (0,40)])
            game_assets['ship_img'] = dummy

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
    pygame.mixer.init()
    if 'sfx' not in game_assets:
        game_assets['sfx'] = {}
        sfx_list = ['axesound', 'bombsound', 'flowersound', 'gunsound', 'swordsound', 'wrenchsound', 'hit', 'explosion', 'lose', 'winsound', 'win', 'buffsound', 'tanksound']
        for sfx in sfx_list:
            path = os.path.join('sound', f"{sfx}.mp3")
            if os.path.exists(path):
                try: game_assets['sfx'][sfx] = pygame.mixer.Sound(path)
                except: pass
            else:
                path_wav = os.path.join('sound', f"{sfx}.wav")
                if os.path.exists(path_wav):
                    try: game_assets['sfx'][sfx] = pygame.mixer.Sound(path_wav)
                    except: pass

    def play_cached_sfx(name):
        if 'sfx' in game_assets and name in game_assets['sfx']:
            game_assets['sfx'][name].play()
        elif name in ['winsound', 'win']:
            if 'win' in game_assets.get('sfx', {}): game_assets['sfx']['win'].play()
            elif 'winsound' in game_assets.get('sfx', {}): game_assets['sfx']['winsound'].play()
            
    game_assets['play_sfx'] = play_cached_sfx

    try:
        pygame.mixer.music.load(os.path.join('sound', 'battletheme.mp3'))
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
    except:
        pass

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
        trees = [pygame.Rect(x, y, tree_w, tree_h) for x,y in [(10, 190), (300, 350), (380, 420)]]

    all_obstacles = dirts + rocks + trees
    player = Player(WIDTH // 2, HEIGHT // 2)
    player.kaboom_level = 0
    player.total_kills = 0
    player.dame_buff_kills = 0 
    
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

    player_weapons = [weapon.WeaponEntity(get_weapon_image())]
    player_special = special.SpecialSkill(player) 
    score.game_score.reset_score()
    
    active_dangers, active_lavas, active_endless_entities = [], [], []
    danger_spawn_timer, lava_spawn_timer = 3.0, 0.0
    endless_danger_spawn_timer = 5.0  # Timer spawn DangerExplosion (alarm + ex) cho ENDLESS
    player_in_lava = False

    current_wave = 1
    max_waves = 10 if mode_name != 'ENDLESS' else 999999
    enemies_to_spawn = get_wave_enemies(mode_name, current_wave)
    active_enemies = []
    enemy_projectiles = []
    enemy_spawn_timer = 0.5
    game_state = "PLAYING" 
    transition_timer = 0

    player_buffs = {b: 0 for b in BUFF_TYPES}
    buff_choices = [] 
    
    base_max_health = player.max_health
    shield_hp = 0
    kaboom_throws = 0
    orange_explosions = []
    kaboom_explosions = []
    player_extra_bullets = [] 
    active_weapon_explosions = [] # QUẢN LÝ CÁC HIỆU ỨNG NỔ CỦA SÚNG ĐỂ RENDER CHUẨN XÁC
    magic_orb = MagicOrb()
    
    weapon_cooldown_timer = 0
    player_poison_time_left, player_last_poison_tick = 0, 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0 
        camera_x, camera_y = (int(player.x) - WIDTH // 2, int(player.y) - HEIGHT // 2) if mode_name == 'ENDLESS' else (0, 0)
        current_time = pygame.time.get_ticks()
        
        damage_multiplier = 1.0 + (0.3 * player_buffs['dame'])
        if player_buffs['dame'] > 0:
            damage_multiplier += (player.dame_buff_kills * 0.0025)
# ---> TRUYỀN BUFF DAMAGE SANG SPECIAL.PY <---
            player.damage_multiplier = damage_multiplier
        is_gun = (weapon.SELECTED_WEAPON == 'gun')
        trigger_shoot = False
        target_x, target_y = 0, 0
        click_x, click_y = -1, -1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                running = False
                
            # ĐÃ XÓA TÍNH NĂNG GIỮ CHUỘT, CHỈ BẮN KHI CLICK (MOUSEBUTTONDOWN)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "PLAYING":
                    trigger_shoot = True
                    mx, my = pygame.mouse.get_pos()
                    target_x, target_y = mx + camera_x, my + camera_y
                elif game_state == "CHOOSING_BUFF":
                    click_x, click_y = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and game_state == "PLAYING":
                player_special.trigger_random_skill()

        if trigger_shoot and game_state == "PLAYING":
            # --- CƠ CHẾ BẮN VÀ COOLDOWN ---
            # Với Gun, Cooldown gốc là 300ms, không bị giảm bởi speed vì speed dùng để tăng số đạn bắn liên tiếp (Burst)
            req_cd = 300 if is_gun else max(50, 300 - player_buffs['speed']*60)
            
            if current_time - weapon_cooldown_timer > req_cd:
                is_special = player_special.on_player_throw_weapon(weapon.SELECTED_WEAPON, target_x, target_y, player.x, player.y)
                if not is_special:
                    if is_gun:
                        base_angle = math.atan2(target_y - player.y, target_x - player.x)
                        num_bullets = 1 + player_buffs['speed']  # Số đạn bắn liên tiếp mỗi loạt
                        target_weapon_count = 1 + player_buffs['x2']  # Số nòng súng (bắn song song)
                        muzzle_radius = 65
                        
                        # Truyền tín hiệu giật súng
                        for pw in player_weapons:
                            if pw.state == 'orbit':
                                pw.recoil_timer = 10
                                pw.shoot_angle = base_angle
                                
                        # Bắn từ tất cả các nòng súng (Buff X2)
                        for b_idx in range(target_weapon_count):
                            offset_ang = base_angle + math.pi/2
                            offset_dist = (b_idx - (target_weapon_count - 1) / 2.0) * 18
                            muzzle_x = player.x + math.cos(base_angle) * muzzle_radius + math.cos(offset_ang) * offset_dist
                            muzzle_y = player.y + math.sin(base_angle) * muzzle_radius + math.sin(offset_ang) * offset_dist
                            
                            # CƠ CHẾ BURST FIRE: Bắn liên tiếp nhiều viên (Buff Speed)
                            for i in range(num_bullets):
                                player_extra_bullets.append({
                                    'x': muzzle_x, 'y': muzzle_y,
                                    'vx': math.cos(base_angle) * 30,
                                    'vy': math.sin(base_angle) * 30,
                                    'life': 30,
                                    'delay': i * 5  # Độ trễ 5 frames giữa mỗi viên để thành chuỗi đạn bay
                                })
                                
                        weapon_cooldown_timer = current_time
                        play_cached_sfx('gunsound')
                        
                        if player_buffs['kaboom'] > 0:
                            kaboom_throws += 1
                            required_throws = max(2, 8 - player_buffs['kaboom'])
                            if kaboom_throws >= required_throws:
                                kaboom_throws = 0
                                play_cached_sfx('tanksound')
                                kaboom_explosions.append(KaboomExplosion(player.x, player.y, player_buffs['kaboom'], damage_multiplier))
                    else:
                        orbiting_weapons = [pw for pw in player_weapons if pw.state == 'orbit']
                        if orbiting_weapons:
                            spread_angles = [0, -15, 15, -30, 30, -45, 45]
                            for i, pw in enumerate(orbiting_weapons):
                                spread = spread_angles[i] if i < len(spread_angles) else random.randint(-30, 30)
                                dx, dy = target_x - player.x, target_y - player.y
                                angle_rad = math.radians(spread)
                                nx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
                                ny = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
                                pw.throw(player.x + nx, player.y + ny, player.x, player.y)
                            
                            weapon_cooldown_timer = current_time
                            if weapon.SELECTED_WEAPON == 'flower': play_cached_sfx('flowersound')
                            elif weapon.SELECTED_WEAPON == 'sword': play_cached_sfx('swordsound')
                            
                            if player_buffs['kaboom'] > 0:
                                kaboom_throws += 1
                                required_throws = max(2, 8 - player_buffs['kaboom'])
                                if kaboom_throws >= required_throws:
                                    kaboom_throws = 0
                                    play_cached_sfx('tanksound')
                                    kaboom_explosions.append(KaboomExplosion(player.x, player.y, player_buffs['kaboom'], damage_multiplier))

        if not player.update_environment_logic(mode_name, WIDTH, HEIGHT):
            player.health = 0.0

        if player_poison_time_left > 0:
            if current_time - player_last_poison_tick >= 1000:
                player.health -= 1
                player_last_poison_tick = current_time
                player_poison_time_left -= 1

        current_obstacles = [ent.rect for ent in active_endless_entities] if mode_name == 'ENDLESS' else all_obstacles

        if game_state == "PLAYING":
            player.handle_movement(pygame.key.get_pressed(), current_obstacles, grasses, mode_name, WIDTH, HEIGHT)

            target_weapon_count = 1 + player_buffs['x2']
            if len(player_weapons) < target_weapon_count:
                while len(player_weapons) < target_weapon_count:
                    player_weapons.append(weapon.WeaponEntity(get_weapon_image()))
                for i, pw in enumerate(player_weapons):
                    pw.angle = i * (360 / target_weapon_count)

            if player_buffs['health'] > 0 and current_time % max(1500, 4500 - player_buffs['health'] * 1000) < 20:
                player.health = min(player.max_health, player.health + 1)

            if len(enemies_to_spawn) > 0:
                enemy_spawn_timer -= dt
                if enemy_spawn_timer <= 0:
                    cx, cy = (camera_x, camera_y) if mode_name == 'ENDLESS' else (0, 0)
                    e_type = enemies_to_spawn.pop()
                    
                    sx, sy = 0, 0
                    if e_type == 'ship':
                        for _ in range(50):
                            sx = random.randint(cx + 40, cx + WIDTH - 40)
                            sy = random.randint(cy + 40, cy + HEIGHT - 40)
                            if math.hypot(sx - player.x, sy - player.y) < 250:
                                continue
                            dummy_rect = pygame.Rect(0, 0, 80, 80)
                            dummy_rect.center = (sx, sy)
                            if not any(dummy_rect.colliderect(obs) for obs in current_obstacles):
                                break
                    else:
                        side = random.choice(['top', 'bottom', 'left', 'right'])
                        if side == 'top':      sx, sy = random.randint(cx - 50, cx + WIDTH + 50), cy - 60
                        elif side == 'bottom': sx, sy = random.randint(cx - 50, cx + WIDTH + 50), cy + HEIGHT + 60
                        elif side == 'left':   sx, sy = cx - 60, random.randint(cy - 50, cy + HEIGHT + 50)
                        else:                  sx, sy = cx + WIDTH + 60, random.randint(cy - 50, cy + HEIGHT + 50)
                    
                    if e_type == 'big': active_enemies.append(EnemyNorBig(sx, sy, game_assets['nor_frames'], wave=current_wave))
                    elif e_type == 'green': active_enemies.append(EnemyNorGreen(sx, sy, game_assets['nor_frames'], wave=current_wave))
                    elif e_type == 'orange': active_enemies.append(EnemyNorOrange(sx, sy, game_assets['nor_frames'], wave=current_wave))
                    elif e_type == 'spec': active_enemies.append(EnemySpec(sx, sy, game_assets['spec_frames'], wave=current_wave))
                    elif e_type == 'ship': active_enemies.append(EnemyShip(sx, sy, game_assets['ship_img'], wave=current_wave))
                    else: active_enemies.append(EnemyNor(sx, sy, game_assets['nor_frames'], wave=current_wave))
                    
                    enemy_spawn_timer = max(0.2, 1.0 - (current_wave * 0.05))
            
            elif len(enemies_to_spawn) == 0 and len(active_enemies) == 0:
                if current_wave >= max_waves:
                    if game_state != "WON":
                        pygame.mixer.music.stop()
                        play_cached_sfx('winsound') 
                        game_state = "WON"
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
            dmg_taken = enemy.update(player, dt, WIDTH, HEIGHT, mode_name, player_buffs['shield'], enemy_projectiles, current_obstacles)
            if dmg_taken > 0:
                if shield_hp > 0: 
                    shield_hp -= dmg_taken
                    if player_buffs['shield'] >= 2:
                        for e in active_enemies:
                            dist = math.hypot(e.x - player.x, e.y - player.y)
                            if dist < 120: 
                                if dist > 0:
                                    e.x += ((e.x - player.x) / dist) * 35
                                    e.y += ((e.y - player.y) / dist) * 35
                else: 
                    player.take_damage_and_knockback(dmg_taken, enemy.x, enemy.y, 10, WIDTH, HEIGHT, mode_name)

        for proj in enemy_projectiles[:]:
            if getattr(proj, 'is_chain', False):
                if not proj.update():
                    enemy_projectiles.remove(proj)
                elif math.hypot(player.x - proj.x, player.y - proj.y) < proj.radius + player.radius:
                    pull_dx, pull_dy = proj.owner.x - player.x, proj.owner.y - player.y
                    p_dist = math.hypot(pull_dx, pull_dy)
                    if p_dist > 50:
                        player.x += (pull_dx/p_dist) * 150 
                        player.y += (pull_dy/p_dist) * 150
                    if proj in enemy_projectiles: enemy_projectiles.remove(proj)
                    
            elif getattr(proj, 'is_cannon', False):
                if not proj.update():
                    orange_explosions.append(OrangeExplosion(proj.x, proj.y, current_wave))
                    if proj in enemy_projectiles: enemy_projectiles.remove(proj)
                elif math.hypot(player.x - proj.x, player.y - proj.y) < proj.radius + player.radius:
                    orange_explosions.append(OrangeExplosion(proj.x, proj.y, current_wave))
                    if proj in enemy_projectiles: enemy_projectiles.remove(proj)
            else:
                if not proj.update(): enemy_projectiles.remove(proj)
                elif math.hypot(player.x - proj.x, player.y - proj.y) < proj.radius + player.radius:
                    dmg = 1
                    if shield_hp > 0: shield_hp -= dmg
                    else: 
                        player.health -= dmg
                    player_poison_time_left = 3
                    player_last_poison_tick = current_time
                    if proj in enemy_projectiles: enemy_projectiles.remove(proj)

        weapon_colliders = [obs.inflate(-35, -35) if isinstance(obs, pygame.Rect) else obs for obs in current_obstacles]
        
        # --- CẬP NHẬT ĐẠN SÚNG & VA CHẠM (Có độ trễ Delay) ---
        for b in player_extra_bullets[:]:
            if b.get('delay', 0) > 0:
                b['delay'] -= 1
                continue
                
            b['x'] += b['vx']
            b['y'] += b['vy']
            b['life'] -= 1
            
            hit_something = False
            
            bullet_rect = pygame.Rect(0, 0, 10, 10)
            bullet_rect.center = (int(b['x']), int(b['y']))
            for obs in weapon_colliders:
                obs_rect = obs.rect if hasattr(obs, 'rect') else obs
                if isinstance(obs_rect, pygame.Rect) and bullet_rect.colliderect(obs_rect):
                    hit_something = True
                    break

            if not hit_something:
                for enemy in active_enemies[:]:
                    if math.hypot(enemy.x - b['x'], enemy.y - b['y']) < enemy.radius + 8:
                        is_dead = enemy.take_damage(18 * damage_multiplier)
                        hit_something = True
                        play_cached_sfx('hit')
                        
                        if is_dead or enemy.health <= 0:
                            player.total_kills += 1
                            if player_buffs['dame'] > 0:
                                player.dame_buff_kills += 1
                                
                            if enemy.type == 'orange':
                                orange_explosions.append(OrangeExplosion(enemy.x, enemy.y, current_wave))
                            elif enemy.type == 'big' and current_wave >= 5:
                                for _ in range(2):
                                    rx = enemy.x + random.randint(-25, 25)
                                    ry = enemy.y + random.randint(-25, 25)
                                    active_enemies.append(EnemyNor(rx, ry, game_assets['nor_frames'], wave=current_wave))
                                    
                            if enemy in active_enemies: 
                                active_enemies.remove(enemy)
                            score_mult = 1.0 + (0.5 * player_buffs['coin'])
                            score.game_score.add_points(int(enemy.score_value * score_mult))
                        break
                        
            if hit_something or b['life'] <= 0:
                active_weapon_explosions.append(weapon.WeaponExplosion(b['x'], b['y'], 'gun'))
                player_extra_bullets.remove(b)

        if mode_name == 'MEDIUM':
            if game_state == "PLAYING":
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
                        else: 
                            player.take_damage_and_knockback(dmg_taken, danger.x, danger.y, 25, WIDTH, HEIGHT, mode_name)
                    if danger.state == "DONE": active_dangers.remove(danger)
            else:
                active_dangers.clear()
                
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

            # --- SPAWN DANGER EXPLOSION (ALARM + EX) CHO ENDLESS ---
            if game_state == "PLAYING":
                endless_danger_spawn_timer -= dt
                if endless_danger_spawn_timer <= 0:
                    roll = random.random()
                    spawn_count = 4 if roll < 0.05 else (2 if roll < 0.35 else 1)
                    for _ in range(spawn_count):
                        sx = camera_x + random.randint(80, WIDTH - 80)
                        sy = camera_y + random.randint(80, HEIGHT - 80)
                        active_dangers.append(DangerExplosion(sx, sy, game_assets['alarm'], game_assets['explosion_frames']))
                    endless_danger_spawn_timer = random.uniform(4.0, 7.0)

                for danger in active_dangers[:]:
                    dmg_taken = danger.update(player, WIDTH, HEIGHT, mode_name, player_buffs['shield'])
                    if dmg_taken > 0:
                        if shield_hp > 0: shield_hp -= dmg_taken
                        else:
                            player.take_damage_and_knockback(dmg_taken, danger.x, danger.y, 25, WIDTH, HEIGHT, mode_name)
                    if danger.state == "DONE": active_dangers.remove(danger)
            else:
                active_dangers.clear()

        for pw in player_weapons:
            if not hasattr(pw, 'hit_targets'):
                pw.hit_targets = set()
                
            was_thrown = (pw.state == 'thrown')
            pw.update(player.x, player.y, weapon_colliders)
            
            if pw.state != 'thrown':
                pw.hit_targets.clear()
            
            if was_thrown and pw.state != 'thrown' and weapon.SELECTED_WEAPON != 'sword':
                pw.explosion = weapon.WeaponExplosion(pw.x, pw.y, weapon.SELECTED_WEAPON)
                
                if weapon.SELECTED_WEAPON not in ['flower', 'gun', 'tank', 'sword']:
                    play_cached_sfx(f"{weapon.SELECTED_WEAPON}sound")
                
                if weapon.SELECTED_WEAPON == 'axe':
                    for other_enemy in active_enemies:
                        if math.hypot(other_enemy.x - pw.x, other_enemy.y - pw.y) < 180:
                            other_enemy.take_damage(35 * damage_multiplier)
                            
                elif weapon.SELECTED_WEAPON in ['bomb', 'bomb1', 'bomb2']:
                    for other_enemy in active_enemies:
                        if math.hypot(other_enemy.x - pw.x, other_enemy.y - pw.y) < 150: 
                            other_enemy.take_damage(87 * damage_multiplier) 
                    
                    if getattr(pw, 'is_toxic', False): 
                        player_special.particle_sys.spawn_bomb2_explosion(pw.x, pw.y)
                        player_special.active_toxic_clouds.append(special.ToxicCloudEntity(pw.x, pw.y))
                        
                elif weapon.SELECTED_WEAPON == 'wrench':
                    max_tanks = 3 if player_buffs['speed'] >= 3 else 2
                    if len(player_special.active_tanks) < max_tanks:
                        player_special.active_tanks.append(special.TankEntity(pw.x, pw.y, player_special))

            orbit_hit_this_frame = False

            for enemy in active_enemies[:]:
                is_dead = False
                
                weapon_hit_radius = 22
                dist_to_enemy = math.hypot(enemy.x - pw.x, enemy.y - pw.y)
                
                if pw.state == 'thrown' and dist_to_enemy < (enemy.radius + weapon_hit_radius) and enemy not in pw.hit_targets:
                    base_dmg = 40
                    if weapon.SELECTED_WEAPON == 'sword':
                        base_dmg = 45 # ĐÃ GIẢM DAME SWORD
                        play_cached_sfx('swordsound') 
                    elif weapon.SELECTED_WEAPON in ['bomb', 'bomb1', 'bomb2']:
                        base_dmg = 100
                        
                    is_dead = enemy.take_damage(base_dmg * damage_multiplier) 
                    pw.hit_targets.add(enemy) 
                    
                    if weapon.SELECTED_WEAPON != 'sword':
                        pw.state = 'disappeared'
                        pw.action_time = current_time
                        pw.rect.center = (-9999, -9999) 
                        pw.explosion = weapon.WeaponExplosion(pw.x, pw.y, weapon.SELECTED_WEAPON)
                        
                        if weapon.SELECTED_WEAPON not in ['flower', 'gun', 'tank', 'sword']:
                            play_cached_sfx(f"{weapon.SELECTED_WEAPON}sound")
                        
                        if weapon.SELECTED_WEAPON == 'axe':
                            for other_enemy in active_enemies:
                                if other_enemy != enemy and math.hypot(other_enemy.x - pw.x, other_enemy.y - pw.y) < 180:
                                    other_enemy.take_damage(35 * damage_multiplier)
                                    
                        elif weapon.SELECTED_WEAPON in ['bomb', 'bomb1', 'bomb2']:
                            for other_enemy in active_enemies:
                                if other_enemy != enemy and math.hypot(other_enemy.x - pw.x, other_enemy.y - pw.y) < 150:
                                    other_enemy.take_damage(87 * damage_multiplier)
                        
                        if weapon.SELECTED_WEAPON == 'wrench':
                            max_tanks = 3 if player_buffs['speed'] >= 3 else 2
                            if len(player_special.active_tanks) < max_tanks:
                                player_special.active_tanks.append(special.TankEntity(pw.x, pw.y, player_special))
                                
                        if weapon.SELECTED_WEAPON in ['bomb', 'bomb1', 'bomb2']:
                            if getattr(pw, 'is_toxic', False): 
                                player_special.particle_sys.spawn_bomb2_explosion(pw.x, pw.y)
                                player_special.active_toxic_clouds.append(special.ToxicCloudEntity(pw.x, pw.y))
                
                # --- PHẦN NÀY LÀ FALLBACK VẪN ĐỂ LẠI THEO CLASS VŨ KHÍ GỐC ---
                elif pw.state == 'shooting' and pw.active_bullet:
                    if math.hypot(enemy.x - pw.active_bullet['x'], enemy.y - pw.active_bullet['y']) < enemy.radius + 8:
                        is_dead = enemy.take_damage(30 * damage_multiplier) 
                        pw.explosion = weapon.WeaponExplosion(pw.active_bullet['x'], pw.active_bullet['y'], 'gun')
                        pw.active_bullet = None
                        pw.state = 'orbit'
                        play_cached_sfx('hit')
                        
                elif pw.state == 'orbit' and dist_to_enemy < (enemy.radius + weapon_hit_radius):
                    if not hasattr(pw, 'last_orbit_hit_time'): pw.last_orbit_hit_time = 0
                    if current_time - pw.last_orbit_hit_time > 400:
                        is_dead = enemy.take_damage(15 * damage_multiplier)
                        orbit_hit_this_frame = True
                        
                if is_dead or enemy.health <= 0:
                    player.total_kills += 1
                    if player_buffs['dame'] > 0:
                        player.dame_buff_kills += 1
                        
                    if enemy.type == 'orange':
                        orange_explosions.append(OrangeExplosion(enemy.x, enemy.y, current_wave))
                    elif enemy.type == 'big' and current_wave >= 5:
                        for _ in range(2):
                            rx = enemy.x + random.randint(-25, 25)
                            ry = enemy.y + random.randint(-25, 25)
                            active_enemies.append(EnemyNor(rx, ry, game_assets['nor_frames'], wave=current_wave))
                            
                    if enemy in active_enemies: 
                        active_enemies.remove(enemy)
                    score_mult = 1.0 + (0.5 * player_buffs['coin'])
                    score.game_score.add_points(int(enemy.score_value * score_mult))

            if orbit_hit_this_frame:
                pw.last_orbit_hit_time = current_time

        # --- UPDATE HIỆU ỨNG NỔ CỦA ĐẠN SÚNG ---
        for wex in active_weapon_explosions[:]:
            if not wex.update():
                active_weapon_explosions.remove(wex)

        for ex in orange_explosions[:]:
            if ex.update(player):
                dmg = 20 * (0.95 ** player_buffs['shield']) 
                if shield_hp > 0: shield_hp -= dmg
                else: 
                    player.health -= dmg
            if ex.life <= 0: orange_explosions.remove(ex)
            
        for kex in kaboom_explosions[:]:
            kex.update(active_enemies)
            if kex.life <= 0: kaboom_explosions.remove(kex)

        player_special.update(active_enemies)

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
                    screen.blit(sh_img, sh_img.get_rect(center=(obs.centerx, obs.bottom - 2)))
            for obs, key in zip(all_rects, all_keys):
                screen.blit(game_assets[key], obs.topleft)
                
        if mode_name == 'MEDIUM':
            for danger in active_dangers: danger.draw(screen, camera_x, camera_y)
        elif mode_name == 'ENDLESS':
            for lava in active_lavas: lava.draw_shadow(screen, camera_x, camera_y)
            for lava in active_lavas: lava.draw(screen, camera_x, camera_y)
            for ent in active_endless_entities: ent.draw_shadow(screen, camera_x, camera_y)
            for ent in active_endless_entities: ent.draw(screen, camera_x, camera_y)
            for danger in active_dangers: danger.draw(screen, camera_x, camera_y)

        for enemy in active_enemies: enemy.draw(screen, camera_x, camera_y)
        for proj in enemy_projectiles: proj.draw(screen, camera_x, camera_y)
        for ex in orange_explosions: ex.draw(screen, camera_x, camera_y)
        for kex in kaboom_explosions: kex.draw(screen, camera_x, camera_y)
        
        if game_state == "PLAYING" and player_buffs['magic'] > 0:
            magic_orb.update_and_draw(player, active_enemies, screen, camera_x, camera_y, player_buffs['magic'], damage_multiplier)

        player.draw(screen, draw_player_x, draw_player_y, game_assets['font_level_diff'])
        if player_poison_time_left > 0 and (current_time // 100) % 2 == 0:
            poison_flash = pygame.Surface((player.radius * 2.5, player.radius * 2.5), pygame.SRCALPHA)
            pygame.draw.circle(poison_flash, (0, 255, 0, 100), (player.radius*1.25, player.radius*1.25), player.radius*1.25)
            screen.blit(poison_flash, (draw_player_x - player.radius*1.25, draw_player_y - player.radius*1.25))

        # --- VẼ BÓNG SHIELD & GAI BẢO VỆ (NẾU CÒN GIÁP) ---
        if shield_hp > 0:
            shield_surf = pygame.Surface((player.radius * 4, player.radius * 4), pygame.SRCALPHA)
            center_s = player.radius * 2
            
            # Bóng mờ màu xanh dương trong suốt
            pygame.draw.circle(shield_surf, (50, 150, 255, 70), (center_s, center_s), player.radius * 1.4)
            pygame.draw.circle(shield_surf, (100, 200, 255, 150), (center_s, center_s), player.radius * 1.4, 2)
            
            # Gai đẩy lùi nếu level >= 2
            if player_buffs['shield'] >= 2:
                num_spikes = 6 + player_buffs['shield'] * 2
                t = current_time / 500.0
                for i in range(num_spikes):
                    angle = t + i * (2 * math.pi / num_spikes)
                    inner_r = player.radius * 1.4
                    outer_r = player.radius * 1.8
                    x1 = center_s + math.cos(angle - 0.15) * inner_r
                    y1 = center_s + math.sin(angle - 0.15) * inner_r
                    x2 = center_s + math.cos(angle + 0.15) * inner_r
                    y2 = center_s + math.sin(angle + 0.15) * inner_r
                    x3 = center_s + math.cos(angle) * outer_r
                    y3 = center_s + math.sin(angle) * outer_r
                    pygame.draw.polygon(shield_surf, (100, 200, 255, 180), [(x1,y1), (x2,y2), (x3,y3)])
                    
            screen.blit(shield_surf, (draw_player_x - center_s, draw_player_y - center_s))

        # VẼ ĐẠN CỦA SÚNG KHI BẮN BẰNG CLICK CHUỘT
        for b in player_extra_bullets:
            if b.get('delay', 0) > 0:
                continue  # Nếu đạn đang chờ delay burst thì chưa vẽ ra
            bx = int(b['x'] - camera_x)
            by = int(b['y'] - camera_y)
            tracer_x = bx - b['vx'] * 0.5
            tracer_y = by - b['vy'] * 0.5
            pygame.draw.line(screen, (255, 200, 50), (tracer_x, tracer_y), (bx, by), 4)
            pygame.draw.rect(screen, (255, 215, 0), (bx - 4, by - 4, 8, 8))
            pygame.draw.rect(screen, (255, 255, 255), (bx - 2, by - 2, 4, 4))
            
        # VẼ HIỆU ỨNG NỔ CỦA ĐẠN SÚNG NGAY LẬP TỨC
        for wex in active_weapon_explosions:
            wex.draw(screen, camera_x, camera_y)

        for pw in player_weapons: pw.draw(screen, camera_x, camera_y)
        player_special.draw(screen, camera_x, camera_y)
        
        if mode_name == 'ENDLESS' and player_in_lava and (pygame.time.get_ticks() // 100) % 2 == 0:  
            orange_flash = pygame.Surface((player.radius * 2, player.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(orange_flash, (255, 110, 0, 150), (player.radius, player.radius), player.radius)
            screen.blit(orange_flash, (draw_player_x - player.radius, draw_player_y - player.radius))
        
        draw_health_bar(screen, 20, 20, player.health, player.max_health, game_assets['font_level_diff'], shield_hp, 50 * player_buffs['shield'])
        score.game_score.draw_in_game(screen, game_assets['font_level_diff'], 20, 60)
        
        buff_start_x = 20
        buff_y = 90
        for b_name, b_lvl in player_buffs.items():
            if b_lvl > 0:
                img = buff_images.get(b_name)
                if img:
                    small_img = pygame.transform.smoothscale(img, (32, 32))
                    screen.blit(small_img, (buff_start_x, buff_y))
                    
                    pygame.draw.circle(screen, BLACK, (buff_start_x + 32, buff_y), 9)
                    pygame.draw.circle(screen, (255, 215, 0), (buff_start_x + 32, buff_y), 9, 1)
                    
                    lvl_font = pygame.font.SysFont(None, 18, bold=True)
                    text_obj = lvl_font.render(str(b_lvl), True, WHITE)
                    screen.blit(text_obj, text_obj.get_rect(center=(buff_start_x + 32, buff_y)))
                    
                    if b_name == 'dame':
                        kill_font = pygame.font.SysFont(None, 15, bold=True)
                        bonus_pct = player.dame_buff_kills * 0.25 
                        kill_text = kill_font.render(f"+{bonus_pct:g}%", True, (255, 200, 50))
                        
                        text_rect = kill_text.get_rect(midtop=(buff_start_x + 16, buff_y + 35))
                        bg_rect = text_rect.inflate(4, 4)
                        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect, border_radius=3)
                        screen.blit(kill_text, text_rect)
                    
                    buff_start_x += 42 

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
                    play_cached_sfx('buffsound')
                    
                    if player_buffs[buff_name] < 3: player_buffs[buff_name] += 1
                    
                    if buff_name == 'health': 
                        player.max_health = base_max_health + (50 * player_buffs['health'])
                        player.health += 50 
                    elif buff_name == 'speed': 
                        player.speed = 250 + (30 * player_buffs['speed'])
                    elif buff_name == 'kaboom':
                        player.kaboom_level = player_buffs['kaboom']
                    
                    max_shield = 50 * player_buffs['shield']
                    shield_hp = max_shield
                    
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
        
        if player.health <= 0 and running:
            pygame.mixer.music.stop()
            play_cached_sfx('lose')
            running = False
        
        pygame.display.update()

    score.game_score.save_high_score()
    
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(os.path.join('sound', 'menusound.mp3'))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except:
        pass
        
    transition_func(clock)