#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdatomic.h>
#include <pthread.h>

#include <OMX_Core.h>
#include <OMX_Component.h>

#include <bcm_host.h>
#include <vcos_logging.h>

#define VCOS_LOG_CATEGORY (&il_ffmpeg_log_category)
static VCOS_LOG_CAT_T il_ffmpeg_log_category;

#include <ilclient.h>

#include "libavcodec/avcodec.h"
#include <libavformat/avformat.h>


static AVCodecContext *video_dec_ctx = NULL;
static AVCodecContext *audio_dec_ctx = NULL;
AVCodecContext* codec_context;


static AVStream *video_stream = NULL;
static AVStream *audio_stream = NULL;
static AVPacket pkt;
AVFormatContext *pFormatCtx = NULL;

static int video_stream_idx = -1;
static int audio_stream_idx = -1;


uint8_t extradatasize;
void *extradata;

AVCodec *codec;

void printState(OMX_HANDLETYPE handle) 
{
    // elided
}

char *err2str(int err) 
{
    return "error";
}

void printClockState(COMPONENT_T *clockComponent) 
{
    OMX_ERRORTYPE err = OMX_ErrorNone;
    OMX_TIME_CONFIG_CLOCKSTATETYPE clockState;

    memset(&clockState, 0, sizeof( OMX_TIME_CONFIG_CLOCKSTATETYPE));
    clockState.nSize = sizeof( OMX_TIME_CONFIG_CLOCKSTATETYPE);
    clockState.nVersion.nVersion = OMX_VERSION;

    err = OMX_GetConfig(ilclient_get_handle(clockComponent), 
			OMX_IndexConfigTimeClockState, &clockState);
    if (err != OMX_ErrorNone) 
	{
        fprintf(stderr, "Error getting clock state %s\n", err2str(err));
        return;
    }
    switch (clockState.eState) 
	{
		case OMX_TIME_ClockStateRunning:
		printf("Clock running\n");
		break;
		case OMX_TIME_ClockStateWaitingForStartTime:
		printf("Clock waiting for start time\n");
		break;
		case OMX_TIME_ClockStateStopped:
		printf("Clock stopped\n");
		break;
		default:
		printf("Clock in other state\n");
    }
}

void startClock(COMPONENT_T *clockComponent) 
{
    OMX_ERRORTYPE err = OMX_ErrorNone;
    OMX_TIME_CONFIG_CLOCKSTATETYPE clockState;

    memset(&clockState, 0, sizeof( OMX_TIME_CONFIG_CLOCKSTATETYPE));
    clockState.nSize = sizeof( OMX_TIME_CONFIG_CLOCKSTATETYPE);
    clockState.nVersion.nVersion = OMX_VERSION;

    err = OMX_GetConfig(ilclient_get_handle(clockComponent), OMX_IndexConfigTimeClockState, &clockState);
    if (err != OMX_ErrorNone) 
	{
        fprintf(stderr, "Error getting clock state %s\n", err2str(err));
        return;
    }
    clockState.eState = OMX_TIME_ClockStateRunning;
    err = OMX_SetConfig(ilclient_get_handle(clockComponent), 
			OMX_IndexConfigTimeClockState, &clockState);
    if (err != OMX_ErrorNone) 
	{
        fprintf(stderr, "Error starting clock %s\n", err2str(err));
        return;
    }

}

void eos_callback(void *userdata, COMPONENT_T *comp, OMX_U32 data) 
{
    printf("Got eos event\n");
}

void error_callback(void *userdata, COMPONENT_T *comp, OMX_U32 data) 
{
    printf("OMX error %s\n", err2str(data));
}

void port_settings_callback(void *userdata, COMPONENT_T *comp, OMX_U32 data) 
{
    printf("Got port Settings event\n");
    // exit(0);
}

void empty_buffer_done_callback(void *userdata, COMPONENT_T *comp) 
{
    //printf("Got empty buffer done\n");
}


unsigned int uWidth;
unsigned int uHeight;

unsigned int fpsscale;
unsigned int fpsrate;
unsigned int time_base_num;
unsigned int time_base_den;

#ifdef OMX_SKIP64BIT
OMX_TICKS ToOMXTime(int64_t pts)
{
    OMX_TICKS ticks;
    ticks.nLowPart = pts;
    ticks.nHighPart = pts >> 32;
    return ticks;
}
#else
#define FromOMXTime(x) (x)
#endif

static int starting = 1;
static long int startpts;


