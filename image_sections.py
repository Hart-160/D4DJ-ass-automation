import cv2
from numpy import array, count_nonzero, argmax, pi
from PySide2.QtCore import QObject, Signal

import settings_handler as sh

'''
这个部分负责分析视频
'''

class ImageData(object):
    '''
    对一帧进行对话框和文字判定
    '''
    def __init__(self, image, lower_range, upper_range, white_threshold, 
                 width, height,
                 word_points:tuple, border_points:tuple) -> None:
        self.x1b, self.y1b, self.x2b, self.y2b = border_points
        self.x1w, self.y1w, self.x2w, self.y2w = word_points
        
        self.width = width
        self.height = height
        
        self.image = image
        self.gray = self.image[int(self.height*float(sh.Reference.reference_reader(sh.Reference.TEMPLATE_DETECT_CUT_FACTOR, width, height))):self.height, 0:self.width]
        # self.gray = self.image[self.y1w:self.y2w, self.x1b-4:self.x2b+4] #定位法
        self.gray = cv2.cvtColor(self.gray, cv2.COLOR_BGR2GRAY)
        self.lower = lower_range
        self.upper = upper_range
        self.white_threshold = white_threshold
        self.word = bool(False)
        self.dialogue = bool(False)

    '''
    def __read_pixel(frame, x1, x2, y1, y2):
        #判断四个点是否为白色，如果四个都是，返回true，否则返回false
        yes = 0
        is_dialogue = False
        if frame[y1, x1] == 255:
            yes += 1
        if frame[y2, x1] == 255:
            yes += 1
        if frame[y1, x2] == 255:
            yes += 1
        if frame[y2, x2] == 255:
            yes += 1
        if yes == 4:
            is_dialogue = True
        return is_dialogue
    
    def __is_valid_color(self) -> bool:
        #判断对话框的颜色部分（常规状况下为紫色）
        dialogue = bool(False)

        im = self.image
        im = im[self.y1b:self.y2b, self.x1b:self.x2b]
        fhsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        self.border_color = {'x1':str(fhsv[0, 0]), 'x2':str(fhsv[self.y2b-self.y1b-1, 0]), 'x3':str(fhsv[0, self.x2b-self.x1b-1]), 'x4':str(fhsv[self.y2b-self.y1b-1, self.x2b-self.x1b-1])}
        mask = cv2.inRange(fhsv, array(self.lower), array(self.upper))
        im = cv2.bitwise_and(im, im, mask=mask)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        ret, im = cv2.threshold(im, 80, 255, cv2.THRESH_BINARY)
        read_result = ImageData.__read_pixel(im, 0, self.x2b-self.x1b-1, 0, self.y2b-self.y1b-1)
        if read_result:
            dialogue = bool(True)
        return dialogue

    def __is_valid_white(self):
        #判断对话框外圈的白色部分
        white = bool(False)
        self.border_white = {'x1':str(self.gray[self.y1b-self.y1w-1, 0]), 'x2':str(self.gray[self.y2b-self.y1w-1, 0]), 'x3':str(self.gray[self.y1b-self.y1w-1, self.x2b-self.x1b+7]), 'x4':str(self.gray[self.y2b-self.y1w-1, self.x2b-self.x1b+7])}
        ret, gray = cv2.threshold(self.gray, int(self.white_threshold), 255, cv2.THRESH_BINARY)
        read_result = ImageData.__read_pixel(gray, 0, self.x2b-self.x1b+7, self.y1b-self.y1w-1, self.y2b-self.y1w-1)
        if read_result:
            white = bool(True)
        return white

    def is_dialogue(self):
        #定位点颜色识别法
        #结合颜色判定&白色判定输出对话框判定结果
        
        self.valid_color = ImageData.__is_valid_color(self)
        self.valid_white = ImageData.__is_valid_white(self)
        self.dialogue = self.valid_color and self.valid_white
        return self.dialogue
    #'''

    #'''
    def set_canny(self, canny):
        self.tmp_canny = canny
    
    def is_dialogue(self):
        #模板匹配法
        self.dialogue = bool(False)
        frame_canny = cv2.Canny(self.gray, 50, 150)
        res = cv2.matchTemplate(frame_canny, self.tmp_canny, 5)
        loc = divmod(argmax(res), res.shape[1])
        
        if not (res[loc[0], loc[1]] < 0.3):
            self.dialogue = bool(True)
        return self.dialogue
    #'''

    def is_word(self) -> bool:
        #判断文字
        '''if not self.dialogue:
            return self.word'''
        #img = self.gray[0:self.y2w-self.y1w-1, self.x1w-self.x1b+3:self.x2w-self.x1b+3] #定位法
        img = self.image[self.y1w:self.y2w, self.x1w:self.x2w] #直线法
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, img = cv2.threshold(img, 80, 255, cv2.THRESH_BINARY_INV)
        if count_nonzero(img) >= 50:
            self.word = bool(True)
        return self.word

    def get_detailed_data(self, f, ms):
        #获得详细数据
        #return {'Frame':f, 'MiliSecond':ms, 'IsValidColor':self.valid_color, 'IsValidWhite':self.valid_white,'IsWord':self.word, 'BorderColor':self.border_color, 'BorderWhite':self.border_white} #定位法
        return {'Frame':f, 'MiliSecond':ms, 'IsDialogue':self.dialogue,'IsWord':self.word} #直线法

