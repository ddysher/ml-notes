import torch
import torchvision

# An instance of your model.
model = torchvision.models.resnet18()

# An example input you would normally provide to your model's forward() method.
example = torch.rand(1, 3, 224, 224)

# Use torch.jit.trace to generate a torch.jit.ScriptModule via tracing.
traced_script_module = torch.jit.trace(model, example)

# The traced ScriptModule can now be evaluated identically to a regular PyTorch module.
output = traced_script_module(torch.ones(1, 3, 224, 224))
print(output[0, :5])

# To perform serialization, simply call "save" on the module and pass it a filename.
# Later, we can load the module from this file in C++ and execute it without any
# dependency on Python.
traced_script_module.save("./models/model.pt")
