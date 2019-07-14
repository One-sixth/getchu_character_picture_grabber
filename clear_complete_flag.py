'''
很多时候，爬虫内的忽略标志并不好用
'''

import os


stage1_complete_name = '.complete'
stage2_complete_name = '.complete'
stage3_complete_name = '.complete'
stage3_complete_pic_name = '.complete_pic'


# -----------------------------------------------------------
# 参数区
# 清除标志开关
clear_stage1_complete = False
clear_stage2_complete = False
clear_stage3_complete = False
clear_stage3_complete_pic = False
# -----------------------------------------------------------


dataset_root = 'dataset'

wait_to_delete_mark = []

# 使用一个大循环来解决这个问题
for company_id in os.listdir(dataset_root):
    company_path = os.path.join(dataset_root, company_id)

    if clear_stage1_complete and company_id == stage1_complete_name:
        print('Wait to delete', company_path)
        wait_to_delete_mark.append(company_path)

    elif os.path.isdir(company_path):
        # 如果是文件夹
        for product_id in os.listdir(company_path):
            product_path = os.path.join(company_path, product_id)

            if clear_stage2_complete and product_id == stage2_complete_name:
                print('Wait to delete', product_path)
                wait_to_delete_mark.append(product_path)

            elif os.path.isdir(product_path):
                for file_name in os.listdir(product_path):
                    file_path = os.path.join(product_path, file_name)

                    if clear_stage3_complete and file_name == stage3_complete_name:
                        print('Wait to delete', file_path)
                        wait_to_delete_mark.append(file_path)

                    elif clear_stage3_complete_pic and file_name == stage3_complete_pic_name:
                        print('Wait to delete', file_path)
                        wait_to_delete_mark.append(file_path)

while True:
    r = input('If you want to delete them.\nPlease input y to continue or n to cancel.\n')
    if r == 'n':
        print('Cancel')
        exit(0)
    elif r == 'y':
        break
    else:
        print('Please input y or n.')

for f in wait_to_delete_mark:
    # print(f)
    os.remove(f)

print('Success')
