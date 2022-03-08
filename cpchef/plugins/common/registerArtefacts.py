# This is the common ComputePods Chef plugin which (re)registers all known
# artefacts.

# It provides the MajorDomo details on which artefacts this Chef knows how
# to work with.

import cpchef.plugins
import yaml

def registerPlugin(config, managers, natsClient) :
  print("Registering cpchef.plugins.common.registerArtefacts plugin via registerPlugin")
  print(config['artefactRegistrars'])

  @natsClient.subscribe("artefacts.registerTypes")
  async def reRegisterKnownArtefacts(subject, data) :

    artefactRegistrars = []
    if 'artefactRegistrars' in config :
      artefactRegistrars = config['artefactRegistrars']

    for aRegistrar in artefactRegistrars :
      await aRegistrar(config, natsClient)

  print("Finished registering cpchef.plugins.common.registerArtefacts Plugin")
