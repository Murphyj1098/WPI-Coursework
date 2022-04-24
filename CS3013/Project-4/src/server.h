// Function prototypes
void init(void);
void* fileProcessor(void *inData); // thread function
void result(void);


// Globals
int  badFile;
int  directory;
int  regularFile;
int  specialFile;
long regularBytes;
int  textFile;
long textBytes;

pthread_mutex_t mutex;


// Struct for thread function
struct fileData
{
	char *inFile;
	struct stat *buffer;
};

// Constants
#define MAXLINE 256
#define MAXTHREAD 15