# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors.
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


import os
import unittest

from transformers.file_utils import cached_property
from transformers.testing_utils import require_torch, slow
from transformers.tokenization_reformer import SPIECE_UNDERLINE, ReformerTokenizer

from .test_tokenization_common import TokenizerTesterMixin


SAMPLE_VOCAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures/test_sentencepiece.model")


class ReformerTokenizationTest(TokenizerTesterMixin, unittest.TestCase):

    tokenizer_class = ReformerTokenizer

    def setUp(self):
        super().setUp()

        tokenizer = ReformerTokenizer(SAMPLE_VOCAB, keep_accents=True)
        tokenizer.save_pretrained(self.tmpdirname)

    def test_full_tokenizer(self):
        tokenizer = ReformerTokenizer(SAMPLE_VOCAB, keep_accents=True)

        tokens = tokenizer.tokenize("This is a test")
        self.assertListEqual(tokens, ["▁This", "▁is", "▁a", "▁t", "est"])

        self.assertListEqual(
            tokenizer.convert_tokens_to_ids(tokens), [285, 46, 10, 170, 382],
        )

        tokens = tokenizer.tokenize("I was born in 92000, and this is falsé.")
        self.assertListEqual(
            tokens,
            [
                SPIECE_UNDERLINE + "I",
                SPIECE_UNDERLINE + "was",
                SPIECE_UNDERLINE + "b",
                "or",
                "n",
                SPIECE_UNDERLINE + "in",
                SPIECE_UNDERLINE + "",
                "9",
                "2",
                "0",
                "0",
                "0",
                ",",
                SPIECE_UNDERLINE + "and",
                SPIECE_UNDERLINE + "this",
                SPIECE_UNDERLINE + "is",
                SPIECE_UNDERLINE + "f",
                "al",
                "s",
                "é",
                ".",
            ],
        )
        ids = tokenizer.convert_tokens_to_ids(tokens)
        self.assertListEqual(
            ids, [8, 21, 84, 55, 24, 19, 7, 0, 602, 347, 347, 347, 3, 12, 66, 46, 72, 80, 6, 0, 4],
        )

        back_tokens = tokenizer.convert_ids_to_tokens(ids)
        self.assertListEqual(
            back_tokens,
            [
                SPIECE_UNDERLINE + "I",
                SPIECE_UNDERLINE + "was",
                SPIECE_UNDERLINE + "b",
                "or",
                "n",
                SPIECE_UNDERLINE + "in",
                SPIECE_UNDERLINE + "",
                "<unk>",
                "2",
                "0",
                "0",
                "0",
                ",",
                SPIECE_UNDERLINE + "and",
                SPIECE_UNDERLINE + "this",
                SPIECE_UNDERLINE + "is",
                SPIECE_UNDERLINE + "f",
                "al",
                "s",
                "<unk>",
                ".",
            ],
        )

    @cached_property
    def big_tokenizer(self):
        return ReformerTokenizer.from_pretrained("google/reformer-crime-and-punishment")

    @slow
    def test_tokenization_base_easy_symbols(self):
        symbols = "Hello World!"
        original_tokenizer_encodings = [126, 32, 262, 152, 38, 72, 287]

        self.assertListEqual(original_tokenizer_encodings, self.big_tokenizer.encode(symbols))

    @slow
    def test_tokenization_base_hard_symbols(self):
        symbols = 'This is a very long text with a lot of weird characters, such as: . , ~ ? ( ) " [ ] ! : - . Also we will add words that should not exsist and be tokenized to <unk>, such as saoneuhaoesuth'
        original_tokenizer_encodings = [
            108,
            265,
            24,
            111,
            4,
            258,
            156,
            35,
            28,
            275,
            3,
            259,
            297,
            260,
            84,
            4,
            35,
            110,
            44,
            8,
            259,
            91,
            268,
            21,
            11,
            209,
            274,
            109,
            266,
            277,
            117,
            86,
            93,
            315,
            258,
            278,
            258,
            277,
            258,
            0,
            258,
            288,
            258,
            319,
            258,
            0,
            258,
            0,
            258,
            0,
            258,
            0,
            258,
            287,
            258,
            315,
            258,
            289,
            258,
            278,
            99,
            269,
            266,
            262,
            8,
            259,
            241,
            4,
            217,
            230,
            268,
            266,
            55,
            168,
            106,
            75,
            193,
            266,
            223,
            27,
            49,
            26,
            282,
            25,
            264,
            299,
            19,
            26,
            0,
            258,
            277,
            117,
            86,
            93,
            176,
            183,
            270,
            11,
            262,
            42,
            61,
            265,
        ]

        self.assertListEqual(original_tokenizer_encodings, self.big_tokenizer.encode(symbols))

    @slow
    @require_torch
    def test_torch_encode_plus_sent_to_model(self):
        import torch
        from transformers import ReformerModel, ReformerConfig

        # Build sequence
        first_ten_tokens = list(self.big_tokenizer.get_vocab().keys())[:10]
        sequence = " ".join(first_ten_tokens)
        encoded_sequence = self.big_tokenizer.encode_plus(sequence, return_tensors="pt")
        batch_encoded_sequence = self.big_tokenizer.batch_encode_plus([sequence, sequence], return_tensors="pt")

        config = ReformerConfig()
        # The input gets padded during training so adjust the axial position encodings from the pretrained model value of (512, 1024)
        config.axial_pos_shape = encoded_sequence["input_ids"].shape
        model = ReformerModel(config)

        # Reformer has config.vocab_size == tokenizer.vocab_size == len(tokenizer) - 1 = 320; len(tokenizer) is 321 (including a pad token with id 320)
        assert model.get_input_embeddings().weight.shape[0] >= self.big_tokenizer.vocab_size

        with torch.no_grad():
            model(**encoded_sequence)
            model(**batch_encoded_sequence)
