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
from collections import defaultdict
import os
import numpy as np
from functools import partial

import paddle
import paddle.nn as nn
import paddle.nn.functional as F
from paddle.fluid.framework import in_dygraph_mode

from paddle.fluid.layer_helper import LayerHelper
import paddle
import paddlenlp
from paddlenlp.ops.ext_utils import load, LOADED_EXT
from paddlenlp.utils.log import logger


def infer_transformer_decoding(
        enc_output, memory_seq_lens, word_emb, slf_ln_weight, slf_ln_bias,
        slf_q_weight, slf_q_bias, slf_k_weight, slf_k_bias, slf_v_weight,
        slf_v_bias, slf_out_weight, slf_out_bias, cross_ln_weight,
        cross_ln_bias, cross_q_weight, cross_q_bias, cross_k_weight,
        cross_k_bias, cross_v_weight, cross_v_bias, cross_out_weight,
        cross_out_bias, ffn_ln_weight, ffn_ln_bias, ffn_inter_weight,
        ffn_inter_bias, ffn_out_weight, ffn_out_bias, decoder_ln_weight,
        decoder_ln_bias, linear_weight, linear_bias, pos_emb,
        _decoding_strategy, _beam_size, _topk, _topp, _n_head, _size_per_head,
        _n_layer, _bos_id, _eos_id, _max_out_len, _diversity_rate, _rel_len,
        _alpha):
    helper = LayerHelper('fusion_decoding', **locals())

    inputs = {
        'Input': enc_output,
        'MemSeqLen': memory_seq_lens,
        'WordEmbedding': word_emb,
        'SelfLayernormWeight@VECTOR': slf_ln_weight,
        'SelfLayernormBias@VECTOR': slf_ln_bias,
        'SelfQueryWeight@VECTOR': slf_q_weight,
        'SelfQueryBias@VECTOR': slf_q_bias,
        'SelfKeyWeight@VECTOR': slf_k_weight,
        'SelfKeyBias@VECTOR': slf_k_bias,
        'SelfValueWeight@VECTOR': slf_v_weight,
        'SelfValueBias@VECTOR': slf_v_bias,
        'SelfOutWeight@VECTOR': slf_out_weight,
        'SelfOutBias@VECTOR': slf_out_bias,
        'CrossLayernormWeight@VECTOR': cross_ln_weight,
        'CrossLayernormBias@VECTOR': cross_ln_bias,
        'CrossQueryWeight@VECTOR': cross_q_weight,
        'CrossQueryBias@VECTOR': cross_q_bias,
        'CrossKeyWeight@VECTOR': cross_k_weight,
        'CrossKeyBias@VECTOR': cross_k_bias,
        'CrossValueWeight@VECTOR': cross_v_weight,
        'CrossValueBias@VECTOR': cross_v_bias,
        'CrossOutWeight@VECTOR': cross_out_weight,
        'CrossOutBias@VECTOR': cross_out_bias,
        'FFNLayernormWeight@VECTOR': ffn_ln_weight,
        'FFNLayernormBias@VECTOR': ffn_ln_bias,
        'FFNInterWeight@VECTOR': ffn_inter_weight,
        'FFNInterBias@VECTOR': ffn_inter_bias,
        'FFNOutWeight@VECTOR': ffn_out_weight,
        'FFNOutBias@VECTOR': ffn_out_bias,
        'DecoderLayernormWeight': decoder_ln_weight,
        'DecoderLayernormBias': decoder_ln_bias,
        'EmbWeight': linear_weight,
        'EmbBias': linear_bias,
        'PositionEncEmb': pos_emb
    }

    attrs = {
        'decoding_strategy': _decoding_strategy,
        'beam_size': _beam_size,
        'topk': _topk,
        'topp': _topp,
        'n_head': _n_head,
        'size_per_head': _size_per_head,
        'num_layer': _n_layer,
        'bos_id': _bos_id,
        'eos_id': _eos_id,
        'max_len': _max_out_len,
        'beam_search_diversity_rate': _diversity_rate,
        "rel_len": _rel_len,
        "alpha": _alpha
    }

    output_ids = helper.create_variable(dtype="int32")
    parent_ids = helper.create_variable(dtype="int32")
    sequence_length = helper.create_variable(dtype="int32")

    outputs = {
        'OutputIds': output_ids,
        'ParentIds': parent_ids,
        'SequenceLength': sequence_length
    }

    helper.append_op(
        type='fusion_decoding', inputs=inputs, outputs=outputs, attrs=attrs)

    return output_ids, parent_ids, sequence_length


def infer_force_decoding(
        enc_output, memory_seq_lens, word_emb, slf_ln_weight, slf_ln_bias,
        slf_q_weight, slf_q_bias, slf_k_weight, slf_k_bias, slf_v_weight,
        slf_v_bias, slf_out_weight, slf_out_bias, cross_ln_weight,
        cross_ln_bias, cross_q_weight, cross_q_bias, cross_k_weight,
        cross_k_bias, cross_v_weight, cross_v_bias, cross_out_weight,
        cross_out_bias, ffn_ln_weight, ffn_ln_bias, ffn_inter_weight,
        ffn_inter_bias, ffn_out_weight, ffn_out_bias, decoder_ln_weight,
        decoder_ln_bias, linear_weight, linear_bias, pos_emb, trg_word,
        _decoding_strategy, _beam_size, _topk, _topp, _n_head, _size_per_head,
        _n_layer, _bos_id, _eos_id, _max_out_len, _diversity_rate, _rel_len,
        _alpha):
    helper = LayerHelper('fusion_force_decoding', **locals())

    inputs = {
        'Input': enc_output,
        'MemSeqLen': memory_seq_lens,
        'WordEmbedding': word_emb,
        'SelfLayernormWeight@VECTOR': slf_ln_weight,
        'SelfLayernormBias@VECTOR': slf_ln_bias,
        'SelfQueryWeight@VECTOR': slf_q_weight,
        'SelfQueryBias@VECTOR': slf_q_bias,
        'SelfKeyWeight@VECTOR': slf_k_weight,
        'SelfKeyBias@VECTOR': slf_k_bias,
        'SelfValueWeight@VECTOR': slf_v_weight,
        'SelfValueBias@VECTOR': slf_v_bias,
        'SelfOutWeight@VECTOR': slf_out_weight,
        'SelfOutBias@VECTOR': slf_out_bias,
        'CrossLayernormWeight@VECTOR': cross_ln_weight,
        'CrossLayernormBias@VECTOR': cross_ln_bias,
        'CrossQueryWeight@VECTOR': cross_q_weight,
        'CrossQueryBias@VECTOR': cross_q_bias,
        'CrossKeyWeight@VECTOR': cross_k_weight,
        'CrossKeyBias@VECTOR': cross_k_bias,
        'CrossValueWeight@VECTOR': cross_v_weight,
        'CrossValueBias@VECTOR': cross_v_bias,
        'CrossOutWeight@VECTOR': cross_out_weight,
        'CrossOutBias@VECTOR': cross_out_bias,
        'FFNLayernormWeight@VECTOR': ffn_ln_weight,
        'FFNLayernormBias@VECTOR': ffn_ln_bias,
        'FFNInterWeight@VECTOR': ffn_inter_weight,
        'FFNInterBias@VECTOR': ffn_inter_bias,
        'FFNOutWeight@VECTOR': ffn_out_weight,
        'FFNOutBias@VECTOR': ffn_out_bias,
        'DecoderLayernormWeight': decoder_ln_weight,
        'DecoderLayernormBias': decoder_ln_bias,
        'EmbWeight': linear_weight,
        'EmbBias': linear_bias,
        'PositionEncEmb': pos_emb,
        # The input of custom op must be given.
        # Dispensable() and Intermediate() are not supported.
        'TrgWord': trg_word
    }

    attrs = {
        'decoding_strategy': _decoding_strategy,
        'beam_size': _beam_size,
        'topk': _topk,
        'topp': _topp,
        'n_head': _n_head,
        'size_per_head': _size_per_head,
        'num_layer': _n_layer,
        'bos_id': _bos_id,
        'eos_id': _eos_id,
        'max_len': _max_out_len,
        'beam_search_diversity_rate': _diversity_rate,
        "rel_len": _rel_len,
        "alpha": _alpha
    }

    output_ids = helper.create_variable(dtype="int32")
    parent_ids = helper.create_variable(dtype="int32")
    sequence_length = helper.create_variable(dtype="int32")

    outputs = {
        'OutputIds': output_ids,
        'ParentIds': parent_ids,
        'SequenceLength': sequence_length
    }

    helper.append_op(
        type='fusion_force_decoding',
        inputs=inputs,
        outputs=outputs,
        attrs=attrs)

    return output_ids, parent_ids, sequence_length


def infer_gpt_decoding(
        input, attn_mask, mem_seq_len, word_emb, slf_ln_weight, slf_ln_bias,
        slf_q_weight, slf_q_bias, slf_k_weight, slf_k_bias, slf_v_weight,
        slf_v_bias, slf_out_weight, slf_out_bias, ffn_ln_weight, ffn_ln_bias,
        ffn_inter_weight, ffn_inter_bias, ffn_out_weight, ffn_out_bias,
        decoder_ln_weight, decoder_ln_bias, pos_emb, linear_weight, topk, topp,
        max_out_len, head_num, size_per_head, num_layer, bos_id, eos_id,
        temperature, use_fp16_decoding):
    helper = LayerHelper('fusion_gpt', **locals())

    inputs = {
        "Input": input,
        "AttentionMask": attn_mask,
        "StartLength": mem_seq_len,
        "WordEmbedding": word_emb,
        "SelfLayernormWeight@VECTOR": slf_ln_weight,
        "SelfLayernormBias@VECTOR": slf_ln_bias,
        "SelfQueryWeight@VECTOR": slf_q_weight,
        "SelfQueryBias@VECTOR": slf_q_bias,
        "SelfKeyWeight@VECTOR": slf_k_weight,
        "SelfKeyBias@VECTOR": slf_k_bias,
        "SelfValueWeight@VECTOR": slf_v_weight,
        "SelfValueBias@VECTOR": slf_v_bias,
        "SelfOutWeight@VECTOR": slf_out_weight,
        "SelfOutBias@VECTOR": slf_out_bias,
        "FFNLayernormWeight@VECTOR": ffn_ln_weight,
        "FFNLayernormBias@VECTOR": ffn_ln_bias,
        "FFNInterWeight@VECTOR": ffn_inter_weight,
        "FFNInterBias@VECTOR": ffn_inter_bias,
        "FFNOutWeight@VECTOR": ffn_out_weight,
        "FFNOutBias@VECTOR": ffn_out_bias,
        "DecoderLayernormWeight": decoder_ln_weight,
        "DecoderLayernormBias": decoder_ln_bias,
        "PositionEncEmb": pos_emb,
        "EmbWeight": linear_weight
    }

    attrs = {
        "topk": topk,
        "topp": topp,
        "max_len": max_out_len,
        "n_head": head_num,
        "size_per_head": size_per_head,
        "num_layer": num_layer,
        "bos_id": bos_id,
        "eos_id": eos_id,
        "temperature": temperature,
        "use_fp16": use_fp16_decoding
    }

    output_ids = helper.create_variable(dtype="int32")
    outputs = {'OutputIds': output_ids}

    helper.append_op(
        type='fusion_gpt', inputs=inputs, outputs=outputs, attrs=attrs)

    return output_ids


