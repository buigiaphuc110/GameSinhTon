import pygame
import sys
import os
import math
import random

# Biến toàn cục lưu vũ khí đang được chọn (Mặc định là 'sword')
SELECTED_WEAPON = 'sword'

# Biến toàn cục lưu cache các frame hoạt ảnh nổ của flower
FLOWER_EXPLOSION_CACHE = []

# Biến toàn cục lưu cache hình ảnh các vũ khí để thực thể tự động đồng bộ hình ảnh
WEAPON_IMAGES_CACHE = {}

def get_flower_explosion_frames():
    global FLOWER_EXPLOSION_CACHE
    if not FLOWER_EXPLOSION_CACHE:
        try:
            # Load ảnh sprite sheet, tự động tính toán kích thước thực tế
            sheet_path = os.path.join('weapon', 'flowerex.png')
            sheet = pygame.image.load(sheet_path).convert_alpha()
            
            # Tính toán chiều rộng và cao của mỗi frame (chia đều 4x4)
            frame_w = sheet.get_width() // 4
            frame_h = sheet.get_height() // 4
            
            # Cắt thành 15 frame (Bỏ frame thứ 16 cuối cùng bị lỗi)
            count = 0
            for row in range(4):
                for col in range(4):
                    if count >= 15:
                        break
                    frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (col * frame_w, row * frame_h, frame_w, frame_h))
                    
                    # --- CHỈNH SỬA: Scale frame lên x2 lần ---
                    frame = pygame.transform.scale(frame, (frame_w * 2, frame_h * 2))
                    
                    # --- CHỈNH SỬA: Thêm độ mờ từ từ cho frame 8, 9, 10 ---
                    if count == 8:
                        frame.set_alpha(190) # Mờ 25%
                    elif count == 9:
                        frame.set_alpha(120) # Mờ 50%
                    elif count >= 10:
                        frame.set_alpha(50)  # Mờ 80% cho các frame cuối
                        
                    FLOWER_EXPLOSION_CACHE.append(frame)
                    count += 1
        except Exception as e:
            print(f"Lỗi tải flowerex.png: {e}")
            dummy = pygame.Surface((360, 360), pygame.SRCALPHA) # Tăng kích thước dummy x2
            pygame.draw.circle(dummy, (255, 105, 180), (180, 180), 100)
            FLOWER_EXPLOSION_CACHE = [dummy] * 15
            
    return FLOWER_EXPLOSION_CACHE

