APP=dopple
CC=g++

LIBS=-lstdc++
INCLUDES=
OPTIONS=
CFLAGS=-c -g -Wno-write-strings -O2 -Wall -x c++
SOURCES=timer.cpp $(APP).cpp

OBJECTS=$(SOURCES:.cpp=.o)

all : $(APP)

$(APP) : $(OBJECTS)
	$(CC) $(OBJECTS) $(LIBS) -o $(APP)

.cpp.o:
	$(CC) $(CFLAGS) $< -o $@

clean :
	rm -f *.o
	rm -f $(APP)

install :
	cp $(APP) /usr/local/bin/.

