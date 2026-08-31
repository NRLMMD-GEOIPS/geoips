# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Functions for creating box and whisker plots."""

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Geoips libraries
from geoips.filenames.base_paths import PATHS as gpaths


def boxplot(
    memusg_dict,
    stat="Max. Resident Set Size (GB)",
    rotation=90,
    fontsize=12,
    figsize=(8, 8),
    skip_sources=["modis"],
    geoips_vers=None,
    output_dir=None,
    window_start_datetime=None,
    window_end_datetime=None,
    source_map=None,
):
    """Create box and whisker plots of overall resource usage for procflows."""
    labels = {
        "Max. Resident Set Size (GB)": "GB",
        "System time": "Minutes",
        "Total Time": "Minutes",
        "Number Products": "Number of Products",
    }
    titles = {
        "Max. Resident Set Size (GB)": "Maximum Memory Usage",
        "System time": "Total User Processing Time",
        "Total Time": "Total Processing Time",
        "Number Products": "Number of Products Produced by Procflow",
    }
    if not source_map:
        source_map = {}
    tmp_dict = {}
    for key, dframe in memusg_dict.items():
        if key.lower() in skip_sources:
            continue
        elif " " in key:
            name = " ".join(key.split("_")[2:]).upper()
        elif key in source_map:
            name = source_map[key]
        else:
            name = key.upper()
        data = dframe[stat]
        if "time" in stat.lower():
            data /= 60.0
        tmp_dict[name] = data
    stat_dframe = pd.DataFrame(tmp_dict)
    fig = plt.figure(figsize=figsize)
    bplot = stat_dframe.boxplot(fontsize=fontsize)
    bplot.set_ylabel(labels[stat], fontsize=fontsize)
    bplot.set_title(titles[stat], fontsize=fontsize)
    # bplot.set_xticklabels(bplot["Names"], rotation=rotation)
    plt.xticks(rotation=rotation)
    sname = (
        stat.replace(".", "")
        .replace(" ", "_")
        .lower()
        .replace("(", "")
        .replace(")", "")
    )
    if geoips_vers:
        sname += f"_{geoips_vers}"
    if window_start_datetime and window_end_datetime:
        sname += (
            f"_{window_start_datetime.strftime('%Y%m%dT%H%MZ')}"
            f"-{window_end_datetime.strftime('%Y%m%dT%H%MZ')}"
        )
    if output_dir is None:
        output_dir = Path(gpaths["GEOIPS_OUTDIRS"]).joinpath(
            "processing_statistics", "plots"
        )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig.savefig(f"{output_dir}/geoips_usage_stats_{sname}.png", bbox_inches="tight")
    print(f"Created: {output_dir}/geoips_usage_stats_{sname}.png")
    plt.close(fig)
    return f"{output_dir}/geoips_usage_stats_{sname}.png"


def checkpoint_boxplot(
    memusg_dict,
    stat="elapsed time",
    rotation=90,
    fontsize=18,
    figsize=(24, 8),
    source=None,
    platform=None,
    skip_sources=["modis"],
    skip_sectors=["DYNAMIC-TC", "DYNAMIC TC"],
    plot_sectors=None,
    geoips_vers=None,
    output_dir=None,
    window_start_datetime=None,
    window_end_datetime=None,
    source_map=None,
):
    """Create box and whisker plots of stats broken down by checkpoints."""
    labels = {
        "Max. Resident Set Size (GB)": "GB",
        "System time": "Minutes",
        "Total Time": "Minutes",
        "Number Products": "Number of Products",
        "elapsed time": "Minutes",
    }
    titles = {
        "Max. Resident Set Size (GB)": "Maximum Memory Usage",
        "System time": "Total User Processing Time",
        "Total Time": "Total Processing Time",
        "Number Products": "Number of Products Produced by Procflow",
        "elapsed time": "Total Processing Time for Checkpoint",
    }
    if not source_map:
        source_map = {}
    tmp_dict = {}
    for key, dframe in memusg_dict.items():
        sector_name = "_".join(key.split("_")[0:-1])
        if plot_sectors is not None:
            if sector_name.upper() not in [x.upper() for x in plot_sectors]:
                # print(f"{sector_name} not in {plot_sectors}")
                continue
            else:
                name = key.upper()
        elif key.lower() in skip_sources:
            continue
        elif sector_name.upper() in skip_sectors:
            continue
        elif " " in key:
            name = " ".join(key.split("-")[2:]).upper()
        elif key in source_map:
            name = source_map[key]
        else:
            name = key.upper()
        data = dframe[stat].copy()
        if "time" in stat.lower():  # and stat.lower() != "elapsed time":
            data /= 60.0
        tmp_dict[name] = data.reset_index(drop=True)
        print(f"Max val for {stat} {key}: {data.max()}")
    stat_dframe = pd.DataFrame(tmp_dict)
    box_color = {
        "ZARR": "darkgreen",
        "MEMMAP": "crimson",
    }
    col_types = [x.split("_")[-1] for x in stat_dframe.columns]
    ncol_types = len(list(set(col_types)))
    patch_artist = ncol_types > 1
    all_sectors = ["-".join(x.split("_")[0:-1]) for x in stat_dframe.columns]
    label_colors = ["black", "midnightblue"]
    num_colors = len(label_colors)
    sector_label_colors = {}
    for i, sect in enumerate(sorted(set(all_sectors))):
        sector_label_colors[sect] = label_colors[i % num_colors]
    # fig = plt.figure(figsize=figsize)
    fig, ax = plt.subplots(figsize=figsize)
    boxes, props = stat_dframe.boxplot(
        fontsize=fontsize, patch_artist=patch_artist, return_type="both", ax=ax
    )
    boxes.set_ylabel(labels[stat], fontsize=fontsize)
    if platform and platform != "all":
        title = titles[stat] + f"\n{platform.upper()} {source.upper()}"
    else:
        title = titles[stat] + f"\n{source.upper()}"
    boxes.set_title(title, fontsize=fontsize)
    for i, label in enumerate(boxes.get_xticklabels()):
        sector_name = "-".join(label.get_text().split("_")[0:-1])
        if ncol_types > 1:
            label.set_color(sector_label_colors[sector_name])
    # for box, col_type in zip(boxes.artists, col_types):
    # box.set_facecolor(box_color[col_type])
    if ncol_types > 1:
        for patch, col_type in zip(props["boxes"], col_types):
            patch.set_facecolor(box_color[col_type])
    # bplot.set_xticklabels(bplot["Names"], rotation=rotation)
    plt.xticks(rotation=rotation)
    sname = (
        stat.replace(".", "")
        .replace(" ", "_")
        .lower()
        .replace("(", "")
        .replace(")", "")
    )
    if source:
        sname += f"_{source}"
    if platform:
        sname += f"_{platform}"
    if geoips_vers:
        sname += f"_{geoips_vers}"
    if window_start_datetime and window_end_datetime:
        sname += (
            f"_{window_start_datetime.strftime('%Y%m%dT%H%MZ')}"
            f"-{window_end_datetime.strftime('%Y%m%dT%H%MZ')}"
        )
    if output_dir is None:
        output_dir = Path(gpaths["GEOIPS_OUTDIRS"]).joinpath(
            "processing_statistics", "plots"
        )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    sname = f"{output_dir}/geoips_checkpoint_usage_stats_{sname}"
    if plot_sectors:
        sname += "_" + "_".join(plot_sectors).replace(" ", "-")
    fig.savefig(f"{sname}.png", bbox_inches="tight")
    print(f"Created: {sname}.png")
    plt.close(fig)
    return f"{sname}.png"
