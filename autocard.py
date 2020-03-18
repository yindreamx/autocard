#! _*_ coding: utf-8 _*_
import sys, os, pyqrcode
from ftplib import FTP
from prompt_toolkit import prompt
import pathlib
from PIL import Image, ImageDraw, ImageFont
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
import time

data_filename = "card_data.txt"
database=pathlib.Path(data_filename)
active = 0
remember = 0
user_info_list = [0]*3
check = 0
configure_list = [0]*2

def help():
    '''
    Ham in ra man hinh cac lenh chuc nang de su dung chuong trinh.
    '''
    print("AutoCard by Dang Nam\n")
    print("Co so du lieu cua chuong trinh duoc luu tru tren may chu. Vui long dang nhap de tai co so du lieu ve truoc khi su dung chuong trinh, dieu nay la bat buoc! De dang nhap vao may chu, su dung lenh --login.\n")
    print("Cac lenh su dung trong chuong trinh: \n")
    print("--showall: Hien thi toan bo du lieu the co trong co so du lieu.")
    print("--show + ten nha mang: Hien thi toan bo du lieu the co trong co so du lieu theo nha mang cu the.")
    print("--exportcard + ten nha mang + menh gia + so luong: Xuat the duoi dang text.")
    print("--exporttoqr + ten nha mang + menh gia + so luong: Xua the duoi dang QR Code.")
    print("--exporttolist + ten nha mang + menh gia + so luong + ten file muon xuat: Xua the duoi dang tep text.")
    print("--countcard + ten nha mang + menh gia: Kiem tra so luong the co trong co so du lieu tuy theo nha mang va menh gia.")
    print("--importcard + ten nha mang + menh gia + ma pin + serial: Nhap the vao co so du lieu.")
    print("--importlist + ten file muon nhap vao co so du lieu: Nhap the tu tep text vao co so du lieu.")

