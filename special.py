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
    'flower2_ex_frames': [],
    'subflower_ex_frames': [],
    'wrench_img': None,  
    'tank_img': None,
    'rocket_img': None,
    'bomb_normal_img': None,   # Bom thường (80%)
    'bomb_special_img': None,  # Bom độc (20%)
    'bomb_orbit_img': None     # THÊM: Bom hiển thị lúc xoay (bomb1)
}

def init_special_assets():
    if SPECIAL_ASSETS['flower2_img'] is not None:
        return

    flower2_path = os.path.join('specialskill', 'flower2.png')
    try:
        SPECIAL_ASSETS['flower2_img'] = pygame.transform.scale(pygame.image.load(flower2_path).convert_alpha(), (70, 70))
    except:
        dummy = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(dummy, (255, 50, 50), (35, 35), 25)
        SPECIAL_ASSETS['flower2_img'] = dummy

    try:
        SPECIAL_ASSETS['subflower_img'] = pygame.transform.scale(pygame.image.load(os.path.join('weapon', 'flower1.png')).convert_alpha(), (48, 48))
    except:
        dummy_sub = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(dummy_sub, (255, 105, 180), (24, 24), 15)
        SPECIAL_ASSETS['subflower_img'] = dummy_sub

    try:
        SPECIAL_ASSETS['wrench_img'] = pygame.transform.scale(pygame.image.load(os.path.join('weapon', 'wrench.png')).convert_alpha(), (35, 35))
    except:
        dummy_wr = pygame.Surface((35, 35), pygame.SRCALPHA)
        pygame.draw.rect(dummy_wr, (160, 160, 160), (12, 4, 10, 26))
        pygame.draw.circle(dummy_wr, (130, 130, 130), (17, 8), 8, 3)
        SPECIAL_ASSETS['wrench_img'] = dummy_wr

    try:
        raw_tank = pygame.image.load(os.path.join('specialskill', 'tank.png')).convert_alpha()
        corrected_tank = pygame.transform.rotate(raw_tank, 90)
        SPECIAL_ASSETS['tank_img'] = pygame.transform.scale(corrected_tank, (60, 60))
    except:
        dummy_tank = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.rect(dummy_tank, (60, 110, 60), (3, 10, 45, 40), border_radius=6)
        pygame.draw.rect(dummy_tank, (40, 80, 40), (15, 18, 24, 24), border_radius=3)
        pygame.draw.rect(dummy_tank, (30, 60, 30), (35, 26, 22, 8))
        SPECIAL_ASSETS['tank_img'] = dummy_tank

    # TẠO ROCKET
    rocket = pygame.Surface((30, 14), pygame.SRCALPHA)
    pygame.draw.rect(rocket, (200, 200, 200), (8, 3, 16, 8))
    pygame.draw.polygon(rocket, (255, 50, 50), [(24, 3), (24, 11), (30, 7)])
    pygame.draw.polygon(rocket, (255, 150, 0), [(8, 3), (2, 0), (4, 3)])
    pygame.draw.polygon(rocket, (255, 150, 0), [(8, 11), (2, 14), (4, 11)])
    pygame.draw.circle(rocket, (255, 200, 0), (3, 7), 3)
    SPECIAL_ASSETS['rocket_img'] = rocket

    # BOM THƯỜNG DÙNG ẢNH BOMB2 TRONG WEAPON
    try:
        SPECIAL_ASSETS['bomb_normal_img'] = pygame.transform.scale(pygame.image.load(os.path.join('weapon', 'bomb2.png')).convert_alpha(), (35, 35))
    except:
        dummy_b1 = pygame.Surface((35, 35), pygame.SRCALPHA)
        pygame.draw.circle(dummy_b1, (55, 55, 55), (17, 17), 12)
        pygame.draw.rect(dummy_b1, (220, 60, 60), (16, 2, 3, 5)) 
        SPECIAL_ASSETS['bomb_normal_img'] = dummy_b1

    # BOM TỶ LỆ 20% DÙNG ẢNH BOMB2 TRONG SPECIALSKILL
    try:
        SPECIAL_ASSETS['bomb_special_img'] = pygame.transform.scale(pygame.image.load(os.path.join('specialskill', 'bomb2.png')).convert_alpha(), (42, 42))
    except:
        dummy_b2 = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.circle(dummy_b2, (20, 100, 20), (21, 21), 15)
        pygame.draw.circle(dummy_b2, (90, 240, 90), (21, 21), 15, 2)
        pygame.draw.rect(dummy_b2, (150, 255, 50), (20, 2, 3, 5))  
        SPECIAL_ASSETS['bomb_special_img'] = dummy_b2

    # THÊM THEO YÊU CẦU: ẢNH BOMB1 TRONG WEAPON ĐỂ HIỆN KHI XOAY
    try:
        SPECIAL_ASSETS['bomb_orbit_img'] = pygame.transform.scale(pygame.image.load(os.path.join('weapon', 'bomb1.png')).convert_alpha(), (36, 36))
    except:
        dummy_bo = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(dummy_bo, (80, 80, 90), (18, 18), 12)
        pygame.draw.circle(dummy_bo, (240, 180, 30), (18, 18), 5)
        SPECIAL_ASSETS['bomb_orbit_img'] = dummy_bo

