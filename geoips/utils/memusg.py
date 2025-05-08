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
from datetime import datetime
import platform

# Installed libraires
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
            "cpu_percent": [],
            "thread_count": [],
            "unique_set_size": [],
            "res_set_size": [],
            "utc_datetime": [],
        }
        if platform.system() == "Linux":
            self.usage_dict["cpu_count"] = []

        while self.pid_bool:

            ps_child = self.ps_parent.children(recursive=True)

            # filter out own pid and any children spawned
            all_pids = [self.ps_parent] + [
                i
                for i in ps_child
                for j in i.parents()
                if i.pid != self.own_pid and j.pid != self.own_pid
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

            dtime = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            self.usage_dict["cpu_percent"].append(cpu_per)
            if platform.system() == "Linux":
                self.usage_dict["cpu_count"].append(len(set(tmp_cpu)))
            self.usage_dict["thread_count"].append(thrd_cnt)
            self.usage_dict["unique_set_size"].append(uss_tmp)
            self.usage_dict["res_set_size"].append(rss_tmp)
            self.usage_dict["utc_datetime"].append(dtime)

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

        if len(self.usage_dict["unique_set_size"]) > 0:
            ram_usg = max(self.usage_dict["unique_set_size"])
            highest = max(self.usage_dict["res_set_size"])
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
        usage_dict["ru_cpuusg"] = max(self.usage_dict["cpu_percent"])  # [-1]
        usage_dict["ru_threads"] = max(self.usage_dict["thread_count"])
        if platform.system() == "Linux":
            usage_dict["ru_cpucnt"] = max(self.usage_dict["cpu_count"])
        usage_dict["ru_uss"] = self.usage_dict["unique_set_size"][-1]
        usage_dict["ru_maxuss"] = max(self.usage_dict["unique_set_size"])
        LOG.info(
            "RESOURCE "
            + self.logstr
            + " Max. User Set Size (RAM) = "
            + str(max(self.usage_dict["unique_set_size"]))
        )
        LOG.info(
            "RESOURCE "
            + self.logstr
            + " Max. CPU % Usage = "
            + str(max(self.usage_dict["cpu_percent"]))
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
            "Time [UTC]": self.usage_dict["utc_datetime"],
            "CPU Percent": self.usage_dict["cpu_percent"],
            "Thread Count": self.usage_dict["thread_count"],
            "USS [RAM bytes]": self.usage_dict["unique_set_size"],
            "RSS [bytes]": self.usage_dict["res_set_size"],
        }
        if platform.system() == "Linux":
            usg_dict["CPU Count"] = self.usage_dict["cpu_count"]
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
