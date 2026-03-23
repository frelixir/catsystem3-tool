# -*- coding: utf-8 -*-
import sys

import script_code.extract_iss2json as iss2json
import script_code.extract_iss2txt as iss2txt
import script_code.repack_json2iss as json2iss
import script_code.repack_txt2iss as txt2iss
import package_code.extract_file as ext_file
import package_code.repack_file as rpk_file

if __name__ == '__main__':
    print("Written by 听一场风雪")
    while True:
        print("请选择你要使用的程序:\n1.解包文本成json\n2.json文本回封\n3.解包文本成txt(包括脚本命令)\n4.txt文本回封\n5.解包dat\n6.dat回封\ne.退出程序")
        choice = input("")
        if choice == '1':
            iss2json.CLI_main()
        elif choice == '2':
            json2iss.CLI_main()
        elif choice == '3':
            iss2txt.CLI_main()
        elif choice == '4':
            txt2iss.CLI_main()
        elif choice == '5':
            ext_file.CLI_main()
        elif choice == '6':
            rpk_file.CLI_main()
        elif choice == 'e':
            sys.exit()
        else:
            print("检测到非法参数，请重新输入\n")
            continue