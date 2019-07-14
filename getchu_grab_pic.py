'''
负责读取记录，然后下载图像
'''

import requests
from requests.adapters import HTTPAdapter
import os
import json
import time
import queue
from threading import Thread


dataset_root = 'dataset'

company_json = 'id2name.json'
product_list_json = 'id2name.json'
product_json = 'data.json'


# -----------------------------------------------------------
# 参数区
# 设定是否无视完成标志，一般不需要设定True
ignore_complete_mark = False
# 设定多少个线程一起工作
# 设定为0代表不使用多线程
n_thread = 4
# 发起下一次请求的间隔
req_interval = 0.5
# 重试次数
retries = 20
# 超时
timeout = 10
# 是否使用代理，中国境内必须使用
use_proxy = True
# 代理地址, 神奇啊，socks5协议居然可以直接用http协议连上
proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080'
}
# -----------------------------------------------------------


if not use_proxy:
    proxies = {}
# 增加标志，可以进入某些页面
cookies = {'getchu_adalt_flag': 'getchu.com'}
# 保持默认即可
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
           'Accept-Encoding': 'gzip, deflate',
           'Cookie': 'getchu_adalt_flag=getchu.com;',
           'Connection': 'keep-alive'}


def download(link):
    '''
    下载内容，遇到错误状态码为500时自动重试下载，其他错误状态码则退出
    :param link:
    :return:
    '''
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))

    for _ in range(retries):
        try:
            r = s.get(link, timeout=timeout, headers=headers, cookies=cookies, proxies=proxies, verify=False)
            time.sleep(req_interval)
        except requests.Timeout:
            continue
        if r.status_code == 200:
            return r.status_code, r.content
        elif r.status_code == 500:
            print('Download failure status_code {}, will be retry.'.format(r.status_code))
            continue
        else:
            # 如果状态码不是 200 或 500，则立即退出
            print('Download failure status_code {}.'.format(r.status_code))
            break
    try:
        return r.status_code, None
    except:
        return None, None


def get_product_pic(dataset_root, company_id, product_id, data: dict):
    '''
    抓取产品的图像
    :param dataset_root: 数据库根目录
    :param company_id: 公司id
    :param product_id: 产品id
    :param data: 数据，就是 data.json 字典
    :return:
    '''
    complete_mark = os.path.join(dataset_root, company_id, product_id, '.complete_pic')
    # 检查完成标志
    if not os.path.exists(complete_mark) or ignore_complete_mark:
        if os.path.exists(complete_mark):
            os.remove(complete_mark)
        # 封面图下载
        cover_pic_link = data["product"]["cover_pic_link"]
        cover_pic_name = data["product"]["cover_pic_name"]
        # 可能没有封面图
        if cover_pic_link is not None:
            cover_pic_path = os.path.join(dataset_root, company_id, product_id, cover_pic_name)
            code, pic_data = download(cover_pic_link)

            # 加入特例，有的游戏有封面大图链接，然而打开却是404，此时，尝试获取小图
            # 例如 http://www.getchu.com/soft.phtml?id=1275
            if code == 404:
                print('Found cover_pic_link 404, try to download small version pic.', code)
                pos = cover_pic_link.rfind('.')
                link_head = cover_pic_link[:pos]
                link_end = cover_pic_link[pos:]
                new_cover_pic_link = link_head + '_s' + link_end
                code, pic_data = download(new_cover_pic_link)

            # 没能获取封面图时，直接退出
            if pic_data is None:
                print('Download cover_pic_link failure', cover_pic_link)
                return False
            open(cover_pic_path, 'wb').write(pic_data)

        # 角色图下载
        chara_list = data['chara']
        for chara_data in chara_list.values():
            chara_main_pic_name = chara_data['chara_main_pic_name']
            chara_main_pic_link = chara_data['chara_main_pic_link']

            # 下载角色主图，可能会没有
            if chara_main_pic_link is not None:
                chara_main_pic_path = os.path.join(dataset_root, company_id, product_id, chara_main_pic_name)
                code, pic = download(chara_main_pic_link)
                if pic is None:
                    print('Download chara_main_pic_link failure', chara_main_pic_link, code)
                    return False
                else:
                    open(chara_main_pic_path, 'wb').write(pic)

            # 下载角色全身图，可能会没有
            chara_full_pic_name = chara_data['chara_full_pic_name']
            chara_full_pic_link = chara_data['chara_full_pic_link']

            if chara_full_pic_link is not None:
                chara_full_pic_path = os.path.join(dataset_root, company_id, product_id, chara_full_pic_name)
                code, pic = download(chara_full_pic_link)
                if pic is None:
                    print('Download chara_full_pic_link failure', chara_full_pic_link, code)
                    return False
                else:
                    open(chara_full_pic_path, 'wb').write(pic)
        open(complete_mark, 'wb')
    else:
        print('Found complete mark.')
    return True


n_failure = 0

worker_no_more = False
command_quene = queue.Queue(maxsize=n_thread)


def worker_run():
    '''
    工作线程
    :return:
    '''
    global n_failure
    while True:
        try:
            new_command = command_quene.get(block=True, timeout=2)
            b = get_product_pic(*new_command)
            if not b:
                n_failure += 1

        except queue.Empty:
            if worker_no_more and command_quene.empty():
                break


if __name__ == '__main__':

    worker_threads = []
    for i in range(n_thread):
        t = Thread(target=worker_run)
        t.start()
        worker_threads.append(t)
        # 使进程启动时间错开一定间隔
        time.sleep(0.1)

    company_id_list = json.load(open(os.path.join(dataset_root, company_json), 'r', encoding='utf8')).keys()
    print(company_id_list)

    n_company = len(company_id_list)

    for n_id, company_id in enumerate(company_id_list):

        product_id_list = json.load(open(os.path.join(dataset_root, company_id, product_list_json), 'r', encoding='utf8')).keys()

        n_product = len(product_id_list)

        for n_id2, product_id in enumerate(product_id_list):
            print('({}/{}) ({}/{}) Getting company_id/product_id: ({}/{})'.format(n_id+1, n_company, n_id2+1, n_product, company_id, product_id))

            data_path = os.path.join(dataset_root, company_id, product_id, product_json)
            if not os.path.isfile(data_path):
                continue
            data = json.load(open(data_path, 'r', encoding='utf8'))

            if n_thread == 0:
                b = get_product_pic(dataset_root, company_id, product_id, data)
                if not b:
                    n_failure += 1
            else:
                command_quene.put([dataset_root, company_id, product_id, data], block=True)

    if n_thread > 0:
        print('Waiting worker quit')
        worker_no_more = True
        for t in worker_threads:
            t.join()

    if n_failure > 0:
        print('Failure download count {}'.format(n_failure))
    else:
        print('Success')