def infer_unified_decoding(
        input_ids, attn_mask, memory_seq_lens, type_id, decoder_type_id,
        logits_mask, word_emb, slf_ln_weight, slf_ln_bias, slf_q_weight,
        slf_q_bias, slf_k_weight, slf_k_bias, slf_v_weight, slf_v_bias,
        slf_out_weight, slf_out_bias, ffn_ln_weight, ffn_ln_bias,
        ffn_inter_weight, ffn_inter_bias, ffn_out_weight, ffn_out_bias,
        decoder_ln_weight, decoder_ln_bias, trans_weight, trans_bias,
        lm_ln_weight, lm_ln_bias, linear_weight, linear_bias, pos_emb, type_emb,
        role_id, decoder_role_id, role_emb, position_id, decoder_position_id,
        _decoding_strategy, _beam_size, _topk, _topp, _n_head, _size_per_head,
        _n_layer, _bos_id, _eos_id, _max_out_len, _diversity_rate, _unk_id,
        _mask_id, _temperature, _len_penalty, _normalize_before, _pos_bias,
        _hidden_act, _rel_len, _early_stopping, _min_length):
    helper = LayerHelper('fusion_unified_decoding', **locals())

    inputs = {
        "InputIds": input_ids,
        "AttnMask": attn_mask,
        "MemSeqLen": memory_seq_lens,
        "TypeIds": type_id,
        "DecTypeIds": decoder_type_id,
        "LogitsMask": logits_mask,
        "WordEmbedding": word_emb,
        "SelfLayernormWeight@VECTOR": slf_ln_weight,
        "SelfLayernormBias@VECTOR": slf_ln_bias,
        "SelfQueryWeight@VECTOR": slf_q_weight,
        "SelfQueryBias@VECTOR": slf_q_bias,
        "SelfKeyWeight@VECTOR": slf_k_weight,
        "SelfKeyBias@VECTOR": slf_k_bias,
        "SelfValueWeight@VECTOR": slf_v_weight,
        "SelfValueBias@VECTOR": slf_v_bias,
        "SelfOutWeight@VECTOR": slf_out_weight,
        "SelfOutBias@VECTOR": slf_out_bias,
        "FFNLayernormWeight@VECTOR": ffn_ln_weight,
        "FFNLayernormBias@VECTOR": ffn_ln_bias,
        "FFNInterWeight@VECTOR": ffn_inter_weight,
        "FFNInterBias@VECTOR": ffn_inter_bias,
        "FFNOutWeight@VECTOR": ffn_out_weight,
        "FFNOutBias@VECTOR": ffn_out_bias,
        "DecoderLayernormWeight": decoder_ln_weight,
        "DecoderLayernormBias": decoder_ln_bias,
        "TransWeight": trans_weight,
        "TransBias": trans_bias,
        "LMLayernormWeight": lm_ln_weight,
        "LMLayernormBias": lm_ln_bias,
        "EmbWeight": linear_weight,
        "EmbBias": linear_bias,
        "PositionEncEmb": pos_emb,
        "TypeEmb": type_emb,
        "RoleIds": role_id,
        "DecRoleIds": decoder_role_id,
        "RoleEmbedding": role_emb,
        "PositionIds": position_id,
        "DecPositionIds": decoder_position_id
    }

    attrs = {
        "decoding_strategy": _decoding_strategy,
        "beam_size": _beam_size,
        "topk": _topk,
        "topp": _topp,
        "n_head": _n_head,
        "size_per_head": _size_per_head,
        "num_layer": _n_layer,
        "bos_id": _bos_id,
        "eos_id": _eos_id,
        "max_len": _max_out_len,
        "beam_search_diversity_rate": _diversity_rate,
        "unk_id": _unk_id,
        "mask_id": _mask_id,
        "temperature": _temperature,
        "len_penalty": _len_penalty,
        "normalize_before": _normalize_before,
        "pos_bias": _pos_bias,
        "hidden_act": _hidden_act,
        "rel_len": _rel_len,
        "early_stopping": _early_stopping,
        "min_length": _min_length
    }

    output_ids = helper.create_variable(dtype="int32")
    parent_ids = helper.create_variable(dtype="int32")
    sequence_length = helper.create_variable(dtype="int32")
    output_scores = helper.create_variable(dtype="float32")

    outputs = {
        'OutputIds': output_ids,
        'ParentIds': parent_ids,
        'SequenceLength': sequence_length,
        "OutputScores": output_scores
    }

    helper.append_op(
        type='fusion_unified_decoding',
        inputs=inputs,
        outputs=outputs,
        attrs=attrs)

    return output_ids, parent_ids, sequence_length, output_scores


def infer_bart_decoding(
        enc_output, memory_seq_lens, word_emb, slf_ln_weight, slf_ln_bias,
        slf_q_weight, slf_q_bias, slf_k_weight, slf_k_bias, slf_v_weight,
        slf_v_bias, slf_out_weight, slf_out_bias, cross_ln_weight,
        cross_ln_bias, cross_q_weight, cross_q_bias, cross_k_weight,
        cross_k_bias, cross_v_weight, cross_v_bias, cross_out_weight,
        cross_out_bias, ffn_ln_weight, ffn_ln_bias, ffn_inter_weight,
        ffn_inter_bias, ffn_out_weight, ffn_out_bias, decoder_ln_weight,
        decoder_ln_bias, linear_weight, linear_bias, pos_emb,
        _decoding_strategy, _beam_size, _topk, _topp, _n_head, _size_per_head,
        _n_layer, _bos_id, _eos_id, _max_out_len, _diversity_rate, _rel_len,
        _alpha, _early_stopping):

    helper = LayerHelper('fusion_bart_decoding', **locals())

    inputs = {
        'Input': enc_output,
        'MemSeqLen': memory_seq_lens,
        'WordEmbedding': word_emb,
        'SelfLayernormWeight@VECTOR': slf_ln_weight,
        'SelfLayernormBias@VECTOR': slf_ln_bias,
        'SelfQueryWeight@VECTOR': slf_q_weight,
        'SelfQueryBias@VECTOR': slf_q_bias,
        'SelfKeyWeight@VECTOR': slf_k_weight,
        'SelfKeyBias@VECTOR': slf_k_bias,
        'SelfValueWeight@VECTOR': slf_v_weight,
        'SelfValueBias@VECTOR': slf_v_bias,
        'SelfOutWeight@VECTOR': slf_out_weight,
        'SelfOutBias@VECTOR': slf_out_bias,
        'CrossLayernormWeight@VECTOR': cross_ln_weight,
        'CrossLayernormBias@VECTOR': cross_ln_bias,
        'CrossQueryWeight@VECTOR': cross_q_weight,
        'CrossQueryBias@VECTOR': cross_q_bias,
        'CrossKeyWeight@VECTOR': cross_k_weight,
        'CrossKeyBias@VECTOR': cross_k_bias,
        'CrossValueWeight@VECTOR': cross_v_weight,
        'CrossValueBias@VECTOR': cross_v_bias,
        'CrossOutWeight@VECTOR': cross_out_weight,
        'CrossOutBias@VECTOR': cross_out_bias,
        'FFNLayernormWeight@VECTOR': ffn_ln_weight,
        'FFNLayernormBias@VECTOR': ffn_ln_bias,
        'FFNInterWeight@VECTOR': ffn_inter_weight,
        'FFNInterBias@VECTOR': ffn_inter_bias,
        'FFNOutWeight@VECTOR': ffn_out_weight,
        'FFNOutBias@VECTOR': ffn_out_bias,
        'DecoderLayernormWeight': decoder_ln_weight,
        'DecoderLayernormBias': decoder_ln_bias,
        'EmbWeight': linear_weight,
        'EmbBias': linear_bias,
        'PositionEncEmb': pos_emb
    }

    attrs = {
        'decoding_strategy': _decoding_strategy,
        'beam_size': _beam_size,
        'topk': _topk,
        'topp': _topp,
        'n_head': _n_head,
        'size_per_head': _size_per_head,
        'num_layer': _n_layer,
        'bos_id': _bos_id,
        'eos_id': _eos_id,
        'max_len': _max_out_len,
        'beam_search_diversity_rate': _diversity_rate,
        "rel_len": _rel_len,
        "alpha": _alpha,
        "early_stopping": _early_stopping
    }

    output_ids = helper.create_variable(dtype="int32")
    parent_ids = helper.create_variable(dtype="int32")
    sequence_length = helper.create_variable(dtype="int32")

    outputs = {
        'OutputIds': output_ids,
        'ParentIds': parent_ids,
        'SequenceLength': sequence_length
    }

    helper.append_op(
        type='fusion_bart_decoding',
        inputs=inputs,
        outputs=outputs,
        attrs=attrs)

    return output_ids, parent_ids, sequence_length


