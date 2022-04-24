#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <semaphore.h>
#include <time.h>
#include <string.h>
#include <ctype.h>

#include "message.h"


int main(int argc, char *argv[])
{
	int numbThread;
	int nb = 0;
	pthread_t i;

	int queue = 0; // mailbox queue position for non-blocking mode
	pthread_t queueThread[numbThread];

	// argument parsing
	if(argc > 1)
	{
		numbThread = atoi(argv[1]); // number of threads
		if(argc > 2 && strcmp(argv[2], "nb") == 0)
		{
			nb = 1; // nb mode
			printf("Running in non-blocking mode\n");
		}
		else
			printf("Runnin in standard blocking mode\n");
	}
	else
		usage();

	initMailbox(nb);

	pthread_t threadArr[numbThread];  // create array to hold thread pointers

	// Populate threadArr
	for(i=1; i<=numbThread; i++)
	{
		if(pthread_create(&threadArr[i], NULL, adder, (void *)i) != 0)
		{
			perror("Thread creation error");
			exit(1);
		}
	}

	// read from stdin
	struct msg *newMsg = (struct msg *)malloc(sizeof(struct msg));
	char inLine[10];
	pthread_t sendID;
	int msgVal;

	while(1)
	{
		printf("> ");
		char* status = fgets(inLine, 10, stdin);
		if(status == NULL || inLine == NULL || inLine[0] == '\0') //EOF, terminate threads
		{
			printf("End of file detected\n");
			fflush(stdout);
			newMsg->iFrom = 0;
			newMsg->value = -1;
			newMsg->cnt = 0;
			newMsg->tot = 0;
			for(i=1; i<=numbThread; i++)
				SendMsg(i, newMsg);
			break;
		}
		else if(inLine[0] == '\n')
		{
			printf("Blank line, skipping line\n");
			fflush(stdout);
			continue;
		}
		else if(!isdigit(inLine[0]) && !isdigit(inLine[1]))
		{
			printf("Invalid input, skipping line\n");
			fflush(stdout);
			continue;
		}
		else if((atoi(&inLine[1]) > numbThread) || (atoi(&inLine[1]) <= 0))
		{
			printf("invalid thread ID, skipping line\n");
			fflush(stdout);
			continue;
		}
		else // valid input
		{
			printf("Valid input, parsing\n");
			sendID = atoi(&inLine[1]);
			msgVal = atoi(&inLine[0]);

			//printf("Thread ID to send to is %ld\n", sendID);
			//printf("The message value is %d\n", msgVal);

			newMsg->iFrom = 0;
			newMsg->value = msgVal;
			newMsg->cnt = 0;
			newMsg->tot = 0;

			if(nb) // non-blocking mode
			{
				int blocked = NBSendMsg(sendID, newMsg);
				if(blocked)
				{
					// store message and its thread
					mailboxQueue[queue] = newMsg;
					queueThread[queue] = sendID;
					queue++;
				}
			}
			else // if message doesn't get blocked
				SendMsg(sendID, newMsg);
		}
	}

	// send out queued messages (won't run in non nb mode bc queue is init to 0)
	while(queue)
	{
		int isBlocked;
		pthread_t threadID;
		newMsg = mailboxQueue[queue];
		threadID = queueThread[queue];

		isBlocked = NBSendMsg(threadID, newMsg);
		while(isBlocked) // try to send until successful
			isBlocked = NBSendMsg(threadID, newMsg);

		queue--; // repeate until queue is empty
	}




	// wait for threads to complete
	for(i = 1; i<=numbThread; i++)
	{
		struct msg *rMsgMain = (struct msg *)malloc(sizeof(struct msg));

		// clear out previous values
		rMsgMain->iFrom = -2;
		rMsgMain->value = -2;
		rMsgMain->cnt = -2;
		rMsgMain->tot = -2;


		RecvMsg(0, rMsgMain);
		printf("The result from thread %d is %d from %d operations during %d seconds.\n", rMsgMain->iFrom, rMsgMain->value, rMsgMain->cnt, rMsgMain->tot);
	}

	// Clean up
	for(i=1; i<=numbThread; i++)
	{
		pthread_join(threadArr[i], NULL);
		sem_destroy(sendSemArr[i-1]);
		sem_destroy(recvSemArr[i-1]);
	}

	sem_destroy(sendSemArr[numbThread]);
	sem_destroy(recvSemArr[numbThread]);

	free(sendSemArr);
	free(recvSemArr);
	free(mailbox);

	if(nb)
		free(mailboxQueue);

	return 0;
}

