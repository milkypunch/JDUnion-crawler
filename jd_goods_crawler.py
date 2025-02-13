import requests
import cv2
import numpy as np
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import hashlib
import pymongo

def visit_page(driver):

    driver.get("https://union.jd.com/proManager/index")

    time.sleep(3)

    login_link = driver.find_element(By.XPATH, '//label[@class="el-radio-button"][5]')
    ActionChains(driver).move_to_element(login_link).perform()
    time.sleep(1)  
    login_link.click()

    time.sleep(3)

def input_phone_and_click_button(driver):

    time.sleep(3)
    
    iframe = driver.find_element(By.XPATH, '//*[@id="indexIframe"]')
    driver.switch_to.frame(iframe)
   
    phone_input = driver.find_element(By.XPATH, '/html/body/form/div/div/div/div[1]/div/input')
    ActionChains(driver).move_to_element(phone_input).perform()
    time.sleep(1)  
    phone_input.click()

    phone_number = "15579327821"
    for digit in phone_number:
        phone_input.send_keys(digit)
        time.sleep(random.uniform(0.2, 0.5))  

    pwd_input = driver.find_element(By.XPATH, '/html/body/form/div/div/div/div[2]/div/input')
    ActionChains(driver).move_to_element(pwd_input).perform()
    time.sleep(1)  
    pwd_input.click()

    pwd = "LOSEr889"
    for char in pwd:
        pwd_input.send_keys(char)
        time.sleep(random.uniform(0.2, 0.5)) 

    send_code_button = driver.find_element(By.XPATH, '/html/body/form/div/div/div/div[4]/input')
    ActionChains(driver).move_to_element(send_code_button).perform()
    time.sleep(1)  
    send_code_button.click()

    time.sleep(3)

def save_image_from_src(src, filename):
    
    if src.startswith('data:image/png;base64,'):

        base64_data = src.split(',')[1]  
        image_data = base64.b64decode(base64_data)  
    else:
        
        response = requests.get(src)
        if response.status_code == 200:
            image_data = response.content  
        else:
            raise Exception(f"Failed to retrieve image from URL: {src}")

    
    with open(filename, 'wb') as file:
        file.write(image_data)

    print(f"Image saved as: {filename}")

def fetch_image(driver, bg_path, patch_path):
    bg_elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="JDJRV-bigimg"]/img'))
            )
    bg_url =  bg_elem.get_attribute('src')
    patch_elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="JDJRV-smallimg"]/img'))
            )
    patch_url =  patch_elem.get_attribute('src')
    save_image_from_src(bg_url, bg_path)
    save_image_from_src(patch_url, patch_path)

def get_dis(bg, patch):
    bg = cv2.imread(bg)
    patch = cv2.imread(patch)
    res = cv2.matchTemplate(bg, patch, cv2.TM_CCORR_NORMED)
    value = cv2.minMaxLoc(res)[2][0]  
      
    dis = value / 360 * 281
    return dis

def easeInOutQuint(t):
    if t < 0.5:
        return 16 * t * t * t * t * t
    else:
        t -= 1
        return 1 + 16 * t * t * t * t * t
        
def get_tracks_by_time(distance, duration, ease_func):
    tracks = []
    offsets = []
    start_time = time.time()
    end_time = start_time + duration
    current_time = start_time
    

    while current_time < end_time:
        elapsed_time = current_time - start_time
        ease = globals()[ease_func]
        offset = ease(elapsed_time / duration) * distance

        if offsets:
            tracks.append(offset - offsets[-1])
        else:
            tracks.append(offset)
        offsets.append(offset)
        current_time = time.time()
        time.sleep(0.02)  
        
    tracks.append(distance - sum(tracks))
    return tracks

def move_slider(slider, puzzle_element, target_position, driver):
    def get_element_position(element):
        return element.location['x'] - 30

    current_position = get_element_position(puzzle_element)
    distance = target_position - current_position

    action = ActionChains(driver)
    action.click_and_hold(slider).perform()

    duration = 0.1
    tracks = get_tracks_by_time(distance, duration, 'easeInOutQuint')
    print(f'steps/distance: ', len(tracks) / distance)

    for track in tracks:
        action.move_by_offset(track, 0).perform()
        current_position = get_element_position(puzzle_element)
        print(f"Current position: {current_position}, target: {target_position}, timestamp: {time.time() * 1000}")
  
    distance = target_position - current_position
    print("最后一步距离：", distance)
    action.move_by_offset(distance, 0).perform()
    action.pause(0.2).release(slider).perform()
    time.sleep(3)

