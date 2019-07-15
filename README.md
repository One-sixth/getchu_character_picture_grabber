# getchu_character_picture_grabber
A tool main for grab getchu character picture.  
一个用于抓取角色图的getchu爬虫。  

## Example / 示例
![](https://github.com/One-sixth/getchu_character_picture_grabber/blob/master/sample/sample1.jpg)

# Downloaded dataset / 已下载的数据集
#### 2019/7/12
Baidu disk：https://pan.baidu.com/s/1bTWoEcJRzXJaMM8jELPCBA  

## Dependent / 依赖
BeautifulSoup >= 4.7.1  
requests  
lxml  

You can install dependently package with command  
你可以使用以下命令安装依赖包
```
pip3 install -U BeautifulSoup4 requests lxml
```

## Dataset structure / 数据集结构

Directory structure | 目录结构  

/dataset  

Level top | 第一层  
/dataset/company.html  
/dataset/id2name.json  
/dataset/company_id  

Level second | 第二层  
/dataset/company_id/list.html  
/dataset/company_id/id2name.json  
/dataset/company_id/product_id  

Level third | 第三层  
/dataset/company_id/product_id/soft.html  
/dataset/company_id/product_id/data.json  
/dataset/company_id/product_id/*.jpg  

----------------------------------------------------------------

data.json structure | data.json 结构  

\<chara>  
----<*chara_name>  
--------<main_pic_name>  
--------<main_pic_link>  
--------<full_pic_name>  
--------<full_pic_link>  
\<product>  
----<cover_pic_name>  
----<cover_pic_link>  
----\<painter>  
----<release_date>  

## How to use / 怎么用

All parameters are defined in the file.  
所有的参数都定义在文件中。  

### Step 1 download data structure / 第一步 下载数据结构
1.Open getchu_grab_info.py file with your text editor  
2.Setting proxy  
If your country can direct access to www.getchu.com, find the variable use_proxy and set it to False.
```
use_proxy = False
```
Otherwise find the proxies variable and change it to your proxy address.
```
proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080'
}
```
Please be careful if your proxy agreement is socks5. For example, the proxy address is socks5://127.0.0.1:1080  
Please still use the http style proxy address.  
Like this.  
```
proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080'
}
```
Not like it.  
```
proxies = {
    'http': 'socks5://127.0.0.1:1080',
    'https': 'socks5://127.0.0.1:1080'
}
```
Because of testing on my system, requests are not properly connected to the socks5 proxy protocol. Of course, if your requests library is properly connected to the socks5 proxy protocol, you can still use them.  

It is recommended to use Japanese IP to achieve faster download speeds.

3.Save file.  
4.Call the following command to start the download.  
```
python3 getchu_grab_info.py
```
5. Downloading is difficult once. If the download fails halfway, please directly call the command to continue the download. The downloaded file will not be downloaded repeatedly.  
```
python3 getchu_grab_info.py
```
7. After the download successful, the terminal will prints Success.  

----------------------------------------------------------------

1.用文本编辑器打开 getchu_grab_info.py 文件  
2.设定代理  
如果你所在的区域可以直接访问 www.getchu.com, 请找到变量 use_proxy 并设置为 False.  
```
use_proxy = False
```
否则请找到 proxies 变量，并修改为你的代理地址。  
```
proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080'
}
```
请注意，如果你的代理协议是socks5，代理地址为 socks5://127.0.0.1:1080  
请仍然使用http样式的代理地址，  
```
proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080'
}
```
而不是  
```
proxies = {
    'http': 'socks5://127.0.0.1:1080',
    'https': 'socks5://127.0.0.1:1080'
}
```
因为在我的系统上测试，requests 不能正常连接上 socks5 代理协议。当然，如果你的 requests 库能正常连接上 socks5 代理协议，你仍然可以使用它们。  

建议使用日本的IP，可以达到较快的下载速度。

3.保存文件  
4.调用以下命令开始下载  
```
python3 getchu_grab_info.py
```
5.下载很难一次成功。如果中途下载失败，请直接调用命令继续下载，已下载的文件不会重复进行下载。  
```
python3 getchu_grab_info.py
```
6.下载成功后，终端会打印出 Success 字符串。  

### Step 2 Download character picture | 第二步 下载角色图

1. Open getchu_grab_pic.py with your text editor  
2. Find the variable use_proxy and set it in the same way as the first step.  
3. Find the variable proxies and set it up in the same way as the first step.  
4. Save the file  
5. Call the following command to start the download  
```
python3 getchu_grab_pic.py
```
6. Downloading is difficult once. If the download fails halfway, please directly call the command to continue the download. The downloaded file will not be downloaded repeatedly.  
```
python3 getchu_grab_pic.py
```
7. After the download successful, the terminal will print out the Success.  
8. At this point, the dataset download has been completed, and all data can be found in the dataset folder.  

------------------------------------------------------------------------

1.用文本编辑器打开 getchu_grab_pic.py  
2.找到变量 use_proxy，并设置，设置方式与第一步相同  
3.找到变量 proxies 并设置，设置方式与第一步相同  
4.保存文件  
5.调用以下命令开始下载  
```
python3 getchu_grab_pic.py
```
6.下载很难一次成功。如果中途下载失败，请直接调用命令继续下载，已下载的文件不会重复进行下载。  
```
python3 getchu_grab_pic.py
```
7.下载成功后，终端会打印出 Success 字符串。  
8.此时已完成数据抓取，抓取到数据将会位于 dataset 文件夹中  

### Update dataset / 更新数据库
After a while, getchu will have new products on the shelves and need to update the dataset.  
The update method is to clear the completion flag first, and then repeat the first and second steps above to update the dataset.  

一段时间后，getchu会有新的产品上架，需要更新数据集。  
更新方式是先清除完成标志，然后再重复以上的第一第二步，更新数据集  

1. Open clear_complete_flag.py with your text editor  
2. If you want to refresh the list of companies, find and set clear_stage1_complete = True  
3. If you want to refresh the list of product list for each company, find and set clear_stage2_complete = True  
4. If you want to refresh each product information, find and set clear_stage3_complete = True  
5. If you want to re-download images for each product, find and set clear_stage3_complete_pic = True  
6. Save the file  
7. Start with the following command  
```
python3 clear_complete_flag.py
```
8. After scanning, enter y to confirm clear, or n to cancel  
9. If the clear is completed, it will output 'Success'; if it is canceled, it will output 'Cancel'  
10. After the cleanup success, repeat the step 1 and step 2 to update the dataset.  

--------------------------------------------------------------------

1.用文本编辑器打开 clear_complete_flag.py  
2.如果要刷新公司列表，请找到和设置 clear_stage1_complete = True  
3.如果要刷新每个公司的产品列表，请找到和设置 clear_stage2_complete = True  
4.如果要刷新每个产品信息，请找到和设置 clear_stage3_complete = True  
5.如果要重新下载每个产品的图像，请找到和设置 clear_stage3_complete_pic = True  
6.保存文件  
7.使用以下命令开始  
```
python clear_complete_flag.py
```
8.扫描完后，输入 y 确认清除，或 n 取消  
9.如果清除完成，则会输出 'Success'；如果取消了，则会输出 'Cancel'  
10.清除完成后，重复第一第二步，更新数据库  
