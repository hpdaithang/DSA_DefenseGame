import json
import os

class Leaderboard:
    """
    Lớp quản lý Bảng xếp hạng điểm số (Thời gian sinh tồn) của người chơi.
    Dữ liệu được lưu trữ và đọc dưới định dạng JSON.
    """
    def __init__(self, filename="leaderboard.json"):
        """Khởi tạo cơ bản cho lớp này"""
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        """Load file"""
        # Kiểm tra nếu file tồn tại thì đọc, không thì tạo danh sách rỗng
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def add_score(self, name, survival_time):
        """Khi có một điểm số mới hàm này quyết định nó có được phép xuất hiện trong đây không và xuất hiện tại đâu bằng thuật toán dùng thuật toán sắp xếp chèn (Insertion Sort)"""
        self.data.append({"name": name, "time": survival_time}) 

        for i in range(1,len(self.data)):
            val_data_i = self.data[i] 
            j = i - 1 
            while j >= 0 and self.data[j]['time'] < val_data_i['time']:
                self.data[j + 1] = self.data[j] 
                j -= 1 
            self.data[j + 1] = val_data_i  
        
        self.data = self.data[:10]
        self.save_data()

    def save_data(self):
        """Lưu dữ liệu"""
        with open(self.filename, "w") as f:
            json.dump(self.data, f)