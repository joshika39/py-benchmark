import json
import os
import subprocess
import urllib.parse
import csv
import re
from jsonservice import JsonService

service = JsonService("config.dotnet.json", create_if_not_exists=False)

csv_header = ["Requests/sec_Avg", "Requests/sec_Stdev", "Requests/sec_Max",
              "Latency_Avg(ms)", "Latency_Stdev(ms)", "Latency_Max(ms)"]

# Extract server details
server = service.read("server")
base_url = f"http://{server['host']}:{server['port']}"
csv_file = "dotnet-results"

use_one_file = True

def get_file_name(endpoint: str, method: str):
    return f"{csv_file}_{endpoint}_{method}.csv" if not use_one_file else f"{csv_file}.csv"


def create_csv_file(file_name: str, contents: list):
    if use_one_file:
        contents = ["Endpoint", "Method"] + contents

    with open(file_name, "w") as f:
        writer = csv.writer(f)
        writer.writerow(contents)


def write_csv_file(endpoint: str, method: str, metrics: dict):
    contents = [
        metrics.get("Req/Sec_Avg", ""),
        metrics.get("Req/Sec_Stdev", ""),
        metrics.get("Req/Sec_Max", ""),
        metrics.get("Latency_Avg(ms)", ""),
        metrics.get("Latency_Stdev(ms)", ""),
        metrics.get("Latency_Max(ms)", "")
    ]

    if use_one_file:
        contents = [endpoint, method] + contents

    with open(get_file_name(endpoint, method), "a") as f:
        writer = csv.writer(f)
        writer.writerow(contents)


def parse_wrk_output(output):
    _metrics = {}

    # Extract latency stats (Avg, Stdev, Max)
    latency_match = re.search(
        r"Latency\s+([\d.]+)([a-z]+)\s+([\d.]+)([a-z]+)\s+([\d.]+)([a-z]+)", output
    )
    if latency_match:
        avg_latency = float(latency_match.group(1))
        stdev_latency = float(latency_match.group(3))
        max_latency = float(latency_match.group(5))

        if latency_match.group(2) == "us":  # microseconds to milliseconds
            avg_latency /= 1000
        if latency_match.group(4) == "us":
            stdev_latency /= 1000
        if latency_match.group(6) == "us":
            max_latency /= 1000

        _metrics["Latency_Avg(ms)"] = avg_latency
        _metrics["Latency_Stdev(ms)"] = stdev_latency
        _metrics["Latency_Max(ms)"] = max_latency

    # Extract Req/Sec stats (Avg, Stdev, Max)
    reqs_match = re.search(
        r"Req/Sec\s+([\d.]+[a-z]?)\s+([\d.]+[a-z]?)\s+([\d.]+[a-z]?)", output
    )
    if reqs_match:
        avg_reqs = float(reqs_match.group(1).replace("k", "e3"))
        stdev_reqs = float(reqs_match.group(2).replace("k", "e3"))
        max_reqs = float(reqs_match.group(3).replace("k", "e3"))

        _metrics["Req/Sec_Avg"] = avg_reqs
        _metrics["Req/Sec_Stdev"] = stdev_reqs
        _metrics["Req/Sec_Max"] = max_reqs

    return _metrics

def get_url(endpoint):
    path = endpoint["path"]
    query = endpoint.get("query", {})

    if query:
        query_string = urllib.parse.urlencode(query)
        full_url = f"{base_url}{path}?{query_string}"
    else:
        full_url = f"{base_url}{path}"
    return full_url

def main():
    if use_one_file:
        create_csv_file(f"{csv_file}.csv", csv_header)

    for endpoint in service.read("endpoints"):
        method = endpoint.get("method", "GET")
        body = endpoint.get("body", {})
        if not use_one_file:
            create_csv_file(get_file_name(endpoint["path"], method), csv_header)
        full_url = get_url(endpoint)

        wrk_command = ["wrk", "-t8", "-c100", "-d10s"]

        if method == "POST" and body:
            lua_script = f"""
            wrk.method = "POST"
            wrk.body = '{json.dumps(body)}'
            wrk.headers["Content-Type"] = "application/json"
            """
            with open("post_request.lua", "w") as lua_file:
                lua_file.write(lua_script)
            wrk_command += ["-s", "post_request.lua"]

        wrk_command.append(full_url)

        result = subprocess.run(wrk_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)

        metrics = parse_wrk_output(result.stdout)
        if metrics:
            write_csv_file(endpoint["path"], method, metrics)

    if os.path.exists("post_request.lua"):
        os.remove("post_request.lua")


if __name__ == "__main__":
    main()