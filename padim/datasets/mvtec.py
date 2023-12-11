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

import cv2
import torch
from omegaconf import DictConfig
from torch.utils.data import Dataset

from padim.utils.download import DownloadInfo
from padim.utils.transform import get_data_transforms

logger = logging.getLogger(__name__)

DOWNLOAD_INFO = DownloadInfo(
    name="mvtec",
    url="https://www.mydrive.ch/shares/38536/3830184030e49fe74747669442f0f282/download/420938113-1629952094/mvtec_anomaly_detection.tar.xz",
    hash="eefca59f2cede9c3fc5b6befbfec275e",
)

CLASS_NAMES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper",
]


class MVTecDataset(Dataset):
    r"""MVTec Dataset

    Args:
        config (DictConfig): configuration
        is_train (bool, optional): if True, load train dataset, else load test dataset. Defaults to True.

    Examples:
        >>> from padim.datasets import MVTecDataset
        >>> from omegaconf import OmegaConf
        >>> config = OmegaConf.load("config.yaml")
        >>> config = OmegaConf.create(config)
        >>> dataset = MVTecDataset(config, is_train=True)
        >>> image, target, mask = dataset[0]
        >>> image.shape
        torch.Size([3, 256, 256])
        >>> target
        0
        >>> mask.shape
        torch.Size([1, 256, 256])
    """
    def __init__(
            self,
            config: DictConfig,
            is_train: bool = True,
    ) -> None:
        super().__init__()
        self.root = str(config.ROOT)
        self.category = str(config.CATEGORY)
        self.is_train = is_train

        # set transforms
        self.transform_image = get_data_transforms(config.TRANSFORMS, mask_mode=False)
        self.transform_mask = get_data_transforms(config.TRANSFORMS, mask_mode=True)
        self.mask_height = config.TRANSFORMS.RESIZE.HEIGHT
        self.mask_width = config.TRANSFORMS.RESIZE.WIDTH

        # load dataset
        self.images, self.targets, self.masks = self.load()

    def load(self):
        phase = "train" if self.is_train else "test"
        images, targets, masks = [], [], []

        images_dir = os.path.join(self.root, self.category, phase)
        gt_dir = os.path.join(self.root, self.category, "ground_truth")

        image_types = sorted(os.listdir(images_dir))
        for image_type in image_types:
            # load images
            image_type_dir = os.path.join(images_dir, image_type)
            if not os.path.isdir(image_type_dir):
                continue
            image_file_path_list = sorted([os.path.join(image_type_dir, f) for f in os.listdir(image_type_dir) if f.endswith(".png")])
            images.extend(image_file_path_list)

            # load gt labels
            if image_type == "good":
                targets.extend([0] * len(image_file_path_list))
                masks.extend([None] * len(image_file_path_list))
            else:
                targets.extend([1] * len(image_file_path_list))
                gt_type_dir = os.path.join(gt_dir, image_type)
                image_file_name_list = [os.path.splitext(os.path.basename(f))[0] for f in image_file_path_list]
                gt_file_path_list = [os.path.join(gt_type_dir, image_fname + "_mask.png") for image_fname in image_file_name_list]
                masks.extend(gt_file_path_list)

        assert len(images) == len(targets), "number of x and y should be same"

        return list(images), list(targets), list(masks)

    def __getitem__(self, index: int) -> tuple:
        image = cv2.imread(self.images[index])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.transform_image(image=image)

        target = self.targets[index]

        if self.targets[index] == 0:
            mask = torch.zeros([1, self.mask_height, self.mask_width])
        else:
            mask = cv2.imread(self.masks[index])
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
            mask = self.transform_mask(image=mask)

        return image, target, mask

    def __len__(self):
        return len(self.images)
