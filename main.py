import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
from captcha_ocr import get_ocr_res

# 设置基本的URL和数据
RandCodeUrl = "http://zhjw.qfnu.edu.cn/verifycode.servlet"  # 验证码请求URL
loginUrl = "http://zhjw.qfnu.edu.cn/Logon.do?method=logonLdap"  # 登录请求URL
dataStrUrl = (
    "http://zhjw.qfnu.edu.cn/Logon.do?method=logon&flag=sess"  # 初始数据请求URL
)

# 用户输入学号和密码
userAccount = "2022416246"
userPassword = "qfnuWS0814@"

# 创建session对象，保持会话
session = requests.session()

# 获取初始的网页数据和cookies
response = session.get(dataStrUrl, timeout=1000)
cookies = session.cookies.get_dict()  # 保存当前cookies
dataStr = response.text  # 获取网页内容，用来提取后续需要的数据

# 获取验证码并显示
response = session.get(RandCodeUrl, cookies=cookies)
image = Image.open(BytesIO(response.content))
image.show()  # 显示验证码图片
random_code = get_ocr_res(image)  # 识别验证码
print(random_code)  # 打印验证码

# 提取数据并生成encoded字符串
res = dataStr.split("#")
code = res[0]
sxh = res[1]
data = userAccount + "%%%" + userPassword
encoded = ""

# 计算并生成encoded字符串
b = 0
length = len(code)
for a in range(length):
    if a < 20:
        encoded += data[a]
        for c in range(int(sxh[a])):  # 根据sxh的数字对code进��重复操作
            encoded += code[b]
            b += 1
    else:
        encoded += data[a:]
        break

# 登录请求数据
data = {
    "userAccount": userAccount,
    "userPassword": userPassword,
    "RANDOMCODE": random_code,  # 用户输入的验证码
    "encoded": encoded,  # 生成的encoded字符串
}

# 发送POST请求登录
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "Origin": "http://zhjw.qfnu.edu.cn",
    "Referer": "http://zhjw.qfnu.edu.cn/",
    "Upgrade-Insecure-Requests": "1",
}

# 发送登录请求
response = session.post(
    loginUrl, headers=headers, data=data, cookies=cookies, timeout=1000
)

# 输出响应结果
print(response.text)  # 查看响应，确认是否登录成功
# 保存到文件
with open("response.html", "w", encoding="utf-8") as f:
    f.write(response.text)

# 确认登录成功后，获取指定页面内容
target_url = "http://zhjw.qfnu.edu.cn/jsxsd/xsks/xsksap_list?xqlbmc=&sxxnxq=&dqxnxq=&ckbz=&xnxqid=2024-2025-1&xqlb=#/"
response = session.get(target_url, cookies=cookies, headers=headers, timeout=1000)

# 输出获取的页面内容
print(response.text)  # 打印页面内容以确认获取成功
# 保存到文件
with open("target_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

# 读取HTML文件内容
with open("target_page.html", "r", encoding="utf-8") as file:
    html_content = file.read()


# 解析HTML
soup = BeautifulSoup(html_content, "html.parser")

# 创建一个日历对象
calendar = Calendar()

# 遍历表格行，提取信息
for row in soup.select("table#dataList tr")[1:]:  # 跳过表头
    cells = row.find_all("td")
    if len(cells) < 7:
        continue

    # 提取信息
    exam_number = cells[0].text.strip()
    campus = cells[1].text.strip()
    session = cells[2].text.strip()
    course_code = cells[3].text.strip()
    course_name = cells[4].text.strip()
    teacher = cells[5].text.strip()
    exam_time = cells[6].text.strip()
    location = cells[7].text.strip()

    # 解析考试时间
    date_str, time_range = exam_time.split(" ")
    start_time, end_time = time_range.split("~")
    start_datetime = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")

    # 创建一个事件
    event = Event()
    event.name = f"{course_name} - {teacher}"
    event.begin = start_datetime
    event.end = end_datetime
    event.location = location
    event.description = f"课程编号: {course_code}, 校区: {campus}, 场次: {session}"

    # 添加事件到日历
    calendar.events.add(event)

# 将日历保存到文件
with open("exam_schedule.ics", "w", encoding="utf-8") as f:
    f.write(calendar.serialize())
