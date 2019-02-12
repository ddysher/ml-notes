local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["my-benchmark"];

local k = import "k.libsonnet";
local kubebench = import "kubebench/kubebench-job/kubebench-job.libsonnet";

local configArgsStr = params.config_args;
local configImage = params.config_image;
local name = params.name;
local namespace = params.namespace;
local pvcMount = params.pvc_mount;
local pvcName = params.pvc_name;
local reportArgsStr = params.report_args;
local reportImage = params.report_image;

local configArgs =
  if configArgsStr == "null" then
    []
  else
    std.split(configArgsStr, ",");
local reportArgs =
  if reportArgsStr == "null" then
    []
  else
    std.split(reportArgsStr, ",");

std.prune(k.core.v1.list.new([
  kubebench.parts.workflow(name,
                           namespace,
                           configImage,
                           configArgs,
                           reportImage,
                           reportArgs,
                           pvcName,
                           pvcMount),
]))
