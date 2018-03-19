
OBJS = control.o
BIN = control.bin


CFLAGS = -O2 -Wall
LDFLAGS = -L /usr/X11R6/lib -lX11 -lm
INCLUDES=

all: $(BIN) $(LIB)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -g -c $< -o $@ 

%.bin: $(OBJS)
	$(CC) -o $@  $(OBJS) $(LDFLAGS) 