def infer_mbart_decoding(
        enc_output, memory_seq_lens, word_emb, slf_ln_weight, slf_ln_bias,
        slf_q_weight, slf_q_bias, slf_k_weight, slf_k_bias, slf_v_weight,
        slf_v_bias, slf_out_weight, slf_out_bias, cross_ln_weight,
        cross_ln_bias, cross_q_weight, cross_q_bias, cross_k_weight,
        cross_k_bias, cross_v_weight, cross_v_bias, cross_out_weight,
        cross_out_bias, ffn_ln_weight, ffn_ln_bias, ffn_inter_weight,
        ffn_inter_bias, ffn_out_weight, ffn_out_bias, decoder_ln_weight,
        decoder_ln_bias, mbart_ln_weight, mbart_ln_bias, linear_weight,
        linear_bias, pos_emb, trg_word, _decoding_strategy, _beam_size, _topk,
        _topp, _n_head, _size_per_head, _n_layer, _bos_id, _eos_id,
        _max_out_len, _diversity_rate, _rel_len, _alpha, _temperature,
        _early_stopping, _hidden_act):
    helper = LayerHelper('fusion_mbart_decoding', **locals())

    inputs = {
        'Input': enc_output,
        'MemSeqLen': memory_seq_lens,
        'WordEmbedding': word_emb,
        'SelfLayernormWeight@VECTOR': slf_ln_weight,
        'SelfLayernormBias@VECTOR': slf_ln_bias,
        'SelfQueryWeight@VECTOR': slf_q_weight,
        'SelfQueryBias@VECTOR': slf_q_bias,
        'SelfKeyWeight@VECTOR': slf_k_weight,
        'SelfKeyBias@VECTOR': slf_k_bias,
        'SelfValueWeight@VECTOR': slf_v_weight,
        'SelfValueBias@VECTOR': slf_v_bias,
        'SelfOutWeight@VECTOR': slf_out_weight,
        'SelfOutBias@VECTOR': slf_out_bias,
        'CrossLayernormWeight@VECTOR': cross_ln_weight,
        'CrossLayernormBias@VECTOR': cross_ln_bias,
        'CrossQueryWeight@VECTOR': cross_q_weight,
        'CrossQueryBias@VECTOR': cross_q_bias,
        'CrossKeyWeight@VECTOR': cross_k_weight,
        'CrossKeyBias@VECTOR': cross_k_bias,
        'CrossValueWeight@VECTOR': cross_v_weight,
        'CrossValueBias@VECTOR': cross_v_bias,
        'CrossOutWeight@VECTOR': cross_out_weight,
        'CrossOutBias@VECTOR': cross_out_bias,
        'FFNLayernormWeight@VECTOR': ffn_ln_weight,
        'FFNLayernormBias@VECTOR': ffn_ln_bias,
        'FFNInterWeight@VECTOR': ffn_inter_weight,
        'FFNInterBias@VECTOR': ffn_inter_bias,
        'FFNOutWeight@VECTOR': ffn_out_weight,
        'FFNOutBias@VECTOR': ffn_out_bias,
        'DecoderLayernormWeight': decoder_ln_weight,
        'DecoderLayernormBias': decoder_ln_bias,
        'MBARTLayernormWeight': mbart_ln_weight,
        'MBARTLayernormBias': mbart_ln_bias,
        'EmbWeight': linear_weight,
        'EmbBias': linear_bias,
        'PositionEncEmb': pos_emb,
        # The input of custom op must be given.
        # Dispensable() and Intermediate() are not supported.
        'TrgWord': trg_word
    }

    attrs = {
        'decoding_strategy': _decoding_strategy,
        'beam_size': _beam_size,
        'topk': _topk,
        'topp': _topp,
        'n_head': _n_head,
        'size_per_head': _size_per_head,
        'num_layer': _n_layer,
        'bos_id': _bos_id,
        'eos_id': _eos_id,
        'max_len': _max_out_len,
        'beam_search_diversity_rate': _diversity_rate,
        "rel_len": _rel_len,
        "alpha": _alpha,
        "temperature": _temperature,
        "early_stopping": _early_stopping,
        "hidden_act": _hidden_act
    }

    output_ids = helper.create_variable(dtype="int32")
    parent_ids = helper.create_variable(dtype="int32")
    sequence_length = helper.create_variable(dtype="int32")

    outputs = {
        'OutputIds': output_ids,
        'ParentIds': parent_ids,
        'SequenceLength': sequence_length
    }

    helper.append_op(
        type='fusion_mbart_decoding',
        inputs=inputs,
        outputs=outputs,
        attrs=attrs)

    return output_ids, parent_ids, sequence_length


def finalize(beam_size,
             output_ids,
             parent_ids,
             out_seq_lens,
             forced_eos_token_id=None,
             max_seq_len=None,
             decoding_strategy="beam_search"):
    if max_seq_len is None:
        max_seq_len = paddle.max(out_seq_lens)
    ids = paddle.slice(output_ids, [0], [0], [max_seq_len])
    if decoding_strategy.startswith("beam_search"):
        parent_ids = paddle.slice(parent_ids, [0], [0], [max_seq_len]) % (
            beam_size * 2 if decoding_strategy.endswith("_v2") or
            decoding_strategy.endswith("_v3") else beam_size)
        ids = paddle.nn.functional.gather_tree(ids, parent_ids)
        if forced_eos_token_id is not None:
            ids[-1, :, :] = forced_eos_token_id
    else:
        if forced_eos_token_id is not None:
            ids[-1, :] = forced_eos_token_id
    return ids


def transfer_param(p, is_bias=False, dtype="float16", restore_data=False):
    param_shape = p.shape
    # Allow CPU/GPU and float16/float32 transfer
    # NOTE: str(p.place) differs between paddle develop and 2.2
    if str(p.dtype)[-len(dtype):] == dtype and ("gpu" in str(p.place).lower() or
                                                "cuda" in str(p.place).lower()):
        return p
    if restore_data:
        if in_dygraph_mode():
            param_data = p.numpy()
            # Creating parameters with Assign initializer is too slow. Maybe we
            # can cast to fp16 directly and get a tensor, while we do it more
            # elaborately to get a ParamBase. Also note `VarBase.set_value`
            # enforce the same dtype and can not be used directly.
            new_p = type(p)(shape=param_shape, dtype=dtype, is_bias=is_bias)
            new_p.value().get_tensor().set(
                param_data.astype(dtype),
                paddle.fluid.framework._current_expected_place())
            return new_p
        else:
            param_data = np.array(paddle.static.global_scope().find_var(p.name)
                                  .get_tensor())
    return paddle.create_parameter(
        shape=param_shape,
        dtype=dtype,
        is_bias=is_bias,
        default_initializer=paddle.nn.initializer.Assign(param_data)
        if restore_data else None)


