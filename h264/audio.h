int32_t audioplay_create(ILCLIENT_T *, COMPONENT_T *, COMPONENT_T **, int);
int32_t audioplay_delete(COMPONENT_T *);
int32_t audioplay_play_buffer(COMPONENT_T *, uint8_t *, uint32_t);
int32_t audioplay_set_dest(COMPONENT_T *, const char *);
uint32_t audioplay_get_latency(COMPONENT_T *);
