#include<Arduino.h>
#include"xbeecom.h"

#define XBEE_CHECKSUM(total) (0xFF - (total % 0xFF))

XbeeCom::XbeeCom(){
    iBufferStart = 0;
    iBufferCurrent = 0;
    
    pBufferStart = 0;
    pBufferCurrent = 0; 
}

boolean XbeeCom::isBufferValid(){
   int length = iBufferCurrent - iBufferStart;
   if(length == 0){
      return true;
   } 
   if(length == 1 && xbeeIncommingBuffer[iBufferStart] != 125){
      return false;
   }
   if(length == 2 && xbeeIncommingBuffer[iBufferStart+1] != 126){
      return false;
   }
   if(length < 8){
      return true;
   }
   int expected = xbeeIncommingBuffer[iBufferStart+6] + 8;
   if(length < expected){
      return true;
   }
   int ccTotal = 0;
   int index = 0;
   for(index = iBufferStart+7; index < expected-1; index++){
     ccTotal += xbeeIncommingBuffer[index];
   }
   return xbeeIncommingBuffer[expected-1] == XBEE_CHECKSUM(ccTotal);
   
}

boolean XbeeCom::isPacketComplete(){
   int length = iBufferCurrent - iBufferStart;
   if(length < 8){
      return false;
   }
   int expected = xbeeIncommingBuffer[iBufferStart+6] + 8;
   if(length < expected){
      return false;
   }
   return true;
}

void XbeeCom::xbeeReceiveByte(byte input){
  //Serial.println((int)input);
   xbeeIncommingBuffer[iBufferCurrent++] = input;
   if(!isBufferValid()){
     Serial.println("Buffer Invalid");
     iBufferStart = 0;
     iBufferCurrent = 0;
   }
   if(isPacketComplete()){
     moveCompletePacket();
     iBufferStart = 0;
     iBufferCurrent = 0;     
   }
  
   if(iBufferCurrent >= XBEE_INCOMING_BUFFER){
       iBufferCurrent = 0;
   }
}

boolean XbeeCom::xbeeIsPacketAvailable(void){
   return pBufferStart != pBufferCurrent;
}

struct XbeePacket XbeeCom::xbeeNextPacket(void){
   struct XbeePacket result = xbeePacketBuffer[pBufferStart++];
   if(pBufferStart >= XBEE_PACKET_BUFFER_SIZE){
      pBufferStart = 0;
   }
   return result;
}


short XbeeCom::xbeeSend(byte source, byte destination, byte length, byte* data, byte* buffer){
   buffer[0] = 125;
   buffer[1] = 126;
   buffer[2] = source;
   buffer[3] = destination;
   buffer[4] = 0; // TODO: Packet Number
   buffer[5] = 0;
   buffer[6] = length;
   
   int total = 0;
   int index = 0;
   int count = 0;
   for(index = 7; count < length; index++){
     buffer[index] = data[count];
     total += data[count];
     count++;
   }

   buffer[index] = XBEE_CHECKSUM(total);

   return index+1;
}


void XbeeCom::moveCompletePacket(){
   struct XbeePacket packet = xbeePacketBuffer[pBufferCurrent];
   
   packet.source = xbeeIncommingBuffer[iBufferStart+2];
   packet.destination = xbeeIncommingBuffer[iBufferStart+3];
   
   int ending = xbeeIncommingBuffer[iBufferStart+6] + 6;
   
   int index = 0;
   int count = 0;
   for(index = iBufferStart+7; index < ending+1; index++){
     packet.data[count++] = xbeeIncommingBuffer[index];
   }
   
   packet.dataLength = count;
   byte msb = xbeeIncommingBuffer[iBufferStart+4];
   byte lsb = xbeeIncommingBuffer[iBufferStart+5];
   packet.packetNumber = ((msb<<2) || lsb);
   
   iBufferStart = ending;
   xbeePacketBuffer[pBufferCurrent] = packet;
   pBufferCurrent++;
   if(pBufferCurrent >= XBEE_PACKET_BUFFER_SIZE){
     pBufferCurrent = 0;
   }
}