def convert_params(faster_model,
                   model,
                   fuse_qkv=1,
                   use_fp16=False,
                   restore_data=False):
    r"""
    Convert parameters included in Transformer layer (`nn.TransformerEncoder`
    and `gpt.modeling.TransformerDecoder`) from original models to the format
    of faster models.

    Args:
        faster_model (Layer): The faster model object.
        model (Layer): The Transformer layer. It can be an instance of
            `nn.TransformerEncoder` or `gpt.modeling.TransformerDecoder`
            currently, and `nn.TransformerDecoder` would be supported soon.
        fuse_qkv (int): 0 for nofuse, 1 for fuse, 2 for fuse and delete the
            unfused parameters. If environment variable `PPFG_QKV_MEM_OPT` is
            set and the weights of q/k/v is fused, it will try to delete the
            original unfused weights. Note the rollback to original model would
            not be guarantee anymore when the faster model failed if the original
            weights are deleted. Default to 1.
        use_fp16 (bool): Whether to use float16. Maybe we should use the default
            dtype as the highest priority later. Default to `False`.
        restore_data (bool): If `False`, need to reload the weight values. It
            should be `True` for weight loaded models. Default to `False`.

    Returns:
        defaultdict: Each value is a list including converted parameters in all
            layers. For other parameters not included in Transformer module to
            be converted, such as embeddings, you can achieve it by using the
            returned dict `params` though `params['word_emb'].append()` directly
            which would do CPU/GPU and fp32/fp16 transfer automatically.
    """
    if fuse_qkv == 1:
        fuse_qkv = 2 if os.getenv("PPFG_QKV_MEM_OPT", "0") == "1" else 1

    class _list(list):
        def append(self, item):
            if isinstance(item[0], nn.Layer):
                layer, attr = item
                param = getattr(layer, attr)
                param = transfer_param(
                    param,
                    is_bias=attr.endswith("bias"),
                    dtype="float16" if use_fp16 else "float32",
                    restore_data=restore_data)
                setattr(layer, attr, param)
            else:
                # NOTE: Compared with if branch, there is no layer attribute
                # refered to the transfered param, thus we should set it as
                # the layer attribute to be able to convert to static graph.
                if len(item) == 2:
                    param, is_bias = item
                    attr_handle = lambda x: x
                else:
                    param, is_bias, attr_handle = item
                param = transfer_param(
                    param,
                    is_bias=is_bias,
                    dtype="float16" if use_fp16 else "float32",
                    restore_data=restore_data)
                attr_handle(param)
            return super().append(param)

    params = defaultdict(_list)

    def _concat_param(q_proj,
                      k_proj,
                      v_proj,
                      attr="weight",
                      use_numpy=True,
                      del_param=False):
        # TODO(guosheng): maybe static graph need this
        # p = faster_model.create_parameter(
        #     shape=[q.shape[0], q.shape[1] + k.shape[1] + v.shape[1]],
        #     dtype=q.dtype,
        #     is_bias=is_bias)
        q = getattr(q_proj, attr)
        k = getattr(k_proj, attr)
        v = getattr(v_proj, attr)
        if use_numpy:
            q = q.numpy()
            if del_param:
                if attr == "weight":
                    del q_proj.weight
                else:
                    del q_proj.bias
            k = k.numpy()
            if del_param:
                if attr == "weight":
                    del k_proj.weight
                else:
                    del k_proj.bias
            v = v.numpy()
            if del_param:
                if attr == "weight":
                    del v_proj.weight
                else:
                    del v_proj.bias
            p = paddle.to_tensor(np.concatenate([q, k, v], axis=-1))
        else:
            p = paddle.concat([q, k, v], axis=-1)
            if del_param:
                for i in [q_proj, k_proj, v_proj]:
                    if attr == "weight":
                        del i.weight
                    else:
                        del i.bias
        return p

    def _convert(module):
        if isinstance(
                module,
            (
                nn.TransformerEncoder,  # nn.TransformerDecoder,
                paddlenlp.transformers.gpt.modeling.TransformerDecoder)):
            for i, layer in enumerate(module.layers):
                # fuse_qkv: 0 for nofuse, 1 for fuse,
                # 2 for fuse and delete the unfused
                if fuse_qkv == 0:
                    params["slf_q_weight"].append(
                        (layer.self_attn.q_proj, "weight"))
                    params["slf_q_bias"].append(
                        (layer.self_attn.q_proj, "bias"))
                    params["slf_k_weight"].append(
                        (layer.self_attn.k_proj, "weight"))
                    params["slf_k_bias"].append(
                        (layer.self_attn.k_proj, "bias"))
                    params["slf_v_weight"].append(
                        (layer.self_attn.v_proj, "weight"))
                    params["slf_v_bias"].append(
                        (layer.self_attn.v_proj, "bias"))
                else:
                    w = _concat_param(
                        layer.self_attn.q_proj,
                        layer.self_attn.k_proj,
                        layer.self_attn.v_proj,
                        attr="weight",
                        use_numpy=fuse_qkv == 2,
                        del_param=fuse_qkv == 2)
                    b = _concat_param(
                        layer.self_attn.q_proj,
                        layer.self_attn.k_proj,
                        layer.self_attn.v_proj,
                        attr="bias",
                        use_numpy=fuse_qkv == 2,
                        del_param=fuse_qkv == 2)
                    params["slf_q_weight"].append((w, False))
                    params["slf_q_bias"].append((b, True))
                    # NOTE: use `params["slf_q_weight"][-1]` rather than `w`
                    # since the appended tensor might be a new transfered tensor
                    setattr(faster_model, "slf_q_weight_" + str(i),
                            params["slf_q_weight"][-1])
                    setattr(faster_model, "slf_q_bias_" + str(i),
                            params["slf_q_bias"][-1])
                    # TODO(guosheng): Tensor with size 0 might be failed in
                    # paddle develop, thus use tensor with size 1 instead
                    # temporarily. While size 0 seems all right in to_static.
                    dummy_tensor = paddle.zeros([1])
                    for key in [
                            f"slf_{m}_{n}"
                            for m in ("k", "v") for n in ("weight", "bias")
                    ]:
                        params[key].append((dummy_tensor, True
                                            if key.endswith("bias") else False))
                        setattr(faster_model, key + "_" + str(i),
                                params[key][-1])

                params["slf_out_weight"].append(
                    (layer.self_attn.out_proj, "weight"))
                params["slf_out_bias"].append(
                    (layer.self_attn.out_proj, "bias"))
                params["slf_ln_weight"].append((layer.norm1, "weight"))
                params["slf_ln_bias"].append((layer.norm1, "bias"))
                params["ffn_inter_weight"].append((layer.linear1, "weight"))
                params["ffn_inter_bias"].append((layer.linear1, "bias"))
                params["ffn_out_weight"].append((layer.linear2, "weight"))
                params["ffn_out_bias"].append((layer.linear2, "bias"))
                params["ffn_ln_weight"].append((layer.norm2, "weight"))
                params["ffn_ln_bias"].append((layer.norm2, "bias"))
                if isinstance(module, nn.TransformerDecoder):
                    # TODO(guosheng): support nn.TransformerDecoder
                    pass
            if module.norm is not None:
                params["decoder_ln_weight"].append((module.norm, "weight"))
                params["decoder_ln_bias"].append((module.norm, "bias"))

    model.apply(_convert)
    return params


