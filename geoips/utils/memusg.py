# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for tracking and monitoring memory and resource usage."""
# Python standard Libraries
# Python standard Libraries
import logging
import socket
import os
import resource
import threading
from ast import literal_eval
from sys import argv
from datetime import datetime, timezone
import platform

# Installed libraires
from collections import defaultdict
import pandas as pd

# Geoips libraries
from geoips.filenames.base_paths import PATHS as gpaths

from geoips.utils.context_managers import import_optional_dependencies

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import psutil


def print_mem_usage(logstr="", verbose=False):
    """Print memory usage to LOG.info.

    * By default include psutil output.
    * If verbose is True, include output from both psutil and resource packages.
    """
    # If psutil / socket / resource are not imported, do not fail
    usage_dict = {}
    try:
        vmem_percent = psutil.virtual_memory().percent
        LOG.info(
            "virtual perc: %s on %s %s",
            str(vmem_percent),
            str(socket.gethostname()),
            logstr,
        )
        swap_percent = psutil.swap_memory().percent
        LOG.info(
            "swap perc:    %s on %s %s",
            str(swap_percent),
            str(socket.gethostname()),
            logstr,
        )
    except NameError as resp:
        vmem_percent = swap_percent = "nan"
        LOG.info(
            "%s: psutil or socket not defined, no percent memusg output", str(resp)
        )
    try:
        highest = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        LOG.info(
            "highest:      %s on %s %s",
            str(highest),
            str(socket.gethostname()),
            logstr,
        )
    except NameError as resp:
        highest = "nan"
        LOG.info(
            "%s: resource or socket not defined, no highest memusg output", str(resp)
        )

    if verbose:
        usage_dict = print_resource_usage(logstr)
    usage_dict["memusg_virtual"] = vmem_percent
    usage_dict["memusg_swap"] = swap_percent
    usage_dict["memusg_highest"] = highest
    return usage_dict


def print_resource_usage(logstr=""):
    """Print verbose resource usage, using "resource" package."""
    usage_dict = {}
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        for name, desc in [
            ("ru_utime", "RESOURCE " + logstr + " User time"),
            ("ru_stime", "RESOURCE " + logstr + " System time"),
            ("ru_maxrss", "RESOURCE " + logstr + " Max. Resident Set Size"),
            ("ru_ixrss", "RESOURCE " + logstr + " Shared Memory Size"),
            ("ru_idrss", "RESOURCE " + logstr + " Unshared Memory Size"),
            ("ru_isrss", "RESOURCE " + logstr + " Stack Size"),
            ("ru_inblock", "RESOURCE " + logstr + " Block inputs"),
            ("ru_oublock", "RESOURCE " + logstr + " Block outputs"),
        ]:
            LOG.info("%-25s (%-10s) = %s", desc, name, getattr(usage, name))
            usage_dict[name] = getattr(usage, name)
    except NameError:
        LOG.info("resource not defined")
    return usage_dict


