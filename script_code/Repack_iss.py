# -*- coding: utf-8 -*-
import os

class Repack_Dat:

    def __init__(self):
        self.iss_dat_magic = b'\x73\x00\x63\x00\x65\x00\x6E\x00\x65\x00\x2F\x00\x69\x00\x73\x00\x73\x00\x00\x00\x00\x00\x00\x00'

    def main_func(self, source_path, org_dat_path):
        self.source_path = source_path
        self.org_dat = org_dat_path
        if not self.check_magic():
            raise ValueError("提供的剧情dat文件路径或魔术头错误！")
        new_dat_folder = os.path.join(os.getcwd(), 'Packed_dat')
        os.makedirs(new_dat_folder, exist_ok=True)
        self.global_pos = self.find_pattern_offset(self.org_dat)
        if not self.global_pos:
            raise ValueError("没有在提供的dat文件里找到剧本文件组，请检查输入的dat文件\n")
        self.global_pos -= 16
        self.new_dat_path = os.path.join(new_dat_folder, os.path.basename(self.org_dat))
        self.src_path = os.path.join(self.source_path, 'iss')
        self.dst_path = os.path.join(self.source_path, 'new_iss')
        print("重封包dat中……")
        self.get_structure()
        print(f"重封包已完成！重封包文件在{new_dat_folder}下")

    def find_pattern_offset(self, scene_dat, chunk_size: int = 4096):
        file_obj = open(scene_dat, 'rb')
        pattern = self.iss_dat_magic
        pattern_len = len(pattern)
        if pattern_len == 0:
            return None
        file_obj.seek(0)
        overlap = pattern_len - 1
        previous_tail = b""
        position = 0
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            data = previous_tail + chunk
            idx = data.find(pattern)
            if idx != -1:
                return position - len(previous_tail) + idx
            previous_tail = data[-overlap:] if overlap > 0 else b""
            position += len(chunk)
        file_obj.close()
        return None
    
    def get_structure(self):

        pos = self.global_pos
        pos1 = self.global_pos
        file_size = os.path.getsize(self.org_dat)

        with open(self.org_dat, 'rb') as old_fp:
            with open(self.new_dat_path, 'wb') as new_fp:
                new_fp.write(old_fp.read(pos))
            global_head_data_count = old_fp.read(4)
            data_int = int.from_bytes(global_head_data_count, byteorder='little', signed=False)
            global_head_data = bytearray(old_fp.read(data_int - 4))
            data_group_length = int.from_bytes(global_head_data[0:4], byteorder='little', signed=False)
            if data_group_length == 0:
                over_flag = True
            else:
                over_flag = False
            head_name_length = int.from_bytes(global_head_data[(data_int // 2) - 4:data_int // 2], byteorder='little', signed=False)
            global_name_enc = old_fp.read(head_name_length)
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
            new_file_list, new_data_group_length = self.get_new_list(file_head_list)
            for file_tmp_dict in new_file_list:
                new_data_group_length += int.from_bytes(file_tmp_dict["size"],byteorder="little",signed=False) + file_tmp_dict["name_length"]
            new_data_group_length += 32 + head_name_length
            if not over_flag:
                global_head_data[0:4] = new_data_group_length.to_bytes(4, byteorder="little", signed=False)
            byte_block = global_head_data_count + global_head_data + global_name_enc + head_data_count + head_data
            new_file_list, tmp_pos = self.write_new_head(new_file_list, byte_block)
            positions = self.write_file_data(new_file_list)
            self.update_pos(positions, new_file_list, tmp_pos)
            pos = pos + data_group_length
            pos1 = pos1 + new_data_group_length
            if over_flag or pos >= file_size:
                return
            else:
                old_fp.seek(pos)
                with open(self.new_dat_path, 'ab') as new_fp:
                    new_fp.write(old_fp.read())
                print("已把除iss文件组部分写入")

    def get_new_list(self, file_head_list):
        new_data_length = 0
        for org_head in file_head_list:
            new_iss_path = os.path.join(self.dst_path, org_head['decode_name'])
            old_iss_path = os.path.join(self.src_path, org_head['decode_name'])
            if os.path.exists(new_iss_path):
                new_data_length += os.path.getsize(new_iss_path)
                with open(new_iss_path, 'rb') as new_iss_fp:
                    org_head['iss_path'] = new_iss_path
                    content = new_iss_fp.read()
                    org_head['data_size'] = len(content)
                    org_head['real_data_size'] = len(content.rstrip(b'\x00'))
                continue
            elif os.path.exists(old_iss_path) and not os.path.exists(new_iss_path):
                new_data_length += os.path.getsize(old_iss_path)
                org_head['iss_path'] = old_iss_path
                continue
            else:
                raise ValueError(f"存在文件错误，请先检查一下这个文件是否存在: {org_head['decode_name']}")
        return file_head_list, new_data_length

    def write_new_head(self, new_filehead_list, byte_block):
        with open(self.new_dat_path, 'ab') as new_dat_file:
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

    def write_file_data(self, new_filehead_list):
        positios = []
        with open(self.new_dat_path, 'ab') as new_dat_file:
            for file_head in new_filehead_list:
                with open(file_head['iss_path'], 'rb') as iss_file:
                    positios.append(new_dat_file.tell())
                    new_dat_file.write(iss_file.read())
        return positios

    def update_pos(self, positions, file_head_list, tmp_pos):
        with open(self.new_dat_path, 'rb+') as new_dat_file:
            for pos, file_head in zip(positions, file_head_list):
                new_dat_file.seek(file_head['head_pos'])
                pos = pos - tmp_pos
                if pos < 0:
                    raise ValueError('dat文件更新位移出现问题！')
                new_dat_file.write(pos.to_bytes(4, byteorder='little', signed=False))

    def check_magic(self):
        if not os.path.exists(self.org_dat):
            return False
        with open(self.org_dat, 'rb') as f:
            if f.read(24) != b'\x49\x52\x49\x53\x50\x43\x4B\x00\x00\x00\x01\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00':
                return False
            else:
                return True
