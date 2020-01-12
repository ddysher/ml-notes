import torch

# Convert it to a ScriptModule by subclassing it from "torch.jit.ScriptModule".
class MyModule(torch.jit.ScriptModule):
    def __init__(self, N, M):
        super(MyModule, self).__init__()
        self.weight = torch.nn.Parameter(torch.rand(N, M))

    # Adding a "@torch.jit.script_method" annotation to the model’s forward method.
    @torch.jit.script_method
    def forward(self, input):
        if bool(input.sum() > 0):
          output = self.weight.mv(input)
        else:
          output = self.weight + input
        return output

my_script_module = MyModule(2, 3)


# Similar to tracing module, we can directly call the script module, and call
# "save" to serialize the model.
output = my_script_module(torch.ones(3))
print(output)

my_script_module.save("./models/simple.pt")
