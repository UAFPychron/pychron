# ===============================================================================
# Copyright 2021 ross
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
import time
from threading import Thread
from traits.api import List, Float, Event, Bool, Property
from traitsui.api import View, Item, UItem, ButtonEditor, InstanceEditor, ListEditor

from pychron.extraction_line.device_manager import DeviceManager
from pychron.managers.manager import Manager


class HeaterManager(DeviceManager):
    device_view_name = "heater_view"


# ============= EOF =============================================