class InferTransformerDecoding(nn.Layer):
    def __init__(self,
                 decoder,
                 word_embedding,
                 positional_embedding,
                 linear,
                 num_decoder_layers,
                 n_head,
                 d_model,
                 bos_id=0,
                 eos_id=1,
                 decoding_strategy="beam_search",
                 beam_size=4,
                 topk=1,
                 topp=0.0,
                 max_out_len=256,
                 diversity_rate=0.0,
                 decoding_lib=None,
                 use_fp16_decoding=False,
                 rel_len=False,
                 alpha=0.6):
        # if decoding_lib is None:
        #     raise ValueError(
        #         "The args decoding_lib must be set to use FasterTransformer. ")
        # elif not os.path.exists(decoding_lib):
        #     raise ValueError("The path to decoding lib is not exist.")
        if decoding_lib is not None and os.path.isfile(decoding_lib):
            # Maybe it has been loadad by `ext_utils.load`
            if "FasterTransformer" not in LOADED_EXT.keys():
                ops = paddle.utils.cpp_extension.load_op_meta_info_and_register_op(
                    decoding_lib)
                LOADED_EXT["FasterTransformer"] = ops
        else:
            if decoding_lib is not None:
                logger.warning(
                    "The specified decoding_lib does not exist, and it will be built automatically."
                )
            load("FasterTransformer", verbose=True)

        size_per_head = d_model / n_head
        # fuse_qkv can only support size_per_head of [32, 64, 128].
        if size_per_head in [32, 64, 128]:
            self._fuse_qkv = True
        else:
            self._fuse_qkv = False

        super(InferTransformerDecoding, self).__init__()
        for arg, value in locals().items():
            if arg not in [
                    "self", "decoder", "word_embedding", "positional_embedding",
                    "linear"
            ]:
                setattr(self, "_" + arg, value)
        # process weights
        if use_fp16_decoding:
            for mod in decoder.layers:
                mod.norm1.weight = transfer_param(mod.norm1.weight)
                mod.norm1.bias = transfer_param(mod.norm1.bias, is_bias=True)
                mod.self_attn.q_proj.weight = transfer_param(
                    mod.self_attn.q_proj.weight)
                mod.self_attn.q_proj.bias = transfer_param(
                    mod.self_attn.q_proj.bias, is_bias=True)
                mod.self_attn.k_proj.weight = transfer_param(
                    mod.self_attn.k_proj.weight)
                mod.self_attn.k_proj.bias = transfer_param(
                    mod.self_attn.k_proj.bias, is_bias=True)
                mod.self_attn.v_proj.weight = transfer_param(
                    mod.self_attn.v_proj.weight)
                mod.self_attn.v_proj.bias = transfer_param(
                    mod.self_attn.v_proj.bias, is_bias=True)
                mod.self_attn.out_proj.weight = transfer_param(
                    mod.self_attn.out_proj.weight)
                mod.self_attn.out_proj.bias = transfer_param(
                    mod.self_attn.out_proj.bias, is_bias=True)

                mod.norm2.weight = transfer_param(mod.norm2.weight)
                mod.norm2.bias = transfer_param(mod.norm2.bias, is_bias=True)
                mod.cross_attn.q_proj.weight = transfer_param(
                    mod.cross_attn.q_proj.weight)
                mod.cross_attn.q_proj.bias = transfer_param(
                    mod.cross_attn.q_proj.bias, is_bias=True)
                mod.cross_attn.k_proj.weight = transfer_param(
                    mod.cross_attn.k_proj.weight)
                mod.cross_attn.k_proj.bias = transfer_param(
                    mod.cross_attn.k_proj.bias, is_bias=True)
                mod.cross_attn.v_proj.weight = transfer_param(
                    mod.cross_attn.v_proj.weight)
                mod.cross_attn.v_proj.bias = transfer_param(
                    mod.cross_attn.v_proj.bias, is_bias=True)
                mod.cross_attn.out_proj.weight = transfer_param(
                    mod.cross_attn.out_proj.weight)
                mod.cross_attn.out_proj.bias = transfer_param(
                    mod.cross_attn.out_proj.bias, is_bias=True)

                mod.norm3.weight = transfer_param(mod.norm3.weight)
                mod.norm3.bias = transfer_param(mod.norm3.bias, is_bias=True)
                mod.linear1.weight = transfer_param(mod.linear1.weight)
                mod.linear1.bias = transfer_param(
                    mod.linear1.bias, is_bias=True)
                mod.linear2.weight = transfer_param(mod.linear2.weight)
                mod.linear2.bias = transfer_param(
                    mod.linear2.bias, is_bias=True)

            decoder.norm.weight = transfer_param(decoder.norm.weight)
            decoder.norm.bias = transfer_param(decoder.norm.bias, is_bias=True)

            linear.weight = transfer_param(linear.weight)
            linear.bias = transfer_param(linear.bias, is_bias=True)

            positional_embedding.weight = transfer_param(
                positional_embedding.weight)
            word_embedding.weight = transfer_param(word_embedding.weight)

        self.slf_ln_weight = []
        self.slf_ln_bias = []
        self.slf_q_weight = []
        self.slf_q_bias = []
        self.slf_k_weight = []
        self.slf_k_bias = []
        self.slf_v_weight = []
        self.slf_v_bias = []
        self.slf_out_weight = []
        self.slf_out_bias = []

        self.cross_ln_weight = []
        self.cross_ln_bias = []
        self.cross_q_weight = []
        self.cross_q_bias = []
        self.cross_k_weight = []
        self.cross_k_bias = []
        self.cross_v_weight = []
        self.cross_v_bias = []
        self.cross_out_weight = []
        self.cross_out_bias = []

        self.ffn_ln_weight = []
        self.ffn_ln_bias = []
        self.ffn_inter_weight = []
        self.ffn_inter_bias = []
        self.ffn_out_weight = []
        self.ffn_out_bias = []

        for i, mod in enumerate(decoder.layers):
            self.slf_ln_weight.append(mod.norm1.weight)
            self.slf_ln_bias.append(mod.norm1.bias)

            if self._fuse_qkv:
                q_weight_shape = mod.self_attn.q_proj.weight.shape
                k_weight_shape = mod.self_attn.k_proj.weight.shape
                v_weight_shape = mod.self_attn.v_proj.weight.shape

                q_weights = self.create_parameter(
                    shape=[
                        q_weight_shape[0], q_weight_shape[1] + k_weight_shape[1]
                        + v_weight_shape[1]
                    ],
                    dtype="float16" if use_fp16_decoding else "float32")
                setattr(self, "slf_q_weight_" + str(i), q_weights)
                self.slf_q_weight.append(
                    getattr(self, "slf_q_weight_" + str(i)))

                q_bias_shape = mod.self_attn.q_proj.bias.shape
                k_bias_shape = mod.self_attn.k_proj.bias.shape
                v_bias_shape = mod.self_attn.v_proj.bias.shape

                q_biases = self.create_parameter(
                    shape=[
                        q_bias_shape[0] + k_bias_shape[0] + v_bias_shape[0]
                    ],
                    dtype="float16" if use_fp16_decoding else "float32",
                    is_bias=True)
                setattr(self, "slf_q_bias_" + str(i), q_biases)
                self.slf_q_bias.append(getattr(self, "slf_q_bias_" + str(i)))
            else:
                self.slf_q_weight.append(mod.self_attn.q_proj.weight)
                self.slf_q_bias.append(mod.self_attn.q_proj.bias)

            self.slf_k_weight.append(mod.self_attn.k_proj.weight)
            self.slf_k_bias.append(mod.self_attn.k_proj.bias)
            self.slf_v_weight.append(mod.self_attn.v_proj.weight)
            self.slf_v_bias.append(mod.self_attn.v_proj.bias)
            self.slf_out_weight.append(mod.self_attn.out_proj.weight)
            self.slf_out_bias.append(mod.self_attn.out_proj.bias)

            self.cross_ln_weight.append(mod.norm2.weight)
            self.cross_ln_bias.append(mod.norm2.bias)
            self.cross_q_weight.append(mod.cross_attn.q_proj.weight)
            self.cross_q_bias.append(mod.cross_attn.q_proj.bias)
            self.cross_k_weight.append(mod.cross_attn.k_proj.weight)
            self.cross_k_bias.append(mod.cross_attn.k_proj.bias)
            self.cross_v_weight.append(mod.cross_attn.v_proj.weight)
            self.cross_v_bias.append(mod.cross_attn.v_proj.bias)
            self.cross_out_weight.append(mod.cross_attn.out_proj.weight)
            self.cross_out_bias.append(mod.cross_attn.out_proj.bias)

            self.ffn_ln_weight.append(mod.norm3.weight)
            self.ffn_ln_bias.append(mod.norm3.bias)
            self.ffn_inter_weight.append(mod.linear1.weight)
            self.ffn_inter_bias.append(mod.linear1.bias)
            self.ffn_out_weight.append(mod.linear2.weight)
            self.ffn_out_bias.append(mod.linear2.bias)

        self.decoder_ln_weight = [decoder.norm.weight]
        self.decoder_ln_bias = [decoder.norm.bias]

        self.pos_emb = [positional_embedding.weight]
        self.word_emb = [word_embedding.weight]

        self.linear_weight = [linear.weight]
        self.linear_bias = [linear.bias]

    def forward(self, enc_output, memory_seq_lens, trg_word=None):
        def parse_function(func_name):
            return partial(
                func_name,
                word_emb=self.word_emb,
                slf_ln_weight=self.slf_ln_weight,
                slf_ln_bias=self.slf_ln_bias,
                slf_q_weight=self.slf_q_weight,
                slf_q_bias=self.slf_q_bias,
                slf_k_weight=self.slf_k_weight,
                slf_k_bias=self.slf_k_bias,
                slf_v_weight=self.slf_v_weight,
                slf_v_bias=self.slf_v_bias,
                slf_out_weight=self.slf_out_weight,
                slf_out_bias=self.slf_out_bias,
                cross_ln_weight=self.cross_ln_weight,
                cross_ln_bias=self.cross_ln_bias,
                cross_q_weight=self.cross_q_weight,
                cross_q_bias=self.cross_q_bias,
                cross_k_weight=self.cross_k_weight,
                cross_k_bias=self.cross_k_bias,
                cross_v_weight=self.cross_v_weight,
                cross_v_bias=self.cross_v_bias,
                cross_out_weight=self.cross_out_weight,
                cross_out_bias=self.cross_out_bias,
                ffn_ln_weight=self.ffn_ln_weight,
                ffn_ln_bias=self.ffn_ln_bias,
                ffn_inter_weight=self.ffn_inter_weight,
                ffn_inter_bias=self.ffn_inter_bias,
                ffn_out_weight=self.ffn_out_weight,
                ffn_out_bias=self.ffn_out_bias,
                decoder_ln_weight=self.decoder_ln_weight,
                decoder_ln_bias=self.decoder_ln_bias,
                linear_weight=self.linear_weight,
                linear_bias=self.linear_bias,
                pos_emb=self.pos_emb,
                _decoding_strategy=self._decoding_strategy,
                _beam_size=self._beam_size,
                _topk=self._topk,
                _topp=self._topp,
                _n_head=self._n_head,
                _size_per_head=int(self._d_model / self._n_head),
                _n_layer=self._num_decoder_layers,
                _bos_id=self._bos_id,
                _eos_id=self._eos_id,
                _max_out_len=self._max_out_len,
                _diversity_rate=self._diversity_rate,
                _rel_len=self._rel_len,
                _alpha=self._alpha)

        if self._decoding_strategy.startswith("beam_search"):
            # TODO: Due to paddle.tile bug in static graph, tile_beam_merge_with_batch
            # cannot work properly. These comments should be opened after PaddlePaddle v2.2.2.
            if paddle.__version__ <= "2.1.3":
                enc_output = nn.decode.BeamSearchDecoder.tile_beam_merge_with_batch(
                    enc_output, self._beam_size)
                memory_seq_lens = nn.decode.BeamSearchDecoder.tile_beam_merge_with_batch(
                    memory_seq_lens, self._beam_size)
            else:
                enc_output_shape = paddle.shape(enc_output)
                batch_size = enc_output_shape[0]
                max_seq_len = enc_output_shape[1]
                enc_output = enc_output.unsqueeze([1])
                memory_seq_lens = memory_seq_lens.unsqueeze([1])
                enc_output = paddle.expand(
                    enc_output,
                    shape=[
                        batch_size, self._beam_size, max_seq_len, self._d_model
                    ]
                ).reshape(
                    [batch_size * self._beam_size, max_seq_len, self._d_model])
                memory_seq_lens = paddle.expand(
                    memory_seq_lens,
                    shape=[batch_size, self._beam_size]).reshape(
                        [batch_size * self._beam_size])

        if trg_word is None:
            output_ids, parent_ids, sequence_length = parse_function(
                infer_transformer_decoding)(enc_output=[enc_output],
                                            memory_seq_lens=[memory_seq_lens])
        else:
            output_ids, parent_ids, sequence_length = parse_function(
                infer_force_decoding)(enc_output=[enc_output],
                                      memory_seq_lens=[memory_seq_lens],
                                      trg_word=[trg_word])

        ids = finalize(
            self._beam_size,
            output_ids,
            parent_ids,
            sequence_length,
            decoding_strategy=self._decoding_strategy)

        return ids


class InferGptDecoding(nn.Layer):
    def __init__(self, model, decoding_lib=None, use_fp16_decoding=False):
        if decoding_lib is not None and os.path.isfile(decoding_lib):
            if "FasterTransformer" not in LOADED_EXT.keys():
                ops = paddle.utils.cpp_extension.load_op_meta_info_and_register_op(
                    decoding_lib)
                LOADED_EXT["FasterTransformer"] = ops
        else:
            if decoding_lib is not None:
                logger.warning(
                    "The specified decoding_lib does not exist, and it will be built automatically."
                )
            load("FasterTransformer", verbose=True)

        super(InferGptDecoding, self).__init__()

        self.use_fp16_decoding = use_fp16_decoding
        self.model = model
        self.head_num = self.model.gpt.config['num_attention_heads']
        self.size_per_head = int(self.model.gpt.config['hidden_size'] /
                                 self.head_num)
        self.num_layer = self.model.gpt.config['num_hidden_layers']

        params = convert_params(
            self,
            model,
            fuse_qkv=1,
            use_fp16=use_fp16_decoding,
            restore_data=True)
        params["word_emb"].append(
            (self.model.gpt.embeddings.word_embeddings, "weight"))
        params["pos_emb"].append(
            (self.model.gpt.embeddings.position_embeddings, "weight"))
        params["linear_weight"].append(
            (self.model.gpt.embeddings.word_embeddings, "weight"))
        for k, v in params.items():
            setattr(self, k, v)

    def forward(self,
                input_ids,
                mem_seq_len,
                attention_mask=None,
                topk=4,
                topp=0.0,
                bos_token_id=None,
                eos_token_id=None,
                pad_token_id=None,
                forced_eos_token_id=None,
                max_out_len=256,
                temperature=1):
        if attention_mask is None:
            batch_size = paddle.shape(input_ids)[0]
            attention_mask = paddle.tril(
                paddle.ones(
                    [batch_size, mem_seq_len, mem_seq_len],
                    dtype="float16" if self.use_fp16_decoding else "float32"))
        elif self.use_fp16_decoding and attention_mask.dtype == paddle.float32:
            attention_mask = paddle.cast(attention_mask, dtype="float16")

        output_ids = infer_gpt_decoding(
            input=[input_ids],
            attn_mask=[attention_mask],
            mem_seq_len=[mem_seq_len],
            word_emb=self.word_emb,
            slf_ln_weight=self.slf_ln_weight,
            slf_ln_bias=self.slf_ln_bias,
            slf_q_weight=self.slf_q_weight,
            slf_q_bias=self.slf_q_bias,
            slf_k_weight=self.slf_k_weight,
            slf_k_bias=self.slf_k_bias,
            slf_v_weight=self.slf_v_weight,
            slf_v_bias=self.slf_v_bias,
            slf_out_weight=self.slf_out_weight,
            slf_out_bias=self.slf_out_bias,
            ffn_ln_weight=self.ffn_ln_weight,
            ffn_ln_bias=self.ffn_ln_bias,
            ffn_inter_weight=self.ffn_inter_weight,
            ffn_inter_bias=self.ffn_inter_bias,
            ffn_out_weight=self.ffn_out_weight,
            ffn_out_bias=self.ffn_out_bias,
            decoder_ln_weight=self.decoder_ln_weight,
            decoder_ln_bias=self.decoder_ln_bias,
            pos_emb=self.pos_emb,
            linear_weight=self.linear_weight,
            topk=topk,
            topp=topp,
            max_out_len=max_out_len,
            head_num=self.head_num,
            size_per_head=self.size_per_head,
            num_layer=self.num_layer,
            bos_id=bos_token_id,
            eos_id=eos_token_id,
            temperature=temperature,
            use_fp16_decoding=self.use_fp16_decoding)

        output_ids = output_ids[paddle.shape(input_ids)[-1]:, :]
        if forced_eos_token_id is not None:
            output_ids[:, -1] = forced_eos_token_id
        return output_ids


