# Workflow Hệ thống Tưới Thông minh sử dụng LLM Agent

Tài liệu này mô tả chi tiết luồng hoạt động, kiến trúc, cấu trúc dữ liệu và các prompt cốt lõi của hệ thống tưới tự động, được điều khiển bởi LLM Agent.

## 1. Mục tiêu & Nguyên tắc Thiết kế

### 1.1. Mục tiêu

- **Tự động hóa:** Tự động điều chỉnh lịch tưới cho cây giống trong bầu.
- **Tối ưu hóa:** Duy trì nồng độ dinh dưỡng (EC) trong bầu cây ở mức mục tiêu **4.0**.
- **Tự học hỏi:** Hệ thống có khả năng tự cải thiện dựa trên dữ liệu lịch sử và kết quả thực tế.

### 1.2. Nguyên tắc Thiết kế

1.  **Vòng lặp Phản hồi Kép:** `Plan Agent` ra quyết định dựa trên cả dữ liệu định lượng (số liệu đo đạc) và nhận xét định tính (văn bản do `Reflection LLM` tạo ra).
2.  **Trí nhớ Toàn diện (JSON):** Mỗi chu trình tưới được lưu trữ như một đối tượng JSON hoàn chỉnh, đóng vai trò là "trí nhớ" dài hạn của hệ thống.
3.  **Tách biệt Giai đoạn:** Quy trình được chia thành 2 giai đoạn rõ ràng: `Hiệu chỉnh` (khởi tạo) và `Vận hành` (tối ưu).
4.  **Điều khiển dựa trên Sự kiện:** Hành động tưới luôn kết thúc khi cảm biến EC phát hiện dòng chảy (`Tưới_Cho_Đến_Khi_Đầy`), đảm bảo tính chính xác và nhất quán.

## 2. Kiến trúc Hệ thống

Hệ thống bao gồm 4 thành phần chính:

-   `Controller`: "Tay chân" của hệ thống, thực thi lệnh tưới và đọc cảm biến.
-   `Database (Trí nhớ)`: Lưu trữ toàn bộ lịch sử các chu trình dưới dạng các đối tượng JSON.
-   `Reflection Agent`: "Nhà phân tích", chuyển đổi dữ liệu số thành nhận xét định tính.
-   `Plan Agent`: "Bộ não", ra quyết định về lịch trình tưới tiếp theo.

## 3. Cấu trúc Dữ liệu (JSON Schema)

Mỗi chu trình tưới được lưu vào `Database` dưới dạng một đối tượng JSON theo cấu trúc sau:

```json
{
  "id": 123,
  "timestamp": "2023-10-27T14:30:00Z",
  "phase": "operation",
  "input_data": {
    "T_chờ_phút": 150,
    "môi_trường_tb": {
      "nhiệt_độ": 31.8,
      "độ_ẩm": 68.5,
      "et0": 0.26
    }
  },
  "output_data": {
    "T_đầy_giây": 38,
    "EC_đo_được": 4.8
  },
  "reflection_text": "EC=4.8 vẫn cao hơn mục tiêu 4.0. Khoảng chờ 150 phút có thể vẫn còn hơi dài trong điều kiện thời tiết này. Cần xem xét rút ngắn hơn nữa."
}
```

## 4. Luồng Hoạt động Chi tiết (Workflow)

### Giai đoạn 1: Hiệu chỉnh (Cold Start)

> **Mục đích:** Đưa hệ thống từ trạng thái không xác định về trạng thái đã biết và thu thập dữ liệu nền. Thực hiện **một lần** khi khởi động.

1.  **Kích hoạt:** Hệ thống bắt đầu với trạng thái `cần hiệu chỉnh`.
2.  **Hành động:** `Controller` thực thi lệnh `Tưới_Cho_Đến_Khi_Đầy()`.
3.  **Lưu trữ:** Một bản ghi JSON mới được tạo và lưu vào `Database` với `"phase": "calibration"`.

### Giai đoạn 2: Vận hành & Tối ưu (Vòng lặp)

> **Mục đích:** Liên tục tối ưu khoảng thời gian chờ (`T_chờ`) để duy trì EC ở mức 4.0.

#### **Vòng lặp bắt đầu:**

1.  **Chuẩn bị Context:**
    *   Hệ thống truy vấn `Database` để lấy:
        *   **Lịch sử JSON:** Mảng các đối tượng JSON của các chu trình trong **3 ngày gần nhất**.
        *   **Nhận xét gần nhất:** Giá trị `reflection_text` từ bản ghi JSON cuối cùng.
    *   Hệ thống gọi các `tool` để lấy dữ liệu môi trường hiện tại và dự báo thời tiết.

