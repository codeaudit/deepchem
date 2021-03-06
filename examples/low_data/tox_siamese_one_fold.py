"""
Train low-data siamese models on Tox21. Test last fold only.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import tempfile
import numpy as np
import deepchem as dc
import tensorflow as tf
from datasets import load_tox21_convmol

# Number of folds for split 
K = 4 
# num positive/negative ligands
n_pos = 1
n_neg = 1
# Set batch sizes for network
test_batch_size = 128
support_batch_size = n_pos + n_neg
nb_epochs = 1
n_train_trials = 2000
n_eval_trials = 20 
n_steps_per_trial = 1
learning_rate = 1e-4
log_every_n_samples = 50
# Number of features on conv-mols
n_feat = 71

tox21_tasks, dataset, transformers = load_tox21_convmol()

# Define metric
metric = dc.metrics.Metric(
    dc.metrics.roc_auc_score, verbosity="high", mode="classification")

task_splitter = dc.splits.TaskSplitter()
fold_datasets = task_splitter.k_fold_split(dataset, K)

train_folds = fold_datasets[:-1] 
train_dataset = dc.splits.merge_fold_datasets(train_folds)
test_dataset = fold_datasets[-1]

# Train support model on train
support_model = dc.nn.SequentialSupportGraph(n_feat)

# Add layers
support_model.add(dc.nn.GraphConv(64, activation='relu'))
support_model.add(dc.nn.GraphPool())
support_model.add(dc.nn.GraphConv(128, activation='relu'))
support_model.add(dc.nn.GraphPool())
support_model.add(dc.nn.GraphConv(64, activation='relu'))
support_model.add(dc.nn.GraphPool())
support_model.add(dc.nn.Dense(128, activation='tanh'))

support_model.add_test(dc.nn.GraphGather(test_batch_size, activation='tanh'))
support_model.add_support(dc.nn.GraphGather(support_batch_size, activation='tanh'))

with tf.Session() as sess:
  model = dc.models.SupportGraphClassifier(
    sess, support_model, test_batch_size=test_batch_size,
    support_batch_size=support_batch_size, learning_rate=learning_rate,
    verbosity="high")

  ############################################################ DEBUG
  print("FIT")
  ############################################################ DEBUG
  model.fit(train_dataset, nb_epochs=nb_epochs,
            n_episodes_per_epoch=n_train_trials,
            n_pos=n_pos, n_neg=n_neg, log_every_n_samples=log_every_n_samples)
  ############################################################ DEBUG
  print("EVAL")
  ############################################################ DEBUG
  scores = model.evaluate(
      test_dataset, metric, n_pos, n_neg, n_trials=n_eval_trials)
  print("Scores on evaluation dataset")
  print(scores)
