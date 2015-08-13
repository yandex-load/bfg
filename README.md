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

## License

BFG is made available under the MIT License. For more details, see the LICENSE file in the repository.

## Authors

BFG is maintained by Alexey Lavrenuke <direvius@gmail.com>.
