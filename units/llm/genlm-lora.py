#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020-2024, Hojin Koh
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

# Do LoRA Training on a training set

import csv
import os
import re
import sys

import torch

from transformers import Trainer, TrainingArguments
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)

# Override some defaults in tqdm: dirty hack
import tqdm.asyncio
from functools import partialmethod
try:
    fpShow = open('/dev/fd/5', 'w', encoding='utf-8')
    tqdm.asyncio.tqdm.__init__ = partialmethod(tqdm.asyncio.tqdm.__init__, file=fpShow)
except:
    pass
finally:
    tqdm.asyncio.tqdm.__init__ = partialmethod(tqdm.asyncio.tqdm.__init__, smoothing=0, mininterval=2, dynamic_ncols=True)

def computeMetricHF(pred):
    aPreds = pred.predictions.argmax(-1)
    aLabels = pred.label_ids
    n = len(aLabels)
    nCorrect = 0
    for i in range(n):
        if aLabels[i] == aPreds[i]:
            nCorrect += 1

    return {
            'acc': 1.0 * nCorrect / n,
            }

def formatSample(objTok, text, ans):
    aMsg = (
        {'role': 'system', 'content': "你是一名摘要撰写人员。阅读全文，理解主要论点、关键信息和结构流程，然后用你自己的话写一个新的、简洁的版本，同时保留原始含义。\n\n简洁地使用简体中文撰写摘要，目标是将长文本浓缩为其重要元素。使用你自己的语言描述思想、论点和信息，而不是引用或仅仅改写原文中的句子。目标是创建一个易于阅读和理解的摘要，即使对于不熟悉原文的人也是如此，同时忠实地呈现其内容和中心信息。\n\n避免使用英文和项目列表。请只使用简体中文，并将长度限制在50字左右，大约2~3句话之内。"},
        {'role': 'user', 'content': F"原始文本如下：\n\n{text}\n\n---\n\n(全文結束)"},
        {'role': 'assistant', 'content': F"（注意：我已将文本浓缩成大约50字左右的摘要。）\n\n搞要如下：\n\n{ans}\n\n---\n\n(摘要结束)"}
    )
    return objTok.apply_chat_template(aMsg, tokenize=False)

class DatasetCompletion(torch.utils.data.Dataset):
    def __init__(self, objTok, mText, mLabel, aOrder):
        self.m_objTok = objTok
        self.m_mText = mText
        self.m_mLabel = mLabel
        self.m_aOrder = aOrder

    def __len__(self):
        return len(self.m_aOrder)

    def __getitem__(self, idx):
        key = self.m_aOrder[idx]
        rtn = {}
        rtn['text'] = formatSample(self.m_objTok, self.m_mText[key], self.m_mLabel[key])
        return rtn

