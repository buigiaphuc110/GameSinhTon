import pygame
import sys
import os
import math
import random
import gameplay
import weapon 
import score # <-- KẾT NỐI VỚI HỆ THỐNG ĐIỂM (SCORE)

# ==========================================
# KHỞI TẠO VÀ CẤU HÌNH CƠ BẢN
# ==========================================
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Sinh Tồn 2D - Pixel Edition")

# --- MÀU SẮC ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (50, 50, 50, 180) 
HOVER_COLOR = (100, 100, 100, 200) 
TITLE_COLOR = (255, 215, 0) 
LEVEL_TITLE_COLOR = (200, 230, 255)

COLOR_EASY = (100, 255, 100)
COLOR_NORMAL = (255, 255, 100)
COLOR_HARD = (255, 150, 50)
COLOR_ENDLESS = (255, 50, 50)


# ==========================================
# HÀM LOAD TÀI NGUYÊN (ASSETS)
# ==========================================
def load_assets():
    assets = {}
    
    # Background chính
    if os.path.exists('background.png') and os.path.exists('background2.png'):
        assets['bg1'] = pygame.transform.scale(pygame.image.load('background.png').convert(), (WIDTH, HEIGHT))
        assets['bg2'] = pygame.transform.scale(pygame.image.load('background2.png').convert(), (WIDTH, HEIGHT))
    else:
        assets['bg1'] = assets['bg2'] = None

    # Background chọn màn chơi
    bg3_frames = []
    frame_idx = 1
    while True:
        frame_name = f"background3_{frame_idx}.png"
        if os.path.exists(frame_name):
            bg3_frames.append(pygame.transform.scale(pygame.image.load(frame_name).convert(), (WIDTH, HEIGHT)))
            frame_idx += 1
        else:
            break
            
    if not bg3_frames and os.path.exists('background3.png'):
        bg3_frames.append(pygame.transform.scale(pygame.image.load('background3.png').convert(), (WIDTH, HEIGHT)))
    assets['bg3'] = bg3_frames if bg3_frames else None

    # Load toàn bộ background ground 1 -> 4
    for i in range(1, 5):
        ground_key = f'ground{i}'
        file_name = f'{ground_key}.png'
        if os.path.exists(file_name):
            img = pygame.image.load(file_name).convert()
            assets[ground_key] = pygame.transform.scale(img, (WIDTH, HEIGHT))
        else:
            assets[ground_key] = None

    # Load mây bay
    cloud_assets = []
    cloud_size_ranges = [(150, 60, 200, 80), (200, 80, 250, 100), (250, 100, 300, 120), (300, 120, 350, 140), (350, 140, 450, 180)]
    if os.path.exists('cloud.png'):
        cloud_base = pygame.image.load('cloud.png').convert_alpha()
        for min_w, min_h, max_w, max_h in cloud_size_ranges:
            cloud_img = pygame.transform.scale(cloud_base, (random.randint(min_w, max_w), random.randint(min_h, max_h)))
            cloud_alpha = cloud_img.copy()
            cloud_alpha.fill((255, 255, 255, 153), special_flags=pygame.BLEND_RGBA_MULT)
            cloud_assets.append(cloud_alpha)
    else:
        for min_w, min_h, max_w, max_h in cloud_size_ranges:
            dummy = pygame.Surface((random.randint(min_w, max_w), random.randint(min_h, max_h)), pygame.SRCALPHA)
            dummy.fill((255, 255, 255, 100)) 
            cloud_assets.append(dummy)
    assets['clouds'] = cloud_assets

    # Load whiteball
    if os.path.exists('whiteball.png'):
        assets['whiteball'] = pygame.transform.scale(pygame.image.load('whiteball.png').convert_alpha(), (30, 30))
    else:
        dummy_ball = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(dummy_ball, WHITE, (15, 15), 15)
        assets['whiteball'] = dummy_ball

    # Load ảnh các nút chọn màn
    base_names = ['game1', 'game2', 'game3', 'endless']
    level_keys = ['level1', 'level2', 'level3', 'level4']
    for i, base in enumerate(base_names):
        frames = []
        frame_idx = 1
        while True:
            frame_name = f"{base}_{frame_idx}.png"
            if os.path.exists(frame_name):
                frames.append(pygame.image.load(frame_name).convert())
                frame_idx += 1
            else:
                break
        if not frames and os.path.exists(f"{base}.png"):
            frames.append(pygame.image.load(f"{base}.png").convert())
        assets[level_keys[i]] = frames 

    # Load Fonts
    if os.path.exists('pixel_font.ttf'):
        assets['font_title'] = pygame.font.Font('pixel_font.ttf', 60)
        assets['font_btn'] = pygame.font.Font('pixel_font.ttf', 30)
    else:
        assets['font_title'] = pygame.font.SysFont(None, 70)
        assets['font_btn'] = pygame.font.SysFont(None, 40)
        
    if os.path.exists('pixel_font2.ttf'):
        assets['font_level_title'] = pygame.font.Font('pixel_font2.ttf', 45) 
        assets['font_level_diff'] = pygame.font.Font('pixel_font2.ttf', 20)  
        assets['font_level_txt'] = pygame.font.Font('pixel_font2.ttf', 30)
    else:
        assets['font_level_title'] = pygame.font.SysFont(None, 55)
        assets['font_level_diff'] = pygame.font.SysFont(None, 25)
        assets['font_level_txt'] = assets['font_btn']
        
    return assets

