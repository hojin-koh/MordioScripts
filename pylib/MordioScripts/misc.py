#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020-2024, Hojin Koh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Misc tools common to all scripts

# Override some defaults in tqdm: dirty hack
def overrideTqdmDefaults():
    import tqdm.asyncio
    import tqdm
    from functools import partialmethod
    try:
        fpShow = open('/dev/fd/5', 'w', encoding='utf-8')
        tqdm.asyncio.tqdm.__init__ = partialmethod(tqdm.asyncio.tqdm.__init__, file=fpShow)
        tqdm.tqdm.__init__ = partialmethod(tqdm.tqdm.__init__, file=fpShow)
    except Exception:
        pass
    finally:
        tqdm.asyncio.tqdm.__init__ = partialmethod(tqdm.asyncio.tqdm.__init__, smoothing=0, mininterval=1, dynamic_ncols=True, colour='blue')
        tqdm.tqdm.__init__ = partialmethod(tqdm.tqdm.__init__, smoothing=0, mininterval=1, dynamic_ncols=True, colour='blue')

