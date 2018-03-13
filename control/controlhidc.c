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



char mouseinput[] = {
	0x00,0x01,
	0x00,0x0c,
	0x01,0x01,
	0x00,0x00,
	0x03,0x00,
	0x00,0x00
};

char keyboardinput[] = {
	0x00,0x01,
	0x00,0x0c,
	0x01,0x00,
	0x00,0x00,
	0x03,0x00,
	0x00,0x00
};
/*
char reportdescriptor[55] = {
	0x01,0x01,
	0x01,0x00,
	50,
	0x05, 0x01,                    // USAGE_PAGE (Generic Desktop)
	0x09, 0x02,                    // USAGE (Mouse)
	0xa1, 0x01,                    // COLLECTION (Application)
	0x09, 0x01,                    //   USAGE (Pointer)
	0xa1, 0x00,                    //   COLLECTION (Physical)
	0x05, 0x09,                    //     USAGE_PAGE (Button)
	0x19, 0x01,                    //     USAGE_MINIMUM (Button 1)
	0x29, 0x03,                    //     USAGE_MAXIMUM (Button 3)
	0x15, 0x00,                    //     LOGICAL_MINIMUM (0)
	0x25, 0x01,                    //     LOGICAL_MAXIMUM (1)
	0x95, 0x03,                    //     REPORT_COUNT (3)
	0x75, 0x01,                    //     REPORT_SIZE (1)
	0x81, 0x02,                    //     INPUT (Data,Var,Abs)
	0x95, 0x01,                    //     REPORT_COUNT (1)
	0x75, 0x05,                    //     REPORT_SIZE (5)
	0x81, 0x03,                    //     INPUT (Cnst,Var,Abs)
	0x05, 0x01,                    //     USAGE_PAGE (Generic Desktop)
	0x09, 0x30,                    //     USAGE (X)
	0x09, 0x31,                    //     USAGE (Y)
	0x15, 0x81,                    //     LOGICAL_MINIMUM (-127)
	0x25, 0x7f,                    //     LOGICAL_MAXIMUM (127)
	0x75, 0x08,                    //     REPORT_SIZE (8)
	0x95, 0x02,                    //     REPORT_COUNT (2)
	0x81, 0x06,                    //     INPUT (Data,Var,Rel)
	0xc0,                          //   END_COLLECTION
	0xc0                           // END_COLLECTION
};*/


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
	serveraddr.sin_port = htons(50000);

	int flag = 1;

	setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, (char *)&flag, sizeof(flag));

	if (connect(fd, (struct sockaddr *)&serveraddr,sizeof(serveraddr)) < 0)
	{
		perror("connect failed!");
		exit(1);
	}

	


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
	w = XCreateSimpleWindow(d, RootWindow(d, s), 0, 0, 1280, 720, 1, BlackPixel(d, s), WhitePixel(d, s));

	Atom delWindow = XInternAtom( d, "WM_DELETE_WINDOW", 0 );
	XSetWMProtocols(d , w, &delWindow, 1);

	XSelectInput(d, w, ExposureMask | KeyPressMask | KeyReleaseMask | ButtonPressMask | ButtonReleaseMask | PointerMotionMask  );

	XMapWindow(d, w);




	int oldx = 0, oldy = 0;
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
		{
			keyboardinput[11] = e.xkey.keycode;
			printf("KeyPress:%d\n", keyboardinput[11]);
			printf("send:%d\n", send(fd, keyboardinput, sizeof(keyboardinput), 0));


		}
		else if (e.type == KeyRelease)
		{
			keyboardinput[11] = 0;
			printf("KeyRelease:%d\n", e.xkey.keycode);
			printf("send:%d\n", send(fd, keyboardinput, sizeof(keyboardinput), 0));
		}
		else if (e.type == ButtonPress)
		{
			int buttonnum = e.xbutton.button;
			printf("ButtonPress:%d\n", buttonnum);

			char mask;
			switch (buttonnum)
			{
			case 1:
				mask = 1;
				break;
			case 3:
				mask = 2;
				break;
			case 2:
				mask = 4;
				break;
			default:
				mask = 0;
			}
			mouseinput[9] |= mask;
			mouseinput[10] = 0;
			mouseinput[11] = 0;
			printf("send:%d\n", send(fd, mouseinput, sizeof(mouseinput), 0));



		}
		else if (e.type == ButtonRelease)
		{
			int buttonnum = e.xbutton.button;
			printf("ButtonRelease:%d\n", buttonnum);

			char mask;
			switch (buttonnum)
			{
			case 1:
				mask = 1;
				break;
			case 3:
				mask = 2;
				break;
			case 2:
				mask = 4;
				break;
			default:
				mask = 0;
			}
			mask = ~mask;
			mouseinput[9] &= mask;
			mouseinput[10] = 0;
			mouseinput[11] = 0;
			printf("send:%d\n", send(fd, mouseinput, sizeof(mouseinput), 0));
		}
		else if (e.type == MotionNotify)
		{
			int newx = e.xmotion.x;
			int newy = e.xmotion.y;
			
			printf("MotionNotify:%d,%d\n", newx, newy);


			int xdiff = newx - oldx;
			int ydiff = newy - oldy;
			oldx = newx;
			oldy = newy;



			if (xdiff > 127)
				mouseinput[10] = 127;
			else if (xdiff < -128)
				mouseinput[10] = -128;
			else
				mouseinput[10] = xdiff;

			if (ydiff > 127)
				mouseinput[11] = 127;
			else if (ydiff < -128)
				mouseinput[11] = -128;
			else
				mouseinput[11] = ydiff;
			//printf("xdiff:%d,ydiff:%d\n", xdiff, ydiff);
			//for (int i = 0; i < sizeof(mouseinput); i++)
				//printf("%d,",mouseinput[i]);
			printf("send:%d\n", send(fd, mouseinput, sizeof(mouseinput), 0));

		}


	}
	close(fd);

	XDestroyWindow(d, w);

	XCloseDisplay(d);

   return 0;
 }