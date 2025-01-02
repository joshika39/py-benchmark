# Python Benchmarking and Graphing Tool

> [!IMPORTANT]
> - This is a python port of the popular `wrk` tool.
> - You will need to have `python` and `pip` installed on your machine to run this tool.

## Setup

> [!NOTE]
> The project was meant to be run on a linux machine. You can try to run it on windows, but it's not guaranteed to work.

### Python
You can install the required dependencies by running the following command:

```bash
# Create a virtual environment for better isolation
python -m venv venv && source venv/bin/activate

pip install -r requirements.txt
```

### Wrk

You can install `wrk` by running the following command:
```bash
# This is debian based, but you can find the equivalent for your distro
sudo apt-get install build-essential libssl-dev git -y

git clone https://github.com/wg/wrk.git && cd wrk

sudo make

# move the executable to somewhere in your PATH, ex: 
sudo cp wrk /usr/local/bin
```

## Usage

### Benchmarking

First, `cd` into the `benchmark` directory. Then you'll need a configuration file. Take the `./benchmark/config.example.json` file and copy it to `./benchmark/config.json`. You can then edit the `config.json` file to suit your needs.

> [!IMPORTANT]
> - Don't forget to change the `server.host` and `server.port` to match your server.
> - Only `GET` and `POST` requests are supported. *Others will be ignored*.

Let's assume you have a server running on `localhost:3000` and you want to benchmark it and you already have the configuration file ready. You can run the following command:
```bash
# Preferably you named you file config.json. If not, you have to change the CONFIG_FILE variable in ./benchmark/benchmark.py

python benchmark.py
```

### Images

You can generate graphs from the output `csv` of the benchmarking tool *(under the benchmark directory)*


