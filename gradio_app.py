#!/usr/bin/env python3
"""
Giao diện Web cho Hệ thống Tưới Tự Động Thông Minh
Sử dụng Gradio để tạo UI đẹp và dễ sử dụng
"""

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import threading
import time
from typing import Dict, List, Tuple

from main import IrrigationSystem
from components import Database, EnvironmentSensor, EnvironmentData
from agents import ReflectionAgent, PlanAgent


class DemoIrrigationSystem(IrrigationSystem):
    """Phiên bản demo với thời gian tính bằng giây thay vì phút"""
    
    def run_calibration_phase(self):
        """Giai đoạn 1: Hiệu chỉnh (demo với giây)"""
        print("🔧 === GIAI ĐOẠN HIỆU CHỈNH ===")
        
        # Lấy dữ liệu môi trường
        env_data = EnvironmentSensor.get_current_environment()
        print(f"🌡️ Môi trường: {env_data.nhiệt_độ}°C, {env_data.độ_ẩm}%, ET0: {env_data.et0}")
        
        # Sử dụng thời gian chờ demo (giây thay vì phút)
        initial_wait = 15  # giây cho demo
        
        from components import InputData, OutputData, CycleRecord
        input_data = InputData(
            T_chờ_phút=initial_wait,  # Lưu vào field cũ nhưng giá trị là giây
            môi_trường_tb=env_data
        )
        
        print(f"⏰ Thời gian chờ hiệu chỉnh: {initial_wait} giây (demo)")
        
        # Mô phỏng chờ
        print("⏳ Đang chờ... (demo)")
        time.sleep(initial_wait)  # Chờ thực tế theo giây
        
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
            reflection_text="Chu trình hiệu chỉnh ban đầu (demo mode)."
        )
        
        self.database.add_record(record)
        print(f"✅ Hoàn thành hiệu chỉnh. EC đo được: {EC}")
    
    def run_operation_cycle(self) -> bool:
        """Chạy một chu trình vận hành (demo với giây)"""
        print("\n🚀 === CHU TRÌNH VẬN HÀNH (DEMO) ===")
        
        # Bước 1: Chuẩn bị context
        print("📊 Chuẩn bị dữ liệu...")
        history = self.database.get_recent_records(days=3)
        last_record = self.database.get_last_record()
        last_reflection = last_record["reflection_text"] if last_record else ""
        
        current_env = EnvironmentSensor.get_current_environment()
        forecast = EnvironmentSensor.get_weather_forecast()
        
        print(f"🌡️ Môi trường hiện tại: {current_env.nhiệt_độ}°C, {current_env.độ_ẩm}%")
        print(f"🌤️ Dự báo: {forecast}")
        
        # Bước 2: Plan Agent quyết định (điều chỉnh cho demo)
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
        
        # Chuyển đổi từ phút sang giây cho demo
        T_chờ_phút_gốc = decision["T_chờ_đề_xuất"]
        T_chờ_giây_demo = max(5, min(30, T_chờ_phút_gốc // 4))  # Chia 4 và giới hạn 5-30 giây
        lý_do = decision["lý_do"]
        
        print(f"⏰ Quyết định: Chờ {T_chờ_giây_demo} giây (demo từ {T_chờ_phút_gốc} phút)")
        print(f"💭 Lý do: {lý_do}")
        
        # Bước 3: Chờ thực tế
        print(f"⏳ Đang chờ {T_chờ_giây_demo} giây...")
        time.sleep(T_chờ_giây_demo)
        
        # Bước 4: Thực hiện tưới
        T_đầy_mới, EC_mới = self.controller.tưới_cho_đến_khi_đầy()
        
        # Bước 5: Reflection Agent phản tư
        print("🤔 Reflection Agent đang phân tích...")
        reflection_text = self.reflection_agent.create_reflection(
            input_data={"T_chờ_phút": T_chờ_giây_demo},  # Ghi giây vào field phút
            output_data={"T_đầy_giây": T_đầy_mới, "EC_đo_được": EC_mới}
        )
        
        print(f"📝 Nhận xét: {reflection_text}")
        
        # Bước 6: Lưu trữ
        from components import InputData, OutputData, CycleRecord
        input_data = InputData(
            T_chờ_phút=T_chờ_giây_demo,  # Lưu giây vào field này
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
            reflection_text=f"{reflection_text} (Demo: {T_chờ_giây_demo}s)"
        )
        
        self.database.add_record(record)
        
        # Hiển thị trạng thái
        if abs(EC_mới - self.target_ec) <= 0.2:
            print(f"🎯 Tuyệt vời! EC {EC_mới} đã đạt gần mục tiêu {self.target_ec}")
        elif EC_mới > self.target_ec:
            print(f"📈 EC {EC_mới} cao hơn mục tiêu {self.target_ec}, cần tưới sớm hơn")
        else:
            print(f"📉 EC {EC_mới} thấp hơn mục tiêu {self.target_ec}, cần chờ lâu hơn")
            
        return True


class IrrigationWebUI:
    """Lớp quản lý giao diện web của hệ thống tưới"""
    
    def __init__(self):
        self.irrigation_system = DemoIrrigationSystem()  # Sử dụng phiên bản demo
        self.database = Database()
        self.is_running = False
        self.auto_mode = False
        
    def get_system_status(self) -> Tuple[str, str, str, str]:
        """Lấy trạng thái hệ thống hiện tại"""
        try:
            # Thông tin môi trường
            env_data = EnvironmentSensor.get_current_environment()
            env_info = f"""
            🌡️ **Nhiệt độ:** {env_data.nhiệt_độ}°C
            💧 **Độ ẩm:** {env_data.độ_ẩm}%
            🌿 **ET0:** {env_data.et0}
            """
            
            # Thông tin hệ thống
            last_record = self.database.get_last_record()
            total_cycles = len(self.database.data)
            
            if last_record:
                last_ec = last_record["output_data"]["EC_đo_được"]
                last_time = last_record["timestamp"]
                system_info = f"""
                🎯 **EC Mục tiêu:** {self.irrigation_system.target_ec}
                📊 **EC Gần nhất:** {last_ec}
                🔄 **Tổng chu trình:** {total_cycles}
                ⏰ **Lần cuối:** {last_time[:19]}
                """
            else:
                system_info = f"""
                🎯 **EC Mục tiêu:** {self.irrigation_system.target_ec}
                📊 **EC Gần nhất:** Chưa có dữ liệu
                🔄 **Tổng chu trình:** 0
                ⏰ **Lần cuối:** Chưa có
                """
            
            # Trạng thái hoạt động
            status = "🟢 Đang chạy" if self.is_running else "🔴 Dừng"
            auto_status = "🤖 Tự động" if self.auto_mode else "✋ Thủ công"
            
            return env_info, system_info, status, auto_status
            
        except Exception as e:
            return f"❌ Lỗi: {str(e)}", "", "", ""
    
    def run_single_cycle(self) -> str:
        """Chạy một chu trình tưới đơn lẻ"""
        try:
            self.is_running = True
            
            # Kiểm tra nếu cần hiệu chỉnh
            if not self.database.data:
                self.irrigation_system.run_calibration_phase()
                result = "✅ **Hoàn thành chu trình hiệu chỉnh**\\n\\nHệ thống đã được khởi tạo thành công."
            else:
                # Chạy chu trình vận hành
                success = self.irrigation_system.run_operation_cycle()
                if success:
                    last_record = self.database.get_last_record()
                    ec = last_record["output_data"]["EC_đo_được"]
                    wait_time = last_record["input_data"]["T_chờ_phút"]
                    
                    result = f"""
                    ✅ **Chu trình hoàn thành thành công!**
                    
                    📊 **EC đo được:** {ec}
                    ⏰ **Thời gian chờ:** {wait_time} giây (demo)
                    🎯 **EC mục tiêu:** {self.irrigation_system.target_ec}
                    """
                else:
                    result = "❌ **Có lỗi khi chạy chu trình tưới**"
            
            self.is_running = False
            return result
            
        except Exception as e:
            self.is_running = False
            return f"❌ **Lỗi:** {str(e)}"
    
    def get_history_data(self) -> pd.DataFrame:
        """Lấy dữ liệu lịch sử dưới dạng DataFrame"""
        history = self.database.get_recent_records(days=30)
        
        if not history:
            return pd.DataFrame()
        
        data = []
        for record in history:
            data.append({
                'ID': record['id'],
                'Thời gian': record['timestamp'][:19],
                'Giai đoạn': record['phase'],
                'Thời gian chờ (giây)': record['input_data']['T_chờ_phút'],  # Đổi label thành giây
                'Thời gian tưới (giây)': record['output_data']['T_đầy_giây'],
                'EC đo được': record['output_data']['EC_đo_được'],
                'Nhiệt độ (°C)': record['input_data']['môi_trường_tb']['nhiệt_độ'],
                'Độ ẩm (%)': record['input_data']['môi_trường_tb']['độ_ẩm']
            })
        
        return pd.DataFrame(data)
    
    def create_ec_chart(self) -> go.Figure:
        """Tạo biểu đồ EC theo thời gian"""
        df = self.get_history_data()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Chưa có dữ liệu để hiển thị",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title="📊 Biến động EC theo thời gian")
            return fig
        
        fig = go.Figure()
        
        # Đường EC thực tế
        fig.add_trace(go.Scatter(
            x=df['Thời gian'],
            y=df['EC đo được'],
            mode='lines+markers',
            name='EC đo được',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        # Đường EC mục tiêu
        fig.add_hline(
            y=self.irrigation_system.target_ec,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mục tiêu: {self.irrigation_system.target_ec}"
        )
        
        fig.update_layout(
            title="📊 Biến động EC theo thời gian",
            xaxis_title="Thời gian",
            yaxis_title="EC",
            hovermode='x unified',
            template="plotly_white"
        )
        
        return fig
    
    def create_environment_chart(self) -> go.Figure:
        """Tạo biểu đồ môi trường"""
        df = self.get_history_data()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Chưa có dữ liệu để hiển thị",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title="🌡️ Điều kiện môi trường")
            return fig
        
        fig = go.Figure()
        
        # Nhiệt độ
        fig.add_trace(go.Scatter(
            x=df['Thời gian'],
            y=df['Nhiệt độ (°C)'],
            mode='lines+markers',
            name='Nhiệt độ (°C)',
            yaxis='y',
            line=dict(color='red')
        ))
        
        # Độ ẩm
        fig.add_trace(go.Scatter(
            x=df['Thời gian'],
            y=df['Độ ẩm (%)'],
            mode='lines+markers',
            name='Độ ẩm (%)',
            yaxis='y2',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title="🌡️ Điều kiện môi trường theo thời gian",
            xaxis_title="Thời gian",
            yaxis=dict(title="Nhiệt độ (°C)", side="left"),
            yaxis2=dict(title="Độ ẩm (%)", side="right", overlaying="y"),
            hovermode='x unified',
            template="plotly_white"
        )
        
        return fig
    
    def get_data_analysis(self) -> str:
        """Phân tích dữ liệu và đưa ra khuyến nghị"""
        df = self.get_history_data()
        
        if df.empty:
            return "📭 **Chưa có dữ liệu để phân tích**\\n\\nHãy chạy ít nhất một chu trình tưới để có dữ liệu phân tích."
        
        # Thống kê cơ bản
        ec_avg = df['EC đo được'].mean()
        ec_std = df['EC đo được'].std()
        wait_avg = df['Thời gian chờ (giây)'].mean()  # Đổi thành giây
        temp_avg = df['Nhiệt độ (°C)'].mean()
        humidity_avg = df['Độ ẩm (%)'].mean()
        
        # Đánh giá hiệu suất
        target_ec = self.irrigation_system.target_ec
        deviation = abs(ec_avg - target_ec)
        
        if deviation <= 0.2:
            performance = "🎯 **Xuất sắc** - Hệ thống hoạt động rất tốt"
        elif deviation <= 0.5:
            performance = "✅ **Tốt** - Hệ thống hoạt động ổn định"
        elif deviation <= 1.0:
            performance = "⚠️ **Cần cải thiện** - Hệ thống cần điều chỉnh"
        else:
            performance = "❌ **Cần xem xét** - Hệ thống cần kiểm tra lại"
        
        # Xu hướng
        if len(df) >= 3:
            recent_ec = df['EC đo được'].tail(3).mean()
            earlier_ec = df['EC đo được'].head(3).mean()
            
            if abs(recent_ec - target_ec) < abs(earlier_ec - target_ec):
                trend = "📈 **Đang cải thiện** - Hệ thống học tốt"
            else:
                trend = "📉 **Cần theo dõi** - Hiệu suất chưa ổn định"
        else:
            trend = "📊 **Cần thêm dữ liệu** - Chưa đủ dữ liệu để đánh giá xu hướng"
        
        analysis = f"""
        ## 📊 Phân tích hiệu suất hệ thống
        
        ### 🎯 Hiệu suất tổng thể
        {performance}
        
        ### 📈 Xu hướng
        {trend}
        
        ### 📋 Thống kê chi tiết
        - **EC trung bình:** {ec_avg:.2f} (Mục tiêu: {target_ec})
        - **Độ lệch chuẩn EC:** {ec_std:.2f}
        - **Thời gian chờ trung bình:** {wait_avg:.1f} giây (demo)
        - **Nhiệt độ trung bình:** {temp_avg:.1f}°C
        - **Độ ẩm trung bình:** {humidity_avg:.1f}%
        - **Tổng số chu trình:** {len(df)}
        
        ### 💡 Khuyến nghị
        """
        
        # Đưa ra khuyến nghị
        if ec_avg > target_ec + 0.3:
            analysis += "- 🔄 Giảm thời gian chờ để EC không quá cao\\n"
        elif ec_avg < target_ec - 0.3:
            analysis += "- ⏰ Tăng thời gian chờ để EC đạt mục tiêu\\n"
        
        if ec_std > 0.5:
            analysis += "- 📊 EC biến động nhiều, cần ổn định hệ thống\\n"
        
        if temp_avg > 32:
            analysis += "- 🌡️ Nhiệt độ cao, có thể cần tưới thường xuyên hơn\\n"
        
        if humidity_avg < 65:
            analysis += "- 💧 Độ ẩm thấp, cần theo dõi chặt chẽ\\n"
        
        return analysis
    
    def toggle_auto_mode(self, enabled: bool) -> str:
        """Bật/tắt chế độ tự động"""
        self.auto_mode = enabled
        if enabled:
            return "🤖 **Chế độ tự động được BẬT**\\n\\nHệ thống sẽ tự động chạy chu trình theo lịch."
        else:
            return "✋ **Chế độ tự động được TẮT**\\n\\nHệ thống chỉ chạy khi được yêu cầu thủ công."


def create_gradio_interface():
    """Tạo giao diện Gradio"""
    
    # Khởi tạo hệ thống
    irrigation_ui = IrrigationWebUI()
    
    # CSS tùy chỉnh
    css = """
    .gradio-container {
        font-family: 'Arial', sans-serif;
    }
    .status-box {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 15px;
        background-color: #f9f9f9;
    }
    """
    
    with gr.Blocks(
        title="🌱 Hệ thống Tưới Tự Động Thông Minh",
        theme=gr.themes.Soft(),
        css=css
    ) as app:
        
        gr.Markdown("""
        # 🌱 Hệ thống Tưới Tự Động Thông Minh
        ### Điều khiển và giám sát hệ thống tưới dựa trên AI
        """)
        
        # Tab chính
        with gr.Tabs():
            
            # Tab Dashboard
            with gr.Tab("📊 Dashboard"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🌡️ Môi trường hiện tại")
                        env_status = gr.Markdown()
                        
                    with gr.Column(scale=1):
                        gr.Markdown("### ⚙️ Trạng thái hệ thống")
                        system_status = gr.Markdown()
                        
                    with gr.Column(scale=1):
                        gr.Markdown("### 🔄 Hoạt động")
                        running_status = gr.Markdown()
                        auto_status = gr.Markdown()
                
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Làm mới", variant="secondary")
                    run_cycle_btn = gr.Button("🚀 Chạy chu trình", variant="primary")
                
                cycle_result = gr.Markdown()
                
                # Biểu đồ
                with gr.Row():
                    ec_chart = gr.Plot(label="📊 Biến động EC")
                    env_chart = gr.Plot(label="🌡️ Môi trường")
            
            # Tab Lịch sử
            with gr.Tab("📋 Lịch sử"):
                gr.Markdown("### 📊 Dữ liệu lịch sử tưới")
                history_table = gr.Dataframe(
                    headers=["ID", "Thời gian", "Giai đoạn", "Thời gian chờ (giây)", 
                            "Thời gian tưới (giây)", "EC đo được", "Nhiệt độ (°C)", "Độ ẩm (%)"],
                    interactive=False
                )
                
                refresh_history_btn = gr.Button("🔄 Làm mới lịch sử")
            
            # Tab Phân tích
            with gr.Tab("📈 Phân tích"):
                gr.Markdown("### 🧠 Phân tích thông minh")
                analysis_result = gr.Markdown()
                
                analyze_btn = gr.Button("🔍 Phân tích dữ liệu", variant="primary")
            
            # Tab Cài đặt
            with gr.Tab("⚙️ Cài đặt"):
                gr.Markdown("### 🎛️ Cài đặt hệ thống")
                
                with gr.Row():
                    auto_mode_toggle = gr.Checkbox(
                        label="🤖 Chế độ tự động",
                        info="Bật để hệ thống tự động chạy theo lịch"
                    )
                
                auto_mode_result = gr.Markdown()
        
        # Hàm cập nhật dashboard
        def update_dashboard():
            env_info, sys_info, status, auto_stat = irrigation_ui.get_system_status()
            ec_fig = irrigation_ui.create_ec_chart()
            env_fig = irrigation_ui.create_environment_chart()
            return env_info, sys_info, status, auto_stat, ec_fig, env_fig
        
        # Hàm cập nhật lịch sử
        def update_history():
            return irrigation_ui.get_history_data()
        
        # Event handlers
        refresh_btn.click(
            fn=update_dashboard,
            outputs=[env_status, system_status, running_status, auto_status, ec_chart, env_chart]
        )
        
        run_cycle_btn.click(
            fn=irrigation_ui.run_single_cycle,
            outputs=[cycle_result]
        ).then(
            fn=update_dashboard,
            outputs=[env_status, system_status, running_status, auto_status, ec_chart, env_chart]
        )
        
        refresh_history_btn.click(
            fn=update_history,
            outputs=[history_table]
        )
        
        analyze_btn.click(
            fn=irrigation_ui.get_data_analysis,
            outputs=[analysis_result]
        )
        
        auto_mode_toggle.change(
            fn=irrigation_ui.toggle_auto_mode,
            inputs=[auto_mode_toggle],
            outputs=[auto_mode_result]
        )
        
        # Tự động cập nhật ban đầu
        app.load(
            fn=update_dashboard,
            outputs=[env_status, system_status, running_status, auto_status, ec_chart, env_chart]
        )
        
        app.load(
            fn=update_history,
            outputs=[history_table]
        )
    
    return app


def main():
    """Khởi chạy ứng dụng web"""
    print("🌱 Khởi động Hệ thống Tưới Tự Động Web UI...")
    print("=" * 50)
    
    app = create_gradio_interface()
    
    print("🚀 Server đang chạy tại:")
    print("   📱 Local: http://localhost:7860")
    print("   🌐 Network: http://0.0.0.0:7860")
    print("⏹️  Nhấn Ctrl+C để dừng server")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        quiet=False,
    )


if __name__ == "__main__":
    main()
