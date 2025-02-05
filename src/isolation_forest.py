# AnomalyDetection is a free software developed by Tommaso Fontana for Würth Phoenix S.r.l. under GPL-2 License.

import sys
import random
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest as IF

from logger import logger
from ml_template import ML_template

class IsolationForest(ML_template):

    def __init__(self, model_settings, read_settings):
        logger.info("Using model [IsolationForest]")
        self.path  = model_settings.pop("model_file_format").format(**read_settings)
        logger.info("The model path is [{path}]".format(path=self.path))
        self.model_settings = model_settings
        self.models = {}

    def needs_training(self):
        return True

    def _stack_data(self, values):
        return np.column_stack(list(values.values()))

    def train(self, data, settings):
        self._check_data(data, settings["min_n_of_data_points"])
        logger.info("Training the Models")

        for selector, values in data.items():
            self.models[selector] = IF(**self.model_settings)
            self.models[selector].fit(self._stack_data(values))

        logger.info("Models Trained")

    
    def set_seed(self, seed):
        logger.info(f"Setting the seed to [{seed}]")
        random.seed(seed)
        np.random.seed(seed)

    def analyze(self, data, settings):
        self._check_data(data, settings["min_n_of_data_points"])
        logger.info("Setting the seed for reproducibility porpouses.")
        self.set_seed(settings["seed"])
        logger.info("Predicting the average anomalies scores for the data")
        output = data.copy()

        for selector, values in data.items():
            output[selector]["score"] = self.models[selector].decision_function(self._stack_data(values)).reshape(-1, 1)

        return output

    def classify(self, data, classification_settings):
        logger.info("Classifying the scores")
        for selector, points in data.items():
            values = points["score"]
            # Calc the two thresholds for normals and anomalies
            normals   = np.nanquantile(values, self.settings["normal_percentage"])
            logger.info(f"The normal quantile for the selector [{selector}] is [{normals}]")
            anomalies = np.nanquantile(values, self.settings["anomaly_percentage"])
            logger.info(f"The anomaly quantile for the selector [{selector}] is [{anomalies}]")
            # By default values are possible anomalies
            result = np.ones_like(values)
            result[values < normals] = 0
            result[values > anomalies] = 2

            if classification_settings["ignore_lower_values"]:
                logger.info("The analysis will defaults to normal points under the mean")
                # If the flag is set then the value below the mean are normal by defaults
                result[np.all(self._stack_data(points) < self.models[selector]["loc"], axis=1)] = 0
                
            data[selector]["class"] = result
        
        return data