def get_data():
    '''
    Ham ket noi voi Google Spreadsheets thông qua API cua Google de lay thong tin dang nhap ve chuong trinh.
    '''
    datalist = [0]*4
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("api.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("user info").sheet1 
    datalist[0] = sheet.cell(2, 1).value 
    datalist[1] = sheet.cell(2, 2).value
    datalist[2] = sheet.cell(2, 3).value
    print(datalist)
    return datalist

def post_data(HOST, USERNAME, PASSWD):
    '''
    Ham ket noi voi Google Spreadsheets thong qua API cua Google de tai thong tin dang nhap len.
    '''
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("api.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("user info").sheet1
    sheet.update_cell(2, 1, HOST)
    sheet.update_cell(2, 2, USERNAME)
    sheet.update_cell(2, 3, PASSWD)

def data_from_configure():
    '''
    Ham doc du lieu trong file configure.txt de lay cac thong tin cai dat can thiet.
    '''
    global configure_list
    data = read_data('configure.txt', "r")
    configure_list[0] = data[0][11:12]
    configure_list[1] = data[1][7:31]
    return configure_list
    
def login(HOST, USERNAME, PASSWD, remember):
    '''
    Ham ket noi voi may chu thong qua giao thuc FTP de lay file database ve may nguoi dung.
    '''
    local_time = time.asctime(time.localtime(time.time()))
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftp.connect(HOST,21)
    ftp.login(USERNAME, PASSWD)
    ftp.cwd('/public_html')
    ftp.retrbinary("RETR " + data_filename, open(data_filename, 'wb').write)
    ftp.close()
    print("Da lay du lieu tu may chu %s thanh cong!\nVui long dang xuat bang lenh --logout sau khi ket thuc phien lam viec." %HOST)
    if remember:
        post_data(HOST, USERNAME, PASSWD)
        f = open("configure.txt", "w+")
        data = "Remember = 1\nTime = " + local_time
        f.write(data)
        f.close()
    else:
        f = open("configure.txt", "w+")
        data = "Remember = 0\nTime = " + local_time
        f.write(data)
        f.close()

def logout(input):
    '''
    Ham ket noi voi may chu thong qua giao thuc FTP de tai du lieu database len may chu sau khi ket thuc phien lam viec cua nguoi su dung.
    '''
    LOCAL_FILE = 'card_data.txt'
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftp.connect(user_info_list[0], 21)
    ftp.login(user_info_list[1], user_info_list[2])
    ftp.cwd('/public_html')
    fp=open(LOCAL_FILE, 'rb')
    ftp.storbinary('STOR {}'.format(os.path.basename(LOCAL_FILE)), fp, 1024)
    ftp.close()
    os.remove(data_filename)
    if input:
        print("Da tai du lieu len may chu %s thanh cong!\nPhien hoat dong ket thuc.\nXin chao va hen gap lai!" %user_info_list[0].strip())
    else:
        print("Da tai du lieu len may chu %s thanh cong!\nPhien hoat dong ket thuc.\nXin chao va hen gap lai!" %user_info_list[0].strip())

def remember(input):
    '''
    Ham kiem tra hanh dong luu thong tin dang nhap nguoi dung.
    '''
    global remember
    remember = input
    return remember

def remember_result():
    '''
    Ham tra ket qua duoi dang string de chuong trinh co the thuc thi.
    '''
    return remember

def save_info_for_logout(input_host, input_username, input_passwd):
    '''
    Ham luu thong tin dang nhap nguoi dung vao bo nho may de khi dang xuat khong can nhap lai cung nhu khong can lay du lieu tu mot tep cuc bo nao do.
    '''
    global user_info_list
    user_info_list[0] = input_host
    user_info_list[1] = input_username
    user_info_list[2] = input_passwd
    return user_info_list

def checkdatabase():
    '''
    Ham kiem tra su ton tai cua file database.
    '''
    global active
    if database.exists():
        active = 1
    else:
        active = 0
    return active

def checkuserinfo():
    '''
    Ham kiem tra thong tin nguoi dung co duoc luu lai hay khong.
    '''
    global check
    if int(configure_list[0]):
        check = 1
    else:
        check = 0
    return check

def read_data(data_filename, mode):
    '''
    Ham doc du lieu tu mot file text bat ky.
    '''
    datafile = open(data_filename, mode)
    data_lines = datafile.readlines()
    datafile.close()
    return data_lines

def check_duplicate_one_card(pin, serial):
    '''
    Ham kiem tra the trung lap (1 the/lan).
    '''
    data_lines9 = read_data(data_filename, "r")
    for data_line9 in data_lines9:
        pin_check = data_line9[17:30].strip()
        serial_check = data_line9[30:48].strip()
        if (pin == pin_check) or (serial == serial_check):
            return 1
    return 0

def check_duplicate(input):
    '''
    Ham kiem tra the trung lap theo danh sach.
    '''
    data_lines10 = read_data(input, "r")
    list = []
    data = [data_line10.strip() for data_line10 in data_lines10]
    data_lines12 = read_data(input, "r")
    list.extend(data)
    k = 0
    duplicate = 0
    data_lines11 = read_data(data_filename, "r")
    for data_line11 in data_lines11:
        pin_check = data_line11[17:30].strip()
        serial_check = data_line11[30:48].strip()
        for data_line12 in data_lines12:
            pin_check2 = data_line12[17:30].strip()
            serial_check2 = data_line12[30:48].strip()
            if (pin_check == pin_check2) or (serial_check == serial_check2):
                list.remove(list[k])
                k = k-1
                duplicate = duplicate+1
            if int(len(list)-1) == k:
                pass
            else:
                k = k+1
        k = 0
    os.remove(input)
    f = open(input, "w+")
    print(list)
    for z in range(len(list)):
        f.write(list[z] + "\n")
        z = z+1
    f.close()
    print(duplicate)
    return duplicate
                
def show_data(input):
    '''
    Ham hien thong tin the.
    '''
    C=''
    if checkdatabase():
        data_lines = read_data(input, "r")
        price_sum = 0
        i=0
        for data_line in data_lines:
            A = data_line
            i = i+1
            A = "%3d. "%i + A
            C = C + A
        count = int(len(data_lines))
        return C
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def add_text(carrier_name, pricecard, pincode, serialcode, time, number, folder):
    '''
    Ham chen du lieu the vao mot file anh.
    '''
    font = ImageFont.truetype('/Users/macos/Desktop/GUI/Roboto-Bold.ttf', size=45)
    (xpin, ypin) = (135, 125)
    (xserial, yserial) = (135, 237)
    (xtime, ytime) = (135, 350)
    (xprice, yprice) = (280,611)
    color = 'rgb(0, 0, 0)'
    pin = pincode
    serial = serialcode
    price = pricecard + ',000 VND'
    if (carrier_name == 'Viettel'):
        image = Image.open('/Users/macos/Desktop/GUI/viettel_form.png')
    if (carrier_name == 'Vinaphone'):
        image = Image.open('/Users/macos/Desktop/GUI/vinaphone_form.png')
    if (carrier_name == 'Mobifone'):
        image = Image.open('/Users/macos/Desktop/GUI/mobifone_form.png')
    if (carrier_name == 'Vietnamobile'):
        image = Image.open('/Users/macos/Desktop/GUI/vietnamobile_form.png')
    draw = ImageDraw.Draw(image) 
    draw.text((xpin, ypin), pin, fill = color, font = font)
    draw.text((xserial, yserial), serial, fill = color, font = font)
    draw.text((xprice, yprice), price, stroke_fill = color, font = font)
    draw.text((xtime,ytime), time, fill = color, font = font)
    foldername = folder.rstrip('.png')
    save = foldername + "_%d" %number
    image.save(save + ".png", optimize=True, quality=100)
 
def show_carrier(carrier_name):
    '''
    Ham hien thong tin the theo nha mang cu the.
    '''
    A=''
    if checkdatabase():
        data_lines1 = read_data(data_filename, "r")
        count = 0
        price_sum = 0
        i = 0
        for data_line1 in data_lines1:
            B = data_line1[0:12].strip()
            D = int(data_line1[13:16].strip())
            C = data_line1
            if B == carrier_name:
                count = count +1
                i = i+1
                price_sum = price_sum + D
                C = "%3d. "%i + C
                A = A + C
                print (C)
        if count > 0:
            A =  A + "\nCo %d the %s! Tong gia tri: " %(count, carrier_name) + format(price_sum, ',d') + ",000 VND." 
            return A
        else:
            B = "Da het the %s!" %carrier_name
            return B
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")


def countcard(carrier_name, price):
    '''
    Ham dem so luong the theo nha mang va menh gia.
    '''
    data_lines2 = read_data(data_filename, "r")
    count = 0
    for data_line2 in data_lines2:
        A = data_line2[0:12].strip()
        B = data_line2[13:16].strip()
        if (A == carrier_name) and (B == price):
            count = count+1
    return count

def count():
    '''
    Ham dem so luong the.
    '''
    data_lines8 = read_data(data_filename, "r")
    count = int(len(data_lines8))
    price_sum = 0
    for data_line8 in data_lines8:
        A = int(data_line8[13:16].strip())
        price_sum = A + price_sum
    price_sum = price_sum*1000
    B = "\nTrong kho con co " + format(count, ',d') + " the! " + "Tong gia tri: " + format(price_sum, ',d')+" VND."
    return B

def count_for_import(file_name):
    '''
    Ham dem so luong the phuc vu cho viec nhap the.
    '''
    data_lines13 = read_data(file_name, "r")
    count = int(len(data_lines13))
    print(count)
    return count 

def exportcard(carrier_name, price, amount):
    '''
    Ham xuat the thong thuong.
    '''
    if checkdatabase():
        data_lines3 = read_data(data_filename, "r")
        datalist = []
        data = [data_line3.strip() for data_line3 in data_lines3]
        datalist.extend(data)
        i = 0
        k = 0
        N=''
        j = countcard(carrier_name, price)
        if int(amount) <= j:
            for data_line3 in data_lines3:
                A = data_line3[0:12].strip()
                B = data_line3[13:16].strip()
                pincode = data_line3[17:30].strip()
                serial = data_line3[30:48].strip()
                C = datalist[k]
                if i < int(amount):
                    if (A == carrier_name) and (B == price):
                        i = i+1
                        datalist.remove(C)
                        k = k-1
                        N = N + "The %s:\nNha mang: %s\nMenh gia: %s\nMa PIN:   %s\nSerial:   %s\n==========================\n" %(i,carrier_name, price, pincode, serial)
                k = k + 1   
            N = N + "Da xuat thanh cong %s the %s \nmenh gia %s,000 VND!\n" %(amount, carrier_name, price)
            os.remove(data_filename)
            f = open("card_data.txt", "w+")
            for z in range(len(datalist)):
                f.write(datalist[z] + "\n")
                z = z+1
            f.close()
            print ("Cap nhat du lieu moi thanh cong!")
            return N
        else:
            return "So luong the khong du! Trong kho chi con %s \nthe %s menh gia %s,000 VND!\n" %(j, carrier_name, price)

    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def exportimage(carrier_name, price, amount, time, folder):
    '''
    Ham xuat the duoi dang file anh.
    '''
    if checkdatabase():
        data_lines8 = read_data(data_filename, "r")
        datalist = []
        data_export = []
        data = [data_line8.strip() for data_line8 in data_lines8]
        datalist.extend(data)
        i = 0
        j = 0
        k = 0
        j = countcard(carrier_name, price)
        N=''
        if int(amount) <= j:
            for data_line8 in data_lines8:
                A = data_line8[0:12].strip()
                B = data_line8[13:16].strip()
                pincode = data_line8[17:30].strip()
                serial = data_line8[30:48].strip()
                C = datalist[k]
                if i < int(amount):
                    if (A == carrier_name) and (B == price):
                        i = i+1
                        datalist.remove(C)
                        add_text(carrier_name, price, pincode, serial, time, i, folder)
                        k = k-1
                        N = N + "The %s => Image => Thanh cong\n==========================\n" %i
                k = k+1
            N = N + "Da xuat thanh cong %s the %s \nmenh gia %s,000 VND!\n" %(amount, carrier_name, price)
            os.remove(data_filename)
            f= open("card_data.txt", "w+")
            for z in range(len(datalist)):
                f.write(datalist[z] + "\n")
                z = z+1
            f.close()
            print ("Cap nhat du lieu moi thanh cong!")
            return N
        else:
            return 1
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def exporttolist(carrier_name, price, amount, outputfile):
    '''
    Ham xuat the duoi dang mot file text.
    '''
    if checkdatabase():
        data_lines7 = read_data(data_filename, "r")
        datalist = []
        data_export = []
        data = [data_line7.strip() for data_line7 in data_lines7]
        datalist.extend(data)
        i = 0
        j = 0
        k = 0
        j = countcard(carrier_name, price)
        list_card = open(outputfile, "w+")
        N = ''
        if int(amount) <= j:
            for data_line7 in data_lines7:
                A = data_line7[0:12].strip()
                B = data_line7[13:16].strip()
                pincode = data_line7[17:30].strip()
                serial = data_line7[30:48].strip()
                C = datalist[k]
                if i < int(amount):
                    if (A == carrier_name) and (B == price):
                        i =i+1
                        datalist.remove(C)
                        list_card.write("The %s:\nNha mang: %s\nMenh gia: %s\nMa PIN:   %s\nSerial:   %s\n==========================\n" %(i, carrier_name, price, pincode, serial))
                        k = k-1
                        N = N + "Xuat thanh cong the thu %s.\n==========================\n" %i
                k = k+1   
            N = N + "Da xuat thanh cong %s the %s menh gia \n%s,000 VND!" %(amount, carrier_name, price)
            list_card.close()
            os.remove(data_filename)
            f = open("card_data.txt", "w+")
            for z in range(len(datalist)):
                f.write(datalist[z] + "\n")
                z = z+1
            f.close()
            print ("Cap nhat du lieu moi thanh cong!")
            return N
        else:
            return 1
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def exporttolist2(carrier_name, price, amount, outputfile):
    '''
    Ham xuat the tiep tuc vao mot file text da co san.
    '''
    if checkdatabase():
        data_lines7 = read_data(data_filename, "r")
        datalist = []
        data_export = []
        data = [data_line7.strip() for data_line7 in data_lines7]
        datalist.extend(data)
        i = 0
        j = 0
        k = 0
        j = countcard(carrier_name, price)
        lines = open(outputfile, "r")
        number_line = lines.readlines()
        lines.close()
        length = int(len(number_line))
        list_card = open(outputfile, "a")
        number_line = length//6
        N = ''
        if int(amount) <= j:
            for data_line7 in data_lines7:
                A = data_line7[0:12].strip()
                B = data_line7[13:16].strip()
                pincode = data_line7[17:30].strip()
                serial = data_line7[30:48].strip()
                C = datalist[k]
                if i < int(amount):
                    if (A == carrier_name) and (B == price):
                        i = i+1
                        number_line = number_line+1
                        datalist.remove(C)
                        list_card.write("The %s:\nNha mang: %s\nMenh gia: %s\nMa PIN:   %s\nSerial:   %s\n==========================\n" %(number_line, carrier_name, price, pincode, serial))
                        k = k-1
                        N = N + "Xuat thanh cong the thu %s.\n==========================\n" %i
                k = k+1   
            N = N + "Da xuat thanh cong %s the %s menh gia \n%s,000 VND! Tong cong trong file co: %d the!" %(amount, carrier_name, price, number_line)
            list_card.close()
            os.remove(data_filename)
            f = open("card_data.txt", "w+")
            for z in range(len(datalist)):
                f.write(datalist[z] + "\n")
                z = z+1
            f.close()
            print ("Cap nhat du lieu moi thanh cong!")
            return N
        else:
            list_card.close()
            os.remove(outputfile)
            return 1
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def check_remain(carrier, price, amount):
    '''
    Ham kiem tra so luong the con lai.
    '''
    if checkdatabase():
        j = countcard(carrier, price)
        if int(amount) <= j:
            return 0
        else:
            return "Trong kho chi con %s the %s menh gia \n%s,000 VND!" %(j, carrier, price)
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def exporttoqr(carrier_name, price, amount, output):
    '''
    Ham xuat the duoi dang ma QRCode.
    '''
    if checkdatabase():
        data_lines4 = read_data(data_filename,"r")
        datalist = []
        data = [data_line4.strip() for data_line4 in data_lines4]
        datalist.extend(data)
        i = 0
        j = 0
        k = 0
        j = countcard(carrier_name,price)
        N = ''
        if int(amount) <= j:
            for data_line4 in data_lines4:
                A = data_line4[0:12].strip()
                B = data_line4[13:16].strip()
                pincode = data_line4[17:30].strip()
                serial = data_line4[30:48].strip()
                C = datalist[k]
                if i < int(amount):
                    if (A == carrier_name) and (B == price):
                        i = i+1
                        datalist.remove(C)
                        k = k - 1
                        card = "*101*" + pincode + "#"
                        output = output.rstrip('.svg')
                        outputsvg = output + "_%d" %i
                        url = pyqrcode.create(card)
                        url.svg(outputsvg + ".svg", scale = 8)
                        N=N+"The %s => QRCode => Thanh cong\n==========================\n" %i
                k = k+1   
            N = N + "Da xuat thanh cong %s the %s \nmenh gia %s,000 VND!\n" %(amount, carrier_name, price)
            os.remove(data_filename)
            f = open("card_data.txt", "w+")
            for z in range(len(datalist)):
                f.write(datalist[z] + "\n")
                z = z+1
            f.close()
            print ("Cap nhat du lieu moi thanh cong!")
            return N
        else:
            return 1
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def getblank(carrier_name):
    '''
    Ham lay khoang trong tuy theo ten nha mang.
    '''
    if carrier_name == "Vietnamobile":
       blank = " "
    elif carrier_name == "Viettel":
        blank = "      "
    elif carrier_name == "Mobifone":
        blank = "     "
    else:
        blank = "    "
    return blank

def getblankforprice(price):
    '''
    Ham lay khoang trong tuy theo menh gia the.
    '''
    if (price == "10") or (price == "20") or (price == "50") or (price == "30"):
        blank = "  "
    else:
        blank = " "
    return blank

def importcard(carrier_name, price, pincode, serial):
    '''
    Ham nhap the vao database.
    '''
    if checkdatabase():
        blank = getblank(carrier_name)
        blank_for_price = getblankforprice(price)
        datafile5 = open(data_filename, "a")
        dataimport = carrier_name + blank + price + blank_for_price + pincode + " " + serial + "\n"
        datafile5.write(dataimport)
        datafile5.close()
        A = "The %s menh gia %s,000 VND da duoc cap nhat\nthanh cong vao co so du lieu!" %(carrier_name, price)
        print (A)
        return A
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

def importlist(file_input):
    '''
    Ham nhap the theo danh sach vao database.
    '''
    if checkdatabase():
        file_name = file_input
        data_lines6 = read_data(file_name, "r")
        datalist = []
        data = [data_line6.strip() for data_line6 in data_lines6]
        datalist.extend(data)
        datafile7 = open(data_filename, "a")
        ln=len(datalist)
        for z in range(ln):
                datafile7.write(datalist[z] + "\n")
                z = z+1
        datafile7.close()
        A="Cap nhat thanh cong %s the vao co so du lieu!" %(ln)
        print(A)
        return A
    else:
        print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print ("Chuong trinh AutoCard by Dang Nam\n=================================")
        print('Vui long go lenh "autocard.py" -help de duoc biet cach thuc su dung chuong trinh!')
    else:
        if sys.argv[1] == "--showall":
            show_data()
        elif sys.argv[1] == "--show":
            show_carrier(sys.argv[2])
        elif sys.argv[1] == "--login":
            login()
        elif sys.argv[1] == "--logout":
            logout()
        elif sys.argv[1] == "--exportcard":
            exportcard(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        elif sys.argv[1] == "--image":
            add_text(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif sys.argv[1] == "--exportimage":
            exportimage(sys.argv[2], sys.argv[3], sys.argv[4])
        elif sys.argv[1] == "--countcard":
            if checkdatabase():
                j = countcard(sys.argv[2], sys.argv[3])
                print ("Trong kho con %d the %s menh gia %s,000 VND!" %(j, sys.argv[2], sys.argv[3]))
            else:
                print("Khong tim thay co so du lieu. Vui long dang nhap vao may chu de cap nhat co so du lieu moi nhat. Su dung lenh: --login.")
        elif sys.argv[1] == "--exporttoqr":
            exporttoqr(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        elif sys.argv[1] == "--exporttolist":
            exporttolist(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif sys.argv[1] == "--importcard":
            importcard(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif sys.argv[1] == "--help":
            help()
        elif sys.argv[1] == '--importlist':
            importlist(sys.argv[2])
        elif sys.argv[1] == '--config':
            data_from_configure()
        elif sys.argv[1] == '--get':
            get_data()
        elif sys.argv[1] == '--check':
            print(checkuserinfo())
        elif sys.argv[1] == '--data':
            print(data_from_configure())
        else:
            print ("Khong co lenh nao phu hop!")