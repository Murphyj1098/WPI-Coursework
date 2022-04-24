// Structs
struct msg
{
	int iFrom; 	// who sent the message (0 .. number-of-threads)
	int value;	// its value
	int cnt;	// count of operations (not needed by all messages)
	int tot;	// total time (not needed by all messages)
};

// Constants
#define REQUEST 1
#define REPLY 2
#define MAXTHREAD 10

// Function prototypes
int NBSendMsg (int iTo, struct msg *pMsg);
void SendMsg(int iTo, struct msg *pMsg);
void RecvMsg(int iRecv, struct msg *pMsg);
void initMailbox(int nb);
void *adder(void *);
void usage(void);

// Globals
struct msg **mailbox;
struct msg **mailboxQueue;
sem_t **sendSemArr;
sem_t **recvSemArr;