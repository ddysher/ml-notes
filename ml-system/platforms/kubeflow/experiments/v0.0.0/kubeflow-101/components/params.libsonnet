{
  global: {
    // User-defined global parameters; accessible to all component and environments, Ex:
    // replicas: 4,
  },
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    "kubeflow-core": {
      cloud: "null",
      disks: "null",
      jupyterHubAuthenticator: "null",
      jupyterHubImage: "gcr.io/kubeflow/jupyterhub-k8s:1.0.1",
      jupyterHubServiceType: "ClusterIP",
      name: "kubeflow-core",
      namespace: "null",
      reportUsage: "false",
      tfAmbassadorServiceType: "ClusterIP",
      tfDefaultImage: "null",
      tfJobImage: "gcr.io/kubeflow-images-staging/tf_operator:v20180326-6214e560",
      tfJobUiServiceType: "ClusterIP",
      usageId: "unknown_cluster",
    },
    serveInception: {
      modelPath: "gs://kubeflow-models/inception",
      name: "inception",
    },
    myjob: {
      args: "null",
      image: "gcr.io/tf-on-k8s-dogfood/tf_sample:d4ef871-dirty-991dde4",
      image_gpu: "null",
      name: "myjob",
      namespace: "null",
      num_gpus: 0,
      num_masters: 1,
      num_ps: 0,
      num_workers: 0,
    },
  },
}
