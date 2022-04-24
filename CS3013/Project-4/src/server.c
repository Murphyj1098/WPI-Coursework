#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/time.h>
#include <sys/types.h>
#include <string.h>
#include <ctype.h>
#include <sys/resource.h>

#include "server.h"

int main(int argc, char *argv[])
{
	int mode; // serial or thread mode (0 - serial, 1 - thread)
	int threadNum; // number of threads in multithread mode

	struct stat **fileBuffer; // array of stat buffers (serial mode only needs 1, threaded mode needs 1 per thread)
	pthread_t threadArr[MAXTHREAD]; // array to hold thread pointers

	int oldThread = 0; // index of oldest thread (to be replaced)
	int threadCnt = 0; // number of threads that have been created

	char* inLine; // holds stdin input
	char* inStatus; // holds return value of fgets

	struct timeval startTime, endTime;
    gettimeofday(&startTime, NULL); //get time process starts

	init();

	// input parsing
	if(argc > 1 && strcmp(argv[1], "thread") == 0)
	{
		// thread mode
		if(argc > 2 && (atoi(argv[2]) <= MAXTHREAD) && (atoi(argv[2]) >= 1))
		{
			// correct arguments
			printf("Thread mode\n");
			threadNum = atoi(argv[2]);
			mode = 1;

			fileBuffer = (struct stat**)malloc(sizeof(struct stat*) * threadNum);

			for(int i = 0; i < threadNum; i++)
				fileBuffer[i] = (struct stat*)malloc(sizeof(struct stat));
		}
		else
		{
			// missing thread number argument
			printf("Thread mode requires an argument for number of threads (1-15)\n");
			return 0;
		}
	}
	else
	{
		// serial mode
		printf("Serial mode\n");
		mode = 0;
		fileBuffer = (struct stat**)malloc(sizeof(struct stat*));
		fileBuffer[0] = (struct stat*)malloc(sizeof(struct stat));
	}

	// loop through each input file and send to fileProcessor
	while(1)
	{
		inLine = (char *)malloc(sizeof(char) * MAXLINE);
		inStatus = fgets(inLine, MAXLINE, stdin);

		if(inStatus == NULL || inLine == NULL || inLine[0] == '\0')
			break; // EOF

		char *token = strtok(inLine, "\n"); // remove any spaces or newlines (files error out stat() otherwise)

		struct fileData *processFile;
		processFile = (struct fileData*)malloc(sizeof(struct fileData));
		processFile->inFile = inLine;
		
		if(!mode)
		{
			// serial
			processFile->buffer = fileBuffer[0];
			fileProcessor(processFile);
		}
		else if(mode)
		{
			// create and start threads
			if(threadCnt < threadNum) // empty threads to be used
			{
				processFile->buffer = fileBuffer[threadCnt];
				pthread_create(&threadArr[threadCnt], NULL, fileProcessor, (void *)processFile);
				threadCnt++;
			}
			else // wait for existing thread and repurpose it
			{
				pthread_join(threadArr[oldThread], NULL);
				processFile->buffer = fileBuffer[oldThread];
				pthread_create(&threadArr[oldThread], NULL, fileProcessor, (void *)processFile);

				if(oldThread == threadNum - 1)
					oldThread = 0; // loop
				else
					oldThread++;
			}
		}
	}

	if(mode)
	{
		for(int i = 0; i < threadCnt; i++)
			pthread_join(threadArr[i], NULL);
	}
	
	result();

	struct rusage usageStat;
	getrusage(RUSAGE_SELF, &usageStat);
	gettimeofday(&endTime, NULL);

	double wallClock = ((endTime.tv_sec - startTime.tv_sec) * 1000) +  ((double)(endTime.tv_usec - startTime.tv_usec) / 1000);
	double userClock = ((usageStat.ru_utime.tv_sec) * 1000) + ((double)(usageStat.ru_utime.tv_usec) / 1000);
	double systClock = ((usageStat.ru_stime.tv_sec) * 1000) + ((double)(usageStat.ru_stime.tv_usec) / 1000);

	printf("\n");
	printf("Wall Clock time (ms): %f\n", wallClock);
	printf("System time (ms): %f\n", systClock);
	printf("User time (ms): %f\n", userClock);

	return 0;
}

void init(void)
{
	// changing these variables is considered critical region, use mutex
	badFile = 0;
	directory = 0;
	regularFile = 0;
	specialFile = 0;
	regularBytes = 0;
	textFile = 0;
	textBytes = 0;
	
	pthread_mutex_init(&mutex, NULL);
}

void* fileProcessor(void *inData)
{
	// Seperate input data from input struct
	struct fileData *data = (struct fileData *)inData; // cast as appropriate type
	struct stat *buffer = data->buffer;
	char *file = data->inFile;

	if(stat(file, buffer) < 0) // error (bad file)
	{
		pthread_mutex_lock(&mutex);
		badFile++;
		pthread_mutex_unlock(&mutex);
		return 0;
	}
	if(S_ISDIR(buffer->st_mode)) // is directory
	{
		pthread_mutex_lock(&mutex);
		directory++;
		pthread_mutex_unlock(&mutex);
	}
	if(S_ISREG(buffer->st_mode)) // is regular file
	{
		pthread_mutex_lock(&mutex);
		regularFile++;
		regularBytes += buffer->st_size;
		pthread_mutex_unlock(&mutex);
	}
	if(!(S_ISDIR(buffer->st_mode)) && !(S_ISREG(buffer->st_mode))) // special file (not directory or regular)
	{
		pthread_mutex_lock(&mutex);
		specialFile++;
		pthread_mutex_unlock(&mutex);
	}

	long bytes = 0;
	int fd;
	char pos[1];
	
	fd = open(file, O_RDONLY); // open the file as read only

	if(fd < 0) // file can't be opened
	{
		return 0;
	}

	while(read(fd, pos, 1) > 0) // not end of file
	{
		if(isprint(pos[0]) || isspace(pos[0])) // if current character is printable or a space
			bytes++;
		else
		{
			bytes = 0; // entire file is not printable chars or spaces
			break;
		}
	}

	pthread_mutex_lock(&mutex);
	textBytes += bytes;
	textFile++;
	pthread_mutex_unlock(&mutex);

	close(fd);

	return 0;
}

void result(void)
{
	printf("Bad files: %d\n", badFile);
	printf("Directories: %d\n", directory);
	printf("Regular files: %d\n", regularFile);
	printf("Special files: %d\n", specialFile);
	printf("Regular file bytes: %ld\n", regularBytes);
	printf("Text files: %d\n", textFile);
	printf("Text file bytes: %ld\n", textBytes);
}