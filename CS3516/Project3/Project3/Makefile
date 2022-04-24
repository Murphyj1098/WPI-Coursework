CC := gcc
TARGET := project3
NODES := src/node0.c src/node1.c src/node2.c src/node3.c
SRC := src/project3.c $(NODES)
INC := include

FLAGS := -I $(INC) -o $(TARGET) -Wall

all:
		$(CC) $(FLAGS) $(SRC)

clean:
		rm $(TARGET)