2.  **Quyết định:**
    *   Toàn bộ context được đưa vào `Plan Agent`.
    *   `Plan Agent` phân tích và trả về quyết định `T_chờ_mới`.

3.  **Chờ:**
    *   Hệ thống tạm dừng hoạt động và đợi trong khoảng thời gian `T_chờ_mới`.

4.  **Hành động & Thu thập kết quả:**
    *   Khi hết thời gian chờ, `Controller` thực thi lệnh `Tưới_Cho_Đến_Khi_Đầy()`.
    *   Kết quả `T_đầy_mới` và `EC_mới` được ghi nhận.

5.  **Phản tư (Reflection):**
    *   Dữ liệu của chu trình vừa rồi (`T_chờ_mới`, `T_đầy_mới`, `EC_mới`) được đưa vào `Reflection Agent`.
    *   `Reflection Agent` tạo ra một chuỗi `reflection_text` mới.

6.  **Lưu trữ & Lặp lại:**
    *   Một bản ghi JSON hoàn chỉnh mới (chứa cả `reflection_text` vừa tạo) được ghi vào `Database`.
    *   Hệ thống quay lại **Bước 1** của Giai đoạn Vận hành.

## 5. Prompts của các Agent

### 5.1. Prompt cho `Reflection Agent`

> **Mục tiêu:** Tạo nhận xét định tính để `Plan Agent` sử dụng.

```text
Bạn là một chuyên gia nông học có nhiệm vụ phân tích và tạo nhận xét để ghi vào nhật ký hệ thống.
**Mục tiêu:**
Đánh giá chu trình tưới vừa kết thúc dựa trên mục tiêu EC=4.0. Nhận xét của bạn sẽ được Plan Agent sử dụng trong chu trình tiếp theo để ra quyết định.

**Dữ liệu chu trình vừa kết thúc (JSON):**
{
  "input_data": { "T_chờ_phút": 150 },
  "output_data": { "T_đầy_giây": 38, "EC_đo_được": 4.8 }
}

**Yêu cầu:**
Tạo một chuỗi văn bản nhận xét ("reflection_text") ngắn gọn, súc tích và mang tính gợi ý.
```

### 5.2. Prompt cho `Plan Agent`

> **Mục tiêu:** Quyết định `T_chờ` tiếp theo dựa trên dữ liệu định lượng và định tính.

```text
Bạn là một chuyên gia điều khiển hệ thống tưới thông minh, có khả năng kết hợp phân tích dữ liệu định lượng và nhận định định tính để ra quyết định tối ưu.
**Mục tiêu chính:**
Điều chỉnh khoảng thời gian chờ (`T_chờ`) để đưa giá trị EC về gần mức mục tiêu là **4.0**.

**Dữ liệu cung cấp:**

1.  **Nhận xét từ chu trình gần nhất:**
    // [Hệ thống tự động điền giá trị `reflection_text` từ bản ghi JSON cuối cùng vào đây]
    "EC=4.8 vẫn cao hơn mục tiêu 4.0. Khoảng chờ 150 phút có thể vẫn còn hơi dài trong điều kiện thời tiết này. Cần xem xét rút ngắn hơn nữa."

2.  **Lịch sử vận hành (Dữ liệu JSON thô của 3 ngày gần nhất):**
    // [Hệ thống tự động điền mảng các đối tượng JSON lịch sử vào đây]
    [
      { "id": 121, "input_data": {"T_chờ_phút": 180}, "output_data": {"EC_đo_được": 5.2}, "reflection_text": "..." },
      { "id": 122, "input_data": {"T_chờ_phút": 150}, "output_data": {"EC_đo_được": 4.8}, "reflection_text": "..." }
    ]

3.  **Dữ liệu môi trường hiện tại & Dự báo (12 giờ tới):**
    // [Hệ thống tự động điền dữ liệu từ tools vào đây]
    {
      "hiện_tại": { "nhiệt_độ": 32, "độ_ẩm": 70 },
      "dự_báo": "Trời nắng, nhiệt độ có xu hướng tăng nhẹ."
    }

**Yêu cầu:**
Dựa trên **cả nhận xét định tính và dữ liệu định lượng**, hãy tính toán và đề xuất khoảng thời gian chờ tiếp theo (`T_chờ`). Hãy giải thích logic của bạn, cho thấy bạn đã cân nhắc tất cả các nguồn thông tin.

**Format trả lời phải là một JSON object:**
{
  "T_chờ_đề_xuất": <số phút>,
  "lý_do": "<giải thích về việc bạn đã tổng hợp nhận xét và dữ liệu số như thế nào>"
}
```