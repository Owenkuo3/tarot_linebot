from flask import Flask, request, abort
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3
from datetime import datetime

app = Flask(__name__)

line_bot_api = LineBotApi('M4a2HWyiSIlZAMB+ciIw6ZsEOZBavOT9ClySuBAGBRu4elOXLuYjJ2bTUEZlOyoagFoxByYGrX1gD3glTGXHi83mDwpbRAuu4/XJJadfjnsR5GVhJGEaB9U1cczXuebJTcjIRxqJKmzrzADVd4Gg6gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('691f964a7ef924b0dfde14ea617eef8f')

user_stages = {}  # 用戶階段記錄


def parse_user_input(input_str):
    try:
        # 假设用户输入的日期格式为 "YYYY-MM-DD"，例如 "2023-08-31"
        user_date = datetime.strptime(input_str, "%Y-%m-%d")
        return user_date
    except ValueError:
        return None

# 使用示例
user_input = "2023-08-31"
parsed_date = parse_user_input(user_input)

if parsed_date:
    print("解析成功，日期为:", parsed_date)
else:
    print("日期解析失败")


def get_question_by_date(date):
    try:
        conn = sqlite3.connect('tarot.db')
        cursor = conn.cursor()

        cursor.execute("SELECT question FROM tarot_questions WHERE date = ?", (date,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        else:
            return "抱歉，我找不到与您选择的日期匹配的问题。"
    except sqlite3.Error as e:
        return "数据库查询出现错误：" + str(e)
    
def get_answer_by_date(question, option):
    try:
        conn = sqlite3.connect('tarot.db')
        cursor = conn.cursor()

        # 假设数据库中有一个表 tarot_options 存储了问题的选项及对应的答案
        cursor.execute("SELECT answer FROM tarot_options WHERE question = ? AND option = ?", (question, option))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        else:
            return "抱歉，我找不到与您选择的选项匹配的答案。"
    except sqlite3.Error as e:
        return "数据库查询出现错误：" + str(e)
    
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text
    
    if user_input.lower() == '開始':
        user_stages[user_id] = 1
        reply_message = TextSendMessage(text="請輸入日期（例如：2000.01.01）")
    
    elif user_stages.get(user_id) == 1:
        # 第一階段：請它們輸入日期
        # 在這裡處理日期的輸入，例如將字符串轉換為日期對象
        # 假設 user_date 是日期對象
        user_date = parse_user_input(user_input)  # 根據實際需求處理日期輸入
        
        # 在這裡從資料庫中查找對應的題目
        question = get_question_by_date(user_date)
        
        user_stages[user_id] = 2
        reply_message = TextSendMessage(text=f"您選擇的日期是：{user_date}\n對應的題目是：{question}\n請選擇選項 A、B、C 或 D。")
    
    elif user_stages.get(user_id) == 2:
        # 第二階段：回傳題目對應的選項答案
        answer = get_answer_by_date(question)  # 假設您有一個函式 get_answer() 從資料庫中獲取相應的答案
        reply_message = TextSendMessage(text=f"您選的題目是：{question}\n答案是：{answer}\n是否需要再選一個選項？（是/否）")
        user_stages[user_id] = 3
    
    elif user_stages.get(user_id) == 3:
        # 第三階段：根據回答回傳相應的結果
        if user_input == '是':
            user_stages[user_id] = 4  # 进入新的阶段，等待用户输入选项
            reply_message = TextSendMessage(text="請輸入選項（例如：A、B、C 或 D）。")
        elif user_input == '否':
            user_stages[user_id] = 1
            reply_message = TextSendMessage(text="請輸入日期（例如：2000.01.01）")

    # 新的阶段，等待用户输入选项
    elif user_stages.get(user_id) == 4:
        # 在这里处理用户输入的选项，然后根据选项获取答案
        option = user_input  # 根据实际需求处理选项输入
        answer = get_answer_by_date(question, option)  # 假设有一个函数从数据库中获取相应选项的答案
        reply_message = TextSendMessage(text=f"您選的選項是 {option}。\n答案是：{answer}。是否需要再選一個選項？請輸入是或否。")
        user_stages[user_id] = 3
    
    line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == "__main__":
    app.run()
