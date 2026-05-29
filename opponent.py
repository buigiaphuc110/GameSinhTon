import pygame
import math

class EnemyNor:
    def __init__(self, x, y, frames):
        self.x = float(x)
        self.y = float(y)
        
        # Xử lý giảm kích thước 1.4 lần
        self.frames = []
        for frame in frames:
            w, h = frame.get_size()
            scaled_frame = pygame.transform.scale(frame, (int(w / 1.65), int(h / 1.4)))
            self.frames.append(scaled_frame)
            
        self.frame_index = 0
        self.frame_rate = 100 
        self.last_frame_time = pygame.time.get_ticks()
        
        self.speed = 30 
        self.radius = 30 / 1.4 
        self.damage_cooldown = 1000 
        self.last_damage_time = 0
        
        self.angle = 0 

        # --- Hệ thống máu ---
        self.max_health = 100  # Bạn có thể điều chỉnh lượng máu tùy ý
        self.health = self.max_health
        
        # Tạo khung Hitbox Rect cố định để đồng bộ với cơ chế check va chạm của Vũ khí
        if self.frames:
            fw, fh = self.frames[0].get_size()
            self.rect = pygame.Rect(0, 0, fw, fh)
        else:
            self.rect = pygame.Rect(0, 0, 32, 32)
        self.rect.center = (int(self.x), int(self.y))

    def take_damage(self, amount):
        """Hàm nhận sát thương từ vũ khí"""
        self.health -= amount
        if self.health < 0:
            self.health = 0
        return self.health <= 0  # Trả về True nếu quái chết

    def update(self, player, dt, width, height, mode_name):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            # Di chuyển về phía người chơi
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
            
            # --- Xử lý hướng mặt ---
            # Cộng thêm 180 độ vì ảnh gốc của con Nor đang hướng sang trái
            self.angle = math.degrees(math.atan2(-dy, dx)) + 180

        # Cập nhật vị trí Hitbox liên tục để vũ khí đâm trúng
        self.rect.center = (int(self.x), int(self.y))

        # Xử lý animation
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_time > self.frame_rate:
            if self.frames:
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_frame_time = current_time

        # Gây sát thương cho Player
        if dist < self.radius + player.radius:
            if current_time - self.last_damage_time > self.damage_cooldown:
                if hasattr(player, 'take_damage_and_knockback'):
                    player.take_damage_and_knockback(5, self.x, self.y, 10, width, height, mode_name)
                else:
                    player.health -= 5
                self.last_damage_time = current_time

    def draw(self, screen, camera_x, camera_y):
        if not self.frames: return
        
        # Tọa độ vẽ sau khi trừ đi camera
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        # Xoay và vẽ quái vật
        img = self.frames[self.frame_index]
        rotated_img = pygame.transform.rotate(img, self.angle)
        rect = rotated_img.get_rect(center=(draw_x, draw_y))
        
        screen.blit(rotated_img, rect)

        # --- Thanh máu Pixel nhỏ gọn trên đầu ---
        if self.health < self.max_health: # Chỉ hiện khi quái bị mất máu
            bar_width = 20   # Chiều ngang thanh máu
            bar_height = 3   # Chiều cao thanh máu mỏng chuẩn pixel
            offset_y = 20    # Khoảng cách so với tâm quái vật
            
            # Tọa độ góc trên bên trái của thanh máu
            bx = draw_x - bar_width // 2
            by = draw_y - offset_y
            
            # 1. Vẽ viền đen (Pixel Border) bằng khối màu đen đặc bọc ngoài
            pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, bar_width + 2, bar_height + 2))
            
            # 2. Vẽ Nền máu trống (Empty Health) - Màu đỏ sẫm
            pygame.draw.rect(screen, (50, 15, 15), (bx, by, bar_width, bar_height))
            
            # 3. Vẽ Thanh máu hiện tại (Current Health) - Màu xanh lá pixel
            health_ratio = self.health / self.max_health
            current_bar_width = int(bar_width * health_ratio)
            
            if current_bar_width > 0:
                pygame.draw.rect(screen, (60, 230, 60), (bx, by, current_bar_width, bar_height))