class InferUnifiedDecoding(nn.Layer):
    def __init__(self,
                 model,
                 decoding_lib=None,
                 use_fp16_decoding=False,
                 logits_mask=None,
                 n_head=8,
                 hidden_dims=512,
                 size_per_head=64,
                 n_layer=6,
                 unk_id=0,
                 mask_id=30000,
                 normalize_before=True,
                 hidden_act="gelu"):
        if decoding_lib is not None and os.path.isfile(decoding_lib):
            # Maybe it has been loadad by `ext_utils.load`
            if "FasterTransformer" not in LOADED_EXT.keys():
                ops = paddle.utils.cpp_extension.load_op_meta_info_and_register_op(
                    decoding_lib)
                LOADED_EXT["FasterTransformer"] = ops
        else:
            if decoding_lib is not None:
                logger.warning(
                    "The specified decoding_lib does not exist, and it will be built automatically."
                )
            load("FasterTransformer", verbose=True)

        super(InferUnifiedDecoding, self).__init__()
        for arg, value in locals().items():
            if arg not in ["self"]:
                setattr(self, "_" + arg, value)

        params = convert_params(
            self,
            model,
            fuse_qkv=1,
            use_fp16=use_fp16_decoding,
            restore_data=True)
        params["word_emb"].append((model.embeddings.word_embeddings, "weight"))
        params["pos_emb"].append(
            (model.embeddings.position_embeddings, "weight"))
        params["type_emb"].append(
            (model.embeddings.token_type_embeddings, "weight"))
        if getattr(model.embeddings, "role_embeddings", None) is not None:
            params["role_emb"].append(
                (model.embeddings.role_embeddings, "weight"))
        else:
            # inputs of custom op cannot be None
            params["role_emb"].append((paddle.zeros(shape=[1]), False, partial(
                setattr, self, "default_role_emb")))
        if not self._normalize_before:
            # pre-norm params has been converted in `convert_params`, and this
            # is only for post-norm such as UNIMO.
            params["decoder_ln_weight"].append((model.encoder_norm, "weight"))
            params["decoder_ln_bias"].append((model.encoder_norm, "bias"))
        params["trans_weight"].append((model.lm_head.transform, "weight"))
        params["trans_bias"].append((model.lm_head.transform, "bias"))
        params["lm_ln_weight"].append((model.lm_head.layer_norm, "weight"))
        params["lm_ln_bias"].append((model.lm_head.layer_norm, "bias"))
        # NOTE: newly created tensors should be layer attribute refered to be
        # able to convert to static graph.
        params["linear_weight"].append((model.lm_head.decoder_weight.t(), False,
                                        partial(setattr, self, "dec_weight")))
        params["linear_bias"].append((paddle.assign(model.lm_head.decoder_bias),
                                      True, partial(setattr, self, "dec_bias")))
        for k, v in params.items():
            setattr(self, k, v)

    def forward(self,
                input_ids,
                attn_mask,
                memory_seq_lens,
                type_id,
                decoder_type_id,
                role_id=None,
                decoder_role_id=None,
                position_id=None,
                decoder_position_id=None,
                beam_size=4,
                topk=4,
                topp=0.0,
                decoding_strategy="greedy_search",
                max_out_len=256,
                bos_token_id=None,
                eos_token_id=None,
                pad_token_id=None,
                forced_eos_token_id=None,
                temperature=1.0,
                length_penalty=1.0,
                diversity_rate=0.0,
                pos_bias=True,
                rel_len=False,
                early_stopping=False,
                min_length=0):
        if role_id is None:
            role_id = paddle.zeros(shape=[0], dtype="int32")
            decoder_role_id = paddle.zeros(shape=[0], dtype="int32")
        if position_id is None:
            position_id = paddle.zeros(shape=[0], dtype="int32")
            decoder_position_id = paddle.zeros(shape=[0], dtype="int32")

        if decoding_strategy == "greedy_search":
            decoding_strategy = "topk_sampling"
            topk = 1
            topp = 0
        elif decoding_strategy in [
                "sampling", "topk_sampling", "topp_sampling"
        ]:
            if topp == 1 and topk > 0:
                decoding_strategy = "topk_sampling"
                topp = 0
            elif topp > 0 and topk == 0:
                decoding_strategy = "topp_sampling"
            else:
                raise AttributeError(
                    "Only topk sampling or topp sampling are supported. " \
                    "Topk sampling and topp sampling cannot be both applied in the faster version.")
        elif decoding_strategy.startswith("beam_search"):
            decoding_strategy = "beam_search_v3"

        output_ids, parent_ids, sequence_length, output_scores = infer_unified_decoding(
            input_ids=[input_ids],
            attn_mask=[attn_mask],
            memory_seq_lens=[memory_seq_lens],
            type_id=[type_id],
            decoder_type_id=[decoder_type_id],
            logits_mask=[self._logits_mask],
            word_emb=self.word_emb,
            slf_ln_weight=self.slf_ln_weight,
            slf_ln_bias=self.slf_ln_bias,
            slf_q_weight=self.slf_q_weight,
            slf_q_bias=self.slf_q_bias,
            slf_k_weight=self.slf_k_weight,
            slf_k_bias=self.slf_k_bias,
            slf_v_weight=self.slf_v_weight,
            slf_v_bias=self.slf_v_bias,
            slf_out_weight=self.slf_out_weight,
            slf_out_bias=self.slf_out_bias,
            ffn_ln_weight=self.ffn_ln_weight,
            ffn_ln_bias=self.ffn_ln_bias,
            ffn_inter_weight=self.ffn_inter_weight,
            ffn_inter_bias=self.ffn_inter_bias,
            ffn_out_weight=self.ffn_out_weight,
            ffn_out_bias=self.ffn_out_bias,
            decoder_ln_weight=self.decoder_ln_weight,
            decoder_ln_bias=self.decoder_ln_bias,
            trans_weight=self.trans_weight,
            trans_bias=self.trans_bias,
            lm_ln_weight=self.lm_ln_weight,
            lm_ln_bias=self.lm_ln_bias,
            linear_weight=self.linear_weight,
            linear_bias=self.linear_bias,
            pos_emb=self.pos_emb,
            type_emb=self.type_emb,
            role_id=[role_id],
            decoder_role_id=[decoder_role_id],
            role_emb=self.role_emb,
            position_id=[position_id],
            decoder_position_id=[decoder_position_id],
            _decoding_strategy=decoding_strategy,
            _beam_size=beam_size,
            _topk=topk,
            _topp=topp,
            _n_head=self._n_head,
            _size_per_head=self._size_per_head,
            _n_layer=self._n_layer,
            _bos_id=bos_token_id,
            _eos_id=eos_token_id,
            _max_out_len=max_out_len,
            _diversity_rate=-diversity_rate,
            _unk_id=self._unk_id,
            _mask_id=self._mask_id,
            _temperature=temperature,
            _len_penalty=length_penalty,
            _normalize_before=self._normalize_before,
            _pos_bias=pos_bias,
            _hidden_act=self._hidden_act,
            _rel_len=rel_len,
            _early_stopping=early_stopping,
            _min_length=min_length)
        ids = finalize(
            beam_size,
            output_ids,
            parent_ids,
            sequence_length,
            forced_eos_token_id=forced_eos_token_id,
            decoding_strategy=decoding_strategy)
        return ids, output_scores


