#!/usr/bin/env python3
"""Download classic systems papers from ArXiv."""

import os
import urllib.request
import time

# List of ArXiv IDs for classic systems papers (1990-2026)
PAPERS = [
    # Containers & Virtualization
    ("1410.0846", "docker_intro_reproducible_research"),
    ("1501.02967", "docker_security_analysis"),
    ("2206.00789", "unikernel_linux_ukl"),
    # Orchestration & Kubernetes
    ("2305.07651", "kubernetes_resource_prediction"),
    # eBPF & Linux Kernel
    ("2410.00026", "ebpf_runtime_linux_kernel"),
    # Distributed Systems & Consensus
    ("2004.05074", "paxos_vs_raft_consensus"),
    ("2202.06348", "understanding_paxos_consensus"),
    # Big Data Frameworks
    ("1707.04939", "hadoop_spark_evaluation"),
    ("1904.11812", "spark_supercomputers_benchmark"),
    ("1811.08834", "spark_ecosystem_survey"),
    ("1403.1528", "tale_two_data_intensive_paradigms"),
    ("1408.6008", "hadoop_yarn"),
    # Storage Systems
    ("2007.11112", "dbos_data_centric_os"),
    ("1807.05308", "tabular_rosa_os_heterogeneous"),
    ("1909.00363", "alluxio_virtual_distributed_storage"),
    # ML/AI Infrastructure
    ("1608.01390", "tensorflow_large_scale_ml"),
    ("1912.05910", "dask_parallel_computing"),
    ("1910.11494", "ray_distributed_ai"),
    ("1706.03762", "attention_is_all_you_need"),
    # Data Pipelines
    ("2207.09430", "kafka_real_time_data_pipelines"),
]


def download_paper(arxiv_id: str, filename: str, papers_dir: str):
    """Download a paper from ArXiv."""
    # ArXiv PDF URL
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    filepath = os.path.join(papers_dir, f"{filename}.pdf")

    if os.path.exists(filepath):
        print(f"  [SKIP] {filename} (already exists)")
        return

    print(f"  [DOWNLOAD] {arxiv_id} -> {filename}.pdf")
    try:
        urllib.request.urlretrieve(url, filepath)
        time.sleep(1)  # Be nice to ArXiv
    except Exception as e:
        print(f"  [ERROR] {arxiv_id}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)


def main():
    # papers/ stays at week8/papers (sibling of data/) so the app can mount it
    week8_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    papers_dir = os.path.join(week8_root, "papers")
    os.makedirs(papers_dir, exist_ok=True)

    print("Downloading 20 classic systems papers from ArXiv...")
    print(f"Destination: {papers_dir}/\n")

    for arxiv_id, filename in PAPERS:
        download_paper(arxiv_id, filename, papers_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