# ==========================================
# CLASS HIỆU ỨNG NỔ TÙY CHỈNH CHO VŨ KHÍ
# ==========================================
class WeaponExplosion:
    def __init__(self, x, y, weapon_name):
        self.x = x
        self.y = y
        self.timer = 0
        self.weapon_name = weapon_name
        self.particles = []
        
        if self.weapon_name == 'sword':
            self.lifetime = 18  
            colors = [(255, 255, 255), (220, 220, 225), (180, 180, 185), (130, 130, 140), (90, 90, 100)]
            self.slashes = []
            num_slashes = random.randint(5, 8)
            for _ in range(num_slashes):
                self.slashes.append({
                    'offset_x': random.uniform(-20, 20),
                    'offset_y': random.uniform(-20, 20),
                    'angle': random.uniform(0, 2 * math.pi),
                    'length': random.uniform(40, 70),  
                    'width': random.randint(3, 8),     
                    'color': random.choice(colors)
                })
                
            self.sparks = []
            num_sparks = random.randint(10, 20)
            for _ in range(num_sparks):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2.0, 7.0)
                self.sparks.append({
                    'x': 0, 'y': 0,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': random.uniform(3, 7), 
                    'color': random.choice(colors)
                })
                
        elif self.weapon_name == 'axe':
            self.lifetime = 35 
            self.shockwaves = [
                {'radius': 0, 'max_radius': random.uniform(180, 240), 'speed': 8.0, 'width': 6, 'color': (50, 150, 255)}, 
                {'radius': -15, 'max_radius': random.uniform(150, 200), 'speed': 7.5, 'width': 4, 'color': (255, 255, 255)} 
            ]
            self.smoke_particles = []
            num_smoke = random.randint(20, 30)
            for _ in range(num_smoke):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.0, 4.5)
                smoke_color = random.choice([(120, 120, 120), (170, 170, 170), (100, 150, 200)])
                self.smoke_particles.append({
                    'x': 0, 'y': 0,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': random.uniform(4, 10), 
                    'color': smoke_color
                })
            
        elif self.weapon_name == 'gun':
            self.lifetime = 15  
            num_particles = random.randint(8, 12)
            gun_colors = [(255, 255, 100), (255, 215, 0), (200, 150, 100), (180, 130, 80)]
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(1, 6) 
                self.particles.append({
                    'dx': math.cos(angle) * dist,
                    'dy': math.sin(angle) * dist,
                    'color': random.choice(gun_colors),
                    'speed': random.uniform(1.0, 1.8), 
                    'current_radius': random.randint(5, 10) 
                })

        elif self.weapon_name == 'flower':
            # --- HIỆU ỨNG HOA: FLIPBOOK 15 FRAMES ---
            self.frames = get_flower_explosion_frames()
            self.current_frame = 0
            self.animation_speed = 0.5 
            self.lifetime = int(len(self.frames) / self.animation_speed)
            
        elif self.weapon_name == 'wrench':
            self.lifetime = 18
            wrench_colors = [(255, 255, 255), (210, 210, 210), (130, 130, 130), (70, 70, 70)]
            num_squares = random.randint(30, 45) 
            for _ in range(num_squares):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(4.0, 9.0) 
                self.particles.append({
                    'x': 0, 'y': 0,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': random.choice([2, 3, 4]), 
                    'color': random.choice(wrench_colors)
                })
                
        else: # Hiệu ứng nổ nổ tung tóe chung (dành cho Bomb và các loại khác)
            self.lifetime = 20  
            num_particles = random.randint(12, 18)
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(2, 15)
                self.particles.append({
                    'dx': math.cos(angle) * dist,
                    'dy': math.sin(angle) * dist,
                    'color_phase': random.uniform(0, 1),
                    'speed': random.uniform(1.0, 2.0),
                    'current_radius': random.randint(8, 20)
                })

    def update(self):
        self.timer += 1
        
        if self.weapon_name == 'sword':
            for s in self.slashes:
                s['length'] *= 0.75  
            for sp in self.sparks:
                sp['x'] += sp['vx']
                sp['y'] += sp['vy']
                sp['size'] -= 0.25   
                
        elif self.weapon_name == 'axe':
            for s in self.shockwaves:
                s['radius'] += s['speed']
            for p in self.smoke_particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['size'] -= 0.15 
                
        elif self.weapon_name == 'gun':
            for p in self.particles:
                p['dx'] *= p['speed']
                p['dy'] *= p['speed']
                p['current_radius'] = max(0, p['current_radius'] - 1.0)
                
        elif self.weapon_name == 'flower':
            self.current_frame += self.animation_speed
            if int(self.current_frame) >= len(self.frames):
                return False 
            return True
            
        elif self.weapon_name == 'wrench':
            for p in self.particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.91
                p['vy'] *= 0.91
                
        else:
            for p in self.particles:
                p['dx'] *= p['speed']
                p['dy'] *= p['speed']
                p['current_radius'] = max(0, p['current_radius'] - 1.0)
            
        return self.timer < self.lifetime

    def draw(self, surface, camera_x=0, camera_y=0):
        if self.weapon_name != 'flower':
            alpha = int(255 * (1 - (self.timer / self.lifetime)))
            if alpha < 0: alpha = 0

        if self.weapon_name == 'sword':
            surf_size = 160 
            slash_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = surf_size // 2
            
            for s in self.slashes:
                if s['length'] < 2: continue
                dx = math.cos(s['angle']) * (s['length'] / 2)
                dy = math.sin(s['angle']) * (s['length'] / 2)
                start_pos = (center + s['offset_x'] - dx, center + s['offset_y'] - dy)
                end_pos = (center + s['offset_x'] + dx, center + s['offset_y'] + dy)
                
                current_width = max(1, int(s['width'] * (1 - self.timer / self.lifetime)))
                color_with_alpha = (*s['color'], alpha)
                pygame.draw.line(slash_surf, color_with_alpha, start_pos, end_pos, current_width)
                
            for sp in self.sparks:
                if sp['size'] < 1: continue
                color_with_alpha = (*sp['color'], alpha)
                rect_size = int(sp['size'])
                spark_rect = pygame.Rect(center + sp['x'] - rect_size // 2, center + sp['y'] - rect_size // 2, rect_size, rect_size)
                pygame.draw.rect(slash_surf, color_with_alpha, spark_rect)
                
            surface.blit(slash_surf, (self.x - center - camera_x, self.y - center - camera_y))
            
        elif self.weapon_name == 'axe':
            for s in self.shockwaves:
                if 0 < s['radius'] < s['max_radius']:
                    r = int(s['radius'])
                    wave_alpha = max(0, int(255 * (1 - (s['radius'] / s['max_radius']))))
                    final_alpha = int(wave_alpha * (alpha / 255))
                    
                    if final_alpha > 0:
                        surf_size = int(s['max_radius'] * 2 + 50)
                        center = surf_size // 2
                        circle_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                        
                        num_blocks = max(12, int((2 * math.pi * r) / 18))
                        block_size = int(s['width'] * 2)
                        
                        for i in range(num_blocks):
                            angle = (2 * math.pi / num_blocks) * i
                            px = center + math.cos(angle) * r
                            py = center + math.sin(angle) * r
                            pygame.draw.rect(circle_surf, (*s['color'], final_alpha), 
                                             (px - block_size//2, py - block_size//2, block_size, block_size))
                        
                        surface.blit(circle_surf, (self.x - center - camera_x, self.y - center - camera_y))
                        
            for p in self.smoke_particles:
                if p['size'] > 0:
                    size = int(p['size'])
                    smoke_alpha = max(0, int(alpha * 0.8))
                    smoke_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                    pygame.draw.circle(smoke_surf, (*p['color'], smoke_alpha), (size//2, size//2), size//2)
                    surface.blit(smoke_surf, (self.x + p['x'] - size//2 - camera_x, self.y + p['y'] - size//2 - camera_y))
                        
        elif self.weapon_name == 'gun':
            for p in self.particles:
                if p['current_radius'] <= 0: continue
                r = int(p['current_radius'])
                color_with_alpha = (*p['color'], alpha)
                
                circle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.rect(circle_surf, color_with_alpha, (0, 0, r * 2, r * 2))
                surface.blit(circle_surf, (self.x + p['dx'] - r - camera_x, self.y + p['dy'] - r - camera_y))

        elif self.weapon_name == 'flower':
            if self.frames:
                frame_idx = min(int(self.current_frame), len(self.frames) - 1)
                img = self.frames[frame_idx]
                draw_x = self.x - img.get_width() // 2 - camera_x
                draw_y = self.y - img.get_height() // 2 - camera_y
                surface.blit(img, (draw_x, draw_y))

        elif self.weapon_name == 'wrench':
            for p in self.particles:
                if alpha <= 0: continue
                size = p['size']
                wrench_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                color_with_alpha = (*p['color'], alpha)
                pygame.draw.rect(wrench_surf, color_with_alpha, (0, 0, size, size))
                surface.blit(wrench_surf, (self.x + p['x'] - size//2 - camera_x, self.y + p['y'] - size//2 - camera_y))

        else:
            for p in self.particles:
                if p['current_radius'] <= 0: continue
                total_phase = p['color_phase'] + (self.timer / self.lifetime)
                if total_phase < 0.3: color = (255, 255, 100, alpha)
                elif total_phase < 0.6: color = (255, 160, 50, alpha)
                elif total_phase < 0.9: color = (220, 50, 50, alpha)
                else:
                    darkness = int(50 * (1 - alpha/255))
                    color = (darkness, darkness, darkness, alpha)

                r = int(p['current_radius'])
                if r > 0:
                    circle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(circle_surf, color, (r, r), r)
                    surface.blit(circle_surf, (self.x + p['dx'] - r - camera_x, self.y + p['dy'] - r - camera_y))

# ==========================================
# CƠ CHẾ VŨ KHÍ (ORBIT, THROW & EXPLODE)
# ==========================================
class WeaponEntity:
    def __init__(self, image):
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect()
        
        self.state = 'orbit' 
        self.thrown_weapon_type = 'sword'
        
        self.angle = 0
        self.orbit_radius = 60
        self.orbit_speed = 5
        
        self.x, self.y = 0, 0
        self.vx, self.vy = 0, 0
        self.friction = 0.94  
        
        self.action_time = 0     
        self.display_angle = 0   
        self.shoot_angle = 0     
        
        self.trail = []          
        self.max_trail_len = 6   
        self.spin_speed = 22     
        
        self.explosion = None
        self.active_bullet = None
        
    def throw(self, target_x, target_y, start_x, start_y):
        if self.state == 'orbit':
            self.thrown_weapon_type = SELECTED_WEAPON
            self.x, self.y = start_x, start_y
            
            dx = target_x - start_x
            dy = target_y - start_y
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                if self.thrown_weapon_type == 'axe':
                    self.state = 'thrown'
                    speed = 18   
                    self.friction = 0.92 
                    self.spin_speed = 12
                    self.vx = (dx / dist) * speed
                    self.vy = (dy / dist) * speed
                    
                elif self.thrown_weapon_type == 'gun':
                    self.state = 'shooting'
                    self.action_time = pygame.time.get_ticks()
                    self.shoot_angle = math.degrees(math.atan2(-dy, dx)) - 45
                    
                    bullet_speed = 30 
                    self.active_bullet = {
                        'x': start_x, 'y': start_y, 
                        'vx': (dx / dist) * bullet_speed,
                        'vy': (dy / dist) * bullet_speed,
                        'life': 30,
                        'just_shot': True 
                    }
                    
                else: 
                    self.state = 'thrown'
                    speed = 22  
                    self.friction = 0.94
                    self.vx = (dx / dist) * speed
                    self.vy = (dy / dist) * speed
                    
                    # --- CHỈNH SỬA: Sword bay thẳng thay vì xoay ---
                    if self.thrown_weapon_type == 'sword':
                        self.spin_speed = 0 # Vô hiệu hoá lực xoay
                        self.display_angle = math.degrees(math.atan2(-dy, dx)) - 45 # Hướng thẳng mũi kiếm về phía ném
                    else:
                        self.spin_speed = 22
            
            self.trail.clear()
            self.explosion = None

    def update(self, player_x, player_y, entities):
        global WEAPON_IMAGES_CACHE
        current_time = pygame.time.get_ticks()
        
        if self.explosion:
            if not self.explosion.update():
                self.explosion = None
        
        if self.state == 'orbit':
            # SỬA LỖI: Tự động cập nhật hình ảnh đúng với vũ khí đang chọn trong bộ nhớ đệm
            if WEAPON_IMAGES_CACHE and SELECTED_WEAPON in WEAPON_IMAGES_CACHE:
                if self.original_image != WEAPON_IMAGES_CACHE[SELECTED_WEAPON]:
                    self.original_image = WEAPON_IMAGES_CACHE[SELECTED_WEAPON]
                    # Reset lại kích thước khung hitbox rect tương ứng với vũ khí mới
                    old_center = self.rect.center
                    self.rect = self.original_image.get_rect()
                    self.rect.center = old_center

            self.angle = (self.angle + self.orbit_speed) % 360
            rad = math.radians(self.angle)
            self.x = player_x + math.cos(rad) * self.orbit_radius
            self.y = player_y + math.sin(rad) * self.orbit_radius
            self.display_angle = -self.angle - 45
            self.rect.center = (int(self.x), int(self.y))
            self.trail.clear()
            
        elif self.state == 'thrown':
            self.x += self.vx
            self.y += self.vy
            self.vx *= self.friction
            self.vy *= self.friction
            
            # --- CHỈNH SỬA: Bỏ qua cộng góc xoay (spin) nếu là kiếm ---
            if self.thrown_weapon_type != 'sword':
                self.display_angle = (self.display_angle + self.spin_speed) % 360
            
            self.rect.center = (int(self.x), int(self.y))
            
            self.trail.append((self.x, self.y, self.display_angle))
            if len(self.trail) > self.max_trail_len:
                self.trail.pop(0)
            
            hit_entity = False
            for entity in entities:
                entity_rect = entity.rect if hasattr(entity, 'rect') else entity
                if isinstance(entity_rect, pygame.Rect) and self.rect.colliderect(entity_rect):
                    hit_entity = True
                    break
                    
            if hit_entity or math.hypot(self.vx, self.vy) < 1.0:
                self.state = 'disappeared'
                self.action_time = current_time 
                self.rect.center = (-9999, -9999) 
                self.explosion = WeaponExplosion(self.x, self.y, self.thrown_weapon_type)
                
        elif self.state == 'shooting':
            closer_radius = self.orbit_radius * 0.4
            rad = math.radians(self.angle)
            base_x = player_x + math.cos(rad) * closer_radius
            base_y = player_y + math.sin(rad) * closer_radius
            
            if current_time - self.action_time < 150:
                self.x = base_x + random.uniform(-3, 3)
                self.y = base_y + random.uniform(-3, 3)
            else:
                self.x = base_x
                self.y = base_y
                
            self.display_angle = self.shoot_angle 
            self.rect.center = (int(self.x), int(self.y))
            self.trail.clear()
            
            if self.active_bullet:
                if self.active_bullet.get('just_shot'):
                    self.active_bullet['x'] = self.x
                    self.active_bullet['y'] = self.y
                    self.active_bullet['just_shot'] = False
                
                self.active_bullet['x'] += self.active_bullet['vx']
                self.active_bullet['y'] += self.active_bullet['vy']
                self.active_bullet['life'] -= 1
                
                bullet_rect = pygame.Rect(0, 0, 10, 10)
                bullet_rect.center = (int(self.active_bullet['x']), int(self.active_bullet['y']))
                
                hit_entity = False
                for entity in entities:
                    entity_rect = entity.rect if hasattr(entity, 'rect') else entity
                    if isinstance(entity_rect, pygame.Rect) and bullet_rect.colliderect(entity_rect):
                        hit_entity = True
                        break
                        
                if hit_entity or self.active_bullet['life'] <= 0:
                    self.explosion = WeaponExplosion(self.active_bullet['x'], self.active_bullet['y'], 'gun')
                    self.active_bullet = None
                    self.state = 'orbit' 
                
        elif self.state == 'disappeared':
            if current_time - self.action_time >= 500:
                self.state = 'orbit'

    def draw(self, surface, camera_x=0, camera_y=0):
        if self.explosion:
            self.explosion.draw(surface, camera_x, camera_y)
            
        if self.state == 'disappeared':
            return
            
        if self.state == 'thrown':
            for i, (tx, ty, tangle) in enumerate(self.trail):
                alpha = int((i + 1) * (180 / self.max_trail_len))
                trail_rotated = pygame.transform.rotate(self.original_image, tangle)
                trail_surf = trail_rotated.copy()
                trail_surf.set_alpha(alpha)
                trail_rect = trail_surf.get_rect(center=(int(tx - camera_x), int(ty - camera_y)))
                surface.blit(trail_surf, trail_rect)

        rotated_image = pygame.transform.rotate(self.original_image, self.display_angle)
        draw_rect = rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        surface.blit(rotated_image, draw_rect)
        
        if self.state == 'shooting' and self.active_bullet:
            bx = self.active_bullet['x'] - camera_x
            by = self.active_bullet['y'] - camera_y
            
            tracer_end_x = bx - self.active_bullet['vx'] * 0.5
            tracer_end_y = by - self.active_bullet['vy'] * 0.5
            pygame.draw.line(surface, (255, 200, 50), (tracer_end_x, tracer_end_y), (bx, by), 4)
            
            pygame.draw.rect(surface, (255, 215, 0), (bx - 4, by - 4, 8, 8)) 
            pygame.draw.rect(surface, (255, 255, 255), (bx - 2, by - 2, 4, 4)) 

# ==========================================
# LOAD ẢNH VÀ HIỂN THỊ MENU CHỌN VŨ KHÍ
# ==========================================
def load_weapon_images():
    global WEAPON_IMAGES_CACHE
    weapons = {}
    folder = 'weapon'
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    ignore_files = ['flower2', 'bomb1', 'flowerex'] 
    
    # Quy tắc đổi tên từ file ảnh vật lý sang tên định danh trong logic game
    rename_rules = {
        'flower1': 'flower',  
        'bomb2': 'bomb'       
    }

    if os.path.exists(folder):
        for file_name in os.listdir(folder):
            if file_name.lower().endswith('.png') or file_name.lower().endswith('.jpg'):
                base_name = file_name.rsplit('.', 1)[0]
                if base_name in ignore_files:
                    continue
                
                weapon_name = rename_rules.get(base_name, base_name)
                try:
                    img = pygame.image.load(os.path.join(folder, file_name)).convert_alpha()
                    
                    # --- CHỈNH SỬA: Giảm kích thước vũ khí gun, bomb, flower đi 1.2 lần (70 / 1.2 = ~58) ---
                    if weapon_name in ['gun', 'bomb', 'flower']:
                        new_size = int(70 / 1.2)
                        weapons[weapon_name] = pygame.transform.scale(img, (new_size, new_size))
                    else:
                        weapons[weapon_name] = pygame.transform.scale(img, (70, 70))
                        
                except Exception as e:
                    print(f"Không thể tải ảnh {file_name}: {e}")
            
    # --- TẠO CHẤT LIỆU DUMMY PHÒNG HỜ ---
    if 'sword' not in weapons:
        dummy = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.line(dummy, (200, 200, 200), (15, 55), (55, 15), 8) 
        weapons['sword'] = dummy
    if 'flower' not in weapons:
        dummy = pygame.Surface((58, 58), pygame.SRCALPHA)
        pygame.draw.circle(dummy, (255, 105, 180), (29, 29), 16)
        pygame.draw.circle(dummy, (255, 215, 0), (29, 29), 6)
        weapons['flower'] = dummy
    if 'wrench' not in weapons:
        dummy = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.line(dummy, (150, 150, 150), (20, 50), (50, 20), 10)
        pygame.draw.circle(dummy, (120, 120, 120), (50, 20), 12, width=4)
        weapons['wrench'] = dummy
    if 'bomb' not in weapons:
        dummy = pygame.Surface((58, 58), pygame.SRCALPHA)
        pygame.draw.circle(dummy, (50, 50, 50), (29, 29), 20)
        pygame.draw.line(dummy, (200, 50, 50), (29, 8), (29, -4), 3)
        weapons['bomb'] = dummy
        
    # Cập nhật vào bộ nhớ cache toàn cục để WeaponEntity lấy dữ liệu đồng bộ
    WEAPON_IMAGES_CACHE = weapons
    return weapons

def draw_text_with_shadow(text, font, color, surface, x, y):
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, shadow.get_rect(center=(x+3, y+3)))
    surface.blit(font.render(text, True, color), font.render(text, True, color).get_rect(center=(x, y)))

def weapon_selection_menu(screen, clock, WIDTH, HEIGHT, game_assets, transition_out, transition_in):
    global SELECTED_WEAPON
    weapons_data = load_weapon_images()
    weapon_names = list(weapons_data.keys())
    
    if SELECTED_WEAPON not in weapon_names and weapon_names:
        SELECTED_WEAPON = weapon_names[0]
    
    BOX_SIZE, GAP = 120, 40
    start_x = (WIDTH - (len(weapon_names) * BOX_SIZE + (len(weapon_names) - 1) * GAP)) // 2
    
    boxes = []
    for i, name in enumerate(weapon_names):
        rect = pygame.Rect(start_x + i * (BOX_SIZE + GAP), HEIGHT // 2 - BOX_SIZE // 2, BOX_SIZE, BOX_SIZE)
        boxes.append((rect, name))

    btn_back = pygame.Rect(20, 20, 70, 45)

    def draw_screen(mx, my):
        screen.fill((30, 30, 40))
        draw_text_with_shadow("CHOOSE YOUR WEAPON", game_assets['font_level_title'], (255, 215, 0), screen, WIDTH//2, 80)
        
        pygame.draw.rect(screen, (100, 100, 100) if btn_back.collidepoint((mx, my)) else (50, 50, 50), btn_back, border_radius=10)
        draw_text_with_shadow("<<", game_assets['font_btn'], (255, 255, 255), screen, btn_back.centerx, btn_back.centery)
        
        for rect, name in boxes:
            is_hover = rect.collidepoint((mx, my))
            is_selected = (name == SELECTED_WEAPON)
            
            bg_color = (80, 80, 90) if is_hover else (50, 50, 60)
            border_color = (100, 255, 100) if is_selected else (30, 30, 30)
            
            pygame.draw.rect(screen, bg_color, rect, border_radius=15)
            pygame.draw.rect(screen, border_color, rect, width=4 if is_selected else 2, border_radius=15)
            
            img = weapons_data[name]
            screen.blit(img, img.get_rect(center=rect.center))
            draw_text_with_shadow(name.upper(), game_assets['font_level_diff'], (255, 255, 255), screen, rect.centerx, rect.bottom + 25)

    transition_in(clock, lambda: draw_screen(-100, -100))
    
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        draw_screen(mx, my)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_back.collidepoint((mx, my)):
                    transition_out(clock)
                    running = False
                
                for rect, name in boxes:
                    if rect.collidepoint((mx, my)):
                        SELECTED_WEAPON = name
                        
        pygame.display.update()
        clock.tick(60)