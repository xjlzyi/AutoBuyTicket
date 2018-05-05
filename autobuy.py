# -*- encoding: utf-8 -*-
import re
import ssl
import urllib.parse
import urllib.request
import http.cookiejar
import datetime
import time
import json
from PIL import Image, ImageFile

stations = {"上海":"SHH", "杭州":"HZH", "宁波":"NGH","北京":"BJP","南京":"NJH"}
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
user_name = input("请输入用户名：")
pass_word = input("请输入密码：")

from_name = ""
to_name = ""
purpose_code = ""
query_date = ""

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

ImageFile.LOAD_TRUNCATED_IMAGES = True

class UserInfo(object):
    def __init__(self):
        self.all_name = []
        self.all_id = []
        self.all_mobile = []
        self.all_country = []
        

def login():
    #建立cookie处理
    cjar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cjar))
    urllib.request.install_opener(opener)
    #自动登录
    login_url = "https://kyfw.12306.cn/otn/login/init"
    req_data = get_request_data(login_url)
    print("login: " + req_data)

def parse_yzm_pos():
    yzm_url = "https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand"
    while True:
        urllib.request.urlretrieve(yzm_url, "./12306_yzm.png")
        im = Image.open("12306_yzm.png")
        im.show()
        yzm_indexs = input("请输入正确的图片序号（1-8）：")
        if (yzm_indexs != "re"):
            break
    
    yzm_index = yzm_indexs.split(",")
    all_pic_pos = ""
    for index in yzm_index:
        pos = get_subimage_pos(int(index))
        for j in pos:
            all_pic_pos = all_pic_pos + str(j) + ","
    result = re.compile("(.*?).$").findall(all_pic_pos)[0]
    return result

def get_subimage_pos(index):
    assert 1 <= index <= 8
    row = (index - 1) // 4
    column = (index - 1) % 4
    x = 20 + (67 + 5) * column
    y = 41 + (67 + 5) * row
    return (x, y)

def post_yzm_data(yzm_pic_pos):
    yzm_post_url = "https://kyfw.12306.cn/passport/captcha/captcha-check"
    yzm_post_data = urllib.parse.urlencode({
        "answer":yzm_pic_pos,
        "rand":"sjrand",
        "login_site":"E",
    }).encode("utf-8")
    req_data = get_request_data(yzm_post_url, yzm_post_data)
    print("验证码结果: " + req_data)
    result = json.loads(req_data)
    if (result['result_code'] == "5"):
        post_yzm_data(parse_yzm_pos())

def post_username_data():
    login_url = "https://kyfw.12306.cn/passport/web/login"
    login_data = urllib.parse.urlencode({
        "username":user_name,
        "password":pass_word,
        "appid":"otn",
    }).encode("utf-8")
    req_data = get_request_data(login_url, login_data)
    print("user_login: " + req_data)

def post_other_login():
    login_url = "https://kyfw.12306.cn/otn/login/userLogin"
    get_request_data(login_url)

    uamtk_url = "https://kyfw.12306.cn/passport/web/auth/uamtk"
    uamtk_data = urllib.parse.urlencode({
        "appid":"otn",
    }).encode("utf-8")
    uamtk_req_data = get_request_data(uamtk_url, uamtk_data)
    pat_req='"newapptk":"(.*?)"'
    tk = re.compile(pat_req, re.S).findall(uamtk_req_data)[0]

    uamauth_url = "https://kyfw.12306.cn/otn/uamauthclient"
    uamauth_data = urllib.parse.urlencode({
        "tk": tk,
    }).encode('utf-8')
    req_data = get_request_data(uamauth_url, uamauth_data)

    print("login_result: " + req_data)

def test_user_center():
    center_url = "https://kyfw.12306.cn/otn/index/initMy12306"
    req_data = get_request_data(center_url)
    print("登录成功")

def get_request_data(url, url_data=None):
    req = urllib.request.Request(url, url_data)
    req.add_header("User-Agent", user_agent)
    req_data = urllib.request.urlopen(req).read().decode("utf-8", "ignore")
    return req_data

