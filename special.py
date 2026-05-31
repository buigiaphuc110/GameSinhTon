import pygame
import math
import os
import random

# ==========================================
# CACHE HÌNH ẢNH VÀ TẠO HÌNH BẰNG CODE
# ==========================================
SPECIAL_ASSETS = {
    'flower2_img': None,
    'subflower_img': None,
    'tank_img': None,
    'rocket_img': None
}

def init_special_assets():
    if SPECIAL_ASSETS['flower2_img'] is not None:
        return

    # 1. Tải ảnh Hoa Lớn (Flower2)
    flower2_path = os.path.join('specialskill', 'flower2.png')
    try:
        img = pygame.image.load(flower2_path).convert_alpha()
        SPECIAL_ASSETS['flower2_img'] = pygame.transform.scale(img, (70, 70))
    except:
        dummy = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(dummy, (255, 50, 50), (35, 35), 25)
        SPECIAL_ASSETS['flower2_img'] = dummy

    # 2. Tải ảnh Hoa Nhỏ (Subflower)
    try:
        img = pygame.image.load(os.path.join('weapon', 'flower1.png')).convert_alpha()
        SPECIAL_ASSETS['subflower_img'] = pygame.transform.scale(img, (48, 48))
    except:
        dummy_sub = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(dummy_sub, (255, 105, 180), (24, 24), 15)
        SPECIAL_ASSETS['subflower_img'] = dummy_sub

    # 3. Tải ảnh Xe Tăng (Tank)
    try:
        raw_tank = pygame.image.load(os.path.join('specialskill', 'tank.png')).convert_alpha()
        rotated_tank = pygame.transform.rotate(raw_tank, 90)
        SPECIAL_ASSETS['tank_img'] = pygame.transform.scale(rotated_tank, (60, 60))
    except:
        dummy_tank = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.rect(dummy_tank, (60, 110, 60), (3, 10, 45, 40), border_radius=6)
        pygame.draw.rect(dummy_tank, (40, 80, 40), (15, 18, 24, 24), border_radius=3)
        pygame.draw.rect(dummy_tank, (30, 60, 30), (35, 26, 22, 8))
        SPECIAL_ASSETS['tank_img'] = dummy_tank

    # 4. Vẽ Tên Lửa (Rocket) bằng code dự phòng
    rocket = pygame.Surface((30, 14), pygame.SRCALPHA)
    pygame.draw.rect(rocket, (200, 200, 200), (8, 3, 16, 8))
    pygame.draw.polygon(rocket, (255, 50, 50), [(24, 3), (24, 11), (30, 7)])
    pygame.draw.polygon(rocket, (255, 150, 0), [(8, 3), (2, 0), (4, 3)])
    pygame.draw.polygon(rocket, (255, 150, 0), [(8, 11), (2, 14), (4, 11)])
    pygame.draw.circle(rocket, (255, 200, 0), (3, 7), 3)
    SPECIAL_ASSETS['rocket_img'] = rocket


