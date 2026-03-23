## Dat_file

```c++
bytes[24] magic = 'IRISPCK';

head structure1:
int structure_length; (一般是0x10)
int filegroup_length; (如果是最后一个文件组或者只有一个文件组这个值为0)
int folderpath_length; 
int totallength; (structure_length+folderpath_length)
data:
bytes[folderpath_length] folderpath; (UTF-16LE)

head structure2:
int structure_length;
int Number_of_files;
int Number_of_files*File_information_length;
int Unknown; (猜测也是时间戳，四字节，算回去都是1971年7月)

files_structure:
fileoffset = ftell(); (这里是在获取第一个文件信息前拿到的文件流偏移，后面不用随着文件信息的循环而更改，用这个加上后面的relative_pos可以求出文件实际偏移)
int structure_length; (一般是0x20)
int relative_pos; (pos = relative_pos + fileoffset)
int file_size without 0x00; (这个是文件去掉末尾的0x00后的长度)
int file_size; (这个是文件真实长度)
int filename_length;
bytes[8] Timestamp;  (这个是时间戳，应该是写入时的时间转换的，转换的参考代码在etc文件夹里)
int 0x00;
data:
bytes[filename_length] filename; (UTF-16LE)
files_data:
这片文件数据区域用上面结构体求出来的偏移和真实长度来获取对应的文件数据即可。
```

> 一个封包可能有多个也可能只有一个文件组，如果有多个文件组那就要按上面的结构循环提取，不然只能提取出第一个文件组。

## Iss_file

```c++
head_structure:
int magic = 'ISS';
int structure_length; (一般是0x20，包括前面四字节的magic头)
int compress_length; (Zlib 压缩方式)
int decompress_length; (Zlib decompressed data length or Zlib decompressed data length + uncompressed_data length)
int compress_flag; (0x01是启用压缩)
bytes[8] Timestamp; (这个是时间戳，应该是写入时的时间转换的，转换的参考代码在etc文件夹里);
bytes[4] Unknown; (基本固定为0x84F88F00)
data:
bytes[compress_length] file_data;
if remain:
bytes[file_size-ftell()] Uncompressed_data;
```

## Text for iss_decompress_data

```c++
head structure1:
int structure_length; (一般是0x10)
int 0x00;
int text_length;
int 0x00;
data:
bytes[text_length] Scene_name; (UTF-16LE)

Text group info(全局):
int Text group flag;
int Text group count;

循环次数(Text group count):

head structure2:
int structure_length; (一般是0x20)
int Text group length; (包括 head structure2, Text info, head structure3, data)
bytes[24] Unused data;

Text info:
int Text group flag;
int Text count;

循环次数(Text count):

head structure3:
int structure_length; (一般是0x20)
int total length; (structure_length + text_length)
bytes[8] Text type; (0x6500000001000000 是文本, 0x6400000001000000 是人名)
bytes[16] Unused data; (一般都是0x00)
data:
bytes[text_length] Text; (UTF-16LE) (text_length=total length - structure_length)
```

> 如果Header Structure2里Text Group Length的值为0x00,则这是这段数据里最后一个语句组。