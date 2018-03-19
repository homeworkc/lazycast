#include <X11/Xlib.h>
#include <stdio.h>
#include <stdlib.h> 
#include <unistd.h> 
#include <string.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/tcp.h>



char inputreport[] = {
	0x00,0x00,
	0x00,20,
	0x02,0x00,
	0x06,0x01,
	0x00,0x00,
	0x00,0x00,
	0x00    ,0x00,
	0x00,0x00,
	0x00,0x00,
	0x00,0x00
};




int main(int argc, char **argv)
{
	int fd;
	if ((fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
	{
		printf("socket failed!");
		exit(1);
	}

	struct sockaddr_in serveraddr;



	memset(&serveraddr, 0, sizeof(serveraddr));
	serveraddr.sin_family = AF_INET;
	serveraddr.sin_addr.s_addr = inet_addr("192.168.101.80");
	serveraddr.sin_port = htons(49509);

	int flag = 1;

	setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, (char *)&flag, sizeof(flag));


	if (connect(fd, (struct sockaddr *)&serveraddr,sizeof(serveraddr)) < 0)
	{
		perror("connect failed!");
		exit(1);
	}

	int width = 1280, height = 800;


	Display *d;
	int s;
	Window w;
	XEvent e;

	d = XOpenDisplay(NULL);
	if (d == NULL)
	{
		printf("Cannot open display\n");
		exit(1);
	}
	s = DefaultScreen(d);
	w = XCreateSimpleWindow(d, RootWindow(d, s), 0, 0, width, height, 1, BlackPixel(d, s), WhitePixel(d, s));

	Atom delWindow = XInternAtom( d, "WM_DELETE_WINDOW", 0 );
	XSetWMProtocols(d , w, &delWindow, 1);

	XSelectInput(d, w, ExposureMask | KeyPressMask | KeyReleaseMask | ButtonPressMask | ButtonReleaseMask | PointerMotionMask  );

	XMapWindow(d, w);




	int x = 0, y = 0;
	unsigned short nx, ny;
	while(1) 
	{





		XNextEvent(d, &e);
		if (e.type == Expose)
		{
			;
		}
		else if (e.type == ClientMessage)
			break;
		else if (e.type == KeyPress)
			printf("KeyPress:%d\n", e.xkey.keycode);
		else if (e.type == KeyRelease)
			printf("KeyRelease:%d\n", e.xkey.keycode);
		else if (e.type == ButtonPress)
		{
			printf("ButtonPress:%d\n", e.xbutton.button);
			inputreport[4] = 0;
			inputreport[9] = x >> 8;
			inputreport[10] = 0xFF & x;
			inputreport[11] = y >> 8;
			inputreport[12] = 0xFF & y;
			printf("send:%d\n", send(fd, inputreport, sizeof(inputreport), 0));
		}
		else if (e.type == ButtonRelease)
		{
			printf("ButtonRelease:%d\n", e.xbutton.button);
			inputreport[4] = 1;
			inputreport[9] = x >> 8;
			inputreport[10] = 0xFF & x;
			inputreport[11] = y >> 8;
			inputreport[12] = 0xFF & y;
			printf("send:%d\n", send(fd, inputreport, sizeof(inputreport), 0));
		}
		else if (e.type == MotionNotify)
		{
			x = e.xmotion.x;
			y = e.xmotion.y;
			printf("MotionNotify:%d,%d\n", x, y);
			inputreport[4] = 2;
			inputreport[9] = x >> 8;
			inputreport[10] = 0xFF & x;
			inputreport[11] = y >> 8;
			inputreport[12] = 0xFF & y;
			printf("send:%d\n", send(fd, inputreport, sizeof(inputreport), 0));

		}


	}
	close(fd);

	XDestroyWindow(d, w);

	XCloseDisplay(d);

   return 0;
 }