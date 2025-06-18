#!/usr/bin/env python3
"""
Hệ thống Tưới Tự Động Đối Thoại
Baseline cuối cùng với vòng lặp phản hồi kép
"""

import time
from datetime import datetime
from components import (
    Controller, Database, EnvironmentSensor, 
    CycleRecord, InputData, OutputData, EnvironmentData
)
from agents import ReflectionAgent, PlanAgent

class IrrigationSystem:
    """Hệ thống tưới tự động chính"""
    
    def __init__(self):
        self.controller = Controller()
        self.database = Database()
        self.reflection_agent = ReflectionAgent()
        self.plan_agent = PlanAgent()
        self.target_ec = 4.0
        
    def run_calibration_phase(self):
        """Giai đoạn 1: Hiệu chỉnh"""
        print("🔧 === GIAI ĐOẠN HIỆU CHỈNH ===")
        
        # Lấy dữ liệu môi trường
        env_data = EnvironmentSensor.get_current_environment()
        print(f"🌡️ Môi trường: {env_data.nhiệt_độ}°C, {env_data.độ_ẩm}%, ET0: {env_data.et0}")
        
        # Sử dụng thời gian chờ mặc định cho hiệu chỉnh
        initial_wait = 120  # phút
        
        input_data = InputData(
            T_chờ_phút=initial_wait,
            môi_trường_tb=env_data
        )
        
        print(f"⏰ Thời gian chờ hiệu chỉnh: {initial_wait} phút")
        
        # Mô phỏng chờ (rút ngắn cho demo)
        print("⏳ Đang chờ... (mô phỏng)")
        time.sleep(2)
        
        # Thực hiện tưới
        T_đầy, EC = self.controller.tưới_cho_đến_khi_đầy()
        
        output_data = OutputData(T_đầy_giây=T_đầy, EC_đo_được=EC)
        
        # Tạo bản ghi hiệu chỉnh
        record = CycleRecord(
            id=self.database.get_next_id(),
            timestamp=datetime.now().isoformat(),
            phase="calibration",
            input_data=input_data,
            output_data=output_data,
            reflection_text="Chu trình hiệu chỉnh ban đầu."
        )
        
        self.database.add_record(record)
        print(f"✅ Hoàn thành hiệu chỉnh. EC đo được: {EC}")
        
    def run_operation_cycle(self) -> bool:
        """
        Chạy một chu trình vận hành
        Returns: True nếu tiếp tục, False nếu dừng
        """
        print("\n🚀 === CHU TRÌNH VẬN HÀNH ===")
        
        # Bước 1: Chuẩn bị context
        print("📊 Chuẩn bị dữ liệu...")
        history = self.database.get_recent_records(days=3)
        last_record = self.database.get_last_record()
        last_reflection = last_record["reflection_text"] if last_record else ""
        
        current_env = EnvironmentSensor.get_current_environment()
        forecast = EnvironmentSensor.get_weather_forecast()
        
        print(f"🌡️ Môi trường hiện tại: {current_env.nhiệt_độ}°C, {current_env.độ_ẩm}%")
        print(f"🌤️ Dự báo: {forecast}")
        
        # Bước 2: Plan Agent quyết định
        print("🧠 Plan Agent đang phân tích...")
        decision = self.plan_agent.decide_next_wait_time(
            last_reflection=last_reflection,
            history=history,
            current_env={
                "nhiệt_độ": current_env.nhiệt_độ,
                "độ_ẩm": current_env.độ_ẩm,
                "et0": current_env.et0
            },
            forecast=forecast
        )
        
        T_chờ_mới = decision["T_chờ_đề_xuất"]
        lý_do = decision["lý_do"]
        
        print(f"⏰ Quyết định: Chờ {T_chờ_mới} phút")
        print(f"💭 Lý do: {lý_do}")
        
        # Bước 3: Chờ (mô phỏng)
        print(f"⏳ Đang chờ {T_chờ_mới} phút... (mô phỏng)")
        time.sleep(3)  # Mô phỏng thời gian chờ
        
        # Bước 4: Thực hiện tưới
        T_đầy_mới, EC_mới = self.controller.tưới_cho_đến_khi_đầy()
        
        # Bước 5: Reflection Agent phản tư
        print("🤔 Reflection Agent đang phân tích...")
        reflection_text = self.reflection_agent.create_reflection(
            input_data={"T_chờ_phút": T_chờ_mới},
            output_data={"T_đầy_giây": T_đầy_mới, "EC_đo_được": EC_mới}
        )
        
        print(f"📝 Nhận xét: {reflection_text}")
        
        # Bước 6: Lưu trữ
        input_data = InputData(
            T_chờ_phút=T_chờ_mới,
            môi_trường_tb=current_env
        )
        
        output_data = OutputData(
            T_đầy_giây=T_đầy_mới,
            EC_đo_được=EC_mới
        )
        
        record = CycleRecord(
            id=self.database.get_next_id(),
            timestamp=datetime.now().isoformat(),
            phase="operation",
            input_data=input_data,
            output_data=output_data,
            reflection_text=reflection_text
        )
        
        self.database.add_record(record)
        
        # Hiển thị trạng thái
        if abs(EC_mới - self.target_ec) <= 0.2:
            print(f"🎯 Tuyệt vời! EC {EC_mới} đã đạt gần mục tiêu {self.target_ec}")
        elif EC_mới > self.target_ec:
            print(f"📈 EC {EC_mới} cao hơn mục tiêu {self.target_ec}, cần tưới sớm hơn")
        else:
            print(f"📉 EC {EC_mới} thấp hơn mục tiêu {self.target_ec}, cần chờ lâu hơn")
            
        return True  # Tiếp tục vòng lặp
        
    def run(self, max_cycles: int = 5):
        """Chạy hệ thống hoàn chỉnh"""
        print("🌱 === HỆ THỐNG TƯỚI TỰ ĐỘNG THÔNG MINH ===")
        print(f"🎯 Mục tiêu EC: {self.target_ec}")
        
        # Kiểm tra nếu đã có dữ liệu hiệu chỉnh
        if not self.database.data:
            self.run_calibration_phase()
        else:
            print("✅ Đã có dữ liệu hiệu chỉnh, bỏ qua giai đoạn này")
        
        # Chạy vòng lặp vận hành
        for cycle in range(max_cycles):
            print(f"\n🔄 Chu trình {cycle + 1}/{max_cycles}")
            
            try:
                should_continue = self.run_operation_cycle()
                if not should_continue:
                    break
                    
                # Hỏi người dùng có muốn tiếp tục
                if cycle < max_cycles - 1:
                    user_input = input("\n⏸️ Nhấn Enter để tiếp tục chu trình tiếp theo (hoặc 'q' để dừng): ")
                    if user_input.lower() == 'q':
                        break
                        
            except KeyboardInterrupt:
                print("\n⏹️ Dừng hệ thống theo yêu cầu người dùng")
                break
            except Exception as e:
                print(f"❌ Lỗi trong chu trình: {e}")
                break
                
        print("\n🏁 Kết thúc hệ thống")
        self.show_summary()
        
    def show_summary(self):
        """Hiển thị tổng kết"""
        print("\n📊 === TỔNG KẾT ===")
        history = self.database.get_recent_records(days=1)
        
        if not history:
            print("Không có dữ liệu")
            return
            
        ec_values = [record["output_data"]["EC_đo_được"] for record in history]
        wait_times = [record["input_data"]["T_chờ_phút"] for record in history]
        
        print(f"📈 Số chu trình: {len(history)}")
        print(f"🎯 EC trung bình: {sum(ec_values)/len(ec_values):.1f}")
        print(f"⏰ Thời gian chờ trung bình: {sum(wait_times)//len(wait_times)} phút")
        print(f"📊 EC gần nhất: {ec_values[-1]} (mục tiêu: {self.target_ec})")

def main():
    """Hàm chính"""
    system = IrrigationSystem()
    system.run(max_cycles=3)  # Chạy 3 chu trình demo

if __name__ == "__main__":
    main()