def start():
    init_url = "https://kyfw.12306.cn/otn/leftTicket/init"
    get_request_data(init_url)
    try:
        while True:
            global query_date, from_name, to_name, purpose_code
            from_name = input("请输入出发地：")
            from_code = stations[from_name]
            to_name = input("请输入目的地：")
            to_code = stations[to_name]
            show_no_ticket = "Y"#input(" 显示全部可预订车次（Y：是 N：否）")
            query_date = input("请输入要查询的日期，如2017-03-05：")
            purpose_code = "ADULT"
            train_dic = query_ticket(from_code, to_code, show_no_ticket)
            next_step = input("请选择下一步操作（0：退出 1：重新查询 2：购票）：")
            if next_step == '0':
                exit(1)
            elif next_step == '1':
                continue
            else:
                buy_ticket(train_dic)
                break
    except Exception as err:
        raise err

def query_ticket(from_code, to_code, show_no_ticket):
    while True:
        #开始查询
        query_url = "https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=" + query_date + \
                    "&leftTicketDTO.from_station=" + from_code + \
                    "&leftTicketDTO.to_station=" + to_code + \
                    "&purpose_codes=" + purpose_code
        context = ssl._create_unverified_context()
        url_data = urllib.request.urlopen(query_url).read().decode("utf-8", "ignore")
        patrst = '"result":\[(.*?)\]'
        rst = re.compile(patrst).findall(url_data)[0]
        all_trains = rst.split(",")
        checimap_pat = '"map":({.*?})'
        checimap = eval(re.compile(checimap_pat).findall(url_data)[0])

        train_dic = {} #存储所有班次信息
        #显示查询结果
        print("车次\t出发站名\t到达站名\t出发时间\t到达时间\t商务座\t一等座\t二等座\t硬座\t无座")
        has_ticket = False
        for i in range(0, len(all_trains)):
            train_data = all_trains[i].replace("\"", "").split("|") #这里需要把双引号替换掉，不然下面提交订单的时候出错
            if show_no_ticket == "Y" and train_data[11] == "N":
                continue
            train_code = train_data[3]
            from_code = train_data[6]
            from_name = checimap[from_code]
            to_code = train_data[7]
            to_name = checimap[to_code]
            stime = train_data[8]
            atime = train_data[9]
            tdz = train_data[32]#特等座
            ydz = train_data[31]#一等
            edz = train_data[30]#二等
            #rw = train_data[23]#软卧
            #yw = train_data[28]#硬卧
            yz = train_data[29]#硬座
            wz = train_data[26]#无座
            print(train_code + "\t" + from_name + "\t\t" + to_name + "\t\t" + stime + "\t\t" + atime + "\t\t" + str(tdz) + "\t" + str(ydz) + "\t" + str(edz) + "\t" + str(yz) + "\t" + str(wz))
            train_dic[train_code] = train_data[0]
            has_ticket = True
        if not has_ticket:
            print("暂时无票，继续查询")
            continue
        else:
            return train_dic