class PidLog:
    """Track a PID and all children.

    * Requires psutil and threading
    """

    def __init__(self, inpid, logstr=""):

        self.ps_parent = psutil.Process(pid=inpid)
        self.own_pid = os.getpid()
        self.logstr = logstr
        self.pid_bool = self.ps_parent.is_running()
        # allows for other process to run
        self.track_pid_thread = threading.Thread(
            target=self.track_pids, name="TrackPID", daemon=True
        )
        self.track_pid_thread.start()

    def track_pids(self):
        """Track pids and create a dict of values."""
        self.usage_dict = {
            "overall": {
                "cpu_percent": [],
                "thread_count": [],
                "unique_set_size": [],
                "res_set_size": [],
                "utc_datetime": [],
            },
            "checkpoints": {},
        }

        if platform.system() == "Linux":
            self.usage_dict["overall"]["cpu_count"] = []

        while self.pid_bool:

            ps_child = self.ps_parent.children(recursive=True)

            # filter out own pid and any children spawned
            try:
                all_pids = [self.ps_parent] + [
                    i
                    for i in ps_child
                    for j in i.parents()
                    if i.pid != self.own_pid and j.pid != self.own_pid
                ]
            except psutil.NoSuchProcess as resp:
                LOG.warning(f"Process no longer exists, skipping, {resp}")
                continue

            tmp_cpu, cpu_per, thrd_cnt, uss_tmp, rss_tmp = [], 0, 0, 0, 0

            for i in all_pids:
                try:
                    # CPU usage with oneshot doesn't work

                    with i.oneshot():
                        # cpu_num only works for Linux, FreeBSD, SunOS
                        if platform.system() == "Linux":
                            tmp_cpu += [i.cpu_num()]
                        thrd_cnt += i.num_threads()
                        tmp_mem = i.memory_full_info()
                        uss_tmp += tmp_mem.uss
                        rss_tmp += tmp_mem.rss
                    # might want average over all cpus?
                    cpu_per += i.cpu_percent(interval=0.1)
                except psutil.Error:
                    # pid expired quickly, need to remove invalid values
                    continue

            dtime = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            self.usage_dict["overall"]["cpu_percent"].append(cpu_per)
            if platform.system() == "Linux":
                self.usage_dict["overall"]["cpu_count"].append(len(set(tmp_cpu)))
            self.usage_dict["overall"]["thread_count"].append(thrd_cnt)
            self.usage_dict["overall"]["unique_set_size"].append(uss_tmp)
            self.usage_dict["overall"]["res_set_size"].append(rss_tmp)
            self.usage_dict["overall"]["utc_datetime"].append(dtime)

        return

    def print_mem_usg(self, logstr="", verbose=False):
        """Print verbose resouce usage."""
        usage_dict = {}
        vmem_percent = psutil.virtual_memory().percent
        LOG.info(
            "virtual perc: %s on %s %s",
            str(vmem_percent),
            str(socket.gethostname()),
            self.logstr,
        )
        #

        swap_percent = psutil.swap_memory().percent
        LOG.info(
            "swap perc:    %s on %s %s",
            str(swap_percent),
            str(socket.gethostname()),
            self.logstr,
        )

        if len(self.usage_dict["overall"]["unique_set_size"]) > 0:
            ram_usg = max(self.usage_dict["overall"]["unique_set_size"])
            highest = max(self.usage_dict["overall"]["res_set_size"])
        else:
            ram_usg = 0
            highest = 0

        LOG.info(
            "highest ram:    %s on %s %s",
            str(ram_usg),
            str(socket.gethostname()),
            self.logstr,
        )

        LOG.info(
            "highest rss:      %s on %s %s",
            str(highest),
            str(socket.gethostname()),
            self.logstr,
        )

        if verbose:
            usage_dict = self.print_resource_usage()

        usage_dict["memusg_virtual"] = vmem_percent
        usage_dict["memusg_swap"] = swap_percent
        usage_dict["memusg_highest"] = highest

        return usage_dict

    def track_resource_usage(
        self,
        logstr="",
        verbose=False,
        key=None,
        show_log=True,
        checkpoint=False,
        increment_key=True,
    ):
        """Record resouce usage for a given processing marker in GeoIPS.

        Parameters
        ----------
        logstr : str, optional
            String to include at the start of the log message, by default ""
        verbose : bool, optional
            Print the full resource usage statistics dict to stdout, by default False
        key : str, optional
            Unique name of marker to record statistics, by default None
            A marker can be categorized as part of a group when using ":" in the
            marker name (e.g "FOO: BAR"). This is used in the checkpoint_usage_stats
            method, where markers will have a "checkpoint_group" key in their resource
            usage statistics dictionary holding the name of the group.
            (e.g. stats["BAR"]["checkpoint_group"] == "FOO")
        show_log : bool, optional
            Use LOG.info to print the current memory usage, by default True
        checkpoint : bool, optional
            Re-use a marker key to record more detailed profiling of resource usage in
            terms of both timing and maximum memory usage, by default False
        increment_key : bool, optional
            Append the number of times marker is re-used to the key, by default True
            Marker names should be unique, and should at minimum hold the start/end
            resource usage for the marker. If a marker is re-used and increment_key is
            False, a KeyError is raised. If increment_key is True and the marker has
            both start/end stats, a number is automatically appended to the key name.
            This number represents how many times a marker has been re-used. For
            example: "FOO: BAR" -> "FOO: BAR(1)": -> "FOO: BAR(2)"
            (Note: "FOO: BAR(2)" is only created if "FOO: BAR(1)" has start/end stats)

        Returns
        -------
        dict
            Resource usage statistics for checkpoint

        Raises
        ------
        KeyError
            Duplicate key is discovered and increment_key is False
        """
        usage_dict = {}
        vmem_percent = psutil.virtual_memory().percent
        swap_percent = psutil.swap_memory().percent

        overall_usage_dict = self.usage_dict["overall"]
        if len(overall_usage_dict["unique_set_size"]) > 0:
            # Take the latest value under the tracked resource dict - this might be
            # a problematic approach...
            last_stat = {x: y[-1] for x, y in overall_usage_dict.items()}
            dt = datetime.strptime(last_stat["utc_datetime"], "%Y%m%d_%H%M%S_%f")
        else:
            last_stat = {x: 0 for x in overall_usage_dict.keys()}
            dt = datetime.now(timezone.utc)
            last_stat["utc_datetime"] = dt.strftime("%Y%m%d_%H%M%S_%f")

        gran_usg_dict = self.usage_dict["checkpoints"]
        if key not in gran_usg_dict:
            LOG.info(f"New tracker {key}")
            gran_usg_dict[key] = defaultdict(list)
            elapsed_time = 0
            total_runtime = 0
        elif len(overall_usage_dict["utc_datetime"]) == 0:
            LOG.warning(
                f"UNEXPECTED ERROR IN RESOURCE TRACKING {key}: "
                "No overall usage defined, starting over with tracking :shrug:\n"
                f"gran_usg_dict[{key}] = {gran_usg_dict.get(key)}\n"
                f"overall_usage_dict: \n{overall_usage_dict}"
            )
            gran_usg_dict[key] = defaultdict(list)
            elapsed_time = 0
            total_runtime = 0
        else:
            start_dt = datetime.strptime(
                overall_usage_dict["utc_datetime"][0], "%Y%m%d_%H%M%S_%f"
            )
            prior_dt = datetime.strptime(
                gran_usg_dict[key]["utc_datetime"][-1], "%Y%m%d_%H%M%S_%f"
            )
            total_runtime = (dt - start_dt).total_seconds()
            elapsed_time = (dt - prior_dt).total_seconds()

        # Check if this key is being re-used. Arrays should at maximum length of 2:
        if (
            len(gran_usg_dict[key]["unique_set_size"]) == 2
            and checkpoint is False
            and increment_key is False
        ):
            raise KeyError(f"Usage key '{key}' already exists and is of length 2")
        elif len(gran_usg_dict[key]["unique_set_size"]) == 2 and increment_key:
            orig_key = key
            inc_keys = [x for x in gran_usg_dict.keys() if key in x]
            for inc_num, ikey in enumerate(inc_keys, 1):
                if gran_usg_dict[ikey]["unique_set_size"] == 2:
                    continue
                elif len(gran_usg_dict[ikey]["unique_set_size"]) < 2:
                    key = ikey
                    break
            else:
                key = f"{key}({inc_num})"
            if key not in gran_usg_dict:
                gran_usg_dict[key] = defaultdict(list)
                elapsed_time = 0
                total_runtime = 0
            LOG.warning(
                "Usage key '%s' already exists and is of length 2. increment_keys "
                "is True, so will instead use '%s'.",
                orig_key,
                key,
            )

        if checkpoint and len(gran_usg_dict[key]["unique_set_size"]) == 0:
            LOG.warning(
                "Flagged %s as checkpoint, but found no stats. Likely this is not "
                "a true checkpoint. Considering this the start of resource tracking.",
                key,
            )
            checkpoint = False

        if checkpoint:
            # Use sub-checkpoints to track highest memory usage
            if "subcheck" not in gran_usg_dict[key]:
                gran_usg_dict[key]["subcheck"] = defaultdict(list)
            for stat, val in last_stat.items():
                gran_usg_dict[key]["subcheck"][stat].append(val)
            return

        # Track the resource statistics for this checkpoint
        for stat, val in last_stat.items():
            gran_usg_dict[key][stat].append(val)
        # Also track the elapsed time of the checkpoint, and the total run time
        gran_usg_dict[key]["elapsed_time"].append(elapsed_time)
        gran_usg_dict[key]["total_runtime"].append(total_runtime)
        gran_usg_dict[key]["datetime"].append(dt)
        # Grab the highest value for all statistics
        if "subcheck" in gran_usg_dict[key]:
            all_stats = {
                stat: gran_usg_dict[key][stat] + gran_usg_dict[key]["subcheck"][stat]
                for stat in overall_usage_dict.keys()
            }
        else:
            all_stats = gran_usg_dict[key]
        max_stat = {
            stat: max(vals)
            for stat, vals in all_stats.items()
            if "datetime" not in stat and "max_" not in stat
        }

        for stat, val in max_stat.items():
            gran_usg_dict[key][f"max_{stat}"] = val

        ram_usg = max_stat["unique_set_size"]
        highest = max_stat["res_set_size"]
        if show_log and not checkpoint:
            LOG.info(
                "%s: virtual perc: %s on %s %s",
                key,
                str(vmem_percent),
                str(socket.gethostname()),
                self.logstr,
            )
            LOG.info(
                "%s: swap perc:    %s on %s %s",
                key,
                str(swap_percent),
                str(socket.gethostname()),
                self.logstr,
            )
            LOG.info(
                "%s: highest ram:    %s on %s %s",
                key,
                str(ram_usg),
                str(socket.gethostname()),
                self.logstr,
            )
            LOG.info(
                "%s: highest rss:      %s on %s %s",
                key,
                str(highest),
                str(socket.gethostname()),
                self.logstr,
            )
            LOG.info(
                "%s: elapsed runtime (seconds):    %s on %s %s",
                key,
                str(elapsed_time),
                str(socket.gethostname()),
                self.logstr,
            )

            if verbose:
                usage_dict = self.print_resource_usage()

        usage_dict["memusg_virtual"] = vmem_percent
        usage_dict["memusg_swap"] = swap_percent
        usage_dict["memusg_highest"] = highest
        usage_dict["elapsed_runtime"] = elapsed_time
        usage_dict["total_procflow_runtime"] = total_runtime

        return usage_dict

    def checkpoint_usage_stats(self):
        """Return organized dictionary of stats from track_resource_usage.

        Returns
        -------
        dict
            Resource usage statistics for markers/checkpoints recorded by the
            track_resource_usage method. Dictionary is ordered by the markers passed to
            track_resource_usage. Each key in the return dictionary will hold a
            dictionary of the resource usage statistics. If a group is specified in the
            marker name (e.g. "FOO: BAR"), the return dictionary will have a "BAR" key,
            and will have a "checkpoint_group" key in the corresponding resource usage
            dictionary with a value of "FOO".
        """
        checkpoint_usage_stats = {}
        exclude_stats = [
            "max_elapsed_time",
            "max_total_runtime",
            "utc_datetime",
            "subcheck",
        ]
        for check_name, check_stats in self.usage_dict["checkpoints"].items():
            checkpoint_usage_stats[check_name] = {}
            if ": " in check_name:
                group = check_name.split(": ")[0]
                checkpoint_usage_stats[check_name]["checkpoint_group"] = group
            for stat, val in check_stats.items():
                if stat in exclude_stats:
                    continue
                elif stat in ["elapsed_time"]:
                    checkpoint_usage_stats[check_name][stat] = val[-1]
                elif "max_" in stat:
                    checkpoint_usage_stats[check_name][stat] = val
                else:
                    if stat == "datetime":
                        stat = f"checkpoint_{stat}"
                    checkpoint_usage_stats[check_name][f"{stat}_start"] = val[0]
                    checkpoint_usage_stats[check_name][f"{stat}_stop"] = val[-1]
        return checkpoint_usage_stats

    def print_resource_usage(self):
        """Print verbose resource usage, using "resource" package."""
        usage_dict = {}
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            for name, desc in [
                ("ru_utime", "RESOURCE " + self.logstr + " User time"),
                ("ru_stime", "RESOURCE " + self.logstr + " System time"),
                ("ru_maxrss", "RESOURCE " + self.logstr + " Max. Resident Set Size"),
                ("ru_ixrss", "RESOURCE " + self.logstr + " Shared Memory Size"),
                ("ru_idrss", "RESOURCE " + self.logstr + " Unshared Memory Size"),
                ("ru_isrss", "RESOURCE " + self.logstr + " Stack Size"),
                ("ru_inblock", "RESOURCE " + self.logstr + " Block inputs"),
                ("ru_oublock", "RESOURCE " + self.logstr + " Block outputs"),
            ]:
                LOG.info("%-25s (%-10s) = %s", desc, name, getattr(usage, name))
                usage_dict[name] = getattr(usage, name)
        except NameError:
            LOG.info("resource not defined")
        usage_dict["ru_cpuusg"] = max(self.usage_dict["overall"]["cpu_percent"])  # [-1]
        usage_dict["ru_threads"] = max(self.usage_dict["overall"]["thread_count"])
        if platform.system() == "Linux":
            usage_dict["ru_cpucnt"] = max(self.usage_dict["overall"]["cpu_count"])
        usage_dict["ru_uss"] = self.usage_dict["overall"]["unique_set_size"][-1]
        usage_dict["ru_maxuss"] = max(self.usage_dict["overall"]["unique_set_size"])
        LOG.info(
            "RESOURCE "
            + self.logstr
            + " Max. User Set Size (RAM) = "
            + str(max(self.usage_dict["overall"]["unique_set_size"]))
        )
        LOG.info(
            "RESOURCE "
            + self.logstr
            + " Max. CPU % Usage = "
            + str(max(self.usage_dict["overall"]["cpu_percent"]))
        )
        return usage_dict

    def save_exit(self):
        """Exit the thread cleanly."""
        LOG.info("Stopping resource tracking.")
        self.pid_bool = False
        self.track_pid_thread.join()

    def save_csv(self):
        """Save a csv file to output."""
        usg_dict = {
            "Time [UTC]": self.usage_dict["overall"]["utc_datetime"],
            "CPU Percent": self.usage_dict["overall"]["cpu_percent"],
            "Thread Count": self.usage_dict["overall"]["thread_count"],
            "USS [RAM bytes]": self.usage_dict["overall"]["unique_set_size"],
            "RSS [bytes]": self.usage_dict["overall"]["res_set_size"],
        }
        if platform.system() == "Linux":
            usg_dict["CPU Count"] = self.usage_dict["overall"]["cpu_count"]
        df = pd.DataFrame(usg_dict)

        outdir = os.path.join(gpaths["GEOIPS_OUTDIRS"], "memory_logs")
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        outname = "geoips_memtrack_p{}.csv".format(self.ps_parent.pid)
        outpath = outdir + "/" + outname
        LOG.info("Saving csv memory track to {}".format(outpath))

        df.to_csv(outpath, index=False)


