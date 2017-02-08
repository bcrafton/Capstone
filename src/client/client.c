
#include "client.h"

// main socket
static int current_socket_fd;
// ring buffer to store sound packets
static ring_buf_t* rbuf;
// the SDL spec that defines the data we are playing 
static SDL_AudioSpec spec;
// the thread that will read from the tcp socket
static pthread_t tcp_thread;
// the mutex to keep the ring buffer thread safe
static pthread_mutex_t rbuf_mutex;
// buffer for reading from tcp socket
static uint8_t* swap_buf;

int main(int argc, char *argv[]) {
    wait_for_connection();
    
    if (SDL_Init(SDL_INIT_AUDIO) < 0)
    {
        return 1;
    }

    // allocate the ring buffer
    rbuf = new_ring_buf(DATA_BUFFER_SIZE, FRAME_SIZE);

    // allocate the tcp swap buffer
    swap_buf = (uint8_t*) malloc(sizeof(uint8_t) * FRAME_SIZE);

    SDL_memset(&spec, 0, sizeof(spec));
    spec.freq = 48000;
    spec.channels = 2;
    spec.samples = 4096;
    spec.callback = callback;
    spec.userdata = NULL;

    if ( SDL_OpenAudio(&spec, NULL) < 0 )
    {
        fprintf(stderr, "Couldn't open audio: %s\n", SDL_GetError());
        exit(-1);
	}

    int ret = pthread_create(&tcp_thread, NULL, run_tcp_thread, NULL);
    if (ret)
    {
        fprintf(stderr,"Error: pthread_create() return code: %d\n", ret);
        // add an enumeration for this error case
        exit(1);
    }

    SDL_PauseAudio(0);

    return 0;
}

int read_socket(int socketfd, void* buffer, int size)
{
    int total_read = 0;
    int total_left = size;
    void* buffer_pointer = buffer;
    while(total_left > 0)
    {
        int current = read(socketfd, buffer_pointer, total_left);    
        
        if(current < 0)
        {
            perror("error return code on socket read");
        }
        else
        {
            total_read += current;
            total_left -= current;
            buffer += current;
        }
    }
    return total_read;
}

void wait_for_connection()
{
    int sockfd;
    int newsockfd;
    int clilen;
    sockaddr_in serv_addr;
    sockaddr_in cli_addr;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
    {
        perror("ERROR opening socket");
    }    
    bzero((char *) &serv_addr, sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons( PORTNO );
    if ( bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0 )
    {
        perror("ERROR on binding");
    }    
    listen(sockfd,5);
    clilen = sizeof(cli_addr);
    while(1)
    {
        // pretty sure this blocks which is what we want
        if ( ( newsockfd = accept( sockfd, (struct sockaddr *) &cli_addr, (socklen_t*) &clilen) ) < 0 )
        {
            perror("ERROR on accept");
        }
        else
        {
            // get out of the inf while loop
            current_socket_fd = newsockfd;
            break;
        }
    }
}

void callback(void *userdata, Uint8 *stream, int len) {
	assert(len == FRAME_SIZE);

    pthread_mutex_lock(&rbuf_mutex);
    // copy from one buffer into the other
	SDL_memcpy(stream, read_buffer(rbuf, FRAME_SIZE), len);
    pthread_mutex_unlock(&rbuf_mutex);
}

static void* run_tcp_thread(void *data)
{
    while (!isFull(rbuf))
    {
        // read from the tcp socket into the swap buffer
        read_socket(current_socket_fd, swap_buf, sizeof(uint8_t) * FRAME_SIZE);
        // attempt to acquite lock & copy from swap buffer into ring buffer
        pthread_mutex_lock(&rbuf_mutex);
        write_buffer(rbuf, swap_buf, sizeof(uint8_t) * FRAME_SIZE);
        pthread_mutex_unlock(&rbuf_mutex);
    }
}