class ImageSections(QObject):
    update_bar = Signal(int) #向GUI发送进度，更新进度条
    setmax = Signal(int)  #向GUI发送进度条最大值，并设置

    def __Merge(dict1, dict2): 
        res = {**dict1, **dict2} 
        return res 

    def get_template_canny(template_route):
        tmp = cv2.imread(template_route)
        tmp = cv2.cvtColor(tmp, cv2.COLOR_BGR2GRAY)
        tmp_canny = cv2.Canny(tmp, 50, 150)
        return tmp_canny

    def image_section_generator(vid, width, height):
        '''
        输入视频路径，返回一个包含各节点的列表
        '''
        cap = cv2.VideoCapture(vid)
        total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        pb.setmax.emit(total_frame)

        image_sections = []
        word_count = 1

        # data_li是拿来输出更详细的视频读取数据的
        #data_li = []

        #border
        border_points = sh.Reference.box_splitter(sh.Reference.reference_reader(sh.Reference.TEXT_BORDER_MX, width, height))

        #dialogue
        word_points = sh.Reference.box_splitter(sh.Reference.reference_reader(sh.Reference.TEXT_WORD_MX, width, height))
        
        #读取设置传入ImageData构造器
        lower_r = sh.Settings.hsv_range_splitter(sh.Settings.settings_reader(sh.Settings.DEFAULT_LOWER_RANGE))
        upper_r = sh.Settings.hsv_range_splitter(sh.Settings.settings_reader(sh.Settings.DEFAULT_UPPER_RANGE))
        white_gate = sh.Settings.settings_reader(sh.Settings.DEFAULT_WHITE_THRESHOLD)

        tmp_canny = ImageSections.get_template_canny('template.png')

        success, p_frame = cap.read()
        f = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        pb.update_bar.emit(f)
        prev_frame = ImageData(p_frame, lower_r, upper_r, white_gate, width, height, word_points, border_points)
        prev_frame.set_canny(tmp_canny)
        prev_frame.dialogue = prev_frame.is_dialogue()
        prev_frame.word = prev_frame.is_word()

        start = ''
        end = ''
        spec = {}

        while success:
            try:
                success, c_frame = cap.read()
                ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                f = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                pb.update_bar.emit(f)
                curr_frame = ImageData(c_frame, lower_r, upper_r, white_gate, width, height, word_points, border_points)
                curr_frame.set_canny(tmp_canny)
                curr_frame.dialogue = curr_frame.is_dialogue()
                curr_frame.word = curr_frame.is_word()
                # data_li是拿来输出更详细视频读取结果的
                #data_li.append(curr_frame.get_detailed_data(f, ms))
                if curr_frame.dialogue == prev_frame.dialogue:
                    if curr_frame.dialogue:
                        if curr_frame.word == False and prev_frame.word != curr_frame.word:
                            #判断文本更新
                            end = ms
                            image_sections.append(ImageSections.__Merge({'Index':word_count,'Start':start, 'End':end, 'Length':end-start}, spec))
                            start = ms
                            spec = {}
                            word_count += 1
                else:
                    if curr_frame.dialogue:
                        #前一帧不是对话框，当前帧是对话框，判断对话框出现
                        start = ms
                        spec = {'OpenWindow':True}
                    else:
                        #前一帧是对话框，当前帧不是对话框，判断对话框消失
                        end = ms
                        spec = ImageSections.__Merge(spec, {'CloseWindow':True})
                        #Length项为测试代码，正式打包时不需要
                        image_sections.append(ImageSections.__Merge({'Index':word_count,'Start':start, 'End':end, 'Length':end-start}, spec))
                        word_count += 1
                prev_frame = curr_frame
            except cv2.error:
                pb.update_bar.emit(total_frame)
                break
            except TypeError:
                pb.update_bar.emit(total_frame)
                break
        cap.release()

        return image_sections
        #return image_sections, data_li

    def jitter_cleaner(img_sections:list):
        '''
        输入image sections，返回清理后的image sections和警告列表

        清除时间过短的视频分段，合并连续的过段分段并从主列表清除，另添加至警告列表
        '''

        #清除时长小于1秒的section
        remove_li = []
        for im in img_sections:
            if im['End'] - im['Start'] < 1000.0:
                remove_li.append(im)

        #合并多个连续的小于一秒的section
        tmp = []
        remove_subli = []
        for r in remove_li:
            img_sections.remove(r)
            if len(remove_subli) == 0 or remove_subli[-1]['Index'] + 1 == r['Index']:
                remove_subli.append(r)
            else:
                if len(remove_subli) >= 2:
                    tmp.append(remove_subli)
                remove_subli = [r]
        if len(remove_subli) >= 2:
            tmp.append(remove_subli)
            remove_subli = []

        #将合并的连续短section整合，另外添加至警告列表内
        alert = []
        count = 0
        for t in tmp:
            start = t[0]['Start']
            end = t[-1]['End']
            alert.append({'Index':count, 'Start':start, 'End':end, 'Jitter':True})

        for i in range(len(img_sections)):
            img = img_sections[i]
            img['Index'] = i+1

        return img_sections, alert

pb = ImageSections() #为GUI信号输出创建的实例

if __name__ == '__main__':
    pass