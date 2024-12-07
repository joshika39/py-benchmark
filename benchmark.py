import json
import subprocess
import urllib.parse
import csv
import re
from jsonservice import JsonService

service = JsonService("config.json", create_if_not_exists=False)

# Extract server details
server = service.read("server")
base_url = f"http://{server['host']}:{server['port']}"

# Prepare CSV file
csv_file = "benchmark_results.csv"
csv_header = ["Endpoint", "Method", "Requests/sec", "Latency_Min(ms)", "Latency_Max(ms)", "Latency_Mean(ms)", "Latency_Stdev(ms)", "Transfer/sec"]

# Write CSV header
with open(csv_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(csv_header)

# Function to parse wrk output
def parse_wrk_output(output):
    metrics = {}
    # Extract requests/sec
    reqs_match = re.search(r"Requests/sec:\s+([\d.]+)", output)
    if reqs_match:
        metrics["Requests/sec"] = float(reqs_match.group(1))

    # Extract latency stats
    latency_match = re.search(r"Latency\s+(\d+\.\d+)ms\s+(\d+\.\d+)ms\s+(\d+\.\d+)ms\s+(\d+\.\d+)ms", output)
    if latency_match:
        metrics["Latency_Min(ms)"] = float(latency_match.group(1))
        metrics["Latency_Max(ms)"] = float(latency_match.group(2))
        metrics["Latency_Mean(ms)"] = float(latency_match.group(3))
        metrics["Latency_Stdev(ms)"] = float(latency_match.group(4))

    # Extract transfer rate
    transfer_match = re.search(r"Transfer/sec:\s+([\d.]+)(\w+)", output)
    if transfer_match:
        transfer_value = float(transfer_match.group(1))
        transfer_unit = transfer_match.group(2)
        if transfer_unit == "KB":
            transfer_value *= 1024
        elif transfer_unit == "MB":
            transfer_value *= 1024 * 1024
        metrics["Transfer/sec"] = transfer_value

    return metrics


# Process each endpoint
for endpoint in service.read("endpoints"):
    method = endpoint.get("method", "GET")
    path = endpoint["path"]
    query = endpoint.get("query", {})
    body = endpoint.get("body", {})

    # Construct the full URL with query parameters if present
    if query:
        query_string = urllib.parse.urlencode(query)
        full_url = f"{base_url}{path}?{query_string}"
    else:
        full_url = f"{base_url}{path}"

    # Construct the wrk command
    wrk_command = ["wrk", "-t1", "-c10", "-d10s"]

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
        # Add endpoint and method info
        metrics["Endpoint"] = path
        metrics["Method"] = method

        # Save to CSV
        with open(csv_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                metrics.get("Endpoint", ""),
                metrics.get("Method", ""),
                metrics.get("Requests/sec", ""),
                metrics.get("Latency_Min(ms)", ""),
                metrics.get("Latency_Max(ms)", ""),
                metrics.get("Latency_Mean(ms)", ""),
                metrics.get("Latency_Stdev(ms)", ""),
                metrics.get("Transfer/sec", "")
            ])