# ==========================================
# QUẢN LÝ HẠT PARTICLE PHÂN RÃ
# ==========================================
class ParticleManager:
    def __init__(self):
        self.particles = []

    def spawn_smoke(self, x, y):
        self.particles.append({
            'x': x + random.uniform(-5, 5), 'y': y + random.uniform(-5, 5),
            'vx': random.uniform(-0.5, 0.5), 'vy': random.uniform(-0.5, 0.5),
            'radius': random.uniform(3, 6), 'color': (150, 150, 150),
            'life': 255, 'decay': random.uniform(15, 25), 'type': 'smoke'
        })

    def spawn_explosion(self, x, y):
        colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (100, 100, 100), (30, 30, 30)]
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'radius': random.uniform(2, 7), 'color': random.choice(colors),
                'life': 255, 'decay': random.uniform(10, 20), 'type': 'spark'
            })
            
    # HIỆU ỨNG NỔ CỦA FLOWER 1 (Dùng khi cánh hoa nhỏ nổ ra)
    def spawn_flower1_explosion(self, x, y):
        flower_colors = [(255, 105, 180), (255, 192, 203), (220, 20, 60), (255, 240, 245)]
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'radius': random.uniform(2, 5), 
                'color': random.choice(flower_colors),
                'life': 255, 'decay': random.uniform(12, 22), 'type': 'spark'
            })

    # THÊM THEO YÊU CẦU: HIỆU ỨNG NỔ FLOWER 2 TO VÀ HOÀNH TRÁNG HƠN
    def spawn_flower2_explosion(self, x, y):
        flower2_colors = [(255, 20, 147), (255, 105, 180), (255, 192, 203), (220, 20, 60), (255, 255, 255), (255, 215, 0)]
        for _ in range(70):  # Tăng lên 70 hạt hoành tráng
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(4, 13)  # Tốc độ bay mạnh và xa hơn
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'radius': random.uniform(4, 11),  # Hạt vụn to rõ nét hơn
                'color': random.choice(flower2_colors),
                'life': 255, 'decay': random.uniform(6, 13), 'type': 'spark'
            })

    def spawn_bomb2_explosion(self, x, y):
        bomb2_colors = [(10, 50, 10), (35, 130, 35), (100, 255, 80), (170, 255, 0), (15, 15, 15), (5, 5, 5)]
        for _ in range(55): 
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 11) 
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'radius': random.uniform(4, 11), 
                'color': random.choice(bomb2_colors),
                'life': 255, 'decay': random.uniform(7, 13), 'type': 'spark'
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
# CHECK VA CHẠM LINH HOẠT
# ==========================================
def check_collision_flexible(rect, projectile_x, projectile_y, enemy):
    if hasattr(enemy, 'rect') and isinstance(enemy.rect, pygame.Rect):
        return rect.colliderect(enemy.rect)
    else:
        ex = getattr(enemy, 'x', None)
        ey = getattr(enemy, 'y', None)
        if ex is not None and ey is not None:
            return math.hypot(ex - projectile_x, ey - projectile_y) < 25
    return False

