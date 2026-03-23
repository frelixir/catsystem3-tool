# -*- coding: utf-8 -*-
import os
import zlib
import json
import time
from .Extract_iss import Extract_file

class Extract_text:

    def __init__(self):
        self.extract_file = Extract_file()

    def json2vnt(self, json_file, text_dict):
        if not text_dict:
            return
        text_list = []
        for value_dict in text_dict.values():
            new_dict = {}
            string = ''
            string_exists = False
            ## 这里获得的值也是字典
            for key, value in value_dict.items():
                if key == 'name':
                    new_dict[key] = value
                elif key == 'message1':
                    string = value
                    string_exists = True
                elif key != 'message1' and 'message' in key:
                    string = string + '\n' + value
            if string_exists:
                new_dict['message'] = string
                text_list.append(new_dict)
        with open(json_file, 'w', encoding='utf-8') as json_fp:
            json.dump(text_list, json_fp, ensure_ascii=False, indent=4)
        
    def main_func(self, dat_path, vnt_flag):
        self.dat_path = dat_path
        self.iss_path = self.extract_file.main_func(self.dat_path)
        iss_list = [os.path.join(self.iss_path, file) for file in os.listdir(self.iss_path) if file.endswith('.iss')]
        os.makedirs(os.path.join(self.iss_path, 'bin'), exist_ok=True)
        os.makedirs(os.path.join(self.iss_path, 'json'), exist_ok=True)
        os.makedirs(os.path.join(os.path.split(self.iss_path)[0], 'cn_json'), exist_ok=True)
        for iss_file in iss_list:
            bin_file = os.path.join(os.path.split(iss_file)[0], 'bin', os.path.split(iss_file)[1].replace('.iss', '.bin'))
            json_file = os.path.join(os.path.split(iss_file)[0], 'json', os.path.split(iss_file)[1].replace('.iss', '.json'))
            with open(iss_file, 'rb') as iss_fp, open(bin_file, 'wb') as bin_fp:
                bin_fp.write(self.decompress_func(iss_fp))
            self.extract_json(bin_file, json_file, vnt_flag)
        print(f"已完成剧本提取，请在{os.path.join(self.iss_path, 'json')}文件夹内查看文本json")
        self.get_name_dictionary(os.path.join(self.iss_path, 'json'))
        print('已提取出名字字典')

    def get_name_dictionary(self, json_path):
        try:
            json_list = [os.path.join(json_path, file) for file in os.listdir(json_path) if '.json' in file]
        except:
            raise RuntimeError('提取名字字典出现问题，即将退出……')
        name_dict = {}
        for json_file in json_list:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                if type(json_data) == dict:
                    ## 非vnt文本json
                    for key0, value0 in json_data.items():
                        if value0.get("name"):
                            if value0["name"] != "" and not name_dict.get(value0["name"]):
                                name_dict[value0["name"]] = value0["name"]
                elif type(json_data) == list:
                    ## vnt文本json
                    for text_dict in json_data:
                        if not text_dict.get('name'):
                            continue
                        else:
                            if text_dict["name"] != "" and not name_dict.get(text_dict["name"]):
                                name_dict[text_dict["name"]] = text_dict["name"]
        os.makedirs(os.path.join(self.iss_path, 'name_dict'), exist_ok=True)
        with open(os.path.join(self.iss_path, 'name_dict', 'name_dictionary.json'), 'w', encoding='utf-8') as dict_fp:
            json.dump(name_dict, dict_fp, ensure_ascii=False, indent=4)

    def decompress_func(self, compress_fp):
        file_data = compress_fp.read()
        compress_length = int.from_bytes(file_data[8:12], byteorder='little', signed=False)
        decompress_length = int.from_bytes(file_data[12:16], byteorder='little', signed=False)
        decompress_data = zlib.decompressobj().decompress(file_data[32:32+compress_length])
        if len(decompress_data) != decompress_length:
            uncompress_data = file_data[32+compress_length:32+compress_length+decompress_length-len(decompress_data)]
            if uncompress_data:
                decompress_data = decompress_data + uncompress_data
        return decompress_data
    
    def remove_zerozero(self, data):
        while data.endswith(b'\x00\x00'):
            data = data[:-2]
        return data

    def extract_json(self, bin_file, json_file, vnt_flag):
        with open(bin_file, 'rb') as bin_fp:
            scene_head_length = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
            scene_head = bin_fp.read(scene_head_length - 4)
            scene_head_data = bin_fp.read(int.from_bytes(scene_head[4:8], byteorder='little', signed=False) - scene_head_length)
            group_flag = bin_fp.read(4)
            if group_flag == b'\x08\x00\x00\x00':
                group_count = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
            else:
                raise RuntimeError(f"{bin_file}获取语句组数量失败")
            text_dict_total = {}
            for i in range(group_count):
                text_dict = {}
                text_group_start_pos = bin_fp.tell()
                text_group_info_length = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
                text_group_info = bin_fp.read(text_group_info_length - 4)
                text_group_size = int.from_bytes(text_group_info[0:4], byteorder='little', signed=False)
                text_group_flag = int.from_bytes(text_group_info[4:8], byteorder='little', signed=False)
                text_info = bin_fp.read(8)
                text_num = int.from_bytes(text_info[4:8], byteorder='little', signed=False)
                text_count = 1
                for j in range(text_num):
                    text_head = bin_fp.read(32)
                    if text_head[8:16] == b'\x64\x00\x00\x00\x01\x00\x00\x00':
                        try:
                            text_dict["name"] = self.remove_zerozero(bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)).decode('UTF-16LE').replace('\\n', '')
                            if text_dict['name'].startswith('"') and text_dict['name'].endswith('"'):
                                text_dict['name'] = text_dict['name'][1:-1]
                        except Exception as e:
                            raise RuntimeError(f"{bin_file}里处理人名出现问题: {e}，提取失败")
                    elif text_head[8:16] == b'\x65\x00\x00\x00\x01\x00\x00\x00':
                        try:
                            text_dict[f"message{text_count}"] = self.remove_zerozero(bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)).decode('UTF-16LE').replace('\\n', '')
                            if text_dict[f"message{text_count}"].startswith('"') and text_dict[f"message{text_count}"].endswith('"'):
                                text_dict[f"message{text_count}"] = text_dict[f"message{text_count}"][1:-1]
                            text_count += 1
                        except Exception as e:
                            raise RuntimeError(f"{bin_file}里处理文本出现问题: {e}，提取失败")
                    elif int.from_bytes(text_head[4:8],byteorder='little',signed=False) == 0 and text_head[8:12] == b'\x69\x00\x00\x00':
                        bin_fp.read(32)
                        break
                    elif text_head[8:12] == b'\x67\x00\x00\x00':
                        bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)
                    else:
                        bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)
                # if not text_dict.get("name"):
                #     if text_dict.get("message1"):
                #         text_dict['name'] = ""
                if text_dict:
                    text_dict_total[i] = text_dict
            ## 以下是关于导出的json格式选择
            if not vnt_flag:
                ## 这里是原处理函数，导出字典套字典的完整语句组json
                if text_dict_total:
                    with open(json_file, 'w', encoding='utf-8') as json_fp:
                        json.dump(text_dict_total, json_fp, indent=4, ensure_ascii=False)
            else:
                ## 这里是转换成vnt格式函数，导出vnt格式json
                self.json2vnt(json_file, text_dict_total)
            

def CLI_main():
    while True:
        dat_path = input("请输入剧情dat的文件路径，输入e返回\n")
        if dat_path == 'e':
            print("返回中……\n")
            break
        choose_flag = input("请选择你提取的json格式，1为原json格式，2为vnt格式，按e返回\n")
        if choose_flag == '1':
            vnt_flag = False
        elif choose_flag == '2':
            vnt_flag = True
        elif choose_flag == 'e':
            print("返回中……\n")
            break
        else:
            print("非法输入，请重新输入……")
            continue
        try:
            extract_text = Extract_text()
            extract_text.main_func(dat_path, vnt_flag)
            print("返回中……\n")
            break
        except Exception as e:
            print(e)
            time.sleep(0.5)
