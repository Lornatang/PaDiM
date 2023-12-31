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
"""
ImageNet Dataset `https://www.image-net.org/`
"""
import logging
import os
from pathlib import Path
from typing import Any

import albumentations as A
import cv2
import torch.utils.data

logger = logging.getLogger(__name__)


class FolderDataset(torch.utils.data.Dataset):
    r"""Folder Dataset

    Args:
        root (str | Path): root directory of dataset where directory ``mvtec_anomaly_detection`` exists.
        image_transform (A.Compose, optional): image transform. Defaults to None.
        mask_size (tuple[int, int], optional): mask size after resizing. Defaults to (224, 224).

    Examples:
        >>> from padim.datasets import FolderDataset
        >>> from omegaconf import OmegaConf
        >>> from padim.utils import get_data_transform
        >>> config = OmegaConf.load("configs/folder.yaml")
        >>> config = OmegaConf.create(config)
        >>> image_transforms = A.Compose(get_data_transform(config.DATASETS.TRANSFORMS))
        >>> mask_size = (224, 224)
        >>> dataset = FolderDataset("data/folder/train", image_transforms, mask_size, True)
        >>> sample = dataset[0]
        >>> image, target, mask, image_path = sample["image"], sample["target"], sample["mask"], sample["image_path"]
        >>> print(image.shape, target, mask.shape, image_path)
        torch.Size([3, 224, 224]) 0 torch.Size([1, 224, 224]) ./data/folder/train/good/000.png
    """

    def __init__(
            self,
            root: str | Path,
            image_transform: A.Compose = None,
            mask_size: tuple[int, int] = (224, 224),
            train: bool = True,
    ) -> None:
        super().__init__()
        if isinstance(root, str):
            root = Path(root)
        self.image_transforms = image_transform
        self.mask_size = mask_size

        # load dataset
        if train:
            pattern = "good/*"
        else:
            pattern = "*/*"
        self.image_path_list = list(root.glob(pattern))

    def __getitem__(self, index: int) -> dict[str, str | None | Any]:
        image_path = str(self.image_path_list[index])

        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = image.astype("float32") / 255.0
        image = self.image_transforms(image=image)["image"]

        target_type = 0
        mask = torch.zeros([1, self.mask_size[0], self.mask_size[1]])

        return {"image": image,
                "target": target_type,
                "mask": mask,
                "image_path": image_path}

    def __len__(self):
        return len(self.image_path_list)
