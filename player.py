import pygame
import math

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class Player:
    def __init__(self, start_x, start_y):
        self.x = start_x
        self.y = start_y
        self.radius = 20
        self.hitbox_radius = 18
        
        self.base_speed = 3.05
        
        # Biến ẩn lưu trữ máu thực sự
        self._health = 100.0  
        self.max_health = 100
        
        # --- CƠ CHẾ BẤT TỬ (I-FRAMES) ---
        self.invincible_until = 0       # Thời điểm (ms) kết thúc bất tử
        self.invincibility_duration = 500 # 500ms = 0.5 giây
        
        # Biến tạo quán tính (dùng cho knockback)
        self.vx = 0.0
        self.vy = 0.0
        
        self.water_timer = 0.0
        self.in_grass = False
        self.in_water = False
        
        # Biến quản lý Lava
        self.in_lava = False
        self.lava_damage_timer = 0.0

    # ==========================================
    # LỚP MÀNG LỌC BẢO VỆ MÁU THÔNG MINH
    # ==========================================
    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        current_time = pygame.time.get_ticks()
        
        # Nếu Player đang bị trừ máu (nhận sát thương)
        if value < self._health:
            damage_taken = self._health - value
            
            # Nếu đang trong thời gian bất tử -> Chặn sát thương, không làm gì cả
            if current_time < self.invincible_until:
                return 
                
            # Áp dụng trừ máu
            self._health = value
            
            # Nếu lượng sát thương nhận vào > 5 -> Kích hoạt 0.5s bất tử
            if damage_taken > 4:
                self.invincible_until = current_time + self.invincibility_duration
        else:
            # Nếu là Hồi máu (Heal) hoặc cài đặt máu ban đầu thì cho phép bình thường
            self._health = value

    def handle_movement(self, keys, all_obstacles, grasses, mode_name, width, height):
        current_rect = pygame.Rect(self.x - self.hitbox_radius, self.y - self.hitbox_radius, self.hitbox_radius * 2, self.hitbox_radius * 2)
        if mode_name in ['EASY', 'MEDIUM', 'HARD']:
            self.in_grass = any(current_rect.colliderect(g) for g in grasses)
        else:
            self.in_grass = False

        current_speed = self.base_speed / 1.5 if self.in_water else (self.base_speed / 2 if self.in_grass else self.base_speed)

        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= current_speed
        if keys[pygame.K_s]: dy += current_speed
        if keys[pygame.K_a]: dx -= current_speed
        if keys[pygame.K_d]: dx += current_speed

        # CỘNG VẬN TỐC QUÁN TÍNH VÀO HƯỚNG DI CHUYỂN
        dx += self.vx
        dy += self.vy
        
        # ÁP DỤNG MA SÁT (Giảm tốc độ văng dần dần)
        self.vx *= 0.85
        self.vy *= 0.85
        if abs(self.vx) < 0.1: self.vx = 0
        if abs(self.vy) < 0.1: self.vy = 0

        self.x += dx
        player_rect = pygame.Rect(self.x - self.hitbox_radius, self.y - self.hitbox_radius, self.hitbox_radius * 2, self.hitbox_radius * 2)
        for obs in all_obstacles:
            obs_hitbox = obs.inflate(-16, -16)
            if player_rect.colliderect(obs_hitbox):
                if dx > 0: self.x = obs_hitbox.left - self.hitbox_radius; self.vx = 0
                elif dx < 0: self.x = obs_hitbox.right + self.hitbox_radius; self.vx = 0

        self.y += dy
        player_rect = pygame.Rect(self.x - self.hitbox_radius, self.y - self.hitbox_radius, self.hitbox_radius * 2, self.hitbox_radius * 2)
        for obs in all_obstacles:
            obs_hitbox = obs.inflate(-16, -16)
            if player_rect.colliderect(obs_hitbox):
                if dy > 0: self.y = obs_hitbox.top - self.hitbox_radius; self.vy = 0
                elif dy < 0: self.y = obs_hitbox.bottom + self.hitbox_radius; self.vy = 0

        if mode_name != 'ENDLESS':
            if self.x - self.radius < 0: self.x = self.radius; self.vx = 0
            if self.x + self.radius > width: self.x = width - self.radius; self.vx = 0
            if self.y - self.radius < 0: self.y = self.radius; self.vy = 0
            if self.y + self.radius > height: self.y = height - self.radius; self.vy = 0

    def take_damage_and_knockback(self, damage, source_x, source_y, force, width, height, mode_name):
        # Chặn lực văng (knockback) nếu đang trong trạng thái bất tử
        if pygame.time.get_ticks() < self.invincible_until:
            return

        # Việc gán self.health ở đây sẽ tự động kích hoạt bộ lọc @health.setter ở trên
        self.health = max(0.0, self.health - damage)
        
        dx = self.x - source_x
        dy = self.y - source_y
        dist = math.hypot(dx, dy)
        
        if dist == 0: 
            dx, dy, dist = 1, 0, 1
            
        # ÁP LỰC VÀO QUÁN TÍNH THAY VÌ DỊCH CHUYỂN TỨC THỜI
        self.vx += (dx / dist) * force
        self.vy += (dy / dist) * force

    def update_environment_logic(self, mode_name, width, height):
        if mode_name == 'HARD':
            x1, y1 = 0, int(height * 0.40)
            x2, y2 = int(width * 0.90), height
            m = (y2 - y1) / (x2 - x1) if (x2 - x1) != 0 else 0
            line_y = m * self.x + y1
            
            if self.y < line_y: 
                self.in_water = True
                self.water_timer = min(15.0, self.water_timer + 1/60)
            else: 
                self.in_water = False
                self.water_timer = max(0.0, self.water_timer - 1/60)
                
            if self.water_timer >= 15.0: 
                self.health = 0.0
                return False
        else: 
            self.water_timer = 0.0
            self.in_water = False
        return True

    def update_lava_logic(self, dt):
        """Hàm xử lý trừ máu liên tục và mượt mà khi đứng trong Lava"""
        if self.in_lava:
            damage_per_second = 45.0 
            # Cứ mỗi frame bị trừ 1 xíu máu (vd: 0.75 máu). Vì bé hơn 5 nên sẽ không bị kích hoạt bất tử
            # Nhưng nếu đang bất tử sẵn thì nó sẽ không trừ
            self.health -= damage_per_second * dt
            
            if self.health < 0:
                self.health = 0.0
        else:
            self.lava_damage_timer = 0.0

    def draw(self, screen, draw_x, draw_y, font_level_diff):
        player_color, player_border_color, visual_bob_y = (240, 40, 40), (180, 20, 20), 0
        
        if self.water_timer > 0:
            ratio = self.water_timer / 15.0
            target_blue, target_border = (15, 25, 140), (5, 10, 85)
            player_color = (
                int(240 + (target_blue[0] - 240) * ratio), 
                int(40 + (target_blue[1] - 40) * ratio), 
                int(40 + (target_blue[2] - 40) * ratio)
            )
            player_border_color = (
                int(180 + (target_border[0] - 180) * ratio), 
                int(20 + (target_border[1] - 20) * ratio), 
                int(20 + (target_border[2] - 20) * ratio)
            )
            if self.in_water: 
                visual_bob_y = math.sin(pygame.time.get_ticks() / 150.0) * 3

        final_draw_y = int(draw_y + visual_bob_y)
        
        # --- KIỂM TRA TRẠNG THÁI BẤT TỬ ĐỂ TẠO HIỆU ỨNG NHẤP NHÁY ---
        is_invincible = pygame.time.get_ticks() < self.invincible_until
        show_player = True
        
        # Nếu đang bất tử, nhấp nháy (chớp tắt) mỗi 50ms
        if is_invincible and (pygame.time.get_ticks() // 50) % 2 == 0:
            show_player = False

        if show_player:
            pygame.draw.circle(screen, BLACK, (int(draw_x) + 2, final_draw_y + 3), self.radius)
            pygame.draw.circle(screen, player_color, (int(draw_x), final_draw_y), self.radius)
            pygame.draw.circle(screen, player_border_color, (int(draw_x), final_draw_y), self.radius, width=3)
            pygame.draw.circle(screen, WHITE, (int(draw_x - 6), final_draw_y - 6), 5)

        # Mặc dù nhấp nháy tàng hình, gợn sóng nước vẫn vẽ bình thường
        if self.in_water:
            light_blue, dark_blue = (210, 240, 255), (60, 120, 220)
            t = pygame.time.get_ticks() / 150.0
            wave_offsets = [
                (-26, -4, light_blue, 0.0), (-5, -10, dark_blue, 3.14), 
                (-5, 6, light_blue, 1.0), (10, -9, light_blue, 2.0), 
                (-20, 3, dark_blue, 5.0), (10, 9, dark_blue, 3.5)
            ]
            for rx, ry, color, phase in wave_offsets:
                r_bob = math.sin(t + phase) * 2.5
                wave_surf = font_level_diff.render("~", True, color)
                wave_surf = pygame.transform.scale(wave_surf, (wave_surf.get_width() * 2, wave_surf.get_height() * 2))
                screen.blit(wave_surf, (int(draw_x) + rx, final_draw_y + ry + int(r_bob)))