"""
Module quản lý Giao diện người dùng (UI) cho game.
Xử lý hiển thị thông tin công trình, bảng giá tài nguyên, quản lý vận chuyển và nhật ký.
"""
import pygame
import os
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, UI_HEIGHT, COLORS

class UIManager:
    """Lớp quản lý toàn bộ giao diện điều khiển phía dưới màn hình."""
    
    def __init__(self):
        self.font = pygame.font.SysFont("tahoma", 20, bold=True)
        self.small_font = pygame.font.SysFont("tahoma", 16)
        self.selected_building = None
        self.panel_rect = pygame.Rect(0, MAP_HEIGHT * TILE_SIZE, MAP_WIDTH * TILE_SIZE, UI_HEIGHT)
        
        self.mode = 'INFO' 
        self.transport_payload = {'wood': 0, 'stone': 0, 'coal': 0}
        self.transport_dest_cc = None
        self.is_selecting_dest = False
        
        # [MỚI]: Biến đếm thời gian để xử lý ấn giữ chuột (Hold)
        self.hold_timer = 0 
        
        self.btn_repair = pygame.Rect(550, MAP_HEIGHT * TILE_SIZE + 30, 100, 40)
        self.btn_open_transport = pygame.Rect(670, MAP_HEIGHT * TILE_SIZE + 30, 130, 40)
        
        self.btn_select_dest = pygame.Rect(820, MAP_HEIGHT * TILE_SIZE + 15, 150, 30)
        self.btn_confirm_trans = pygame.Rect(820, MAP_HEIGHT * TILE_SIZE + 55, 150, 30)
        self.btn_cancel_trans = pygame.Rect(980, MAP_HEIGHT * TILE_SIZE + 55, 80, 30)
        
        self.plus_minus_rects = {}
        self.event_logs = [] 
        
        self.res_icons = {}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for res in ['wood', 'stone', 'coal']:
            try:
                img_path = os.path.join(base_dir, "assets", f"{res}_tn.png")
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (22, 22))
                self.res_icons[res] = img
            except:
                self.res_icons[res] = None

    def add_log(self, message):
        self.event_logs.append(message)
        if len(self.event_logs) > 4: 
            self.event_logs.pop(0)

    def reset_transport(self):
        self.mode = 'INFO'
        self.transport_payload = {'wood': 0, 'stone': 0, 'coal': 0}
        self.transport_dest_cc = None
        self.is_selecting_dest = False

    def handle_click(self, pos):
        """
        Xử lý tương tác click chuột của người chơi vào các nút bấm trên UI (Sửa chữa, Vận chuyển, Cộng/Trừ tài nguyên).
        """
        if not self.panel_rect.collidepoint(pos):
            return False

        if not self.selected_building:
            return True

        cc = self.selected_building

        if self.mode == 'INFO':
            if self.btn_repair.collidepoint(pos): cc.repair()
            elif self.btn_open_transport.collidepoint(pos): self.mode = 'TRANSPORT'
        elif self.mode == 'TRANSPORT':
            if self.btn_cancel_trans.collidepoint(pos): self.reset_transport()
            elif self.btn_select_dest.collidepoint(pos): self.is_selecting_dest = True 
            elif self.btn_confirm_trans.collidepoint(pos):
                if self.transport_dest_cc and sum(self.transport_payload.values()) > 0:
                    return "CONFIRM_TRANSPORT"

            for key, rect in self.plus_minus_rects.items():
                if rect.collidepoint(pos):
                    res_type, action = key.split('_') 
                    if action == 'plus' and self.transport_payload[res_type] < getattr(cc, 'inventory', {})[res_type]:
                        self.transport_payload[res_type] += 1
                    elif action == 'minus' and self.transport_payload[res_type] > 0:
                        self.transport_payload[res_type] -= 1
        return True

    def draw_button(self, surface, rect, text, is_active=True, is_highlighted=False):
        """vẽ nút bấm"""
        color = COLORS['btn'] if is_active else COLORS['btn_disabled']
        if is_active and rect.collidepoint(pygame.mouse.get_pos()):
            color = COLORS['btn_hover']
        if is_highlighted:
            color = (50, 200, 50) 

        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        
        txt_surf = self.font.render(text, True, COLORS['text'])
        text_x = rect.x + (rect.w - txt_surf.get_width()) // 2
        text_y = rect.y + (rect.h - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (text_x, text_y))

    def draw(self, surface, build_mode=None, free_cc=False):
        """
        Hiển thị khu vực Panel UI lên màn hình. Tùy thuộc vào trạng thái đang tương tác (Đang xây, Chọn nhà, Chuyển đồ) để vẽ giao diện phù hợp.
        """
        pygame.draw.rect(surface, COLORS['ui_bg'], self.panel_rect)
        pygame.draw.line(surface, (255, 255, 255), (0, MAP_HEIGHT * TILE_SIZE), (MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE), 3)
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]: # Phát hiện đang đè chuột trái
            self.hold_timer += 1
            # Đợi 15 khung hình (0.25s) để chống nảy, sau đó mỗi 3 khung hình nhảy 1 số
            if self.hold_timer > 15 and self.hold_timer % 3 == 0:
                if self.mode == 'TRANSPORT' and self.selected_building:
                    cc = self.selected_building
                    for key, rect in self.plus_minus_rects.items():
                        if rect.collidepoint(mouse_pos):
                            res_type, action = key.split('_') 
                            if action == 'plus' and self.transport_payload[res_type] < getattr(cc, 'inventory', {})[res_type]:
                                self.transport_payload[res_type] += 1
                            elif action == 'minus' and self.transport_payload[res_type] > 0:
                                self.transport_payload[res_type] -= 1
        else:
            self.hold_timer = 0 # Nhả chuột ra thì reset bộ đếm

        if build_mode is not None:
            costs = {
                'CC': {'wood': 10, 'stone': 3, 'coal': 3, 'name': "THÀNH TRÌ"},
                'WALL': {'wood': 2, 'stone': 1, 'coal': 0, 'name': "TƯỜNG PHÒNG THỦ"},
                'BARRACKS': {'wood': 10, 'stone': 2, 'coal': 3, 'name': "DOANH TRẠI LÍNH"}
            }
            info = costs.get(build_mode)
            if info:
                title_str = f"--- ĐANG CHUẨN BỊ XÂY: {info['name']} ---"
                if build_mode == 'CC' and free_cc:
                    title_str += " [MIỄN PHÍ]"
                surface.blit(self.font.render(title_str, True, (0, 255, 255)), (20, MAP_HEIGHT * TILE_SIZE + 15))
                
                surface.blit(self.font.render("Chi phí:", True, (200, 200, 200)), (20, MAP_HEIGHT * TILE_SIZE + 45))
                
                start_x = 100
                y_pos = MAP_HEIGHT * TILE_SIZE + 45
                
                for res in ['wood', 'stone', 'coal']:
                    cost_val = info[res]
                    if build_mode == 'CC' and free_cc: cost_val = 0
                    
                    icon = self.res_icons.get(res)
                    if icon:
                        surface.blit(icon, (start_x, y_pos - 2))
                        start_x += 25
                    else:
                        pygame.draw.rect(surface, COLORS.get(res, (255,255,255)), (start_x, y_pos, 15, 15))
                        start_x += 20
                        
                    text_surf = self.font.render(f"{cost_val}   ", True, (255, 255, 255))
                    surface.blit(text_surf, (start_x, y_pos))
                    start_x += text_surf.get_width()
            return

        if not self.selected_building:
            surface.blit(self.font.render("    Nhật ký      ", True, (255, 215, 0)), (20, MAP_HEIGHT * TILE_SIZE + 10))
            for i, log_msg in enumerate(self.event_logs):
                surface.blit(self.small_font.render(log_msg, True, (200, 200, 200)), (20, MAP_HEIGHT * TILE_SIZE + 35 + i * 20))
            return

        cc = self.selected_building
        max_cap = getattr(cc, 'inventory_limit', 50) 
        
        surface.blit(self.font.render(f"HP: {cc.hp}/{cc.max_hp}", True, COLORS['text']), (20, MAP_HEIGHT * TILE_SIZE + 20))
        
        y_inv = MAP_HEIGHT * TILE_SIZE + 60
        x_inv = 20
        for res in ['wood', 'stone', 'coal']:
            icon = self.res_icons.get(res)
            if icon:
                surface.blit(icon, (x_inv, y_inv - 2))
                x_inv += 25
            else:
                pygame.draw.rect(surface, COLORS.get(res, (255,255,255)), (x_inv, y_inv, 15, 15))
                x_inv += 20
                
            text_surf = self.font.render(f": {cc.inventory[res]}/{max_cap}   ", True, COLORS['text'])
            surface.blit(text_surf, (x_inv, y_inv))
            x_inv += text_surf.get_width()

        if self.mode == 'INFO':
            can_repair = cc.hp < cc.max_hp and cc.inventory['wood'] >= 5 and cc.inventory['stone'] >= 5
            self.draw_button(surface, self.btn_repair, "Sửa (H)", can_repair)
            self.draw_button(surface, self.btn_open_transport, "Vận chuyển")

        elif self.mode == 'TRANSPORT':
            self.plus_minus_rects.clear()
            base_y = MAP_HEIGHT * TILE_SIZE + 10
            start_x = 450 
            
            for i, res in enumerate(['wood', 'stone', 'coal']):
                y = base_y + i * 28 
                
                icon = self.res_icons.get(res)
                if icon: 
                    surface.blit(icon, (start_x, y))
                else:
                    pygame.draw.rect(surface, COLORS.get(res, (255,255,255)), (start_x, y, 20, 20))
                
                minus_rect = pygame.Rect(start_x + 35, y, 25, 25)
                self.draw_button(surface, minus_rect, "-")
                self.plus_minus_rects[f"{res}_minus"] = minus_rect
                
                payload_str = str(self.transport_payload[res])
                num_surf = self.font.render(payload_str, True, (255, 255, 0))
                surface.blit(num_surf, (start_x + 78 - num_surf.get_width()//2, y + 2))
                
                plus_rect = pygame.Rect(start_x + 95, y, 25, 25)
                self.draw_button(surface, plus_rect, "+")
                self.plus_minus_rects[f"{res}_plus"] = plus_rect

            dest_text = "Chọn Đích..." if self.is_selecting_dest else (f"Đích: ({self.transport_dest_cc.col}, {self.transport_dest_cc.row})" if self.transport_dest_cc else "Chọn Đích")
            self.draw_button(surface, self.btn_select_dest, dest_text, True, self.is_selecting_dest)
            
            can_confirm = self.transport_dest_cc is not None and sum(self.transport_payload.values()) > 0
            self.draw_button(surface, self.btn_confirm_trans, "Xuất phát", can_confirm)
            self.draw_button(surface, self.btn_cancel_trans, "Hủy")