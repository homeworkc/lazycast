/*
Copyright (c) 2012, Broadcom Europe Ltd
All rights reserved.

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

// Audio output demo using OpenMAX IL though the ilcient helper library

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>

#include "bcm_host.h"
#include "ilclient.h"
#include <alsa/asoundlib.h>


typedef int int32_t;
static uint32_t audioplay_alsapcm_init(void);

snd_pcm_t *pcm_dev = NULL;
uint8_t is_alsa = 0;


int32_t audioplay_create(ILCLIENT_T *client, COMPONENT_T** audio_render, COMPONENT_T **list, int listindex)
{
   int32_t ret = -1;

	int size = 4096;


	OMX_ERRORTYPE error;
	OMX_PARAM_PORTDEFINITIONTYPE param;
	OMX_AUDIO_PARAM_PCMMODETYPE pcm;

	ret = 0;


	ilclient_create_component(client, audio_render, "audio_render", ILCLIENT_ENABLE_INPUT_BUFFERS | ILCLIENT_DISABLE_ALL_PORTS);
	assert(*audio_render != NULL);

	list[listindex] = *audio_render;

	// set up the number/size of buffers
	memset(&param, 0, sizeof(OMX_PARAM_PORTDEFINITIONTYPE));
	param.nSize = sizeof(OMX_PARAM_PORTDEFINITIONTYPE);
	param.nVersion.nVersion = OMX_VERSION;
	param.nPortIndex = 100;

	error = OMX_GetParameter(ILC_GET_HANDLE(*audio_render), OMX_IndexParamPortDefinition, &param);
	assert(error == OMX_ErrorNone);

	param.nBufferSize = size;
	param.nBufferCountActual = 4;
	//param.nBufferCountActual = num_buffers;

	error = OMX_SetParameter(ILC_GET_HANDLE(*audio_render), OMX_IndexParamPortDefinition, &param);
	assert(error == OMX_ErrorNone);

	// set the pcm parameters
	memset(&pcm, 0, sizeof(OMX_AUDIO_PARAM_PCMMODETYPE));
	pcm.nSize = sizeof(OMX_AUDIO_PARAM_PCMMODETYPE);
	pcm.nVersion.nVersion = OMX_VERSION;
	pcm.nPortIndex = 100;
	pcm.nChannels = 2;
	pcm.eNumData = OMX_NumericalDataSigned;
	pcm.eEndian = OMX_EndianBig;
	pcm.nSamplingRate = 48000;
	pcm.bInterleaved = OMX_TRUE;
	pcm.nBitPerSample = 16;
	pcm.ePCMMode = OMX_AUDIO_PCMModeLinear;

	pcm.eChannelMapping[1] = OMX_AUDIO_ChannelRF;
	pcm.eChannelMapping[0] = OMX_AUDIO_ChannelLF;

	error = OMX_SetParameter(ILC_GET_HANDLE(*audio_render), OMX_IndexParamAudioPcm, &pcm);
	assert(error == OMX_ErrorNone);

	ilclient_change_component_state(*audio_render, OMX_StateIdle);
	if(ilclient_enable_port_buffers(*audio_render, 100, NULL, NULL, NULL) < 0)
	{
		// error
		ilclient_change_component_state(*audio_render, OMX_StateLoaded);

		return -1;
	}

	ilclient_change_component_state(*audio_render, OMX_StateExecuting);

	return ret;
}

int32_t audioplay_delete(COMPONENT_T *audio_render)
{
   OMX_ERRORTYPE error;

   ilclient_change_component_state(audio_render, OMX_StateIdle);

   error = OMX_SendCommand(ILC_GET_HANDLE(audio_render), OMX_CommandStateSet, OMX_StateLoaded, NULL);
   assert(error == OMX_ErrorNone);

   ilclient_change_component_state(audio_render, OMX_StateLoaded);

   assert(error == OMX_ErrorNone);


   return 0;
}



int32_t audioplay_play_buffer(COMPONENT_T *audio_render, uint8_t *buffer, uint32_t length)
{
	if(is_alsa) {
		
	}
	else {
		OMX_BUFFERHEADERTYPE *hdr = ilclient_get_input_buffer(audio_render, 100, 0);
		int32_t ret = -1;

		if (hdr == NULL)
			return ret;

		OMX_ERRORTYPE error;

		hdr->nOffset = 0;
		memcpy(hdr->pBuffer, buffer, length);
		hdr->nFilledLen = length;

		error = OMX_EmptyThisBuffer(ILC_GET_HANDLE(audio_render), hdr);
		assert(error == OMX_ErrorNone);
	}
	return 0;
}

int32_t audioplay_set_dest(COMPONENT_T *audio_render, const char *name)
{
	int32_t success = -1;
	OMX_CONFIG_BRCMAUDIODESTINATIONTYPE ar_dest;

	if (name && strlen(name) < sizeof(ar_dest.sName))
	{
		printf("set audio backend :%s\n", name);
		if(strcmp(name, "alsa") == 0) {
			is_alsa = 1;

			audioplay_alsapcm_init();
		}
		else {
			is_alsa = 0;

			OMX_ERRORTYPE error;
			memset(&ar_dest, 0, sizeof(ar_dest));
			ar_dest.nSize = sizeof(OMX_CONFIG_BRCMAUDIODESTINATIONTYPE);
			ar_dest.nVersion.nVersion = OMX_VERSION;
			strcpy((char *)ar_dest.sName, name);

			error = OMX_SetConfig(ILC_GET_HANDLE(audio_render), OMX_IndexConfigBrcmAudioDestination, &ar_dest);
			assert(error == OMX_ErrorNone);
		}
		success = 0;
	}

	return success;
}

static uint32_t audioplay_alsapcm_init(void)
{
	int err, retry_times;
	unsigned int rate;
	snd_pcm_hw_params_t *hwp;
	snd_pcm_uframes_t buffer_size, period_size, period_size_max;

	retry_times = 0;
reopen:
	printf("alsa pcm init ...\n");
	err = snd_pcm_open(&pcm_dev, "default", SND_PCM_STREAM_PLAYBACK, 0);
	if (err < 0) {
		if(++retry_times > 2) {
			goto alsa_error;
		}
		else {
			usleep(300);
			goto reopen;
		}
	}
	retry_times = 0;

	rate = 48000;
	buffer_size = rate / 5;
	period_size = buffer_size / 4;
	period_size_max = buffer_size / 3;

	printf("alsa open success\n");
	snd_pcm_hw_params_alloca(&hwp);
	snd_pcm_hw_params_any(pcm_dev, hwp);
	err = snd_pcm_hw_params_set_channels(pcm_dev, hwp, 2);
	if (err)
		goto alsa_error;
	err = snd_pcm_hw_params_set_access(pcm_dev, hwp, SND_PCM_ACCESS_RW_INTERLEAVED);
	if (err)
		goto alsa_error;
	err = snd_pcm_hw_params_set_rate_near(pcm_dev, hwp, &rate, 0);
	if (err)
		goto alsa_error;
	err = snd_pcm_hw_params_set_format(pcm_dev, hwp, SND_PCM_FORMAT_S16_LE);
	if (err)
		goto alsa_error;
	err = snd_pcm_hw_params_set_period_size_max(pcm_dev, hwp, &period_size_max, 0);
	if (err)
		goto alsa_error;
	err = snd_pcm_hw_params_set_buffer_size_near(pcm_dev, hwp, &buffer_size);
	if (err)
		goto alsa_error;
	err = snd_pcm_hw_params_set_period_size_near(pcm_dev, hwp, &period_size, 0);
	if (err) goto alsa_error;
	err = snd_pcm_hw_params(pcm_dev, hwp);
	if (err)
		goto alsa_error;
	printf("alsa config success\n");

	int dir;
	snd_pcm_hw_params_get_rate(hwp, &rate, &dir);
	printf("rate = %d bps\n", rate);

	snd_pcm_hw_params_get_period_time(hwp, &rate, &dir);
	printf("period time = %d us\n", rate);

	snd_pcm_hw_params_get_period_size(hwp, &period_size_max, &dir);
	printf("period size = %d frames\n", (int)period_size_max);

	snd_pcm_hw_params_get_buffer_time(hwp, &rate, &dir);
	printf("buffer time = %d us\n", rate);

	snd_pcm_hw_params_get_buffer_size(hwp, (snd_pcm_uframes_t *) &buffer_size);
	printf("buffer size = %d frames\n", buffer_size);

	snd_pcm_hw_params_get_periods(hwp, &rate, &dir);
	printf("periods per buffer = %d frames\n", rate);

	return 0;
alsa_error:
	if (pcm_dev)
		snd_pcm_close(pcm_dev);

	return 1;
}

uint32_t audioplay_get_latency(COMPONENT_T *audio_render)
{
	OMX_PARAM_U32TYPE param;
	OMX_ERRORTYPE error;

	memset(&param, 0, sizeof(OMX_PARAM_U32TYPE));
	param.nSize = sizeof(OMX_PARAM_U32TYPE);
	param.nVersion.nVersion = OMX_VERSION;
	param.nPortIndex = 100;

	error = OMX_GetConfig(ILC_GET_HANDLE(audio_render), OMX_IndexConfigAudioRenderingLatency, &param);
	assert(error == OMX_ErrorNone);

	return param.nU32;
}


