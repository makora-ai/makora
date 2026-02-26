# Copyright 2026 Makora Inc.
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


from enum import Enum

from pydantic import BaseModel

from .openapi import KernelLanguage


class TargetDevice(Enum):
    H100 = "H100"
    H200 = "H200"
    B200 = "B200"
    L40S = "L40S"
    MI300X = "MI300X"
    ADRENO_830 = "Adreno 830"
    ADRENO_750 = "Adreno 750"
    HEXAGON_V79 = "Hexagon v79"
    HEXAGON_V75 = "Hexagon v75"

    def get_default_language(self) -> KernelLanguage:
        match self:
            case TargetDevice.H100 | TargetDevice.H200 | TargetDevice.B200 | TargetDevice.L40S:
                return KernelLanguage.cuda
            case TargetDevice.MI300X:
                return KernelLanguage.hip
            case TargetDevice.ADRENO_750 | TargetDevice.ADRENO_830:
                return KernelLanguage.opencl
            case TargetDevice.HEXAGON_V75 | TargetDevice.HEXAGON_V79:
                return KernelLanguage.ripple

    def supports_language(self, lang: KernelLanguage) -> bool:
        match self:
            case TargetDevice.H100 | TargetDevice.H200 | TargetDevice.B200 | TargetDevice.L40S:
                return lang in {
                    KernelLanguage.cuda,
                    KernelLanguage.triton,
                }

            case TargetDevice.MI300X:
                return lang in {
                    KernelLanguage.triton,
                    KernelLanguage.hip,
                }

            case TargetDevice.ADRENO_750 | TargetDevice.ADRENO_830:
                return lang == KernelLanguage.opencl

            case TargetDevice.HEXAGON_V75 | TargetDevice.HEXAGON_V79:
                return lang == KernelLanguage.ripple

    def to_api_device(self) -> str:
        match self:
            case TargetDevice.H100:
                return "nvidia:h100"
            case TargetDevice.H200:
                return "nvidia:h200"
            case TargetDevice.B200:
                return "nvidia:b200"
            case TargetDevice.L40S:
                return "nvidia:L40S"
            case TargetDevice.MI300X:
                return "amd:mi300x"
            case TargetDevice.ADRENO_830:
                return "qualcomm:snapdragon_8_elite_gpu"
            case TargetDevice.ADRENO_750:
                return "qualcomm:snapdragon_8_gen_3_gpu"
            case TargetDevice.HEXAGON_V79:
                return "qualcomm:snapdragon_8_elite_npu"
            case TargetDevice.HEXAGON_V75:
                return "qualcomm:snapdragon_8_gen_3_npu"

    @classmethod
    def from_api_name(cls, name: str) -> "TargetDevice":
        match name:
            case "nvidia:h100":
                return cls.H100
            case "nvidia:h200":
                return cls.H200
            case "nvidia:b200":
                return cls.B200
            case "nvidia:L40S":
                return cls.L40S
            case "amd:mi300x":
                return cls.MI300X
            case "qualcomm:snapdragon_8_elite_gpu":
                return cls.ADRENO_830
            case "qualcomm:snapdragon_8_gen_3_gpu":
                return cls.ADRENO_750
            case "qualcomm:snapdragon_8_elite_npu":
                return cls.HEXAGON_V79
            case "qualcomm:snapdragon_8_gen_3_npu":
                return cls.HEXAGON_V75
            case _:
                raise NotImplementedError()


class SessionExtra(BaseModel):
    speedup: float | None = None
    device: TargetDevice | None = None