def main():
    fieldRef = os.environ.get('MORDIOSCRIPTS_FIELD_LABEL', '')
    fieldInput = os.environ.get('MORDIOSCRIPTS_FIELD_TEXT', '')

    from datasets import disable_caching
    disable_caching()

    dirOutput = sys.argv.pop(1)
    nameModel = sys.argv.pop(1) # unsloth/Meta-Llama-3.1-8B-Instruct

    mmFileInput = {'train': {}, 'dev': {}}
    mmFileInput['train']['text'] = sys.argv.pop(1)
    mmFileInput['train']['label'] = sys.argv.pop(1)
    mmFileInput['dev']['text'] = sys.argv.pop(1)
    mmFileInput['dev']['label'] = sys.argv.pop(1)

    # Get our tokenizer and save a copy—will need it later
    objTok = AutoTokenizer.from_pretrained(nameModel, use_fast=True, do_lower_case=False, clean_up_tokenization_spaces=False)
    # Delete garbage from llama3's default chat templates https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/discussions/74
    objTok.chat_template = re.sub(R'{{- "Cutting Knowledge Date.*?}}\n', "", objTok.chat_template)
    objTok.chat_template = re.sub(R'{{- "Today Date:.*?}}\n', "", objTok.chat_template)
    objTok.save_pretrained(dirOutput)

    # Load model
    objModel = AutoModelForCausalLM.from_pretrained(
            nameModel,
            low_cpu_mem_usage=True,
            device_map="auto",
    )

    # Load all data
    mmText = {'train': {}, 'dev': {}}
    mmLabel = {'train': {}, 'dev': {}}

    for ss in mmFileInput:
        for f, tgt in ((mmFileInput[ss]['text'], mmText[ss]), (mmFileInput[ss]['label'], mmLabel[ss])):
            with open(f, 'r', encoding='utf-8') as fp:
                objReader = csv.DictReader(fp)
                fieldKey = objReader.fieldnames[0]
                fieldData = objReader.fieldnames[1]
                for row in objReader:
                    tgt[row[fieldKey]] = row[fieldData].replace('\\n', '\n')
    maOrder = {k: list(mmText[k].keys()) for k in mmText}

    from datasets import Dataset

    datasetTrain = Dataset.from_list(DatasetCompletion(objTok, mmText['train'], mmLabel['train'], maOrder['train']))
    datasetDev = Dataset.from_list(DatasetCompletion(objTok, mmText['dev'], mmLabel['dev'], maOrder['dev']))

    print("Train Sample Size: {}".format(len(datasetTrain)), file=sys.stderr)
    print("Validation Sample Size: {}".format(len(datasetDev)), file=sys.stderr)
    print(datasetDev[0]['text'])

    # TO BE REPLACED LATER
    from trl import DataCollatorForCompletionOnlyLM

    collator = DataCollatorForCompletionOnlyLM("摘要如下：\n\n", tokenizer=objTok)

    from peft import (
        LoraConfig,
        TaskType,
        get_peft_model,
        prepare_model_for_kbit_training
    )

    # this is recommended by original lora paper: using lora, we should target the linear layers only
    confLora = LoraConfig(
        r=32,  # rank for matrix decomposition
        lora_alpha=16,
        target_modules=[
            "self_attn.q_proj",
            "self_attn.k_proj",
            "self_attn.v_proj",
            "self_attn.o_proj",
            "mlp.gate_proj",
            "mlp.up_proj",
            "mlp.down_proj"
        ],
        lora_dropout=0.05,
        bias='none',
        task_type=TaskType.CAUSAL_LM
    )

    objLora = get_peft_model(objModel, confLora)

    from trl import SFTConfig, SFTTrainer

    confSFT = SFTConfig(
        output_dir=F'tmp/hfoutputs-berttrain-{os.getpid()}',
        save_strategy='steps',
        save_steps=0.2,  # save every 20% of the trainig steps
        save_total_limit=2,
        load_best_model_at_end=True,
        eval_on_start=False,
        eval_strategy='steps',
        eval_steps=0.2,  # evalaute every 20% of the trainig steps
        logging_dir=F'tmp/hfoutputs-berttrain-{os.getpid()}',
        logging_first_step=True,
        logging_steps=10,

        dataset_text_field='text',  # this is the final text example we formatted
        max_seq_length=3000,
        num_train_epochs=1,
        auto_find_batch_size=True,
        per_device_train_batch_size=1,  # training batch size
        per_device_eval_batch_size=1,  # eval batch size
        gradient_accumulation_steps=8,  # by using gradient accum, we updating weights every: batch_size * gradient_accum_steps = 4 * 2 = 8 steps

        #optim="paged_adamw_8bit",  # paged adamw
        learning_rate=1e-4,
        warmup_ratio=0.1,  # learning rate warmup
        bf16=True,
        #fsdp=True,
        lr_scheduler_type="cosine",  # scheduler
        save_safetensors=True,  # saving to safetensors
        dataset_kwargs={
            "add_special_tokens": False,  # we template with special tokens already
            "append_concat_token": False,  # no need to add additional sep token
        },

        label_names=["labels"], # workaround weird warning
    )

    objTrainer = SFTTrainer(
        model=objLora,
        args=confSFT,
        processing_class=objTok,
        train_dataset=datasetTrain,
        eval_dataset=datasetDev,
        data_collator=collator,
    )

    #print(objTrainer.evaluate(), file=sys.stderr)
    print("BEGIN TRAINING", file=sys.stderr)
    objTrainer.train()
    #print(objTrainer.evaluate(), file=sys.stderr)

    objTrainer.save_model(dirOutput)
    print("Best model saved: {}".format(dirOutput), file=sys.stderr)

if __name__ == '__main__':
    main()