def login_attempt(driver):

    puzzle_element = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="JDJRV-smallimg"]/img'))
                )
    
    bg_path = '/Users/milkypunch/Desktop/bg.png'
    patch_path = '/Users/milkypunch/Desktop/patch.png'
    fetch_image(driver, bg_path, patch_path)

    target_position = get_dis(bg_path,patch_path)
    
    slider = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH,'//div[@class="JDJRV-slide-inner JDJRV-slide-btn"]'))
    )
    move_slider(slider, puzzle_element, target_position, driver) 

def get_cookie(driver):
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        login_attempt(driver)
        time.sleep(8)
        url = driver.current_url
        elements = driver.find_elements(By.XPATH, '//div[@class="el-menu-logo"]')
        if url == 'https://union.jd.com/proManager/index?pageNo=1' or elements:   
            cookies = driver.get_cookies()
            flash = next((cookie['value'] for cookie in cookies if cookie['name'] == 'flash'), None)
            return flash

        else:
            attempts += 1
    if attempts == max_attempts:
        print("达到最大尝试次数，滑块失败")

def fetch_data(flash, page):
    JD_cookie = {
        "flash": flash,
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://union.jd.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://union.jd.com/",
        "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "x-referer-page": "https://union.jd.com/proManager/index",
        "x-rp-client": "h5_1.0.0"
    }

    url = "https://api.m.jd.com/api"
    
    json_string = r'{"funName":"search","page":{"pageNo":{page},"pageSize":80},"param":{"bonusIds":null,"category1":null,"category2":null,"category3":null,"deliveryType":null,"fromCommission":null,"toCommission":null,"fromPrice":null,"toPrice":null,"hasCoupon":null,"isHot":null,"isNeedPreSale":null,"isPinGou":null,"isZY":null,"isCare":null,"lock":null,"orientationFlag":null,"sort":null,"sortName":null,"keyWord":"","searchType":"st3","keywordType":"kt0","hasSimRecommend":1,"requestScene":0,"requestExtFields":["shopInfo","orientations"],"source":20310},"clientPageId":"jingfen_pc"}'
    formatted_json_string = json_string.replace("{page}", str(page))
    params = {
        "functionId": "unionSearchGoods",
        "appid": "unionpc",
        "_": "1730010714559",
        "loginType": "3",
        "body": formatted_json_string,
    }
    response = requests.get(url, headers=headers, cookies=JD_cookie, params=params)

    goods_list = response.json()['result']['skuPage']['result']
    return goods_list

def hash_string(s: str):
    """生成字符串的哈希值"""
    return hashlib.md5(s.encode()).hexdigest()

def extract_data(goods_list):
    seen_codes = set()  
    unique_items = []  

    for item in goods_list:
        goods_id = item["skuId"]
        code_hash = hash_string(str(goods_id))  
        if code_hash not in seen_codes:  
            seen_codes.add(code_hash)  
            unique_items.append({
                "标题": item["skuName"],
                "价格/元": item["purchasePriceInfo"]["purchasePrice"],
                "店铺": item["venderName"],
                "好评数": item["goodComments"],
            })
    print(unique_items, len(unique_items), 'items')
    return unique_items

def save_goods_info(db, items):
    if items:
        db.insert_many(items)
        print('insert successfully: ', len(items), 'items')

def close(client_mongo):
    client_mongo.close()
    print("MongoDB connection closed")

def main():
    driver = webdriver.Chrome()
    driver.set_window_size(1470, 956)
    visit_page(driver)

    input_phone_and_click_button(driver)
    flash = get_cookie(driver)

    mongo_client = pymongo.MongoClient()
    collection = mongo_client['py_spider']['jd_goods_info']
# 修改了爬数据逻辑 改成while 改了数据库collection名称

    item_num = 0
    page = 1
    while item_num < 2000:
        item_list = fetch_data(flash, page)
        unique_list = extract_data(item_list)
        save_goods_info(collection, unique_list)
        
        item_num += len(unique_list)
        page += 1

        time.sleep(3)

    # for page in range(1, 27):
    #     item_list = fetch_data(flash, page)
    #     unique_list = extract_data(item_list)
    #     save_goods_info(collection, unique_list)
        
    close(mongo_client)

if __name__ == "__main__":
    main()