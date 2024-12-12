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

# Do zero-shot document rewrite with an llm
# Usage: rewrite-zeroshot.py [options] <model> <config>

import csv
import re
import sys

import numpy as np
import torch

from pathlib import Path

from jinja2 import Template
#++# from transformers import AutoModelForCausalLM, AutoTokenizer
# Disable stdout logging before importing vllm
import os
os.environ['VLLM_LOGGING_LEVEL'] = 'ERROR'
from vllm import LLM, SamplingParams

def main():
    nameModel = sys.argv[1]
    lenContext = int(sys.argv[2])
    fileConfig = sys.argv[3]
    sizeBatch = 16

    # Load the prompts
    promptSys = None
    promptUser = None
    promptFinal = None
    aStop = []
    with open(fileConfig, 'r', encoding='utf-8') as fp:
        objReader = csv.DictReader(fp)
        for row in objReader:
            print(row, file=sys.stderr)
            value = row['value'].replace("\\n", "\n")
            if row['param'] == 'prompt-sys':
                promptSys = Template(value)
            elif row['param'] == 'prompt-user':
                promptUser = Template(value)
            elif row['param'] == 'prompt-final':
                promptFinal = Template(value)
            elif row['param'] == 'generation-stop':
                aStop.append(value)

    # Get our tokenizer and model
    #++# objTok = AutoTokenizer.from_pretrained(nameModel, padding_side='left')
    #++# objModel = AutoModelForCausalLM.from_pretrained(
    #++#         nameModel,
    #++#         device_map='auto',
    #++#         low_cpu_mem_usage=True,
    #++#         attn_implementation='sdpa'
    #++#         )
    objLLM = LLM(model=nameModel, max_model_len=lenContext, dtype='float32', tensor_parallel_size=torch.cuda.device_count())
    objTok = objLLM.get_tokenizer()

    # Deal with troubles with tokenizers
    if not objTok.pad_token:
        objTok.pad_token = objTok.eos_token # https://huggingface.co/docs/transformers/en/llm_tutorial
    #++# objModel.generation_config.pad_token_id = objTok.pad_token_id
    # Delete contaminations from llama3's default chat templates https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/discussions/74
    objTok.chat_template = re.sub(R'{{- "Cutting Knowledge Date.*?}}\n', "", objTok.chat_template)
    objTok.chat_template = re.sub(R'{{- "Today Date:.*?}}\n', "", objTok.chat_template)

    argSampling = SamplingParams(
            temperature=0.6,
            top_p=0.98,
            frequency_penalty=0.1,
            repetition_penalty=1.1,
            )

    #++# objModel.generation_config.top_p = 0.98
    #++# print(objModel.generation_config, file=sys.stderr)

    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    objReader = csv.DictReader(sys.stdin)
    nameKey = objReader.fieldnames[0]
    nameText = objReader.fieldnames[1]
    objWriter = csv.DictWriter(sys.stdout, (nameKey, nameText), lineterminator="\n")
    objWriter.writeheader()

    def commitBatch(aKeys, aPrompts):
        if len(aKeys) == 0 or len(aPrompts) == 0:
            return
        #++# argPrompts = objTok(aPrompts, padding=True, return_tensors="pt").to(objModel.device)
        #++# rslt = objModel.generate(**argPrompts, max_new_tokens=int(max(len(t) for t in aPrompts)*1.2))
        #++# aOutput = objTok.batch_decode(rslt[:, argPrompts['input_ids'].shape[1]:], skip_special_tokens=True)
        #++# for i in range(len(aOutput)):
        #++#     print(aPrompts[i], file=sys.stderr)
        #++#     objWriter.writerow({nameKey: aKeys[i], nameText: aOutput[i].strip().replace("\n", "\\n")})
        #++#     print(aKeys[i], file=sys.stderr)
        #++#     print(aOutput[i].strip(), file=sys.stderr)
        #print(aPrompts, file=sys.stderr)
        argSampling.max_tokens = int(max(len(t) for t in aPrompts)*1.5)
        argSampling.min_tokens = int(min(len(t) for t in aPrompts)*0.2)
        for i, rslt in enumerate(objLLM.generate(aPrompts, argSampling, use_tqdm=False)):
            output = rslt.outputs[0].text
            for s in aStop:
                output = re.sub(F"{s}.*", "", output, flags=re.DOTALL)
            objWriter.writerow({nameKey: aKeys[i], nameText: output.strip().replace("\n", "\\n")})
        aKeys.clear()
        aPrompts.clear()

    aKeys = []
    aBatch = []
    for row in objReader:
        eid = row[nameKey]
        text = row[nameText].replace("\\n", "\n").strip()

        aChat = []
        mEnv = {'text': text, 'length': len(text)}
        if promptSys:
            aChat.append({'role': 'system', 'content': promptSys.render(mEnv)})
        if promptUser:
            aChat.append({'role': 'user', 'content': promptUser.render(mEnv)})
        if promptFinal:
            aChat.append({'role': 'assistant', 'content': promptFinal.render(mEnv)})
        aKeys.append(eid)
        aBatch.append(objTok.apply_chat_template(aChat, tokenize=False, continue_final_message=True))

        if len(aBatch) >= sizeBatch:
            commitBatch(aKeys, aBatch)
    commitBatch(aKeys, aBatch)

if __name__ == '__main__':
    main()