OMX_ERRORTYPE copy_into_buffer_and_empty(AVPacket *pkt,COMPONENT_T *component,OMX_BUFFERHEADERTYPE *buff_header) 
{
    OMX_ERRORTYPE r;

    int buff_size = buff_header->nAllocLen;
    int size = pkt->size;
    uint8_t *content = pkt->data;
	

    while (size > 0) 
	{
		buff_header->nFilledLen = (size > buff_header->nAllocLen-1) ?
			buff_header->nAllocLen-1 : size;
		memset(buff_header->pBuffer, 0x0, buff_header->nAllocLen);
		memcpy(buff_header->pBuffer, content, buff_header->nFilledLen);
		size -= buff_header->nFilledLen;
		content += buff_header->nFilledLen;
    
	
		buff_header->nFlags = 0;
		if (size <= 0) 
			buff_header->nFlags |= OMX_BUFFERFLAG_ENDOFFRAME;

	
		if (starting==0)
		{
			long int rpts = pkt->pts - startpts;
			buff_header->nTimeStamp = ToOMXTime((uint64_t)(rpts * 1000000 / time_base_den));
			//printf("rpts:%d\n", rpts);
		}
		else
		{
			startpts = pkt->pts;
			buff_header->nFlags |= OMX_BUFFERFLAG_STARTTIME;
			starting = 0;
		}



		r = OMX_EmptyThisBuffer(ilclient_get_handle(component),	buff_header);
		/*
		if (r != OMX_ErrorNone) 
		{
			fprintf(stderr, "Empty buffer error %s\n",err2str(r));
		} else 
		{
			printf("Emptying buffer %p\n", buff_header);
		}
		*/


		if (size > 0) 
		{
			 buff_header = ilclient_get_input_buffer(component, 130,  1 /* block */);
		}
    }
    return r;
}

int img_width, img_height;

int SendDecoderConfig(COMPONENT_T *component)
{
    OMX_ERRORTYPE omx_err   = OMX_ErrorNone;

    /* send decoder config */
    if(extradatasize > 0 && extradata != NULL)
	{

	    OMX_BUFFERHEADERTYPE *omx_buffer = ilclient_get_input_buffer(component,130, 1 /* block */);

	    if(omx_buffer == NULL)
		{
		    fprintf(stderr, "%s - buffer error 0x%08x", __func__, omx_err);
		    return 0;
		}

	    omx_buffer->nOffset = 0;
	    omx_buffer->nFilledLen = extradatasize;
	    if(omx_buffer->nFilledLen > omx_buffer->nAllocLen)
		{
		    fprintf(stderr, "%s - omx_buffer->nFilledLen > omx_buffer->nAllocLen",  __func__);
		    return 0;
		}

	    memset((unsigned char *)omx_buffer->pBuffer, 0x0, omx_buffer->nAllocLen);
	    memcpy((unsigned char *)omx_buffer->pBuffer, extradata, omx_buffer->nFilledLen);
	    omx_buffer->nFlags = OMX_BUFFERFLAG_CODECCONFIG | OMX_BUFFERFLAG_ENDOFFRAME;
  
	    omx_err =  OMX_EmptyThisBuffer(ilclient_get_handle(component), omx_buffer);
	    if (omx_err != OMX_ErrorNone)
		{
		    fprintf(stderr, "%s - OMX_EmptyThisBuffer() failed with result(0x%x)\n", __func__, omx_err);
		    return 0;
		} else 
		{
			printf("Config sent, emptying buffer %d\n", extradatasize);
	    }
	}
    return 1;
}

OMX_ERRORTYPE set_video_decoder_input_format(COMPONENT_T *component) 
{
    int err;

    // set input video format
    printf("Setting video decoder format\n");
    OMX_VIDEO_PARAM_PORTFORMATTYPE videoPortFormat;

    memset(&videoPortFormat, 0, sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE));
    videoPortFormat.nSize = sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE);
    videoPortFormat.nVersion.nVersion = OMX_VERSION;
    videoPortFormat.nPortIndex = 130;

    err = OMX_GetParameter(ilclient_get_handle(component),
			   OMX_IndexParamVideoPortFormat, &videoPortFormat);
    if (err != OMX_ErrorNone) 
	{
        fprintf(stderr, "Error getting video decoder format %s\n", err2str(err));
        return err;
    }

    videoPortFormat.nPortIndex = 130;
    videoPortFormat.nIndex = 0;
    videoPortFormat.eCompressionFormat = OMX_VIDEO_CodingAVC;
    videoPortFormat.eColorFormat = OMX_COLOR_FormatUnused;
    videoPortFormat.xFramerate = 0;