# Tải tài nguyên ngay khi khởi động
game_assets = load_assets()


# ==========================================
# CÁC LỚP ĐỐI TƯỢNG (CLASSES)
# ==========================================
class Cloud:
    def __init__(self, image, start_side): 
        self.image = image
        self.y = random.randint(20, 150) 
        self.speed = random.uniform(1.0, 3.0)
        self.side = start_side
        
        if self.side == 'left':
            self.x = -self.image.get_width()
            self.move_to = 'right'
        else:
            self.x = WIDTH
            self.move_to = 'left'
            
    def update(self):
        if self.move_to == 'right':
            self.x += self.speed
            if self.x > WIDTH:
                self.move_to = 'left'
                self.y = random.randint(20, 150)
        else:
            self.x -= self.speed
            if self.x < -self.image.get_width():
                self.move_to = 'right'
                self.y = random.randint(20, 150)
                
    def draw(self, surface): 
        surface.blit(self.image, (self.x, self.y))


class Whiteball:
    def __init__(self, image, x_start):
        self.image = image
        self.x = x_start
        self.base_y = HEIGHT - 40 
        self.jump_height = random.randint(30, 60)
        self.jump_speed = random.uniform(0.005, 0.008) 
        self.time_offset = random.uniform(0, math.pi)
        self.current_y = self.base_y
        
    def update(self, time_now):
        self.current_y = self.base_y - abs(math.sin(time_now * self.jump_speed + self.time_offset) * self.jump_height)
        
    def draw(self, surface): 
        surface.blit(self.image, (self.x, self.current_y))


# ==========================================
# CÁC HÀM TIỆN ÍCH (UTILITIES)
# ==========================================
def draw_text_with_shadow(text, font, color, surface, x, y):
    shadow_rect = font.render(text, True, BLACK).get_rect(center=(x+3, y+3))
    surface.blit(font.render(text, True, BLACK), shadow_rect)
    textrect = font.render(text, True, color).get_rect(center=(x, y))
    surface.blit(font.render(text, True, color), textrect)

def draw_styled_button(surface, rect, color, text, font):
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect(), border_radius=10)
    surface.blit(shape_surf, rect.topleft)
    draw_text_with_shadow(text, font, WHITE, surface, rect.centerx, rect.centery)

