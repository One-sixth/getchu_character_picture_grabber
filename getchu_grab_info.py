'''
getchu 角色图爬虫
数据集布局：
datset/
company.html

dataset/id2name.json
dataset/list.html
dataset/company_id/

dataset/company_id/id2name.json
dataset/company_id/product_id/

dataset/company_id/product_id/角色主图.jpg
dataset/company_id/product_id/角色全身图.jpg
dataset/company_id/product_id/data.json
dataset/company_id/product_id/soft.html

*.html 为原始页面数据，同时也是缓存

data.json 内容

<chara>
----<chara_name>
--------<main_pic_name>
--------<main_pic_link>
--------<full_pic_name>
--------<full_pic_link>

# 角色介绍挖出来没啥用，去掉
#--------<chara_comment>
#--------<cv>

<product>
----<cover_pic_name>
----<cover_pic_link>
----<painter>
----<release_date>

# 脚本和音乐因为不够通用，同时也用处不大，去掉了
#----<scenario>
#----<composer>

'''

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
import re
import os
import json
import urllib.parse
import time
import queue
from threading import Thread


# -----------------------------------------------------------
# 参数区
# 这里控制缓存使用，设置为False则无视缓存，一般情况下，只需要设置 auto_use_stage1_cache 和 auto_use_stage2_cache 为 False 就行了。
auto_use_stage1_cache = True
auto_use_stage2_cache = True
auto_use_stage3_cache = True
# 发起下一次请求的间隔
req_interval = 0.3
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

# 默认即可
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
           'Accept-Encoding': 'gzip, deflate',
           'Connection': 'keep-alive'}

# 增加标志，可以进入某些页面
cookies = {'getchu_adalt_flag': 'getchu.com'}

# 这个目前仅用于填充
web_root = 'http://www.getchu.com'


def step1_get_companies_list(html):
    '''
    输入索引页，解析出作品搜索链接，公司名，和公司ID
    :param html:
    :return: [[products_search_link, company_name，company_id], ...]
    '''
    # 这里使用正则表达式直接挖出来
    companies_link_name = re.findall(r'<a href="(http://www\.getchu\.com/php/search\.phtml\?search_brand_id=\d+)">(.+?)</a>', html, re.I)
    companies_link_name_id = []
    for link, name in companies_link_name:
        # id_ = link[link.rfind('=')+1:]
        # 提取link中的id
        id_ = None
        params = urllib.parse.splitquery(link)[1].split('&')
        for p in params:
            ps = p.split('=')
            if ps[0] == 'search_brand_id':
                id_ = ps[1]
                break
        companies_link_name_id.append([link, name, id_])
    return companies_link_name_id


def step2_get_products_list(html):
    '''
    输入作品搜索页面，输出作品名，作品链接和作品ID
    :param html:
    :return: [[product_link，product_name，product_id], ...]
    '''
    # 这里使用正则表达式直接挖出来
    products_link_name = re.findall(r'<a href="\.\.(/soft\.phtml\?id=\d+)" class="blueb">(.+?)</a>', html, re.I)
    products_link_name_id = []
    for link, name in products_link_name:
        # id_ = link[link.rfind('=')+1:]
        # 提取link中的id
        id_ = None
        params = urllib.parse.splitquery(link)[1].split('&')
        for p in params:
            ps = p.split('=')
            if ps[0] == 'id':
                id_ = ps[1]
                break
        products_link_name_id.append([web_root+link, name, id_])
    return products_link_name_id