// doesn't seem to make any difference!!!
	videoPortFormat.xFramerate = (long long)(1<<16)*fpsrate / fpsscale;
    printf("FPS num %d den %d\n", fpsrate, fpsscale);
    printf("Set frame rate to %d\n", videoPortFormat.xFramerate);
   //
	err = OMX_SetParameter(ilclient_get_handle(component), OMX_IndexParamVideoPortFormat, &videoPortFormat);
    if (err != OMX_ErrorNone) 
	{
        fprintf(stderr, "Error setting video decoder format %s\n", err2str(err));
        return err;
    } else 
	{
        printf("Video decoder format set up ok\n");
    }

    OMX_PARAM_PORTDEFINITIONTYPE portParam;
    memset(&portParam, 0, sizeof( OMX_PARAM_PORTDEFINITIONTYPE));
    portParam.nSize = sizeof( OMX_PARAM_PORTDEFINITIONTYPE);
    portParam.nVersion.nVersion = OMX_VERSION;

    portParam.nPortIndex = 130;

    err =  OMX_GetParameter(ilclient_get_handle(component), OMX_IndexParamPortDefinition, &portParam);
    if(err != OMX_ErrorNone)
	{
	    fprintf(stderr, "COMXVideo::Open error OMX_IndexParamPortDefinition omx_err(0x%08x)\n", err);
	    return err;
	}

    printf("Default framerate %d\n", portParam.format.video.xFramerate);

    portParam.nPortIndex = 130;
	portParam.nBufferSize = 163840*2;
    portParam.format.video.nFrameWidth  = img_width;
    portParam.format.video.nFrameHeight = img_height;

    err =  OMX_SetParameter(ilclient_get_handle(component), OMX_IndexParamPortDefinition, &portParam);
    if(err != OMX_ErrorNone)
	{
	    fprintf(stderr, "COMXVideo::Open error OMX_IndexParamPortDefinition omx_err(0x%08x)\n", err);
	    return err;
	}

    return OMX_ErrorNone;
}

int setup_demuxer(const char *filename) {
    // Register all formats and codecs
    av_register_all();
    if(avformat_open_input(&pFormatCtx, filename, NULL, NULL)!=0) {
	fprintf(stderr, "Can't get format\n");
        return -1; // Couldn't open file
    }
    // Retrieve stream information
    if (avformat_find_stream_info(pFormatCtx, NULL) < 0) {
	return -1; // Couldn't find stream information
    }
    printf("Format:\n");
    av_dump_format(pFormatCtx, 0, filename, 0);

    int ret;
    ret = av_find_best_stream(pFormatCtx, AVMEDIA_TYPE_VIDEO, -1, -1, NULL, 0);
    if (ret >= 0) 
	{
		video_stream_idx = ret;

		video_stream = pFormatCtx->streams[video_stream_idx];
		video_dec_ctx = video_stream->codec;

		img_width         = video_stream->codec->width;
		img_height        = video_stream->codec->height;
		extradata         = video_stream->codec->extradata;
		extradatasize     = video_stream->codec->extradata_size;
		fpsscale          = video_stream->r_frame_rate.den;
		fpsrate           = video_stream->r_frame_rate.num;
		time_base_num         = video_stream->time_base.num;
		time_base_den         = video_stream->time_base.den;

		printf("Rate %d scale %d time base %d %d\n",
			   video_stream->r_frame_rate.num,
			   video_stream->r_frame_rate.den,
			   video_stream->time_base.num,
			   video_stream->time_base.den);

		AVCodec *codec = avcodec_find_decoder(video_stream->codec->codec_id);
	
		if (codec) 
		{
			printf("Codec name %s\n", codec->name);
		}
    }
	ret = av_find_best_stream(pFormatCtx, AVMEDIA_TYPE_AUDIO, -1, -1, NULL, 0);
	if (ret >= 0)
	{
		audio_stream_idx = ret;

		audio_stream = pFormatCtx->streams[audio_stream_idx];
		audio_dec_ctx = audio_stream->codec;


		AVCodec *codec = avcodec_find_decoder(audio_stream->codec->codec_id);
		codec_context = avcodec_alloc_context3(codec);
		if (codec)
		{
			printf("Codec name %s\n", codec->name);
		}

		if (!avcodec_open2(codec_context, codec, NULL) < 0)
		{
			fprintf(stderr, "Could not find open the needed codec");
			exit(1);
		}
	}
	else
	{
		audio_stream_idx = 1;

		audio_stream = pFormatCtx->streams[audio_stream_idx];
		audio_dec_ctx = audio_stream->codec;


		AVCodec *codec = avcodec_find_decoder(AV_CODEC_ID_AAC);
		codec_context = avcodec_alloc_context3(codec);
		if (codec)
		{
			printf("Codec name %s\n", codec->name);
		}

		if (!avcodec_open2(codec_context, codec, NULL) < 0)
		{
			fprintf(stderr, "Could not find open the needed codec");
			exit(1);
		}
	}




    return 0;
}

