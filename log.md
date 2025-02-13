
# 分析接口
1. 返回图片数据接口bg和patch, challenge
https://iv.jd.com/slide/g.html

2. 通过两张图计算滑块距离
原图宽度360
渲染宽度281
distance / 360 * 281

3. 滑块通过会返回一个validate 
https://iv.jd.com/slide/g.html
参数：
d: 轨迹坐标["x", "y", ts] + js算法getCoordinates
c: challenge
e: eid
j: jsToken  
s: sessionId // e, j, s自动化补环境可提取
o: encodeURIComponent("15579327821") //手机号

4. 商品信息请求成功需要登录状态的cookie: flash
"https://api.m.jd.com/api"

# 坐标规律分析，协议请求

1. 缓动函数模拟，失败
2. 截取成功坐标的正常滑动阶段和晃动阶段（晃动坐标从0开始）
    并替换时间戳前8位，进行拼接，只能成功一次

# 自动化登录读取cookie
1. opencv识别滑动距离
2. 用加速最快的缓动函数模拟，距离固定，控制滑动步数
    关键点：加速快，速度不过慢，微调对准阶段自然
3. 取消webdriver绕过检测的options可以直接登录，猜测对webdriver有反爬检测
4. 登录成功后读取flash请求接口，去重，储存