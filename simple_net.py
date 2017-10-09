import numpy as np

'''
This file contains functions for the neural network implementation.
It is based on cs231n implementation that Volodymyr wrote.

Some details of the implementation:

- Optimization is a simple GD, but the nice part is a decaying learning rate. Whenever
  we encounter that the loss is worse than before, we probably went the wrong way, and
  LR is multiplied by <1 factor. This seems to do really well in practice.
- We only use a ReLU activation function.
- I adapted the API to mimic scipy's with fit() and predict().
'''

class SimpleNet(object):

  def __init__(self, matrix_dims, weight_magnitude=1e-2, reg=0.01, input_size=30):
    '''
    input_size - dimension of input data
    matrix_dims - dimensions of matrices used in NN, aka layer sizes
    weight_magnitude - we initialize matrice with Gaussian(0, 1) multiplied by this magnitude
    reg - regularization strength
    '''
    # In this task we only deal with 2 classes
    classes = 2

    self.reg = reg
    self.params = {}
    self.num_layers = len(matrix_dims) + 1
    all_md = [input_size] + matrix_dims + [classes]

    for i in range(self.num_layers):
      self.params['W' + str(i)] = weight_magnitude * np.random.randn(all_md[i], all_md[i + 1])
      self.params['b' + str(i)] = np.zeros(all_md[i + 1])

  def loss(self, X, y=None):
    '''
    Compute loss and gradients.
    '''
    # Compute the forward pass
    M = {} # Results of applying affine layer + ReLU
    for i in range(self.num_layers - 1):
      prev = X
      if i > 0:
        prev = M[i - 1]
      Wi, bi = self.params['W' + str(i)], self.params['b' + str(i)]
      Mi = prev.dot(Wi) + bi
      Mi = np.maximum(Mi, np.zeros(Mi.shape))
      M[i] = Mi.copy()

    Wlast, blast = self.params['W' + str(self.num_layers - 1)], self.params['b' + str(self.num_layers - 1)]
    scores = Mi.dot(Wlast) + blast
    
    # If we just need the predictions
    if y is None:
      return scores

    # Compute softmax loss with L2 regularization
    # Disclosure: My implementation used a loop when I implemented this and I
    # looked up how people do it with crazy arrange() usage
    shifted_by_max = scores - np.max(scores, axis=1, keepdims=True)
    Z = np.sum(np.exp(shifted_by_max), axis=1, keepdims=True)
    log_probs = shifted_by_max - np.log(Z)
    probs = np.exp(log_probs)
    loss = -np.sum(log_probs[np.arange(scores.shape[0]), y]) / scores.shape[0]

    # Add regularization
    for i in range(self.num_layers):
      Wi = self.params['W' + str(i)]
      loss += self.reg * (Wi * Wi).sum()

    # Backward pass: compute gradients, storing them in the grads dictionary
    grads = {}

    # probs is sort of the gradient
    probs[range(X.shape[0]), y] -= 1
    probs /= X.shape[0]

    grads['W' + str(self.num_layers - 1)] = M[self.num_layers - 2].T.dot(probs) + 2 * self.reg * self.params['W' + str(self.num_layers - 1)]
    grads['b' + str(self.num_layers - 1)] = np.sum(probs, axis=0)

    idx = self.num_layers - 2
    hg = probs
    while idx >= 0:
      # Relu backward
      hg = hg.dot(self.params['W' + str(idx + 1)].T)
      hg[M[idx] <= 0] = 0

      # Affine backward
      prev = X
      if idx > 0:
        prev = M[idx - 1]

      grads['W' + str(idx)] = prev.T.dot(hg) + 2 * self.reg * self.params['W' + str(idx)]
      grads['b' + str(idx)] = np.sum(hg, axis=0)

      idx -= 1

    return loss, grads

  def fit(self, X, y, learning_rate=0.1, num_iters=1000, verbose=False, decrease_lr_on_mistake=True):
    if verbose:
      print('Started fitting the neural network!')

    # Run gradient descent to optimize W
    loss_history = []
    ploss = 10000.0 # previous loss
    for it in range(num_iters):
      # Evaluate loss and gradient
      loss, grad = self.loss(X, y=y)
      loss_history.append(loss)

      if decrease_lr_on_mistake and loss > ploss:
        # Decrease LR so that we take smaller steps
        learning_rate *= 0.8
        if verbose:
          print('We went the wrong way! Decreasing LR!')
          print('New LR is ' + str(learning_rate))
      ploss = loss

      # Update gradients
      for p, w in self.params.items():
        dw = grad[p]
        next_w = w - learning_rate * dw
        self.params[p] = next_w

      if verbose:
        print('iteration %d / %d: loss %f' % (it, num_iters, loss))

    return loss_history

  def predict(self, X):
    return self.loss(X).argmax(axis=1)