def buy_ticket(all_train_data):
    train_code = input("请输入需要预定的车次：")
    if train_code not in all_train_data:
        print("输入的车次不存在，请确认后重新输入")
        buy_ticket(train_data)
    else:
        #确认用户状态
        check_url = "https://kyfw.12306.cn/otn/login/checkUser"
        check_data = urllib.parse.urlencode({
            "_json_att":""
        }).encode('utf-8')
        get_request_data(check_url, check_data)
        #自动得到当前时间并转为年-月-格式
        back_date = datetime.datetime.now().strftime("%Y-%m-%d")
        #进行“预订”提交
        secret_str = all_train_data[train_code]
        submit_url = "https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest"
        submit_data = urllib.parse.urlencode({
            "secretStr": secret_str,
            "train_date": query_date,
            "back_train_date": back_date,
            "tour_flag": "dc",
            "purpose_codes": purpose_code,
            "query_from_station_name": from_name,
            "query_to_station_name": to_name,
        }).replace("%25", "%").encode("utf-8")
        submit_req_data = get_request_data(submit_url, submit_data)
        result = json.loads(submit_req_data)
        if not result["status"]:
            print(result["messages"])
            return
        #订票获取Token、leftTicketStr、key_check_isChange、train_location
        comfirm_url = "https://kyfw.12306.cn/otn/confirmPassenger/initDc"
        comfirm_data = urllib.parse.urlencode({
            "_json_att:": ""
        }).encode('utf-8')
        comfirm_req_data = get_request_data(comfirm_url, comfirm_data)
        #获取train_no、leftTicketStr、fromStationTelecode、toStationTelecode、train_location
        train_no_pat="'train_no':'(.*?)'"
        leftTicketStr_pat="'leftTicketStr':'(.*?)'"
        from_station_telecode_pat="from_station_telecode':'(.*?)'"
        to_station_telecode_pat="'to_station_telecode':'(.*?)'"
        train_location_pat="'train_location':'(.*?)'"
        pattoken="var globalRepeatSubmitToken.*?'(.*?)'"
        patkey="'key_check_isChange':'(.*?)'"
        pattrain_location="'tour_flag':'dc','train_location':'(.*?)'"
        train_no_all = re.compile(train_no_pat).findall(comfirm_req_data)
        ticket_data = {}
        if len(train_no_all) == 0:
            raise Exception("获取数据失败")
        else:
            ticket_data['train_no'] = train_no_all[0]
        ticket_data['leftTicketStr'] = re.compile(leftTicketStr_pat).findall(comfirm_req_data)[0]
        ticket_data['from_station_telecode'] = re.compile(from_station_telecode_pat).findall(comfirm_req_data)[0]
        ticket_data['to_station_telecode'] = re.compile(to_station_telecode_pat).findall(comfirm_req_data)[0]
        ticket_data['train_location'] = re.compile(train_location_pat).findall(comfirm_req_data)[0]
        ticket_data['token'] = re.compile(pattoken).findall(comfirm_req_data)[0]
        ticket_data['key'] = re.compile(patkey).findall(comfirm_req_data)[0]
        
        user = get_user_data(ticket_data['token'])
        comfirm_ticket(user, train_code, ticket_data)


