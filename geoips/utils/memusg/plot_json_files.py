# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Find JSON statistics files on disk and plot stats."""

import argparse
from datetime import datetime, timedelta
import pandas as pd
from glob import glob
import isodate
from pathlib import Path
import pytz

from .boxplots import boxplot, checkpoint_boxplot
from .dataframe_utils import create_checkpoint_dataframe, sort_resource_stats

# Geoips libraries
from geoips.filenames.base_paths import PATHS as gpaths


def get_json_file_lists(
    json_stats_output_directory,
    geoips_version,
    window_start,
    window_end,
    sector_type=None,
    include_checkpoints=False,
):
    """Find list of JSON statistic files to load.

    Parameters
    ----------
    json_stats_output_directory : str
        Base output directory of JSON files
    geoips_version : str
        Version of GeoIPS
    window_start : datetime.datetime
        Start of search window
    window_end : datetime.datetime
        End of search window
    sector_type : str, optional
        Limit jsons to either: mixed, static, or tc specific procflows, by default None
    include_checkpoints : bool, optional
        Attempt to load detailed checkpoint statistics, by default False

    Returns
    -------
    dict
        List of files for each key
    """
    overall_jsons = []
    checkpoint_jsons = []
    ctime = window_start
    while ctime <= window_end:
        sdir = ctime.strftime(
            str(
                Path(json_stats_output_directory).joinpath(
                    geoips_version, "config_based/overall/%Y%m/%Y%m%d/%Y%m%d.%H"
                )
            )
        )
        if sector_type is not None:
            file_glob = f"*{sector_type}*"
        else:
            file_glob = "*"
        sglob = str(Path(sdir).joinpath(file_glob))
        print(f"Checking: {sglob}")
        overall_jsons += glob(sglob)
        if include_checkpoints:
            sdir = sdir.replace("/overall/", "/resource_usage_checkpoints/")
            sglob = str(Path(sdir).joinpath(file_glob))
            print(f"Checking: {sglob}")
            checkpoint_jsons += glob(sglob)
        ctime += timedelta(hours=1)
    return {
        "overall_procflow_jsons": overall_jsons,
        "checkpoint_jsons": checkpoint_jsons,
    }


def load_jsons_into_single_dataframe(
    json_files, json_filename_keys=None, rename_columns=False
):
    """Load JSON files into single pandas dataframe.

    Parameters
    ----------
    json_files : list
        List of json files to read
    json_filename_keys   : list, optional
        List of filename tags used to differentiate experiments
    rename_columns : bool, optional
        Rename columns to be more plotting friendly, by default False

    Returns
    -------
    pandas.core.frame.DataFrame
        Dataframe of stats
    """
    df = pd.DataFrame()
    if not json_filename_keys:
        json_filename_keys = ["*"]
    for jfile in json_files:
        print(f"Reading: {jfile}")
        data = pd.read_json(jfile)
        for tag in json_filename_keys:
            if tag in jfile.split("/")[-1]:  # Check if a json key is in filename
                data["source"] = data["source"] + "_" + tag
                break

        df = pd.concat([df, data], ignore_index=True)
    if rename_columns:
        df = df.rename(
            columns={
                "ru_maxrss": "Max. Resident Set Size (GB)",
                "ru_utime": "System time",
                "num_products_created": "Number Products",
                "procflow_id": "Procflow ID",
                "output_config": "Procflow Output Config",
            }
        )
        df["Max. Resident Set Size (GB)"] *= 1e-6
    for key, vals in df.items():
        if "datetime" in key:
            df[key] = pd.to_datetime(vals, unit="ms")
    if "starting_time" in df and "ending_time" in df:
        df["Total Time"] = [
            x.total_seconds() for x in (df["ending_time"] - df["starting_time"])
        ]
    return df


def create_usage_dataframe_per_source(loaded_json_dataframe):
    """Separate dataframe into multiple by source.

    Parameters
    ----------
    loaded_json_dataframe : pandas.core.frame.DataFrame
        Single dataframe with all stats

    Returns
    -------
    dict
        Dict of DataFrames where each key is a different source
    """
    source_dframes = {}
    for source in set(loaded_json_dataframe.source):
        source_dframes[source] = loaded_json_dataframe.where(
            loaded_json_dataframe["source"] == source
        ).dropna()
    return source_dframes