# ==========================================
# CLASS KHÓI ĐỘC TỒN TẠI 3 GIÂY (STYLE PIXEL)
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
                ex = e.rect.centerx if hasattr(e, 'rect') else getattr(e, 'x', None)
                ey = e.rect.centery if hasattr(e, 'rect') else getattr(e, 'y', None)
                if ex is not None and ey is not None:
                    if math.hypot(ex - self.x, ey - self.y) < 85: 
                        if hasattr(e, 'take_damage'): e.take_damage(6)
                        elif hasattr(e, 'hp'): e.hp -= 6
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        current_time = pygame.time.get_ticks()
        life_ratio = (current_time - self.spawn_time) / self.duration
        fade_alpha = 1.0 - life_ratio 
        
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

# ==========================================
# CLASS PROJECTILE BOM THƯỜNG
# ==========================================
class BombProjectileEntity:
    def __init__(self, start_x, start_y, target_x, target_y, is_special_bomb, manager):
        self.x, self.y, self.manager = start_x, start_y, manager
        self.is_special_bomb = is_special_bomb
        self.image = SPECIAL_ASSETS['bomb_special_img'] if is_special_bomb else SPECIAL_ASSETS['bomb_normal_img']
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        
        dx, dy = target_x - start_x, target_y - start_y
        self.max_dist = math.hypot(dx, dy)
        self.dist_traveled = 0
        speed = 13.0
        self.vx = (dx / self.max_dist) * speed if self.max_dist > 0 else speed
        self.vy = (dy / self.max_dist) * speed if self.max_dist > 0 else 0
        self.display_angle = 0
        self.spin_speed = 14

    def update(self, entities):
        self.x += self.vx
        self.y += self.vy
        self.dist_traveled += math.hypot(self.vx, self.vy)
        self.display_angle = (self.display_angle + self.spin_speed) % 360
        self.rect.center = (int(self.x), int(self.y))
        
        if random.random() < 0.3:
            self.manager.particle_sys.spawn_smoke(self.x, self.y)

        hit = any(check_collision_flexible(self.rect, self.x, self.y, e) for e in entities)
        if hit or self.dist_traveled >= self.max_dist:
            if self.is_special_bomb:
                self.manager.particle_sys.spawn_bomb2_explosion(self.x, self.y)
                self.manager.active_toxic_clouds.append(ToxicCloudEntity(self.x, self.y))
                for e in entities:
                    ex = e.rect.centerx if hasattr(e, 'rect') else getattr(e, 'x', None)
                    ey = e.rect.centery if hasattr(e, 'rect') else getattr(e, 'y', None)
                    if ex is not None and ey is not None:
                        if math.hypot(ex - self.x, ey - self.y) < 100:
                            if hasattr(e, 'take_damage'): e.take_damage(75)
                            elif hasattr(e, 'hp'): e.hp -= 75
            else:
                self.manager.particle_sys.spawn_explosion(self.x, self.y)
                for e in entities:
                    ex = e.rect.centerx if hasattr(e, 'rect') else getattr(e, 'x', None)
                    ey = e.rect.centery if hasattr(e, 'rect') else getattr(e, 'y', None)
                    if ex is not None and ey is not None:
                        if math.hypot(ex - self.x, ey - self.y) < 60:
                            if hasattr(e, 'take_damage'): e.take_damage(40)
                            elif hasattr(e, 'hp'): e.hp -= 40
            return False
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        rotated_image = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(rotated_image, rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))

