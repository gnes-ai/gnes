from typing import List

import random
import torch


def get_lengths_from_binary_sequence_mask(mask: torch.Tensor):
    """
    Compute sequence lengths for each batch element in a tensor using a
    binary mask.
    Parameters
    ----------
    mask : torch.Tensor, required.
        A 2D binary mask of shape (batch_size, sequence_length) to
        calculate the per-batch sequence lengths from.
    Returns
    -------
    A torch.LongTensor of shape (batch_size,) representing the lengths
    of the sequences in the batch.
    """
    return mask.long().sum(-1)


def sort_batch_by_length(tensor: torch.autograd.Variable,
                         sequence_lengths: torch.autograd.Variable):
    """
    Sort a batch first tensor by some specified lengths.
    Parameters
    ----------
    tensor : Variable(torch.FloatTensor), required.
        A batch first Pytorch tensor.
    sequence_lengths : Variable(torch.LongTensor), required.
        A tensor representing the lengths of some dimension of the tensor which
        we want to sort by.
    Returns
    -------
    sorted_tensor : Variable(torch.FloatTensor)
        The original tensor sorted along the batch dimension with respect to sequence_lengths.
    sorted_sequence_lengths : Variable(torch.LongTensor)
        The original sequence_lengths sorted by decreasing size.
    restoration_indices : Variable(torch.LongTensor)
        Indices into the sorted_tensor such that
        ``sorted_tensor.index_select(0, restoration_indices) == original_tensor``
    permuation_index : Variable(torch.LongTensor)
        The indices used to sort the tensor. This is useful if you want to sort many
        tensors using the same ordering.
    """

    if not isinstance(tensor, Variable) or not isinstance(
            sequence_lengths, Variable):
        raise Exception(
            "Both the tensor and sequence lengths must be torch.autograd.Variables."
        )

    sorted_sequence_lengths, permutation_index = sequence_lengths.sort(
        0, descending=True)
    sorted_tensor = tensor.index_select(0, permutation_index)

    # This is ugly, but required - we are creating a new variable at runtime, so we
    # must ensure it has the correct CUDA vs non-CUDA type. We do this by cloning and
    # refilling one of the inputs to the function.
    index_range = sequence_lengths.data.clone().copy_(
        torch.arange(0, len(sequence_lengths)))
    # This is the equivalent of zipping with index, sorting by the original
    # sequence lengths and returning the now sorted indices.
    index_range = Variable(index_range.long())
    _, reverse_mapping = permutation_index.sort(0, descending=False)
    restoration_indices = index_range.index_select(0, reverse_mapping)
    return sorted_tensor, sorted_sequence_lengths, restoration_indices, permutation_index


def get_dropout_mask(dropout_probability: float,
                     tensor_for_masking: torch.autograd.Variable):
    """
    Computes and returns an element-wise dropout mask for a given tensor, where
    each element in the mask is dropped out with probability dropout_probability.
    Note that the mask is NOT applied to the tensor - the tensor is passed to retain
    the correct CUDA tensor type for the mask.
    Parameters
    ----------
    dropout_probability : float, required.
        Probability of dropping a dimension of the input.
    tensor_for_masking : torch.Variable, required.
    Returns
    -------
    A torch.FloatTensor consisting of the binary mask scaled by 1/ (1 - dropout_probability).
    This scaling ensures expected values and variances of the output of applying this mask
     and the original tensor are the same.
    """
    binary_mask = tensor_for_masking.clone()
    binary_mask.data.copy_(
        torch.rand(tensor_for_masking.size()) > dropout_probability)
    # Scale mask by 1/keep_prob to preserve output statistics.
    dropout_mask = binary_mask.float().div(1.0 - dropout_probability)
    return dropout_mask


