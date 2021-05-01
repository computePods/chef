# This is ConTeXt ComputePods Chef plugin

# It provides the Chef with recipes on how to typeset ConTeXt documents....

import plugins
import yaml

async def registerPlugin(natsClient) :
  print("Registering ConTeXt plugin via registerPlugin")

  async def subscribe(subscription, callback) :
    await natsClient.listenForMessages(subscription, callback)

  @subscribe("silly.>")
  async def dealWithSillyMessages(msg) :
    subject = msg.subject
    data = msg.data.decode()
    print(type(subject))
    print(subject)
    print(type(data))
    print(data)
    # do something!!!
    # If we are *inside* an instance method.... we have access to self.
    # which we *will* need to send messages using the natsClient
      

  print("Finished registering Context Plugin")