def step3_get_product_info(html):
    '''
    输出作品页面，输出一个字典
    字典包含，角色名，图像名，图像链接，作品名，原画等...
    :param html:
    :return: {'chara': ... , 'product': ...}
    '''
    data = {'chara': {}, 'product': {}}
    # 检查是否有角色栏
    # 如果没有角色栏，则跳过该作品
    if html.find(';キャラクター</div>') != -1:

        soup = BeautifulSoup(html, 'lxml')
        tags = soup.select('table')

        # 标题栏
        head_tag = soup.find_all('table', {'id': 'soft_table'})[0]
        # 先找封面图
        ## 这个没找到啥特别特征，目前就用序号来查
        # 居然有的作品，连封面都没。。。
        cover_tag = head_tag.find_all('td', {'rowspan': 2})[0]
        _some_tags = re.findall(r'href="\.(/\w+?/\w+?/[\w.]+?)"', str(cover_tag), re.I)
        if len(_some_tags) > 0:
            cover_pic_link = _some_tags[0]
            cover_pic_link = web_root + cover_pic_link
            data['product']['cover_pic_link'] = cover_pic_link
            data['product']['cover_pic_name'] = cover_pic_link[cover_pic_link.rfind('/')+1:]
        else:
            data['product']['cover_pic_link'] = None
            data['product']['cover_pic_name'] = None
            # 没有封面，角色图更加不可能存在了，跳过就行了
            # 还是暂时留着吧
            # return None

        # 然后找原画师，用正则挖
        # 当然，可能没有原画。。。
        try:
            painter = re.findall(r'\n原画：(.+?)\n', head_tag.text, re.I)[0]
            painter = painter.split('、')
        except IndexError:
            painter = ''
        data['product']['painter'] = painter

        # 找发售日
        try:
            release_date = re.findall(r'発売日：\s*(\d+/\d+/\d+)\s', head_tag.text, re.I)[0]
        except IndexError:
            release_date = ''
        data['product']['release_date'] = release_date

        # 角色介绍栏
        chara_tags = None
        # 查找哪个是角色介绍栏
        for t in tags:
            if str(t).find('chara-name') != -1:
                chara_tags = t
                break
        wait_to_check_chara_tags = chara_tags.select('tr')
        # 通过检查有没有找到字符串 chara-name 来检查是角色条还是占位条
        chara_tags = []
        for t in wait_to_check_chara_tags:
            if str(t).find('chara-name') != -1:
                chara_tags.append(t)
        # print('Found {} chara'.format(len(chara_tags)))

        # 开始分解角色栏组成部分
        for chara_tag in chara_tags:
            _l = chara_tag.select('td')
            # 角色全身图不一定有
            chara_full_pic_tag = None
            if len(_l) == 3:
                # 该栏有 主图，介绍，全身图
                chara_main_pic_tag, chara_content_tag, chara_full_pic_tag = _l
            elif len(_l) == 2:
                # 该栏只有 主图，介绍
                chara_main_pic_tag, chara_content_tag = _l
            else:
                # 遇到产品id为 1017496 这种，直接跳过
                return None
                # # 网页结构改变了
                # raise AssertionError('你需要再次检查网页，网页结构变了')

            chara_main_pic_link = chara_name = chara_full_pic_link = None

            # 处理角色主图
            if chara_main_pic_tag is not None:
                # 有的角色没有任何图像。。。
                try:
                    # 直接用正则表达式把图像链接挖出来
                    chara_main_pic_link = re.findall(r'src="\.(/\w+?/\w+?/[\w.]+?)"', str(chara_main_pic_tag), re.I)[0]
                    # 补充网站前缀
                    chara_main_pic_link = web_root + chara_main_pic_link
                except:
                    pass

            # 处理角色名字
            if chara_content_tag is not None:
                chara_name_tag = chara_content_tag.select('h2', {'class': 'chara-name'})[0]
                # 角色名处理有点复杂
                # 这里排除掉头衔，有的角色有头衔，例如 鸣濑白羽 的头衔 忘记暑假的少女
                # 有的作品，角色名会与CV分成两行，这就需要两行了
                # 算了，放弃只挖名字。。。 很麻烦啊，还是包括头衔等一堆东西算了

                # 屏蔽这里
                # chara_name = str(chara_name_tag.contents[-2]) + str(chara_name_tag.contents[-1])
                # # 角色名常见配置 "鳴瀨 しろは（なるせ しろは）　CV：小原好美"
                # # 先检查括号，有括号就直接用括号来排除；没有括号就检查 CV：，排除掉CV：；如果都没有检测到，这个就是全角色名了
                # # 注意要用全角符号
                # _pos = chara_name.find('（')
                # if _pos == -1:
                #     _pos = chara_name.find('CV：')
                #
                # if _pos == -1:
                #     _pos = None
                # chara_name = chara_name[:_pos]

                # 去除角色名左右两边多余的空格，但不要去除角色名内部的空格
                chara_name = chara_name_tag.text

                # 好吧，因为还存在着名字只有一个空格的角色。。。产品ID：27393
                # 所以屏蔽以下。。
                # chara_name = chara_name.strip()

                if len(chara_name) == 0:
                    raise AssertionError('Found chara name is empty!')

            # 处理角色全身图
            if chara_full_pic_tag is not None:
                # 老办法，使用正则直接挖出来
                chara_full_pic_link = re.findall(r'href="\.(/\w+?/\w+?/[\w.]+?)"', str(chara_full_pic_tag), re.I)[0]
                chara_full_pic_link = web_root + chara_full_pic_link

            # print(chara_main_pic_link, chara_name, chara_full_pic_link)

            # 加入表
            chara_main_pic_name = chara_full_pic_name = None

            if chara_main_pic_link is not None:
                chara_main_pic_name = chara_main_pic_link[chara_main_pic_link.rfind('/')+1:]

            if chara_full_pic_link is not None:
                chara_full_pic_name = chara_full_pic_link[chara_full_pic_link.rfind('/')+1:]

            data['chara'][chara_name] = {'chara_main_pic_name': chara_main_pic_name, 'chara_main_pic_link': chara_main_pic_link,
                                         'chara_full_pic_name': chara_full_pic_name, 'chara_full_pic_link': chara_full_pic_link}

        return data
    else:
        return None


