#!/usr/bin/env zsh
description="Train a HuBERT classifier"
metaDepScripts=("uc/llm/hubert-train.py")
metaDepOpts=(typeModel nameModel fieldLabel)
avoidRerun=true

setupArgs() {
  opt -r out '' "Output HuBERT"
  optType out output modeldir

  opt -r in '' "Input audio"
  optType in input archive
  opt -r inDev '' "Input audio for development set"
  optType inDev input archive
  opt -r inLabel '' "Input label"
  optType inLabel input table

  opt typeModel "HuBERT" "type of HuggingFace Transformer model"
  opt nameModel "facebook/hubert-large-ls960-ft" "name of HuggingFace base model"

  opt fieldLabel '' "Name of label field. By default the second column"
}

main() {
  local outThis
  out::putDir outThis

  in::load \
  | MORDIOSCRIPTS_FIELD_LABEL=$fieldLabel \
    uc/llm/hubert-train.py "$outThis" "$typeModel" "$nameModel" <(inDev::load) <(inLabel::load)
}

source Mordio/mordio
