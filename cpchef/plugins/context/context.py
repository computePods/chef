# This is ConTeXt ComputePods Chef plugin

# It provides the Chef with recipes on how to typeset ConTeXt documents....

import os
import signal
import yaml

from cputils.debouncingTaskRunner import \
  NatsLogger, FileLogger, MultiLogger, DebouncingTaskRunner
from cpchef.utils import chefUtils
import cpchef.plugins

def registerPlugin(config, natsClient) :
  print("Registering ConTeXt plugin via registerPlugin")
  chefUtils()

  @natsClient.subscribe("build.from.>")
  async def dealWithBuildRequest(subject, data) :
    projectDir = os.getcwd()
    if 'path' in data : projectDir = data['path']
    projectDir = os.path.abspath(os.path.expanduser(projectDir))
    taskName = "aTask"
    if 'name' in data : taskName = data['name']
    documentName = taskName
    if 'doc' in data : documentName = data['doc']
    taskDetails = {
      'cmd' : [
        'context',
        documentName
      ],
      'projectDir' : projectDir
    }
    taskLog = FileLogger("stdout", 5)
    #taskLog = MultiLogger([
    #  FileLogger("stdout", 5),
    #  FileLogger("/tmp/test.log", 5),
    #  NatsLogger(natsClient, "logger", 5),
    #])
    await taskLog.open()

    await taskLog.write([
      "\n",
      "=========================================================\n",
      "Running ConTeXt on:\n",
    ])
    await taskLog.write(yaml.dump(data))
    await taskLog.write("\n")

    theTask = DebouncingTaskRunner(
      1, taskName, taskDetails, taskLog, signal.SIGHUP
    )
    await theTask.reStart()

  print("Finished registering Context Plugin")

async def registerArtefacts(config, natsClient) :
  await natsClient.sendMessage("artefact.register.type.pdfFile",{
    "name" : "pdfFile",
    "extensions" : [
      "*.pdf"
    ]
  })