# ==========================================
# THÊM THEO YÊU CẦU: CLASS QUẢ BOM XOAY (BOMB ORBIT)
# ==========================================
class BombOrbitEntity:
    def __init__(self):
        self.image = SPECIAL_ASSETS['bomb_orbit_img'] # Hiện bomb1 lúc xoay quanh người
        self.rect = self.image.get_rect()
        self.state = 'orbit'
        self.angle = 0 # Góc xoay lệch góc của hoa để không đè lên nhau
        self.display_angle = 0
        self.x, self.y, self.vx, self.vy = 0, 0, 0, 0
        self.manager_ref = None
        self.dist_traveled, self.max_dist = 0, 0
        self.is_special_bomb = False

    def throw(self, tx, ty, sx, sy, manager):
        if self.state == 'orbit':
            self.state = 'thrown'
            self.manager_ref = manager
            self.x, self.y = sx, sy
            dx, dy = tx - sx, ty - sy
            self.max_dist = math.hypot(dx, dy)
            self.dist_traveled = 0
            speed = 15.0
            if self.max_dist > 0:
                self.vx = (dx / self.max_dist) * speed
                self.vy = (dy / self.max_dist) * speed
            else:
                self.vx, self.vy = speed, 0
            
            # Khi ném đi, quả bom tích tụ này có 40% biến thành bom độc khổng lồ, còn lại nổ cực to
            self.is_special_bomb = random.random() < 0.40
            self.image = SPECIAL_ASSETS['bomb_special_img'] if self.is_special_bomb else SPECIAL_ASSETS['bomb_normal_img']

    def update(self, px, py, entities):
        if self.state == 'orbit':
            self.angle = (self.angle + 5) % 360
            self.x = px + math.cos(math.radians(self.angle)) * 80
            self.y = py + math.sin(math.radians(self.angle)) * 80
            self.display_angle = (self.display_angle + 12) % 360
            self.rect.center = (int(self.x), int(self.y))
        elif self.state == 'thrown':
            self.x += self.vx
            self.y += self.vy
            self.dist_traveled += math.hypot(self.vx, self.vy)
            self.display_angle = (self.display_angle + 16) % 360
            self.rect.center = (int(self.x), int(self.y))
            
            if random.random() < 0.3:
                self.manager_ref.particle_sys.spawn_smoke(self.x, self.y)

            hit = any(check_collision_flexible(self.rect, self.x, self.y, e) for e in entities)
            if hit or self.dist_traveled >= self.max_dist:
                if self.is_special_bomb:
                    self.manager_ref.particle_sys.spawn_bomb2_explosion(self.x, self.y)
                    self.manager_ref.active_toxic_clouds.append(ToxicCloudEntity(self.x, self.y))
                    for e in entities:
                        ex = e.rect.centerx if hasattr(e, 'rect') else getattr(e, 'x', None)
                        ey = e.rect.centery if hasattr(e, 'rect') else getattr(e, 'y', None)
                        if ex is not None and ey is not None:
                            if math.hypot(ex - self.x, ey - self.y) < 120:
                                if hasattr(e, 'take_damage'): e.take_damage(90)
                                elif hasattr(e, 'hp'): e.hp -= 90
                else:
                    self.manager_ref.particle_sys.spawn_explosion(self.x, self.y)
                    for e in entities:
                        ex = e.rect.centerx if hasattr(e, 'rect') else getattr(e, 'x', None)
                        ey = e.rect.centery if hasattr(e, 'rect') else getattr(e, 'y', None)
                        if ex is not None and ey is not None:
                            if math.hypot(ex - self.x, ey - self.y) < 80:
                                if hasattr(e, 'take_damage'): e.take_damage(60)
                                elif hasattr(e, 'hp'): e.hp -= 60
                return False
        return True

    def draw(self, surface, cx=0, cy=0):
        ri = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(ri, ri.get_rect(center=(int(self.x - cx), int(self.y - cy))))

# ==========================================
# CLASS TANK VÀ CÁC THÀNH PHẦN KHÁC
# ==========================================
class RocketEntity:
    def __init__(self, x, y, target_angle, manager):
        self.x, self.y, self.manager = x, y, manager
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
                if hasattr(e, 'take_damage'): e.take_damage(50)
                elif hasattr(e, 'hp'): e.hp -= 50
                return False 
        if self.x < -2000 or self.x > 5000 or self.y < -2000 or self.y > 5000:
            return False
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        rotated_image = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(rotated_image, rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))

class TankEntity:
    def __init__(self, x, y, manager):
        self.x, self.y, self.manager = x, y, manager
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
        closest, min_dist = None, 999999
        for e in entities:
            ex = e.rect.centerx if hasattr(e, 'rect') else getattr(e, 'x', None)
            ey = e.rect.centery if hasattr(e, 'rect') else getattr(e, 'y', None)
            if ex is not None and ey is not None:
                dist = math.hypot(ex - self.x, ey - self.y)
                if dist < min_dist: min_dist, closest = dist, e
        return closest, min_dist

    def update(self, entities):
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time > self.duration:
            self.manager.particle_sys.spawn_explosion(self.x, self.y)
            return False
            
        target, dist = self.get_closest_enemy(entities)
        if target:
            tx = target.rect.centerx if hasattr(target, 'rect') else getattr(target, 'x', self.x)
            ty = target.rect.centery if hasattr(target, 'rect') else getattr(target, 'y', self.y)
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
            if self.idle_state == 'rotate': self.display_angle += self.idle_spin_dir
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

