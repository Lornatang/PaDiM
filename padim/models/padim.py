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
import random

import torch
from omegaconf import ListConfig, OmegaConf
from torch import nn, Tensor
from torch.nn import functional as F_torch

from padim.models.module import AnomalyMap, FeatureExtractor, MultiVariateGaussian


class PaDiM(nn.Module):
    r"""Pytorch implementation of PaDiM.

    Args:
        backbone (str): The backbone of the feature extractor.
        return_nodes (list[str]): The nodes to return from the feature extractor.
        pretrained (bool): Whether to use pretrained weights for the feature extractor.
        mask_size (tuple[int, int], optional): The input image size. Default: (224, 224)

    Raises:
        ValueError: If the backbone is not supported.

    Examples:
        >>> import torch
        >>> from padim.models import PaDiM
        >>> model = PaDiM("wide_resnet50_2", ["layer1.2.relu_2", "layer2.3.relu_2", "layer3.3.relu_2"], mask_size=(224, 224), )
        >>> x = torch.rand((32, 3, 224, 224))
        >>> out = model(x)
        >>> out.shape
            torch.Size([32, 550, 56, 56])

    """
    num_features_dict = {
        "resnet18": 100,
        "wide_resnet50_2": 550,
    }
    max_features_dict = {
        "resnet18": 448,
        "wide_resnet50_2": 1792,
    }

    def __init__(
            self,
            backbone: str,
            return_nodes: ListConfig | list[str],
            pretrained: bool = True,
            mask_size: tuple[int, int] = (224, 224)
    ) -> None:
        super().__init__()
        if isinstance(return_nodes, ListConfig):
            return_nodes = OmegaConf.to_container(return_nodes)
        self.return_nodes = return_nodes
        self.feature_extractor = FeatureExtractor(backbone, return_nodes, pretrained)
        self.anomaly_map = AnomalyMap(mask_size)

        self.index: Tensor
        max_features = self.max_features_dict[backbone]
        num_features = self.num_features_dict[backbone]
        self.register_buffer("index", torch.tensor(random.sample(range(0, max_features), num_features)))

        self.multi_variate_gaussian = MultiVariateGaussian(num_features, max_features)

    def forward(self, x: Tensor) -> Tensor:
        with torch.no_grad():
            features = self.feature_extractor(x)
            embeddings = self.generate_embedding(features)

        if self.training:
            return embeddings
        else:
            return self.anomaly_map(embeddings, self.multi_variate_gaussian.mean, self.multi_variate_gaussian.inv_covariance)

    def generate_embedding(self, features: dict[str, Tensor]) -> Tensor:
        """Generate embedding from hierarchical feature map.

        Args:
            features (dict[str, Tensor]): Hierarchical feature map from a CNN (ResNet18 or WideResnet)

        Returns:
            Embedding vector
        """

        embeddings = features[self.return_nodes[0]]
        for layer in self.return_nodes[1:]:
            layer_embedding = features[layer]
            layer_embedding = F_torch.interpolate(layer_embedding, size=embeddings.shape[-2:], mode="nearest")
            embeddings = torch.cat((embeddings, layer_embedding), 1)

        # subsample embeddings
        index = self.index.to(embeddings.device)
        embeddings = torch.index_select(embeddings, 1, index)
        return embeddings
