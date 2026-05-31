import pygame
import sys
import os
import math
import random

# Biến toàn cục lưu vũ khí đang được chọn
SELECTED_WEAPON = 'sword'

# Cache hoạt ảnh
FLOWER_EXPLOSION_CACHE = []
WEAPON_IMAGES_CACHE = {}
CURRENT_PLAYER = None

def get_flower_explosion_frames():
    global FLOWER_EXPLOSION_CACHE
    if not FLOWER_EXPLOSION_CACHE:
        try:
            sheet_path = os.path.join('weapon', 'flowerex.png')
            sheet = pygame.image.load(sheet_path).convert_alpha()
            frame_w = sheet.get_width() // 4
            frame_h = sheet.get_height() // 4
            count = 0
            for row in range(4):
                for col in range(4):
                    if count >= 15: break
                    frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (col * frame_w, row * frame_h, frame_w, frame_h))
                    frame = pygame.transform.scale(frame, (frame_w * 2, frame_h * 2))
                    
                    if count == 8: frame.set_alpha(190)
                    elif count == 9: frame.set_alpha(120)
                    elif count >= 10: frame.set_alpha(50)
                        
                    FLOWER_EXPLOSION_CACHE.append(frame)
                    count += 1
        except Exception as e:
            print(f"Lỗi tải flowerex.png: {e}")
            dummy = pygame.Surface((360, 360), pygame.SRCALPHA)
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
            for _ in range(random.randint(5, 8)):
                self.slashes.append({
                    'offset_x': random.uniform(-20, 20),
                    'offset_y': random.uniform(-20, 20),
                    'angle': random.uniform(0, 2 * math.pi),
                    'length': random.uniform(40, 70),  
                    'width': random.randint(3, 8),     
                    'color': random.choice(colors)
                })
            self.sparks = []
            for _ in range(random.randint(10, 20)):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2.0, 7.0)
                self.sparks.append({
                    'x': 0, 'y': 0,
                    'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
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
            for _ in range(random.randint(20, 30)):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.0, 4.5)
                self.smoke_particles.append({
                    'x': 0, 'y': 0,
                    'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                    'size': random.uniform(4, 10), 
                    'color': random.choice([(120, 120, 120), (170, 170, 170), (100, 150, 200)])
                })
            
        elif self.weapon_name == 'gun':
            self.lifetime = 15  
            gun_colors = [(255, 255, 100), (255, 215, 0), (200, 150, 100), (180, 130, 80)]
            for _ in range(random.randint(8, 12)):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(1, 6) 
                self.particles.append({
                    'dx': math.cos(angle) * dist, 'dy': math.sin(angle) * dist,
                    'color': random.choice(gun_colors),
                    'speed': random.uniform(1.0, 1.8), 
                    'current_radius': random.randint(5, 10) 
                })

        elif self.weapon_name == 'flower':
            self.frames = get_flower_explosion_frames()
            self.current_frame = 0
            self.animation_speed = 0.5 
            self.lifetime = int(len(self.frames) / self.animation_speed)
            
        elif self.weapon_name == 'wrench':
            self.lifetime = 18
            wrench_colors = [(255, 255, 255), (210, 210, 210), (130, 130, 130), (70, 70, 70)]
            for _ in range(random.randint(30, 45)):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(4.0, 9.0) 
                self.particles.append({
                    'x': 0, 'y': 0,
                    'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                    'size': random.choice([2, 3, 4]), 
                    'color': random.choice(wrench_colors)
                })
                
        else:
            cp = globals().get('CURRENT_PLAYER')
            k_lvl = cp.kaboom_level if cp and hasattr(cp, 'kaboom_level') else 0
            if self.weapon_name in ['bomb', 'bomb1', 'bomb2'] and k_lvl == 0:
                k_lvl = 1  
                
            if k_lvl > 0:
                self.lifetime = 25 + k_lvl * 5
                num_p = random.randint(25, 40) if k_lvl < 3 else random.randint(90, 130)
                for _ in range(num_p):
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(2, 25 * k_lvl if k_lvl < 3 else 700)
                    self.particles.append({
                        'dx': math.cos(angle) * dist, 'dy': math.sin(angle) * dist,
                        'color_phase': random.uniform(0, 0.7),
                        'speed': random.uniform(1.02, 1.06) if k_lvl < 3 else random.uniform(1.04, 1.14),
                        'current_radius': random.randint(12, 28) * (1 + k_lvl * 0.25)
                    })
            else:
                self.lifetime = 20  
                for _ in range(random.randint(12, 18)):
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(5, 25)
                    self.particles.append({
                        'dx': math.cos(angle) * dist, 'dy': math.sin(angle) * dist,
                        'color_phase': random.uniform(0, 1),
                        'speed': random.uniform(1.0, 2.0),
                        'current_radius': random.randint(12, 25)
                    })

    def update(self):
        self.timer += 1
        if self.weapon_name == 'sword':
            for s in self.slashes: s['length'] *= 0.75  
            for sp in self.sparks:
                sp['x'] += sp['vx']; sp['y'] += sp['vy']; sp['size'] -= 0.25   
        elif self.weapon_name == 'axe':
            for s in self.shockwaves: s['radius'] += s['speed']
            for p in self.smoke_particles:
                p['x'] += p['vx']; p['y'] += p['vy']; p['size'] -= 0.15 
        elif self.weapon_name == 'gun':
            for p in self.particles:
                p['dx'] *= p['speed']; p['dy'] *= p['speed']
                p['current_radius'] = max(0, p['current_radius'] - 1.0)
        elif self.weapon_name == 'flower':
            self.current_frame += self.animation_speed
            if int(self.current_frame) >= len(self.frames): return False 
            return True
        elif self.weapon_name == 'wrench':
            for p in self.particles:
                p['x'] += p['vx']; p['y'] += p['vy']
                p['vx'] *= 0.91; p['vy'] *= 0.91
        else:
            for p in self.particles:
                p['dx'] *= p['speed']; p['dy'] *= p['speed']
                p['current_radius'] = max(0, p['current_radius'] - 1.0)
        return self.timer < self.lifetime

    def draw(self, surface, camera_x=0, camera_y=0):
        if self.weapon_name != 'flower':
            alpha = max(0, int(255 * (1 - (self.timer / self.lifetime))))

        if self.weapon_name == 'sword':
            surf_size = 160 
            slash_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = surf_size // 2
            for s in self.slashes:
                if s['length'] < 2: continue
                dx, dy = math.cos(s['angle']) * (s['length'] / 2), math.sin(s['angle']) * (s['length'] / 2)
                current_width = max(1, int(s['width'] * (1 - self.timer / self.lifetime)))
                pygame.draw.line(slash_surf, (*s['color'], alpha), (center + s['offset_x'] - dx, center + s['offset_y'] - dy), (center + s['offset_x'] + dx, center + s['offset_y'] + dy), current_width)
            for sp in self.sparks:
                if sp['size'] < 1: continue
                rect_size = int(sp['size'])
                pygame.draw.rect(slash_surf, (*sp['color'], alpha), pygame.Rect(center + sp['x'] - rect_size // 2, center + sp['y'] - rect_size // 2, rect_size, rect_size))
            surface.blit(slash_surf, (self.x - center - camera_x, self.y - center - camera_y))
            
        elif self.weapon_name == 'axe':
            for s in self.shockwaves:
                if 0 < s['radius'] < s['max_radius']:
                    r = int(s['radius'])
                    wave_alpha = max(0, int(255 * (1 - (s['radius'] / s['max_radius']))))
                    final_alpha = int(wave_alpha * (alpha / 255))
                    if final_alpha > 0:
                        surf_size = int(s['max_radius'] * 2 + 50)
                        circle_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                        num_blocks = max(12, int((2 * math.pi * r) / 18))
                        block_size = int(s['width'] * 2)
                        for i in range(num_blocks):
                            angle = (2 * math.pi / num_blocks) * i
                            pygame.draw.rect(circle_surf, (*s['color'], final_alpha), (surf_size//2 + math.cos(angle) * r - block_size//2, surf_size//2 + math.sin(angle) * r - block_size//2, block_size, block_size))
                        surface.blit(circle_surf, (self.x - surf_size//2 - camera_x, self.y - surf_size//2 - camera_y))
            for p in self.smoke_particles:
                if p['size'] > 0:
                    size = int(p['size'])
                    smoke_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                    pygame.draw.circle(smoke_surf, (*p['color'], max(0, int(alpha * 0.8))), (size//2, size//2), size//2)
                    surface.blit(smoke_surf, (self.x + p['x'] - size//2 - camera_x, self.y + p['y'] - size//2 - camera_y))
                        
        elif self.weapon_name == 'gun':
            for p in self.particles:
                if p['current_radius'] <= 0: continue
                r = int(p['current_radius'])
                circle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.rect(circle_surf, (*p['color'], alpha), (0, 0, r * 2, r * 2))
                surface.blit(circle_surf, (self.x + p['dx'] - r - camera_x, self.y + p['dy'] - r - camera_y))

        elif self.weapon_name == 'flower':
            if self.frames:
                frame_idx = min(int(self.current_frame), len(self.frames) - 1)
                img = self.frames[frame_idx]
                surface.blit(img, (self.x - img.get_width() // 2 - camera_x, self.y - img.get_height() // 2 - camera_y))

        elif self.weapon_name == 'wrench':
            for p in self.particles:
                if alpha <= 0: continue
                size = p['size']
                wrench_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.rect(wrench_surf, (*p['color'], alpha), (0, 0, size, size))
                surface.blit(wrench_surf, (self.x + p['x'] - size//2 - camera_x, self.y + p['y'] - size//2 - camera_y))

        else:
            for p in self.particles:
                if p['current_radius'] <= 0: continue
                total_phase = p['color_phase'] + (self.timer / self.lifetime)
                if total_phase < 0.3: color = (255, 255, 100, alpha)
                elif total_phase < 0.6: color = (255, 160, 50, alpha)
                elif total_phase < 0.9: color = (220, 50, 50, alpha)
                else: color = (int(50 * (1 - alpha/255)), int(50 * (1 - alpha/255)), int(50 * (1 - alpha/255)), alpha)

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
        self.recoil_timer = 0    # Hiệu ứng co giật súng
        
        self.trail = []          
        self.max_trail_len = 6   
        self.spin_speed = 22     
        
        self.explosion = None
        self.last_orbit_hit_time = 0 
        self.is_toxic = False 
        
    def throw(self, target_x, target_y, start_x, start_y):
        # NOTE: Súng (Gun) hiện tại điều khiển đạn độc lập bên gameplay.py
        # Hàm throw này chỉ áp dụng cho các vũ khí cận chiến/ném khác
        if self.state == 'orbit':
            self.thrown_weapon_type = SELECTED_WEAPON
            self.x, self.y = start_x, start_y
            
            if self.thrown_weapon_type in ['bomb', 'bomb1', 'bomb2']:
                self.is_toxic = random.random() < 0.25 
                if self.is_toxic and 'toxic_bomb' in WEAPON_IMAGES_CACHE:
                    self.original_image = WEAPON_IMAGES_CACHE['toxic_bomb']
            else:
                self.is_toxic = False
            
            dx = target_x - start_x
            dy = target_y - start_y
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                self.state = 'thrown'
                speed = 18 if self.thrown_weapon_type == 'axe' else (12 if self.thrown_weapon_type in ['bomb', 'bomb1', 'bomb2'] else 22)
                self.friction = 0.92 if self.thrown_weapon_type == 'axe' else 0.94
                self.vx = (dx / dist) * speed
                self.vy = (dy / dist) * speed
                
                if self.thrown_weapon_type == 'sword':
                    self.spin_speed = 0 
                    self.display_angle = math.degrees(math.atan2(-dy, dx)) - 45 
                else:
                    self.spin_speed = 12 if self.thrown_weapon_type == 'axe' else 22
            
            self.trail.clear()
            self.explosion = None

    def update(self, player_x, player_y, colliders):
        global WEAPON_IMAGES_CACHE
        current_time = pygame.time.get_ticks()
        
        if self.explosion:
            if not self.explosion.update():
                self.explosion = None
        
        if self.state == 'orbit':
            self.is_toxic = False 
            if WEAPON_IMAGES_CACHE and SELECTED_WEAPON in WEAPON_IMAGES_CACHE:
                if self.original_image != WEAPON_IMAGES_CACHE[SELECTED_WEAPON]:
                    self.original_image = WEAPON_IMAGES_CACHE[SELECTED_WEAPON]
                    old_center = self.rect.center
                    self.rect = self.original_image.get_rect()
                    self.rect.center = old_center

            self.angle = (self.angle + self.orbit_speed) % 360
            rad = math.radians(self.angle)
            
            # --- HIỆU ỨNG CO GIẬT SÚNG ---
            if hasattr(self, 'recoil_timer') and self.recoil_timer > 0:
                self.recoil_timer -= 1
                recoil_dist = self.orbit_radius * 0.4
                self.x = player_x + math.cos(self.shoot_angle) * recoil_dist + random.uniform(-4, 4)
                self.y = player_y + math.sin(self.shoot_angle) * recoil_dist + random.uniform(-4, 4)
                self.display_angle = -math.degrees(self.shoot_angle)
            else:
                self.x = player_x + math.cos(rad) * self.orbit_radius
                self.y = player_y + math.sin(rad) * self.orbit_radius
                if SELECTED_WEAPON == 'gun':
                    self.display_angle = -self.angle
                else:
                    self.display_angle = -self.angle - 45
                
            self.rect.center = (int(self.x), int(self.y))
            self.trail.clear()
            
        elif self.state == 'thrown':
            self.x += self.vx
            self.y += self.vy
            self.vx *= self.friction
            self.vy *= self.friction
            
            if self.thrown_weapon_type != 'sword':
                self.display_angle = (self.display_angle + self.spin_speed) % 360
            
            self.rect.center = (int(self.x), int(self.y))
            
            self.trail.append((self.x, self.y, self.display_angle))
            if len(self.trail) > self.max_trail_len:
                self.trail.pop(0)
            
            hit_obstacle = False
            for obs in colliders:
                obs_rect = obs.rect if hasattr(obs, 'rect') else obs
                if isinstance(obs_rect, pygame.Rect) and self.rect.colliderect(obs_rect):
                    hit_obstacle = True
                    if self.thrown_weapon_type == 'flower':
                        cp = globals().get('CURRENT_PLAYER')
                        if cp and hasattr(cp, 'health'):
                            cp.health = min(cp.health + 1, cp.max_health)
                    break 
                    
            if hit_obstacle or math.hypot(self.vx, self.vy) < 0.5:
                self.state = 'disappeared'
                self.action_time = current_time 
                self.rect.center = (-9999, -9999) 
                self.explosion = WeaponExplosion(self.x, self.y, self.thrown_weapon_type)
                
        elif self.state == 'disappeared':
            respawn_cooldown = 1800 if self.thrown_weapon_type in ['bomb', 'bomb1', 'bomb2'] else 500
            if current_time - self.action_time >= respawn_cooldown:
                self.state = 'orbit'

    def draw(self, surface, camera_x=0, camera_y=0):
        if self.explosion:
            self.explosion.draw(surface, camera_x, camera_y)
            
        if self.state == 'disappeared': return
            
        if self.state == 'thrown':
            for i, (tx, ty, tangle) in enumerate(self.trail):
                alpha = int((i + 1) * (180 / self.max_trail_len))
                trail_rotated = pygame.transform.rotate(self.original_image, tangle)
                trail_surf = trail_rotated.copy()
                trail_surf.set_alpha(alpha)
                surface.blit(trail_surf, trail_surf.get_rect(center=(int(tx - camera_x), int(ty - camera_y))))

        rotated_image = pygame.transform.rotate(self.original_image, self.display_angle)
        surface.blit(rotated_image, rotated_image.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y))))

# ==========================================
# LOAD ẢNH VÀ HIỂN THỊ MENU CHỌN VŨ KHÍ
# ==========================================
def load_weapon_images():
    global WEAPON_IMAGES_CACHE
    weapons = {}
    folder = 'weapon'
    if not os.path.exists(folder): os.makedirs(folder)
        
    ignore_files = ['flower2', 'bomb1', 'flowerex'] 
    rename_rules = {'flower1': 'flower', 'bomb2': 'bomb'}

    if os.path.exists(folder):
        for file_name in os.listdir(folder):
            if file_name.lower().endswith(('.png', '.jpg')):
                base_name = file_name.rsplit('.', 1)[0]
                if base_name in ignore_files: continue
                weapon_name = rename_rules.get(base_name, base_name)
                try:
                    img = pygame.image.load(os.path.join(folder, file_name)).convert_alpha()
                    if weapon_name in ['gun', 'bomb', 'flower']:
                        weapons[weapon_name] = pygame.transform.scale(img, (int(70 / 1.2), int(70 / 1.2)))
                    else:
                        weapons[weapon_name] = pygame.transform.scale(img, (70, 70))
                except Exception as e:
                    print(f"Không thể tải ảnh {file_name}: {e}")
                    
    try:
        tb_img = pygame.image.load(os.path.join('specialskill', 'bomb2.png')).convert_alpha()
        weapons['toxic_bomb'] = pygame.transform.scale(tb_img, (int(70 / 1.2), int(70 / 1.2)))
    except:
        dummy_tb = pygame.Surface((58, 58), pygame.SRCALPHA)
        pygame.draw.circle(dummy_tb, (150, 30, 200), (29, 29), 20)
        weapons['toxic_bomb'] = dummy_tb
            
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
        
    WEAPON_IMAGES_CACHE = weapons
    return weapons

def draw_text_with_shadow(text, font, color, surface, x, y):
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, shadow.get_rect(center=(x+3, y+3)))
    surface.blit(font.render(text, True, color), font.render(text, True, color).get_rect(center=(x, y)))

def weapon_selection_menu(screen, clock, WIDTH, HEIGHT, game_assets, transition_out, transition_in):
    global SELECTED_WEAPON
    weapons_data = load_weapon_images()
    weapon_names = [n for n in list(weapons_data.keys()) if n != 'toxic_bomb']
    
    if SELECTED_WEAPON not in weapon_names and weapon_names:
        SELECTED_WEAPON = weapon_names[0]
        
    bg_image = None
    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG']:
        if os.path.exists('background5' + ext):
            bg_image = pygame.transform.scale(pygame.image.load('background5' + ext).convert(), (WIDTH, HEIGHT))
            break
            
    bg_x = 0
    BOX_SIZE, GAP = 120, 30
    cols = max(1, 4 if len(weapon_names) >= 4 else len(weapon_names))
    rows = math.ceil(len(weapon_names) / cols)
    
    start_x = (WIDTH - (cols * BOX_SIZE + (cols - 1) * GAP)) // 2
    start_y = (HEIGHT - (rows * BOX_SIZE + (rows - 1) * GAP)) // 2 + 20 
    
    boxes = [(pygame.Rect(start_x + (i % cols) * (BOX_SIZE + GAP), start_y + (i // cols) * (BOX_SIZE + GAP), BOX_SIZE, BOX_SIZE), name) for i, name in enumerate(weapon_names)]
    btn_back = pygame.Rect(20, 20, 70, 45)

    def draw_screen(mx, my, current_bg_x):
        if bg_image:
            screen.blit(bg_image, (int(current_bg_x), 0))
            screen.blit(bg_image, (int(current_bg_x) - WIDTH, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((30, 30, 40))
            
        draw_text_with_shadow("CHOOSE YOUR WEAPON", game_assets['font_level_title'], (255, 215, 0), screen, WIDTH//2, 80)
        
        pygame.draw.rect(screen, (100, 100, 100) if btn_back.collidepoint((mx, my)) else (50, 50, 50), btn_back, border_radius=10)
        draw_text_with_shadow("<<", game_assets['font_btn'], (255, 255, 255), screen, btn_back.centerx, btn_back.centery)
        
        for rect, name in boxes:
            is_hover = rect.collidepoint((mx, my))
            is_selected = (name == SELECTED_WEAPON)
            
            box_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (80, 80, 90, 200) if is_hover else (50, 50, 60, 200), box_surf.get_rect(), border_radius=15)
            pygame.draw.rect(box_surf, (100, 255, 100) if is_selected else (30, 30, 30), box_surf.get_rect(), width=4 if is_selected else 2, border_radius=15)
            screen.blit(box_surf, rect.topleft)
            
            img = weapons_data[name]
            screen.blit(img, img.get_rect(center=(rect.centerx, rect.centery - 10)))
            draw_text_with_shadow(name.upper(), game_assets['font_level_diff'], (255, 255, 255), screen, rect.centerx, rect.bottom - 20)

    transition_in(clock, lambda: draw_screen(-100, -100, 0))
    
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        bg_x = (bg_x + 1) % WIDTH 
        draw_screen(mx, my, bg_x)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_back.collidepoint((mx, my)):
                    if game_assets.get('sound_button'): game_assets['sound_button'].play()
                    transition_out(clock)
                    running = False
                
                for rect, name in boxes:
                    if rect.collidepoint((mx, my)):
                        if SELECTED_WEAPON != name and game_assets.get('sound_button'):
                            game_assets['sound_button'].play()
                        SELECTED_WEAPON = name
                        
        pygame.display.update()
        clock.tick(60)