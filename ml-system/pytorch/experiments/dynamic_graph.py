from __future__ import print_function

import torch
import torch.nn as nn
import random

class TestNet(nn.Module):

  def __init__(self):
    super(TestNet, self).__init__()
    self.fc_1 = nn.Linear(4, 1)
    self.fc_2 = nn.Linear(4, 1)

  def forward(self, x):
    if random.random() < 0.5:
      x = self.fc_1(x)
    else:
      x = self.fc_2(x)
    return x


data = torch.rand(32, 4)

net = TestNet()
out = net(data) # net(data) will call nn.Module.__call__(), which in turn invokes forward()
loss = sum(out)
loss.backward()

# We called forward/backward once, the gradients of the weights (parameters) of
# either fc_1 or fc_2 should be None.
print("Weights and gradients after one f/b call")
for param in net.parameters():
  print(param)
  print("Gradient:", param.grad, "\n")

# Let's do 10 more forward/backward steps (setting grad to zero between steps).
for _ in range(10):
  out = net(data)
  loss = sum(out)
  net.zero_grad()
  loss.backward()

# Now (unless we were very unlucky (0.5**10-unlucky)), all gradients are not
# None, and only the gradient with respect to the weights that were called
# in the last iteration are non-zero.
print("Weights and gradients after 10 f/b calls")
for param in net.parameters():
  print(param)
  print("Gradient:", param.grad, "\n")
