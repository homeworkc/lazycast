/*
Copyright (c) 2012, Broadcom Europe Ltd
All rights reserved.
Copyright (c) 2018, Hsun-Wei Cho

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
* Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
* Neither the name of the copyright holder nor the
names of its contributors may be used to endorse or promote products
derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

// Video deocode demo using OpenMAX IL though the ilcient helper library
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>

#include <sys/socket.h>
#include <arpa/inet.h>

#include "bcm_host.h"
#include "ilclient.h"
#include "audio.h"

#define here() printf("line:%d\n",__LINE__);

typedef struct srtppacket
{
	unsigned char* buf;
	int recvlen;
	int seqnum;
	struct srtppacket* next;
} rtppacket;

atomic_int numofnode;


int largers(int a, int b)
{
	if (abs(a - b) < 32768)
		return a > b;
	else if (a - b <= -32768)
		return 1;
	else
		return 0;
}

int sendtodecoder(COMPONENT_T *video_decode, COMPONENT_T *video_scheduler, COMPONENT_T *video_render, TUNNEL_T* tunnel,
	OMX_BUFFERHEADERTYPE *buf, rtppacket **beg, rtppacket *scan,
	int* port_settings_changed, int *first)
{
	int loop = 1;
	int theveryfirst = 1;
	while (loop)
	{
		buf = ilclient_get_input_buffer(video_decode, 130, 1);
		if (buf == NULL)
			return 0;
		unsigned char *dest = buf->pBuffer;

		int data_len = 0;
		while (1)
		{
			int numofts = ((*beg)->recvlen - 12) / 188;
			for (int i = 0; i < numofts; i++)
			{
				unsigned char* buffer = (*beg)->buf + 12 + i * 188;
				short pid = ((0x1F & buffer[1]) << 8) + buffer[2];
				if (pid != 0x1011)
					continue;
				int ad = 3 & (buffer[3] >> 4);
				if (ad & 1)
				{
					int adlen = buffer[4];
					int shift = (ad == 1) ? 4 : adlen + 5;
					if (theveryfirst)
					{
						shift += 14;
						theveryfirst = 0;
					}
					memcpy(dest + data_len, buffer + shift, 188 - shift);
					data_len += 188 - shift;
				}
			}

			rtppacket* nexttemp = (*beg)->next;
			free((*beg)->buf);
			free((*beg));
			(*beg) = nexttemp;

			if ((*beg) == scan)
			{
				loop = 0;
				break;
			}
			else if (buf->nAllocLen - data_len < 1500)
			{
				break;
			}


		}

		if ((*port_settings_changed) == 0 &&
			((data_len > 0 && ilclient_remove_event(video_decode, OMX_EventPortSettingsChanged, 131, 0, 0, 1) == 0) ||
			(data_len == 0 && ilclient_wait_for_event(video_decode, OMX_EventPortSettingsChanged, 131, 0, 0, 1,
				ILCLIENT_EVENT_ERROR | ILCLIENT_PARAMETER_CHANGED, 10000) == 0)))
		{
			*port_settings_changed = 1;

			if (ilclient_setup_tunnel(tunnel, 0, 0) != 0)
				return -7;

			ilclient_change_component_state(video_scheduler, OMX_StateExecuting);

			// now setup tunnel to video_render
			if (ilclient_setup_tunnel(tunnel + 1, 0, 1000) != 0)
				return -12;

			ilclient_change_component_state(video_render, OMX_StateExecuting);
		}

		const unsigned char sidedata[14] = { 0xea, 0x00, 0x00, 0x00,
			0x01, 0xce, 0x8c, 0x4d,
			0x9d, 0x10, 0x8e, 0x25, 0xe9, 0xfe };


		if (!loop)
		{
			memcpy(dest + data_len, sidedata, 14);
			data_len += 14;
			buf->nFlags |= OMX_BUFFERFLAG_ENDOFFRAME;
		}


		buf->nFilledLen = data_len;

		//printf("len:%d\n", data_len);
		
		buf->nOffset = 0;
		if (*first)
		{
			buf->nFlags |= OMX_BUFFERFLAG_STARTTIME;
			*first = 0;
		}else
			buf->nFlags |= OMX_BUFFERFLAG_TIME_UNKNOWN;


		



		if (OMX_EmptyThisBuffer(ILC_GET_HANDLE(video_decode), buf) != OMX_ErrorNone)
			return -6;
	}

}


int idrsockport = -1;
static void* addnullpacket(rtppacket* beg)
{
	struct sockaddr_in addr1, addr2;
	struct sockaddr_in sourceaddr;
	socklen_t addrlen = sizeof(sourceaddr);
	int fd, fd2;



	if ((fd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
	{
		perror("cannot create socket\n");
		return 0;
	}


	memset((char *)&addr1, 0, sizeof(addr1));
	addr1.sin_family = AF_INET;
	addr1.sin_addr.s_addr = inet_addr("192.168.101.1");
	addr1.sin_port = htons(1028);

	if (bind(fd, (struct sockaddr *)&addr1, sizeof(addr1)) < 0)
	{
		perror("bind failed");
		return 0;
	}

	if (idrsockport > 0)
	{
		if ((fd2 = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
		{
			perror("cannot create socket\n");
			return 0;
		}
		memset((char *)&addr2, 0, sizeof(addr2));
		addr2.sin_family = AF_INET;
		addr2.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
		addr2.sin_port = htons(idrsockport);
	}






	while (1)
	{
		beg->buf = malloc(2048 * sizeof(unsigned char));
		beg->recvlen = recvfrom(fd, beg->buf, 2048, 0, (struct sockaddr *)&sourceaddr, &addrlen);
		if (beg->recvlen <= 0)
		{
			free(beg->buf);
			free(beg);
			continue;
		}
		beg->seqnum = (beg->buf[2] << 8) + beg->buf[3];
		beg->next = NULL;
		break;

	}

	rtppacket* head = beg;
	rtppacket* oldhead = NULL;


	int numofpacket = 1;
	int osn = 0xFFFF & (beg->seqnum);
	int hold = 0;
	int sentseqnum = -1;

	while (1)
	{
		rtppacket* p1 = malloc(sizeof(rtppacket));
		p1->buf = malloc(2048 * sizeof(unsigned char));
		p1->recvlen = recvfrom(fd, p1->buf, 2048, 0, (struct sockaddr *)&sourceaddr, &addrlen);
		if (p1->recvlen <= 0)
		{
			free(p1->buf);
			free(p1);
			continue;
		}

		p1->seqnum = (p1->buf[2] << 8) + p1->buf[3];
		p1->next = NULL;

		if (largers(sentseqnum, p1->seqnum) && sentseqnum > 0)
		{
			printf("drop:%d\n", p1->seqnum);
			free(p1->buf);
			free(p1);
			continue;
		}

		if (numofpacket == 0)
		{
			head = p1;
		}
		else
		{
			rtppacket* currentp = head;
			rtppacket* prevp = NULL;


			while (currentp != NULL)
			{
				if (largers(currentp->seqnum, p1->seqnum))
				{
					if (prevp == NULL)
						head = p1;
					else
						prevp->next = p1;
					p1->next = currentp;
					break;
				}
				prevp = currentp;
				currentp = currentp->next;
			}


			if (currentp == NULL)//end
			{
				prevp->next = p1;
			}

		}

		numofpacket++;

		if (head->seqnum == osn)
		{
			hold = 0;

		}
		else if (numofpacket > 14)
		{
			hold = 0;
			printf("start:%d, end:%d\n", osn, head->seqnum);

			osn = head->seqnum;
			sentseqnum = osn;

		}
		else if (idrsockport > 0 && (numofpacket == 12))
		{
			unsigned char topython[12];
			if (sendto(fd2, topython, 12, 0, (struct sockaddr *)&addr2, addrlen) < 0)
				perror("sendto error");
			printf("idr:%d\n", numofpacket);
		}


		if (numofpacket > 0 && !hold && osn == head->seqnum && oldhead != NULL)
		{
			oldhead->next = head;
		}



		while (numofpacket > 0 && !hold)
		{
			if (osn != head->seqnum)
			{
				hold = 1;
				break;
			}

			sentseqnum = osn;

			osn = 0xFFFF & (osn + 1);
			oldhead = head;
			head = head->next;
			numofpacket--;
			atomic_fetch_add(&numofnode, 1);

		}

	}

}
int audiodest = 0;

static int video_decode_test(rtppacket* beg)
{
	OMX_VIDEO_PARAM_PORTFORMATTYPE format;
	OMX_TIME_CONFIG_CLOCKSTATETYPE cstate;
	COMPONENT_T *video_decode = NULL, *video_scheduler = NULL, *video_render = NULL, *clock = NULL, *audio_render = NULL;
	COMPONENT_T *list[5];
	TUNNEL_T tunnel[4];
	ILCLIENT_T *client;
	int status = 0;

	memset(list, 0, sizeof(list));
	memset(tunnel, 0, sizeof(tunnel));


	if ((client = ilclient_init()) == NULL)
		return -3;

	if (OMX_Init() != OMX_ErrorNone)
	{
		ilclient_destroy(client);
		return -4;
	}

	// create video_decode
	if (ilclient_create_component(client, &video_decode, "video_decode", ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS) != 0)
		status = -14;
	list[0] = video_decode;

	// create video_render
	if (status == 0 && ilclient_create_component(client, &video_render, "video_render", ILCLIENT_DISABLE_ALL_PORTS) != 0)
		status = -14;
	list[1] = video_render;

	// create clock
	if (status == 0 && ilclient_create_component(client, &clock, "clock", ILCLIENT_DISABLE_ALL_PORTS) != 0)
		status = -14;
	list[2] = clock;

	memset(&cstate, 0, sizeof(cstate));
	cstate.nSize = sizeof(cstate);
	cstate.nVersion.nVersion = OMX_VERSION;
	cstate.eState = OMX_TIME_ClockStateWaitingForStartTime;
	cstate.nWaitMask = 1;
	if (clock != NULL && OMX_SetParameter(ILC_GET_HANDLE(clock), OMX_IndexConfigTimeClockState, &cstate) != OMX_ErrorNone)
		status = -13;

	// create video_scheduler
	if (status == 0 && ilclient_create_component(client, &video_scheduler, "video_scheduler", ILCLIENT_DISABLE_ALL_PORTS) != 0)
		status = -14;
	list[3] = video_scheduler;

	if (audioplay_create(client, &audio_render, list, 4) != 0)
		printf("create error\n");

	if (audiodest == 1)
		audioplay_set_dest(audio_render, "local");
	else
		audioplay_set_dest(audio_render, "hdmi");

	set_tunnel(tunnel, video_decode, 131, video_scheduler, 10);
	set_tunnel(tunnel + 1, video_scheduler, 11, video_render, 90);
	set_tunnel(tunnel + 2, clock, 80, video_scheduler, 12);

	// setup clock tunnel first
	if (status == 0 && ilclient_setup_tunnel(tunnel + 2, 0, 0) != 0)
		status = -15;
	else
		ilclient_change_component_state(clock, OMX_StateExecuting);

	if (status == 0)
		ilclient_change_component_state(video_decode, OMX_StateIdle);

	memset(&format, 0, sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE));
	format.nSize = sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE);
	format.nVersion.nVersion = OMX_VERSION;
	format.nPortIndex = 130;
	format.eCompressionFormat = OMX_VIDEO_CodingAVC;

	//OMX_PARAM_PORTDEFINITIONTYPE portParam;
	//memset(&portParam, 0, sizeof(OMX_PARAM_PORTDEFINITIONTYPE));
	//portParam.nSize = sizeof(OMX_PARAM_PORTDEFINITIONTYPE);
	//portParam.nVersion.nVersion = OMX_VERSION;
	//if (OMX_GetParameter(ILC_GET_HANDLE(video_decode), OMX_IndexParamPortDefinition, &portParam) == OMX_ErrorNone)
	//	printf("get error\n");

	//portParam.nPortIndex = 130;
	//portParam.nBufferSize = 188;
	//if (OMX_SetParameter(ILC_GET_HANDLE(video_decode), OMX_IndexParamPortDefinition, &portParam) == OMX_ErrorNone)
	//	printf("set error\n");


	if (status == 0 &&
		OMX_SetParameter(ILC_GET_HANDLE(video_decode), OMX_IndexParamVideoPortFormat, &format) == OMX_ErrorNone &&
		ilclient_enable_port_buffers(video_decode, 130, NULL, NULL, NULL) == 0
		)
	{
		OMX_BUFFERHEADERTYPE *buf;
		int port_settings_changed = 0;

		ilclient_change_component_state(video_decode, OMX_StateExecuting);

		
		int oldcc = 0;
		int peserror = 1;
		int first = 1;
		int peslen = -100, actuallen = 0;
		unsigned char* oldlen = NULL;

		rtppacket*scan = beg;
		while (1)
		{
			int non = atomic_load(&numofnode);
			if (non < 2)
			{
				usleep(10);
				continue;
			}
			/*else if (non > 10)
			{
				printf("node:%d\n", non);
			}*/

			int numofts = (scan->recvlen - 12) / 188;
			for (int i = 0; i < numofts; i++)
			{
				unsigned char* buffer = scan->buf + 12 + i * 188;
				
				unsigned char sync = buffer[0];
				if (sync == 0x47)
				{
					int startindicator = buffer[1] & 0x40;
					short pid = ((0x1F & buffer[1]) << 8) + buffer[2];

					if (pid == 0x1011)
					{
						int ad = 3 & (buffer[3] >> 4);
						int cc = buffer[3] & 0x0F;
						if (cc != oldcc)
						{
							printf("oldcc %d cc %d\n", oldcc, cc);
							oldcc = cc;
							peserror = 1;
						}
						oldcc = 0xF & (oldcc + 1);


						if (ad & 1)
						{
							int adlen = buffer[4];
							int shift = (ad == 1) ? 4 : adlen + 5;
							if (buffer[shift] == 0 && buffer[shift + 1] == 0 && buffer[shift + 2] == 1)/////newpesstart
							{
								if (peserror == 0)
								{

									sendtodecoder(video_decode, video_scheduler, video_render, tunnel,
										buf, &beg, scan, &port_settings_changed, &first);

								}
								else
								{
									while (beg != scan)
									{
										rtppacket* nexttemp = beg->next;
										free(beg->buf);
										free(beg);
										beg = nexttemp;
									}
									first = 1;
								}
								peserror = 0;
							}
						}
					}else if (pid == 0x1100)
					{
						int ad = 3 & (buffer[3] >> 4);

						if (ad & 1)
						{
							int adlen = buffer[4];
							int shift = (ad == 1) ? 4 : adlen + 5;
							if (buffer[shift] == 0 && buffer[shift + 1] == 0 && buffer[shift + 2] == 1)/////newpesstart
							{
								shift += 20;
							}
							
							//for (int k = shift; k < 188; k = k + 2)
							//{
							//	
							//	int samp = (buffer[k]<<8)+buffer[k+1];
							//	samp = samp > 32767 ? samp - 65536 : samp;
							//	samp = samp *2;
							//	if (samp > 32767)
							//	{
							//		samp = 32767;
							//	}else if (samp < -32768)
							//	{
							//		samp = -32768;
							//	}

							//
							//	//printf("%d\n",samp);

							//	buffer[k + 1] = samp >> 8;
							//	buffer[k] = samp & 0xFF;
							//}

							if (audioplay_play_buffer(audio_render, buffer + shift, 188 - shift) < 0)
								printf("sound error\n");



						}
					}






					
				}
				
			}
			atomic_fetch_sub(&numofnode, 1);
			scan = scan->next;
		}

		buf->nFilledLen = 0;
		buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN | OMX_BUFFERFLAG_EOS;

		if (OMX_EmptyThisBuffer(ILC_GET_HANDLE(video_decode), buf) != OMX_ErrorNone)
			status = -20;

		// wait for EOS from render
		ilclient_wait_for_event(video_render, OMX_EventBufferFlag, 90, 0, OMX_BUFFERFLAG_EOS, 0,
			ILCLIENT_BUFFER_FLAG_EOS, -1);

		// need to flush the renderer to allow video_decode to disable its input port
		ilclient_flush_tunnels(tunnel, 0);

	}


	ilclient_disable_tunnel(tunnel);
	ilclient_disable_tunnel(tunnel + 1);
	ilclient_disable_tunnel(tunnel + 2);
	ilclient_disable_port_buffers(video_decode, 130, NULL, NULL, NULL);
	ilclient_teardown_tunnels(tunnel);

	ilclient_state_transition(list, OMX_StateIdle);
	ilclient_state_transition(list, OMX_StateLoaded);

	ilclient_cleanup_components(list);

	OMX_Deinit();

	ilclient_destroy(client);
	return status;
}

int main(int argc, char **argv)
{
	if (argc > 1)
	{
		idrsockport = atoi(argv[1]);
		printf("idrport:%d\n", idrsockport);
	}
	if (argc > 2)
	{
		audiodest = atoi(argv[2]);
		printf("audiodest:%d\n", audiodest);
	}

	atomic_store(&numofnode, 0);

	pthread_t npthread;
	pthread_t dthread;
	
	rtppacket* beg = malloc(sizeof(rtppacket));

	if (pthread_create(&npthread, NULL, addnullpacket, beg) != 0)
		exit(1);
	if (pthread_create(&dthread, NULL, video_decode_test, beg) != 0)
		exit(1);

	bcm_host_init();

	if (pthread_join(npthread, NULL) != 0)
		exit(1);
	if (pthread_join(dthread, NULL) != 0)
		exit(1);

	return 0;

}


