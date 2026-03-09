from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Consultant Assistant API")

# Configure CORS for local development testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize OpenAI Client for DashScope (阿里云百炼)
# Note: DashScope uses the OpenAI SDK format
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY") or "sk-f7bb5fba6b484f4bb8f57c38d259a6d2"
if not dashscope_api_key:
    print("WARNING: DASHSCOPE_API_KEY environment variable not set.")

client = AsyncOpenAI(
    api_key=dashscope_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    max_retries=0 # Ensure fast fallback
)

# Initialize OpenAI Client for Zhipu (GLM) fallback
glm_api_key = os.getenv("GLM_API_KEY") or "8e20cfcac7a04e76ad4ed7ea32857a38.Y5krkwWIfwxoXXZj"
glm_client = AsyncOpenAI(
    api_key=glm_api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    max_retries=0 # Ensure clean failure for frontend
)

# Feedback Storage Plan
FEEDBACK_FILE = Path(__file__).parent / "意见反馈文件.txt"

# Request Models
class FeedbackRequest(BaseModel):
    feedback: str

class AnalysisRequest(BaseModel):
    requirement: str

# Read the system prompt from the file
def get_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an AI Consultant Assistant. Analyze the requirements and provide a structured plan."

# ✅ Serve the frontend HTML at the root URL
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = Path(__file__).parent / "ai_consultant_assistant_ui.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(Path(__file__).parent / "favicon.ico")

@app.post("/api/feedback")
async def collect_feedback(request: FeedbackRequest):
    if not request.feedback.strip():
        raise HTTPException(status_code=400, detail="Feedback cannot be empty")
    
    try:
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- Feedback Entry ---\n{request.feedback}\n\n")
        return {"status": "success", "message": "Knowledge recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_requirement(request: AnalysisRequest):
    if not request.requirement.strip():
        raise HTTPException(status_code=400, detail="Requirement text cannot be empty")
        
    try:
        system_prompt = get_system_prompt()
        
        import re
        
        prompt_payload = [
            {"role": "system", "content": system_prompt + """

**CRITICAL INSTRUCTION FOR OUTPUT FORMAT**:
You MUST output a valid JSON object. Your output must exactly match the following JSON schema. 

{
  "features": [
    {
      "id": 1,
      "name": "必须存在的功能模块名称",
      "type": "纯工程实现" 或 "复合/大模型驱动",
      "engineering": {
        "architecture": "原理解释（讲解架构与交互方案核心逻辑）...",
        "data_requirements": "说明实现该功能我们需要收集哪些数据，并应用在何处..."
      },
      "llm": { 
        "prompt_strategy": "说明基于何种提示词框架实现及预期效果...",
        "ai_capabilities": "说明需要用到哪些具体的AI能力以及构建知识库需要哪些业务数据..."
      },
      "consultant_advice": "（必填）向AI顾问提供的审查与推演建议：用通俗语言。如果评估该功能通过大模型实现可行度高，明确建议顾问可以继续深化此需求；如果评估存在困难或超出能力边界，指出问题并给出将需求向大模型擅长方向转变的指导建议。"
    }
  ],
  "disclaimer": "此报告仅供参考，不能直接作为与客户沟通的依据。里面内容还需要进行技术验证。"
}

Note: IF the "type" is "纯工程实现", you MUST omit the "llm" key or set it to null. However, "consultant_advice" MUST always be provided for ALL features."""},
            {"role": "user", "content": request.requirement}
        ]
        
        try:
            print("Attempting analysis with primary model: qwen-plus")
            # Call Qwen API first (usually faster for structured output recently)
            response = await client.chat.completions.create(
                model="qwen-plus",
                messages=prompt_payload,
                timeout=10 # Very tight to allow fallback window
            )
            result_text = response.choices[0].message.content
            print("Successfully received response from Qwen.")
        except Exception as qwen_err:
            print(f"Qwen API error: {qwen_err}. Falling back to GLM-Flash (Zhipu)...")
            # Fallback to GLM-Flash (extreme speed, high availability)
            response = await glm_client.chat.completions.create(
                model="glm-4-flash",
                messages=prompt_payload,
                timeout=12 
            )
            result_text = response.choices[0].message.content
            print("Successfully received fallback response from GLM-Flash.")
        
        # Parse the JSON response dynamically
        # (Redundant assignment removed)
        
        # Extract JSON from possible Markdown wrappers
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = result_text.strip()
            
        result_json = json.loads(json_str)
        
        return result_json
        
    except Exception as e:
        print(f"Error calling Qwen API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Use PORT env var for Railway compatibility
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
