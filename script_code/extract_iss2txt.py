# -*- coding: utf-8 -*-
import zlib
import os
import re
import time
from .Extract_iss import Extract_file

class Iss2Txt:

    def __init__(self):
        self.extract_file = Extract_file()

    def main_func(self, dat_path):
        self.dat_path = dat_path
        self.iss_path = self.extract_file.main_func(self.dat_path)
        self.bin_folder = os.path.join(self.iss_path, 'bin')
        self.txt_folder = os.path.join(self.iss_path, 'txt')
        self.retxt_folder = os.path.join(os.path.join(os.path.split(self.iss_path)[0], 'cn_re_txt'))
        os.makedirs(self.bin_folder, exist_ok=True)
        os.makedirs(self.txt_folder, exist_ok=True)
        iss_list = [file for file in os.listdir(self.iss_path) if file.endswith('.iss')]
        for iss_file in iss_list:
            self.iss2bin(iss_file)
            self.text_dump(iss_file)
        os.makedirs(self.retxt_folder, exist_ok=True)
        for iss_file in iss_list:
            self.extract_re_text(iss_file.replace('.iss', '.txt'))
        os.makedirs(os.path.join(os.path.split(self.iss_path)[0], 'cn_txt'), exist_ok=True)
        print(f"已完成剧本提取，请在{self.txt_folder}文件夹内查看文本txt，在{self.retxt_folder}查看文本")

    def has_cjk(self, text: str) -> bool:
        for ch in text:
            code = ord(ch)
            # CJK Unified Ideographs（中日韩汉字）
            if 0x4E00 <= code <= 0x9FFF:
                return True
            # 日文平假名 / 片假名
            if 0x3040 <= code <= 0x30FF:
                return True
            # 全角片假名扩展
            if 0x31F0 <= code <= 0x31FF:
                return True
        return False
    
    def extract_re_text(self, filename):
        with open(os.path.join(self.txt_folder, filename), 'r', encoding="UTF-16") as org_fp, open(os.path.join(self.retxt_folder, filename), 'w', encoding='utf-8-sig') as new_fp:
            pattern = r'"(.*?)"'
            for text in org_fp:
                if re.search(pattern, text):
                    match = re.search(pattern, text)
                    if self.has_cjk(match.group(0)):
                        new_fp.write(match.group(0))
                        new_fp.write('\n')
        if os.path.getsize(os.path.join(self.retxt_folder, filename)) == 0:
            os.remove(os.path.join(self.retxt_folder, filename))

    def iss2bin(self, filename):
        with open(os.path.join(self.iss_path, filename), 'rb') as iss_fp, open(os.path.join(self.bin_folder, filename.replace('.iss', '.bin')), 'wb') as bin_fp:
            bin_fp.write(self.unpack_data(iss_fp.read()))

    def text_dump(self, file_name):
        with open(os.path.join(self.txt_folder, file_name.replace('.iss', '.txt')), 'wb') as new_fp:
            new_fp.write(b'\xff\xfe')
        with open(os.path.join(self.bin_folder, file_name.replace('.iss', '.bin')), 'rb') as org_file, open(os.path.join(self.txt_folder, file_name.replace('.iss', '.txt')), 'ab') as new_file: # , 'w', encoding='UTF-16LE') as new_file:
            scene_head_count = int.from_bytes(org_file.read(4), byteorder='little', signed=False)
            scene_head_data = org_file.read(scene_head_count - 4)
            scene_data_count = int.from_bytes(scene_head_data[4:8], byteorder='little', signed=False) - scene_head_count
            scene_name = org_file.read(scene_data_count).decode('UTF-16LE')
            group_info = org_file.read(8)
            group_count = int.from_bytes(group_info[4:8], byteorder='little', signed=False)
            for i in range(group_count):
                text_group_head_count = int.from_bytes(org_file.read(4), byteorder='little', signed=False)
                text_group_head_data = org_file.read(text_group_head_count - 4)
                text_group_size = int.from_bytes(text_group_head_data[0:4], byteorder='little', signed=False)
                if text_group_size == 0:
                    pos = org_file.tell()
                text_group_info = org_file.read(8)
                text_num = int.from_bytes(text_group_info[4:8], byteorder='little', signed=False)
                for j in range(text_num):
                    text_head_count = int.from_bytes(org_file.read(4), byteorder='little', signed=False)
                    text_head_data = org_file.read(text_head_count - 4)
                    if text_head_data[4:8] == b'\x69\x00\x00\x00':
                        org_file.read(32)
                        if j != text_num - 1:
                            raise ValueError('出现语句组结尾异常！')
                        break
                    if text_head_data[4:8] == b'\x67\x00\x00\x00':
                        text_size = int.from_bytes(text_head_data[0:4], byteorder='little', signed=False) - text_head_count
                        text_data = org_file.read(text_size) # .decode('UTF-16LE')
                        if not text_data:
                            continue
                        new_file.write(text_data)
                        new_file.write('\n\n'.encode('UTF-16LE'))
                        continue
                    text_size = int.from_bytes(text_head_data[0:4], byteorder='little', signed=False) - text_head_count
                    text_data = org_file.read(text_size) # .decode('UTF-16LE')
                    new_file.write(text_data)
                    new_file.write('\n\n'.encode("UTF-16LE"))

    def unpack_data(self, file_data):
        data = file_data[8:12]
        int_value = int.from_bytes(data, byteorder='little', signed=False)
        decompress_count = file_data[12:16]
        decompress_count_value = int.from_bytes(decompress_count, byteorder='little', signed=False)
        compress_data = file_data[32:32+int_value]
        decompress_data = zlib.decompressobj().decompress(compress_data)
        if len(decompress_data) != decompress_count_value:
            uncompress_data = file_data[32+int_value:32+int_value+(decompress_count_value-len(decompress_data))]
            if uncompress_data:
                decompress_data = decompress_data + uncompress_data
        return decompress_data



def CLI_main():
    dat_path = input("请输入你的剧情dat路径，按e返回\n")
    if dat_path == 'e':
        print("返回中……\n")
        return
    while True:
        try:
            extract_iss = Iss2Txt()
            extract_iss.main_func(dat_path)
            print("返回中……\n")
            break
        except Exception as e:
            print(e)
            time.sleep(0.5)
            dat_path = input("请输入你的剧情dat路径，按e返回\n")
            if dat_path == 'e':
                print("返回中……\n")
                return