class WrenchProjectileEntity:
    def __init__(self, start_x, start_y, target_x, target_y, manager):
        self.x, self.y, self.manager = start_x, start_y, manager
        self.image = SPECIAL_ASSETS['wrench_img']
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        dx, dy = target_x - start_x, target_y - start_y
        self.max_dist, self.dist_traveled = math.hypot(dx, dy), 0
        speed = 16.0
        self.vx = (dx / self.max_dist) * speed if self.max_dist > 0 else speed
        self.vy = (dy / self.max_dist) * speed if self.max_dist > 0 else 0
        self.display_angle, self.spin_speed = 0, 24
        
    def update(self, entities):
        self.x += self.vx
        self.y += self.vy
        self.dist_traveled += math.hypot(self.vx, self.vy)
        self.display_angle = (self.display_angle + self.spin_speed) % 360
        self.rect.center = (int(self.x), int(self.y))
        
        hit = any(check_collision_flexible(self.rect, self.x, self.y, e) for e in entities)
        if hit or self.dist_traveled >= self.max_dist:
            self.manager.particle_sys.spawn_explosion(self.x, self.y)
            self.manager.active_tanks.append(TankEntity(self.x, self.y, self.manager))
            return False  
        return True
        
    def draw(self, surface, camera_x=0, camera_y=0):
        rotated_image = pygame.transform.rotate(self.image, self.display_angle)
        surface.blit(rotated_image, rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))

