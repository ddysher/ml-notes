<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Models: Text & Sequence](#models-text--sequence)
  - [LSTM, 1997](#lstm-1997)
  - [GRU, 2014](#gru-2014)
  - [RNN Encoder-Decoder (2014, TODO)](#rnn-encoder-decoder-2014-todo)
  - [Seq2Seq, 2014](#seq2seq-2014)
  - [Transformer (TODO)](#transformer-todo)
  - [BERT (TODO)](#bert-todo)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Models: Text & Sequence

## LSTM, 1997

Long Short Term Memory networks – usually just called "LSTMs" – are a special kind of RNN, capable
of learning long-term dependencies. They were introduced by Hochreiter & Schmidhuber (1997), and
were refined and popularized by many people in following work. They work tremendously well on a
large variety of problems, and are now widely used.

Essentially, LSTM is just another way to compute a hidden state. In basic RNN, we compute the hidden
state based on current input at step `t`, and previous hidden state at step `t-1`, which is then
directly used as RNN cell output. **A LSTM unit does the exact same thing, just in a different way**,
as we'll see in the following formula. In practice, we can treat BasicRNN, LSTM, and GRU units as
black boxes.

Following is the equation for LSTM:

<p align="center"><img src="./assets/lstm-equation.png" height="140px" width="auto"></p>

Different components in LSTM:
- The input gate (`i`) defines how much of the newly computed state for the current input you want
  to let through.
- The forget gate (`f`) defines how much of the previous state you want to let through.
- The output gate (`o`) defines how much of the internal state you want to expose to the external
  network (higher layers and the next time step).
- The internal hidden state "candidate" (`g`) is computed based on the current input and the previous
  hidden state (like in basic RNN cell).
- The internal memory of the unit (`c_t`, or `c_t_hat`) is a combination of the previous memory
  multiplied by the forget gate, and the newly computed hidden state, multiplied by the input gate.
  Thus, intuitively it is a combination of how we want to combine previous memory and the new input.
- The final hidden state (`s_t` or `h_t` or `a_t`) is computed by multiplying the internal memory
  with the output gate.

Intuitively, plain RNNs could be considered a special case of LSTMs (e.g. set input gate to all
1's, forget gate to all 0's, etc). The gating mechanism is what allows LSTMs to explicitly model
long-term dependencies. By learning the parameters for its gates, the network learns how its memory
should behave.

Each LSTM cell contains multiple neurons, which decides the internal hidden state size, i.e.

<p align="center"><img src="./assets/lstm-num-units.png" height="360px" width="auto"></p>
<p align="center"><a href="https://stackoverflow.com/questions/37901047/what-is-num-units-in-tensorflow-basiclstmcell" style="font-size: 12px">Image Source</a></p>

LSTM only handles fixed length input and fixed length output, so
- for variable-length input, we need to use zero padding
- for variable-length output, we need to use `<eos>` tokens

A popular LSTM variant is peephole connections. It is introduced by Gers & Schmidhuber (2000), that
allow the gates to not only depend on the previous hidden state `s_{t-1}`, but also on the previous
internal state `c_{t-1}`, adding an additional term in the gate equations.

**LSTM Usages: Sequence Generation Problem**

In sequence generation problem, we usually train a model with one or more RNN layers to generate
text, music, etc. At training time, the input is a list of sequence, and the output is all these
sequences left shift by 1. For example, if the task is to generate baby name, then one intput
sequence can be `<go>alice`, and output sequence is `alice<eos>`, where `<go>` means start of
sequence and `<eos>` means end of sequence.

Given an input sequence `x` at timestep (location) `t`, the model will predict a character based on
current input character at `t`, as well as past characters. For example, given character `l` in the
above example, the model should ideally predict `i`. Strictly speaking, the model will produce a
probability distribution across all possible values (vocabulary). That is, the model will return,
for example, [0.01, 0.05, ... ,0.04], where 0.01 corresponds to the probability that the next
character is 'a', 0.05 is the probability for 'b', etc. Note if the vocabulary size is large, then
it's infeasible to compute all the probabilities. There is a technology called "Sampled Softmax" to
solve the problem.

Now we have the probability distribution across all timestep, the total loss of the sequence is the
sum of all losses at individual timestep. In the above example, we use cross entropy to compute loss
for character `a`, character `l`, character `i`, etc, and sum them up. Once we have the loss value,
we can adjust relevant weights using backpropagation through time.

At inference time, we depend on "Sampling" to generate desired sequence. It works as follows: we
first feed an initial input (can be all zeros) to the model, then sample a value from its probability
distribution, e.g. for initial zero input, it's likely that the model will output a probability
distribution where characters like `a` have larger probability, and characters like `z` have smaller
probability. We then feed the generated character to the network, just like the initial zero input,
then repeat the process for the whole sequence until we reach `<eos>` or other termination condition
like max generated sequence length.

**LSTM Usages: Encoder-Decoder LSTM for seq2seq Problem**

Sequence-to-sequence prediction problems are challenging because the number of items in the input
and output sequences can vary. For example, text translation and learning to execute programs are
examples of seq2seq problems.

One approach to seq2seq prediction problems that has proven very effective is called the Encoder-Decoder
LSTM. This architecture is comprised of **two models**: one for reading the input sequence and encoding
it into a fixed-length vector, and a second for decoding the fixed-length vector and outputting the
predicted sequence. The use of the models in concert gives the architecture its name of Encoder-Decoder
LSTM designed specifically for seq2seq problems.

> ... RNN Encoder-Decoder, consists of two recurrent neural networks (RNN) that act as an encoder
> and a decoder pair. The encoder maps a variable-length source sequence to a fixed-length vector,
> and the decoder maps the vector representation back to a variable-length target sequence.

Note this approach has also been used with image inputs where a Convolutional Neural Network is used
as a feature extractor on input images, which is then read by a decoder LSTM.

> ... we propose to follow this elegant recipe, replacing the encoder RNN by a deep convolution
> neural network (CNN). ... it is natural to use a CNN as an image encoder, by first pre-training
> it for an image classification task and using the last hidden layer as an input to the RNN decoder
> that generates sentences

**Misc Notes**

Two functions in Keras are commonly used in Encoder-Decoder LSTM:
- TimeDistributed
- RepeatVector

For more information, refer to [this blog](https://machinelearningmastery.com/encoder-decoder-long-short-term-memory-networks/).

*References*

- http://colah.github.io/posts/2015-08-Understanding-LSTMs/
- https://hackernoon.com/understanding-architecture-of-lstm-cell-from-scratch-with-code-8da40f0b71f4
- https://adventuresinmachinelearning.com/recurrent-neural-networks-lstm-tutorial-tensorflow/
- [recurrent-neural-network-tutorial-part-4-implementing-a-grulstm-rnn-with-python-and-theano](http://www.wildml.com/2015/10/recurrent-neural-network-tutorial-part-4-implementing-a-grulstm-rnn-with-python-and-theano/)

## GRU, 2014

GRU is a variant (simplified version) of LSTM.

A GRU has two gates, a reset gate `r`, and an update gate `z`. Intuitively, the reset gate determines
how to combine the new input with the previous memory, and the update gate defines how much of the
previous memory to keep around. If we set the reset to all 1's and update gate to all 0's, we again
arrive at our plain RNN model.

<p align="center"><img src="./assets/gru-equation.png" height="100px" width="auto"></p>

**GRU vs LSTM**

There isn’t a clear winner. In many tasks both architectures yield comparable performance and tuning
hyperparameters like layer size is probably more important than picking the ideal architecture.

## RNN Encoder-Decoder (2014, TODO)

Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation

https://arxiv.org/abs/1406.1078

## Seq2Seq, 2014

The sequence to sequence model, short for [seq2seq](https://arxiv.org/abs/1409.3215), is introduced
for the first time in 2014 by Google. It aims to map a fixed length input with a fixed length output
where the length of the input and output may differ.

For example, translating "What are you doing today?" from English to Chinese has input of 5 words and
output of 7 symbols. Clearly, we can't use a regular LSTM network to map each word from the English
sentence to the Chinese sentence. This is why sequence to sequence model is used to address problems
like that one.

Summary of seq2seq model:

> Our method uses a multilayered Long Short-Term Memory (LSTM) to map the input sequence to a vector
> of a fixed dimensionality, and then another deep LSTM to decode the target sequence from the vector.

Diagram 1:

<p align="center"><img src="./assets/seq2seq.jpeg" height="240px" width="auto"></p>

Diagram 2:

<p align="center"><img src="./assets/seq2seq-2.png" height="240px" width="auto"></p>

The power of seq2seq model lies in the fact that it can map sequences of different lengths to each
other. As you can see the inputs and outputs are not correlated and their lengths can differ. This
opens a whole new range of problems which can now be solved using such architecture.

*References*

- [understanding-encoder-decoder-sequence-to-sequence-model](https://towardsdatascience.com/understanding-encoder-decoder-sequence-to-sequence-model-679e04af4346)
- [seq2seq-the-clown-car-of-deep-learning](https://medium.com/@devnag/seq2seq-the-clown-car-of-deep-learning-f88e1204dac3)
- https://github.com/tensorflow/nmt

## Transformer (TODO)

https://arxiv.org/abs/1706.03762

## BERT (TODO)

https://arxiv.org/abs/1810.04805
