import os

loop = True

while loop:
    os.system('sudo iwlist wlan0 scan > scan.txt')

    infile = open('scan.txt','r')
    lines = infile.readlines()
    infile.close()

    display = False


    for line in lines:
        if 'DIRECT' in line:
            display = True
            loop = False
        elif 'Cell' in line:
            display = False
        if display:
            print line,