def block_orthogonal(tensor: torch.Tensor,
                     split_sizes: List[int],
                     gain: float = 1.0) -> None:
    """
        An initializer which allows initializing model parameters in "blocks". This is helpful
        in the case of recurrent models which use multiple gates applied to linear projections,
        which can be computed efficiently if they are concatenated together. However, they are
        separate parameters which should be initialized independently.
        Parameters
        ----------
        tensor : ``torch.Tensor``, required.
            A tensor to initialize.
        split_sizes : List[int], required.
            A list of length ``tensor.ndim()`` specifying the size of the
            blocks along that particular dimension. E.g. ``[10, 20]`` would
            result in the tensor being split into chunks of size 10 along the
            first dimension and 20 along the second.
        gain : float, optional (default = 1.0)
            The gain (scaling) applied to the orthogonal initialization.
        """

    if isinstance(tensor, Variable):
        # in pytorch 4.0, Variable equals Tensor
        #    block_orthogonal(tensor.data, split_sizes, gain)
        #else:
        sizes = list(tensor.size())
        if any([a % b != 0 for a, b in zip(sizes, split_sizes)]):
            raise ConfigurationError(
                "tensor dimensions must be divisible by their respective "
                "split_sizes. Found size: {} and split_sizes: {}".format(
                    sizes, split_sizes))
        indexes = [
            list(range(0, max_size, split))
            for max_size, split in zip(sizes, split_sizes)
        ]
        # Iterate over all possible blocks within the tensor.
        for block_start_indices in itertools.product(*indexes):
            # A list of tuples containing the index to start at for this block
            # and the appropriate step size (i.e split_size[i] for dimension i).
            index_and_step_tuples = zip(block_start_indices, split_sizes)
            # This is a tuple of slices corresponding to:
            # tensor[index: index + step_size, ...]. This is
            # required because we could have an arbitrary number
            # of dimensions. The actual slices we need are the
            # start_index: start_index + step for each dimension in the tensor.
            block_slice = tuple([
                slice(start_index, start_index + step)
                for start_index, step in index_and_step_tuples
            ])
            tensor[block_slice] = torch.nn.init.orthogonal_(
                tensor[block_slice].contiguous(), gain=gain)


def preprocess_data(sents, max_chars=None):
    """
    read raw text file. The format of the input is like, one sentence per line
    words are separated by '\t'
    :param path:
    :param max_chars: int, the number of maximum characters in a word, this
      parameter is used when the model is configured with CNN word encoder.
    :return:
    """
    dataset = []
    textset = []
    for sent in sents:
        data = ['<bos>']
        text = []
        for token in sent:
            text.append(token)
            if max_chars is not None and len(token) + 2 > max_chars:
                token = token[:max_chars - 2]
            data.append(token)
        data.append('<eos>')
        dataset.append(data)
        textset.append(text)
    return dataset, textset


def recover(li, ind):
    # li[piv], ind = torch.sort(li[piv], dim=0, descending=(not unsort))
    dummy = list(range(len(ind)))
    dummy.sort(key=lambda l: ind[l])
    li = [li[i] for i in dummy]
    return li


