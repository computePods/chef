import asyncio
import logging
import signal
import traceback

from externalWebServer import ExternalWebServer
from podWebServer import PodWebServer
from natsClient import NatsClient
from natsServer import NatsServer

#logging.basicConfig(filename='majorDomo.log', encoding='utf-8', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.info("ComputePods MajorDomo starting")
  
class SignalException(Exception):
  def __init__(self, message):
    super(SignalException, self).__init__(message)

def signalHandler(signum, frame) :
  msg = "SignalHandler: Caught signal {}".format(signum)
  logging.info(msg)
  raise SignalException(msg)

signal.signal(signal.SIGTERM, signalHandler)
signal.signal(signal.SIGHUP, signalHandler)

async def main() :
  natsServer = NatsServer()
  natsServerTask = asyncio.create_task(natsServer.runNatsServer())
  await natsServer.waitUntilRunning("cpmd")
  
  natsClient = NatsClient("majorDomo", 10)
  await natsClient.connectToServers()
  
  externalWS = ExternalWebServer(natsClient)
  podWS      = PodWebServer(natsClient)

  try: 
    await asyncio.gather(
      natsClient.heartBeat(),
      externalWS.runApp(),
      podWS.runApp()
    )
  finally: 
    await natsClient.closeConnection()
    await natsServer.stopServer()
    await natsServerTask

try: 
  asyncio.run(main(), debug=True)
except SignalException as err :
  logging.info("Shutting down: {}".format(str(err)))
except Exception as err :
  msg = "\n ".join(traceback.format_exc().split("\n"))
  logging.info("Shutting down after exception: \n {}".format(msg))
