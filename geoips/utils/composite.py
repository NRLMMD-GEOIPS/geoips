# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for swath compositing in GeoIPS."""

import isodate
from datetime import timedelta

from geoips.interfaces import databases


def find_preproc_alg_files(
    product_time,
    composite_window,
    sector_name,
    product,
    sensor,
    platform,
    file_format="netcdf",
    product_db=False,
    db_query_plugin=None,
    db_schemas=None,
    db_tables=None,
):
    """Find pre-processed algorithm files that were saved to disk.

    Parameters
    ----------
    product_time : datetime.datetime
        Product time
    composite_window : str
        How far back to search for pre-processed files.
        Window needs to be specified in iso8601 duration format (e.g. PT4H)
    sector_name : str
        Name of sector to composite
    product : str
        Name of product to composite
    sensor : str
        Name of sensor to composite
    platform : str
        Name of platform to composite
    file_format : str, optional
        Pre-processed file format, by default "netcdf"
    product_db : bool, optional
        Use product database to find any pre-processed file, by default False
    db_query_plugin : str, optional
        Name of product database query plugin, by default None
    db_schemas : list, optional
        Names of postgres schema to query, by default None
    db_tables : list, optional
        Names of table to query under schema, by default None

    Returns
    -------
    list
        List of pre-processed algorithm files
    """
    product_time_start = product_time - isodate.parse_duration(composite_window)
    product_time_end = product_time - timedelta(seconds=1)
    if isinstance(db_schemas, str):
        db_schemas = [db_schemas]
    if isinstance(db_tables, str):
        db_tables = [db_tables]
    if file_format == "netcdf":
        preproc_files = find_preproc_alg_netcdfs(
            product_time_start,
            product_time_end,
            sector_name,
            product,
            sensor,
            platform,
            product_db=product_db,
            postgres_query_plugin=db_query_plugin,
            postgres_schemas=db_schemas,
            postgres_tables=db_tables,
        )
    return preproc_files


def find_preproc_alg_netcdfs(
    product_time_start,
    product_time_end,
    sector_name,
    product,
    sensor,
    platform,
    product_db=False,
    postgres_query_plugin=None,
    postgres_schemas=None,
    postgres_tables=None,
):
    """Find pre-processed algorithm netCDF files that were saved to disk.

    Parameters
    ----------
    product_time_start : datetime.datetime
        Earliest product time to search for valid files
    product_time_start : datetime.datetime
     Latest product time to search for valid files
    sector_name : str
        Name of sector to composite
    product : str
        Name of product to composite
    sensor : str
        Name of sensor to composite
    platform : str
        Name of platform to composite
    file_format : str, optional
        Pre-processed file format, by default "netcdf"
    product_db : bool, optional
        Use product database to find any pre-processed file, by default False
    db_query_plugin : str, optional
        Name of product database query plugin, by default None
    db_schemas : list, optional
        Names of postgres schema to query, by default None
    db_tables : list, optional
        Names of table to query under schema, by default None

    Returns
    -------
    list
        List of pre-processed netCDF algorithm files
    """
    if product_db:
        query_plugin = databases.get_plugin(postgres_query_plugin)
        search_schema = []
        for schema in postgres_schemas:
            for ptime in [product_time_start, product_time_end]:
                schema_name = ptime.strftime(schema)
                if schema_name not in search_schema:
                    search_schema.append(schema_name)
        query_out = query_plugin(
            product_time_start,
            product_time_end,
            sector_name,
            product,
            sensor,
            platform,
            search_schema,
            file_type="nc",
            postgres_tables=postgres_tables,
        )
    nc_files = []
    for product in query_out["products"]:
        nc_file = product["productPath"]
        if nc_file not in nc_files:
            nc_files.append(nc_file)
    return sorted(nc_files)