# ==========================================
# QUẢN LÝ HẠT PARTICLE
# ==========================================
class ParticleManager:
    def __init__(self):
        self.particles = []

    def spawn_smoke(self, x, y):
        for _ in range(5):
            self.particles.append({
                'x': x + random.uniform(-5, 5),
                'y': y + random.uniform(-5, 5),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'radius': random.uniform(3, 6),
                'color': (150, 150, 150),
                'life': 255,
                'decay': random.uniform(15, 25),
                'type': 'smoke'
            })

    def spawn_explosion(self, x, y):
        colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (100, 100, 100)]
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'radius': random.uniform(2, 7),
                'color': random.choice(colors),
                'life': 255,
                'decay': random.uniform(10, 20),
                'type': 'spark'
            })
            
    def spawn_flower1_explosion(self, x, y):
        flower_colors = [(255, 105, 180), (255, 192, 203), (220, 20, 60), (255, 240, 245)]
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'radius': random.uniform(2, 5),
                'color': random.choice(flower_colors),
                'life': 255,
                'decay': random.uniform(12, 22),
                'type': 'spark'
            })

    def spawn_flower2_explosion(self, x, y):
        flower2_colors = [(255, 20, 147), (255, 105, 180), (255, 192, 203), (220, 20, 60), (255, 255, 255), (255, 215, 0)]
        for _ in range(70):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(4, 13)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'radius': random.uniform(4, 11),
                'color': random.choice(flower2_colors),
                'life': 255,
                'decay': random.uniform(6, 13),
                'type': 'spark'
            })

    def spawn_bomb2_explosion(self, x, y):
        bomb2_colors = [(10, 50, 10), (35, 130, 35), (100, 255, 80), (170, 255, 0), (15, 15, 15), (5, 5, 5)]
        for _ in range(55): 
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 11) 
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'radius': random.uniform(4, 11),
                'color': random.choice(bomb2_colors),
                'life': 255,
                'decay': random.uniform(7, 13),
                'type': 'spark'
            })

    def update(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= p['decay']
            
            if p['type'] == 'smoke': 
                p['radius'] += 0.2
            else:
                p['radius'] -= 0.1
                p['vx'] *= 0.9
                p['vy'] *= 0.9
                
            if p['life'] <= 0 or p['radius'] <= 0: 
                self.particles.remove(p)

    def draw(self, surface, camera_x, camera_y):
        for p in self.particles:
            if p['life'] > 0 and p['radius'] > 0:
                surf = pygame.Surface((int(p['radius']*2), int(p['radius']*2)), pygame.SRCALPHA)
                r, g, b = p['color']
                pygame.draw.circle(surf, (r, g, b, max(0, int(p['life']))), (int(p['radius']), int(p['radius'])), int(p['radius']))
                surface.blit(surf, (int(p['x'] - p['radius'] - camera_x), int(p['y'] - p['radius'] - camera_y)))


# ==========================================
# CÔNG CỤ VA CHẠM VÀ GÂY SÁT THƯƠNG
# ==========================================
def heal_player(player, amount):
    """Hàm bổ sung hỗ trợ hồi máu an toàn cho player."""
    try:
        if hasattr(player, 'heal'):
            player.heal(amount)
        elif hasattr(player, 'health'):
            player.health += amount
            if hasattr(player, 'max_health'):
                player.health = min(player.health, player.max_health)
        elif hasattr(player, 'hp'):
            player.hp += amount
            if hasattr(player, 'max_hp'):
                player.hp = min(player.hp, player.max_hp)
    except Exception:
        pass

def check_collision_flexible(rect, projectile_x, projectile_y, enemy):
    if hasattr(enemy, 'rect') and isinstance(enemy.rect, pygame.Rect): 
        return rect.colliderect(enemy.rect)
    else:
        ex = getattr(enemy, 'x', None)
        ey = getattr(enemy, 'y', None)
        if ex is not None and ey is not None: 
            return math.hypot(ex - projectile_x, ey - projectile_y) < 25
    return False

def deal_damage(entity, amount):
    try:
        if hasattr(entity, 'take_damage'): 
            entity.take_damage(amount)
        elif hasattr(entity, 'health'): 
            entity.health -= amount
        elif hasattr(entity, 'hp'): 
            entity.hp -= amount
    except Exception: 
        pass


# ==========================================
# CÁC CLASS KỸ NĂNG ĐẶC BIỆT
# ==========================================
class ToxicCloudEntity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 3000
        self.last_damage_tick = 0
        self.damage_interval = 250
        
        self.cloud_puffs = []
        for _ in range(24):
            self.cloud_puffs.append({
                'rel_x': random.uniform(-60, 60),
                'rel_y': random.uniform(-60, 60),
                'size': random.randint(12, 26),
                'color': random.choice([
                    (30, 110, 30, 140),  
                    (70, 200, 70, 110),  
                    (15, 60, 15, 160),   
                    (10, 15, 10, 120)    
                ]),
                'wobble_speed': random.uniform(0.003, 0.007),
                'seed': random.uniform(0, 100)
            })

    def update(self, entities):
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time > self.duration: 
            return False
            
        if current_time - self.last_damage_tick > self.damage_interval:
            self.last_damage_tick = current_time
            for e in entities:
                ex = getattr(e, 'x', None)
                ey = getattr(e, 'y', None)
                if ex is not None and ey is not None and math.hypot(ex - self.x, ey - self.y) < 85: 
                    deal_damage(e, 6) 
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        current_time = pygame.time.get_ticks()
        fade_alpha = max(0.0, 1.0 - ((current_time - self.spawn_time) / self.duration))
        
        for p in self.cloud_puffs:
            wave = math.sin(current_time * p['wobble_speed'] + p['seed']) * 5
            px = int(self.x + p['rel_x'] - camera_x + wave)
            py = int(self.y + p['rel_y'] - camera_y + wave * 0.5)
            
            current_size = max(2, int(p['size'] * (0.5 + 0.5 * fade_alpha)))
            puff_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
            
            r, g, b, base_a = p['color']
            final_a = max(0, int(base_a * fade_alpha))
            
            pygame.draw.circle(puff_surf, (r, g, b, final_a), (current_size, current_size), current_size)
            surface.blit(puff_surf, (px - current_size, py - current_size))


class RocketEntity:
    def __init__(self, x, y, target_angle, manager):
        self.x = x
        self.y = y
        self.manager = manager
        self.image = SPECIAL_ASSETS['rocket_img']
        self.rect = self.image.get_rect()
        
        speed = 15.0
        self.vx = math.cos(target_angle) * speed
        self.vy = math.sin(target_angle) * speed
        self.display_angle = -math.degrees(target_angle)
        
    def update(self, entities):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        
        self.manager.particle_sys.spawn_smoke(self.x - self.vx*1.2, self.y - self.vy*1.2)
        
        for e in entities:
            if check_collision_flexible(self.rect, self.x, self.y, e):
                self.manager.particle_sys.spawn_explosion(self.x, self.y)
                deal_damage(e, 35) 
                return False 
                
        if self.x < -2000 or self.x > 5000 or self.y < -2000 or self.y > 5000: 
            return False
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        rotated_image = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(rotated_image, rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))


