// mtlinklist.cpp : Defines the entry point for the console application.
//

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdatomic.h>
#include <pthread.h>

atomic_int numofnode = 0;

typedef struct Node
{
	int* pbuff;
	struct Node* next;
} Nodetype;

static void * receivepkt(Nodetype* oldnode)
{
	for (int i = 0; i < 100; i++)
	{
		oldnode->pbuff = malloc(sizeof(int));
		(*oldnode->pbuff) = i;
		oldnode->next = malloc(sizeof(Nodetype));

		Nodetype* pnext = oldnode->next;

		oldnode = pnext;
		atomic_fetch_add(&numofnode, 1);
	}
	

}

int main()
{
	Nodetype* oldnode = malloc(sizeof(Nodetype));
	Nodetype* oldnodecopy = oldnode;


	pthread_t thread;
	if (pthread_create(&thread, NULL, receivepkt, oldnodecopy) != 0)
		exit(1);
	
	while (1)
	{
		if (numofnode < 2)
		{
			usleep(10);
			continue;
		}
		printf("%d\n", numofnode);

		printf("%d\n", *(oldnode->pbuff));
		free(oldnode->pbuff);
		Nodetype* pnext = oldnode->next;
		free(oldnode);

		oldnode = pnext;
		atomic_fetch_sub(&numofnode, 1);
	}
	

	

	if (pthread_join(thread, NULL) != 0)
		exit(1);


	free(oldnode);
	return 0;
}


