# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= standard library imports ========================
import os

from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Bool, Int, Float, Enum
from traitsui.api import View, Item, VGroup, HGroup, spring
from traitsui.editors.api import FileEditor
from traitsui.group import Tabbed
from traitsui.item import UItem

# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.tasks.base_preferences_helper import (
    BasePreferencesHelper,
    BaseConsolePreferences,
    BaseConsolePreferencesPane,
)
from pychron.extraction_line import LOG_LEVEL_NAMES
from pychron.paths import paths


class ConsolePreferences(BaseConsolePreferences):
    preferences_path = "pychron.extraction_line.console"


class ConsolePreferencesPane(BaseConsolePreferencesPane):
    model_factory = ConsolePreferences
    label = "Extraction Line"

    def traits_view(self):
        preview = CustomLabel(
            "preview",
            size_name="fontsize",
            color_name="textcolor",
            bgcolor_name="bgcolor",
        )

        v = View(
            VGroup(
                HGroup(UItem("fontsize"), UItem("textcolor"), UItem("bgcolor")),
                preview,
                show_border=True,
                label=self.label,
            )
        )
        return v


class BaseExtractionLinePreferences(BasePreferencesHelper):
    name = "ExtractionLine"
    preferences_path = "pychron.extraction_line"
    id = "pychron.extraction_line.preferences_page"

    use_network = Bool
    inherit_state = Bool
    display_volume = Bool
    volume_key = Str

    gauge_update_period = Float
    gauge_update_enabled = Bool

    pump_update_period = Float
    pump_update_enabled = Bool

    heater_update_period = Float
    heater_update_enabled = Bool

    canvas_path = Str
    canvas_config_path = Str
    valves_path = Str

    logging_level = Enum(LOG_LEVEL_NAMES)


class ExtractionLinePreferences(BaseExtractionLinePreferences):
    use_hardware_update = Bool
    hardware_update_period = Float
    check_master_owner = Bool


class ExtractionLinePreferencesPane(PreferencesPane):
    model_factory = ExtractionLinePreferences
    category = "ExtractionLine"

    def _network_group(self):
        n_grp = VGroup(
            Item(
                "use_network",
                label="Use Network",
                tooltip="Flood the extraction line with the maximum state color",
            ),
            Item(
                "inherit_state",
                label="Inherit State",
                tooltip="Should the valves inherit the maximum state color",
                enabled_when="use_network",
            ),
            VGroup(
                HGroup(
                    Item(
                        "display_volume",
                        label="Display Volume",
                        tooltip="Display the volume for selected section. Hover over section "
                        'and hit the defined volume key (default="v")',
                    ),
                    Item(
                        "volume_key",
                        tooltip="Hit this key to display volume",
                        label="Key",
                        width=-50,
                        enabled_when="display_volume",
                    ),
                    spring,
                ),
                show_border=True,
                label="Volume",
                enabled_when="use_network",
            ),
            show_border=True,
            label="Network",
        )
        return n_grp

    def _get_valve_group(self):
        v_grp = VGroup(
            VGroup(
                Item(
                    "check_master_owner",
                    label="Check Master Ownership",
                    tooltip="Check valve ownership even if this is the master computer",
                ),
                Item("use_hardware_update"),
                Item("hardware_update_period", enabled_when="use_hardware_update"),
                show_border=True,
                label="Update",
            ),
            self._network_group(),
            show_border=True,
            label="Valves",
        )

        return v_grp

    def _get_path_group(self):
        p_grp = VGroup(
            Item(
                "canvas_path",
                editor=FileEditor(
                    root_path=os.path.join(paths.canvas2D_dir, "canvas.xml")
                ),
            ),
            Item("canvas_config_path", editor=FileEditor()),
            Item(
                "valves_path",
                editor=FileEditor(
                    root_path=os.path.join(paths.extraction_line_dir, "valves.xml")
                ),
            ),
            label="Paths",
        )
        return p_grp

    def _get_gauge_group(self):
        g_grp = BorderVGroup(
            Item(
                "gauge_update_enabled",
                label="Use Gauge Update",
                tooltip="Start a timer to periodically update the gauge pressures",
            ),
            Item(
                "gauge_update_period",
                label="Period",
                tooltip="Delay between updates in seconds. ",
                enabled_when="gauge_update_enabled",
            ),
            label="Gauges",
        )

        return g_grp

    def _get_heater_group(self):
        g_grp = BorderVGroup(
            Item(
                "heater_update_enabled",
                label="Use Heater Update",
                tooltip="Start a timer to periodically update the heater temperatures",
            ),
            Item(
                "heater_update_period",
                label="Period",
                tooltip="Delay between updates in seconds. ",
                enabled_when="heater_update_enabled",
            ),
            label="Heaters",
        )

        return g_grp

    def _get_pump_group(self):
        g_grp = BorderVGroup(
            Item(
                "pump_update_enabled",
                label="Use Pump Update",
                tooltip="Start a timer to periodically update the pump parameters",
            ),
            Item(
                "pump_update_period",
                label="Period",
                tooltip="Delay between updates in seconds. ",
                enabled_when="pump_update_enabled",
            ),
            label="Pumps",
        )

        return g_grp

    def _get_tabs(self):
        p_grp = self._get_path_group()
        v_grp = self._get_valve_group()
        d_grp = VGroup(
            self._get_gauge_group(),
            self._get_heater_group(),
            self._get_pump_group(),
            label="Device Managers",
        )
        return p_grp, v_grp, d_grp

    def traits_view(self):
        mgrp = VGroup(Item("logging_level"))
        return View(VGroup(Tabbed(*self._get_tabs()), mgrp))


# ============= EOF =============================================
