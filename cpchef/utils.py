
import yaml

config = None

def setConfig(theConfig) :
  global config
  config = theConfig

def chefUtils() :
  print("hello from chef utils!")
  print(yaml.dump(config))