void setup_decodeComponent(ILCLIENT_T  *handle, char *decodeComponentName, COMPONENT_T **decodeComponent) 
{
    int err;

    err = ilclient_create_component(handle,
				    decodeComponent,
				    decodeComponentName,
				    ILCLIENT_DISABLE_ALL_PORTS
				    |
				    ILCLIENT_ENABLE_INPUT_BUFFERS
				    |
				    ILCLIENT_ENABLE_OUTPUT_BUFFERS
				    );
    if (err == -1) 
	{
		fprintf(stderr, "DecodeComponent create failed\n");
		exit(1);
    }
    printState(ilclient_get_handle(*decodeComponent));

    err = ilclient_change_component_state(*decodeComponent, OMX_StateIdle);
    if (err < 0) 
	{
		fprintf(stderr, "Couldn't change state to Idle\n");
		exit(1);
    }
    printState(ilclient_get_handle(*decodeComponent));

    // must be before we enable buffers
    set_video_decoder_input_format(*decodeComponent);
}

void setup_renderComponent(ILCLIENT_T  *handle,char *renderComponentName, COMPONENT_T **renderComponent) 
{
    int err;

    err = ilclient_create_component(handle, renderComponent,  renderComponentName,
		ILCLIENT_DISABLE_ALL_PORTS  | ILCLIENT_ENABLE_INPUT_BUFFERS);
    if (err == -1) 
	{
		fprintf(stderr, "RenderComponent create failed\n");
		exit(1);
    }
    printState(ilclient_get_handle(*renderComponent));

    err = ilclient_change_component_state(*renderComponent,  OMX_StateIdle);
    if (err < 0) 
	{
		fprintf(stderr, "Couldn't change state to Idle\n");
		exit(1);
    }
    printState(ilclient_get_handle(*renderComponent));
}

void setup_schedulerComponent(ILCLIENT_T  *handle,char *schedulerComponentName, COMPONENT_T **schedulerComponent) 
{
    int err;

    err = ilclient_create_component(handle, schedulerComponent,schedulerComponentName,
				    ILCLIENT_DISABLE_ALL_PORTS  | ILCLIENT_ENABLE_INPUT_BUFFERS);
    if (err == -1) 
	{
		fprintf(stderr, "SchedulerComponent create failed\n");
		exit(1);
    }
    printState(ilclient_get_handle(*schedulerComponent));

    err = ilclient_change_component_state(*schedulerComponent,	  OMX_StateIdle);
    if (err < 0) 
	{
		fprintf(stderr, "Couldn't change state to Idle\n");
		exit(1);
    }
    printState(ilclient_get_handle(*schedulerComponent));
}

