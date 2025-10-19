# HDU-ChromeDriver-Checkin

使用chromedriver实现的杭电上课啦自动签到

## 免责声明

该项目本身需要获得签到码, 即该项目只是模拟了一个 `打开钉钉->认证->打开上课啦->输入签到码` 这一流程

所以实际上是需要去上课的, 只是说提供了一个简单的接口, 可以更方便更自动化的签到(例如你不想在手机上安装钉钉等国产软件). 该项目不能也不会用于翘课.

本人也已经没什么课程了, 这个项目是一年半之前写的, 不会考虑再维护

## 使用方法

运行getdingtalkcookie.py获取cookie，按照提示进行即可

再编辑main.py，修改里面的usernames列表，把已有的用户添加进去

保存后运行main.py，访问
http://127.0.0.1:5000/hducheckckin/preload
来预加载webdriver

再签到
http://127.0.0.1:5000/hducheckckin/checkin?code={}

要关闭程序，只需要访问
http://127.0.0.1:5000/hducheckckin/checkin?code=close

目前这样写是为了方便远程对接qq机器人，机器人与这个程序可以部署在异地的服务器上