class TankEntity:
    def __init__(self, x, y, manager):
        self.x = x
        self.y = y
        self.manager = manager
        self.image = SPECIAL_ASSETS['tank_img']
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 10000 
        self.display_angle = random.uniform(0, 360) 
        self.move_speed = 2.5
        self.last_shot_time = 0
        self.fire_rate = 800
        
        self.idle_speed = 0.5
        self.idle_state = 'rotate'
        self.idle_timer = pygame.time.get_ticks()
        self.idle_duration = random.randint(1500, 3500)
        self.idle_spin_dir = 0.5
        
        self.shadow_surface = pygame.Surface((60, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow_surface, (0, 0, 0, 90), (0, 0, 60, 18))
        
    def get_closest_enemy(self, entities):
        closest = None
        min_dist = 999999
        for e in entities:
            ex = getattr(e, 'x', None)
            ey = getattr(e, 'y', None)
            if ex is not None and ey is not None:
                dist = math.hypot(ex - self.x, ey - self.y)
                if dist < min_dist: 
                    min_dist = dist
                    closest = e
        return closest, min_dist

    def update(self, entities):
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time > self.duration:
            self.manager.particle_sys.spawn_explosion(self.x, self.y)
            return False
            
        target, dist = self.get_closest_enemy(entities)
        if target:
            tx = getattr(target, 'x', self.x)
            ty = getattr(target, 'y', self.y)
            target_angle = math.atan2(ty - self.y, tx - self.x)
            self.display_angle = -math.degrees(target_angle)
            
            if dist > 200:
                self.x += math.cos(target_angle) * self.move_speed
                self.y += math.sin(target_angle) * self.move_speed
                
            if current_time - self.last_shot_time > self.fire_rate:
                self.last_shot_time = current_time
                barrel_x = self.x + math.cos(target_angle) * 30
                barrel_y = self.y + math.sin(target_angle) * 30
                self.manager.active_rockets.append(RocketEntity(barrel_x, barrel_y, target_angle, self.manager))
        else:
            if current_time - self.idle_timer > self.idle_duration:
                self.idle_timer = current_time
                self.idle_duration = random.randint(1500, 3500) 
                self.idle_state = random.choice(['rotate', 'wander'])
                self.idle_spin_dir = random.choice([-0.8, 0.8]) 
                
            if self.idle_state == 'rotate': 
                self.display_angle += self.idle_spin_dir
            elif self.idle_state == 'wander':
                rad_angle = math.radians(-self.display_angle)
                self.x += math.cos(rad_angle) * self.idle_speed
                self.y += math.sin(rad_angle) * self.idle_speed
                
        self.rect.center = (int(self.x), int(self.y))
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        shadow_rect = self.shadow_surface.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y + 20)))
        surface.blit(self.shadow_surface, shadow_rect)
        rotated_image = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(rotated_image, rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))


