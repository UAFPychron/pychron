# ===============================================================================
# Copyright 2016 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= standard library imports ========================
import glob
import os
from datetime import datetime
from math import isnan

from git import Repo, GitCommandError
from traits.api import Str, Bool, HasTraits
from uncertainties import nominal_value, std_dev

from pychron import json
from pychron.dvc import analysis_path, repository_path
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.pychron_constants import SAMPLE_METADATA


def repository_has_staged(ps, remote="origin", branch=None):
    if not hasattr(ps, "__iter__"):
        ps = (ps,)

    changed = []
    # repo = GitRepoManager()

    for p in ps:
        pp = repository_path(p)
        repo = Repo(pp)
        if branch is None:
            branch = repo.active_branch

        try:
            if repo.git.log("{}/{}..HEAD".format(remote, branch), "--oneline"):
                changed.append(p)
        except GitCommandError:
            if branch == "master":
                try:
                    if repo.git.log("{}/{}..HEAD".format(remote, "main"), "--oneline"):
                        changed.append(p)
                except GitCommandError:
                    pass

    return changed


def push_repositories(ps, host=None, remote="origin", branch=None, quiet=True):
    for p in ps:
        pp = repository_path(p)

        repo = GitRepoManager()
        repo.open_repo(pp)

        if host is not None:
            remote = host.default_remote_name

        if branch is None:
            branch = repo.active_repo.active_branch

        if not branch:
            branch = "main"

        if repo.smart_pull(remote=remote, branch=branch, quiet=quiet):
            repo.push(remote=remote, branch=branch)


def reviewed(items):
    return any((i for i in items if i.status))


def is_blank_reviewed(obj, date):
    return make_rsd_items(obj, date, "Bk")


def is_icfactors_reviewed(obj, date):
    return make_rsd_items(obj, date, "IC")


def is_intercepts_reviewed(obj, date):
    return make_rsd_items(obj, date, "Iso Evo")


def make_rsd_items(obj, date, tag):
    items = [
        RSDItem(
            process="{} {}".format(k, tag), date=date, status=iso.get("reviewed", False)
        )
        for k, iso in obj.items()
    ]
    return items


class RSDItem(HasTraits):
    process = Str
    status = Bool
    date = Str


def get_review_status(record):
    ms = 0
    ritems = []
    root = repository_path(record.repository_identifier)
    if os.path.isdir(root):
        repo = Repo(root)
        for m, func in (
            ("blanks", is_blank_reviewed),
            ("intercepts", is_intercepts_reviewed),
            ("icfactors", is_icfactors_reviewed),
        ):
            p = analysis_path(record, record.repository_identifier, modifier=m)
            if os.path.isfile(p):
                with open(p, "r") as rfile:
                    obj = json.load(rfile)
                    date = repo.git.log("-1", "--format=%cd", p)
                    items = func(obj, date)
                    if items:
                        if reviewed(items):
                            ms += 1
                        ritems.extend(items)

        # setattr(record, '{}_review_status'.format(m), (reviewed, date))
    record.review_items = ritems
    ret = "Intermediate"  # intermediate
    if not ms:
        ret = "Default"  # default
    elif ms == 3:
        ret = "All"  # all

    record.review_status = ret


def find_interpreted_age_path(idn, repositories, prefixlen=3):
    prefix = idn[:prefixlen]
    suffix = "{}*.ia.json".format(idn[prefixlen:])
    # ret = []
    # for e in repositories:
    #     pathname = os.path.join(paths.repository_dataset_dir,
    #                             e, prefix, 'ia', suffix)
    #     ps = glob.glob(pathname)
    #     if ps:
    #         ret.extend(ps)

    ret = [
        p
        for repo in repositories
        for p in glob.glob(repository_path(repo, prefix, "ia", suffix))
    ]
    print(prefix, ret)
    return ret


class GitSessionCTX(object):
    def __init__(self, parent, repository_identifier, message):
        self._parent = parent
        self._repository_id = repository_identifier
        self._message = message
        self._parent.get_repository(repository_identifier)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._parent.is_dirty():
                self._parent.repository_commit(self._repository_id, self._message)


def make_interpreted_age_dict(ia):
    def ia_dict(keys):
        print(keys)
        return {attr: getattr(ia, attr) for attr in keys}

    # make general
    d = ia_dict(("name", "uuid"))

    # make analyses
    def analysis_factory(x):
        return dict(
            uuid=x.uuid,
            rundate=x.rundate.isoformat(),
            record_id=x.record_id,
            extract_value=x.extract_value,
            age=x.age,
            age_err=x.age_err,
            age_err_wo_j=x.age_err_wo_j,
            age_units=x.arar_constants.age_units,
            radiogenic_yield=nominal_value(x.radiogenic_yield),
            radiogenic_yield_err=std_dev(x.radiogenic_yield),
            kca=float(nominal_value(x.kca)),
            kca_err=float(std_dev(x.kca)),
            kcl=float(nominal_value(x.kcl)),
            kcl_err=float(std_dev(x.kcl)),
            tag=x.tag,
            plateau_step=ia.get_is_plateau_step(x),
            baseline_corrected_intercepts=x.baseline_corrected_intercepts_to_dict(),
            blanks=x.blanks_to_dict(),
            icfactors=x.icfactors_to_dict(),
            ic_corrected_values=x.ic_corrected_values_to_dict(),
            interference_corrected_values=x.interference_corrected_values_to_dict(),
        )

    d["analyses"] = [analysis_factory(xi) for xi in ia.analyses]

    # make sample metadata
    d["sample_metadata"] = ia_dict(SAMPLE_METADATA)

    # make preferred
    pf = ia_dict(
        (
            "nanalyses",
            "include_j_error_in_mean",
            "include_j_error_in_plateau",
            "include_j_position_error",
        )
    )

    a = ia.get_preferred_age()
    mswd = ia.get_preferred_mswd()
    pf.update(
        {
            "age": float(nominal_value(a)),
            "age_err": float(std_dev(a)),
            "display_age_units": ia.age_units,
            "preferred_kinds": ia.preferred_values_to_dict(),
            "mswd": float(0 if isnan(mswd) else mswd),
            "arar_constants": ia.arar_constants.to_dict(),
            "ages": ia.ages(),
        }
    )
    d["preferred"] = pf

    d["collection_metadata"] = {
        "instrument": ia.mass_spectrometer,
        "technique": "Ar/Ar",
    }
    d["session_metadata"] = {"date": datetime.now().isoformat()}
    return d


# ============= EOF =============================================
