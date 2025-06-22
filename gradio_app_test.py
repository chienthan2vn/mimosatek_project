import gradio as gr
import json
import time
import threading
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
import queue

# Import các component từ project
from components import (
    Controller, Database, EnvironmentSensor, 
    CycleRecord, InputData, OutputData, EnvironmentData
)
from agents import ReflectionAgent, PlanAgent

class RealTimeIrrigationApp:
    """Ứng dụng Gradio cho hệ thống tưới thời gian thực"""
    
    def __init__(self):
        self.controller = Controller()
        self.database = Database()
        self.reflection_agent = ReflectionAgent()
        self.plan_agent = PlanAgent()
        self.target_ec = 4.0
        
        # Queue để truyền dữ liệu giữa threads
        self.status_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # Trạng thái hệ thống
        self.is_running = False
        self.current_cycle = 0
        self.system_thread = None
        
        # Dữ liệu real-time
        self.current_status = {
            "phase": "Chờ khởi động",
            "ec_current": 0.0,
            "ec_target": self.target_ec,
            "wait_time": 0,
            "temperature": 0.0,
            "humidity": 0.0,
            "et0": 0.0,
            "last_reflection": "",
            "cycles_completed": 0
        }
        
    def update_status(self, **kwargs):
        """Cập nhật trạng thái hệ thống"""
        self.current_status.update(kwargs)
        self.status_queue.put(self.current_status.copy())
        
    def add_log(self, message: str, level: str = "INFO"):
        """Thêm log message"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        self.log_queue.put(log_entry)
        
    def get_current_data(self):
        """Lấy dữ liệu hiện tại cho dashboard"""
        try:
            # Cập nhật trạng thái từ queue
            while not self.status_queue.empty():
                self.current_status = self.status_queue.get()
                
            # Tạo metrics
            status_text = f"🔄 **Trạng thái:** {self.current_status['phase']}\n"
            status_text += f"🎯 **EC hiện tại:** {self.current_status['ec_current']:.1f} / {self.current_status['ec_target']:.1f}\n"
            status_text += f"⏰ **Thời gian chờ:** {self.current_status['wait_time']} phút\n"
            status_text += f"🌡️ **Nhiệt độ:** {self.current_status['temperature']:.1f}°C\n"
            status_text += f"💧 **Độ ẩm:** {self.current_status['humidity']:.1f}%\n"
            status_text += f"🔄 **Chu trình hoàn thành:** {self.current_status['cycles_completed']}"
            
            # Gauge chart cho EC
            ec_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = self.current_status['ec_current'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "EC Level"},
                delta = {'reference': self.target_ec},
                gauge = {
                    'axis': {'range': [None, 6]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 3.5], 'color': "lightgray"},
                        {'range': [3.5, 4.5], 'color': "lightgreen"},
                        {'range': [4.5, 6], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': self.target_ec
                    }
                }
            ))
            ec_gauge.update_layout(height=300)
            
            # Lấy logs
            log_messages = []
            while not self.log_queue.empty():
                log_messages.append(self.log_queue.get())
            
            log_text = ""
            for log in log_messages[-10:]:  # Chỉ hiển thị 10 log gần nhất
                level_emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(log["level"], "📝")
                log_text += f"{log['timestamp']} {level_emoji} {log['message']}\n"
                
            return status_text, ec_gauge, log_text, self.current_status['last_reflection']
            
        except Exception as e:
            return f"❌ Lỗi cập nhật: {str(e)}", go.Figure(), "", ""
    
    def get_history_chart(self):
        """Tạo biểu đồ lịch sử EC"""
        try:
            history = self.database.get_recent_records(days=1)
            if not history:
                return go.Figure().add_annotation(text="Chưa có dữ liệu", xref="paper", yref="paper", x=0.5, y=0.5)
            
            # Chuẩn bị dữ liệu
            timestamps = []
            ec_values = []
            wait_times = []
            
            for record in history:
                timestamps.append(datetime.fromisoformat(record['timestamp']))
                ec_values.append(record['output_data']['EC_đo_được'])
                wait_times.append(record['input_data']['T_chờ_phút'])
            
            # Tạo subplot
            fig = go.Figure()
            
            # EC values
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=ec_values,
                mode='lines+markers',
                name='EC đo được',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))
            
            # Target line
            fig.add_hline(y=self.target_ec, line_dash="dash", line_color="red", 
                         annotation_text="Mục tiêu EC=4.0")
            
            fig.update_layout(
                title="Lịch sử EC theo thời gian",
                xaxis_title="Thời gian",
                yaxis_title="EC",
                height=400,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            return go.Figure().add_annotation(text=f"Lỗi: {str(e)}", xref="paper", yref="paper", x=0.5, y=0.5)
    
    def run_system_cycle(self):
        """Chạy một chu trình hệ thống trong background thread"""
        try:
            self.add_log("🚀 Bắt đầu chu trình mới", "INFO")
            self.update_status(phase="Đang chuẩn bị...")
            
            # Chuẩn bị dữ liệu
            history = self.database.get_recent_records(days=3)
            last_record = self.database.get_last_record()
            last_reflection = last_record["reflection_text"] if last_record else ""
            
            current_env = EnvironmentSensor.get_current_environment()
            forecast = EnvironmentSensor.get_weather_forecast()
            
            self.update_status(
                temperature=current_env.nhiệt_độ,
                humidity=current_env.độ_ẩm,
                et0=current_env.et0,
                phase="Đang phân tích..."
            )
            
            self.add_log(f"🌡️ Môi trường: {current_env.nhiệt_độ}°C, {current_env.độ_ẩm}%", "INFO")
            
            # Plan Agent quyết định
            self.add_log("🧠 Plan Agent đang phân tích...", "INFO")
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
            
            self.update_status(
                wait_time=T_chờ_mới,
                phase=f"Chờ {T_chờ_mới} phút"
            )
            
            self.add_log(f"⏰ Quyết định chờ {T_chờ_mới} phút: {lý_do}", "INFO")
            
            # Mô phỏng thời gian chờ (rút ngắn cho demo)
            for i in range(5):  # 5 giây thay vì thời gian thực
                if not self.is_running:
                    return
                time.sleep(1)
                remaining = 5 - i - 1
                self.update_status(phase=f"Chờ còn {remaining}s (mô phỏng)")
            
            # Thực hiện tưới
            self.update_status(phase="Đang tưới...")
            self.add_log("🚿 Bắt đầu tưới...", "INFO")
            
            T_đầy_mới, EC_mới = self.controller.tưới_cho_đến_khi_đầy()
            
            self.update_status(
                ec_current=EC_mới,
                phase="Đang phân tích kết quả"
            )
            
            self.add_log(f"✅ Tưới hoàn thành! EC: {EC_mới}, Thời gian: {T_đầy_mới}s", "SUCCESS")
            
            # Reflection Agent
            self.add_log("🤔 Reflection Agent đang phân tích...", "INFO")
            reflection_text = self.reflection_agent.create_reflection(
                input_data={"T_chờ_phút": T_chờ_mới},
                output_data={"T_đầy_giây": T_đầy_mới, "EC_đo_được": EC_mới}
            )
            
            self.update_status(last_reflection=reflection_text)
            self.add_log(f"📝 Nhận xét: {reflection_text}", "INFO")
            
            # Lưu dữ liệu
            input_data = InputData(T_chờ_phút=T_chờ_mới, môi_trường_tb=current_env)
            output_data = OutputData(T_đầy_giây=T_đầy_mới, EC_đo_được=EC_mới)
            
            record = CycleRecord(
                id=self.database.get_next_id(),
                timestamp=datetime.now().isoformat(),
                phase="operation",
                input_data=input_data,
                output_data=output_data,
                reflection_text=reflection_text
            )
            
            self.database.add_record(record)
            
            self.current_cycle += 1
            self.update_status(
                cycles_completed=self.current_cycle,
                phase="Hoàn thành chu trình"
            )
            
            # Đánh giá kết quả
            if abs(EC_mới - self.target_ec) <= 0.2:
                self.add_log(f"🎯 Tuyệt vời! EC {EC_mới} đạt gần mục tiêu", "SUCCESS")
            elif EC_mới > self.target_ec:
                self.add_log(f"📈 EC {EC_mới} cao hơn mục tiêu, cần tưới sớm hơn", "WARNING")
            else:
                self.add_log(f"📉 EC {EC_mới} thấp hơn mục tiêu, cần chờ lâu hơn", "WARNING")
            
        except Exception as e:
            self.add_log(f"❌ Lỗi trong chu trình: {str(e)}", "ERROR")
            self.update_status(phase="Lỗi hệ thống")
    
    def start_system(self):
        """Khởi động hệ thống"""
        if self.is_running:
            return "⚠️ Hệ thống đang chạy!"
        
        self.is_running = True
        self.add_log("🌱 Khởi động hệ thống tưới tự động", "SUCCESS")
        
        # Chạy hiệu chỉnh nếu chưa có dữ liệu
        if not self.database.data:
            self.add_log("🔧 Chạy hiệu chỉnh ban đầu...", "INFO")
            env_data = EnvironmentSensor.get_current_environment()
            input_data = InputData(T_chờ_phút=120, môi_trường_tb=env_data)
            T_đầy, EC = self.controller.tưới_cho_đến_khi_đầy()
            output_data = OutputData(T_đầy_giây=T_đầy, EC_đo_được=EC)
            
            record = CycleRecord(
                id=self.database.get_next_id(),
                timestamp=datetime.now().isoformat(),
                phase="calibration",
                input_data=input_data,
                output_data=output_data,
                reflection_text="Chu trình hiệu chỉnh ban đầu."
            )
            self.database.add_record(record)
            self.update_status(ec_current=EC)
            self.add_log(f"✅ Hiệu chỉnh hoàn thành. EC: {EC}", "SUCCESS")
        
        return "✅ Hệ thống đã khởi động!"
    
    def stop_system(self):
        """Dừng hệ thống"""
        self.is_running = False
        if self.system_thread and self.system_thread.is_alive():
            self.system_thread.join(timeout=2)
        self.add_log("⏹️ Hệ thống đã dừng", "INFO")
        self.update_status(phase="Đã dừng")
        return "⏹️ Hệ thống đã dừng!"
    
    def run_single_cycle(self):
        """Chạy một chu trình đơn"""
        if not self.is_running:
            return "⚠️ Hãy khởi động hệ thống trước!"
        
        self.system_thread = threading.Thread(target=self.run_system_cycle)
        self.system_thread.daemon = True
        self.system_thread.start()
        
        return "🔄 Đang chạy chu trình..."
    
    def create_interface(self):
        """Tạo giao diện Gradio"""
        with gr.Blocks(title="🌱 Hệ Thống Tưới Tự Động Thông Minh", theme=gr.themes.Soft()) as app:
            gr.Markdown("# 🌱 Hệ Thống Tưới Tự Động Thông Minh")
            gr.Markdown("### Dashboard thời gian thực với AI Agents")
            
            with gr.Row():
                # Cột điều khiển
                with gr.Column(scale=1):
                    gr.Markdown("## 🎛️ Điều khiển")
                    
                    start_btn = gr.Button("🚀 Khởi động hệ thống", variant="primary")
                    cycle_btn = gr.Button("🔄 Chạy chu trình", variant="secondary")
                    stop_btn = gr.Button("⏹️ Dừng hệ thống", variant="stop")
                    refresh_btn = gr.Button("🔄 Làm mới", variant="secondary")
                    
                    control_output = gr.Textbox(label="Trạng thái điều khiển", interactive=False)
                    
                    gr.Markdown("## ⚙️ Cài đặt")
                    target_ec_input = gr.Number(label="Mục tiêu EC", value=4.0, step=0.1)
                    
                # Cột trạng thái chính
                with gr.Column(scale=2):
                    gr.Markdown("## 📊 Trạng thái hệ thống")
                    
                    status_display = gr.Markdown("🔄 Đang khởi tạo...")
                    
                    with gr.Row():
                        ec_gauge = gr.Plot(label="EC Gauge")
                        history_chart = gr.Plot(label="Lịch sử EC")
            
            with gr.Row():
                # Cột phản hồi AI
                with gr.Column():
                    gr.Markdown("## 🤖 Phản hồi AI")
                    reflection_display = gr.Textbox(
                        label="Nhận xét từ Reflection Agent",
                        lines=3,
                        interactive=False
                    )
                
                # Cột logs
                with gr.Column():
                    gr.Markdown("## 📝 System Logs")
                    log_display = gr.Textbox(
                        label="Nhật ký hệ thống",
                        lines=10,
                        interactive=False,
                        max_lines=15
                    )
            
            # Events
            start_btn.click(
                fn=self.start_system,
                outputs=control_output
            )
            
            cycle_btn.click(
                fn=self.run_single_cycle,
                outputs=control_output
            )
            
            stop_btn.click(
                fn=self.stop_system,
                outputs=control_output
            )
            
            refresh_btn.click(
                fn=self.get_current_data,
                outputs=[status_display, ec_gauge, log_display, reflection_display]
            )
            
            refresh_btn.click(
                fn=self.get_history_chart,
                outputs=history_chart
            )
            
            # Initialize interface
            def auto_refresh():
                return self.get_current_data()
            
            def auto_refresh_chart():
                return self.get_history_chart()
            
            # Set up auto-refresh using Gradio's built-in functionality
            demo = gr.Blocks(title="🌱 Auto-refresh Demo")
            with demo:
                # Auto refresh will be handled by JavaScript or manual refresh
                pass
        
        return app

def main():
    """Khởi chạy ứng dụng"""
    app_instance = RealTimeIrrigationApp()
    interface = app_instance.create_interface()
    
    print("🌱 Khởi động giao diện Gradio...")
    print("📱 Truy cập: http://localhost:7860")
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )

if __name__ == "__main__":
    main()