class SubFlowerEntity:
    def __init__(self, x, y, angle_rad, manager):
        self.x = x
        self.y = y
        self.manager = manager
        self.image = SPECIAL_ASSETS['subflower_img']
        self.rect = self.image.get_rect()
        self.vx = math.cos(angle_rad) * 10.0
        self.vy = math.sin(angle_rad) * 10.0
        self.display_angle = 0
        self.state = 'moving'
        
    def update(self, entities):
        if self.state == 'moving':
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.92
            self.vy *= 0.92
            self.display_angle = (self.display_angle + 18) % 360
            self.rect.center = (int(self.x), int(self.y))
            
            hit = False
            for e in entities:
                if check_collision_flexible(self.rect, self.x, self.y, e):
                    deal_damage(e, 30) 
                    hit = True
                    # CƠ CHẾ MỚI: Hồi 1 máu cho player khi ném trúng kẻ địch (Hoa nhỏ Flower1)
                    if self.manager and self.manager.player:
                        heal_player(self.manager.player, 1)
                    break
                    
            if hit or math.hypot(self.vx, self.vy) < 1.0:
                self.state = 'exploded'
                if self.manager: 
                    self.manager.particle_sys.spawn_flower1_explosion(self.x, self.y)
                return False
        return True 
        
    def draw(self, surface, cx=0, cy=0):
        if self.state == 'moving':
            ri = pygame.transform.rotate(self.image, self.display_angle)
            surface.blit(ri, ri.get_rect(center=(int(self.x - cx), int(self.y - cy))))


class Flower2Entity:
    def __init__(self):
        self.image = SPECIAL_ASSETS['flower2_img']
        self.rect = self.image.get_rect()
        self.state = 'orbit'
        self.angle = 180
        self.display_angle = 0
        self.x, self.y, self.vx, self.vy = 0, 0, 0, 0
        self.manager_ref = None
        self.last_orbit_hit_time = 0
        
    def throw(self, tx, ty, sx, sy, manager):
        if self.state == 'orbit':
            self.state = 'thrown'
            self.manager_ref = manager
            self.x, self.y = sx, sy
            dx, dy = tx - sx, ty - sy
            d = math.hypot(dx, dy)
            if d > 0: 
                self.vx = (dx/d) * 20
                self.vy = (dy/d) * 20
            
    def update(self, px, py, entities):
        if self.state == 'orbit':
            self.angle = (self.angle + 6) % 360
            self.x = px + math.cos(math.radians(self.angle)) * 80
            self.y = py + math.sin(math.radians(self.angle)) * 80
            self.display_angle = -self.angle - 45
            self.rect.center = (int(self.x), int(self.y))
            
            current_time = pygame.time.get_ticks()
            if current_time - self.last_orbit_hit_time > 400:
                hit_anything = False
                for e in entities:
                    if check_collision_flexible(self.rect, self.x, self.y, e):
                        deal_damage(e, 15)
                        hit_anything = True
                if hit_anything: 
                    self.last_orbit_hit_time = current_time
                    
        elif self.state == 'thrown':
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.94
            self.vy *= 0.94
            self.display_angle = (self.display_angle + 22) % 360
            self.rect.center = (int(self.x), int(self.y))
            
            hit = False
            for e in entities:
                if check_collision_flexible(self.rect, self.x, self.y, e):
                    deal_damage(e, 65) 
                    hit = True
                    # CƠ CHẾ MỚI: Hồi 1 máu cho player khi ném trúng kẻ địch (Hoa lớn Flower2)
                    if self.manager_ref and self.manager_ref.player:
                        heal_player(self.manager_ref.player, 1)
                    break
                    
            if hit or math.hypot(self.vx, self.vy) < 1.0:
                if self.manager_ref:
                    self.manager_ref.particle_sys.spawn_flower2_explosion(self.x, self.y)
                    ba = math.atan2(self.vy, self.vx)
                    for a in [ba - math.pi/4, ba, ba + math.pi/4]:
                        self.manager_ref.sub_flowers.append(SubFlowerEntity(self.x, self.y, a, self.manager_ref))
                return False
        return True
        
    def draw(self, surface, cx=0, cy=0):
        ri = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(ri, ri.get_rect(center=(int(self.x - cx), int(self.y - cy))))


