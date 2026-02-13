# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Databases interface class."""

from geoips.base_class_plugins import BaseDatabasePlugin
from geoips.interfaces.base import BaseClassInterface


class DatabasesInterface(BaseClassInterface):
    """Interface for database table writers/quieriers."""

    name = "databases"
    plugin_class = BaseDatabasePlugin

    required_args = {
        "xarray_area_def_to_table": ["product_filename", "xarray_obj", "area_def"],
        "xarray_dict_to_table": ["product_filename", "xarray_dict"],
        "memusg_stats_to_table": [],
        "overpass_dict_to_postgres_table": [
            "schema_name",
            "table_name",
            "overpass_dict",
        ],
        "overpass_dict_to_sqlite_table": ["overpass_dict", "dbname"],
        "schema_table_sector_opasses_to_postgres_table": [
            "schema_name",
            "table_name",
            "sector_name",
            "sat_overpasses",
        ],
        "schema_table_storm_opasses_to_postgres_table": [
            "schema_name",
            "table_name",
            "storm_id",
            "storm_time",
            "satellite_overpasses",
        ],
        "storm_opasses_db_to_postgres_table": [
            "storm_id",
            "storm_time",
            "satellite_overpasses",
            "dbname",
        ],
        "query_overpass_table": ["window_start", "window_end"],
        "query_product_table": ["window_start", "window_end"],
    }
    required_kwargs = {
        "xarray_area_def_to_table": [],
        "xarray_dict_to_table": [],
        "memusg_stats_to_table": [],
        "overpass_dict_to_postgres_table": [],
        "overpass_dict_to_sqlite_table": [],
        "storm_opasses_db_to_postgres_table": [],
        "schema_table_storm_opasses_to_postgres_table": [],
        "schema_table_sector_opasses_to_postgres_table": [],
        "query_overpass_table": [],
        "query_product_table": [],
    }


databases = DatabasesInterface()
