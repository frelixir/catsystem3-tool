# -*- coding: utf-8 -*-
import os
import zlib
import time
import re
from .Repack_iss import Repack_Dat

class Txt2Iss:

    def __init__(self):
        self.end_block69 = b'\x20\x00\x00\x00\x00\x00\x00\x00\x69\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.end_block67 = b'\x20\x00\x00\x00\x20\x00\x00\x00\x67\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.end_block = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.issfile_head = b'\x49\x53\x53\x20'
        self.repack_dat = Repack_Dat()

    def main_func(self, source_path, org_dat, choose_flag):
        self.source_path = source_path
        self.org_dat = org_dat
        unused_re_flag = True
        if not os.path.exists(os.path.join(source_path, 'iss')):
            raise ValueError(f"不存在目标路径{os.path.join(source_path, 'iss')}")
        if not os.path.exists(os.path.join(source_path, 'cn_txt')):
            raise ValueError(f"不存在汉化txt路径{os.path.join(source_path, 'cn_txt')}，请把汉化好的txt放在这个路径")
        if os.path.exists(os.path.join(source_path, 'cn_re_txt')) and choose_flag == '1':
            unused_re_flag = False
        self.org_txt_folder = os.path.join(self.source_path, 'iss', 'txt')
        self.cn_txt_folder = os.path.join(self.source_path, 'cn_txt')
        ja_iss_folder = os.path.join(self.source_path, 'iss')
        bin_folder = os.path.join(self.source_path, 'iss', 'bin')
        self.re_txt_folder = os.path.join(self.source_path, 'cn_re_txt')
        os.makedirs('scene/new_iss', exist_ok=True)
        if not unused_re_flag:
            cn_re_txt_list = [file for file in os.listdir(self.re_txt_folder) if file.endswith('.txt')]
            if cn_re_txt_list:
                for txt_file in cn_re_txt_list:
                    self.repack_re_text(txt_file)
        cn_txt_list = [file for file in os.listdir(self.cn_txt_folder) if file.endswith('.txt')]
        for txt_file in cn_txt_list:
            cn_txt = os.path.join(self.cn_txt_folder, txt_file)
            ja_iss_file = os.path.join(ja_iss_folder, txt_file.replace('.txt', '.iss'))
            ja_bin_file = os.path.join(bin_folder, txt_file.replace('.txt', '.bin'))
            if not os.path.exists(ja_iss_file):
                print(f"不存在此文件{ja_iss_file}")
                continue
            cn_iss_name = os.path.join('scene/new_iss', txt_file.replace('.txt', '.iss'))
            cn_bin_file = os.path.join(bin_folder, txt_file.replace('.txt', '_cn.bin'))
            self.repack_main(cn_txt, ja_bin_file, cn_bin_file)
            self.compress_cn_data(cn_iss_name, ja_iss_file, cn_bin_file)
        self.repack_dat.main_func(self.source_path, self.org_dat)

    def load_translated_text(self, path):
        with open(path, 'r', encoding='utf-8-sig') as f:
            return [line.rstrip('\n') for line in f if line.strip()]
        
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
        
    def repack_re_text(self, filename):
        with open(os.path.join(self.org_txt_folder, filename), 'r', encoding='utf-16') as f:
            original_lines = f.readlines()

        cn_re_txt = os.path.join(self.re_txt_folder, filename)
        translated = self.load_translated_text(cn_re_txt)
        trans_idx = 0
        pattern = r'"(.*?)"'
        new_lines = []

        for line in original_lines:
            if trans_idx < len(translated):
                match = re.search(pattern, line)
                if match and self.has_cjk(match.group(0)):
                    line = re.sub(pattern, lambda m: translated[trans_idx], line, count=1)
                    trans_idx += 1
            new_lines.append(line)

        with open(os.path.join(self.cn_txt_folder, filename), "wb") as f:
            f.write(b'\xff\xfe')  # UTF-16LE BOM，只写一次
            for line in new_lines:
                f.write(line.encode("utf-16le"))

    def get_cn_text(self, cn_txt):
        with open(cn_txt, 'r', encoding='UTF-16') as cn_txt_file:
            cn_data_list = []
            while True:
                cn_text_data = cn_txt_file.readline()
                if not cn_text_data:
                    break
                cn_text_data = cn_text_data.strip('\n\n')
                if cn_text_data:
                    cn_data_list.append(cn_text_data)
            return cn_data_list

    def pad_binary_string(self, binary_data):
        # 获取当前长度
        current_length = len(binary_data)
        # 计算余数
        remainder = current_length % 16
        
        # 根据余数决定需要补充的数量
        if remainder <= 4:
            # 补充到余数为8
            padding_length = 8 - remainder
        elif 4 < remainder <= 8:
            # 补充到余数为0
            padding_length = 16 - remainder
        elif 8 < remainder <= 12:
            # 补充到余数为0
            padding_length = 16 - remainder
        else:  # 12 <= remainder < 16
            # 补充到下一个余数为8的位置
            padding_length = 24 - remainder
        
        # 补充指定数量的\x00
        padded_data = binary_data + b'\x00' * padding_length
        return padded_data

    def repack_main(self, cn_txt, ja_bin_file, cn_bin_file):
        count = 0
        cn_data_list = self.get_cn_text(cn_txt)
        with open(ja_bin_file, 'rb') as ja_bin, open(cn_bin_file, 'wb') as chs_bin:
            scene_head_count_data = ja_bin.read(4)
            scene_head_count = int.from_bytes(scene_head_count_data, byteorder='little', signed=False)
            scene_head_data = ja_bin.read(scene_head_count - 4)
            scene_data_count = int.from_bytes(scene_head_data[4:8], byteorder='little', signed=False) - scene_head_count
            scene_name = ja_bin.read(scene_data_count)
            group_info = ja_bin.read(8)
            group_count = int.from_bytes(group_info[4:8], byteorder='little', signed=False)
            chs_bin.write(scene_head_count_data)
            chs_bin.write(scene_head_data)
            chs_bin.write(scene_name)
            chs_bin.write(group_info)
            for i in range(group_count):
                start_pos = chs_bin.tell()
                text_group_head_count_data = ja_bin.read(4)
                text_group_head_count = int.from_bytes(text_group_head_count_data, byteorder='little', signed=False)
                text_group_head_data = bytearray(ja_bin.read(text_group_head_count - 4))
                text_group_size = int.from_bytes(text_group_head_data[0:4], byteorder='little', signed=False)
                if text_group_size == 0:
                    change_group_head = False
                else:
                    change_group_head = True
                text_group_info = ja_bin.read(8)
                text_num = int.from_bytes(text_group_info[4:8], byteorder='little', signed=False)
                chs_bin.write(text_group_head_count_data)
                chs_bin.write(text_group_head_data)
                chs_bin.write(text_group_info)
                for j in range(text_num):
                    text_head_count_data = ja_bin.read(4)
                    text_head_count = int.from_bytes(text_head_count_data, byteorder='little', signed=False)
                    text_head_data = ja_bin.read(text_head_count - 4)
                    text_data_size = int.from_bytes(text_head_data[0:4], byteorder='little', signed=False) - text_head_count
                    if text_head_data[4:8] == b'\x67\x00\x00\x00':
                        chs_bin.write(self.end_block67)
                        continue
                    if text_head_data[4:8] == b'\x69\x00\x00\x00':
                        if j != text_num - 1:
                            raise ValueError('出现语句组结尾异常！')
                        else:
                            ja_bin.read(32)
                            chs_bin.write(self.end_block69)
                            chs_bin.write(self.end_block)
                            continue
                    try:
                        cn_text_bytes = cn_data_list[count].encode('UTF-16LE')
                        cn_text_bytes = self.pad_binary_string(cn_text_bytes)
                        count += 1
                    except Exception as e:
                        raise ValueError(f'编码语句时出现问题: {e}')
                    text_data = ja_bin.read(text_data_size)
                    cn_text_length = len(cn_text_bytes)
                    new_length = (cn_text_length + text_head_count).to_bytes(4, byteorder='little', signed=False)
                    text_head_data = new_length + text_head_data[4:]
                    chs_bin.write(text_head_count_data)
                    chs_bin.write(text_head_data)
                    chs_bin.write(cn_text_bytes)
                end_pos = chs_bin.tell()
                if change_group_head:
                    # 获取长度
                    group_length = end_pos - start_pos
                    # 移动到写长度的地方
                    chs_bin.seek(start_pos + 4)
                    # 更新长度
                    chs_bin.write(group_length.to_bytes(4, byteorder='little', signed=False))
                    # 回到结尾
                    chs_bin.seek(end_pos)

    def compress_cn_data(self, cn_iss_name, ja_iss_file, cn_bin_file):
        with open(cn_bin_file, 'rb') as cn_data_file, open(cn_iss_name, 'wb') as cn_iss_file:
            cn_data = cn_data_file.read()
            cn_data_size = len(cn_data).to_bytes(4, byteorder='little', signed=False)
            compresser = zlib.compressobj(level=9)
            cn_compress_data = compresser.compress(cn_data) + compresser.flush()
            cn_com_data_size = len(cn_compress_data).to_bytes(4, byteorder='little', signed=False)
            cn_iss_file.write(self.issfile_head)
            with open(ja_iss_file, 'rb') as ja_iss_fp:
                ja_iss_fp.seek(20)
                jp_org_data = ja_iss_fp.read(12)
            cn_iss_file.write(b'\x20\x00\x00\x00')
            cn_iss_file.write(cn_com_data_size)
            cn_iss_file.write(cn_data_size)
            cn_iss_file.write(b'\x01\x00\x00\x00')
            cn_iss_file.write(jp_org_data)
            cn_iss_file.write(cn_compress_data)


def CLI_main():
    while True:
        source_path = input("请输入你存放iss的根文件夹，按e返回\n")
        if source_path == 'e':
            print("返回中……\n")
            return
        dat_path = input("请输入原剧情dat文件路径，按e返回\n")
        if dat_path == 'e':
            print("返回中……\n")
            return
        choose_flag = input("是否需要使用cn_re_txt文件夹的文本进行回封？会覆盖cn_txt文件夹中的同名txt(此功能用于防止纯修改命令文本被覆盖)\n1是启用2是关闭，按e返回\n")
        if choose_flag == 'e':
            print("返回中……\n")
            return
        elif choose_flag != '1' and choose_flag != '2':
            print("非法输入，请重新输入选择")
            continue
        try:
            repack_text = Txt2Iss()
            repack_text.main_func(source_path, dat_path, choose_flag)
            print("返回中……\n")
            break
        except Exception as e:
            print(e)
            time.sleep(0.5)
            continue