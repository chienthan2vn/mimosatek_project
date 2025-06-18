import os
from typing import Dict, List
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Shared LLM instance
shared_llm = OpenAILike(
    id="gemini-1.5-flash",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

class ReflectionAgent:
    """Agent phản tư - tạo nhận xét định tính"""
    
    def __init__(self):
        self.agent = Agent(
            model=shared_llm,
            name="Reflection Agent",
            description="Chuyên gia nông học phân tích chu trình tưới",
        )
    
    def create_reflection(self, input_data: Dict, output_data: Dict) -> str:
        """Tạo nhận xét định tính cho chu trình vừa kết thúc"""
        
        prompt = f"""Bạn là một chuyên gia nông học có nhiệm vụ phân tích và tạo nhận xét để ghi vào nhật ký hệ thống.

**Mục tiêu:**
Đánh giá chu trình tưới vừa kết thúc dựa trên mục tiêu EC=4.0. Nhận xét của bạn sẽ được Plan Agent sử dụng trong chu trình tiếp theo để ra quyết định.

**Dữ liệu chu trình vừa kết thúc:**
- Thời gian chờ đã dùng: {input_data['T_chờ_phút']} phút
- Thời gian tưới đầy: {output_data['T_đầy_giây']} giây  
- EC đo được: {output_data['EC_đo_được']}

**Yêu cầu:**
Tạo một chuỗi văn bản nhận xét ngắn gọn, súc tích và mang tính gợi ý (không quá 100 từ).
Tập trung vào việc so sánh EC với mục tiêu 4.0 và đánh giá thời gian chờ có phù hợp không.

Chỉ trả về văn bản nhận xét, không cần giải thích thêm."""

        try:
            response = self.agent.run(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"❌ Lỗi Reflection Agent: {e}")
            return f"EC={output_data['EC_đo_được']} so với mục tiêu 4.0. Thời gian chờ {input_data['T_chờ_phút']} phút cần được đánh giá lại."

class PlanAgent:
    """Agent lập kế hoạch - quyết định thời gian chờ tiếp theo"""
    
    def __init__(self):
        self.agent = Agent(
            model=shared_llm,
            name="Plan Agent",
            description="Chuyên gia điều khiển hệ thống tưới thông minh",
        )
    
    def decide_next_wait_time(self, 
                            last_reflection: str,
                            history: List[Dict], 
                            current_env: Dict,
                            forecast: str) -> Dict:
        """Quyết định thời gian chờ tiếp theo"""
        
        # Chuẩn bị dữ liệu lịch sử
        history_summary = []
        for record in history[-5:]:  # Chỉ lấy 5 bản ghi gần nhất
            history_summary.append({
                "T_chờ_phút": record["input_data"]["T_chờ_phút"],
                "EC_đo_được": record["output_data"]["EC_đo_được"],
                "reflection": record["reflection_text"][:50] + "..." if record["reflection_text"] else ""
            })
        
        prompt = f"""Bạn là một chuyên gia điều khiển hệ thống tưới thông minh, có khả năng kết hợp phân tích dữ liệu định lượng và nhận định định tính để ra quyết định tối ưu.

**Mục tiêu chính:**
Điều chỉnh khoảng thời gian chờ (T_chờ) để đưa giá trị EC về gần mức mục tiêu là 4.0.

**Dữ liệu cung cấp:**

1. **Nhận xét từ chu trình gần nhất:**
{last_reflection}

2. **Lịch sử vận hành gần đây:**
{json.dumps(history_summary, ensure_ascii=False, indent=2)}

3. **Dữ liệu môi trường hiện tại:**
{json.dumps(current_env, ensure_ascii=False, indent=2)}

4. **Dự báo thời tiết:**
{forecast}

**Quy tắc quan trọng:**
- EC cao (>4.0): Cần giảm thời gian chờ để tưới sớm hơn
- EC thấp (<4.0): Cần tăng thời gian chờ để nước bay hơi nhiều hơn  
- Thời gian chờ nên trong khoảng 60-300 phút
- Thay đổi từng bước, không nhảy vọt quá lớn

**Yêu cầu:**
Dựa trên cả nhận xét định tính và dữ liệu định lượng, hãy tính toán và đề xuất khoảng thời gian chờ tiếp theo.

**Format trả lời phải là một JSON object:**
{{
  "T_chờ_đề_xuất": <số phút>,
  "lý_do": "<giải thích ngắn gọn về logic quyết định>"
}}

Chỉ trả về JSON object, không thêm text nào khác."""

        try:
            response = self.agent.run(prompt)
            # Parse JSON response
            result = json.loads(response.content.strip())
            
            # Validate kết quả
            if not isinstance(result.get("T_chờ_đề_xuất"), (int, float)):
                raise ValueError("T_chờ_đề_xuất không hợp lệ")
                
            # Đảm bảo thời gian chờ trong khoảng hợp lý
            wait_time = max(60, min(300, int(result["T_chờ_đề_xuất"])))
            result["T_chờ_đề_xuất"] = wait_time
            
            return result
            
        except Exception as e:
            print(f"❌ Lỗi Plan Agent: {e}")
            # Fallback strategy
            if history:
                last_ec = history[-1]["output_data"]["EC_đo_được"]
                last_wait = history[-1]["input_data"]["T_chờ_phút"]
                
                if last_ec > 4.0:
                    new_wait = max(60, last_wait - 30)
                else:
                    new_wait = min(300, last_wait + 30)
            else:
                new_wait = 120
                
            return {
                "T_chờ_đề_xuất": new_wait,
                "lý_do": "Sử dụng logic fallback do lỗi LLM"
            }
