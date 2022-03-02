""" Load and normalize the cpmd configuration """

import argparse
import importlib
import logging
import os
import pkgutil
import sys
import traceback
import yaml

import cputils.yamlLoader

def parseCliArgs() :
  argparser = argparse.ArgumentParser(
    description="A process which runs, on behalf of users, one type of task inside a ComputePod."
  )
  argparser.add_argument("-c", "--config", action='append',
    default=[], help="overlay configuration from file"
  )
  argparser.add_argument("-p", "--plugins", action='append',
    default=[], help="add a directory of plugins"
  )
  argparser.add_argument("-v", "--verbose", default=False,
    action=argparse.BooleanOptionalAction,
    help="show the loaded configuration"
  )
  argparser.add_argument("-d", "--debug", default=False,
    action=argparse.BooleanOptionalAction,
    help="provide debugging output"
  )
  return argparser.parse_args()

def loadConfig(cliArgs) :

  """

  Load the configuration by merging any `cpmdConfig.yaml` found in the
  current working directory, and then any other configuration files
  specified on the command line.

  Then perform the following normalisation:

  """
  print("Hello from loadConfig")

  config = {
    'verbose' : False,
    'debug'   : False,
    'natsServer' : {
      'host' : '0.0.0.0',
      'port' : 4222
    },
    'pluginsDirs' : [ ]
  }

  if cliArgs.verbose :
    config['verbose'] = cliArgs.verbose

  if cliArgs.debug :
    config['debug'] = cliArgs.debug

  unLoadedConfig = cliArgs.config.copy()
  unLoadedConfig.insert(0,'cpchefConfig.yaml')
  print(yaml.dump(unLoadedConfig))
  while 0 < len(unLoadedConfig) :
    aConfigPath = unLoadedConfig[0]
    del unLoadedConfig[0]
    if os.path.exists(aConfigPath) :
      try :
        cputils.yamlLoader.loadYamlFile(config, aConfigPath)
        if 'include' in config :
          unLoadedConfig.extend(config['include'])
          del config['include']
      except Exception as err :
        print("Could not load configuration from [{}]".format(aConfigPath))
        print(err)

  if cliArgs.plugins :
    config['pluginsDirs'] = cliArgs.plugins
  config['pluginsDirs'].insert(0, 'cpchef/plugins')

  if config['verbose'] :
    print("--------------------------------------------------------------")
    print(yaml.dump(config))
    print("--------------------------------------------------------------")

  return config

async def loadPluginsFrom(
  aPkgPath, aPluginsDir, config, natsClient, artefactRegistrars
) :
  for (_, module_name, _) in pkgutil.iter_modules([aPluginsDir]) :
    modulePackageDir = os.path.join( aPluginsDir, module_name, '__init__.py')
    modulePackagePy  = os.path.join( aPluginsDir, module_name + '.py')
    if os.path.isfile(modulePackageDir) :
      await loadPluginsFrom(
        aPkgPath + '.' + module_name,
        os.path.dirname(modulePackageDir),
        config,
        natsClient,
        artefactRegistrars
      )
    elif os.path.isfile(modulePackagePy) :
      logging.info("Importing the {}.{} plugin".format(aPkgPath, module_name))
      thePlugin = importlib.import_module(aPkgPath+'.'+module_name)
      if hasattr(thePlugin, 'registerPlugin') :
        logging.info("Registering the {}.{} plugin".format(aPkgPath, module_name))
        thePlugin.registerPlugin(config, natsClient)
      else:
        logging.info("Plugin {}.{} has no registerPlugin method!".format(aPkgPath, module_name))
      if hasattr(thePlugin, 'registerArtefacts') :
        print("Adding the registerArtefacts method from the {}.{} plugin".format(aPkgPath, module_name))
        #
        # store for later registration requests...
        #
        artefactRegistrars.append(thePlugin.registerArtefacts)
        #
        # now register for the first time...
        #
        try :
          await thePlugin.registerArtefacts(config, natsClient)
        except Exception as err :
          print("\n----------------------------------------------------------")
          print("ArtefactType registration exception")
          print(f"in module: {aPkgPath}.{module_name}")
          print(f"loaded from: {aPluginsDir}\n")
          print("".join(traceback.format_exc()))
          print("continuing....")
          print("----------------------------------------------------------\n")
          await natsClient.sendMessage("failed.register.artefacts", None)
      else:
        print("Plugin {}.{} has no registerArtefacts method!".format(aPkgPath, module_name))

async def loadPlugins(config, natsClient) :
  config['artefactRegistrars'] = []
  artefactRegistrars = config['artefactRegistrars']

  for aPluginsDir in config['pluginsDirs'] :
    aPkgPath = aPluginsDir.replace('/','.')
    if aPluginsDir.startswith('cpchef') :
      aPluginsDir = os.path.join(os.path.dirname(__file__), aPluginsDir.replace('cpchef/', ''))
    if not aPluginsDir.startswith('/') :
      currentWD = os.path.abspath(os.getcwd())
      if currentWD not in sys.path :
        sys.path.insert(0, currentWD)
    await loadPluginsFrom(
      aPkgPath, aPluginsDir, config, natsClient, artefactRegistrars
    )

  print(config['artefactRegistrars'])
  print("")
  print("Waiting for build requests")
  print("")
