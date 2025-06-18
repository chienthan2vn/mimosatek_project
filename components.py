import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random

@dataclass
class EnvironmentData:
    """Dữ liệu môi trường"""
    nhiệt_độ: float
    độ_ẩm: float
    et0: float

@dataclass
class InputData:
    """Dữ liệu đầu vào của chu trình"""
    T_chờ_phút: int
    môi_trường_tb: EnvironmentData

@dataclass
class OutputData:
    """Kết quả đo được của chu trình"""
    T_đầy_giây: int
    EC_đo_được: float

@dataclass
class CycleRecord:
    """Bản ghi hoàn chỉnh của một chu trình tưới"""
    id: int
    timestamp: str
    phase: str  # "calibration" hoặc "operation"
    input_data: InputData
    output_data: OutputData
    reflection_text: str = ""

    def to_dict(self) -> Dict:
        """Chuyển đổi sang dictionary để lưu JSON"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "phase": self.phase,
            "input_data": asdict(self.input_data),
            "output_data": asdict(self.output_data),
            "reflection_text": self.reflection_text
        }

class Controller:
    """Bộ điều khiển thiết bị tưới (mô phỏng)"""
    
    def __init__(self):
        self.tank_capacity = 100  # Dung tích bình chứa
        
    def tưới_cho_đến_khi_đầy(self) -> tuple[int, float]:
        """
        Mô phỏng quá trình tưới và đo EC
        Returns: (T_đầy_giây, EC_đo_được)
        """
        print("🚿 Bắt đầu tưới...")
        
        # Mô phỏng thời gian tưới (30-60 giây)
        T_đầy = random.randint(30, 60)
        
        # Mô phỏng đo EC (3.5-5.5)
        EC = round(random.uniform(3.5, 5.5), 1)
        
        # Mô phỏng quá trình tưới
        time.sleep(2)  # Mô phỏng thời gian thực tế
        
        print(f"✅ Tưới hoàn thành! Thời gian: {T_đầy}s, EC: {EC}")
        return T_đầy, EC

class Database:
    """Cơ sở dữ liệu lưu trữ lịch sử"""
    
    def __init__(self, file_path: str = "irrigation_history.json"):
        self.file_path = file_path
        self.data: List[Dict] = self._load_data()
        
    def _load_data(self) -> List[Dict]:
        """Tải dữ liệu từ file JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
            
    def _save_data(self):
        """Lưu dữ liệu vào file JSON"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
    def add_record(self, record: CycleRecord):
        """Thêm bản ghi mới"""
        self.data.append(record.to_dict())
        self._save_data()
        print(f"💾 Đã lưu bản ghi #{record.id}")
        
    def get_recent_records(self, days: int = 3) -> List[Dict]:
        """Lấy bản ghi trong N ngày gần nhất"""
        # Đơn giản hóa: lấy N bản ghi cuối cùng
        return self.data[-days*8:] if self.data else []
        
    def get_last_record(self) -> Optional[Dict]:
        """Lấy bản ghi cuối cùng"""
        return self.data[-1] if self.data else None
        
    def get_next_id(self) -> int:
        """Lấy ID cho bản ghi tiếp theo"""
        return len(self.data) + 1

class EnvironmentSensor:
    """Cảm biến môi trường (mô phỏng)"""
    
    @staticmethod
    def get_current_environment() -> EnvironmentData:
        """Lấy dữ liệu môi trường hiện tại"""
        return EnvironmentData(
            nhiệt_độ=round(random.uniform(28, 35), 1),
            độ_ẩm=round(random.uniform(60, 80), 1),
            et0=round(random.uniform(0.2, 0.3), 2)
        )
        
    @staticmethod
    def get_weather_forecast() -> str:
        """Lấy dự báo thời tiết"""
        forecasts = [
            "Trời nắng, nhiệt độ có xu hướng tăng nhẹ.",
            "Thời tiết ổn định, độ ẩm trung bình.",
            "Có thể có mưa nhẹ vào chiều.",
            "Trời âm u, độ ẩm cao."
        ]
        return random.choice(forecasts)
