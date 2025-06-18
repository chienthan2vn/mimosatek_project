# Hệ thống Tưới Tự Động Thông Minh

Hệ thống tưới tự động dựa trên AI với vòng lặp phản hồi kép, kết hợp phân tích định lượng và định tính.

## Đặc điểm

- **Vòng lặp Phản hồi Kép**: Học từ cả dữ liệu số và nhận xét ngôn ngữ tự nhiên
- **Trí nhớ Toàn diện**: Lưu trữ lịch sử hoàn chỉnh dưới dạng JSON
- **2 Giai đoạn**: Hiệu chỉnh và Vận hành riêng biệt
- **AI Agents**: Plan Agent và Reflection Agent

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Cấu hình file `.env` (sửa tên file .env_example thành .env):
```
OPENAI_API_KEY=your_gemini_api_key_here
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

## Sử dụng

```bash
python main.py
```

## Cấu trúc

- `main.py`: Chương trình chính
- `components.py`: Các thành phần cơ bản (Controller, Database, Sensors)
- `agents.py`: AI Agents (Plan Agent, Reflection Agent)
- `requirements.txt`: Dependencies
- `.env`: Cấu hình môi trường

## Luồng hoạt động

1. **Giai đoạn Hiệu chỉnh**: Chu trình khởi tạo đầu tiên
2. **Giai đoạn Vận hành**: Vòng lặp tối ưu hóa liên tục
   - Plan Agent quyết định thời gian chờ
   - Thực hiện tưới và đo EC
   - Reflection Agent tạo nhận xét
   - Lưu trữ và lặp lại

## Mục tiêu

Điều chỉnh thời gian chờ để đạt EC = 4.0 một cách tối ưu.
