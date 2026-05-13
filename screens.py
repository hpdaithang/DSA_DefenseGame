import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, UI_HEIGHT

class GameOverScreen:
    """
    Lớp quản lý và vẽ giao diện màn hình kết thúc (Game Over).
    """
    def __init__(self):
        """Khởi tạo mặc định cho lớp"""
        self.font_large = pygame.font.SysFont("tahoma", 80, bold=True)
        self.font_small = pygame.font.SysFont("tahoma", 40, bold=True)
        
        screen_w = MAP_WIDTH * TILE_SIZE
        screen_h = MAP_HEIGHT * TILE_SIZE + UI_HEIGHT
        
        # Tạo một lớp phủ màu đen mờ
        self.overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180)) 
        
        # Kích thước nút Play Again
        self.btn_rect = pygame.Rect(screen_w // 2 - 120, screen_h // 2 + 50, 240, 60)

    def handle_click(self, pos):
        """kiếm tra thao tác chuột của ng dùng"""
        if self.btn_rect.collidepoint(pos):
            return "RESTART"
        return None

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))
        
        # Vẽ chữ GAME OVER
        title = self.font_large.render("Game Over", True, (255, 50, 50))
        title_rect = title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 50))
        surface.blit(title, title_rect)
        
        # Vẽ nút Play Again
        btn_color = (100, 200, 100)
        if self.btn_rect.collidepoint(pygame.mouse.get_pos()):
            btn_color = (150, 255, 150) # Hiệu ứng Hover
            
        pygame.draw.rect(surface, btn_color, self.btn_rect)
        pygame.draw.rect(surface, (255, 255, 255), self.btn_rect, 3)
        
        btn_text = self.font_small.render("CHƠI LẠI", True, (0, 0, 0))
        text_rect = btn_text.get_rect(center=self.btn_rect.center)
        surface.blit(btn_text, text_rect)