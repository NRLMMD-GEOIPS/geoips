# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Various utils for processing statistics."""

import pandas as pd
import pyaml_env

# Geoips libraries
from geoips.filenames.base_paths import PATHS as gpaths


def print_stats(dframe, suite_name=" "):
    """Print stats to stdout.

    Parameters
    ----------
    dframe : pandas.core.frame.DataFrame
        DataFrame of statistics
    suite_name : str, optional
        Source name of stats, by default " "
    """
    dmax = dframe.max()
    dmin = dframe.min()
    dmean = dframe.mean()
    dmedian = dframe.median()
    spad = 15
    print(
        f"{suite_name.ljust(35)} {'min'.rjust(spad)} {'max'.rjust(spad)}"
        f"{'mean'.rjust(spad)} {'median'.rjust(spad)}"
    )
    n_logs = len(dframe.index)
    hosts = set(dframe.get("host", []))
    for key in dmax.keys():
        if key in ["parsed log", "log", "host"]:
            continue
        min_str = f"{dmin[key]:5.2f}".rjust(spad)
        max_str = f"{dmax[key]:5.2f}".rjust(spad)
        mean_str = f"{dmean[key]:5.2f}".rjust(spad)
        median_str = f"{dmedian[key]:5.2f}".rjust(spad)
        stat = f"{key.ljust(35)} {min_str} {max_str} {mean_str} {median_str}"
        print(stat)
    print(f"N: {n_logs}")
    if hosts:
        print(f"N Unique Hosts: {len(hosts)} ({' ,'.join(hosts)})")


def create_checkpoint_dataframe(json_data, procflow_usg):
    """Create a checkpoint dataframe that incorporates stats from overall usage stats.

    Parameters
    ----------
    json_data : list
        List of json data entries
    procflow_usg : dict
        Dict of panda dataframes where each key is a different source

    Returns
    -------
    dict
        dict of panda dataframes where each key is a different source
    """
    overall_memusg = {}
    for stats in json_data:
        source = stats["source"]
        if source not in overall_memusg:
            overall_memusg[source] = {}
        procflow_id = stats["procflow_id"]
        checkpoint_group = stats["checkpoint_group"]
        checkpoint_name = stats["checkpoint_name"]
        source = stats["source"]
        sdf = procflow_usg[source]
        # from IPython import embed; embed()
        pusg = sdf[sdf["Procflow ID"] == procflow_id]
        if pusg.size > 0:
            ckey = f"{checkpoint_group}: {checkpoint_name}.{procflow_id}"
            # print(ckey)
            if checkpoint_group == "AREA DEF":
                sector_name = checkpoint_name.split(": ")[1]
            else:
                sector_name = None
            overall_memusg[source][ckey] = {
                "start time": stats["checkpoint_datetime_start"].strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "stop time": stats["checkpoint_datetime_stop"].strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "platform": stats["platform"],
                "Max. Resident Set Size (GB)": stats["max_res_set_size"] * 1e-6,
                "Max. Unique Set Size (GB)": stats["max_unique_set_size"] * 1e-6,
                "Max CPU": stats["max_cpu_percent"],
                "elapsed time": stats["elapsed_time"],
                "time": pusg.index[0],
                "Procflow ID": stats["procflow_id"],
                "Procflow Output Config": stats["output_config"],
                "Sector": sector_name,
            }
            for key in pusg.keys():
                if key in ["Procflow ID", "Procflow Output Config"]:
                    continue
                overall_memusg[source][ckey][f"Overall {key}"] = pusg[key].iloc[0]

    if not overall_memusg:
        print("Could not parse usage from loaded json file.\nNo valid logs?")
        return None
    memusg = {}
    for source in sorted(overall_memusg.keys()):
        memusg[source] = pd.DataFrame(overall_memusg[source].values()).set_index(
            "time", drop=True
        )
    return memusg


