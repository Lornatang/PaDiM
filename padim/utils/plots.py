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
import os
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from skimage import morphology
from skimage.segmentation import mark_boundaries

from .ops import de_normalization

__all__ = [
    "plot_score_map", "plot_fig",
]


def plot_score_map(image: np.ndarray, scores: np.ndarray, vmin: float, vmax: float, save_file_path: str | Path):
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    image = de_normalization(image)
    heat_map = scores * 255
    heat_map = heat_map.transpose(1, 2, 0).astype(np.uint8)
    fig_image, ax_image = plt.subplots(1, 2, figsize=(4, 3))
    fig_image.subplots_adjust(right=0.9)
    for ax_i in ax_image:
        ax_i.axes.xaxis.set_visible(False)
        ax_i.axes.yaxis.set_visible(False)
    ax_image[0].imshow(image)
    ax_image[0].title.set_text("Image")
    ax_image[1].imshow(image, cmap="gray", interpolation="none")
    ax_image[1].imshow(heat_map, cmap="jet", alpha=0.5, interpolation="none", norm=norm)
    ax_image[1].title.set_text("Predicted heat map")

    # Add normal score
    pred_score = scores.reshape(-1).max()
    text = f"score:{pred_score * 100:.1f}%"
    ax_image[1].text(0.95, 0.95,
                     text,
                     transform=ax_image[1].transAxes,
                     fontsize=10,
                     verticalalignment="top",
                     horizontalalignment="right",
                     color="white",
                     bbox=dict(facecolor="red", alpha=0.5))

    fig_image.savefig(save_file_path, dpi=100)
    plt.close()


def plot_fig(test_image, scores, gts, threshold, save_dir):
    num = len(scores)
    vmax = scores.max() * 255.
    vmin = scores.min() * 255.
    for i in range(num):
        image = test_image[i]
        image = de_normalization(image)
        gt = gts[i].transpose(1, 2, 0).squeeze()
        heat_map = scores[i] * 255
        heat_map = heat_map.transpose(1, 2, 0).astype(np.uint8)
        mask = scores[i].squeeze()
        mask[mask > threshold] = 1
        mask[mask <= threshold] = 0
        kernel = morphology.disk(4)
        mask = morphology.opening(mask, kernel)
        mask *= 255
        vis_image = mark_boundaries(image, mask, color=(1, 0, 0), mode="thick")
        fig_image, ax_image = plt.subplots(1, 5, figsize=(12, 3))
        fig_image.subplots_adjust(right=0.9)
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        for ax_i in ax_image:
            ax_i.axes.xaxis.set_visible(False)
            ax_i.axes.yaxis.set_visible(False)
        ax_image[0].imshow(image)
        ax_image[0].title.set_text("Image")
        ax_image[1].imshow(gt, cmap="gray")
        ax_image[1].title.set_text("GroundTruth")
        ax = ax_image[2].imshow(heat_map, cmap="jet", norm=norm)
        ax_image[2].imshow(image, cmap="gray", interpolation="none")
        ax_image[2].imshow(heat_map, cmap="jet", alpha=0.5, interpolation="none")
        ax_image[2].title.set_text("Predicted heat map")
        ax_image[3].imshow(mask, cmap="gray")
        ax_image[3].title.set_text("Predicted mask")
        ax_image[4].imshow(vis_image)
        ax_image[4].title.set_text("Segmentation result")
        left = 0.92
        bottom = 0.15
        width = 0.015
        height = 1 - 2 * bottom
        rect = [left, bottom, width, height]
        cbar_ax = fig_image.add_axes(rect)
        cb = plt.colorbar(ax, shrink=0.6, cax=cbar_ax, fraction=0.046)
        cb.ax.tick_params(labelsize=8)
        font = {
            "family": "serif",
            "color": "black",
            "weight": "normal",
            "size": 8,
        }
        cb.set_label("Anomaly Score", fontdict=font)

        fig_image.savefig(os.path.join(save_dir, "{}".format(i)), dpi=100)
        plt.close()
