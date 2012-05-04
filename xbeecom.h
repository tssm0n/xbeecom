#include "Arduino.h"

#define XBEE_INCOMING_BUFFER 150
#define XBEE_MAX_DATA_SIZE 60
#define XBEE_PACKET_BUFFER_SIZE 12

#define XBEE_OUTGOING_BUFFER XBEE_MAX_DATA_SIZE + 8

struct XbeePacket {
   byte source;
   byte destination;
  
   byte data[XBEE_MAX_DATA_SIZE];
   
   byte dataLength;
   int packetNumber;
};

class XbeeCom {
  private:
    byte xbeeIncommingBuffer[XBEE_INCOMING_BUFFER];
    struct XbeePacket xbeePacketBuffer[XBEE_PACKET_BUFFER_SIZE];
    
    int iBufferStart;
    int iBufferCurrent;
    
    int pBufferStart;
    int pBufferCurrent;
  
    void moveCompletePacket();
    boolean isPacketComplete();
    boolean isBufferValid();
  public:
    XbeeCom();
    void xbeeReceiveByte(byte input);
    boolean xbeeIsPacketAvailable(void);
    struct XbeePacket xbeeNextPacket(void);
    short xbeeSend(byte source, byte destination, byte length, byte* data, byte* buffer);
};