class InferBartDecoding(nn.Layer):
    def __init__(self, model, decoding_lib=None, use_fp16_decoding=False):
        if decoding_lib is not None and os.path.isfile(decoding_lib):
            # Maybe it has been loadad by `ext_utils.load`
            if "FasterTransformer" not in LOADED_EXT.keys():
                ops = paddle.utils.cpp_extension.load_op_meta_info_and_register_op(
                    decoding_lib)
                LOADED_EXT["FasterTransformer"] = ops
        else:
            if decoding_lib is not None:
                logger.warning(
                    "The specified decoding_lib does not exist, and it will be built automatically."
                )
            load("FasterTransformer", verbose=True)

        super(InferBartDecoding, self).__init__()
        for arg, value in locals().items():
            if arg not in [
                    "self", "model", "word_embedding", "positional_embedding",
                    "linear"
            ]:
                setattr(self, "_" + arg, value)
        self._num_decoder_layers = model.bart.config['num_decoder_layers']
        self._n_head = model.bart.config['decoder_attention_heads']
        self._d_model = model.bart.config['d_model']

        # process weights
        if use_fp16_decoding:
            for mod in model.bart.decoder.decoder.layers:
                mod.norm1.weight = transfer_param(
                    mod.norm1.weight, restore_data=True)
                mod.norm1.bias = transfer_param(
                    mod.norm1.bias, is_bias=True, restore_data=True)
                mod.self_attn.q_proj.weight = transfer_param(
                    mod.self_attn.q_proj.weight, restore_data=True)
                mod.self_attn.q_proj.bias = transfer_param(
                    mod.self_attn.q_proj.bias, is_bias=True, restore_data=True)
                mod.self_attn.k_proj.weight = transfer_param(
                    mod.self_attn.k_proj.weight, restore_data=True)
                mod.self_attn.k_proj.bias = transfer_param(
                    mod.self_attn.k_proj.bias, is_bias=True, restore_data=True)
                mod.self_attn.v_proj.weight = transfer_param(
                    mod.self_attn.v_proj.weight, restore_data=True)
                mod.self_attn.v_proj.bias = transfer_param(
                    mod.self_attn.v_proj.bias, is_bias=True, restore_data=True)
                mod.self_attn.out_proj.weight = transfer_param(
                    mod.self_attn.out_proj.weight, restore_data=True)
                mod.self_attn.out_proj.bias = transfer_param(
                    mod.self_attn.out_proj.bias,
                    is_bias=True,
                    restore_data=True)

                mod.norm2.weight = transfer_param(
                    mod.norm2.weight, restore_data=True)
                mod.norm2.bias = transfer_param(
                    mod.norm2.bias, is_bias=True, restore_data=True)
                mod.cross_attn.q_proj.weight = transfer_param(
                    mod.cross_attn.q_proj.weight, restore_data=True)
                mod.cross_attn.q_proj.bias = transfer_param(
                    mod.cross_attn.q_proj.bias, is_bias=True, restore_data=True)
                mod.cross_attn.k_proj.weight = transfer_param(
                    mod.cross_attn.k_proj.weight, restore_data=True)
                mod.cross_attn.k_proj.bias = transfer_param(
                    mod.cross_attn.k_proj.bias, is_bias=True, restore_data=True)
                mod.cross_attn.v_proj.weight = transfer_param(
                    mod.cross_attn.v_proj.weight, restore_data=True)
                mod.cross_attn.v_proj.bias = transfer_param(
                    mod.cross_attn.v_proj.bias, is_bias=True, restore_data=True)
                mod.cross_attn.out_proj.weight = transfer_param(
                    mod.cross_attn.out_proj.weight, restore_data=True)
                mod.cross_attn.out_proj.bias = transfer_param(
                    mod.cross_attn.out_proj.bias,
                    is_bias=True,
                    restore_data=True)

                mod.norm3.weight = transfer_param(
                    mod.norm3.weight, restore_data=True)
                mod.norm3.bias = transfer_param(
                    mod.norm3.bias, is_bias=True, restore_data=True)
                mod.linear1.weight = transfer_param(
                    mod.linear1.weight, restore_data=True)
                mod.linear1.bias = transfer_param(
                    mod.linear1.bias, is_bias=True, restore_data=True)
                mod.linear2.weight = transfer_param(
                    mod.linear2.weight, restore_data=True)
                mod.linear2.bias = transfer_param(
                    mod.linear2.bias, is_bias=True, restore_data=True)

            model.decoder.decoder_layernorm_embedding.weight = transfer_param(
                model.decoder.decoder_layernorm_embedding.weight,
                restore_data=True)
            model.decoder.decoder_layernorm_embedding.bias = transfer_param(
                model.decoder.decoder_layernorm_embedding.bias,
                is_bias=True,
                restore_data=True)

            model.lm_head_weight = transfer_param(
                model.lm_head_weight, restore_data=True)
            model.final_logits_bias = transfer_param(
                model.final_logits_bias, is_bias=True, restore_data=True)

            model.decoder.decoder_embed_positions.weight = transfer_param(
                model.decoder.decoder_embed_positions.weight, restore_data=True)
            model.decoder.embed_tokens.weight = transfer_param(
                model.decoder.embed_tokens.weight, restore_data=True)

        self.slf_ln_weight = []
        self.slf_ln_bias = []
        self.slf_q_weight = []
        self.slf_q_bias = []
        self.slf_k_weight = []
        self.slf_k_bias = []
        self.slf_v_weight = []
        self.slf_v_bias = []
        self.slf_out_weight = []
        self.slf_out_bias = []

        self.cross_ln_weight = []
        self.cross_ln_bias = []
        self.cross_q_weight = []
        self.cross_q_bias = []
        self.cross_k_weight = []
        self.cross_k_bias = []
        self.cross_v_weight = []
        self.cross_v_bias = []
        self.cross_out_weight = []
        self.cross_out_bias = []

        self.ffn_ln_weight = []
        self.ffn_ln_bias = []
        self.ffn_inter_weight = []
        self.ffn_inter_bias = []
        self.ffn_out_weight = []
        self.ffn_out_bias = []

        for mod in model.bart.decoder.decoder.layers:
            self.slf_ln_weight.append(mod.norm1.weight)
            self.slf_ln_bias.append(mod.norm1.bias)
            self.slf_q_weight.append(mod.self_attn.q_proj.weight)
            self.slf_q_bias.append(mod.self_attn.q_proj.bias)
            self.slf_k_weight.append(mod.self_attn.k_proj.weight)
            self.slf_k_bias.append(mod.self_attn.k_proj.bias)
            self.slf_v_weight.append(mod.self_attn.v_proj.weight)
            self.slf_v_bias.append(mod.self_attn.v_proj.bias)
            self.slf_out_weight.append(mod.self_attn.out_proj.weight)
            self.slf_out_bias.append(mod.self_attn.out_proj.bias)

            self.cross_ln_weight.append(mod.norm2.weight)
            self.cross_ln_bias.append(mod.norm2.bias)
            self.cross_q_weight.append(mod.cross_attn.q_proj.weight)
            self.cross_q_bias.append(mod.cross_attn.q_proj.bias)
            self.cross_k_weight.append(mod.cross_attn.k_proj.weight)
            self.cross_k_bias.append(mod.cross_attn.k_proj.bias)
            self.cross_v_weight.append(mod.cross_attn.v_proj.weight)
            self.cross_v_bias.append(mod.cross_attn.v_proj.bias)
            self.cross_out_weight.append(mod.cross_attn.out_proj.weight)
            self.cross_out_bias.append(mod.cross_attn.out_proj.bias)

            self.ffn_ln_weight.append(mod.norm3.weight)
            self.ffn_ln_bias.append(mod.norm3.bias)
            self.ffn_inter_weight.append(mod.linear1.weight)
            self.ffn_inter_bias.append(mod.linear1.bias)
            self.ffn_out_weight.append(mod.linear2.weight)
            self.ffn_out_bias.append(mod.linear2.bias)

        self.decoder_ln_weight = [
            model.decoder.decoder_layernorm_embedding.weight
        ]
        self.decoder_ln_bias = [model.decoder.decoder_layernorm_embedding.bias]

        self.pos_emb = [model.decoder.decoder_embed_positions.weight]
        self.word_emb = [model.decoder.embed_tokens.weight]

        self.linear_weight = [model.lm_head_weight.t()]
        self.linear_bias = [model.final_logits_bias]

    def forward(self,
                enc_output,
                memory_seq_lens,
                beam_size=4,
                top_k=1,
                top_p=0.0,
                decoding_strategy="beam_search_v3",
                max_out_len=256,
                diversity_rate=0.0,
                rel_len=False,
                bos_token_id=None,
                eos_token_id=None,
                pad_token_id=None,
                forced_eos_token_id=None,
                alpha=0.6,
                early_stopping=False):
        # beam_search/beam_search_v2/beam_search_v3 should be corrected to beam_search_v3.
        if decoding_strategy.startswith("beam_search"):
            decoding_strategy = "beam_search_v3"
        elif decoding_strategy == "greedy_search":
            decoding_strategy = "topk_sampling"
            top_k = 1
            top_p = 0.0
        elif decoding_strategy in [
                "sampling", "topk_sampling", "topp_sampling"
        ]:
            if top_p == 1 and top_k > 0:
                decoding_strategy = "topk_sampling"
                top_p = 0.0
            elif top_p > 0 and top_k == 0:
                decoding_strategy = "topp_sampling"
            else:
                raise AttributeError(
                    "Only topk sampling or topp sampling are supported. " \
                    "Topk sampling and topp sampling cannot be both applied in the faster version. ")

        output_ids, parent_ids, sequence_length = infer_bart_decoding(
            [enc_output], [memory_seq_lens], self.word_emb, self.slf_ln_weight,
            self.slf_ln_bias, self.slf_q_weight, self.slf_q_bias,
            self.slf_k_weight, self.slf_k_bias, self.slf_v_weight,
            self.slf_v_bias, self.slf_out_weight, self.slf_out_bias,
            self.cross_ln_weight, self.cross_ln_bias, self.cross_q_weight,
            self.cross_q_bias, self.cross_k_weight, self.cross_k_bias,
            self.cross_v_weight, self.cross_v_bias, self.cross_out_weight,
            self.cross_out_bias, self.ffn_ln_weight, self.ffn_ln_bias,
            self.ffn_inter_weight, self.ffn_inter_bias, self.ffn_out_weight,
            self.ffn_out_bias, self.decoder_ln_weight, self.decoder_ln_bias,
            self.linear_weight, self.linear_bias, self.pos_emb,
            decoding_strategy, beam_size, top_k, top_p, self._n_head,
            int(self._d_model / self._n_head), self._num_decoder_layers,
            bos_token_id, eos_token_id, max_out_len, -diversity_rate, rel_len,
            alpha, early_stopping)

        ids = finalize(
            beam_size,
            output_ids,
            parent_ids,
            sequence_length,
            forced_eos_token_id=forced_eos_token_id,
            decoding_strategy=decoding_strategy)
        return ids


