# ComputePods Chef plugins

Any Python file found in this directory will be loaded and the Python 
class with the same name as the file will in instantiated. 

This instantiation will be passed a NatsClient object which is connected 
to a NATS server. This allows the plugin to register its interest in any 
or all known NATS message subjects. 

At the moment we have the following NATS message subjects:

- **`task.request.dependencies`** : a request from a MajorDomo for one or 
  more Chefs to provide the dependencies for a given object. 

- **`task.offer.dependencies`** : an offer, from one or more Cherfs, of 
  dependencies for a given object.

- **`task.request.build`** : a request from a MajorDomo for one or more 
  Chefs to build a given object from its dependencies. 

- **`task.offer.build`** : an offer from a Chef to build a given object. 

- **`task.build.containerName`** : a confirmation for a particular Chef to 
  go ahead and build a given object. 