# =========================================================
# SỬA ĐỔI: THÊM HIỆU ỨNG NỔ FLOWER 1 KHI VA CHẠM / DỪNG
# =========================================================
class SubFlowerEntity:
    def __init__(self, x, y, angle_rad, manager):
        self.x, self.y, self.manager = x, y, manager
        self.image, self.rect = SPECIAL_ASSETS['subflower_img'], SPECIAL_ASSETS['subflower_img'].get_rect()
        self.vx, self.vy = math.cos(angle_rad) * 10.0, math.sin(angle_rad) * 10.0
        self.display_angle, self.explosion, self.state = 0, None, 'moving'
        
    def update(self, entities):
        if self.state == 'moving':
            self.x, self.y = self.x + self.vx, self.y + self.vy
            self.vx, self.vy = self.vx * 0.92, self.vy * 0.92
            self.display_angle = (self.display_angle + 18) % 360
            self.rect.center = (int(self.x), int(self.y))
            if any(check_collision_flexible(self.rect, self.x, self.y, e) for e in entities) or math.hypot(self.vx, self.vy) < 1.0:
                self.state = 'exploded'
                # THÊM THEO YÊU CẦU: Tạo vụ nổ hạt cho từng bông flower1 khi tung ra rồi đụng độ
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
        self.state, self.angle, self.display_angle = 'orbit', 180, 0
        self.x, self.y, self.vx, self.vy, self.manager_ref = 0, 0, 0, 0, None
        
    def throw(self, tx, ty, sx, sy, manager):
        if self.state == 'orbit':
            self.state, self.manager_ref, self.x, self.y = 'thrown', manager, sx, sy
            dx, dy = tx - sx, ty - sy
            d = math.hypot(dx, dy)
            if d > 0: self.vx, self.vy = (dx/d)*20, (dy/d)*20
            
    def update(self, px, py, entities):
        if self.state == 'orbit':
            self.angle = (self.angle + 6) % 360
            self.x = px + math.cos(math.radians(self.angle))*80
            self.y = py + math.sin(math.radians(self.angle))*80
            self.display_angle = -self.angle - 45
            self.rect.center = (int(self.x), int(self.y))
        elif self.state == 'thrown':
            self.x, self.y, self.vx, self.vy = self.x + self.vx, self.y + self.vy, self.vx * 0.94, self.vy * 0.94
            self.display_angle = (self.display_angle + 22) % 360
            self.rect.center = (int(self.x), int(self.y))
            if any(check_collision_flexible(self.rect, self.x, self.y, e) for e in entities) or math.hypot(self.vx, self.vy) < 1.0:
                if self.manager_ref:
                    # SỬA ĐỔI THEO YÊU CẦU: Gọi hiệu ứng nổ mới TO VÀ HOÀNH TRÁNG hơn cho Flower 2
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
    def __init__(self):
        init_special_assets()
        self.flower_throw_count, self.active_flower2, self.sub_flowers = 0, None, []
        self.bomb_throw_count, self.active_bomb_orbit = 0, None # THÊM: Biến quản lý bomb xoay
        self.active_wrenches, self.active_tanks, self.active_rockets = [], [], []
        self.active_bombs, self.active_toxic_clouds = [], [] 
        self.particle_sys = ParticleManager() 

    def on_player_throw_weapon(self, weapon_name, target_x, target_y, start_x, start_y):
        # ƯU TIÊN 1: Nếu có hoa đang xoay, ném hoa đi lập tức và mất hoa trên quỹ đạo
        if self.active_flower2 and self.active_flower2.state == 'orbit':
            self.active_flower2.throw(target_x, target_y, start_x, start_y, self)
            return True 
            
        # ƯU TIÊN 2 (SỬA ĐỔI THEO YÊU CẦU): Nếu có bom đang xoay, ném bom đi và biến mất trên quỹ đạo xoay
        if self.active_bomb_orbit and self.active_bomb_orbit.state == 'orbit':
            self.active_bomb_orbit.throw(target_x, target_y, start_x, start_y, self)
            return True

        if weapon_name == 'flower':
            self.flower_throw_count += 1
            if self.flower_throw_count >= 3 and not self.active_flower2:
                self.flower_throw_count, self.active_flower2 = 0, Flower2Entity() 
                
        elif weapon_name == 'wrench':
            if len(self.active_tanks) < 2:
                self.active_wrenches.append(WrenchProjectileEntity(start_x, start_y, target_x, target_y, self))
                return True

        elif weapon_name in ['bomb1', 'bomb']:
            # SỬA ĐỔI THEO YÊU CẦU: Tích lũy số lần ném bom để kích hoạt quả bom xoay quanh người
            self.bomb_throw_count += 1
            if self.bomb_throw_count >= 3 and not self.active_bomb_orbit:
                self.bomb_throw_count = 0
                self.active_bomb_orbit = BombOrbitEntity() # Tạo quả bom xoay (dùng ảnh bomb1)
                
            # Song song với đó vẫn bắn ra viên bom thường từ tay người chơi
            is_special_bomb = random.random() < 0.20
            self.active_bombs.append(BombProjectileEntity(start_x, start_y, target_x, target_y, is_special_bomb, self))
            return True 
            
        return False

    def update(self, player_x, player_y, entities):
        # Cập nhật Flower 2
        if self.active_flower2 and not self.active_flower2.update(player_x, player_y, entities):
            self.active_flower2 = None 
        for sub in self.sub_flowers[:]:
            if not sub.update(entities): self.sub_flowers.remove(sub)

        # THÊM THEO YÊU CẦU: Cập nhật Bom Xoay
        if self.active_bomb_orbit and not self.active_bomb_orbit.update(player_x, player_y, entities):
            self.active_bomb_orbit = None

        # Cập nhật các thực thể khác
        for wr in self.active_wrenches[:]:
            if not wr.update(entities): self.active_wrenches.remove(wr)
        for tank in self.active_tanks[:]:
            if not tank.update(entities): self.active_tanks.remove(tank)
        for rocket in self.active_rockets[:]:
            if not rocket.update(entities): self.active_rockets.remove(rocket)
            
        for b in self.active_bombs[:]:
            if not b.update(entities): self.active_bombs.remove(b)
        for tc in self.active_toxic_clouds[:]:
            if not tc.update(entities): self.active_toxic_clouds.remove(tc)
            
        self.particle_sys.update()

    def draw(self, surface, camera_x=0, camera_y=0):
        for tc in self.active_toxic_clouds: tc.draw(surface, camera_x, camera_y)
        
        if self.active_flower2: self.active_flower2.draw(surface, camera_x, camera_y)
        for sub in self.sub_flowers: sub.draw(surface, camera_x, camera_y)
        
        # THÊM THEO YÊU CẦU: Vẽ quả bom xoay
        if self.active_bomb_orbit: self.active_bomb_orbit.draw(surface, camera_x, camera_y)
        
        for wr in self.active_wrenches: wr.draw(surface, camera_x, camera_y)
        for tank in self.active_tanks: tank.draw(surface, camera_x, camera_y)
        for rocket in self.active_rockets: rocket.draw(surface, camera_x, camera_y)
        for b in self.active_bombs: b.draw(surface, camera_x, camera_y)
        
        self.particle_sys.draw(surface, camera_x, camera_y)