# ==========================================
# CLASS QUẢN LÝ TỔNG (QUẢN LÝ KỸ NĂNG)
# ==========================================
class SpecialSkill:
    def __init__(self, player=None):
        self.player = player
        init_special_assets()
        self.flower_throw_count = 0
        self.active_flower2 = None
        self.sub_flowers = []
        
        # Đăng ký player sang module weapon để đồng bộ cơ chế hồi máu và buff Kaboom diện rộng
        import weapon
        weapon.CURRENT_PLAYER = player
        
        self.active_tanks = []
        self.active_rockets = []
        self.active_toxic_clouds = []
        
        self.particle_sys = ParticleManager() 

    def on_player_throw_weapon(self, weapon_name, target_x, target_y, start_x, start_y):
        if self.active_flower2 and self.active_flower2.state == 'orbit':
            self.active_flower2.throw(target_x, target_y, start_x, start_y, self)
            return True 
            
        if weapon_name == 'flower':
            self.flower_throw_count += 1
            if self.flower_throw_count >= 3 and not self.active_flower2:
                self.flower_throw_count = 0
                self.active_flower2 = Flower2Entity() 
                
        return False

    def trigger_random_skill(self):
        pass

    def trigger(self, player_x, player_y):
        pass

    def update(self, *args):
        # Luôn cập nhật và bảo đảm reference người chơi mới nhất cho weapon module
        import weapon
        if self.player:
            weapon.CURRENT_PLAYER = self.player

        if len(args) == 1:
            entities = args[0]
            px = self.player.x if self.player else 0
            py = self.player.y if self.player else 0
        elif len(args) == 3:
            px, py, entities = args
        else:
            entities = []
            px, py = 0, 0

        if self.active_flower2:
            if not self.active_flower2.update(px, py, entities):
                self.active_flower2 = None 
                
        for sub in self.sub_flowers[:]:
            if not sub.update(entities): 
                self.sub_flowers.remove(sub)

        for tank in self.active_tanks[:]:
            if not tank.update(entities): 
                self.active_tanks.remove(tank)
                
        for rocket in self.active_rockets[:]:
            if not rocket.update(entities): 
                self.active_rockets.remove(rocket)
            
        for tc in self.active_toxic_clouds[:]:
            if not tc.update(entities): 
                self.active_toxic_clouds.remove(tc)
            
        self.particle_sys.update()

    def draw(self, surface, camera_x=0, camera_y=0):
        for tc in self.active_toxic_clouds: 
            tc.draw(surface, camera_x, camera_y)
        
        if self.active_flower2: 
            self.active_flower2.draw(surface, camera_x, camera_y)
        for sub in self.sub_flowers: 
            sub.draw(surface, camera_x, camera_y)
        
        for tank in self.active_tanks: 
            tank.draw(surface, camera_x, camera_y)
        for rocket in self.active_rockets: 
            rocket.draw(surface, camera_x, camera_y)
            
        self.particle_sys.draw(surface, camera_x, camera_y)


# Đảm bảo tính tương thích với mọi cách gọi tên Class từ các file khác
SpecialSkillManager = SpecialSkill