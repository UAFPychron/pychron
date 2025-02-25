# ===============================================================================
# Copyright 2019 ross
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
from pychron.options.options import SubOptions, TitleSubOptions, GroupSubOptions
from pychron.options.views.isochron_views import (
    InverseIsochronMainOptions,
    InverseIsochronAppearance,
    InverseIsochronCalculationOptions,
)
from pychron.options.views.spectrum_views import (
    SpectrumMainOptions,
    SpectrumAppearance,
    DisplaySubOptions,
    CalculationSubOptions,
)

from traitsui.api import VGroup, Item

from pychron.pychron_constants import GROUPS


class LayoutSubOptions(SubOptions):
    def traits_view(self):
        g = VGroup(Item("orientation_layout"))
        return self._make_view(g)


# class TitleSubOptions(SubOptions):
#     pass

VIEWS = {
    "main": SpectrumMainOptions,
    "spectrum": SpectrumMainOptions,
    "isochron": InverseIsochronMainOptions,
    "display(spec.)": DisplaySubOptions,
    "calculations(spec.)": CalculationSubOptions,
    "appearance(spec.)": SpectrumAppearance,
    "appearance(iso.)": InverseIsochronAppearance,
    "calculations(iso.)": InverseIsochronCalculationOptions,
    "layout": LayoutSubOptions,
    "title": TitleSubOptions,
    GROUPS.lower(): GroupSubOptions,
}
# ============= EOF =============================================