company_id2name = {}


def download(link, path):
    '''
    下载链接到文件
    :param link: 下载链接
    :param path: 下载文件
    :return:
    '''
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        r = s.get(link, timeout=timeout, headers=headers, cookies=cookies, proxies=proxies, verify=False)
    except (requests.ConnectionError, requests.Timeout):
        return None, None
    if r.status_code == 200:
        if path is not None:
            open(path, 'wb').write(r.content)
        return r.status_code, r.content
    else:
        print('Download link {} failure status_code {}.'.format(link, r.status_code))
    return r.status_code, None


if __name__ == '__main__':

    # 初始化会话
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))

    dataset_root = 'dataset'
    os.makedirs(dataset_root, exist_ok=True)

    # stage1
    print('stage 1')
    # 检查有没有现成的公司表
    print('Getting company list')
    complete_mark = os.path.join(dataset_root, '.complete')
    company_list_html_path = os.path.join(dataset_root, 'company.html')

    if os.path.isfile(complete_mark) and auto_use_stage1_cache:
        print('Use cache')
    else:
        # 先删除完成标记，避免临界意外
        if os.path.isfile(complete_mark):
            os.remove(complete_mark)

        code = None
        try_count = 0
        while code != 200 and try_count < retries:
            # 获取公司列表
            code, _ = download('http://www.getchu.com/all/brand.html?genre=pc_soft', company_list_html_path)
            time.sleep(req_interval)
            try_count += 1
        if code != 200:
            raise AttributeError('Download company list html failure with retry {} status_code {}'.format(try_count, code))
        # 生成完成标记
        open(complete_mark, 'wb')

    f = open(company_list_html_path, 'rb').read().decode('EUC-JP', errors='replace')
    # 获取公司链接和名字
    companies_link_name_id = step1_get_companies_list(f)
    #

    n_company = len(companies_link_name_id)

    # stage2
    # 公司数量就 2100 个左右，不使用多线程
    print('stage 2')
    # 保存搜索页面
    for n_id, (company_link, company_name, company_id) in enumerate(companies_link_name_id):
        print('({}/{}) Getting company product list. Company name&id: ({}/{})'.format(n_id+1, n_company, company_name, company_id))
        # 写入id到公司名的映射表
        company_id2name[company_id] = company_name
        # 文件夹名用id来替代
        company_dir = os.path.join(dataset_root, company_id)
        # 建立公司文件夹
        os.makedirs(company_dir, exist_ok=True)

        complete_mark = os.path.join(company_dir, '.complete')
        # 产品列表文件路径
        product_list_html_path = os.path.join(company_dir, 'list.html')

        if os.path.isfile(complete_mark) and auto_use_stage2_cache:
            print('Use cache')
        else:
            s = requests.Session()
            s.mount('http://', HTTPAdapter(max_retries=retries))
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # 先删除完成标记，避免临界意外
            if os.path.isfile(complete_mark):
                os.remove(complete_mark)
            # 添加参数，使所有产品都在同一个页面显示
            # 增加限制，限制为最多5000个产品，限制只有pc游戏
            # 还可以增加日期限制，只需使用 &start_year=2005&start_month=1&start_day=1&end_year=2025&end_month=12&end_day=30
            new_company_link = company_link + '&list_count=5000' + '&genre=pc_soft'

            code = None
            try_count = 0
            while code != 200 and try_count < retries:
                # 获取产品列表
                code, _ = download(new_company_link, product_list_html_path)
                time.sleep(req_interval)
                try_count += 1
                if code != 200:
                    print('Download product list html failure with status_code {}, will be retry.'.format(code))
            if code != 200:
                raise AttributeError(
                    'Download product list html failure with retry {} status_code {}'.format(try_count, code))
            # print('{} 已完成'.format(company_name))
            # 设定完成标记，避免重复处理
            open(complete_mark, 'wb')

    # 保存公司id到公司名映射
    json.dump(company_id2name, open(os.path.join(dataset_root, 'id2name.json'), 'w', encoding='utf8'))

    # stage3
    print('stage 3')
    # 数量太多，分开数据下载和处理，这样就算获取失败了，重启不会耗费太多时间
    # 使用多线程下载
    n_thread = 4
    n_failure = 0
    no_more = False
    command_quene = queue.Queue(maxsize=n_thread)
    worker_threads = []

    def stage3_download(complete_mark, product_link, product_dir):
        # 先删除完成标记，避免临界意外
        if os.path.isfile(complete_mark):
            os.remove(complete_mark)

        # 下载产品网页并保存，如果下载到500页面，可以马上重试，而不是跳过
        code = None
        try_count = 0
        while code != 200 and try_count < retries:
            # 获取产品列表
            code, _ = download(product_link, os.path.join(product_dir, 'soft.html'))
            time.sleep(req_interval)
            try_count += 1
            if code != 200:
                print('Download product info html failure with status_code {}, will be retry.'.format(code))
        if code != 200:
            print('Download product info html failure with retry {} status_code {}.'.format(try_count, code))
            return False

        # 设定完成标记，避免重复处理
        open(complete_mark, 'wb')
        return True

    def stage3_worker_run():
        global n_failure
        while True:
            try:
                new_cmd = command_quene.get(block=True, timeout=2)
            except queue.Empty:
                if no_more and command_quene.empty():
                    break
                continue
            b = stage3_download(*new_cmd)
            if not b:
                n_failure += 1

    # 启动工作线程
    for _ in range(n_thread):
        t = Thread(target=stage3_worker_run)
        t.start()
        worker_threads.append(t)

    # 页面下载
    for n_id, (company_link, company_name, company_id) in enumerate(companies_link_name_id):
        company_dir = os.path.join(dataset_root, company_id)
        t2 = open(os.path.join(company_dir, 'list.html'), 'rb').read().decode('EUC-JP', errors='replace')
        # 产品链接和名字和id
        products_link_name_id = step2_get_products_list(t2)

        product_id2name = {}

        n_product = len(products_link_name_id)

        for n2_id, (product_link, product_name, product_id) in enumerate(products_link_name_id):
            print('({}/{}) ({}/{}) Getting product info. Product name&id: ({}/{}) Company name&id: ({}/{})'.
                  format(n_id+1, n_company, n2_id+1, n_product, product_name, product_id, company_name, company_id))
            # 写入产品id到名字的映射表
            product_id2name[product_id] = product_name
            product_dir = os.path.join(dataset_root, company_id, product_id)
            # 新建产品文件夹
            os.makedirs(product_dir, exist_ok=True)

            complete_mark = os.path.join(product_dir, '.complete')

            if os.path.isfile(complete_mark) and auto_use_stage3_cache:
                print('Use cache')
            else:
                # 这部分使用多线程加速
                # # 先删除完成标记，避免临界意外
                # if os.path.isfile(complete_mark):
                #     os.remove(complete_mark)
                # # 下载产品网页并保存
                # r = s.get(product_link, timeout=10, cookies=cookies, proxies=proxies, verify=False)
                # time.sleep(req_interval)
                # # print(r.status_code)
                # if r.status_code != 200:
                #     print(r.status_code)
                #     raise AssertionError('download html failure')
                # open(os.path.join(product_dir, 'soft.html'), 'wb').write(r.content)
                # # 设定完成标记，避免重复处理
                # open(complete_mark, 'wb')

                command_quene.put([complete_mark, product_link, product_dir], block=True)
                # download(complete_mark, product_link, product_dir)

    no_more = True
    print('waiting worker quit')
    for t in worker_threads:
        t.join()

    # 检查失败数量，不为0就报错退出，因为要全部下载完才进行下一步
    if n_failure > 0:
        print('n_failure', n_failure)
        raise AssertionError('Found n_failure > 0, please restart download')

    # 分析页面和提取数据
    for n_id, (company_link, company_name, company_id) in enumerate(companies_link_name_id):
        company_dir = os.path.join(dataset_root, company_id)
        t2 = open(os.path.join(company_dir, 'list.html'), 'rb').read().decode('EUC-JP', errors='replace')
        # 产品链接和名字和id
        products_link_name_id = step2_get_products_list(t2)

        product_id2name = {}

        n_product = len(products_link_name_id)

        for n2_id, (product_link, product_name, product_id) in enumerate(products_link_name_id):
            print('({}/{}) ({}/{}) Generating product info. Product name&id: ({}/{}) Company name&id: ({}/{})'.
                  format(n_id + 1, n_company, n2_id + 1, n_product, product_name, product_id, company_name,
                         company_id))
            # 写入产品id到名字的映射表
            product_id2name[product_id] = product_name
            product_dir = os.path.join(dataset_root, company_id, product_id)

            t3 = open(os.path.join(product_dir, 'soft.html'), 'rb').read().decode('EUC-JP', errors='replace')

            data = step3_get_product_info(t3)
            if data is not None:
                json.dump(data, open(os.path.join(product_dir, 'data.json'), 'w', encoding='utf8'))

        # 保存id名到游戏名映射
        json.dump(product_id2name, open(os.path.join(dataset_root, company_id, 'id2name.json'), 'w', encoding='utf8'))

    print('Success')
