# -*- coding: utf-8 -*-
import os
import json
import zlib
import time
import shutil
from .Repack_iss import Repack_Dat

class Repack_Text:

    def __init__(self):
        self.repack_dat = Repack_Dat()

    def vnt2json(self, file_name):
        ## 这是将vnt格式json转成原来支持的json格式函数
        json_file = os.path.join(self.json_path, file_name.replace('.iss', '.json'))
        ## 为了下次可以接着运行，先备份，处理完后把json删了还原备份文件
        ## 这里复用原字典代码来处理
        shutil.copyfile(json_file, json_file.replace('.json', '.json.bak'))
        bin_file = os.path.join(self.src_path, 'bin', file_name.replace('.iss', '.bin'))
        with open(json_file, 'r', encoding='utf-8') as json_fp:
            json_data = json.load(json_fp)
            if type(json_data) != list:
                return
        with open(bin_file, 'rb') as bin_fp:
            cn_list_count = 0
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
                text_group_start_pos = bin_fp.tell()
                text_group_info_length = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
                text_group_info = bin_fp.read(text_group_info_length - 4)
                text_group_size = int.from_bytes(text_group_info[0:4], byteorder='little', signed=False)
                text_group_flag = int.from_bytes(text_group_info[4:8], byteorder='little', signed=False)
                text_info = bin_fp.read(8)
                text_num = int.from_bytes(text_info[4:8], byteorder='little', signed=False)
                text_exists = False
                for j in range(text_num):
                    text_head = bin_fp.read(32)
                    if text_head[8:16] == b'\x64\x00\x00\x00\x01\x00\x00\x00':
                        bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)
                    elif text_head[8:16] == b'\x65\x00\x00\x00\x01\x00\x00\x00':
                        bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)
                        text_exists = True
                    elif int.from_bytes(text_head[4:8],byteorder='little',signed=False) == 0 and text_head[8:12] == b'\x69\x00\x00\x00':
                        bin_fp.read(32)
                        break
                    elif text_head[8:12] == b'\x67\x00\x00\x00':
                        bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)
                    else:
                        bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32)
                if text_exists:
                    text_dict = json_data[cn_list_count]
                    if type(text_dict) != dict:
                        raise ValueError(f"读取vnt格式json出现问题: {json_file}")
                    cn_list_count += 1
                    text_new_dict = {}
                    if text_dict.get('name'):
                        text_new_dict['name'] = text_dict['name']
                    string_list = text_dict.get('message', '').split('\n')
                    if len(string_list) == 0:
                        raise ValueError(f"此json的message有问题，切割不了或者文本出错: {json_file}")
                    try:
                        for index in range(len(string_list)):
                            text_new_dict[f"message{index+1}"] = string_list[index]
                    except:
                        print(f"第{i}组，第{index}句，分割为{string_list}")
                    text_dict_total[i] = text_new_dict
            with open(json_file, 'w', encoding='utf-8') as json_fp:
                json.dump(text_dict_total, json_fp, ensure_ascii=False, indent=4)

    def main_func(self, source_path, org_dat_path, vnt_flag):
        self.source_path = source_path
        self.src_path = os.path.join(source_path, 'iss')
        self.json_path = os.path.join(self.source_path, 'cn_json')
        if not os.path.exists(self.src_path) or not os.path.exists(os.path.join(self.src_path, 'bin')):    ##  or not os.path.exists(os.path.join(self.src_path, 'json'))
            raise ValueError(f"不存在剧本路径{self.src_path}及其路径下的bin文件夹，请确认已解包出文本并提供正确的路径")
        if not os.path.exists(self.json_path):
            os.makedirs(self.json_path, exist_ok=True)
            raise ValueError(f"不存在汉化json路径{self.json_path}，请把汉化json放在这个路径下")
        self.org_dat_path = org_dat_path
        file_list = [file for file in os.listdir(self.src_path) if file.endswith('.iss')]
        os.makedirs(os.path.join(self.source_path, 'new_iss'), exist_ok=True)
        for file_name in file_list:
            try:
                self.json_file = os.path.join(self.json_path, file_name.replace('.iss', '.json'))
                if not os.path.exists(self.json_file):
                    continue
                ## 如果导出的是vnt格式的json请调用vnt2json函数适配输入格式，不是请注释掉这个函数
                if vnt_flag:
                    self.vnt2json(file_name)
                ## -----------------------------------------------------
                self.repack_from_json(file_name)
                ## 在这里清理选择vnt模式生成的原字典并还原备份
                if vnt_flag:
                    if os.path.exists(self.json_file) and os.path.exists(self.json_file.replace('.json', '.json.bak')):
                        os.remove(self.json_file)
                        os.rename(self.json_file.replace('.json', '.json.bak'), self.json_file)
            except Exception as e:
                raise RuntimeError(f"导入json数据时出现问题，文件: {file_name.replace('.iss', '.json')}。错误: {e}")
            try:
                self.repack2iss(file_name)
            except Exception as e:
                raise RuntimeError(f"重封包iss时出现问题，文件: {file_name}。") from e
        print("iss文件已重封包完毕，生成dat文件中……")
        self.repack_dat.main_func(self.source_path, self.org_dat_path)


    def pad_binary_string(self, binary_data):
        current_length = len(binary_data)
        remainder = current_length % 16
        
        if remainder <= 4:
            padding_length = 8 - remainder
        elif 4 < remainder <= 8:
            padding_length = 16 - remainder
        elif 8 < remainder <= 12:
            padding_length = 16 - remainder
        else:
            padding_length = 24 - remainder
        
        padded_data = binary_data + b'\x00' * padding_length
        return padded_data

    def repack_from_json(self, file_name):
        json_file = self.json_file # os.path.join(self.src_path, 'json', file_name.replace('.iss', '.json'))
        bin_file = os.path.join(self.src_path, 'bin', file_name.replace('.iss', '.bin'))
        chs_bin_file = os.path.join(self.src_path, 'bin', file_name.replace('.iss', '_chs.bin'))
        with open(json_file, 'r', encoding='utf-8') as js_fp:
            json_data = json.load(js_fp)
            if not json_data:
                return
        with open(bin_file, 'rb') as bin_fp, open(chs_bin_file, 'wb') as chs_bin_fp:
            scene_head_length = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
            scene_head = bin_fp.read(scene_head_length - 4)
            chs_bin_fp.write(scene_head_length.to_bytes(4, byteorder='little', signed=False))
            chs_bin_fp.write(scene_head)
            scene_head_data = bin_fp.read(int.from_bytes(scene_head[4:8], byteorder='little', signed=False) - scene_head_length)
            chs_bin_fp.write(scene_head_data)
            group_flag = bin_fp.read(4)
            if group_flag == b'\x08\x00\x00\x00':
                group_count = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
                chs_bin_fp.write(group_flag)
                chs_bin_fp.write(group_count.to_bytes(4, byteorder='little', signed=False))
            else:
                raise RuntimeError(f"{bin_file}获取语句组数量失败")
            for i in range(group_count):
                ## over_flag是判断是否为最后一个语句组的标志
                over_flag = False
                text_group_start_pos = chs_bin_fp.tell()
                text_group_info_length = int.from_bytes(bin_fp.read(4), byteorder='little', signed=False)
                chs_bin_fp.write(text_group_info_length.to_bytes(4, byteorder='little', signed=False))
                text_group_pos = chs_bin_fp.tell()
                text_group_info = bin_fp.read(text_group_info_length - 4)
                chs_bin_fp.write(text_group_info)
                text_group_size = int.from_bytes(text_group_info[0:4], byteorder='little', signed=False)
                if text_group_size == 0:
                    over_flag = True
                text_group_flag = int.from_bytes(text_group_info[4:8], byteorder='little', signed=False)
                text_info = bin_fp.read(8)
                chs_bin_fp.write(text_info)
                text_num = int.from_bytes(text_info[4:8], byteorder='little', signed=False)
                text_count = 1
                cn_data = json_data.get(str(i))
                for j in range(text_num):
                    text_head = bytearray(bin_fp.read(32))
                    if text_head[8:16] == b'\x64\x00\x00\x00\x01\x00\x00\x00':
                        bin_fp.read((int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32))
                        cn_name = cn_data.get("name")
                        if not cn_name or cn_name == "":
                            name = bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32).replace(b'\x00\x00', b'').decode('utf-16le')
                            raise RuntimeError(f"人名出错，请检查这个名字: {name}，文件：{bin_file}，偏移：{bin_fp.tell()}")
                        cn_name = f"\"{cn_name}\""
                        cn_name = self.pad_binary_string(cn_name.encode('utf-16le'))
                        text_head[4:8] = (len(cn_name)+32).to_bytes(4,byteorder='little',signed=False)
                        chs_bin_fp.write(text_head)
                        chs_bin_fp.write(cn_name)
                    elif text_head[8:16] == b'\x65\x00\x00\x00\x01\x00\x00\x00':
                        bin_fp.read((int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32))
                        cn_message = cn_data.get(f"message{text_count}")
                        if cn_message == None:
                            raise RuntimeError(f"获取第{i}个语句组时出现问题,句子序号为message{text_count}，文件: {bin_file}，偏移：{bin_fp.tell()}")
                        if not cn_message.endswith('\\@'):
                            cn_message = f"\"{cn_message}\\n\""
                        else:
                            cn_message = f"\"{cn_message}\""
                        cn_message = self.pad_binary_string(cn_message.encode('utf-16le'))
                        text_head[4:8] = (len(cn_message)+32).to_bytes(4,byteorder='little',signed=False)
                        text_count += 1
                        chs_bin_fp.write(text_head)
                        chs_bin_fp.write(cn_message)
                    elif text_head[8:12] == b'\x67\x00\x00\x00':
                        chs_bin_fp.write(text_head)
                        if int.from_bytes(text_head[4:8],byteorder='little',signed=False) - 32 != 0:
                            chs_bin_fp.write(bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32))
                    elif int.from_bytes(text_head[4:8],byteorder='little',signed=False) == 0 and text_head[8:12] == b'\x69\x00\x00\x00':
                        chs_bin_fp.write(text_head)
                        chs_bin_fp.write(bin_fp.read(32))
                        break
                    else:
                        chs_bin_fp.write(text_head)
                        chs_bin_fp.write(bin_fp.read(int.from_bytes(text_head[4:8],byteorder='little',signed=False)-32))
                if not over_flag:
                    text_group_end_pos = chs_bin_fp.tell()
                    text_group_new_size = (text_group_end_pos - text_group_start_pos).to_bytes(4, byteorder='little', signed=False)
                    chs_bin_fp.seek(text_group_pos)
                    chs_bin_fp.write(text_group_new_size)
                    chs_bin_fp.seek(text_group_end_pos)

    def repack2iss(self, file_name):
        chs_bin_file = os.path.join(self.src_path, 'bin', file_name.replace('.iss', '_chs.bin'))
        if not os.path.exists(chs_bin_file):
            return
        chs_iss_file = os.path.join(os.path.split(self.src_path)[0], 'new_iss', file_name)
        org_iss_file = os.path.join(self.src_path, file_name)
        issfile_head = b'\x49\x53\x53\x20'
        with open(chs_bin_file, 'rb') as cn_data_fp, open(chs_iss_file, 'wb') as cn_iss_fp:
            cn_data = cn_data_fp.read()
            cn_data_size = len(cn_data).to_bytes(4, byteorder='little', signed=False)
            compresser = zlib.compressobj(level=9)
            cn_compress_data = compresser.compress(cn_data) + compresser.flush()
            cn_com_data_size = len(cn_compress_data).to_bytes(4, byteorder='little', signed=False)
            cn_iss_fp.write(issfile_head)
            with open(org_iss_file, 'rb') as jp_iss_fp:
                jp_iss_fp.seek(20)
                jp_org_data = jp_iss_fp.read(12)
            cn_iss_fp.write(b'\x20\x00\x00\x00')
            cn_iss_fp.write(cn_com_data_size)
            cn_iss_fp.write(cn_data_size)
            cn_iss_fp.write(b'\x01\x00\x00\x00')
            cn_iss_fp.write(jp_org_data)
            cn_iss_fp.write(cn_compress_data)


def CLI_main():  
    while True:
        source_path = input("请输入你存放iss的根文件夹，按e返回\n")
        if source_path == 'e':
            print("返回中……\n")
            break
        dat_path = input("请输入原剧情dat文件路径，按e返回\n")
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
            repack_text = Repack_Text()
            repack_text.main_func(source_path, dat_path, vnt_flag)
            print("返回中……\n")
            break
        except ValueError as e:
            print(e)
            time.sleep(0.5)
            continue
        except RuntimeError as e:
            print(e)
            time.sleep(0.5)
            print("返回中……\n")
            break
        except Exception as e:
            print(e)
            time.sleep(0.5)
            print("返回中……\n")
            break