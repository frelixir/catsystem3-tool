# -*- coding: utf-8 -*-
import sys
import ctypes
import os
import icon

from GUI import Ui_Form
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget
from PyQt5.QtGui import QIcon, QFont

from script_code.extract_iss2json import Extract_text
from script_code.extract_iss2txt import Iss2Txt
from script_code.repack_json2iss import Repack_Text
from script_code.repack_txt2iss import Txt2Iss
from package_code.extract_file import Extract_Dat
from package_code.repack_file import Repack2Dat

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class GUI(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        ## 设置UI界面
        self.setupUi(self)
        self.setFixedSize(647, 457)
        ## 绑定信号槽
        self.iss2json_button.clicked.connect(self.iss2json_main)
        self.iss2txt_button.clicked.connect(self.iss2txt_main)
        self.txt2iss_button.clicked.connect(self.txt2iss_main)
        self.json2iss_button.clicked.connect(self.json2iss_main)
        self.iss2json_usage.clicked.connect(self.iss2json_usage_func)
        self.iss2txt_usage.clicked.connect(self.iss2txt_usage_func)
        self.ext_button.clicked.connect(self.ext_main)
        self.rpk_button.clicked.connect(self.rpk_main)
        self.usage.clicked.connect(self.usage_func)
        self.msg_box.setFont(QFont("SimSun", 13))
        self.msg_box.setPlainText("Written by 听一场风雪\n本界面没做多线程/多进程，使用的时候出现无响应是正常现象，等他处理完了就恢复了。")
        ## 接入功能类
        self.i2j = Extract_text()
        self.i2t = Iss2Txt()
        self.j2i = Repack_Text()
        self.t2i = Txt2Iss()
        self.ext = Extract_Dat()
        self.rpk = Repack2Dat()
    
    def iss2json_main(self):
        text = '请选择提取的json格式'
        button1_text = '原json格式'
        button2_text = 'vnt格式'
        choose_flag = self.messagebox_for_chooseflag(text, button1_text, button2_text)
        if choose_flag == '1':
            vnt_flag = False
            file_path = QFileDialog.getOpenFileName(self, directory="./", filter="*.dat", caption="选择你的剧本dat文件")
        elif choose_flag == '2':
            vnt_flag = True
            file_path = QFileDialog.getOpenFileName(self, directory="./", filter="*.dat", caption="选择你的剧本dat文件")
        if file_path[0]:
            file_path = file_path[0]
            try:
                self.i2j.main_func(file_path, vnt_flag)
                self.msg_box.append("\n已提取完所有文本，json在剧本文件夹下的json文件夹里")
            except Exception as e:
                self.msg_box.append(f"\n提取文本失败，问题: {e}")

    def iss2txt_main(self):
        file_path = QFileDialog.getOpenFileName(self, directory="./", filter="*.dat", caption="选择你的剧本dat文件")
        if file_path[0]:
            file_path = file_path[0]
            try:
                self.i2t.main_func(file_path)
                self.msg_box.append("\n已提取完所有文本，txt在剧本文件夹下的txt文件夹里，正则文本在cn_re_txt文件夹里")
            except Exception as e:
                self.msg_box.append(f"\n提取文本失败，问题: {e}")

    def json2iss_main(self):
        text = '请选择回封的json格式'
        button1_text = '原json格式'
        button2_text = 'vnt格式'
        choose_flag = self.messagebox_for_chooseflag(text, button1_text, button2_text)
        if choose_flag == '1':
            vnt_flag = False
            scene_path = QFileDialog.getExistingDirectory(self, caption='选择剧本根目录', directory='./')
        elif choose_flag == '2':
            vnt_flag = True
            scene_path = QFileDialog.getExistingDirectory(self, caption='选择剧本根目录', directory='./')
        if scene_path:
            dat_path = QFileDialog.getOpenFileName(self, directory='./', filter='*.dat', caption="选择原剧本dat文件")
            if dat_path[0]:
                dat_path = dat_path[0]
                try:
                    self.j2i.main_func(scene_path, dat_path, vnt_flag)
                    self.msg_box.append("\n回封文本成功！")
                except Exception as e:
                    self.msg_box.append(f"\n回封json文本失败，问题: {e}")

    def txt2iss_main(self):
        text = '是否需要使用cn_re_txt文件夹的文本进行回封？会覆盖cn_txt文件夹中的同名txt(此功能用于防止纯修改命令文本被覆盖)'
        button1_text = '是'
        button2_text = '否'
        choose_flag = self.messagebox_for_chooseflag(text, button1_text, button2_text)
        if choose_flag:
            scene_path = QFileDialog.getExistingDirectory(self, caption='选择剧本根目录', directory='./')
            if scene_path:
                dat_path = QFileDialog.getOpenFileName(self, directory='./', filter='*.dat', caption="选择原剧本dat文件")
                if dat_path[0]:
                    dat_path = dat_path[0]
                    try:
                        self.t2i.main_func(scene_path, dat_path, choose_flag)
                        self.msg_box.append("\n回封文本成功！")
                    except Exception as e:
                        self.msg_box.append(f"\n回封txt文本失败，问题: {e}")

    def iss2json_usage_func(self):
        self.msg_box.append('\n功能说明: \n提取时请选择你需要提取文本的剧情dat，该功能会自动提取出文本在剧本路径的json文件夹下，汉化或改动后请放在剧本根目录(例如/scene/)下的cn_json文件夹。(关于json格式请看readme)\n回封时需要先选择剧本根目录(例如scene/iss这种路径就选择scene文件夹)，其次再选取源文本存在的dat文件。')

    def iss2txt_usage_func(self):
        self.msg_box.append('\n功能说明: \n提取时请选择你需要提取文本的剧情dat，该功能会自动提取出所有脚本命令与文本在剧本路径的txt文件夹下，然后提取纯文本在cn_re_txt文件夹下，只改动文本可以在cn_re_txt文件夹里改txt文件，如需改动命令需要在剧本路径的txt文件夹里改对应txt并放到cn_txt文件夹。\n回封时需要先选择存放iss的根文件夹(例如scene/iss这种路径就选择scene文件夹)，其次再选取原剧情dat文件。')

    def ext_main(self):
        text = '请选择你需要的解包模式'
        button1_text = '解包文件'
        button2_text = '解包文件信息表'
        choose_flag = self.messagebox_for_chooseflag(text, button1_text, button2_text)
        if choose_flag == '1':
            file_path = QFileDialog.getOpenFileNames(self, directory="./", filter="*.dat")
            if file_path[0]:
                file_path = file_path[0]
                try:
                    self.ext.main_func(choose_flag, file_path)
                    self.msg_box.append("\n已提取完所有文件，放在程序目录下cs3_extract_file文件夹里")
                except Exception as e:
                    self.msg_box.append(f"\n提取文件失败，问题: {e}")
        if choose_flag == '2':
            file_path = QFileDialog.getOpenFileNames(self, directory="./", filter="*.dat")
            if file_path[0]:
                file_path = file_path[0]
                try:
                    self.ext.main_func(choose_flag, file_path)
                    self.msg_box.append("\n已提取完文件清单，放在程序目录下fileinfo_list文件夹里")
                except Exception as e:
                    self.msg_box.append(f"\n提取文件失败，问题: {e}")

    def rpk_main(self):
        file_path = QFileDialog.getOpenFileName(self, directory="./", filter="*.dat")
        if file_path[0]:
            file_path = file_path[0]
            try:
                self.rpk.main_func(file_path)
                self.msg_box.append("\n已回封完毕，新dat文件在程序目录下Packed_dat文件夹里")
            except Exception as e:
                self.msg_box.append(f"\n回封文件失败，问题: {e}")
        
    def usage_func(self):
        self.msg_box.append('\n功能说明: \n提取时请选择你需要解包的dat文件，该功能会自动提取此dat文件中所有的文件放在程序目录的cs3_extract_file文件夹下。\n回封时需要先把重封包的文件放在程序目录下的Repack_file文件夹里，再选择你需要重封包的dat文件。要注意重封包前必须先解包这个dat获得所有文件。')
    
    def messagebox_for_chooseflag(self, text, button1_text, button2_text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('选择')
        msg_box.setText(text)
        button_option1 = msg_box.addButton(button1_text, QMessageBox.YesRole)
        button_option2 = msg_box.addButton(button2_text, QMessageBox.NoRole)
        msg_box.setDefaultButton(button_option1)
        msg_box.exec_()
        if msg_box.clickedButton() == button_option1:
            return '1'
        elif msg_box.clickedButton() == button_option2:
            return '2'

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        window = GUI()
    except Exception as e:
        msg_box = QWidget()
        QMessageBox.information(msg_box, '提醒', f'窗口运行错误，即将退出\n问题: {e}')
        QApplication.quit()
        sys.exit()
    window.setWindowTitle("cs3工具箱")
    window.setWindowIcon(QIcon(str(':/icon.png')))
    ## Windows系统下设置任务栏图标
    if sys.platform == "win32":
        myappid = "200214"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    ## 显示窗口
    window.show()
    sys.exit(app.exec_())
