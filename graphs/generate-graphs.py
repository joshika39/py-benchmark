import pandas as pd
import matplotlib.pyplot as plt

dotnet_df = pd.read_csv('../benchmark/dotnet-results.csv')
express_df = pd.read_csv('../benchmark/express-results.csv')

def create_combined_graph(property_name, ylabel, output_filename, save_csv=True):
    combined_data = pd.concat([
        dotnet_df[['Endpoint', property_name]].assign(Framework='.NET'),
        express_df[['Endpoint', property_name]].assign(Framework='Express.js')
    ])

    plt.figure(figsize=(12, 6))
    for framework in combined_data['Framework'].unique():
        subset = combined_data[combined_data['Framework'] == framework]
        plt.plot(subset['Endpoint'], subset[property_name], marker='o', label=framework)

    plt.title(f'{ylabel} Comparison (Combined)')
    plt.ylabel(ylabel)
    plt.xlabel('Endpoint')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_csv:
        print("Saving the graph as a jpg file...")
        plt.savefig(f'./{output_filename}.jpg')
    else:
        plt.show()
        #output_path = f'./{output_filename}'
        #combined_data.to_csv(output_path, index=False)

create_combined_graph('Requests/sec_Avg', 'Requests/sec (Average)', 'requests_sec_avg_comparison')
create_combined_graph('Requests/sec_Stdev', 'Requests/sec (Standard Deviation)', 'requests_sec_stdev_comparison')
create_combined_graph('Requests/sec_Max', 'Requests/sec (Max)', 'requests_sec_max_comparison')
create_combined_graph('Latency_Avg(ms)', 'Latency (ms) Average', 'latency_avg_comparison')
create_combined_graph('Latency_Stdev(ms)', 'Latency (ms) Standard Deviation', 'latency_stdev_comparison')
create_combined_graph('Latency_Max(ms)', 'Latency (ms) Max', 'latency_max_comparison')

