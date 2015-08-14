[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/direvius/bfg?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# BFG

BFG is a modular tool and framework for load generation.

As a tool, BFG is intended to be a load generation module in an automated load testing environment.
It will handle creating request to your server(s) using different protocols, maintaining the schedule,
measuring and aggregating the results and sending them to uplinks (Mongo, Graphite, file on disk, etc.)
Ammo preparation, config generation, data storage, analytics and data representation should be done by
other modules of that environment.

As a framework, BFG provides means to implement your own load generator that will be used in that environment.

## Caveat Emptor!

Please be warned: BFG is in a very early alpha. You will encounter bugs when using it. In addition, there are
very many rough edges. With that said, please try it out: I need your feedback to fix the bugs and file down
the rough edges.

### Known issues

* ```batch``` parameter in ammo -- not implemented
* YAML and JSON configs support -- not implemented
* ```raw_file``` parameter in aggregator -- not implemented
* there are no default parameters so you need to specify all of them
* some exceptions in HTTP/2 gun are not handled carefully

## Supported protocols

For now, BFG supports HTTP/2 and it also possible to provide user scenarios as python modules (and you can
support virtually any protocol that way).

## Architectural overview

See architectural scheme source in ```docs/architecture.graphml```. It was created with
[YeD](https://www.yworks.com/en/products/yfiles/yed/) editor, so you’ll probably
need it to open the file.

![Architectural scheme](/docs/architecture.png)

## Requirements and installation

Python 3 is required. Hyper is used for HTTP/2 support.

Install from pip repository:

```
pip install bfg
```

## Quick start

Save following config as ```load.toml```:
```
[gun.mobile]
type = 'http2'
target = "(your HTTP/2 server address here)"

[ammo.myammo]
file = "ammo.line"

[schedule]
ramp = ["line(1, 10, 10s)", "const(10, 10s)"]
line = ["line(1, 30, 1m)"]

[aggregator.caching]
uplinks = []
raw_file = "raw.samples"

[bfg.mobile]
gun = "mobile"
instances = 2
schedule = "ramp"
aggregator = "caching"
ammo = "myammo"
```

Create ammo file ```ammo.line```:
```
/
/my/url
/my/second/url
```

Run bfg:
```
bfg load.toml
```

# Configuration

BFG support [TOML](https://github.com/toml-lang/toml) and [YAML](http://yaml.org/spec/1.2/spec.html) as config file
formats. Look for examples in ```docs/examples```.

The main idea is that you can build several BFGs using *components*. Those components are obtained from component
factories that you configured. Each factory is configured in its own config section. When you ask a component with
key ```key1``` from that factory, it searches for that key in its configuration and returns a component according
with that configuration. The factory also decides if it will return a new component each time you ask for it, or if
it will initialize the components for each key and then just return you a reference to it.

The BFG factory is special. It is the place where all components are binded together. It is the BFG factory who asks
the other factories for the components.

You may want to have a look at the architectural scheme in the corresponding section of this doc where you will see
how the components are connected together.

Thus, the process of configuration is as following:

1. specify configuration for every factory. Teach them how to build the components you want
2. specify configuration for all BFGs you need, mentioning the components you defined before.

For example, let's have a look at this config (in YAML format):

```
aggregator:
  caching:
    uplinks: ['mongo://localhost']
ammo:
  myammo: {file: ./tmp/ammo.line}
gun:
  mobile:
    target: http2.example.org
    type: http2
schedule:
  line: ['line(1, 30, 1m)']
  ramp: ['line(1, 10, 10s)', 'const(10, 10s)']
bfg:
  mobile:
    aggregator: caching
    ammo: myammo
    gun: mobile
    instances: 2
    schedule: ramp
```

We configured ```aggregator```, ```ammo```, ```gun``` and ```schedule``` factories and then used the components in our
```BFG``` factory. There are two schedules configured: ```line``` and ```ramp```, and we are using one of them, ```ramp```
in our ```BFG.mobile``` component. There might also be the second BFG that would be using different ammo and shedule.

## Modules configuration

There are currently five module types:

1. ```ammo``` -- your ammo sources
2. ```schedule``` -- the schedules you will use to send requests
3. ```gun``` -- the guns for different protocols with different settings
4. ```aggregator``` -- results collector. It will also send it to uplinks
5. ```bfg``` -- your BFGs. The place where you build your weapons by connecting other components

### Ammo configuration

For each ammo source, specify following parameters:

* ```file``` -- path to ammo file
* ```format``` -- ammo format

The only supported ammo format by now is Line format. Line file format is very simple: one line equals one request data.
If we have read all the requests from file, BFG will start over automatically.

All markers are assigned to "None".

Line format reader has additional parameter:

```batch``` -- batch size, each task will contain multiple requests. In batch mode, marker is set to ```multi_n```, where
n is the batch size.

For example, look at the following config example (in TOML):

```
[ammo.myammo]
format = "line"
file = "/path/to/ammo.line"
batch = 3
```

Each task will contain 3 lines from ```/path/to/ammo.line``` file 

### Schedule configuration

Each schedule is a list of elementary schedules:

* ```line(start_rps, end_rps, period)``` -- raise load from ```start_rps``` to ```end_rps``` during ```period```
* ```const(rps, period)``` -- hold load ```rps``` for ```period```
* ```step(start_rps, end_rps, step_height, step_period)``` -- stairs-like load from ```start_rps``` to ```end_rps```

```period``` is by default in seconds (34 -> 34 second) but you can also write something like ```2h32m5s``` -> 2 hours, 32 minutes and 5 seconds

Example:
```
[schedule]
ramp = ["line(1, 10, 10s)", "const(10, 1h)"]
```
-- constant load with warm-up period, raise load from 1 rps to 10 rps for 10 seconds and then hold 10 rps for 1 hour

### Gun configuration

Each type of gun is configured in its own way, but the common parameters are:

* ```type``` -- gun type. There are currently two gun types: ```http2`` and ```scenario```
* ```target``` -- where to shoot.

Configuration example:
```
[gun.mobile]
type = 'http2'
target = "http2.example.org"
```

#### HTTP/2 gun

*TODO*

#### Scenario gun

*TODO*


### Aggregator configuration

For each aggregator, specify:

* ```uplinks``` -- list of uplinks, where to send aggregated data
* ```raw_file``` -- a file in which to put raw samples. If empty -- do not write raw samples

The only uplink supported for now is MongoDB. Here is the configuration example:
```
[aggregator.caching]
uplinks = ["mongo://localhost"]
raw_file = "raw.samples"
```

### BFG configuration

Here is the section where you combine other components to work together. These are the parameters:
* ```gun``` -- a gun name (one of those you specified in gun section)
* ```schedule``` -- schedule name
* ```aggregator``` -- aggregator name
* ```ammo``` -- ammo source name
* ```instances``` -- number of workers in this pool

Example:
```
[bfg.mobile]
gun = "mobile"
instances = 2
schedule = "ramp"
aggregator = "caching"
ammo = "myammo"
```

# License

BFG is made available under the MIT License. For more details, see the LICENSE file in the repository.

# Authors

BFG is maintained by Alexey Lavrenuke <direvius@gmail.com>.
