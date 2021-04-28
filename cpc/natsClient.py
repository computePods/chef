import asyncio
import logging
import os
import platform

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

from typing import Optional
from pydantic import BaseModel

class NatsMsg(BaseModel):
  subject: str
  message: str

class NatsClient :

  def __init__(self, aNatsServer) :
    self.nc = NATS()
    self.msgQueue   = asyncio.Queue()
    self.natsServer = aNatsServer
    self.shutdown   = False

  async def heartBeat(self) :
    logging.info("NatsClient: starting heartbeat")
    while not self.shutdown :
      logging.debug("NatsClient: heartbeat")
      loadAvg = os.getloadavg()
      msg = "hello from {} ({} {} {})".format(platform.node(), loadAvg[0], loadAvg[1], loadAvg[2])
      await self.nc.publish("heartbeat", bytes(msg, 'utf-8'))
      await asyncio.sleep(1)

  async def sendMessage(self, msg: NatsMsg) :
    await self.msgQueue.put(msg)

  async def dealWithMessageQueue(self) :
    logging.info("NatsClient: starting to deal with queue")
    i = 0
    while not self.shutdown :
      aMsg = await self.msgQueue.get()
      logging.debug("NatsClient: dealing with queue msg")
      await self.nc.publish(aMsg.subject, 
        bytes("{} : {} ({})".format(aMsg.message, i, self.msgQueue.qsize()), 'utf-8'))
      i += 1
      #await asyncio.sleep(1)
      self.msgQueue.task_done()
      
  async def runNatsClient(self):

    await self.natsServer.waitUntilRunning("testNats")

    await self.nc.connect("127.0.0.1:4222")
    
    await asyncio.gather(
      self.heartBeat(),
      self.dealWithMessageQueue()
    )

    #await self.heartBeat(),
    
    # Terminate connection to NATS.
    await self.nc.close()
