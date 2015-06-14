# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================

from pyface.tasks.action.schema import SToolBar, SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter
from traits.api import Instance, Bool, on_trait_change
# ============= standard library imports ========================
from itertools import groupby
import os
# ============= local library imports  ==========================
from pychron.dvc.dvc import experiment_has_staged, push_experiments
from pychron.globals import globalv
from pychron.paths import paths
from pychron.pipeline.engine import PipelineEngine
from pychron.pipeline.state import EngineState
from pychron.pipeline.tasks.actions import RunAction, SavePipelineTemplateAction, ResumeAction, ResetAction, \
    ConfigureRecallAction, GitRollbackAction, TagAction
from pychron.pipeline.tasks.panes import PipelinePane, AnalysesPane
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.processing.plot.editors.figure_editor import FigureEditor

DEBUG = True


class DataMenu(SMenu):
    id = 'data.menu'
    name = 'Data'


class PipelineTask(BaseBrowserTask):
    name = 'Pipeline Processing'
    engine = Instance(PipelineEngine, ())
    tool_bars = [SToolBar(RunAction(),
                          ResumeAction(),
                          ResetAction(),
                          ConfigureRecallAction(),
                          SavePipelineTemplateAction()),
                 SToolBar(GitRollbackAction()),
                 SToolBar(TagAction())
                 ]
    state = Instance(EngineState)
    resume_enabled = Bool(False)
    run_enabled = Bool(True)
    # reset_enabled = Bool(False)
    run_to = None
    # def switch_to_browser(self):
    #     self._activate_task('pychron.browser.task')

    modified = False
    dbmodified = False
    projects = None

    def run(self):
        self._run_pipeline()

    def activated(self):
        super(PipelineTask, self).activated()

        self.engine.dvc = self.dvc
        self.engine.browser_model = self.browser_model

        self.engine.add_data()

    def _debug(self):
        pass
        # self.engine.add_data()
        self.engine.select_default()
        self.engine.set_template('ideogram')
        # self.engine.set_template('blanks')
        # self.engine.add_is
        # self.engine.add_grouping(run=False)
        # self.engine.add_test_filter()
        # self.engine.add_ideogram(run=False)
        # self.engine.add_series(run=False)

        # self.engine.add_test_filter()
        # self.engine.add_ideogram()
        # self.engine.add_pdf_figure_node()
        # self.engine.add_spectrum()

        # self.run()

    def prepare_destroy(self):
        pass

    def create_dock_panes(self):
        panes = [PipelinePane(model=self.engine),
                 AnalysesPane(model=self.engine)]
        return panes

    # toolbar actions
    def git_rollback(self):
        # select experiment
        expid = 'Cather_McIntosh'

        self.dvc.rollback_experiment_repo(expid)

    def reset(self):
        self.state = None
        self.engine.reset()

    def save_pipeline_template(self):
        # path = self.save_file_dialog()
        # path = '/Users/ross/Sandbox/template.yaml'
        path = os.path.join(paths.pipeline_template_dir, 'test.yaml')
        if path:
            self.engine.save_pipeline_template(path)

    # action handlers
    def set_ideogram_template(self):
        self.engine.set_template('ideogram')

    def set_spectrum_template(self):
        self.engine.set_template('spectrum')

    def set_isochron_template(self):
        self.engine.set_template('isochron')

    # private
    def _close_editor(self, editor):
        for e in self.editor_area.editors:
            if e.name == editor.name:
                self.close_editor(e)
                break

    def _run_pipeline(self):
        self.debug('run pipeline')
        if self.state:
            self.debug('using previous state')
            state = self.state
        else:
            state = EngineState()

        if not self.engine.run(state, self.run_to):
            self.state = state
            self._toggle_run(True)
        else:
            self._toggle_run(False)
            self.state = None

        self.close_all()
        for editor in state.editors:
            self._close_editor(editor)
            self._open_editor(editor)

        self.engine.selected = None
        self.engine.update_needed = True

        if state.dbmodified:
            self.dbmodified = True

    def _toggle_run(self, v):
        self.resume_enabled = v
        self.run_enabled = not v

    def _default_layout_default(self):
        return TaskLayout(left=Splitter(PaneItem('pychron.pipeline.pane',
                                                 width=200),
                                        PaneItem('pychron.pipeline.analyses',
                                                 width=200)))

    def _extra_actions_default(self):
        sas = (('MenuBar/data.menu', RunAction, {}),)
        return [self._sa_factory(path, factory, **kw) for path, factory, kw in sas]

    def _sa_factory(self, path, factory, **kw):
        return SchemaAddition(path=path, factory=factory, **kw)

    # handlers
    @on_trait_change('engine:unknowns[]')
    def _handle_unknowns(self, name, old, new):
        if self.active_editor:
            if not new:
                self.active_editor.set_items(self.engine.unknowns)
                self.active_editor.refresh_needed = True
        self.engine.update_detectors()

    @on_trait_change('engine:references[]')
    def _handle_references(self, name, old, new):
        if self.active_editor:
            # only update if deletion
            if not new:
                self.active_editor.set_references(self.engine.references)
                self.active_editor.refresh_needed = True
        self.engine.update_detectors()

    def _active_editor_changed(self, new):
        if new:
            self.engine.select_node_by_editor(new)

    @on_trait_change('engine:unknowns:[tag_event, invalid_event]')
    def _handle_analysis_tagging(self, name, new):
        if name == 'tag_event':
            self.set_tag(items=new)
        elif name == 'invalid_event':
            from pychron.processing.tagging.analysis_tags import Tag

            self.set_tag(tag=Tag(name='invalid'), items=new, warn=True)

    @on_trait_change('engine:run_needed')
    def _handle_run_needed(self, new):
        self.debug('run needed for {}'.format(new))
        self.run()

    @on_trait_change('engine:recall_analyses_needed')
    def _handle_recall(self, new):
        self.recall(new)

    def _prompt_for_save(self):
        ret = True
        ps = self.engine.get_experiment_ids()
        print ps
        if ps:
            changed = experiment_has_staged(ps)
            if changed:
                m = 'You have changes to analyses. Would you like to share them?'
                ret = self._handle_prompt_for_save(m, 'Share Changes')
                if ret == 'save':
                    push_experiments(ps)

        return ret

    def _opened_hook(self):
        super(PipelineTask, self)._opened_hook()
        if globalv.pipeline_debug:
            self._debug()

    def set_tag(self, tag=None, items=None, use_filter=True, warn=False):
        """
            set tag for either
            analyses selected in unknowns pane
            or
            analyses selected in figure e.g temp_status!=0

        """
        if items is None:
            items = self._get_selection()
            if not items:
                if warn:
                    self.warning_dialog('No analyses selected to Tag')
                    return

        if items:
            name = None
            if tag is None:
                a = self._get_tagname(items)
                if a:
                    tag, items, use_filter = a
                    if tag:
                        name = tag.name
            else:
                name = tag.name

            # set tags for items
            if name and items:
                dvc = self.dvc
                db = dvc.db
                key = lambda x: x.experiment_id

                for expid, ans in groupby(sorted(items, key=key), key=key):
                    # repo = dvc.get_experiment_repo(expid)
                    changed = False
                    # with dvc.git_session_ctx(expid, 'Updated tags'):
                    with db.session_ctx():
                        for it in ans:
                            self.debug('setting {} tag= {}'.format(it.record_id, name))
                            db.set_analysis_tag(it.uuid, name)

                            it.set_tag(tag)
                            if dvc.update_tag(it):
                                changed = True
                    if changed:
                        dvc.experiment_commit(expid, 'Updated tags')

                if use_filter:
                    for e in self.editor_area.editors:
                        if isinstance(e, FigureEditor):
                            e.set_items([ai for ai in e.analyses if ai.tag != 'invalid'])
                #
                if self.active_editor:
                    self.active_editor.refresh_needed = True

                self.browser_model.analysis_table.refresh_needed = True
                self.engine.refresh_table_needed = True
        else:
            # edit tags
            self._get_tagname([])

    def _get_selection(self):
        items = None
        unks = self.engine.unknowns
        if self.engine.unknowns:
            if not items:
                items = self.engine.selected_unknowns

            if not items:
                items = [i for i in unks if i.is_temp_omitted()]
                self.debug('Temp omitted analyses {}'.format(len(items)))

        if not items:
            items = self.browser_model.analysis_table.selected
        return items

    def _get_tagname(self, items):
        from pychron.processing.tagging.analysis_tags import AnalysisTagModel
        from pychron.processing.tagging.views import AnalysisTagView

        # tv = self._tag_table_view
        # if not tv:
        tv = AnalysisTagView(model=AnalysisTagModel())

        db = self.dvc.db
        with db.session_ctx():
            # tv = TagTableView(items=items)
            tv.model.db = db
            tv.model.items = items
            tv.model.load()

        info = tv.edit_traits()
        if info.result:
            tag = tv.model.selected
            # self._tag_table_view = tv
            return tag, tv.model.items, tv.model.use_filter

    def _get_dr_tagname(self, items):
        from pychron.processing.tagging.data_reduction_tags import DataReductionTagModel
        from pychron.processing.tagging.views import DataReductionTagView

        tv = DataReductionTagView(model=DataReductionTagModel(items=items))
        info = tv.edit_traits()
        if info.result:
            return tv.model

# ============= EOF =============================================
