import sys
import xml.etree.ElementTree
import random
import re

if len(sys.argv) != 2:
    sys.stderr.write('Arguments error. Usage:\n')
    sys.stderr.write('\tpython prepare.py data\n')
    sys.exit(1)

# Test data set split ratio
split = 0.20
random.seed(20170426)

input = sys.argv[1]
output_train = 'data.tsv'
output_test = 'data-test.tsv'

try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except NameError:
    pass


def process_posts(fd_in, fd_out_train, fd_out_test, target_tag):
    num = 1
    for line in fd_in:
        try:
            fd_out = fd_out_train if random.random() > split else fd_out_test
            attr = xml.etree.ElementTree.fromstring(line).attrib

            pid = attr.get('Id', '')
            label = 1 if target_tag in attr.get('Tags', '') else 0
            title = re.sub('\s+', ' ', attr.get('Title', '')).strip()
            body = re.sub('\s+', ' ', attr.get('Body', '')).strip()
            text = title + ' ' + body

            fd_out.write(u'{}\t{}\t{}\n'.format(pid, label, text))

            num += 1
        except Exception as ex:
            sys.stderr.write('Error in line {}: {}\n'.format(num, ex))


with open(input) as fd_in:
    with open(output_train, 'w') as fd_out_train:
        with open(output_test, 'w') as fd_out_test:
            process_posts(fd_in, fd_out_train, fd_out_test, u'<python>')
