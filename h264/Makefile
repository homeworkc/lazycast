OBJS=h264.o audio.o
BIN=./h264.bin
DMX_INC =  -I/opt/vc/include/ -I /opt/vc/include/interface/vmcs_host/ -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux  -I/opt/vc/include/interface/vcos/
EGL_INC = 
OMX_INC =  -I /opt/vc/include/IL 
OMX_ILCLIENT_INC = -I/opt/vc/src/hello_pi/libs/ilclient 
INCLUDES = $(DMX_INC) $(EGL_INC) $(OMX_INC) $(OMX_ILCLIENT_INC)
CFLAGS+= -DOMX_SKIP64BIT $(INCLUDES)  
LDFLAGS+= -lilclient -lavformat -lavcodec -lavutil 

include ./Makefile.include

