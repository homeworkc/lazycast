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



char mousemove[] = {
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

char scroll[] = {
	0x00,0x00,
	0x00, 16,
	0x06,
	0x00,0x02,
	0x40,0x02,   
	0x00,
	0x00,0x00,
	0x00,0x00,
	0x00,0x00
};

char keyboard[] = {
	0x00,0x00,
	0x00, 20,
	0x03,
	0x00,0x05,
	0x00,
	0x00,0x00,//key1
	0x00,0x00,//key2
	0x00,0x00,
	0x00,0x00,
	0x00,0x00,
	0x00,0x00
};


#define fdsend
#define warpcursor
int main(int argc, char **argv)
{
#ifdef fdsend
	int fd;
	if ((fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
	{
		printf("socket failed!");
		exit(1);
	}

	struct sockaddr_in serveraddr;

	printf("using port:%s\n", argv[1]);

	memset(&serveraddr, 0, sizeof(serveraddr));
	serveraddr.sin_family = AF_INET;
	serveraddr.sin_addr.s_addr = inet_addr("192.168.173.80");
	serveraddr.sin_port = htons(atoi(argv[1]));

	int flag = 1;

	setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, (char *)&flag, sizeof(flag));


	if (connect(fd, (struct sockaddr *)&serveraddr,sizeof(serveraddr)) < 0)
	{
		perror("connect failed!");
		exit(1);
	}
#endif


	Display *d;
	int s;
	Window w;
	XEvent e;

	d = XOpenDisplay(":0.0");
	//d = XOpenDisplay(NULL);
	if (d == NULL)
	{
		printf("Cannot open display\n");
		exit(1);
	}
	s = DefaultScreen(d);
	int width = XWidthOfScreen(DefaultScreenOfDisplay(d));
	int height = XHeightOfScreen(DefaultScreenOfDisplay(d));
	w = XCreateSimpleWindow(d, RootWindow(d, s), 0, 0, width, height, 1, BlackPixel(d, s), WhitePixel(d, s));

	Atom delWindow = XInternAtom( d, "WM_DELETE_WINDOW", 0 );
	XSetWMProtocols(d , w, &delWindow, 1);

	XSelectInput(d, w, ExposureMask | KeyPressMask | KeyReleaseMask | ButtonPressMask | ButtonReleaseMask | PointerMotionMask  );

	XMapWindow(d, w);

	XWarpPointer(d, None, w, 0, 0, 0, 0, width/2, height/2);


	int x = 0, y = 0;
	int oldx = 0, oldy = 0;
	int warp = 0;
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
			keyboard[4] = 0x03;
			printf("KeyPress code:%d\n", e.xkey.keycode);


			int keysyms_per_keycode_return;
			KeySym *keysym = XGetKeyboardMapping(d, e.xkey.keycode, 1, &keysyms_per_keycode_return);
			
			if ((*keysym) < 256)
			{
				char key;
				if (e.xkey.state & ShiftMask)
					key = keysym[1];
				else if (e.xkey.state & LockMask && keysym[0] > 0x60 && keysym[0] < 0x7B)
					key = keysym[1];
				else
					key = keysym[0];



				if (key != NoSymbol)
				{

					printf("%x	", key);
					//printf("%s	", XKeysymToString(key));
					keyboard[9] = key;
#ifdef fdsend
					printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
				}
			}
			else if ((*keysym) == 0xff08 || (*keysym) == 0xff09
				|| (*keysym) == 0xff0a || (*keysym) == 0xff0b
				|| (*keysym) == 0xff0d || (*keysym) == 0xff13
				|| (*keysym) == 0xff14 || (*keysym) == 0xff15
				|| (*keysym) == 0xff1b)
			{
				keyboard[9] = 0xFF & (*keysym);
#ifdef fdsend
				printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
			}
			else if ((*keysym) == 0xffff)
			{
				keyboard[9] = 0x7F;
				printf("special:%x\n", keyboard[9]);
#ifdef fdsend
				printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
			}
			else if ((*keysym) == 0xff52)
			{
				keyboard[9] = 38;
				printf("special:%x\n", keyboard[9]);
#ifdef fdsend
				printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
			}





			printf("%x\n", *keysym);

			//printf("%s\n", XKeysymToString(*keysym));

			XFree(keysym);

		}
		else if (e.type == KeyRelease)
		{
			keyboard[4] = 0x04;
			printf("KeyRelease code:%d\n", e.xkey.keycode);


			int keysyms_per_keycode_return;
			KeySym *keysym = XGetKeyboardMapping(d, e.xkey.keycode, 1, &keysyms_per_keycode_return);

			if ((*keysym) < 256)
			{
				char key;
				if (e.xkey.state & ShiftMask)
					key = keysym[1];
				else if (e.xkey.state & LockMask && keysym[0] > 0x60 && keysym[0] < 0x7B)
					key = keysym[1];
				else
					key = keysym[0];

				printf("here\n");

				if (key != NoSymbol)
				{

					printf("%x	", key);
					//printf("%s	", XKeysymToString(key));
					keyboard[9] = key;
#ifdef fdsend
					printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif

				}
			}
			else if ((*keysym) == 0xff08 || (*keysym) == 0xff09
				|| (*keysym) == 0xff0a || (*keysym) == 0xff0b
				|| (*keysym) == 0xff0d || (*keysym) == 0xff13
				|| (*keysym) == 0xff14 || (*keysym) == 0xff15
				|| (*keysym) == 0xff1b)
			{
				keyboard[9] = 0xFF & (*keysym);
				printf("special:%x\n", keyboard[9]);
#ifdef fdsend
				printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
			}
			else if ( (*keysym) == 0xffff)
			{
				keyboard[9] = 0x7F;
				printf("special:%x\n", keyboard[9]);
#ifdef fdsend
				printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
			}
			else if ((*keysym) == 0xff52)
			{
				keyboard[9] = 38;
				printf("special:%x\n", keyboard[9]);
#ifdef fdsend
				printf("send:%d\n", send(fd, keyboard, sizeof(keyboard), 0));
#endif
			}


			//printf("%s\n", XKeysymToString(*keysym));

			XFree(keysym);

		}
		else if (e.type == ButtonPress)
		{
			int buttonnum = e.xbutton.button;
			printf("ButtonPress:%d\n", buttonnum);

			if (buttonnum < 4)
			{
				mousemove[4] = 0;
				mousemove[9] = x >> 8;
				mousemove[10] = 0xFF & x;
				mousemove[11] = y >> 8;
				mousemove[12] = 0xFF & y;
#ifdef fdsend
				printf("send:%d\n", send(fd, mousemove, sizeof(mousemove), 0));
#endif
			}
			else if(buttonnum < 6)
			{
				if (buttonnum == 4)
				{
					scroll[7] |= 0x20;
				}
				else
				{
					scroll[7] &= ~0x20;
				}
#ifdef fdsend
				printf("send:%d\n", send(fd, scroll, sizeof(scroll), 0));
#endif

			}

		}
		else if (e.type == ButtonRelease)
		{
			printf("ButtonRelease:%d\n", e.xbutton.button);
			mousemove[4] = 1;
			mousemove[9] = x >> 8;
			mousemove[10] = 0xFF & x;
			mousemove[11] = y >> 8;
			mousemove[12] = 0xFF & y;
#ifdef fdsend
			printf("send:%d\n", send(fd, mousemove, sizeof(mousemove), 0));
#endif
		}
		else if (e.type == MotionNotify)
		{
			int newx = e.xmotion.x;
			int newy = e.xmotion.y;
			int xdiff = newx - oldx;
			int ydiff = newy - oldy;
			oldx = newx;
			oldy = newy;

#ifdef warpcursor
			if (warp == 1)
			{
				warp = 0;
				continue;
			}

			if (newx < 128 || newx > width - 128 || newy < 128 || newy > height - 128)
			{
				XWarpPointer(d, None, w, 0, 0, 0, 0, width/2, height/2);
				warp = 1;
				printf("border\n");

			}
#endif
			printf("MotionNotify:%d,%d\n", newx, newy);

			x += xdiff;
			y += ydiff;
			
			x = x < 0 ? 0 : x;
			y = y < 0 ? 0 : y;

			mousemove[4] = 2;
			mousemove[9] = x >> 8;
			mousemove[10] = 0xFF & x;
			mousemove[11] = y >> 8;
			mousemove[12] = 0xFF & y;
#ifdef fdsend
			printf("send:%d\n", send(fd, mousemove, sizeof(mousemove), 0));
#endif

		}


	}
#ifdef fdsend
	close(fd);
#endif

	XDestroyWindow(d, w);

	XCloseDisplay(d);

   return 0;
 }