def sort_resource_dframe(dframe):
    """Sort resource usage statistics by sector type.

    Parameters
    ----------
    dframe : pandas.core.frame.DataFrame
        Stats

    Returns
    -------
    dict
        Dictionary of dataframes where each key is a different sector type
    """
    unique_sectors = dframe["Sector"].unique()
    # There can be nan's in the dframe, ensure we are only checking strings.
    dynamic_sectors = sorted(
        [x for x in unique_sectors if isinstance(x, str) and x[0:2] == "tc"]
    )
    static_sectors = sorted(
        [x for x in unique_sectors if isinstance(x, str) and x[0:2] != "tc"]
    )
    sector_dframes = {}
    parsed_procflow_configs = {}
    for static_sector in static_sectors:
        print(f"Sorting {static_sector}")
        static_dframe = dframe[dframe["Sector"] == static_sector]
        for procflow_config in static_dframe["Procflow Output Config"]:
            if procflow_config not in parsed_procflow_configs:
                loaded_config = pyaml_env.parse_config(procflow_config)
                system_cache_type = gpaths["GEOIPS_GEOLOCATION_CACHE_BACKEND"]
                if "reader_kwargs" in loaded_config:
                    cache_type = loaded_config["reader_kwargs"].get(
                        "geolocation_cache_backend", system_cache_type
                    )
                else:
                    cache_type = system_cache_type
                parsed_procflow_configs[procflow_config] = cache_type
        memmap_procflows = [
            x
            for x in static_dframe["Procflow Output Config"]
            if parsed_procflow_configs[x] == "memmap"
        ]
        zarr_procflows = [
            x
            for x in static_dframe["Procflow Output Config"]
            if parsed_procflow_configs[x] == "zarr"
        ]
        if memmap_procflows:
            sector_dframes[f"{static_sector}_memmap"] = static_dframe[
                static_dframe["Procflow Output Config"].isin(memmap_procflows)
            ]
        if zarr_procflows:
            sector_dframes[f"{static_sector}_zarr"] = static_dframe[
                static_dframe["Procflow Output Config"].isin(zarr_procflows)
            ]
    print("Sorting Dynamic TC Sectors")
    dynamic_dframe = dframe[dframe["Sector"].isin(dynamic_sectors)]
    for procflow_config in dynamic_dframe["Procflow Output Config"]:
        if procflow_config not in parsed_procflow_configs:
            loaded_config = pyaml_env.parse_config(procflow_config)
            system_cache_type = gpaths["GEOIPS_GEOLOCATION_CACHE_BACKEND"]
            if "reader_kwargs" in loaded_config:
                cache_type = loaded_config["reader_kwargs"].get(
                    "geolocation_cache_backend", system_cache_type
                )
            else:
                cache_type = system_cache_type
            parsed_procflow_configs[procflow_config] = cache_type
    memmap_procflows = [
        x
        for x in dynamic_dframe["Procflow Output Config"]
        if parsed_procflow_configs[x] == "memmap"
    ]
    zarr_procflows = [
        x
        for x in dynamic_dframe["Procflow Output Config"]
        if parsed_procflow_configs[x] == "zarr"
    ]
    if memmap_procflows:
        sector_dframes["Dynamic-TC_memmap"] = dynamic_dframe[
            dynamic_dframe["Procflow Output Config"].isin(memmap_procflows)
        ]
    if zarr_procflows:
        sector_dframes["Dynamic-TC_zarr"] = dynamic_dframe[
            dynamic_dframe["Procflow Output Config"].isin(zarr_procflows)
        ]
    return sector_dframes


def sort_resource_stats(resource_stats_dict, sort_platform=False):
    """Sort resource usage for each source by different sector types.

    Parameters
    ----------
    resource_stats_dict : dict
        Dictionary of dataframes for each source
    sort_platform : bool, optional
        Separate dataframes by platform in addition to source, by default False

    Returns
    -------
    dict
        dictionary of dataframes
    """
    sorted_dframes = {}
    for source, dframe in resource_stats_dict.items():
        sorted_dframes[source] = {}
        if sort_platform:
            for platform in set(dframe["platform"]):
                sorted_dframes[source][platform] = sort_resource_dframe(
                    dframe.where(dframe["platform"] == platform).dropna(
                        subset=["platform"]
                    )
                )
        else:
            sorted_dframes[source]["all"] = sort_resource_dframe(dframe)
    return sorted_dframes
