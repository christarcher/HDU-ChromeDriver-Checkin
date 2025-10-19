from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import pickle
import random
import sys
import logging
import argparse
from pathlib import Path


class DingtalkSignin:
    # 默认配置
    DEFAULT_LOCATION = [30.3203028, 120.3372421]  # 杭电图书馆
    LOGIN_URL = 'https://skl.hdu.edu.cn/api/login/dingtalk/auth?index=&code=0&authCode=0&state=0'
    DINGTALK_URL = 'https://login.dingtalk.com/oauth2/challenge.htm'
    SIGNIN_URL = 'https://skl.hdu.edu.cn/#/sign/in'
    MAX_RETRY = 3
    
    def __init__(self, username, code, headless=False, location=None):
        self.username = username
        self.code = code
        self.headless = headless
        self.location = location or self.DEFAULT_LOCATION
        self.driver = None
        self.setup_logging()
        
    def setup_logging(self):
        """配置日志"""
        Path('./log').mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=f"./log/{self.username}.log",
            filemode='a',
            level=logging.INFO,
            format='[%(levelname)s] [%(asctime)s] : %(message)s',
            encoding='UTF-8'
        )
        
    def setup_driver(self):
        """初始化浏览器驱动"""
        options = webdriver.ChromeOptions()
        options.add_argument(f"--disk-cache-dir=./cache/{self.username}.chromecache")
        options.add_argument('lang=zh_CN.UTF-8')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-web-security')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-gpu')
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_experimental_option("prefs", {"stylesheet": 2})
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        try:
            self.driver = webdriver.Chrome(options=options)
            
            # 设置地理位置
            self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": self.location[0] + random.uniform(-0.0003, 0.0003),
                "longitude": self.location[1] + random.uniform(-0.0003, 0.0003),
                "accuracy": 100
            })
            
            # 防检测
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            
            logging.info(f"浏览器驱动初始化成功")
            return True
            
        except Exception as e:
            logging.error(f"浏览器驱动初始化失败: {e}")
            return False
    
    def close_browser(self, status=0):
        if self.driver:
            try:
                self.driver.quit()
                logging.info('浏览器已关闭')
            except Exception:
                pass
        sys.exit(status)
    
    def load_cookies(self):
        """加载Cookie"""
        try:
            cookie_file = f"./cookies/{self.username}.pkl"
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            self.driver.get(self.DINGTALK_URL)
            
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            logging.info('Cookie加载成功')
            return True
            
        except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
            logging.error(f"Cookie加载失败: {e}")
            return False
    
    def login_dingtalk(self):
        for attempt in range(1, self.MAX_RETRY + 1):
            try:
                self.driver.get(self.LOGIN_URL)
                login_button = WebDriverWait(self.driver, 2.5, 0.05).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'module-confirm-button'))
                )
                login_button.click()
                logging.info('钉钉登录成功')
                return True
                
            except (NoSuchElementException, TimeoutException):
                logging.warning(f"钉钉登录失败, 尝试 {attempt}/{self.MAX_RETRY}")
                if attempt == self.MAX_RETRY:
                    logging.error(f"钉钉登录失败, Cookie可能已失效")
                    return False
                    
            except Exception as e:
                logging.error(f"钉钉登录异常: {e}")
                return False
        
        return False
    
    def wait_for_page_load(self):
        for attempt in range(1, self.MAX_RETRY + 1):
            try:
                WebDriverWait(self.driver, 2.5, 0.05).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'van-loading__spinner'))
                )
                logging.info('页面加载成功')
                return True
                
            except (NoSuchElementException, TimeoutException):
                logging.warning(f"页面加载失败, 尝试 {attempt}/{self.MAX_RETRY}")
                if attempt == self.MAX_RETRY:
                    logging.error(f"页面加载超时")
                    return False
                    
            except Exception as e:
                logging.error(f"页面加载异常: {e}")
                return False
        
        return False
    
    def load_signin_page(self):
        for attempt in range(1, self.MAX_RETRY + 1):
            try:
                self.driver.get(self.SIGNIN_URL)
                WebDriverWait(self.driver, 0.5, 0.05).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'van-number-keyboard'))
                )
                logging.info('签到页面加载成功')
                return True
                
            except (NoSuchElementException, TimeoutException):
                logging.warning(f"签到页面加载失败, 尝试 {attempt}/{self.MAX_RETRY}")
                if attempt == self.MAX_RETRY:
                    logging.error(f"签到页面加载超时")
                    return False
                    
            except Exception as e:
                logging.error(f"签到页面加载异常: {e}")
                return False
        
        return False
    
    def input_signin_code(self):
        try:
            keys = self.driver.find_elements(By.CLASS_NAME, 'van-key')
            
            # 先提取所有元素的text和引用，避免StaleElementReferenceException
            key_map = {}
            for key in keys:
                try:
                    text = key.text
                    if text.isdigit():
                        key_map[text] = key
                except Exception:
                    continue
            
            if not key_map:
                logging.error("未找到任何数字按键")
                return False
            
            for digit in str(self.code):
                if digit in key_map:
                    try:
                        key_map[digit].click()
                    except Exception as e:
                        logging.error(f"点击数字按键 {digit} 失败: {e}")
                        return False
                else:
                    logging.error(f"找不到数字按键: {digit}")
                    return False
            
            logging.info(f"签到码 {self.code} 已输入")
            return True
            
        except NoSuchElementException as e:
            logging.error(f"键盘元素未找到: {e}")
            return False
        except Exception as e:
            logging.error(f"输入签到码时发生异常: {e}")
            return False
    
    def check_signin_result(self):
        time.sleep(3)
        
        result_url = self.driver.current_url
        
        if '#/sign/in/detail' in result_url:
            logging.info(f"签到成功, 签到码: {self.code}, URL: {result_url}")
            return True
        elif '#/sign/in' in result_url:
            logging.warning(f"签到失败, 签到码: {self.code}, URL: {result_url}")
            return False
        else:
            logging.error(f"未知的结果URL: {result_url}")
            return False
    
    def run(self):
        start_time = time.time()
        
        logging.info(f"开始签到流程, 用户: {self.username}, 签到码: {self.code}")
        
        if not self.setup_driver():
            return 1
        
        if not self.load_cookies():
            self.close_browser(1)
        
        if not self.login_dingtalk():
            self.close_browser(1)
        
        if not self.wait_for_page_load():
            self.close_browser(1)
        
        if not self.load_signin_page():
            self.close_browser(1)
        
        if not self.input_signin_code():
            self.close_browser(1)
        
        success = self.check_signin_result()
        
        elapsed_time = time.time() - start_time
        logging.info(f"签到流程完成, 耗时: {elapsed_time:.2f}秒, 结果: {'成功' if success else '失败'}")
        
        self.close_browser(0 if success else 1)


def main():
    parser = argparse.ArgumentParser(description='钉钉自动签到脚本')
    parser.add_argument('username', type=str, help='用户名')
    parser.add_argument('code', type=str, help='签到码(4位数字)')
    parser.add_argument('--headless', action='store_true', help='使用无头模式(不显示浏览器窗口)')
    parser.add_argument('--latitude', type=float, help='纬度(默认: 杭电图书馆)')
    parser.add_argument('--longitude', type=float, help='经度(默认: 杭电图书馆)')
    
    args = parser.parse_args()
    
    # 验证签到码
    if not args.code.isdigit() or len(args.code) != 4:
        print('[ERROR] 签到码必须是4位数字')
        sys.exit(1)
    
    # 设置位置
    location = None
    if args.latitude and args.longitude:
        location = [args.latitude, args.longitude]
    
    # 执行签到
    signin = DingtalkSignin(args.username, args.code, args.headless, location)
    return signin.run()


if __name__ == '__main__':
    sys.exit(main() or 0)