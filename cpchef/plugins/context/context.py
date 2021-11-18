# This is ConTeXt ComputePods Chef plugin

# It provides the Chef with recipes on how to typeset ConTeXt documents....

import asyncio
import os
import signal
import yaml
from aiofiles.os import wrap

aioMakedirs = wrap(os.makedirs)
aioSystem   = wrap(os.system)

from cputils.debouncingTaskRunner import \
  NatsLogger, FileLogger, MultiLogger, DebouncingTaskRunner
from cpchef.utils import chefUtils
import cpchef.plugins

def registerPlugin(config, natsClient) :
  print("Registering ConTeXt plugin via registerPlugin")
  chefUtils()

  @natsClient.subscribe("build.from.>")
  async def dealWithBuildRequest(subject, data) :
    scriptsDir = os.path.abspath(os.path.dirname(__file__))
    workingDir = os.path.join(os.getcwd(), 'tmpDir')
    if 'workingDir' in config :
      workingDir = config['workingDir']
    await aioSystem(f"rm -rf {workingDir}")
    await aioMakedirs(workingDir, exist_ok=True)
    projectDir = workingDir
    if 'path' in data : projectDir = data['path']
    projectDir = os.path.abspath(os.path.expanduser(projectDir))
    taskName = "aTask"
    if 'name' in data : taskName = data['name']
    documentName = taskName
    if 'doc' in data : documentName = data['doc']
    podName = None
    if 'podName' in data : podName = data['podName']
    userName = None
    if 'userName' in data : userName = data['userName']
    if userName is not None and podName is not None :
      projectDir = f"{userName}@{podName}:{projectDir}"
    taskDetails = {
      'cmd' : [
        'sh',
        os.path.join(scriptsDir, 'context.sh'),
        documentName,
        projectDir
      ],
      'projectDir' : workingDir
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

    workDone = asyncio.Event()

    def doneCallback() :
      print("DONE callback!")
      workDone.set()

    theTask = DebouncingTaskRunner(
      1, taskName, taskDetails, taskLog, signal.SIGHUP,
      doneCallback=doneCallback,
    )
    await theTask.reStart()
    await workDone.wait()
    print("ALL DONE!")
    await natsClient.sendMessage('done.'+subject[0], {
      'retCode' : theTask.getReturnCode()
    })

  print("Finished registering Context Plugin")

async def registerArtefacts(config, natsClient) :
  await natsClient.sendMessage("artefact.register.type.pdfFile",{
    "name" : "pdfFile",
    "extensions" : [
      "*.pdf"
    ]
  })
