from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
import time
import pickle
import random
import sys
import logging
import re
import threading
####################################
username = sys.argv[1]
index = int(sys.argv[2])
Location = [30.3203028, 120.3372421] # 杭电图书馆的定位
####################################
start_time = time.time()
logging.basicConfig(filename=f"./log/{username}.log", filemode='w', level=logging.INFO, format='[%(levelname)s] [%(asctime)s] : %(message)s', encoding='UTF-8')
# 正确的关闭浏览器和退出
def closebrowser(driver,status):
    driver.quit()
    logging.info('成功关闭webdriver')
    sys.exit(status)
# 加载防检测环境
options = webdriver.ChromeOptions()
options.add_argument(f"--disk-cache-dir=./cache/{username}.chromecache")
options.add_argument('lang=zh_CN.UTF-8')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')
options.add_argument('--disable-popup-blocking')
options.add_argument('--disable-web-security')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--disable-gpu')
options.add_experimental_option("prefs", {"stylesheet": 2})
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(options=options)
driver.set_window_rect(x=500 * index, y=0, width=480, height=720)
driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
    # 随机经纬度防止位置过于重合 (大约30米的变化)
    "latitude": Location[0] + random.uniform(-0.0003, 0.0003),
    "longitude": Location[1] + random.uniform(-0.0003, 0.0003),
    "accuracy": 100
})
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    # 防止检测webdriver
    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
})
logging.info(f"加载ChromeDriver成功,Index为{index}")
# 加载网站并导入cookie
driver.get('https://login.dingtalk.com/oauth2/challenge.htm')
try:
    cookies = pickle.load(open(f"./cookies/{username}.pkl", "rb"))
except (FileNotFoundError, EOFError, pickle.UnpicklingError):
    logging.error(f"cookie未找到或已经损坏")
    closebrowser(driver, 1)
logging.info('导入cookie成功')
for cookie in cookies:
    driver.add_cookie(cookie)
# 从杭电api获取转跳钉钉登录地址,默认为3次失败
attempts = 0
while True:
    try:
        driver.get('https://skl.hdu.edu.cn/api/login/dingtalk/auth?index=&code=0&authCode=0&state=0')
        login_button = WebDriverWait(driver, 2.50, 0.05).until(EC.element_to_be_clickable((By.CLASS_NAME, 'module-confirm-button')))
        break
    except (NoSuchElementException, TimeoutException):
        attempts += 1
        logging.warning(f"登录钉钉失败,第{attempts}次尝试")
        if attempts == 3:
            logging.error(f"登录钉钉失败过多,可能是cookie失效了")
            closebrowser(driver, 1)
    except Exception as e:
        logging.error(f"发生错误,请检查: {e}")
        closebrowser(driver, 1)
login_button.click()
logging.info('从钉钉登录成功')
# 尝试等待加载杭电skl.hduhelp.com
attempts = 0
while True:
    try:
        WebDriverWait(driver, 2.50, 0.05).until(EC.presence_of_element_located((By.CLASS_NAME, 'van-loading__spinner')))
        break
    except (NoSuchElementException, TimeoutException):
        attempts += 1
        logging.warning(f"加载skl.hduhelp.com时失败,第{attempts}次尝试")
        if attempts == 3:
            logging.error(f"在加载skl.hduhelp.com多次失败,可能是杭电服务器炸了")
            closebrowser(driver, 1)
    except Exception as e:
        logging.error(f"发生错误,请检查: {e}")
        closebrowser(driver, 1)
# 尝试等待加载https://skl.hduhelp.com/#/sign/in
attempts = 0
while True:
    try:
        driver.get('https://skl.hduhelp.com/#/sign/in')
        WebDriverWait(driver, 0.50, 0.05).until(EC.presence_of_element_located((By.CLASS_NAME, 'van-number-keyboard')))
        break
    except (NoSuchElementException, TimeoutException):
        attempts += 1
        logging.warning(f"加载签到界面时失败,第{attempts}次尝试")
        if attempts == 3:
            logging.error(f"在加载签到界面多次失败,可能是杭电服务器炸了")
            closebrowser(driver, 1)
    except Exception as e:
        logging.error(f"发生错误,请检查: {e}")
        closebrowser(driver, 1)
logging.info('加载签到界面成功')
# 从页面中查找需要的数字按钮并按下
try:
    keys = driver.find_elements(By.CLASS_NAME, 'van-key')
    key_map = {key.text: key for key in keys if key.text.isdigit()}
except NoSuchElementException:
    logging.error(f"解析键盘失败")
    closebrowser(driver, 1)
# 按下签到码
def inputcode(code):
    code_str = str(code)
    for number in code_str:
        if number in key_map:
            key_map[number].click()
# 检测签到结果
def checkifsuccess(code):
    result = driver.current_url
    if result.startswith('https://skl.hduhelp.com/#/sign/in/detail'):
        logging.info(f"使用签到码{code}签到成功, 地址为: {result}")
        driver.get_screenshot_as_file(f"./results/{username}.png")
        time.sleep(3)
        driver.get('https://skl.hduhelp.com/#/sign/in')
    elif result == 'https://skl.hduhelp.com/#/sign/in':
        logging.warning(f"使用签到码{code}签到失败, 地址为:{result}")
    else:
        logging.error(f"未知的错误地址: {result}")
# 与main.py交互,代表webdriver加载完成
usedtime = time.time() - start_time
logging.info(f"全部加载成功, 耗时{usedtime:.2f}秒")
print(f"200 OK")
# 等待交互
while True:
    code = input() 
    if re.match(r'^\d{4}$', code):
        inputcode(code)
        time.sleep(3)
        checkifsuccess(code)
        continue
    elif code == 'close':
        break
    else:
        logging.warning(f"输入的{code}不是四位签到码")
closebrowser(driver, 0)
