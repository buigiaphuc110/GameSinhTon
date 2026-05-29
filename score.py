import pygame
import sys
import os

# Màu sắc chủ đạo
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TITLE_COLOR = (255, 215, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
PANEL_BG = (30, 30, 45, 230)
PANEL_BORDER = (100, 100, 150)

class ScoreManager:
    def __init__(self):
        self.current_score = 0
        self.high_score = 0      # Khôi phục biến này để các file khác không bị lỗi
        self.top_scores = []
        self.filepath = "highscore.txt"
        self.score_saved = False
        self.load_high_score()

    def add_points(self, points):
        """Cộng điểm khi diệt quái"""
        self.current_score += points
        # Đồng bộ với điểm cao nhất hiện tại
        if self.current_score > self.high_score:
            self.high_score = self.current_score

    def reset_score(self):
        """Lưu điểm hiện tại vào top 10 và Reset điểm về 0 khi bắt đầu ván mới"""
        self.save_high_score()
        self.current_score = 0
        self.score_saved = False  # Đặt lại cờ trạng thái cho ván mới

    def load_high_score(self):
        """Tải danh sách 10 điểm kỷ lục từ file text"""
        self.top_scores = []
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        val = line.strip()
                        if val.isdigit():
                            self.top_scores.append(int(val))
                # Sắp xếp giảm dần và lấy tối đa 10 điểm
                self.top_scores = sorted(self.top_scores, reverse=True)[:10]
                
                # Cập nhật high_score bằng Top 1
                if self.top_scores:
                    self.high_score = self.top_scores[0]
                    
            except Exception as e:
                print("Lỗi đọc file điểm:", e)

    def save_high_score(self):
        """Lưu điểm hiện tại vào top 10 và ghi ra file text"""
        if self.current_score > 0 and not getattr(self, 'score_saved', False):
            self.top_scores.append(self.current_score)
            self.top_scores = sorted(self.top_scores, reverse=True)[:10]
            self.score_saved = True # Đánh dấu để tránh lưu trùng lặp một điểm nhiều lần
            
            if self.top_scores:
                self.high_score = self.top_scores[0]
            
        try:
            with open(self.filepath, "w") as f:
                for score in self.top_scores:
                    f.write(f"{score}\n")
        except Exception as e:
            print("Lỗi lưu file điểm:", e)

    def draw_in_game(self, surface, font, x, y):
        """Vẽ điểm lên góc trái màn hình khi đang chơi"""
        shadow = font.render(f"SCORE: {self.current_score}", True, BLACK)
        surface.blit(shadow, shadow.get_rect(topleft=(x + 2, y + 2)))
        text = font.render(f"SCORE: {self.current_score}", True, WHITE)
        surface.blit(text, text.get_rect(topleft=(x, y)))

# Tạo một instance toàn cục để các file khác import vào dùng chung
game_score = ScoreManager()

def draw_text_with_shadow(text, font, color, surface, x, y):
    """Tiện ích vẽ chữ có đổ bóng"""
    shadow = font.render(text, True, BLACK)
    surface.blit(shadow, shadow.get_rect(center=(x + 3, y + 3)))
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, text_surf.get_rect(center=(x, y)))

def draw_panel(surface, rect):
    """Vẽ bảng điều khiển mang phong cách pixel-art"""
    # Nền đen mờ
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, PANEL_BG, shape_surf.get_rect(), border_radius=15)
    
    # Viền ngoài
    pygame.draw.rect(shape_surf, PANEL_BORDER, shape_surf.get_rect(), width=4, border_radius=15)
    
    # Viền trong (Tạo chiều sâu)
    inner_rect = shape_surf.get_rect().inflate(-16, -16)
    pygame.draw.rect(shape_surf, (60, 60, 80, 200), inner_rect, width=2, border_radius=10)
    
    surface.blit(shape_surf, rect.topleft)

def score_menu(screen, clock, WIDTH, HEIGHT, game_assets, transition_out, transition_in):
    """Màn hình hiển thị Bảng Điểm TOP 10 (Dành cho nút SCORE ở Menu chính)"""
    btn_back = pygame.Rect(20, 20, 70, 45)
    game_score.load_high_score() # Tải lại điểm mỗi khi mở menu

    # Kích thước bảng điểm
    panel_width = 460
    panel_height = 550
    panel_rect = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2 + 30, panel_width, panel_height)

    def draw_screen(mx, my):
        # Màn hình nền tối
        screen.fill((20, 20, 30))
        
        # Tiêu đề chính
        draw_text_with_shadow("LEADERBOARD", game_assets['font_title'], TITLE_COLOR, screen, WIDTH // 2, 70)
        
        # Nút Trở về
        is_back_hover = btn_back.collidepoint((mx, my))
        pygame.draw.rect(screen, (100, 100, 100) if is_back_hover else (50, 50, 50), btn_back, border_radius=10)
        pygame.draw.rect(screen, (200, 200, 200), btn_back, width=2, border_radius=10)
        draw_text_with_shadow("<<", game_assets['font_btn'], WHITE, screen, btn_back.centerx, btn_back.centery)
        
        # Vẽ khung bảng điểm
        draw_panel(screen, panel_rect)
        
        # Tiêu đề trong bảng điểm
        draw_text_with_shadow("TOP 10 BEST SCORES", game_assets['font_level_diff'], (200, 220, 255), screen, panel_rect.centerx, panel_rect.y + 40)
        pygame.draw.line(screen, PANEL_BORDER, (panel_rect.x + 50, panel_rect.y + 70), (panel_rect.right - 50, panel_rect.y + 70), 3)
        
        # In danh sách Top 10
        start_y = panel_rect.y + 105
        gap_y = 40
        
        if not game_score.top_scores:
            draw_text_with_shadow("NO SCORES YET", game_assets['font_level_diff'], (120, 120, 120), screen, panel_rect.centerx, panel_rect.centery)
        else:
            for i in range(10):
                y_pos = start_y + i * gap_y
                rank_str = f"#{i + 1}"
                
                # Cấp màu cho huy chương Vàng, Bạc, Đồng
                if i == 0: color = GOLD
                elif i == 1: color = SILVER
                elif i == 2: color = BRONZE
                else: color = (220, 220, 220) if i < len(game_score.top_scores) else (100, 100, 100)
                
                if i < len(game_score.top_scores):
                    score_val = f"{game_score.top_scores[i]:,}" # Định dạng số có dấu phẩy
                else:
                    score_val = "---"

                # 1. Vẽ hạng (RANK) căn lề trái
                text_rank = game_assets['font_level_diff'].render(rank_str, True, color)
                shadow_rank = game_assets['font_level_diff'].render(rank_str, True, BLACK)
                screen.blit(shadow_rank, (panel_rect.x + 62, y_pos + 2))
                screen.blit(text_rank, (panel_rect.x + 60, y_pos))

                # 2. Vẽ điểm (SCORE) căn lề phải
                text_score = game_assets['font_level_diff'].render(score_val, True, color)
                shadow_score = game_assets['font_level_diff'].render(score_val, True, BLACK)
                
                score_rect = text_score.get_rect(topright=(panel_rect.right - 60, y_pos))
                shadow_rect = shadow_score.get_rect(topright=(panel_rect.right - 58, y_pos + 2))
                
                screen.blit(shadow_score, shadow_rect)
                screen.blit(text_score, score_rect)

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                transition_out(clock)
                running = False
                
        pygame.display.update()
        clock.tick(60)