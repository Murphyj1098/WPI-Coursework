#include <stdio.h>
#include "project3.h"

extern int TraceLevel;

struct distance_table {
  int costs[MAX_NODES][MAX_NODES];
};
struct distance_table dt3;
struct NeighborCosts   *neighbor3;

#define NODE 3

/////////////////////////////////////////////////////////////////////
//  printdt
//  This routine is being supplied to you.  It is the same code in
//  each node and is tailored based on the input arguments.
//  Required arguments:
//  MyNodeNumber:  This routine assumes that you know your node
//                 number and supply it when making this call.
//  struct NeighborCosts *neighbor:  A pointer to the structure 
//                 that's supplied via a call to getNeighborCosts().
//                 It tells this print routine the configuration
//                 of nodes surrounding the node we're working on.
//  struct distance_table *dtptr: This is the running record of the
//                 current costs as seen by this node.  It is 
//                 constantly updated as the node gets new
//                 messages from other nodes.
/////////////////////////////////////////////////////////////////////
void printdt3( int MyNodeNumber, struct NeighborCosts *neighbor, 
		struct distance_table *dtptr ) {
    int       i, j;
    int       TotalNodes = neighbor->NodesInNetwork;     // Total nodes in network
    int       NumberOfNeighbors = 0;                     // How many neighbors
    int       Neighbors[MAX_NODES];                      // Who are the neighbors

    // Determine our neighbors 
    for ( i = 0; i < TotalNodes; i++ )  {
        if (( neighbor->NodeCosts[i] != INFINITY ) && i != MyNodeNumber )  {
            Neighbors[NumberOfNeighbors] = i;
            NumberOfNeighbors++;
        }
    }
    // Print the header
    printf("                via     \n");
    printf("   D%d |", MyNodeNumber );
    for ( i = 0; i < NumberOfNeighbors; i++ )
        printf("     %d", Neighbors[i]);
    printf("\n");
    printf("  ----|-------------------------------\n");

    // For each node, print the cost by travelling thru each of our neighbors
    for ( i = 0; i < TotalNodes; i++ )   {
        if ( i != MyNodeNumber )  {
            printf("dest %d|", i );
            for ( j = 0; j < NumberOfNeighbors; j++ )  {
                    printf( "  %4d", dtptr->costs[i][Neighbors[j]] );
            }
            printf("\n");
        }
    }
    printf("\n");
}    // End of printdt3


/* students to write the following two routines, and maybe some others */

void rtinit3() {
    neighbor3 = getNeighborCosts(NODE);
    printf("At time t=%f, rtinit3() called.\n", clocktime);
    
    // setup distance table
    for(int i=0; i < MAX_NODES; i++)
    {
        for(int j=0; j < MAX_NODES; j++)
        {
            if(i == j)
                dt3.costs[i][j] = neighbor3->NodeCosts[i];
            else
                dt3.costs[i][j] = INFINITY;
        }
    }

    // print the original table
    printf("At time t=%f, node 3 initial distance vector: %d %d %d %d\n",
        clocktime, dt3.costs[0][0], dt3.costs[1][1], dt3.costs[2][2], dt3.costs[3][3]);

    // initialize packet
    struct RoutePacket pkt;
    pkt.sourceid = NODE;

    // set up minimum neighbor costs
    for(int i=0; i < MAX_NODES; i++)
    {
        // by default, min cost is infinity
        pkt.mincost[i] = INFINITY;

        // if the current min cost is less than infinity, update to smaller cost
        if(pkt.mincost[i] > neighbor3->NodeCosts[i])
            pkt.mincost[i] = neighbor3->NodeCosts[i];
    }

    // send packets
    for(int i=0; i < MAX_NODES; i++)
    {
        if(neighbor3->NodeCosts[i] != INFINITY && i != NODE)
        {
            pkt.destid = i;
            toLayer2(pkt);
            printf("At time t=%f, node 3 sends packet to node %d with: %d %d %d %d\n",
                clocktime, i, pkt.mincost[0], pkt.mincost[1], pkt.mincost[2], pkt.mincost[3]);
        }
    }

}


void rtupdate3( struct RoutePacket *rcvdpkt ) {

    printf("At time t=%f, rtupdate3() called, by a pkt received from Sender id: %d.\n",
        clocktime, rcvdpkt->sourceid);

    int source = rcvdpkt->sourceid;
    int updateTable = 0;
    int minVal[MAX_NODES]; // holds min values
    struct RoutePacket new_pkt; // new packet to send out

    // populate mins array
    for(int i=0; i < MAX_NODES; i++)
    {
        minVal[i] = INFINITY; // default to INFINITY
        for(int j=0; j < MAX_NODES; j++)
        {
            if(dt3.costs[i][j] < minVal[i])
                minVal[i] = dt3.costs[i][j];
        }
    }

    // initialize new_pkt
    for(int i=0; i < MAX_NODES; i++)
    {
        new_pkt.mincost[i] = INFINITY;
    }

    // if a shorter path is returned
    if(dt3.costs[source][source] > rcvdpkt->mincost[NODE])
    {
        dt3.costs[source][source] = rcvdpkt->mincost[NODE];
        updateTable = 1;
    }

    // check if the new cost is shorter amd update the new packet to send
    for(int i=0; i < MAX_NODES; i++)
    {
        if(dt3.costs[i][source] > rcvdpkt->mincost[i] + dt3.costs[source][source])
        {
            dt3.costs[i][source] = rcvdpkt->mincost[i] + dt3.costs[source][source];
            updateTable = 1;
        }
    }

    // update the min array based on updated data
    for(int i=0; i < MAX_NODES; i++)
    {
        for(int j=0; j < MAX_NODES; j++)
        {
            if(dt3.costs[i][j] < minVal[i])
            {
                minVal[i] = dt3.costs[i][j];
                updateTable = 1;
            }
        }
    }

    // populate packet data 
    for(int i=0; i < MAX_NODES; i++)
    {
        new_pkt.mincost[i] = minVal[i];
    }
    
    // send out updated table
    if(updateTable)
    {

        // current distance vector
        printf("At time t=%f, node 3 current distance vector: %d %d %d %d\n",
            clocktime, minVal[0], minVal[1], minVal[2], minVal[3]);

        for(int i=0; i < MAX_NODES; i++)
        {
            if(neighbor3->NodeCosts[i] != INFINITY && i != NODE)
            {
                new_pkt.sourceid = NODE;
                new_pkt.destid = i;
                toLayer2(new_pkt);
                printf("At time t=%f, node 3 sends packet to node %d with: %d %d %d %d\n",
                    clocktime, i, new_pkt.mincost[0], new_pkt.mincost[1], new_pkt.mincost[2], new_pkt.mincost[3]);
            }
        }       
    }
}
