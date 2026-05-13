import pygame
pygame.font.init()

MAP_WIDTH, MAP_HEIGHT = 80, 40
TILE_SIZE = 16
UI_HEIGHT = 120 
FPS = 60

COLORS = {
    'grass': (34, 139, 34),
    'water': (65, 105, 225),
    'grid': (50, 50, 50),
    'cc': (100, 100, 255),       
    'border': (255, 255, 100),   
    'wood': (139, 69, 19),       
    'stone': (128, 128, 128),    
    'coal': (47, 79, 79),        
    'worker': (255, 255, 255),   
    'selection': (0, 255, 0),
    'ui_bg': (40, 40, 40),
    'text': (255, 255, 255),
    'btn': (100, 100, 100),
    'btn_hover': (150, 150, 150),
    'btn_disabled': (50, 50, 50),
    'water_bg' : (65,105,222),
    'road_grass': (169, 169, 169), # Đường đá xám (Xây trên Đất)
    'road_water': (160, 82, 45),    # Cầu gỗ sẫm màu (Xây trên Nước)
    'input_bg': (50, 50, 50),
    'text_gold': (255, 215, 0),
    'white': (255, 255, 255)
}