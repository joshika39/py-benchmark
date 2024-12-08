import json
import os
import subprocess
import urllib.parse
import csv
import re
from jsonservice import JsonService

service = JsonService("config.json", create_if_not_exists=False)

# Extract server details
server = service.read("server")
base_url = f"http://{server['host']}:{server['port']}"
csv_file = "benchmark_results"


def create_csv_file(endpoint: str, method: str):
    csv_header = ["Requests/sec_Avg", "Requests/sec_Stdev", "Requests/sec_Max",
                  "Latency_Avg(ms)", "Latency_Stdev(ms)", "Latency_Max(ms)"]
    with open(f"{csv_file}_{endpoint}_{method}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)

def write_csv_file(endpoint: str, method: str, metrics: dict):
    with open(f"{csv_file}_{endpoint}_{method}.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([
            metrics.get("Req/Sec_Avg", ""),
            metrics.get("Req/Sec_Stdev", ""),
            metrics.get("Req/Sec_Max", ""),
            metrics.get("Latency_Avg(ms)", ""),
            metrics.get("Latency_Stdev(ms)", ""),
            metrics.get("Latency_Max(ms)", "")
        ])


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

        # Convert latency units if necessary (us to ms)
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

def main():
    for endpoint in service.read("endpoints"):
        method = endpoint.get("method", "GET")
        path = endpoint["path"]
        query = endpoint.get("query", {})
        body = endpoint.get("body", {})

        create_csv_file(endpoint["path"].replace("/", "_"), method)

        if query:
            query_string = urllib.parse.urlencode(query)
            full_url = f"{base_url}{path}?{query_string}"
        else:
            full_url = f"{base_url}{path}"

        # Construct the wrk command
        wrk_command = ["wrk", "-t8", "-c100", "-d10s", "--latency"]

        # Add Lua script for POST requests with a body
        if method == "POST" and body:
            lua_script = f"""
            wrk.method = "POST"
            wrk.body = '{json.dumps(body)}'
            wrk.headers["Content-Type"] = "application/json"
            """
            with open("post_request.lua", "w") as lua_file:
                lua_file.write(lua_script)
            wrk_command += ["-s", "post_request.lua"]

        # Add the target URL to the command
        wrk_command.append(full_url)

        # Run the command
        print(f"Benchmarking {method} {full_url}...")
        result = subprocess.run(wrk_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)

        # Parse wrk output
        metrics = parse_wrk_output(result.stdout)
        if metrics:
            write_csv_file(endpoint["path"].replace("/", "_"), method, metrics)
    if os.path.exists("post_request.lua"):
        os.remove("post_request.lua")


if __name__ == "__main__":
    main()