def single_track_pid(procpid):
    """Output a snapshot of a pid usage on server.

    * Requires an input pid.
    """
    ps_parent = psutil.Process(pid=procpid)
    own_pid = os.getpid()
    ps_child = ps_parent.children(recursive=True)

    # filter out own pid and any children spawned
    all_pids = [ps_parent] + [
        i
        for i in ps_child
        for j in i.parents()
        if i.pid != own_pid and j.pid != own_pid
    ]

    tmp_cpu, cpu_per, thrd_cnt, uss_tmp, rss_tmp = [], 0, 0, 0, 0

    for i in all_pids:
        try:
            # CPU usage with oneshot doesn't work

            with i.oneshot():
                # cpu_num only works for Linux, FreeBSD, SunOS
                if platform.system() == "Linux":
                    tmp_cpu += [i.cpu_num()]
                thrd_cnt += i.num_threads()
                tmp_mem = i.memory_full_info()
                uss_tmp += tmp_mem.uss
                rss_tmp += tmp_mem.rss
            # might want average over all cpus?
            cpu_per += i.cpu_percent(interval=0.1)
        except psutil.Error:
            # pid expired quickly, need to remove invalid values
            continue

    if platform.system() == "Linux":
        # outputs CPU percent, CPU count, Thread count, USS, RSS
        print(
            "{}, {}, {}, {}, {}".format(
                cpu_per, len(set(tmp_cpu)), thrd_cnt, uss_tmp, rss_tmp
            )
        )
    else:
        # outputs CPU percent, Thread count, USS, RSS
        print("{}, {}, {}, {}".format(cpu_per, thrd_cnt, uss_tmp, rss_tmp))


if __name__ == "__main__":
    """Track a PID given from command line."""
    pid_track = single_track_pid(literal_eval(argv[1]))
