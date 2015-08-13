# BFG

BFG is a modular tool and framework for load generation.

As a tool, BFG is intended to be a load generation module in an automated load testing environment.
It will handle creating request to your server(s) using different protocols, maintaining the schedule,
measuring and aggregating the results and sending them to an uplink. Ammo preparation, config generation,
data storage, analytics and data representation should be done by other modules of that environment.

As a framework, BFG provides means to implement your own load generator that will be used in that environment.

## Caveat Emptor!

Please be warned: BFG is in a very early alpha. You will encounter bugs when using it. In addition, there are
very many rough edges. With that said, please try it out: I need your feedback to fix the bugs and file down
the rough edges.

## Supported protocols

For now, BFG supports HTTP/2 and it also possible to provide user scenarios as python modules (and you can
support virtually any protocol that way).

## Architectural overview

See architectural scheme in ```docs/architecture.graphml```. It is created with YeD editor, so you’ll probably
need it to open the file.

## Requirements and installation

Python 3 is required. Hyper is used for HTTP/2 support.

Install from pip repository:

```
pip install bfg
```

## Configuration

BFG support TOML and YAML as config file formats. Look for examples in ```docs/examples```.

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

### Module types

There are currently five module types:

1. ```ammo``` -- your ammo sources
2. ```schedule``` -- the schedules you will use to send requests
3. ```gun``` -- the guns for different protocols with different settings
4. ```aggregator``` -- results collector. It will also send it to uplinks
5. ```bfg``` -- your BFGs. The place where you build your weapons by connecting other components

## License

BFG is made available under the MIT License. For more details, see the LICENSE file in the repository.

## Authors

BFG is maintained by Alexey Lavrenuke <direvius@gmail.com>.
