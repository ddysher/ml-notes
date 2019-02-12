import os
import time

time.sleep(1200)

print 'Printing /etc/caicloud'
print os.listdir('/etc/caicloud')
print 'Printing /etc/kubernetes'
print os.listdir('/etc/kubernetes')
