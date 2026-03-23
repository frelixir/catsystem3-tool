# -*- coding: utf-8 -*-
import os
import time
import json

class Extract_Dat:

    def __init__(self):
        self.global_pos = 24
        self.global_filepath = os.path.join(os.getcwd(), 'cs3_extract_file')

    def main_func(self, choose_flag, dat_path):
        if type(dat_path) == list:
            count = 0
            exists_path = []
            for dat_file in dat_path:
                if not self.check_magic(dat_file):
                    count += 1
                    continue
                else:
                    exists_path.append(dat_file)
            if count == len(dat_path):
                raise ValueError(f"输入的dat文件或路径{dat_file}有问题，请重新检查")
            else:
                dat_path = exists_path
        else:
            if not self.check_magic(dat_path):
                raise ValueError(f"输入的dat文件或路径{dat_path}有问题，请重新检查")
        if choose_flag == "1":
            os.makedirs(self.global_filepath, exist_ok=True)
            extract_flag = True
            if type(dat_path) == list:
                for path in dat_path:
                    self.get_structure(extract_flag, path)
            else:
                self.get_structure(extract_flag, dat_path)
            os.makedirs(os.path.join(os.getcwd(), "Repack_file"), exist_ok=True)
            print(f"解压文件完成，在{self.global_filepath}下，如果有重封包需要的请把新文件放在Repack_file文件夹里")
        elif choose_flag == "2":
            os.makedirs(os.path.join(os.getcwd(), 'fileinfo_list'), exist_ok=True)
            extract_flag = False
            if type(dat_path) == list:
                for path in dat_path:
                    self.get_structure(extract_flag, path)
            else:
                self.get_structure(extract_flag, dat_path)
            print(f"提取文件清单完成，放在{os.path.join(os.getcwd(), 'fileinfo_list')}文件夹下")
        else:
            raise ValueError("解包模式输入异常，重新选择解包模式")

    def get_structure(self, extract_flag, dat_path):

        pos = self.global_pos
        multi_flag = False

        with open(dat_path, 'rb') as file:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(pos)
            if not extract_flag:
                file_list_json = {}
            while True:
                file.seek(pos)
                global_head_data_count = file.read(4)
                data_int = int.from_bytes(global_head_data_count, byteorder='little', signed=False)
                global_head_data = file.read(data_int - 4)
                data_group_length = int.from_bytes(global_head_data[0:4], byteorder='little', signed=False)
                if data_group_length != 0:
                    multi_flag = True
                else:
                    multi_flag = False
                head_name_length = int.from_bytes(global_head_data[(data_int // 2) - 4:data_int // 2], byteorder='little', signed=False)
                global_name0 = file.read(head_name_length).replace(b'\x00', b'').decode('utf-8')
                global_name = os.path.join(self.global_filepath, global_name0)
                if extract_flag:
                    os.makedirs(global_name, exist_ok=True)
                head_data_count = file.read(4)
                head_data_count_int = int.from_bytes(head_data_count, byteorder='little', signed=False)
                head_data = file.read(head_data_count_int - 4)
                file_count = int.from_bytes(head_data[0:4], byteorder='little', signed=False)

                file_head_list = []
                file_offset = file.tell()
                for i in range(file_count):
                    file_head = {}
                    file_head_count = int.from_bytes(file.read(4), byteorder='little', signed=False)
                    file_head_data = file.read(file_head_count - 4)
                    file_head['pos'] = int.from_bytes(file_head_data[0:4], byteorder='little', signed=False) + file_offset
                    file_head['real_data_size'] = int.from_bytes(file_head_data[4:8], byteorder='little', signed=False)
                    file_head['data_size'] = int.from_bytes(file_head_data[8:12], byteorder='little', signed=False)
                    file_head['name_length'] = int.from_bytes(file_head_data[12:16], byteorder='little', signed=False)
                    file_head['name'] = global_name + '/' + file.read(file_head['name_length']).replace(b'\x00\x00', b'').decode('utf-16le')
                    file_head_list.append(file_head)
                
                if multi_flag:
                    if extract_flag:
                        self.get_data(file_head_list, dat_path)
                    else:
                        file_name_list = self.get_file_list(file_head_list)
                        file_list_json[global_name0] = file_name_list
                    pos = pos + data_group_length
                    if not pos < file_size:
                        if not extract_flag:
                            self.write_filelist(file_list_json, dat_path)
                        break
                    else:
                        continue
                else:
                    if extract_flag:
                        return self.get_data(file_head_list, dat_path)
                    else:
                        file_name_list = self.get_file_list(file_head_list)
                        file_list_json[global_name0] = file_name_list
                        return self.write_filelist(file_list_json, dat_path)
                    
    def get_data(self, file_head_list, dat_path):
        with open(dat_path, 'rb') as file:
            for file_head in file_head_list:
                file.seek(file_head['pos'])
                file_data = file.read(file_head['data_size'])
                file_name = file_head['name']
                with open(file_name, 'wb') as f:
                    f.write(file_data)

    def get_file_list(self, file_head_list):
        os.makedirs(os.path.join(os.getcwd(), 'fileinfo_list'), exist_ok=True)
        file_name_list = []
        for head_dict in file_head_list:
            file_head_dict = {}
            file_head_dict["filename"] = os.path.basename(head_dict["name"])
            file_head_dict["size"] = head_dict["data_size"]
            file_name_list.append(file_head_dict)
        return file_name_list
        
    def write_filelist(self, file_list_json, dat_path):
        with open(os.path.join(os.getcwd(), f"fileinfo_list/{os.path.basename(dat_path).replace('.dat', '.json')}"), 'a', encoding='utf-8') as f:
            json.dump(file_list_json, f, ensure_ascii=False, indent=4)

    def check_magic(self, dat_path):
        if not os.path.exists(dat_path):
            return False
        with open(dat_path, 'rb') as f:
            if f.read(24) != b'\x49\x52\x49\x53\x50\x43\x4B\x00\x00\x00\x01\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00':
                return False
            else:
                return True


def CLI_main():
    print("你已进入解包程序，此程序循环执行，若要返回上层选择请按e")
    while True:
        choose_flag = input("请选择操作，1是解包文件，2是提取文件列表(不解压)，e是返回\n")
        if choose_flag == 'e':
            print("返回中……\n")
            break
        dat_path = input('请输入dat路径')
        extract_dat = Extract_Dat()
        try:
            extract_dat.main_func(choose_flag, dat_path)
        except Exception as e:
            print(e)
            time.sleep(0.5)
            continue