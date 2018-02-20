import binascii
import struct


file = open("data.ts", "r")
f2 = open("data2.ts", "w")

while 1:
    #rtp header
    data= file.read(12)
    #print data
    #print binascii.hexlify(data)
    for i in range(0,7):
        #ts packet
        data= file.read(188)
        f2.write(data)
        #print data
        #print binascii.hexlify(data)
        '''
        syncbyte=data[0]
        pid = ((ord(data[1])&0x1f)<<8) + ord(data[2])
        #print '%02x' %pid
        # print data[3]
        if(pid==0):
            print "pat"
            (programid,ppid)= struct.unpack("HH", data[4:8])
            ppid=ppid & 0x1fff
            print bin(programid)
            print bin(ppid)
        '''


        