void setup_clockComponent(ILCLIENT_T  *handle, char *clockComponentName,COMPONENT_T **clockComponent) 
{
    int err;

    err = ilclient_create_component(handle, clockComponent,clockComponentName,
				    ILCLIENT_DISABLE_ALL_PORTS);
    if (err == -1) 
	{
		fprintf(stderr, "ClockComponent create failed\n");
		exit(1);
    }
    printState(ilclient_get_handle(*clockComponent));

    err = ilclient_change_component_state(*clockComponent, OMX_StateIdle);
    if (err < 0) 
	{
		fprintf(stderr, "Couldn't change state to Idle\n");
		exit(1);
    }
    printState(ilclient_get_handle(*clockComponent));
    printClockState(*clockComponent);

    OMX_COMPONENTTYPE*clock = ilclient_get_handle(*clockComponent);

    OMX_TIME_CONFIG_ACTIVEREFCLOCKTYPE refClock;
    refClock.nSize = sizeof(OMX_TIME_CONFIG_ACTIVEREFCLOCKTYPE);
    refClock.nVersion.nVersion = OMX_VERSION;
    refClock.eClock = OMX_TIME_RefClockVideo; // OMX_CLOCKPORT0;

    err = OMX_SetConfig(ilclient_get_handle(*clockComponent), OMX_IndexConfigTimeActiveRefClock, &refClock);
    if(err != OMX_ErrorNone) 
	{
		fprintf(stderr, "COMXCoreComponent::SetConfig - %s failed with omx_err(0x%x)\n", "clock", err);
    }

    OMX_TIME_CONFIG_SCALETYPE scaleType;
    scaleType.nSize = sizeof(OMX_TIME_CONFIG_SCALETYPE);
    scaleType.nVersion.nVersion = OMX_VERSION;
    scaleType.xScale = 0x00010000;

    err = OMX_SetConfig(ilclient_get_handle(*clockComponent), 
			OMX_IndexConfigTimeScale, &scaleType);
    if(err != OMX_ErrorNone) 
	{
		fprintf(stderr, "COMXCoreComponent::SetConfig - %s failed with omx_err(0x%x)\n", "clock", err);
    }
}

static void set_audio_render_input_format(COMPONENT_T *component)
{
	// set input audio format
	printf("Setting audio render format\n");
	OMX_AUDIO_PARAM_PORTFORMATTYPE audioPortFormat;
	memset(&audioPortFormat, 0, sizeof(OMX_AUDIO_PARAM_PORTFORMATTYPE));
	audioPortFormat.nSize = sizeof(OMX_AUDIO_PARAM_PORTFORMATTYPE);
	audioPortFormat.nVersion.nVersion = OMX_VERSION;
	audioPortFormat.nPortIndex = 100;
	OMX_GetParameter(ilclient_get_handle(component), OMX_IndexParamAudioPortFormat, &audioPortFormat);
	audioPortFormat.eEncoding = OMX_AUDIO_CodingPCM;
	OMX_SetParameter(ilclient_get_handle(component), OMX_IndexParamAudioPortFormat, &audioPortFormat);

	OMX_AUDIO_PARAM_PCMMODETYPE sPCMMode;
	OMX_ERRORTYPE err;
	memset(&sPCMMode, 0, sizeof(OMX_AUDIO_PARAM_PCMMODETYPE));
	sPCMMode.nSize = sizeof(OMX_AUDIO_PARAM_PCMMODETYPE);
	sPCMMode.nVersion.nVersion = OMX_VERSION;
	sPCMMode.nPortIndex = 100;
	err = OMX_GetParameter(ilclient_get_handle(component), OMX_IndexParamAudioPcm, &sPCMMode);

	sPCMMode.nSamplingRate = 48000; // for anything
	sPCMMode.nChannels = 2;
	err = OMX_SetParameter(ilclient_get_handle(component), OMX_IndexParamAudioPcm, &sPCMMode);
	if (err != OMX_ErrorNone)
	{
		fprintf(stderr, "PCM mode unsupported\n");
		return;
	}



}

void setOutputDevice(OMX_HANDLETYPE handle, const char *name)
{
	OMX_ERRORTYPE err;
	OMX_CONFIG_BRCMAUDIODESTINATIONTYPE arDest;

	if (name && strlen(name) < sizeof(arDest.sName))
	{
		memset(&arDest, 0, sizeof(OMX_CONFIG_BRCMAUDIODESTINATIONTYPE));
		arDest.nSize = sizeof(OMX_CONFIG_BRCMAUDIODESTINATIONTYPE);
		arDest.nVersion.nVersion = OMX_VERSION;

		strcpy((char *)arDest.sName, name);

		err = OMX_SetParameter(handle, OMX_IndexConfigBrcmAudioDestination, &arDest);
		if (err != OMX_ErrorNone)
		{
			fprintf(stderr, "Error on setting audio destination\n");
			exit(1);
		}
	}
}

void setup_audio_renderComponent(ILCLIENT_T  *handle, char *componentName, COMPONENT_T **component)
{
	int err;
	err = ilclient_create_component(handle, component, componentName,
		ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS);
	if (err == -1)
	{
		fprintf(stderr, "Component create failed\n");
		exit(1);
	}
	printState(ilclient_get_handle(*component));

	err = ilclient_change_component_state(*component, OMX_StateIdle);
	if (err < 0)
	{
		fprintf(stderr, "Couldn't change state to Idle\n");
		exit(1);
	}
	printState(ilclient_get_handle(*component));

	// must be before we enable buffers
	set_audio_render_input_format(*component);

	setOutputDevice(ilclient_get_handle(*component), "hdmi");

	// input port
	ilclient_enable_port_buffers(*component, 100, NULL, NULL, NULL);
	ilclient_enable_port(*component, 100);

	err = ilclient_change_component_state(*component, OMX_StateExecuting);
	if (err < 0)
	{
		fprintf(stderr, "Couldn't change state to Executing\n");
		exit(1);
	}
	printState(ilclient_get_handle(*component));
}

