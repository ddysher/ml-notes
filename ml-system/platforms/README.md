<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Platforms (OSS)](#platforms-oss)
  - [comparison](#comparison)
- [Platform (Commercial)](#platform-commercial)
  - [algorithmia](#algorithmia)
  - [dataiku](#dataiku)
  - [datarobot](#datarobot)
  - [datmo](#datmo)
  - [domino](#domino)
  - [h2o](#h2o)
  - [modelarts](#modelarts)
  - [rapidminer](#rapidminer)
  - [r2.ai](#r2ai)
  - [wandb](#wandb)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Platforms (OSS)

## comparison

*Date: 07/07/2018*

**Scope**

- ffdl: only training (can use seldon for serving)
- pipelineai: [continously] training, serving
- riseml: only training
- seldon: only serving

**Build Image**

- ffdl: training image contains framework library and custom scripts: `load.sh`, `train.sh`, `store.sh`
- pipelineai: pass arguments to cli, which then replaces placeholders in pre-built dockerfile
  template with the arguments.
- riseml: a custom python script, using string concatenation to build docker image; the script
  itself is built inside a docker image.
- seldon: recommend s2i from redhat, but also provide its own wrapper.

**Logging**

- ffdl: logging sidecar & elasticsearch. while the learning job is running, a process runs as a
  sidecar to extract the training data from the learner, and then pushes that data into the TDS,
  which pushes the data into ElasticSearch.
- riseml: logging sidecar & rabbitmq
- seldon: none

**Monitoring**

- ffdl: sidecar process for each learner (ps, worker) + per job monitoring process
- seldon: none

**Data**

- ffdl: remote storage (upload to s3)
- riseml: multi-access data volume (PV&PVC)
- seldon: none

# Platform (Commercial)

## [algorithmia](https://algorithmia.com)

Algorithmia is a commercial platform for deploying and managing machine learning models:
- deploy autoscaling ml models with serverless, i.e. upload model, write custom deserialization function then deploy
- catalog your ml portfolio, that is, tag, version control AI models and easily search AI models
- AI marketplace to publish, search and run AI algorithms directly in browser
- data management
  - hosted data, AWS, dropbox, etc; for non-hosted data, only connection is given
  - user collections, session collections, permanent collections, and temporary algorithm collections

Relavance: 4

## [dataiku](https://www.dataiku.com/)

A platform for data analysts, engineers, and scientists together.
- Collaborative Data Science
- Code Or Click
- Prepare & Enrich
- Model & Predict
- Deploy & Run

Relavance: 3+

## [datarobot](https://www.datarobot.com)

Automated Machine Learning Platform.
- Ingest your data
- Select the target variable
- Build hundreds of models in one click
- Explore top models and get insights
- Deploy the best model

Relavance: 3+

## [datmo](https://www.datmo.com/)

Workflow tools to help experiment, deploy, and scale models:
- Experiment: `datmo environment setup`, etc
- Deploy: `datmo deploy`, etc
- Scale

Relavance: 3

## [domino](https://www.dominodatalab.com/)

Domino Data Science Platform: Domino provides an open, unified data science platform to build,
validate, deliver, and monitor models at scale. This accelerates research, sparks collaboration,
increases iteration speed, and removes deployment friction to deliver impactful models.

Relavance: 5

## [h2o](https://www.h2o.ai)

H2O driverless AI speeds up data science workflows by automating feature engineering, model tuning,
ensembling and model deployment.

Relavance: 2+

## [modelarts](https://www.huaweicloud.com/product/modelarts.html)

From Huawei, modelarts is a platform for model development, training, deployment, etc

Relavance: 5

## [rapidminer](https://rapidminer.com/)

Platform for Data Preparation, Machine Learning and Model Deployment.
- Studio for visual workflow
- Auto Model for building models (automatic machine learning, automatic feature engineering, etc)
- Turbo Prep for intuitive data prep

Relavance: 2

## [r2.ai](https://r2.ai/)

An AI development and deployment platform built with AutoML, including:
- data quality check
- feature processing
- model building

Relavance: 3+

## [wandb](https://www.wandb.com/)

wandb is a tool/platform for tracking, saving, and reproducing models. A python sdk is required.
- Visualizing results across models
- Visualizing and debugging hardware performance issues
- Automating large-scale hyperparameter search

Relavance: 3
