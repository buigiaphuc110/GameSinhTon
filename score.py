import pygame
import sys
import os

# Màu sắc
WHITE = (255, 255, 255)
TITLE_COLOR = (255, 215, 0)

class ScoreManager:
    def __init__(self):
        self.current_score = 0
        self.high_score = 0
        self.filepath = "highscore.txt"
        self.load_high_score()

    def add_points(self, points):
        """Cộng điểm khi diệt quái"""
        self.current_score += points
        if self.current_score > self.high_score:
            self.high_score = self.current_score

    def reset_score(self):
        """Reset điểm về 0 khi bắt đầu ván mới"""
        self.save_high_score()
        self.current_score = 0

    def load_high_score(self):
        """Tải điểm kỷ lục từ file text"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self.high_score = int(f.read())
            except:
                self.high_score = 0

    def save_high_score(self):
        """Lưu điểm kỷ lục vào file text"""
        try:
            with open(self.filepath, "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    def draw_in_game(self, surface, font, x, y):
        """Vẽ điểm lên góc trái màn hình trong lúc chơi"""
        score_text = f"SCORE: {self.current_score}"
        
        # Vẽ viền đen tạo bóng
        shadow = font.render(score_text, True, (0, 0, 0))
        surface.blit(shadow, (x + 2, y + 2))
        
        # Vẽ chữ vàng
        text = font.render(score_text, True, (255, 230, 50))
        surface.blit(text, (x, y))

# Tạo đối tượng toàn cục để các file khác dễ dùng
game_score = ScoreManager()

def draw_text_with_shadow(text, font, color, surface, x, y):
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, shadow.get_rect(center=(x+3, y+3)))
    surface.blit(font.render(text, True, color), font.render(text, True, color).get_rect(center=(x, y)))

def score_menu(screen, clock, WIDTH, HEIGHT, game_assets, transition_out, transition_in):
    """Màn hình hiển thị Bảng Điểm (Dành cho nút SCORE ở Menu chính)"""
    btn_back = pygame.Rect(20, 20, 70, 45)
    game_score.load_high_score() # Tải lại điểm cao nhất mỗi khi mở menu

    def draw_screen(mx, my):
        screen.fill((30, 30, 40))
        draw_text_with_shadow("HIGH SCORE", game_assets['font_level_title'], TITLE_COLOR, screen, WIDTH//2, 100)
        
        # Nút Trở về
        pygame.draw.rect(screen, (100, 100, 100) if btn_back.collidepoint((mx, my)) else (50, 50, 50), btn_back, border_radius=10)
        draw_text_with_shadow("<<", game_assets['font_btn'], WHITE, screen, btn_back.centerx, btn_back.centery)
        
        # Hiển thị số điểm
        draw_text_with_shadow(f"{game_score.high_score} POINTS", game_assets['font_level_title'], (100, 255, 100), screen, WIDTH//2, HEIGHT//2)

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
                    
        pygame.display.update()
        clock.tick(60)