def create_one_batch(x,
                     word2id,
                     char2id,
                     config,
                     oov='<oov>',
                     pad='<pad>',
                     sort=True):
    """
    Create one batch of input.
    :param x: List[List[str]]
    :param word2id: Dict | None
    :param char2id: Dict | None
    :param config: Dict
    :param oov: str, the form of OOV token.
    :param pad: str, the form of padding token.
    :param sort: bool, specify whether sorting the sentences by their lengths.
    :return:
    """
    batch_size = len(x)
    # lst represents the order of sentences
    lst = list(range(batch_size))
    if sort:
        lst.sort(key=lambda l: -len(x[l]))

    # shuffle the sentences by
    x = [x[i] for i in lst]
    lens = [len(x[i]) for i in lst]
    max_len = max(lens)

    # get a batch of word id whose size is (batch x max_len)
    if word2id is not None:
        oov_id, pad_id = word2id.get(oov, None), word2id.get(pad, None)
        assert oov_id is not None and pad_id is not None
        batch_w = torch.LongTensor(batch_size, max_len).fill_(pad_id)
        for i, x_i in enumerate(x):
            for j, x_ij in enumerate(x_i):
                batch_w[i][j] = word2id.get(x_ij, oov_id)
    else:
        batch_w = None

    # get a batch of character id whose size is (batch x max_len x max_chars)
    if char2id is not None:
        bow_id, eow_id, oov_id, pad_id = [
            char2id.get(key, None) for key in ('<eow>', '<bow>', oov, pad)
        ]

        assert bow_id is not None and eow_id is not None and oov_id is not None and pad_id is not None

        if config['token_embedder']['name'].lower() == 'cnn':
            max_chars = config['token_embedder']['max_characters_per_token']
            assert max([len(w) for i in lst for w in x[i]]) + 2 <= max_chars
        elif config['token_embedder']['name'].lower() == 'lstm':
            # counting the <bow> and <eow>
            max_chars = max([len(w) for i in lst for w in x[i]]) + 2
        else:
            raise ValueError('Unknown token_embedder: {0}'.format(
                config['token_embedder']['name']))

        batch_c = torch.LongTensor(batch_size, max_len,
                                   max_chars).fill_(pad_id)

        for i, x_i in enumerate(x):
            for j, x_ij in enumerate(x_i):
                batch_c[i][j][0] = bow_id
                if x_ij == '<bos>' or x_ij == '<eos>':
                    batch_c[i][j][1] = char2id.get(x_ij)
                    batch_c[i][j][2] = eow_id
                else:
                    for k, c in enumerate(x_ij):
                        batch_c[i][j][k + 1] = char2id.get(c, oov_id)
                    batch_c[i][j][len(x_ij) + 1] = eow_id
    else:
        batch_c = None

    # mask[0] is the matrix (batch x max_len) indicating whether
    # there is an id is valid (not a padding) in this batch.
    # mask[1] stores the flattened ids indicating whether there is a valid
    # previous token
    # mask[2] stores the flattened ids indicating whether there is a valid
    # next token
    masks = [torch.LongTensor(batch_size, max_len).fill_(0), [], []]

    for i, x_i in enumerate(x):
        for j in range(len(x_i)):
            masks[0][i][j] = 1
            if j + 1 < len(x_i):
                masks[1].append(i * max_len + j)
            if j > 0:
                masks[2].append(i * max_len + j)

    assert len(masks[1]) <= batch_size * max_len
    assert len(masks[2]) <= batch_size * max_len

    masks[1] = torch.LongTensor(masks[1])
    masks[2] = torch.LongTensor(masks[2])

    return batch_w, batch_c, lens, masks


# shuffle training examples and create mini-batches
def create_batches(x,
                   batch_size,
                   word2id,
                   char2id,
                   config,
                   perm=None,
                   shuffle=False,
                   sort=True,
                   text=None):
    ind = list(range(len(x)))
    lst = perm or list(range(len(x)))
    if shuffle:
        random.shuffle(lst)

    if sort:
        lst.sort(key=lambda l: -len(x[l]))

    x = [x[i] for i in lst]
    ind = [ind[i] for i in lst]
    if text is not None:
        text = [text[i] for i in lst]

    sum_len = 0.0
    batches_w, batches_c, batches_lens, batches_masks, batches_text, batches_ind = [], [], [], [], [], []
    size = batch_size
    nbatch = (len(x) - 1) // size + 1
    for i in range(nbatch):
        start_id, end_id = i * size, (i + 1) * size
        bw, bc, blens, bmasks = create_one_batch(
            x[start_id:end_id], word2id, char2id, config, sort=sort)
        sum_len += sum(blens)
        batches_w.append(bw)
        batches_c.append(bc)
        batches_lens.append(blens)
        batches_masks.append(bmasks)
        batches_ind.append(ind[start_id:end_id])
        if text is not None:
            batches_text.append(text[start_id:end_id])

    if sort:
        perm = list(range(nbatch))
        random.shuffle(perm)
        batches_w = [batches_w[i] for i in perm]
        batches_c = [batches_c[i] for i in perm]
        batches_lens = [batches_lens[i] for i in perm]
        batches_masks = [batches_masks[i] for i in perm]
        batches_ind = [batches_ind[i] for i in perm]
        if text is not None:
            batches_text = [batches_text[i] for i in perm]

    recover_ind = [item for sublist in batches_ind for item in sublist]
    if text is not None:
        return batches_w, batches_c, batches_lens, batches_masks, batches_text, recover_ind
    return batches_w, batches_c, batches_lens, batches_masks, recover_ind