def load_jsons_into_dataframes_by_source(json_files, json_filename_keys=None):
    """Take list of json files and return dict of DataFrames.

    Parameters
    ----------
    json_files : list
        List of json files to read
    json_filename_keys   : list, optional
        List of filename tags used to differentiate experiments

    Returns
    -------
    dict
        Dict of DataFrames where each key is a different source
    """
    df = load_jsons_into_single_dataframe(
        json_files, json_filename_keys, rename_columns=True
    )
    return create_usage_dataframe_per_source(df)


def main():
    """Plot statistics."""
    parser = argparse.ArgumentParser()
    default_json_stats_dir = Path(gpaths["GEOIPS_OUTDIRS"]).joinpath(
        "processing_statistics", "plots"
    )
    curr_time = datetime.now().replace(tzinfo=pytz.UTC)
    parser.add_argument(
        "--json-stats-output-directory",
        "-d",
        type=Path,
        required=False,
        default=default_json_stats_dir,
    )
    parser.add_argument(
        "--window-start",
        type=isodate.parse_datetime,
        default=curr_time - timedelta(days=1),
    )
    parser.add_argument(
        "--window-end",
        type=isodate.parse_datetime,
        default=curr_time,
    )
    parser.add_argument(
        "--json-filename-keys", "--keys", "--tags", nargs="+", default=None
    )
    parser.add_argument("--geoips-version", default=gpaths["GEOIPS_VERSION"])
    parser.add_argument("--sector-type", default=None)
    parser.add_argument("--include-checkpoints", action="store_true")
    parser.add_argument("--plot-checkpoint-stats-for-sectors", nargs="+")

    args = parser.parse_args()

    # Start with getting list of JSON files to load:
    input_jsons = get_json_file_lists(
        args.json_stats_output_directory,
        args.geoips_version,
        args.window_start,
        args.window_end,
        args.sector_type,
        args.include_checkpoints,
    )

    # Sort them in to dataframes specific to each source (e.g. abi)
    overall_dframes = load_jsons_into_dataframes_by_source(
        input_jsons["overall_procflow_jsons"], args.json_filename_keys
    )

    created_plots = []
    if input_jsons["checkpoint_jsons"]:
        loaded_checkpoints = load_jsons_into_single_dataframe(
            input_jsons["checkpoint_jsons"]
        ).to_dict("records")
        checkpoint_dframe = create_checkpoint_dataframe(
            loaded_checkpoints, overall_dframes
        )
        sorted_stats = sort_resource_stats(checkpoint_dframe, sort_platform=True)
        for source, platform_dframes in sorted_stats.items():
            for platform, dframe in platform_dframes.items():
                created_plots.append(
                    checkpoint_boxplot(dframe, source=source, platform=platform)
                )
                if args.plot_checkpoint_stats_for_sectors:
                    created_plots.append(
                        checkpoint_boxplot(
                            dframe,
                            source=source,
                            platform=platform,
                            plot_sectors=args.plot_checkpoint_stats_for_sectors,
                        )
                    )

    created_plots.append(
        boxplot(
            overall_dframes,
            stat="Max. Resident Set Size (GB)",
            fontsize=30,
            figsize=(11, 6),
            geoips_vers=args.geoips_version,
            window_start_datetime=args.window_start,
            window_end_datetime=args.window_end,
        )
    )
    created_plots.append(
        boxplot(
            overall_dframes,
            stat="System time",
            fontsize=30,
            figsize=(11, 6),
            geoips_vers=args.geoips_version,
            window_start_datetime=args.window_start,
            window_end_datetime=args.window_end,
        )
    )
    created_plots.append(
        boxplot(
            overall_dframes,
            stat="Total Time",
            fontsize=30,
            figsize=(11, 6),
            geoips_vers=args.geoips_version,
            window_start_datetime=args.window_start,
            window_end_datetime=args.window_end,
        )
    )
    created_plots.append(
        boxplot(
            overall_dframes,
            stat="Number Products",
            fontsize=30,
            figsize=(11, 6),
            geoips_vers=args.geoips_version,
            window_start_datetime=args.window_start,
            window_end_datetime=args.window_end,
        )
    )
    print("Done!")
    print("Full list of created products:\n")
    print("\n".join(created_plots))


if __name__ == "__main__":
    main()
