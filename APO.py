import numpy as np
import cv2
import tkinter as tk
import sys
import os
from PIL import Image, ImageTk

from template_match import TemplateMatcher

HIGH = 400
WIDTH = 400

def stackImages(scale,imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver

def red(img_hsv):
    lower_red_1 = np.array([0,70,60])
    upper_red_1 = np.array([10,255,255])
    lower_red_2 = np.array([170,70,60])
    upper_red_2 = np.array([180,255,255])
    mask_1 = cv2.inRange(img_hsv,lower_red_1,upper_red_1)
    mask_2 = cv2.inRange(img_hsv,lower_red_2,upper_red_2)
    mask = cv2.bitwise_or(mask_1, mask_2)
    return mask

def blue(img_hsv):
    #lower_blue = np.array([100,160,20])
    #upper_blue = np.array([125,255,200])

    lower_blue = np.array([100,100,100])
    upper_blue = np.array([130,255,255])
    mask = (cv2.inRange(img_hsv,lower_blue,upper_blue))
    return mask

def check_colour(img, mask):
    img_result = cv2.bitwise_and(img,img,mask=mask)
    return img_result

def signs_detecion(imgContour, img):
    contours, hierarchy = cv2.findContours(imgContour, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    imgCropped = []
    px_x = []
    px_y = []
    width = []
    high = []
    result = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500:
            perimeter = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
            x, y, w, h = cv2.boundingRect(approx)
            if h < 1.5 * w and h > 0.5 * w:         #eliminowanie obiektów, które nie powinny być znakiem
                px_x.append(x)
                px_y.append(y)
                width.append(w)
                high.append(h)
                result.append('')
                imgCropped.append(img[y-10:y+h+10, x-10:x+w+10])
    imgCropped_list = {'image': imgCropped, 'px_x': px_x, 'px_y': px_y, 'width': width, 'high': high, 'result': result}   #zapisanie wszystkich informacji o wyciętym zdjęciu w słowniku
    return imgCropped_list
    
def signs_mark(img, imgCropped):
    imgSigns = img.copy()
    for i in range (len(imgCropped['red']['image'])):
        cv2.rectangle(imgSigns, (imgCropped['red']['px_x'][i]-5, imgCropped['red']['px_y'][i]-5), 
                                (imgCropped['red']['px_x'][i] + imgCropped['red']['width'][i] + 5, 
                                imgCropped['red']['px_y'][i] + imgCropped['red']['high'][i] + 5), (0, 255, 0), 2)
        cv2.putText(imgSigns, imgCropped['red']['result'][i], (imgCropped['red']['px_x'][i] + (imgCropped['red']['width'][i] // 4),
                                                                    imgCropped['red']['px_y'][i] + (imgCropped['red']['high'][i] // 4)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 2)
    for i in range (len(imgCropped['blue']['image'])):
        cv2.rectangle(imgSigns, (imgCropped['blue']['px_x'][i]-5, imgCropped['blue']['px_y'][i]-5), 
                                (imgCropped['blue']['px_x'][i] + imgCropped['blue']['width'][i] + 5, 
                                imgCropped['blue']['px_y'][i] + imgCropped['blue']['high'][i] + 5), (0, 255, 0), 2)
        cv2.putText(imgSigns, imgCropped['blue']['result'][i], (imgCropped['blue']['px_x'][i] + (imgCropped['blue']['width'][i] // 4),
                                                                    imgCropped['blue']['px_y'][i] + (imgCropped['blue']['high'][i] // 4)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 2)
    return imgSigns

def return_window(window_now, window_new):
    window_now.pack_forget()
    window_new.pack()

def choice_image(window_old):

    def list_img():
        sciezka = "signs"
        if os.path.exists(sciezka) == False:
            os.makedirs(sciezka)
        list = os.listdir(sciezka)
        for i in range(0, len(list)):
            listbox_img.insert('end', str(list[i]))

    def show_img():
        global label_img
        global image
        global img_tk
        if listbox_img.curselection() != ():
            number_img = listbox_img.curselection()
            name_img = listbox_img.get(number_img)
            path_img = "signs" + "\\" + name_img
            image = cv2.imread(path_img)
            img_tk = ImageTk.PhotoImage(file=path_img)
            label_img = tk.Label(window_choice, image=img_tk)
            label_img.pack()
            label_img.place(x=0, y=0, anchor="nw")

    def processing(image):
        global label_img
        global img_tk
        tm = TemplateMatcher()

        image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        image_mask = {}
        image_mask.update({'red': red(image_hsv), 'blue': blue(image_hsv)})

        image_result_colour = {}
        image_result_colour.update({'red': check_colour(image, image_mask['red']), 
                                    'blue': check_colour(image, image_mask['blue'])})

        image_canny = {}
        image_canny.update({'red': cv2.Canny(image_mask['red'], 50, 50), 
                            'blue': cv2.Canny(image_mask['blue'], 50, 50)})

        image_cropped = {}
        image_cropped.update({'red': signs_detecion(image_canny['red'], image_result_colour['red'])})
        image_cropped.update({'blue': signs_detecion(image_canny['blue'], image_result_colour['blue'])})

        for i in range (len(image_cropped['red']['image'])):
            prohibition_img, prohibition_value = tm.offline_test(image_cropped['red']['image'][i], 'zakaz')
            warning_img, warning_value = tm.offline_test(image_cropped['red']['image'][i], 'ostrzegawczy')
            if prohibition_value > warning_value:
                image_cropped['red']['result'][i] = 'zakaz'
            else:
                image_cropped['red']['result'][i] = 'ostrzegawczy'
        for i in range (len(image_cropped['blue']['image'])):
            mandatory_img, mandatory_value = tm.offline_test(image_cropped['blue']['image'][i], 'nakaz')
            information_img, information_value = tm.offline_test(image_cropped['blue']['image'][i], 'informacyjny')
            if mandatory_value > information_value:
                image_cropped['blue']['result'][i] = 'nakaz'
            else:
                image_cropped['blue']['result'][i] = 'informacyjny'

        image_signs = signs_mark(image, image_cropped)
        cv2.imwrite('image_with_detected_signs.jpg', image_signs)
        img_tk = ImageTk.PhotoImage(file='image_with_detected_signs.jpg')
        #label_img.configure(image=img_tk)
        #label_img.image = img_tk
        label_img = tk.Label(window_choice, image=img_tk)
        label_img.pack()
        label_img.place(x=0, y=0, anchor="nw")

    window_old.pack_forget()
    window_choice = tk.Frame(window, height=str(1000), width=str(1900))
    text_available_img = tk.Label(window_choice, text="Lista dostępnych zdjęć:", height=str(0), width=str(0), font = ("timesnewroman", 12))
    listbox_img = tk.Listbox(window_choice, height=str(36), width=str(24), font = ("timesnewroman", 10))
    srollbar_vertical = tk.Scrollbar(window_choice, orient='vertical', command=listbox_img.yview)
    srollbar_horizontal = tk.Scrollbar(window_choice, orient='horizontal', command=listbox_img.xview)
    button_show_img = tk.Button(window_choice, text="Podgląd zdjęcia", width='15', font = ("timesnewroman", 15), command=lambda:show_img())
    button_processing_img = tk.Button(window_choice, text="Wyszukaj znaków", width='15', font = ("timesnewroman", 15), command=lambda:processing(image))
    button_exit = tk.Button(window_choice, text="Powrót do menu", width='15', font = ("timesnewroman", 15), command=lambda: return_window(window_choice, window_old))
    
    list_img()

    text_available_img.pack()
    text_available_img.place(x=1710, y=0, anchor="nw")
    listbox_img.pack()
    listbox_img.place(x=1710, y=30, width=160, anchor="nw")
    srollbar_vertical.pack()
    srollbar_vertical.place(x=1870, y=30, height=615, anchor="nw")
    srollbar_horizontal.pack()
    srollbar_horizontal.place(x=1710, y=650, width=160, anchor="nw")
    button_show_img.pack()
    button_show_img.place(x=1800, y=1000-150, anchor="center")
    button_processing_img.pack()
    button_processing_img.place(x=1800, y=1000-100, anchor="center")
    button_exit.pack()
    button_exit.place(x=1800, y=1000-50, anchor="center")

    window_choice.pack()

def menu():

    window_menu = tk.Frame(window, height=str(HIGH), width=str(WIDTH))
    window_old = window_menu

    text_menu = tk.Label(window_menu, text='Menu', height='30', width='100', font=('timesnewroman', 30, 'bold'))
    button_choice = tk.Button(window_menu, command=lambda: choice_image(window_old), text='Wyszukaj znaków', height='0', width='20', font=('timesnewroman', 18, 'bold'))
    button_exit = tk.Button(window_menu, command=lambda: sys.exit(0), text='Zamknij aplikacje', height='0', width='20', font=('timesnewroman', 18, 'bold'))
    
    text_menu.pack()
    text_menu.place(x=WIDTH/2, y=80, anchor='center')
    button_choice.pack()
    button_choice.place(x=WIDTH/2, y=150, anchor='center')
    button_exit.pack()
    button_exit.place(x=WIDTH/2, y=HIGH-50, anchor='center')

    window_menu.pack()

if __name__ == '__main__':
      
    #Creating window
    window = tk.Tk()
    window.title('Rozpoznawanie znaków drogowych')
    window.minsize(height=str(HIGH), width=str(WIDTH))

    menu()

    window.mainloop()