import optuna
import pickle
import numpy as np
import pandas as pd
import lightgbm as lgb
from IPython.utils import io
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.metrics import fbeta_score


def contains_smaller_value(lst, threshold):
    for x in lst:
        if x <= threshold:
            return True
    return False

def get_label(row, threshold):
    if row['reputationScore'] >= threshold:
        return 1
    else: 
        return 0
    
def norm_value(df):
    for col in df.columns:
        if col.split('_')[0]=='totalInUSD':
            df[f'{col}'] = df[f'{col}']/df['totalUSDTransfer']
    return df

def get_label_future(row, elite_id):
    if row['_id'] in elite_id:
        return 1
    else: 
        return 0

def keys_with_condition(dictionary, condition):
    return [key for key, value in dictionary.items() if condition(value)]


def LGBMTraining(X_train, y_train, X_test, y_test, num_leaves,feature_fraction,max_depth,sampling_strategy, k):
    smote = SMOTE(sampling_strategy=sampling_strategy, k_neighbors=k)
    params = {
    'objective': 'multiclass',
    'metric': 'multi_logloss',
    'num_classes': 2,  # Number of classes in your classification problem
    'num_leaves': num_leaves,  #31
    'learning_rate': 0.05,
    'feature_fraction': feature_fraction,  #0.9
    'max_depth': max_depth
#   'device':'gpu'
    }
    with io.capture_output() as captured:
        X_trainn, X_val, y_trainn, y_val = train_test_split(X_train, y_train, test_size=0.05, random_state=42)
        X_train_res, y_train_res = smote.fit_resample(X_trainn, y_trainn.ravel())
        train_data = lgb.Dataset(X_train_res, label=pd.DataFrame(y_train_res), params={'verbose': -1})
        test_data = lgb.Dataset(pd.DataFrame(X_val), label=pd.DataFrame(y_val), params={'verbose': -1}, reference=train_data)
        num_round = 100  # Number of boosting rounds
        evals={}
        bst = lgb.train(params,train_data, num_round, valid_sets=[train_data, test_data],callbacks = [lgb.record_evaluation(evals)])
        y_pred = bst.predict(X_test, num_iteration=bst.best_iteration)
        y_pred_class = np.argmax(y_pred, axis=1)
        F1_score = fbeta_score(y_test, y_pred_class, pos_label = True,beta=1)
    return bst, F1_score,evals

def get_LGBMscore(trial):
    num_leaves = trial.suggest_int('num_leaves', 160, 300, 10) 
    feature_fraction = trial.suggest_float('feature_fraction', 0.3, 0.9, step=0.1)
    max_depth = trial.suggest_int('max_depth', 35, 55, 1)
    sampling_strategy = trial.suggest_float('sampling_strategy', 0.35, 0.6,step=0.05)
    k = trial.suggest_categorical('k', [2, 3, 5, 7, 9])
    models, F1_scores, evals = LGBMTraining(X_train, y_train, X_test, y_test, num_leaves,feature_fraction,max_depth, sampling_strategy, k)
    
    
    with open("data/aave/training_process/modeling_1711929600/models_{}.pickle".format(trial.number), "wb") as fout:
        pickle.dump(models, fout)
        
    with open("data/aave/training_process/modeling_1711929600/evals_{}.pickle".format(trial.number), "wb") as fout:
        pickle.dump(evals, fout)
    return np.mean(F1_scores)

def optimization(n):
    # define custom values to search on:
    study = optuna.create_study(study_name="Optimization over given values",direction='maximize')
    study.optimize(get_LGBMscore, n_trials = n)
    best_params = study.best_params
    best_metric = study.best_value
    return best_params, best_metric, study


