# -*- coding: utf-8 -*-
import os

class Extract_file:

    def __init__(self):
        pass
        
    def main_func(self, dat_path):
        self.dat_path = dat_path
        if not self.check_magic():
            raise ValueError("提供的剧情dat文件路径或魔术头错误！")
        self.get_iss_data(self.get_fileinfo())
        print('iss文件已解压完毕')
        return self.iss_path

    def check_magic(self):
        if not os.path.exists(self.dat_path):
            return False
        with open(self.dat_path, 'rb') as f:
            if f.read(24) != b'\x49\x52\x49\x53\x50\x43\x4B\x00\x00\x00\x01\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00':
                return False
            else:
                return True
            
    def remove_zerozero(self, data):
        while data.endswith(b'\x00\x00'):
            data = data[:-2]
        return data
            
    def find_binary_pattern(self):

        pattern = b'\x73\x00\x63\x00\x65\x00\x6E\x00\x65\x00\x2F\x00\x69\x00\x73\x00\x73\x00\x00\x00'
        pattern_len = len(pattern)
        buffer_size = 4096
        overlap = pattern_len - 1
        match = 0
        
        with open(self.dat_path, 'rb') as f:
            prev_chunk = b''
            current_offset = 0
            
            while True:
                chunk = f.read(buffer_size)
                if not chunk:
                    break
                data = prev_chunk + chunk
                start_index = 0
                while start_index < len(data):
                    index = data.find(pattern, start_index)
                    if index == -1:
                        break
                    actual_offset = current_offset - len(prev_chunk) + index
                    match = actual_offset
                    start_index = index + 1
                prev_chunk = data[-overlap:] if overlap > 0 else b''
                current_offset += len(chunk)
        
        return match
        
    def get_fileinfo(self):
        iss_offset = self.find_binary_pattern()
        with open(self.dat_path, 'rb') as dat_fp:
            dat_fp.seek(iss_offset - 16)
            global_head_data = dat_fp.read(16)
            iss_path_length = int.from_bytes(global_head_data[8:12], byteorder='little', signed=False)
            self.iss_path = self.remove_zerozero(dat_fp.read(iss_path_length)).decode('utf-16le')
            os.makedirs(self.iss_path, exist_ok=True)
            iss_group_info = dat_fp.read(16)
            iss_num = int.from_bytes(iss_group_info[4:8], byteorder='little', signed=False)
            file_info_list = []
            file_offset = dat_fp.tell()
            for i in range(iss_num):
                file_info = {}
                file_info_data = dat_fp.read(32)
                file_info['pos'] = int.from_bytes(file_info_data[4:8],byteorder='little',signed=False) + file_offset
                file_info['real_data_size'] = int.from_bytes(file_info_data[8:12],byteorder='little',signed=False)
                file_info['data_size'] = int.from_bytes(file_info_data[12:16],byteorder='little',signed=False)
                file_info['name_length'] = int.from_bytes(file_info_data[16:20],byteorder='little',signed=False)
                file_info['encode_name'] = dat_fp.read(file_info['name_length'])
                file_info['decode_name'] = self.remove_zerozero(file_info['encode_name']).decode('utf-16le')
                file_info['file_path'] = os.path.join(self.iss_path, file_info['decode_name'])
                file_info_list.append(file_info)
        return file_info_list
    
    def get_iss_data(self, file_info_list):
        with open(self.dat_path, 'rb') as dat_fp:
            for file_info in file_info_list:
                dat_fp.seek(file_info['pos'])
                with open(file_info['file_path'], 'wb') as iss_fp:
                    iss_fp.write(dat_fp.read(file_info['data_size']))