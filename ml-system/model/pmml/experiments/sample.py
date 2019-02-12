from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import pandas as pd
from xgboost import XGBClassifier

seed = 123456

iris = datasets.load_iris()
target = 'Species'
features = iris.feature_names
iris_df = pd.DataFrame(iris.data, columns=features)
iris_df[target] = iris.target

X, y = iris_df[features], iris_df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=seed)

pipeline = Pipeline([
    ('scaling', StandardScaler()),
    ('xgb', XGBClassifier(n_estimators=5, seed=seed))
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
y_pred_proba = pipeline.predict_proba(X_test)

import pickle
import numpy as np

d = pickle.dumps(pipeline)
saved_pipeline = pickle.loads(d)
y_pred_saved = saved_pipeline.predict(X_test)
y_pred_proba_saved = saved_pipeline.predict_proba(X_test)

assert np.array_equal(y_pred, y_pred_saved), "Not equal after saved"
assert np.array_equal(y_pred_proba_saved, y_pred_proba), "Not equal after saved"

from nyoka import xgboost_to_pmml
xgboost_to_pmml(saved_pipeline, features, target, "xgb-iris.pmml")

from pypmml import Model
model = Model.fromFile("xgb-iris.pmml")
y_pred_pmml = model.predict(X_test)

assert np.array_equal(y_pred, y_pred_pmml["predicted_Species"]), "Not equal after saved"
