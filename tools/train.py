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
import argparse
import logging
import warnings

from omegaconf import OmegaConf

from padim.engine import Trainer
from padim.utils.logger import configure_logger
from padim.utils.seed import init_seed

logger = logging.getLogger("padim")


def get_opts() -> argparse.Namespace:
    """Get parser.

    Returns:
        argparse.ArgumentParser: The parser object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config", metavar="FILE", help="Path to config file.")
    parser.add_argument("--log-level", type=str, default="INFO", help="<DEBUG, INFO, WARNING, ERROR>")
    opts = parser.parse_args()

    return opts


def train(args: argparse.Namespace):
    """Train an anomaly model.

    Args:
        args (Namespace): The arguments from the command line.
    """

    configure_logger(level=args.log_level)

    if args.log_level == "ERROR":
        warnings.filterwarnings("ignore")

    config = OmegaConf.load(args.config)
    config = OmegaConf.create(config)

    if config.get("SEED") is not None:
        init_seed(config.SEED)

    trainer = Trainer(config)
    logger.info("Start training the model.")
    trainer.train()


if __name__ == "__main__":
    opts = get_opts()
    train(opts)