uint32_t audioplay_get_latency(COMPONENT_T *component)
{
	OMX_PARAM_U32TYPE param;
	OMX_ERRORTYPE error;

	memset(&param, 0, sizeof(OMX_PARAM_U32TYPE));
	param.nSize = sizeof(OMX_PARAM_U32TYPE);
	param.nVersion.nVersion = OMX_VERSION;
	param.nPortIndex = 100;

	error = OMX_GetConfig(ilclient_get_handle(component), OMX_IndexConfigAudioRenderingLatency, &param);

	return param.nU32;
}
int latmax = 3000;
OMX_ERRORTYPE read_audio_into_buffer_and_empty(AVFrame *decoded_frame, COMPONENT_T *component)   // OMX_BUFFERHEADERTYPE *buff_header
{
	uint32_t latency = audioplay_get_latency(component);
	//printf("%d\n", latency);

	if (latency > latmax)
	{
		printf("drop, %d\n", latency);
		return 0;
	}
	else if (latency<1000)
	{
		latmax = 9600;
	}

	if (latmax > 6000)
		latmax -= 20;

	OMX_ERRORTYPE r;
	OMX_BUFFERHEADERTYPE *buff_header = NULL;


	int16_t sbuffer[2 * 1024];

	float* fbuffer1 = (float*)(decoded_frame->extended_data[0]);
	float* fbuffer2 = (float*)(decoded_frame->extended_data[1]);
	int j = 0;
	for (int i = 0; i < 1024; i++)
	{
		sbuffer[j++] = (short)(fbuffer1[i] * 32767.0f);
		sbuffer[j++] = (short)(fbuffer2[i] * 32767.0f);
	}



	buff_header = ilclient_get_input_buffer(component, 100, 1);

	memcpy(buff_header->pBuffer, sbuffer, 4096);
	buff_header->nFilledLen = 4096;

	r = OMX_EmptyThisBuffer(ilclient_get_handle(component), buff_header);


	return r;
}


atomic_int numofnode = 0;

typedef struct Node
{
	AVPacket* pbuff;
	struct Node* next;
} Nodetype;


static void * receivepkt(Nodetype* oldnode)
{
	while(1)
	{
		if (av_read_frame(pFormatCtx, &pkt) < 0)
			continue;
		if (numofnode < 0)
		{
			printf("terminate\n");
			break;
		}

		oldnode->pbuff = malloc(sizeof(AVPacket));
		

		(*oldnode->pbuff) = pkt;
		oldnode->next = malloc(sizeof(Nodetype));

		Nodetype* pnext = oldnode->next;
		pnext->next = NULL;

		oldnode = pnext;
		atomic_fetch_add(&numofnode, 1);
	}


}