class InferMBartDecoding(nn.Layer):
    def __init__(self,
                 model,
                 decoding_lib=None,
                 use_fp16_decoding=False,
                 hidden_act="gelu"):
        if decoding_lib is not None and os.path.isfile(decoding_lib):
            # Maybe it has been loadad by `ext_utils.load`
            if "FasterTransformer" not in LOADED_EXT.keys():
                ops = paddle.utils.cpp_extension.load_op_meta_info_and_register_op(
                    decoding_lib)
                LOADED_EXT["FasterTransformer"] = ops
        else:
            if decoding_lib is not None:
                logger.warning(
                    "The specified decoding_lib does not exist, and it will be built automatically."
                )
            load("FasterTransformer", verbose=True)

        super(InferMBartDecoding, self).__init__()
        for arg, value in locals().items():
            if arg not in [
                    "self", "model", "word_embedding", "positional_embedding",
                    "linear"
            ]:
                setattr(self, "_" + arg, value)
        self._num_decoder_layers = model.mbart.config['num_decoder_layers']
        self._n_head = model.mbart.config['decoder_attention_heads']
        self._d_model = model.mbart.config['d_model']

        # process weights
        if use_fp16_decoding:
            for mod in model.mbart.decoder.decoder.layers:
                mod.norm1.weight = transfer_param(
                    mod.norm1.weight, restore_data=True)
                mod.norm1.bias = transfer_param(
                    mod.norm1.bias, is_bias=True, restore_data=True)
                mod.self_attn.q_proj.weight = transfer_param(
                    mod.self_attn.q_proj.weight, restore_data=True)
                mod.self_attn.q_proj.bias = transfer_param(
                    mod.self_attn.q_proj.bias, is_bias=True, restore_data=True)
                mod.self_attn.k_proj.weight = transfer_param(
                    mod.self_attn.k_proj.weight, restore_data=True)
                mod.self_attn.k_proj.bias = transfer_param(
                    mod.self_attn.k_proj.bias, is_bias=True, restore_data=True)
                mod.self_attn.v_proj.weight = transfer_param(
                    mod.self_attn.v_proj.weight, restore_data=True)
                mod.self_attn.v_proj.bias = transfer_param(
                    mod.self_attn.v_proj.bias, is_bias=True, restore_data=True)
                mod.self_attn.out_proj.weight = transfer_param(
                    mod.self_attn.out_proj.weight, restore_data=True)
                mod.self_attn.out_proj.bias = transfer_param(
                    mod.self_attn.out_proj.bias,
                    is_bias=True,
                    restore_data=True)

                mod.norm2.weight = transfer_param(
                    mod.norm2.weight, restore_data=True)
                mod.norm2.bias = transfer_param(
                    mod.norm2.bias, is_bias=True, restore_data=True)
                mod.cross_attn.q_proj.weight = transfer_param(
                    mod.cross_attn.q_proj.weight, restore_data=True)
                mod.cross_attn.q_proj.bias = transfer_param(
                    mod.cross_attn.q_proj.bias, is_bias=True, restore_data=True)
                mod.cross_attn.k_proj.weight = transfer_param(
                    mod.cross_attn.k_proj.weight, restore_data=True)
                mod.cross_attn.k_proj.bias = transfer_param(
                    mod.cross_attn.k_proj.bias, is_bias=True, restore_data=True)
                mod.cross_attn.v_proj.weight = transfer_param(
                    mod.cross_attn.v_proj.weight, restore_data=True)
                mod.cross_attn.v_proj.bias = transfer_param(
                    mod.cross_attn.v_proj.bias, is_bias=True, restore_data=True)
                mod.cross_attn.out_proj.weight = transfer_param(
                    mod.cross_attn.out_proj.weight, restore_data=True)
                mod.cross_attn.out_proj.bias = transfer_param(
                    mod.cross_attn.out_proj.bias,
                    is_bias=True,
                    restore_data=True)

                mod.norm3.weight = transfer_param(
                    mod.norm3.weight, restore_data=True)
                mod.norm3.bias = transfer_param(
                    mod.norm3.bias, is_bias=True, restore_data=True)
                mod.linear1.weight = transfer_param(
                    mod.linear1.weight, restore_data=True)
                mod.linear1.bias = transfer_param(
                    mod.linear1.bias, is_bias=True, restore_data=True)
                mod.linear2.weight = transfer_param(
                    mod.linear2.weight, restore_data=True)
                mod.linear2.bias = transfer_param(
                    mod.linear2.bias, is_bias=True, restore_data=True)

            model.decoder.decoder_layernorm_embedding.weight = transfer_param(
                model.decoder.decoder_layernorm_embedding.weight,
                restore_data=True)
            model.decoder.decoder_layernorm_embedding.bias = transfer_param(
                model.decoder.decoder_layernorm_embedding.bias,
                is_bias=True,
                restore_data=True)

            model.decoder.decoder.norm.weight = transfer_param(
                model.decoder.decoder.norm.weight, restore_data=True)
            model.decoder.decoder.norm.bias = transfer_param(
                model.decoder.decoder.norm.bias,
                is_bias=True,
                restore_data=True)

            model.lm_head_weight = transfer_param(
                model.lm_head_weight, restore_data=True)
            model.final_logits_bias = transfer_param(
                model.final_logits_bias, is_bias=True, restore_data=True)

            model.decoder.decoder_embed_positions.weight = transfer_param(
                model.decoder.decoder_embed_positions.weight, restore_data=True)
            model.decoder.embed_tokens.weight = transfer_param(
                model.decoder.embed_tokens.weight, restore_data=True)

        self.slf_ln_weight = []
        self.slf_ln_bias = []
        self.slf_q_weight = []
        self.slf_q_bias = []
        self.slf_k_weight = []
        self.slf_k_bias = []
        self.slf_v_weight = []
        self.slf_v_bias = []
        self.slf_out_weight = []
        self.slf_out_bias = []

        self.cross_ln_weight = []
        self.cross_ln_bias = []
        self.cross_q_weight = []
        self.cross_q_bias = []
        self.cross_k_weight = []
        self.cross_k_bias = []
        self.cross_v_weight = []
        self.cross_v_bias = []
        self.cross_out_weight = []
        self.cross_out_bias = []

        self.ffn_ln_weight = []
        self.ffn_ln_bias = []
        self.ffn_inter_weight = []
        self.ffn_inter_bias = []
        self.ffn_out_weight = []
        self.ffn_out_bias = []

        for mod in model.mbart.decoder.decoder.layers:
            self.slf_ln_weight.append(mod.norm1.weight)
            self.slf_ln_bias.append(mod.norm1.bias)
            self.slf_q_weight.append(mod.self_attn.q_proj.weight)
            self.slf_q_bias.append(mod.self_attn.q_proj.bias)
            self.slf_k_weight.append(mod.self_attn.k_proj.weight)
            self.slf_k_bias.append(mod.self_attn.k_proj.bias)
            self.slf_v_weight.append(mod.self_attn.v_proj.weight)
            self.slf_v_bias.append(mod.self_attn.v_proj.bias)
            self.slf_out_weight.append(mod.self_attn.out_proj.weight)
            self.slf_out_bias.append(mod.self_attn.out_proj.bias)

            self.cross_ln_weight.append(mod.norm2.weight)
            self.cross_ln_bias.append(mod.norm2.bias)
            self.cross_q_weight.append(mod.cross_attn.q_proj.weight)
            self.cross_q_bias.append(mod.cross_attn.q_proj.bias)
            self.cross_k_weight.append(mod.cross_attn.k_proj.weight)
            self.cross_k_bias.append(mod.cross_attn.k_proj.bias)
            self.cross_v_weight.append(mod.cross_attn.v_proj.weight)
            self.cross_v_bias.append(mod.cross_attn.v_proj.bias)
            self.cross_out_weight.append(mod.cross_attn.out_proj.weight)
            self.cross_out_bias.append(mod.cross_attn.out_proj.bias)

            self.ffn_ln_weight.append(mod.norm3.weight)
            self.ffn_ln_bias.append(mod.norm3.bias)
            self.ffn_inter_weight.append(mod.linear1.weight)
            self.ffn_inter_bias.append(mod.linear1.bias)
            self.ffn_out_weight.append(mod.linear2.weight)
            self.ffn_out_bias.append(mod.linear2.bias)

        self.decoder_ln_weight = [model.decoder.decoder.norm.weight]
        self.decoder_ln_bias = [model.decoder.decoder.norm.bias]

        self.mbart_ln_weight = [
            model.decoder.decoder_layernorm_embedding.weight
        ]
        self.mbart_ln_bias = [model.decoder.decoder_layernorm_embedding.bias]

        self.pos_emb = [model.decoder.decoder_embed_positions.weight]
        self.word_emb = [model.decoder.embed_tokens.weight]

        self.linear_weight = [model.lm_head_weight.t()]
        self.linear_bias = [model.final_logits_bias]

    def forward(self,
                enc_output,
                memory_seq_lens,
                trg_word=None,
                beam_size=4,
                top_k=1,
                top_p=0.0,
                decoding_strategy="beam_search_v3",
                max_out_len=256,
                diversity_rate=0.0,
                rel_len=False,
                bos_token_id=None,
                eos_token_id=None,
                pad_token_id=None,
                alpha=0.6,
                temperature=1.0,
                early_stopping=False):
        # Beam_search/beam_search_v2/beam_search_v3 should be corrected to beam_search_v3.
        if decoding_strategy.startswith("beam_search"):
            decoding_strategy = "beam_search_v3"
        elif decoding_strategy == "greedy_search":
            decoding_strategy = "topk_sampling"
            top_k = 1
            top_p = 0.0
        elif decoding_strategy in [
                "sampling", "topk_sampling", "topp_sampling"
        ]:
            if top_p == 1 and top_k > 0:
                decoding_strategy = "topk_sampling"
                top_p = 0.0
            elif top_p > 0 and top_k == 0:
                decoding_strategy = "topp_sampling"
            else:
                raise AttributeError(
                    "Only topk sampling or topp sampling are supported. " \
                    "Topk sampling and topp sampling cannot be both applied in the faster version. ")
        output_ids, parent_ids, sequence_length = infer_mbart_decoding(
            [enc_output], [memory_seq_lens], self.word_emb, self.slf_ln_weight,
            self.slf_ln_bias, self.slf_q_weight, self.slf_q_bias,
            self.slf_k_weight, self.slf_k_bias, self.slf_v_weight,
            self.slf_v_bias, self.slf_out_weight, self.slf_out_bias,
            self.cross_ln_weight, self.cross_ln_bias, self.cross_q_weight,
            self.cross_q_bias, self.cross_k_weight, self.cross_k_bias,
            self.cross_v_weight, self.cross_v_bias, self.cross_out_weight,
            self.cross_out_bias, self.ffn_ln_weight, self.ffn_ln_bias,
            self.ffn_inter_weight, self.ffn_inter_bias, self.ffn_out_weight,
            self.ffn_out_bias, self.decoder_ln_weight, self.decoder_ln_bias,
            self.mbart_ln_weight, self.mbart_ln_bias, self.linear_weight,
            self.linear_bias, self.pos_emb, trg_word, decoding_strategy,
            beam_size, top_k, top_p, self._n_head,
            int(self._d_model / self._n_head), self._num_decoder_layers,
            bos_token_id, eos_token_id, max_out_len, -diversity_rate, rel_len,
            alpha, temperature, early_stopping, self._hidden_act)

        ids = finalize(
            beam_size,
            output_ids,
            parent_ids,
            sequence_length,
            decoding_strategy=decoding_strategy)
        return ids
