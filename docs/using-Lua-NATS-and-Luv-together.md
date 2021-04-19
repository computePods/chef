# Faking LuaSockets with Luv

## Goal

ComputePods Chef needs to:

- spawn and wait for multiple processes,
  (Luv [spawn](https://github.com/luvit/luv/blob/master/docs.md#uv_process_t--process-handle)
  with possible [async](https://github.com/luvit/luv/blob/master/docs.md#uv_async_t--async-handle))
  
- be script-able,  (Lua?)

- be able to load and use YAML ([Lyaml](https://github.com/gvvaughan/lyaml)?)

- report progress of the spawned processes to the computePod

    - completion with return status or error codes
      ([Luv spawn/on-exit](https://github.com/luvit/luv/blob/master/docs.md#uv_process_t--process-handle))
    
    - monitor logfile updates? ([Luv stdout/stderr using Luv
      pipes](https://github.com/luvit/luv/blob/master/docs.md#uv_process_t--process-handle))
    
- be able to signal/kill a spawned process ([Luv 
  process_kill](https://github.com/luvit/luv/blob/master/docs.md#uvprocess_killprocess-signum))

- be able to make https requests on the syncThing server. 
  **See: [luv-coro-http](https://github.com/creationix/luv-coro-http)**

## Problem

I would *like* to use:

-  [Luv](https://github.com/luvit/luv) for process management.

-  [Lua-NATS](https://github.com/dawnangel/lua-nats)
   for inter-container / inter-pod communication.
   
- Secure Lua-NATS using double ended tls/ssl, to do *this* we need to add a 
  wrapper for [Luasec](https://github.com/brunoos/luasec).
  See also: https://github.com/deleisha/libuv-tls
  See also: [coro-http-luv](https://github.com/squeek502/coro-http-luv)
  **See also: [luv-coro-http](https://github.com/creationix/luv-coro-http)**
  
- Secure Lua-NATS with NKeys (need to implement something like
  [nkeys.rb](https://github.com/nats-io/nkeys.rb) using
  [luanacha](https://github.com/philanc/luanacha)).

Lua-NATS uses [LuaSockets](https://github.com/diegonehab/luasocket) to 
implement sending information "on-the-wire", but Luv also implements a 
socket interface. 

**Q:** Can the LuaSockets and Lua:Sockets be used in the *same* process? 

**A:** Yes they probably could as they simply invoke the same lower level 
C calls. 

**Q:** Can the Lua-NATS and Luv "loops" interwork? 

**A:** Only if we "hack" Lua-NATS to use LuaSockets in no-blocking mode, 
*OR* we wrap Luv-Sockets in the minimal LuaSocket interface which is used by 
Lua-NATS. 

The Lua-NATS "loop" is implemented in the client:wait() and response.read 
methods. This implements a busy loop which *blocks* on the socket reads. 
This means that Luv MUST run Lua-NATS in a "hacked" non-blocking mode, 
*OR* we wrap Luv-Sockets in a LuaSockets interface. 

The Luv "loop" is (generally) the "default" "loop" which coordinates all 
callback behaviour.

## Solutions

1. Just use *all* of Lua-NATS, LuaSockets, and Luv. (need to hack Lua-NATS)

2. Wrap the Luv stream methods required by the lua-nats code, in a 
   LuaSockets interface. We "only" need to wrap 7 methods... 

3. Could use the [copas](https://github.com/keplerproject/copas) strategy 
   of wrapping LibSockets (see copas.wrap in the source code). However, 
   this would break the expected behaviour of LibSockets from Lua-NATS' 
   point of view. (Can/should we use Copas with Lua-NATS for the frontend? 
   -- Probably not as the Xavante webserver is tailored to Copas' way of 
   working but Lua-NATS is not.) 

## Solution 2's strategy

Write a simple Lua level wrapper implementing the methods (below) that 
lua-nats expects from LuaSocket but implemented using Lua LUV's sockets 
instead. 

**TCP:**

- connect(host, port) --> uv.tcp_connect (tcp)

- receive(len) --> uv.read_start (stream)

- send(buffer)  --> uv.write or uv.try_write (stream)

- setoption(???) --> uv.tcp_nodelay (tcp)

- settimeout(???) --> use uv_timer_t to wrap around stream

- shutdown(???) --> uv.shutdown (stream)

- getfd(???) --> ???? (needed for luasec operation; need to create fd 
  outside of luv and then hand it to
  [uv.tcp_open/uv.new_tcp](https://github.com/luvit/luv/blob/master/docs.md#uvnew_tcpflags)
  or use the 
  [uv.fileno method](https://github.com/luvit/luv/blob/master/docs.md#uvfilenohandle)). 

**UNIX:**

- connect(path) --> uv.pipe_connect (pipe)

- receive(len) --> uv.read_start (stream)

- send(buffer) --> uv.write or uv.try_write (stream)

- shutdown(???) --> uv.shutdown (stream)
