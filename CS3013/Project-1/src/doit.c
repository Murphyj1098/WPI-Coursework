/* doit.c */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <unistd.h>

#define MAX_CHARS 128
#define MAX_ARGS 32


void printStats(struct timeval startTime) // Function to print out child usage stats
{
    struct rusage usageStat;
    struct timeval endTime;
    gettimeofday(&endTime, NULL); // get time process stops
    getrusage(RUSAGE_SELF, &usageStat);

    long int start = startTime.tv_sec * 1000 + startTime.tv_usec / 1000; // convert start time to milliseconds
    long int end = endTime.tv_sec * 1000 + endTime.tv_usec / 1000; // convert end time to milliseconds

    printf("\nUsage Statistics\n");
    printf("User CPU Time: %ld milliseconds\n", usageStat.ru_utime.tv_sec * 1000
    	+ usageStat.ru_utime.tv_usec / 1000);
    printf("System CPU Time: %ld milliseconds\n", usageStat.ru_stime.tv_sec * 1000
    	+ usageStat.ru_stime.tv_usec / 1000);
    printf("Wall Clock Time Passed: %ld milliseconds\n", end - start);
    printf("Number of involuntary context switches: %ld\n", usageStat.ru_nivcsw);
    printf("Number of voluntary context switches: %ld\n", usageStat.ru_nvcsw);
    printf("Number of page faults requiring I/O: %ld\n", usageStat.ru_majflt);
    printf("Number of page faults not requiring I/O: %ld\n", usageStat.ru_minflt);
}

void execute(char* newArgs[])
{
    int pid;

    struct timeval startTime;
    gettimeofday(&startTime, NULL); //get time process starts

    if((pid = fork()) < 0) // Fork error
    {
        fprintf(stderr, "Fork error\n");
        exit(1);
    }
    else if(pid == 0) // Child process
    {
        if(execvp(newArgs[0], newArgs) < 0)
        {
            fprintf(stderr, "Execve error\n");
            exit(1);
        }
    }
    else // Parent process
    {
        wait(0); // wait for child to finish
        printStats(startTime);
    }
}

int main(int argc, char *argv[])
{
    /* argc - number of arguments */
    /* argv - an array  of strings */

    char**newArgs = (char **)malloc(MAX_ARGS * sizeof(char *));
    char shellPrompt[] = "==> ";

    if(argc == 1) // shell mode
    {
        printf("Shell Mode\n");

        while(1)
        {
            printf("%s", shellPrompt);

            char inLine[MAX_CHARS];
            fgets(inLine, MAX_CHARS, stdin); // read in user arguments

            if(inLine[0] == '\0' || inLine[0] == '\n') // check if line is empty
                continue;

            /* Parse input and seperate commands and arguments */
            char* token = strtok(inLine, " \n");
            int i = 0;

            while(token != NULL)
            {
                newArgs[i] = token;
                token = strtok(NULL, " \n");
                i++;
            }
            newArgs[i] = NULL;

            // Handle exit
            if(strcmp(newArgs[0], "exit") == 0)
            {
                break;
            }

            execute(newArgs);
        }
    }
    else if(argc > 1) // single command mode
    {
        int i;
        for(i = 1; i < argc; i++) // removes ./doit from arg list
        {
            newArgs[i-1] = argv[i];
        }
        newArgs[argc - 1] = NULL; // NULL terminated

        execute(newArgs);
    }
}
