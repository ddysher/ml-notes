{
  global: {},
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    "kubeflow-core": {
      cloud: 'null',
      disks: 'null',
      jupyterHubAuthenticator: 'null',
      jupyterHubImage: 'gcr.io/kubeflow/jupyterhub-k8s:1.0.1',
      jupyterHubServiceType: 'ClusterIP',
      jupyterNotebookPVCMount: 'null',
      name: 'kubeflow-core',
      namespace: 'null',
      reportUsage: 'false',
      tfAmbassadorServiceType: 'ClusterIP',
      tfDefaultImage: 'null',
      tfJobImage: 'gcr.io/kubeflow-images-public/tf_operator:v20180329-a7511ff',
      tfJobUiServiceType: 'ClusterIP',
      usageId: 'unknown_cluster',
    },
    "kubeflow-argo": {
      imageTag: 'latest',
      name: 'kubeflow-argo',
      namespace: 'null',
    },
    "my-benchmark": {
      config_args: '--config-file=/kubebench/config/job-config.yaml',
      config_image: 'gcr.io/xyhuang-kubeflow/kubebench-configurator:v20180522-1',
      name: 'job-config',
      namespace: 'kubeflow',
      pvc_mount: '/kubebench',
      pvc_name: 'kubebench-pvc',
      report_args: '--output-file=/kubebench/output/results.csv',
      report_image: 'gcr.io/xyhuang-kubeflow/kubebench-tf-cnn-csv-reporter:v20180522-1',
    },
  },
}