int NBSendMsg (int iTo, struct msg *pMsg)
{
	// return 0  - message placed in mailbox
	// return -1 - if mailbox contains message (would normally block) 

	int blocked;

	blocked = sem_trywait(sendSemArr[iTo]);
	if(!blocked)
	{
		mailbox[iTo] = pMsg;
		sem_post(recvSemArr[iTo]);
		return 0;
	}
	else
		return -1;
}

void SendMsg(int iTo, struct msg *pMsg)
{
	// takes an int (index of the thread being sent to) and a message
	sem_wait(sendSemArr[iTo]);
	mailbox[iTo] = pMsg;
	sem_post(recvSemArr[iTo]);

	//printf("Message sent to thread %d\n", iTo);
	//fflush(stdout);
}

void RecvMsg(int iRecv, struct msg *pMsg)
{
	// takes an int (index of the thread receiving the message) and a message
	sem_wait(recvSemArr[iRecv]);
	*pMsg = *mailbox[iRecv];
	sem_post(sendSemArr[iRecv]);

	//printf("Message received by thread %d\n", iRecv);
	//fflush(stdout);
}

void initMailbox(int nb)
{
	// Array of mailboxes of size MAXTHREAD
	// semaphores created to control access to each mailbox <- store in array?
	// Each mailbox needs one producer sempahore and one consumer semaphore

	mailbox = (struct msg **)malloc(sizeof(struct msg *)*(MAXTHREAD+1)); // array of message pointers, each pointer is one "mailbox" for a certain thread

	if(nb)
		mailboxQueue = (struct msg **)malloc(sizeof(struct msg *)*(MAXTHREAD+1)); // queue for messages that can't be immediately placed in box (nb mode)

	sendSemArr = (sem_t **)malloc(sizeof(sem_t *)*(MAXTHREAD+1)); // array of semaphore pointers - controlling "producer" behavior for mailboxes
	recvSemArr = (sem_t **)malloc(sizeof(sem_t *)*(MAXTHREAD+1)); // array of semaphore pointers - controlling "consumer" behavior for mailboxes

	// create semaphores for each mailbox
	for(int i=0; i<=MAXTHREAD; i++)
	{
		sendSemArr[i] = (sem_t *) malloc(sizeof(sem_t));
		sem_init(sendSemArr[i], 0, 1); // producer init to 1 count

		recvSemArr[i] = (sem_t *) malloc(sizeof(sem_t));
		sem_init(recvSemArr[i], 0, 0); //consumer init to 0 count
	}
}

void *adder(void *arg)
{
	pthread_t threadID = (pthread_t)arg; // cast input as pthread_t type

	// function sums the value of the messages received

	int sum = 0;
	int messageCnt = 0;
	time_t start = time(NULL);

	struct msg *rMsg = (struct msg *)malloc(sizeof(struct msg));
	struct msg *sMsg = (struct msg *)malloc(sizeof(struct msg));

	while(1)
	{
		RecvMsg(threadID, rMsg);
		if(rMsg->value == -1)
		{
			time_t end = time(NULL);
			int time = (int)(end-start);
			// termination procedure
			sMsg->iFrom = threadID;
			sMsg->value = sum;
			sMsg->cnt = messageCnt;
			sMsg->tot = time;
			SendMsg(0, sMsg);
			return 0;
		}
		else
		{
			sum += rMsg->value;
			messageCnt++;
			sleep(1);
		}
	}
}

void usage(void)
{
	printf("Please enter up to two arguments\n1: Number of threads to be created\n2: (Optional) If this arg is \"nb\" the program will execute in non-blocking mode \n");
	exit(1);
}