def transition_to_black_pixel(clock):
    pixel_size = 16 
    small_w = WIDTH // pixel_size
    small_h = HEIGHT // pixel_size
    max_radius = int((small_w**2 + small_h**2)**0.5) + 2 
    
    for r in range(0, max_radius, 2):
        small_surf = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
        pygame.draw.circle(small_surf, BLACK, (small_w // 2, small_h // 2), r)
        screen.blit(pygame.transform.scale(small_surf, (WIDTH, HEIGHT)), (0, 0))
        pygame.display.update()
        clock.tick(60)

def transition_fade_in(clock, draw_func):
    black_surf = pygame.Surface((WIDTH, HEIGHT))
    for alpha in range(255, -1, -15):
        draw_func() 
        black_surf.set_alpha(alpha)
        screen.blit(black_surf, (0, 0))
        pygame.display.update()
        clock.tick(60)


# ==========================================
# GIAO DIỆN CHỌN MÀN CHƠI
# ==========================================
def level_selection_menu(clock):
    FRAME_W, FRAME_H, GAP = 160, 230, 30 
    start_x = (WIDTH - (4 * FRAME_W + 3 * GAP)) // 2
    
    frames_base = [pygame.Rect(start_x + i * (FRAME_W + GAP), 230, FRAME_W, FRAME_H) for i in range(4)]
    btn_back = pygame.Rect(20, 20, 70, 45) 
    
    # Thiết lập tham số gán cho từng nút bấm
    level_keys = ['level1', 'level2', 'level3', 'level4']
    hover_texts = [
        ("EASY", COLOR_EASY), 
        ("MEDIUM", COLOR_NORMAL), 
        ("HARD", COLOR_HARD), 
        ("ENDLESS", COLOR_ENDLESS)
    ]
    mode_ground_mapping = ['ground1', 'ground2', 'ground3', 'ground4']
    
    clouds = [Cloud(game_assets['clouds'][i], 'left' if i % 2 == 0 else 'right') for i in range(5)]
    whiteballs = [Whiteball(game_assets['whiteball'], x) for x in (30, 80, WIDTH - 60, WIDTH - 110)]

    def draw_screen(mx=-100, my=-100):
        time_now = pygame.time.get_ticks() 
        
        # Vẽ Background
        if game_assets['bg3']: 
            screen.blit(game_assets['bg3'][(time_now // 200) % len(game_assets['bg3'])], (0, 0))
        else: 
            screen.fill((30, 30, 40)) 
            
        # Cập nhật và vẽ Mây & Whiteballs
        for cloud in clouds: 
            cloud.update()
            cloud.draw(screen)
        for ball in whiteballs: 
            ball.update(time_now)
            ball.draw(screen)
            
        # Tiêu đề và nút Back
        draw_text_with_shadow('SELECT A STAGE', game_assets['font_level_title'], LEVEL_TITLE_COLOR, screen, WIDTH//2, 60)
        draw_styled_button(screen, btn_back, HOVER_COLOR if btn_back.collidepoint((mx, my)) else BUTTON_COLOR, '<<', game_assets['font_btn'])

        # Vẽ danh sách màn chơi
        for i, rect in enumerate(frames_base):
            is_hover = rect.collidepoint((mx, my))
            frame_rect = rect.inflate(12, 12)
            
            # Khung viền ảnh
            pygame.draw.rect(screen, (200, 160, 40), frame_rect, border_radius=8) 
            pygame.draw.rect(screen, (70, 50, 15), frame_rect, width=4, border_radius=8) 
            
            # Ảnh thumbnail màn chơi
            if game_assets[level_keys[i]]:
                img = game_assets[level_keys[i]][(time_now // 150) % len(game_assets[level_keys[i]])]
                screen.blit(pygame.transform.scale(img, rect.size), rect.topleft)
            else:
                pygame.draw.rect(screen, (70, 70, 80), rect)
                draw_text_with_shadow(f"IMG {i+1}", game_assets['font_level_txt'], (150, 150, 150), screen, rect.centerx, rect.centery)

            # Hiệu ứng hover cho ảnh
            if is_hover:
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((255, 255, 255, 60 + int(math.sin(time_now * 0.01) * 30))) 
                screen.blit(overlay, rect.topleft)

            # Badge độ khó
            text_str, text_color = hover_texts[i]
            box_w, box_h = game_assets['font_level_diff'].size(text_str)
            text_bg_rect = pygame.Rect(frame_rect.centerx - (box_w + 16) // 2, frame_rect.top - (box_h + 10) - 15, box_w + 16, box_h + 10)
            
            pygame.draw.rect(screen, (40, 40, 50, 200), text_bg_rect, border_radius=6)
            pygame.draw.rect(screen, text_color, text_bg_rect, width=2, border_radius=6)
            draw_text_with_shadow(text_str, game_assets['font_level_diff'], text_color, screen, text_bg_rect.centerx, text_bg_rect.centery)

    transition_fade_in(clock, draw_screen)

    click = False
    while True:
        mx, my = pygame.mouse.get_pos()
        draw_screen(mx, my)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        if click:
            if btn_back.collidepoint((mx, my)):
                transition_to_black_pixel(clock)
                return 
            
            for i, rect in enumerate(frames_base):
                if rect.collidepoint((mx, my)):
                    transition_to_black_pixel(clock) 
                    
                    # --- GỌI HÀM GAMEPLAY CHUNG VÀ TRUYỀN PARAMETER VÀO ---
                    mode_name = hover_texts[i][0]  
                    ground_key = mode_ground_mapping[i] 
                    gameplay.run_game_mode(screen, clock, WIDTH, HEIGHT, game_assets, transition_to_black_pixel, mode_name, ground_key)
                    
                    # Cập nhật fade-in lại khi quay về màn chọn level
                    transition_fade_in(clock, lambda: draw_screen(mx, my))
            click = False
            
        pygame.display.update()
        clock.tick(60)


# ==========================================
# GIAO DIỆN MENU CHÍNH
# ==========================================
def main_menu():
    click = False
    clock = pygame.time.Clock()
    bg_x = 0
    
    while True:
        # Cập nhật cuộn Background
        if game_assets['bg1'] and game_assets['bg2']:
            for i in range(4): 
                screen.blit(game_assets['bg1' if i % 2 == 0 else 'bg2'], (bg_x + WIDTH * i, 0))
            bg_x -= 1
            if bg_x <= -(WIDTH * 2): 
                bg_x = 0
        else: 
            screen.fill(BLACK) 
        
        # Tiêu đề
        draw_text_with_shadow('GAME SINH TỒN 2D', game_assets['font_title'], TITLE_COLOR, screen, WIDTH//2, 100)
        
        # Lấy tọa độ chuột
        mx, my = pygame.mouse.get_pos()

        # Tạo danh sách các nút
        buttons = [
            (pygame.Rect((WIDTH - 220)//2, 220 + 80 * i, 220, 60), text) 
            for i, text in enumerate(['START', 'WEAPON', 'SCORE', 'EXIT'])
        ]

        # Vẽ nút bấm
        for rect, text in buttons:
            is_hover = rect.collidepoint((mx, my))
            draw_styled_button(screen, rect, HOVER_COLOR if is_hover else BUTTON_COLOR, text, game_assets['font_btn'])

        # Xử lý Click Menu
        if click:
            if buttons[0][0].collidepoint((mx, my)):
                transition_to_black_pixel(clock) 
                level_selection_menu(clock)      
                transition_fade_in(clock, lambda: screen.fill(BLACK)) 
            elif buttons[1][0].collidepoint((mx, my)): 
                # --- Gọi hàm chọn vũ khí từ module weapon ---
                transition_to_black_pixel(clock)
                weapon.weapon_selection_menu(screen, clock, WIDTH, HEIGHT, game_assets, transition_to_black_pixel, transition_fade_in)
                transition_fade_in(clock, lambda: screen.fill(BLACK))
            elif buttons[2][0].collidepoint((mx, my)): 
                # --- THÊM THEO YÊU CẦU: Hiển thị Bảng Điểm (Score Menu) ---
                transition_to_black_pixel(clock)
                score.score_menu(screen, clock, WIDTH, HEIGHT, game_assets, transition_to_black_pixel, transition_fade_in)
                transition_fade_in(clock, lambda: screen.fill(BLACK))
            elif buttons[3][0].collidepoint((mx, my)): 
                pygame.quit()
                sys.exit()
                
            click = False

        # Bắt sự kiện Window
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                click = True

        pygame.display.update()
        clock.tick(60)


if __name__ == '__main__': 
    main_menu()