# ===============================================================================
# Copyright 2020 ross
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
from traits.api import Instance, Button, Property, Color

from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.ui.preference_binding import bind_preference
from pychron.envisage.browser.advanced_filter_view import AdvancedFilterView
from pychron.envisage.browser.analysis_table import AnalysisTable
from pychron.envisage.browser.browser_model import BrowserModel
from pychron.envisage.browser.recall_editor import RecallEditor
from pychron.envisage.browser.view import BrowserView


class AnalysisBrowserModel(BrowserModel):
    table = Instance(AnalysisTable)
    advanced_filter = Instance(AdvancedFilterView, ())
    browser_view = Instance(BrowserView)
    recall_editor = Instance(RecallEditor)

    load_recent_button = Button
    # toggle_view = Button
    graphical_filter_button = Button
    find_references_button = Button
    advanced_filter_button = Button
    add_analysis_group_button = Button

    find_references_enabled = Property(depends_on="table:analyses[]")

    def add_analysis_set(self):
        self.table.add_analysis_set()

    def dump(self):
        # self.time_view_model.dump_filter()
        self.table.dump()
        super(AnalysisBrowserModel, self).dump()

    def _get_find_references_enabled(self):
        return bool(self.table.analyses)

    def _advanced_filter_button_fired(self):
        self.debug("advanced filter")
        # self.warning_dialog('Advanced filtering currently disabled')
        attrs = self.dvc.get_search_attributes()
        if attrs:
            attrs = sort_isotopes(list({a[0].split("_")[0] for a in attrs}))

        m = self.advanced_filter
        m.attributes = attrs
        m.demo()
        info = m.edit_traits(kind="livemodal")
        if info.result:
            uuids = None
            at = self.table
            if not m.apply_to_current_selection and not m.apply_to_current_samples:
                lns = self.dvc.get_analyses_advanced(m, return_labnumbers=True)
                sams = self._load_sample_record_views(lns)
                self.samples = sams
                self.osamples = sams
            elif m.apply_to_current_selection:
                ans = self.table.get_selected_analyses()
                if ans:
                    uuids = [ai.uuid for ai in ans]

            identifiers = None
            if m.apply_to_current_samples:
                identifiers = [si.identifier for si in self.samples]

            ans = self.dvc.get_analyses_advanced(
                m,
                uuids=uuids,
                identifiers=identifiers,
                include_invalid=not m.omit_invalid,
                limit=m.limit,
            )
            if m.apply_to_current_selection and not ans:
                self.warning_dialog("No analyses match criteria")
                return

            ans = self._make_records(ans)
            self.table.set_analyses(ans)

    def _add_analysis_group_button_fired(self):
        ans = self.table.get_selected_analyses()
        if ans:
            self.add_analysis_group(ans)

    def _find_references_button_fired(self):
        self.debug("find references button fired")
        if self.sample_view_active:
            self._find_references_hook()

    def _load_recent_button_fired(self):
        self.debug("load recent button fired")
        self._load_recent()

    def _table_default(self):
        at = AnalysisTable(dvc=self.dvc)

        prefid = "pychron.browser"
        bind_preference(at, "max_history", "{}.max_history".format(prefid))

        adapter = at.tabular_adapter
        bind_preference(
            adapter, "use_analysis_colors", "{}.use_analysis_colors".format(prefid)
        )

        from pychron.experiment.utilities.identifier import (
            ANALYSIS_MAPPING_UNDERSCORE_KEY,
        )

        for analysis_type in ANALYSIS_MAPPING_UNDERSCORE_KEY.keys():
            key = "{}_color".format(analysis_type)
            if not hasattr(adapter, key):
                adapter.add_trait(key, Color)
            bind_preference(adapter, key, "{}.{}_color".format(prefid, analysis_type))

        return at


# ============= EOF =============================================
