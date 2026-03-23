# -*- coding: utf-8 -*-
import os
import time

class Repack2Dat:

    def __init__(self):
        self.global_pos = 24
        
    def main_func(self, dat_path):
        if not os.path.exists(os.path.join(os.getcwd(), 'cs3_extract_file')):
            raise ValueError("未检测到工作区下有cs3_extract_file文件夹，请先使用extract_file解压目标dat的所有文件再重封包")
        if not os.path.exists(os.path.join(os.getcwd(), 'Repack_file')):
            raise ValueError("未检测到工作区下有Repack_file文件夹，请把需要重封包的文件放到这个文件夹下再启动程序")
        os.makedirs(os.path.join(os.getcwd(), "Packed_dat"), exist_ok=True)
        packed_path = os.path.join(os.getcwd(), 'Packed_dat')
        new_dat_path = os.path.join(packed_path, os.path.basename(dat_path))
        try:
            self.get_structure(new_dat_path, dat_path)
            print("重封包已完成")
        except RuntimeError or ValueError:
            raise

    def get_structure(self, new_dat_path, old_dat_path):

        pos = self.global_pos
        pos1 = self.global_pos
        multi_flag = False
        old_dat_size = os.path.getsize(old_dat_path)
        with open(old_dat_path, 'rb') as old_fp:
            new_fp = open(new_dat_path, 'wb')
            new_fp.write(old_fp.read(pos))
            new_fp.close()
            old_fp.seek(0)
            while True:
                old_fp.seek(pos)
                global_head_data_count = old_fp.read(4)
                data_int = int.from_bytes(global_head_data_count, byteorder='little', signed=False)
                global_head_data = bytearray(old_fp.read(data_int - 4))
                data_group_length = int.from_bytes(global_head_data[0:4], byteorder='little', signed=False)
                if data_group_length != 0:
                    multi_flag = True
                else:
                    multi_flag = False
                head_name_length = int.from_bytes(global_head_data[(data_int // 2) - 4:data_int // 2], byteorder='little', signed=False)
                global_name_enc = old_fp.read(head_name_length)
                global_name = global_name_enc.replace(b'\x00\x00', b'').decode('utf-16le')
                global_name = os.path.join(os.getcwd(), "cs3_extract_file", global_name)
                if not os.path.exists(global_name):
                    raise ValueError(f"未检测到{global_name}存在！请先解包对应dat文件再重封包")
                head_data_count = old_fp.read(4)
                head_data_count_int = int.from_bytes(head_data_count, byteorder='little', signed=False)
                head_data = old_fp.read(head_data_count_int - 4)
                file_count = int.from_bytes(head_data[0:4], byteorder='little', signed=False)

                file_head_list = []
                file_offset = old_fp.tell()
                for i in range(file_count):
                    file_head = {}
                    file_head['size'] = old_fp.read(4)
                    file_head_count = int.from_bytes(file_head['size'], byteorder='little', signed=False)
                    file_head_data = old_fp.read(file_head_count - 4)
                    file_head['pos'] = int.from_bytes(file_head_data[0:4], byteorder='little', signed=False) + file_offset
                    file_head['real_data_size'] = int.from_bytes(file_head_data[4:8], byteorder='little', signed=False)
                    file_head['data_size'] = int.from_bytes(file_head_data[8:12], byteorder='little', signed=False)
                    file_head['name_length'] = int.from_bytes(file_head_data[12:16], byteorder='little', signed=False)
                    file_head['other_data'] = file_head_data[16:28]
                    file_head['name'] = old_fp.read(file_head['name_length'])
                    file_head['decode_name'] = file_head['name'].replace(b'\x00', b'').decode('utf-8')
                    file_head_list.append(file_head)
                
                byte_block = global_head_data_count + global_head_data + global_name_enc + head_data_count + head_data

                if multi_flag:
                    new_file_list, new_data_group_length = self.get_new_list(file_head_list, global_name)
                    for file_tmp_dict in new_file_list:
                        new_data_group_length += int.from_bytes(file_tmp_dict["size"],byteorder="little",signed=False) + file_tmp_dict["name_length"]
                    new_data_group_length += 32 + head_name_length
                    global_head_data[0:4] = new_data_group_length.to_bytes(4, byteorder="little", signed=False)
                    byte_block = global_head_data_count + global_head_data + global_name_enc + head_data_count + head_data
                    new_file_list, tmp_pos = self.write_new_head(new_file_list, new_dat_path, byte_block)
                    positions = self.write_file_data(new_file_list, new_dat_path)
                    self.update_pos(positions, new_file_list, new_dat_path, tmp_pos, global_name)
                    pos = pos + data_group_length
                    pos1 = pos1 + new_data_group_length
                    if not pos < old_dat_size:
                        break
                    else:
                        continue
                else:
                    new_file_list, new_data_group_length = self.get_new_list(file_head_list, global_name)
                    for file_tmp_dict in new_file_list:
                        new_data_group_length += int.from_bytes(file_tmp_dict["size"],byteorder="little",signed=False) + file_tmp_dict["name_length"]
                    new_data_group_length += 32 + head_name_length
                    byte_block = global_head_data_count + global_head_data + global_name_enc + head_data_count + head_data
                    new_file_list, tmp_pos = self.write_new_head(new_file_list, new_dat_path, byte_block)
                    positions = self.write_file_data(new_file_list, new_dat_path)
                    self.update_pos(positions, new_file_list, new_dat_path, tmp_pos, global_name)
                    break

            
    def get_new_list(self, file_head_list, global_name):
        new_data_length = 0
        new_root_path = os.path.join(os.getcwd(), "Repack_file")
        old_root_path = global_name
        if not os.path.exists(old_root_path):
            raise ValueError(f"不存在这个路径{old_root_path}")
        for org_head in file_head_list:
            new_file_path = os.path.join(new_root_path, org_head['decode_name'])
            old_file_path = os.path.join(old_root_path, org_head['decode_name'])
            if os.path.exists(new_file_path):
                print(f"Packing {new_file_path}……")
                with open(new_file_path, 'rb') as new_iss_file:
                    org_head['iss_path'] = new_file_path
                    content = new_iss_file.read()
                    new_data_length += os.path.getsize(new_file_path)
                    org_head['data_size'] = len(content)
                    org_head['real_data_size'] = len(content.rstrip(b'\x00'))
                continue
            elif os.path.exists(old_file_path):
                org_head['iss_path'] = old_file_path
                new_data_length += os.path.getsize(old_file_path)
                continue
            else:
                raise ValueError(f"此文件不存在: {old_file_path}")
        return file_head_list, new_data_length

    def write_new_head(self, new_filehead_list, new_dat_path, byte_block):
        with open(new_dat_path, 'ab') as new_dat_file:
            new_dat_file.write(byte_block)
            tmp_pos = new_dat_file.tell()
            for new_head in new_filehead_list:
                new_dat_file.write(new_head['size'])
                new_head['head_pos'] = new_dat_file.tell()
                new_dat_file.write(new_head['pos'].to_bytes(4, byteorder='little', signed=False))
                new_dat_file.write(new_head['real_data_size'].to_bytes(4, byteorder='little', signed=False))
                new_dat_file.write(new_head['data_size'].to_bytes(4, byteorder='little', signed=False))
                new_dat_file.write(new_head['name_length'].to_bytes(4, byteorder='little', signed=False))
                new_dat_file.write(new_head['other_data'])
                new_dat_file.write(new_head['name'])
        return new_filehead_list, tmp_pos


    def write_file_data(self, new_filehead_list, scene_dat_path):
        positios = []
        with open(scene_dat_path, 'ab') as new_dat_file:
            for file_head in new_filehead_list:
                with open(file_head['iss_path'], 'rb') as iss_file:
                    positios.append(new_dat_file.tell())
                    new_dat_file.write(iss_file.read())
        return positios

    def update_pos(self, positions, file_head_list, scene_dat_path, tmp_pos, global_name):
        with open(scene_dat_path, 'rb+') as new_dat_file:
            for pos, file_head in zip(positions, file_head_list):
                new_dat_file.seek(file_head['head_pos'])
                pos = pos - tmp_pos
                if pos < 0:
                    raise ValueError("更新文件偏移失败")
                new_dat_file.write(pos.to_bytes(4, byteorder='little', signed=False))

def CLI_main():
    try:
        repack_dat = Repack2Dat()
    except Exception as e:
        print(e)
        time.sleep(0.5)
        print("返回中……\n")
        return
    dat_path = input("请输入你要重封包的dat文件路径，按e返回\n")
    if dat_path == 'e':
        print("返回中……\n")
        return
    try:
        repack_dat.main_func(dat_path)
        print("返回中……\n")
    except Exception as e:
        print(e)
        time.sleep(0.5)
        print("返回中……\n")
        return
