import asyncio
import logging
import os
import platform
import yaml

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

from typing import Optional, List
from pydantic import BaseModel

class NatsMsg(BaseModel):
  subject: str
  message: List

async def natsClientError(err) :
  logging.error("NatsClient : {err}".format(err=err))

async def natsClientClosedConn() :
  logging.warn("NatsClient : connection to NATS server is now closed.")

async def natsClientReconnected() :
  logging.info("NatsClient : reconnected to NATS server.")

class NatsClient :

  def __init__(self, aContainerName, aHeartBeatPeriod) :
    self.nc = NATS()
    self.containerName = aContainerName
    self.heartBeatPeriod = aHeartBeatPeriod
    self.shutdown   = False
    self.subscriptions = []

  async def heartBeat(self) :
    logging.info("NatsClient: starting heartbeat")
    while not self.shutdown :
      logging.debug("NatsClient: heartbeat")
      loadAvg = os.getloadavg()
      msg = "hello from {}-{} (1:{} 5:{} 15:{})".format(
        platform.node(), self.containerName,
        loadAvg[0], loadAvg[1], loadAvg[2]
      )
      await self.nc.publish("heartbeat", bytes(msg, 'utf-8'))
      await asyncio.sleep(self.heartBeatPeriod)

  def unpackMessage(self, callback) :
    async def callbackWithUnpackedMessage(msg) :
      unpackedSubject = msg.subject.split('.')
      unpackedSubject.insert(0, msg.subject)
      unpackedData    = msg.data.decode()
      if not type(unpackedData) == 'dict' :
        originalUnpackedData = unpackedData
        unpackedData = { 
          str(type(originalUnpackedData).__name__) : originalUnpackedData
        }
      print(unpackedSubject[0])
      print(yaml.dump(unpackedSubject))
      print(yaml.dump(unpackedData))
      await callback(unpackedSubject, unpackedData)
    return callbackWithUnpackedMessage

  # A Python decorator (with an argument)
  # which records the subscription and callback
  # in a list for later processing
  #
  def subscribe(self, subscription) :
    def decorator_subscribe(callback) :
      self.subscriptions.append({
        'subscription' : subscription,
        'callback'     : callback
       })
    return decorator_subscribe
  
  async def listenForMessagesOnDecoratedSubscriptions(self) :
    logging.info("NatsClient: Listening to decorated subscriptions")
    for aSubscription in self.subscriptions :
      await self.nc.subscribe(
        aSubscription['subscription'],
        cb=self.unpackMessage(aSubscription['callback'])
      )

  async def listenForMessages(self, subject, callBack) :
    await self.nc.subscribe(subject, cb=callBack)

  async def sendMessage(self, msg: NatsMsg) :
    await self.nc.publish(msg.subject, bytes(msg.message, 'utf-8'))
        
  async def connectToServers(self):
    await self.nc.connect(
      servers=["nats://127.0.0.1:4222"],
      error_cb=natsClientError,
      closed_cb=natsClientClosedConn,
      reconnected_cb=natsClientReconnected
    )

  async def closeConnection(self) :    
    # Terminate connection to NATS.
    self.shutdown = True
    await asyncio.sleep(1)
    await self.nc.close()