int main(int argc, char** argv) 
{
	char *audiorenderComponentName;
    char *decodeComponentName;
    char *renderComponentName;
    char *schedulerComponentName;
    char *clockComponentName;
    int err;
    ILCLIENT_T  *handle;
	COMPONENT_T *audiorenderComponent;
    COMPONENT_T *decodeComponent;
    COMPONENT_T *renderComponent;
    COMPONENT_T *schedulerComponent;
    COMPONENT_T *clockComponent;

    

    OMX_BUFFERHEADERTYPE *buff_header;
	avformat_network_init();
    setup_demuxer("rtp://0.0.0.0:1028");

	audiorenderComponentName = "audio_render";
	decodeComponentName = "video_decode";
    renderComponentName = "video_render";
    schedulerComponentName = "video_scheduler";
    clockComponentName = "clock";

    bcm_host_init();

    handle = ilclient_init();
    vcos_log_set_level(VCOS_LOG_CATEGORY, VCOS_LOG_TRACE);
    if (handle == NULL) 
	{
		fprintf(stderr, "IL client init failed\n");
		exit(1);
    }

    if (OMX_Init() != OMX_ErrorNone) 
	{
        ilclient_destroy(handle);
        fprintf(stderr, "OMX init failed\n");
		exit(1);
    }

    ilclient_set_error_callback(handle,error_callback,NULL);
    ilclient_set_eos_callback(handle,eos_callback,NULL);
    ilclient_set_port_settings_callback(handle,port_settings_callback,NULL);
    ilclient_set_empty_buffer_done_callback(handle,empty_buffer_done_callback,NULL);

	setup_audio_renderComponent(handle, audiorenderComponentName, &audiorenderComponent);
    setup_decodeComponent(handle, decodeComponentName, &decodeComponent);
    setup_renderComponent(handle, renderComponentName, &renderComponent);
    setup_schedulerComponent(handle, schedulerComponentName, &schedulerComponent);
    setup_clockComponent(handle, clockComponentName, &clockComponent);
    // both components now in Idle state, no buffers, ports disabled


	fprintf(stderr, "Num channels for resmapling %d\n",
		av_get_channel_layout_nb_channels(AV_CH_LAYOUT_STEREO));



    // input port
    err = ilclient_enable_port_buffers(decodeComponent, 130,NULL, NULL, NULL);
    if (err < 0) 
	{
		fprintf(stderr, "Couldn't enable buffers\n");
		exit(1);
    }
    ilclient_enable_port(decodeComponent, 130);

    err = ilclient_change_component_state(decodeComponent, OMX_StateExecuting);

    if (err < 0) 
	{
		fprintf(stderr, "Couldn't change state to Executing\n");
		exit(1);
    }
    printState(ilclient_get_handle(decodeComponent));
 
    SendDecoderConfig(decodeComponent);


    /* read frames from the file */
	while (av_read_frame(pFormatCtx, &pkt) >= 0)
	{
		//printf("Read pkt %d\n", pkt.size);

		AVPacket orig_pkt = pkt;
		if (pkt.stream_index == video_stream_idx)
		{
			//printf("  read video pkt %d\n", pkt.size);
			buff_header = ilclient_get_input_buffer(decodeComponent, 130, 1 /* block */);
			if (buff_header != NULL)
			{
				copy_into_buffer_and_empty(&pkt, decodeComponent, buff_header);
			}
			else
			{
				fprintf(stderr, "Couldn't get a buffer\n");
			}

			err = ilclient_wait_for_event(decodeComponent,
				OMX_EventPortSettingsChanged,
				131, 0, 0, 1,
				ILCLIENT_EVENT_ERROR | ILCLIENT_PARAMETER_CHANGED,
				0);
			if (err < 0)
			{
				//printf("No port settings change\n");
				//exit(1);
			}
			else
			{
				printf("Port settings changed\n");
				// exit(0);
				break;
			}


			if (ilclient_remove_event(decodeComponent, OMX_EventPortSettingsChanged, 131, 0, 0, 1) == 0)
			{
				printf("Removed port settings event\n");
				//exit(0);
				break;
			}
			else
			{
				printf("No portr settting seen yet\n");
			}
		}
		av_free_packet(&orig_pkt);
	}
	while(1)
	{

		TUNNEL_T decodeTunnel;
		set_tunnel(&decodeTunnel, decodeComponent, 131, schedulerComponent, 10);
		if ((err = ilclient_setup_tunnel(&decodeTunnel, 0, 0)) < 0) 
		{
			fprintf(stderr, "Error setting up decode tunnel %X\n", err);
			exit(1);
		} else 
		{
			printf("Decode tunnel set up ok\n");
		}

		TUNNEL_T schedulerTunnel;
		set_tunnel(&schedulerTunnel, schedulerComponent, 11, renderComponent, 90);
		if ((err = ilclient_setup_tunnel(&schedulerTunnel, 0, 0)) < 0) 
		{
			fprintf(stderr, "Error setting up scheduler tunnel %X\n", err);
			exit(1);
		} else 
		{
			printf("Scheduler tunnel set up ok\n");
		}
		//assertion failure:ilclient.c:1082:ilclient_setup_tunnel():error == OMX_ErrorNone
		//Aborted


		TUNNEL_T clockTunnel;
		set_tunnel(&clockTunnel, clockComponent, 80, schedulerComponent, 12);
		if ((err = ilclient_setup_tunnel(&clockTunnel, 0, 0)) < 0) 
		{
			fprintf(stderr, "Error setting up clock tunnel %X\n", err);
			exit(1);
		} else 
		{
			printf("Clock tunnel set up ok\n");
		}
		startClock(clockComponent);
		printClockState(clockComponent);

		// Okay to go back to processing data
		// enable the decode output ports
   
		OMX_SendCommand(ilclient_get_handle(decodeComponent), OMX_CommandPortEnable, 131, NULL);
   
		ilclient_enable_port(decodeComponent, 131);

		// enable the clock output ports
		OMX_SendCommand(ilclient_get_handle(clockComponent), OMX_CommandPortEnable, 80, NULL);
   
		ilclient_enable_port(clockComponent, 80);

		// enable the scheduler ports
		OMX_SendCommand(ilclient_get_handle(schedulerComponent), OMX_CommandPortEnable, 10, NULL);
   
		ilclient_enable_port(schedulerComponent, 10);

		OMX_SendCommand(ilclient_get_handle(schedulerComponent), OMX_CommandPortEnable, 11, NULL);

		ilclient_enable_port(schedulerComponent, 11);


		OMX_SendCommand(ilclient_get_handle(schedulerComponent), OMX_CommandPortEnable, 12, NULL);
   
		ilclient_enable_port(schedulerComponent, 12);

		// enable the render input ports
   
		OMX_SendCommand(ilclient_get_handle(renderComponent), OMX_CommandPortEnable,90, NULL);
   
		ilclient_enable_port(renderComponent, 90);



		// set both components to executing state
		err = ilclient_change_component_state(decodeComponent, OMX_StateExecuting);
		if (err < 0) 
		{
			fprintf(stderr, "Couldn't change state to Idle\n");
			exit(1);
		}
		err = ilclient_change_component_state(renderComponent, OMX_StateExecuting);
		if (err < 0) 
		{
			fprintf(stderr, "Couldn't change state to Idle\n");
			exit(1);
		}

		err = ilclient_change_component_state(schedulerComponent, OMX_StateExecuting);
		if (err < 0) 
		{
			fprintf(stderr, "Couldn't change state to Idle\n");
			exit(1);
		}

		err = ilclient_change_component_state(clockComponent, OMX_StateExecuting);
		if (err < 0) 
		{
			fprintf(stderr, "Couldn't change state to Idle\n");
			exit(1);
		}

		AVFrame *frame = av_frame_alloc(); // av_frame_alloc


		Nodetype* oldnode = malloc(sizeof(Nodetype));
		Nodetype* oldnodecopy = oldnode;
		atomic_store(&numofnode, 0);


		pthread_t thread;
		if (pthread_create(&thread, NULL, receivepkt, oldnodecopy) != 0)
			exit(1);


		while (1) 
		{
			if (numofnode < 1)
			{
				usleep(10);
				continue;
			}
			else if (numofnode != 1)
				printf("numofnode: %d\n", numofnode);

			//printf("%d\n", numofnode);

			AVPacket renderpkt = *(oldnode->pbuff);


			if (renderpkt.stream_index == video_stream_idx)
			{
				buff_header = ilclient_get_input_buffer(decodeComponent, 130, 1 /* block */);
				if (buff_header != NULL)
					copy_into_buffer_and_empty(&renderpkt, decodeComponent, buff_header);

				if (ilclient_wait_for_event(decodeComponent, OMX_EventPortSettingsChanged, 131, 0, 0, 1, ILCLIENT_EVENT_ERROR | ILCLIENT_PARAMETER_CHANGED, 0) >= 0)
				{
					printf("port change\n");
					break;
				}
			}
			else if (renderpkt.stream_index == audio_stream_idx)
			{
				
				int got_frame;

				if (((err = avcodec_decode_audio4(codec_context, frame, &got_frame, &renderpkt)) < 0) ||
					!got_frame)
					continue;//"Error decoding 

				read_audio_into_buffer_and_empty(frame, audiorenderComponent);


			}
			
			av_free_packet(&renderpkt);
			Nodetype* pnext = oldnode->next;
			free(oldnode);

			oldnode = pnext;
			atomic_fetch_sub(&numofnode, 1);


		}
		atomic_fetch_sub(&numofnode, 10000);


		if (pthread_join(thread, NULL) != 0)
			exit(1);

		while (1)
		{
			if (oldnode->next == NULL)
			{
				free(oldnode);
				break;
			}
			AVPacket renderpkt = *(oldnode->pbuff);

			av_free_packet(&renderpkt);
			Nodetype* pnext = oldnode->next;
			free(oldnode);

			oldnode = pnext;
		}



		//free(oldnode);
		


	}

	
    exit(0);
}
