# This is ConTeXt ComputePods Chef plugin

# It provides the Chef with recipes on how to typeset ConTeXt documents....

import cpchef.plugins
#import yaml

def registerPlugin(config, natsClient) :
  print("Registering ConTeXt plugin via registerPlugin")

  @natsClient.subscribe("build.from.>")
  async def dealWithBuildRequest(subject, data) :
    print("Context plugin build request")
    print(type(subject))
    print(subject)
    print(type(data))
    print(data)
    # do something!!!
    # If we are *inside* an instance method.... we have access to self.
    # which we *will* need to send messages using the natsClient

  print("Finished registering Context Plugin")

async def registerArtefacts(config, natsClient) :
  await natsClient.sendMessage("artefact.register.type.pdfFile",{
    "name" : "pdfFile",
    "extensions" : [
      "*.pdf"
    ]
  })
