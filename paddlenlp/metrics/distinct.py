# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import paddle

__all__ = ["Distinct"]


class Distinct(paddle.metric.Metric):
    """
    `Distinct` is an algorithm for evaluating the textual diversity of the
    generated text by calculating the number of distinct n-grams. The larger
    the number of distinct n-grams, the higher the diversity of the text. See
    details at https://arxiv.org/abs/1510.03055.

    :class:`Distinct` could be used as a :class:`paddle.metric.Metric` class,
    or an ordinary class. When :class:`Distinct` is used as a
    :class:`paddle.metric.Metric` class, a function is needed to transform
    the network output to a string list.

    Args:
        n_size (int, optional):
            Number of gram for :class:`Distinct` metric. Defaults to 2.
        trans_func (callable, optional):
            `trans_func` transforms the network output to a string list. Defaults to None.

            .. note::
                When :class:`Distinct` is used as a :class:`paddle.metric.Metric`
                class, `trans_func` must be provided. Please note that the
                input of `trans_func` is numpy array.

        name (str, optional): Name of :class:`paddle.metric.Metric` instance.
            Defaults to "distinct".

    Examples:
        1. Using as a general evaluation object.

        .. code-block:: python

            from paddlenlp.metrics import Distinct
            distinct = Distinct()
            cand = ["The","cat","The","cat","on","the","mat"]
            #update the states
            distinct.add_inst(cand)
            print(distinct.score())
            # 0.8333333333333334

        2. Using as an instance of `paddle.metric.Metric`.

        .. code-block:: python

            import numpy as np
            from functools import partial
            import paddle
            from paddlenlp.transformers import BertTokenizer
            from paddlenlp.metrics import Distinct

            def trans_func(logits, tokenizer):
                '''Transform the network output `logits` to string list.'''
                # [batch_size, seq_len]
                token_ids = np.argmax(logits, axis=-1).tolist()
                cand_list = []
                for ids in token_ids:
                    tokens = tokenizer.convert_ids_to_tokens(ids)
                    strings = tokenizer.convert_tokens_to_string(tokens)
                    cand_list.append(strings.split())
                return cand_list

            paddle.seed(2021)
            tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            distinct = Distinct(trans_func=partial(trans_func, tokenizer=tokenizer))
            batch_size, seq_len, vocab_size = 4, 16, tokenizer.vocab_size
            logits = paddle.rand([batch_size, seq_len, vocab_size])

            distinct.update(logits.numpy())
            print(distinct.accumulate()) # 1.0
    """

    def __init__(self, n_size=2, trans_func=None, name="distinct"):
        super(Distinct, self).__init__()
        self._name = name
        self.diff_ngram = set()
        self.count = 0.0
        self.n_size = n_size
        self.trans_func = trans_func

    def update(self, output, *args):
        """
        Updates the metrics states. This method firstly will use
        :meth:`trans_func` method to process the `output` to get the tokenized
        candidate sentence list. Then call :meth:`add_inst` method to process
        the candidate list one by one.

        Args:
            output (numpy.ndarray|Tensor):
                The outputs of model.
            args (tuple): The additional inputs.
        """
        if isinstance(output, paddle.Tensor):
            output = output.numpy()

        assert self.trans_func is not None, (
            "The `update` method requires user " "to provide `trans_func` when initializing `Distinct`."
        )
        cand_list = self.trans_func(output)

        for cand in cand_list:
            self.add_inst(cand)

    def add_inst(self, cand):
        """
        Updates the states based on the candidate.

        Args:
            cand (list): Tokenized candidate sentence generated by model.
        """
        for i in range(0, len(cand) - self.n_size + 1):
            ngram = " ".join(cand[i : (i + self.n_size)])
            self.count += 1
            self.diff_ngram.add(ngram)

    def reset(self):
        """Resets states and result."""
        self.diff_ngram = set()
        self.count = 0.0

    def accumulate(self):
        """
        Calculates the final distinct score.

        Returns:
            float: The final distinct score.
        """
        distinct = len(self.diff_ngram) / self.count
        return distinct

    def score(self):
        """
        The function is the same as :meth:`accumulate` method.

        Returns:
            float: The final distinct score.
        """
        return self.accumulate()

    def name(self):
        """
        Returns the metric name.

        Returns:
            str: The metric name.
        """
        return self._name