def comfirm_ticket(user, train_code, ticket_data):
    #提交订单
    check_order_url = "https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo"
    select_user_no = 0 #选取的购票人下标
    #商务座：9，一等座：O 二等座：M, 多个乘客用 _ 分隔
    seat_type = 'M'
    passenger_ticket_str = seat_type + ",0,1,"+str(user.all_name[select_user_no])+",1,"+str(user.all_id[select_user_no])+","+str(user.all_mobile[select_user_no])+",N" 
    old_passenger_str = str(user.all_name[select_user_no])+",1,"+str(user.all_id[select_user_no])+",1_"
    check_data = urllib.parse.urlencode({
        "cancel_flag":2,
        "bed_level_order_num":"000000000000000000000000000000",
        "passengerTicketStr":passenger_ticket_str,
        "oldPassengerStr":old_passenger_str,
        "tour_flag":"dc",
        "randCode":"",
        "whatsSelect":1,
        "_json_att":"",
        "REPEAT_SUBMIT_TOKEN":ticket_data['token'],
        }).encode('utf-8')
    get_request_data(check_order_url, check_data)
    #获取队列
    get_queue_url = "https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount"
    train_date = datetime.datetime.strptime(query_date, "%Y-%m-%d").date().strftime("%a+%b+%d+%Y")
    left_ticket = ticket_data['leftTicketStr'].replace("%", "%25")
    get_queue_data = ("train_date=" + str(train_date) + "+00%3A00%3A00+GMT%2B0800&train_no=" + str(ticket_data['train_no']) +\
        "&stationTrainCode=" + train_code + "&seatType=" + seat_type + \
        "&fromStationTelecode=" + str(ticket_data['from_station_telecode']) + \
        "&toStationTelecode=" + str(ticket_data['to_station_telecode']) +\
        "&leftTicket=" + left_ticket + \
        "&purpose_codes=00&train_location=" + str(ticket_data['train_location']) + \
        "&_json_att=&REPEAT_SUBMIT_TOKEN=" + str(ticket_data['token'])).encode("utf-8")
    queue_req_data = get_request_data(get_queue_url, get_queue_data)
    #配置确认提交
    comfirm_url = "https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue"
    comfirm_data = urllib.parse.urlencode({
        "passengerTicketStr":passenger_ticket_str,
        "oldPassengerStr":old_passenger_str,
        "randCode":"",
        "purpose_codes":"00",
        "key_check_isChange":str(ticket_data['key']),
        "leftTicketStr":str(ticket_data['leftTicketStr']),
        "train_location":str(ticket_data['train_location']),
        "choose_seats":"",
        "seatDetailType":"000",
        "whatsSelect":"1",
        "roomType":"00",
        "dwAll":"N",
        "_json_att":"",
        "REPEAT_SUBMIT_TOKEN":ticket_data['token'],
    }).encode("utf-8")
    comfirm_req_data = get_request_data(comfirm_url, comfirm_data)
    start_time = time.time()
    is_timeout = False
    while True:
        #获取orderid
        now = time.time()
        if (now - start_time) // 60 > 5:
            print("获取orderid超时")
            is_timeout = True
            break
        get_order_url = "https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random=" + str(int(time.time()) * 1000) + \
            "&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN=" + str(ticket_data['token'])
        order_req_data = get_request_data(get_order_url)
        order_id_pat = '"orderId":"(.*?)"'
        order_id_all = re.compile(order_id_pat).findall(order_req_data)
        if len(order_id_all) == 0:
            print("未获取到orderid，正在进行新一次的请求。")
            continue
        else:
            order_id = order_id_all[0]
            break
    if is_timeout:
        comfirm_ticket()
        return
    #请求结果
    result_url = "https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue"
    result_data = ("orderSequence_no=" + order_id + "&_json_att=&REPEAT_SUBMIT_TOKEN=" + str(ticket_data['token'])).encode("utf-8")
    result_req_data = get_request_data(result_url, result_data)
    #支付接口页面
    pay_url = "https://kyfw.12306.cn/otn//payOrder/init"
    pay_data = ("_json_att=&REPEAT_SUBMIT_TOKEN=" + str(ticket_data['token'])).encode("utf-8")
    get_request_data(pay_url, pay_data)
    print("订单已经完成提交，可以后台进行支付了")

def get_user_data(token):
    #获取乘客信息
    user_url = "https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs"
    user_data = urllib.parse.urlencode({
        "REPEAT_SUBMIT_TOKEN": token,
    }).encode('utf-8')
    user_req_data = get_request_data(user_url, user_data)
    ##获取用户信息
    #提取姓名
    name_pat = '"passenger_name":"(.*?)"'
    #提取身份证
    id_pat = '"passenger_id_no":"(.*?)"'
    #提取手机号
    mobile_pat = '"mobile_no":"(.*?)"'
    #提取对应乘客所在的国家
    country_pat = '"country_code":"(.*?)"'
    user = UserInfo()
    user.all_name = re.compile(name_pat).findall(user_req_data)
    user.all_id = re.compile(id_pat).findall(user_req_data)
    user.all_mobile = re.compile(mobile_pat).findall(user_req_data)
    user.all_country = re.compile(country_pat).findall(user_req_data)
    #显示联系人信息
    for i in range(0, len(user.all_name)):
        print("第" + str(i + 1) + "位用户,姓名:" + str(user.all_name[i]))
    return user

if __name__ == "__main__":
    login()
    post_yzm_data(parse_yzm_pos())
    post_username_data()
    post_other_login()
    test_user_center()
    start()
