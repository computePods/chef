import asyncio
import logging
import signal

from cpchef.loadConfiguration import parseCliArgs, loadConfig, loadPlugins
from cpchef.utils import setConfig

from cputils.natsClient import NatsClient

async def runTasks(config) :

  natsClient = NatsClient("chef", 10)
  host = "127.0.0.1"
  port = 4222
  if 'natsServer' in config :
    natsServerConfig = config['natsServer']
    if 'host' in natsServerConfig : host = natsServerConfig['host']
    if 'port' in natsServerConfig : port = natsServerConfig['port']
  natsServerUrl = f"nats://{host}:{port}"
  print(f"connecting to nats server: [{natsServerUrl}]")
  await natsClient.connectToServers([ natsServerUrl ])

  await loadPlugins(config, natsClient)

  await natsClient.listenForMessagesOnDecoratedSubscriptions()

  try:
    await asyncio.gather(
      natsClient.heartBeat(),
    )
  finally:
    await natsClient.closeConnection()

def cpchef() :
  cliArgs = parseCliArgs()

  if cliArgs.debug :
    logging.basicConfig(level=logging.DEBUG)
  else :
    logging.basicConfig(level=logging.WARNING)
  logger = logging.getLogger("majorDomo")

  #logging.basicConfig(filename='majorDomo.log', encoding='utf-8', level=logging.DEBUG)
  #logging.basicConfig(level=logging.INFO)

  logging.info("ComputePods Chef starting")

  config = loadConfig(cliArgs)
  setConfig(config)

  loop = asyncio.get_event_loop()

  def signalHandler(signum) :
    """
    Handle an OS system signal by stopping the debouncing tasks

    """
    print("")
    print("Shutting down...")
    logger.info("SignalHandler: Caught signal {}".format(signum))
    loop.stop()

  loop.set_debug(cliArgs.verbose)
  loop.add_signal_handler(signal.SIGTERM, signalHandler, "SIGTERM")
  loop.add_signal_handler(signal.SIGHUP,  signalHandler, "SIGHUP")
  loop.add_signal_handler(signal.SIGINT,  signalHandler, "SIGINT")
  loop.create_task(runTasks(config))
  loop.run_forever()

  print("\ndone!")
