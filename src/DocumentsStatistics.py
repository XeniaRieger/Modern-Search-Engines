import os
import pickle
from urllib.parse import urlparse
import matplotlib.pyplot as plt
from datetime import datetime


def count_roots():
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    document_path = os.path.join(serialisation_folder, "documents")
    total_doc = 0
    count_roots_dic = {}

    # access documents
    for file in os.listdir(document_path):
        with open(os.path.join(document_path, file), 'rb') as pickle_file:
            doc = pickle.load(pickle_file)
            parsed_url = urlparse(doc.url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # count documents
            if (count_roots_dic.get(base_url) is None):
                count_roots_dic[base_url] = 1
                total_doc += 1
            else:
                count_roots_dic[base_url] += 1
                total_doc += 1
    return count_roots_dic, total_doc


def summarize_bellow_threshold(dict, total_doc, threshold):
    stats = {}
    stats["2small2notice"] = 0
    for root in dict.keys():
        if (dict.get(root) < total_doc * (threshold / 100)):
            stats["2small2notice"] += dict[root]
        else:
            stats[root] = dict[root]
    return stats


def plot_root_diversity(threshold):
    counted, total_doc = count_roots()
    sum_stats = summarize_bellow_threshold(counted, total_doc, threshold)
    labels = sum_stats.keys()
    values = sum_stats.values()

    fig, ax = plt.subplots()
    ax.pie(values, autopct='%1.1f%%')
    ax.set_xlim((-1, -1.1))
    fig.legend(labels=labels, bbox_transform=fig.transFigure, fontsize="small")
    return fig


def save_graphic(fig, name):
    stats_path = os.path.join(os.getcwd(), "stats")
    if not os.path.exists(stats_path):
        os.makedirs(stats_path)
    plt.savefig(os.path.join(stats_path, (datetime.now().strftime("%Y_%d_%m-%H_%M_%S") + "_" + name)))
    print(f"Saved file {name} to {stats_path}!")


threshold = 1  # if less than n% of the all websites originate from this site, it is summarized
pie = plot_root_diversity(threshold)
save_graphic(pie, "document_diversity_pie_plot")