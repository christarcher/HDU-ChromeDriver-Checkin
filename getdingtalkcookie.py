from selenium import webdriver
import pickle
import time
import sys
driver = webdriver.Chrome()

def closebrowser(driver,status):
    driver.quit()
    sys.exit(status)
# 打开登录页面
print('用法: 程序会唤起浏览器,这个时候你就自己登录,需要输入钉钉的账号密码还有手机号')
time.sleep(1)
print('登录完成后不要关闭浏览器,否则就必须重新登录')
time.sleep(1)
print('登录完成后切到程序,在里面输入yes')
time.sleep(1)
input('是否已经了解? (按任意键继续): ')
username = input('输入用户名: ')
try:
	driver.get('https://skl.hdu.edu.cn/api/login/dingtalk/auth?index=&code=0&authCode=0&state=0')
except:
	closebrowser(driver, 1)

if (input('是否登录完成? (输入yes)') != 'yes'):
	print('你没登录啊?')
	input()
	closebrowser(driver, 1)

driver.get('https://skl.hdu.edu.cn/api/login/dingtalk/auth?index=&code=0&authCode=0&state=0')
time.sleep(2)
try:
	pickle.dump(driver.get_cookies(), open(f"./cookies/{username}.pkl", "wb"))
except:
	print('没有成功获取,排查错误')
	input()
	closebrowser(driver, 1)
print('cookie已经获取完成,请检查cookies.pkl文件是否有内容,没有就重来罢!')
driver.close()
closebrowser(driver, 0)