from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
from ..config import CHAT_URL, MAX_WAIT_TIME, PAGE_LOAD_WAIT
from .browser import create_browser

class ChatAPI:
    def __init__(self):
        self.ready = False
        print("正在打开聊天界面...")
        self.driver = create_browser()
        self.driver.get(CHAT_URL)
        self._wait_for_chat_ready()

    def _wait_for_chat_ready(self):
        try:
            # 等待输入框出现，最多等待30秒
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "send_textarea"))
            )
            print("聊天界面已就绪")
            self.ready = True
        except TimeoutException:
            print("等待聊天界面超时")
            self.ready = False

    def is_ready(self):
        return self.ready

    def get_chat_response(self):
        logs = self.driver.get_log('performance')
        for log in logs:
            message = json.loads(log['message'])['message']
            if ('Network.responseReceived' in message['method'] and 
                'response' in message['params'] and 
                message['params']['response']['url'].endswith('/api/backends/text-completions/generate')):
                request_id = message['params']['requestId']
                try:
                    response = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    return json.loads(response['body'])
                except Exception:
                    continue
        return None

    def send_message(self, message):
        if not self.ready:
            return "聊天系统尚未就绪，请稍后再试"
        
        try:
            input_box = self.driver.find_element(By.ID, 'send_textarea')
            input_box.clear()
            input_box.send_keys(message)
            input_box.send_keys(Keys.RETURN)
            
            start_time = time.time()
            while True:
                response = self.get_chat_response()
                if response:
                    return response['response']
                    
                if time.time() - start_time > MAX_WAIT_TIME:
                    return "等待响应超时"
                    
                time.sleep(0.5)
                
        except Exception as e:
            return f"发生错误：{str(e)}"

    def close(self):
        self.driver.quit() 