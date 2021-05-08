import asyncio
import importlib
import logging
import os
import signal
import traceback

from natsClient import NatsClient

#logging.basicConfig(filename='majorDomo.log', encoding='utf-8', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.info("ComputePods Chef starting")
  
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
  natsClient = NatsClient(os.getenv('CONTAINER_NAME'), 10)
  await natsClient.connectToServers()

  pluginFiles = os.listdir('./plugins')
  pluginFiles.sort()
  for aFile in pluginFiles :
    if aFile.endswith('.py') :
      if aFile != '__init__.py' :
        logging.info("Importing the {} plugin".format(aFile[:-3]))
        aPlugin = importlib.import_module('plugins.{}'.format(aFile[:-3]))
        if hasattr(aPlugin, 'registerPlugin') :
          logging.info("Registering the {} plugin".format(aFile[:-3]))
          await aPlugin.registerPlugin(natsClient)
        else:
          logging.info("Plugin {} has no registerPlugin method!".format(aFile[:-3]))

  await natsClient.listenForMessagesOnDecoratedSubscriptions()
  
  try: 
    await asyncio.gather(
      natsClient.heartBeat(),
    )
  finally:
    await natsClient.closeConnection()

try: 
  asyncio.run(main(), debug=True)
except SignalException as err :
  logging.info("Shutting down: {}".format(str(err)))
except Exception as err :
  msg = "\n ".join(traceback.format_exc().split("\n"))
  logging.info("Shutting down after exception: \n {}".format(msg))
