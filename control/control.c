#include<X11/Xlib.h>
#include<stdio.h>
#include<stdlib.h> 



int main() 
{
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
		}
		else if (e.type == ButtonRelease)
		{
			printf("ButtonRelease:%d\n", e.xbutton.button);
		}
		else if (e.type == MotionNotify)
		{
			printf("MotionNotify:%d,%d\n", e.xmotion.x, e.xmotion.y);
		}


	}

	XDestroyWindow(d, w);

	XCloseDisplay(d);

   return 0;
 }