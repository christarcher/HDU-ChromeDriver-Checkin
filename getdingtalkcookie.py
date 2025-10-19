from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import pickle
import time
import sys
import os
from pathlib import Path
from datetime import datetime


LOGIN_URL = 'https://skl.hdu.edu.cn/api/login/dingtalk/auth?index=&code=0&authCode=0&state=0'
DINGTALK_DOMAIN = 'login.dingtalk.com'
COOKIES_DIR = './cookies'
REDIRECT_WAIT_TIME = 3


class CookieManager:
    def __init__(self):
        self.driver = None
        self.username = None
        
    def setup_driver(self):
        try:
            chrome_options = Options()
            self.driver = webdriver.Chrome(options=chrome_options)
            print('[INFO] 浏览器启动成功')
            return True
        except WebDriverException as e:
            print(f'[ERROR] 浏览器启动失败: {e}')
            return False
    
    def close_browser(self, status=0):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        sys.exit(status)
    
    def get_username(self):
        while True:
            username = input('请输入用户名(学号或者其他ID): ').strip()
            if username:
                if all(c.isalnum() or c in ('-', '_') for c in username):
                    self.username = username
                    return username
                else:
                    print('[ERROR] 用户名只能包含字母、数字、下划线和横线')
            else:
                print('[ERROR] 用户名不能为空')
    
    def open_login_page(self):
        try:
            print('[INFO] 正在打开登录页面...')
            self.driver.get(LOGIN_URL)
            time.sleep(2)
            
            current_url = self.driver.current_url
            print(f'[INFO] 当前页面: {current_url}')
            
            if DINGTALK_DOMAIN in current_url:
                print('[INFO] 已跳转到钉钉登录页面')
            
            return True
                
        except Exception as e:
            print(f'[ERROR] 无法打开登录页面: {e}')
            return False
    
    def wait_for_qr_scan(self):
        print('[INFO] 请使用钉钉APP扫描二维码登录')
        
        while True:
            response = input('\n输入 yes 继续 / retry 重新加载 / no 取消: ').strip().lower()
            
            if response == 'yes':
                return True
            elif response == 'retry':
                print('[INFO] 重新加载登录页面...')
                if self.open_login_page():
                    continue
                else:
                    return False
            elif response == 'no':
                print('[INFO] 操作已取消')
                return False
            else:
                print('[ERROR] 无效输入')
    
    def redirect_to_dingtalk(self):
        try:
            print('[INFO] 正在跳转到钉钉域名...')
            
            self.driver.get(LOGIN_URL)
            time.sleep(REDIRECT_WAIT_TIME)
            
            current_url = self.driver.current_url
            print(f'[INFO] 当前页面: {current_url}')
            
            if DINGTALK_DOMAIN in current_url:
                print('[INFO] 成功跳转到钉钉域名')
                return True
            else:
                print(f'[WARNING] 当前不在钉钉域名下: {current_url}')
                response = input('是否继续获取Cookie? (yes/no): ').strip().lower()
                return response == 'yes'
                
        except Exception as e:
            print(f'[ERROR] 跳转失败: {e}')
            return False
    
    def check_cookie_expiry(self, cookies):
        print('\n[INFO] Cookie过期时间信息:')
        print('-' * 60)
        
        has_expiry = False
        for cookie in cookies:
            name = cookie.get('name', 'unknown')
            
            if 'expiry' in cookie:
                has_expiry = True
                expiry_timestamp = cookie['expiry']
                expiry_date = datetime.fromtimestamp(expiry_timestamp)
                
                now = datetime.now()
                time_remaining = expiry_date - now
                days_remaining = time_remaining.days
                
                print(f'Cookie: {name}')
                print(f'  过期时间: {expiry_date.strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'  剩余时间: {days_remaining} 天')
                
                if days_remaining < 0:
                    print(f'  状态: 已过期')
                elif days_remaining < 7:
                    print(f'  状态: 即将过期')
                else:
                    print(f'  状态: 正常')
                print()
            else:
                pass
        
        if not has_expiry:
            print('[INFO] 所有Cookie均为会话Cookie (无固定过期时间)')
        
        print('-' * 60)
    
    def save_cookies(self):
        try:
            Path(COOKIES_DIR).mkdir(parents=True, exist_ok=True)
            
            cookies = self.driver.get_cookies()
            
            if not cookies:
                print('[ERROR] 未检测到任何Cookie')
                return False
            
            print(f'\n[INFO] 获取到 {len(cookies)} 个Cookie')
            print(f'[INFO] 当前域名: {self.driver.current_url}')
            
            self.check_cookie_expiry(cookies)

            cookie_file = os.path.join(COOKIES_DIR, f'{self.username}.pkl')
            
            with open(cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            
            print(f'\n[INFO] Cookie已保存到: {cookie_file}')
            
            if os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 0:
                print('[INFO] Cookie文件验证通过')
                return True
            else:
                print('[ERROR] Cookie文件验证失败')
                return False
                
        except Exception as e:
            print(f'[ERROR] 保存Cookie失败: {e}')
            return False
    
    def run(self):
        try:
            print('[INFO] 钉钉Cookie获取工具')
            print('-' * 60)
            
            self.get_username()
            
            if not self.setup_driver():
                return 1
            
            if not self.open_login_page():
                self.close_browser(1)
            
            if not self.wait_for_qr_scan():
                self.close_browser(1)
            
            if not self.redirect_to_dingtalk():
                print('[ERROR] 无法跳转到钉钉域名')
                self.close_browser(1)
            
            if self.save_cookies():
                print('\n[INFO] 操作完成')
                input('按回车键退出...')
                self.close_browser(0)
            else:
                print('[ERROR] Cookie保存失败')
                retry = input('是否重试? (yes/no): ').strip().lower()
                if retry == 'yes':
                    self.close_browser(0)
                    return self.run()
                else:
                    self.close_browser(1)
                
        except KeyboardInterrupt:
            print('\n[INFO] 用户中断操作')
            self.close_browser(1)
        except Exception as e:
            print(f'\n[ERROR] 程序运行出错: {e}')
            import traceback
            traceback.print_exc()
            self.close_browser(1)


def main():
    manager = CookieManager()
    return manager.run()


if __name__ == '__main__':
    sys.exit(main() or 0)