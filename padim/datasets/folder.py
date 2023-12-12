# Copyright 2023 AlphaBetter Corporation. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import logging
import os
from pathlib import Path
from typing import Any

import torch.utils.data
from PIL import Image
from torchvision import transforms
from torchvision.transforms import InterpolationMode

logger = logging.getLogger(__name__)


class FolderDataset(torch.utils.data.Dataset):
    r"""Folder Dataset

    Args:
        root (str | Path): root directory of dataset where directory ``mvtec_anomaly_detection`` exists.
        image_size (int): image size after resizing.
        normalize_mean (list[float]): mean values for normalization.
        normalize_std (list[float]): std values for normalization.

    Examples:
        >>> from padim.datasets import FolderDataset
        >>> from omegaconf import OmegaConf
        >>> transforms_dict_config = OmegaConf.load("configs/transforms.yaml")
        >>> dataset = FolderDataset("./data/imagenet")
        >>> len(dataset)
        209
        >>> image = dataset[0]
        >>> image.shape
        torch.Size([3, 224, 224])
    """

    def __init__(
            self,
            root: str | Path,
            image_size: int = 224,
            normalize_mean: [float, float, float] = None,
            normalize_std: [float, float, float] = None,
    ) -> None:
        super().__init__()
        if normalize_mean is None:
            normalize_mean = [0.485, 0.456, 0.406]
        if normalize_std is None:
            normalize_std = [0.229, 0.224, 0.225]

        self.root = root
        self.image_size = image_size

        # set transforms
        self.image_transforms = transforms.Compose([
            transforms.Resize((image_size, image_size), InterpolationMode.NEAREST),
            transforms.ToTensor(),
            transforms.Normalize(normalize_mean, normalize_std),
        ])

        # load dataset
        self.images = sorted(os.listdir(self.root))

    def __getitem__(self, index: int) -> tuple[Any, Any, Any, str]:
        image_path = os.path.join(self.root, self.images[index])
        image = Image.open(image_path).convert("RGB")
        image = self.image_transforms(image)

        return image, image, image, self.images[index]

    def __len__(self):
        return len(self.images)
