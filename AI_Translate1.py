


import pyperclip
import requests
import time
import os
import json

# --- 配置 ---
# 嘗試從環境變數讀取 API Key，如果沒有則提示用戶輸入或直接在此處填寫
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    API_KEY = "API KEY" # <--- 如果不使用環境變數，請在此處替換你的 API Key

# Gemini API endpoint - 已更新為 gemini-2.0-flash
# 請確保你的 API Key 有權限使用 gemini-2.0-flash 模型
MODEL_NAME = "gemini-2.0-flash" # <--- 修改點：指定模型名稱
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"


# 翻譯提示詞
TRANSLATION_PROMPT_PREFIX = "你是一個將文字翻譯成繁體中文的助手，我們情境多半是工業應用。\n\n請翻譯以下文字：\n"

# 監控間隔 (秒)
POLL_INTERVAL = 1
# --- 配置結束 ---

def call_gemini_translate(text_to_translate):
    """使用 Gemini API 翻譯文字"""
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        print("錯誤：Gemini API Key 未配置。請設置 GEMINI_API_KEY 環境變數或在腳本中修改。")
        return None

    full_prompt = TRANSLATION_PROMPT_PREFIX + text_to_translate

    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ],
        # 你可以添加 generationConfig 來控制輸出，例如溫度等
        # "generationConfig": {
        #   "temperature": 0.7,
        #   "topK": 1,
        #   "topP": 1,
        #   "maxOutputTokens": 2048, # Gemini Flash 通常有較大的上下文和輸出 token 限制
        #   "stopSequences": []
        # }
    }

    try:
        print(f"正在使用模型 {MODEL_NAME} 進行翻譯...")
        response = requests.post(API_URL, headers=headers, json=data, timeout=30) # 增加 timeout
        response.raise_for_status()  # 如果 HTTP 請求返回了錯誤狀態碼，則拋出異常
        
        response_json = response.json()
        
        # 檢查 Gemini 回應結構
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            content = response_json["candidates"][0].get("content", {})
            if "parts" in content and len(content["parts"]) > 0:
                translated_text = content["parts"][0].get("text", "")
                return translated_text.strip()
            else:
                print(f"警告：API 回應中找不到 'parts'。回應：{response_json}")
                return None
        elif "promptFeedback" in response_json and "blockReason" in response_json["promptFeedback"]:
            reason = response_json["promptFeedback"]["blockReason"]
            print(f"警告：請求可能因 '{reason}' 而被阻止。")
            if "safetyRatings" in response_json["promptFeedback"]:
                print(f"安全評級: {response_json['promptFeedback']['safetyRatings']}")
            return None
        else:
            print(f"警告：API 回應格式不符合預期。回應：{response_json}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"API 請求錯誤: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"API 錯誤詳情: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"API 錯誤詳情 (非 JSON): {e.response.text}")
        return None
    except Exception as e:
        print(f"處理 API 回應時發生未知錯誤: {e}")
        return None

def main():
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        print("請先在腳本中設定您的 GEMINI_API_KEY。")
        return

    print("剪貼簿翻譯助手已啟動...")
    print(f"將監控剪貼簿，使用模型 '{MODEL_NAME}' 進行翻譯。")
    print(f"提示詞前綴：'{TRANSLATION_PROMPT_PREFIX[:30]}...'")
    
    try:
        # 獲取初始剪貼簿內容，避免啟動時立即翻譯
        previous_clipboard_content = pyperclip.paste()
        print("初始剪貼簿內容已記錄，等待新的複製操作...")
    except pyperclip.PyperclipException as e:
        print(f"無法訪問剪貼簿，請確保已安裝 xclip (Linux) 或 xsel (Linux) 或配置正確: {e}")
        print("在 Linux 上，你可能需要執行 'sudo apt-get install xclip' 或 'sudo apt-get install xsel'")
        return


    while True:
        try:
            current_clipboard_content = pyperclip.paste()
        except pyperclip.PyperclipException as e:
            print(f"無法讀取剪貼簿: {e}. 稍後重試...")
            time.sleep(POLL_INTERVAL * 5) # 如果讀取失敗，等待更長時間
            continue

        if current_clipboard_content != previous_clipboard_content and current_clipboard_content:
            print(f"\n偵測到新剪貼簿內容:\n'''\n{current_clipboard_content}\n'''")
            
            translated_text = call_gemini_translate(current_clipboard_content)

            if translated_text:
                print(f"翻譯結果:\n'''\n{translated_text}\n'''")
                try:
                    pyperclip.copy(translated_text)
                    print("翻譯結果已複製到剪貼簿。")
                    previous_clipboard_content = translated_text 
                except pyperclip.PyperclipException as e:
                    print(f"無法複製到剪貼簿: {e}")
                    previous_clipboard_content = current_clipboard_content 
            else:
                print("翻譯失敗或無結果。")
                previous_clipboard_content = current_clipboard_content
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
