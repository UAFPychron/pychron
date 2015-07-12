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
from traits.api import Float
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.abstract_device import AbstractDevice


class LinearAxis(AbstractDevice):
    position = Float

    # def update_position(self):
    #     pass
    #
    # def linear_move(self, v, *args, **kw):
    #     pass
    #
    # def relative_move(self, v, *args, **kw):
    #     pass

# ============= EOF =============================================
