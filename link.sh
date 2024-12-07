#!/usr/bin/env bash
set -euo pipefail

TARGET="$1"
DIR_COMMONEXP="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

mkdir -pv "$TARGET"

# Assuming zsh-Mordio is in ../zsh-Mordio
if [[ ! -h "$TARGET/Mordio" ]]; then
  ln -sTv "$DIR_COMMONEXP/../zsh-Mordio" "$TARGET/Mordio"
fi

# Link common scripts
if [[ ! -h "$TARGET/sc" ]]; then
  ln -sTv "$DIR_COMMONEXP/steps" "$TARGET/sc"
fi
if [[ ! -h "$TARGET/uc" ]]; then
  ln -sTv "$DIR_COMMONEXP/units" "$TARGET/uc"
fi

# Link specific experiment scripts (if present)
# Usually, it is from the exp-specific link.sh calling this script
if [[ -n "${DIR_SPECIFICEXP-}" ]]; then
  if [[ ! -h "$TARGET/ss" ]]; then
    ln -sTv "$DIR_SPECIFICEXP/steps" "$TARGET/ss"
  fi
  if [[ ! -h "$TARGET/us" ]]; then
    ln -sTv "$DIR_SPECIFICEXP/units" "$TARGET/us"
  fi
  # The reason this is called srun is because I want run.zsh to be auto-completed with just ./ru<tab>
  if [[ ! -h "$TARGET/srun" ]]; then
    ln -sTv "$DIR_SPECIFICEXP/run" "$TARGET/srun"
  fi
  if [[ ! -h "$TARGET/run.zsh" ]]; then
    ln -sTv "srun/run.zsh" "$TARGET/run.zsh"
  fi
fi # End if specific experiment present



# Link the general raw corpora folder
if [[ ! -e "$TARGET/craw" ]]; then
  if [[ -d "$TARGET/../../corpus" ]]; then
    ln -sTv "../../corpus" "$TARGET/craw"
  else
    mkdir -pv "$TARGET/craw"
  fi
fi

# Link the general processed corpus folder
if [[ ! -h "$TARGET/dc" ]]; then
  if [[ -d "$TARGET/../../data" ]]; then
    mkdir -pv "$TARGET/../../data/common-corpus"
    ln -sTv "../../data/common-corpus" "$TARGET/dc"
  else
    mkdir -pv "$TARGET/dc"
  fi
fi

# Link the general model folder
if [[ ! -h "$TARGET/mc" ]]; then
  if [[ -d "$TARGET/../../data" ]]; then
    mkdir -pv "$TARGET/../../data/common-models"
    ln -sTv "../../data/common-models" "$TARGET/mc"
  else
    mkdir -pv "$TARGET/mc"
  fi
fi



# Experiment-specific data
if [[ -n "${DIR_SPECIFICEXP-}" ]]; then
  TGTNAME="$(basename "$TARGET")"

  # Link the data folder
  if [[ ! -e "$TARGET/ds" ]]; then
    if [[ -d "$TARGET/../../data" ]]; then
      mkdir -pv "$TARGET/../../data/$TGTNAME"
      ln -sTv "../../data/$TGTNAME" "$TARGET/ds"
    else
      mkdir -pv "$TARGET/ds"
    fi
  fi

  # Link the results storage
  if [[ ! -e "$TARGET/rslt" ]]; then
    if [[ -d "$TARGET/../../rslt" ]]; then
      mkdir -pv "$TARGET/../../rslt/$TGTNAME"
      ln -sTv "../../rslt/$TGTNAME" "$TARGET/rslt"
    else
      mkdir -pv "$TARGET/rslt"
    fi
  fi
fi # End if specific experiment present

# Binary things
make -C "$DIR_COMMONEXP/src"
if [[ ! -h "$TARGET/bc" ]]; then
  ln -sTv "$DIR_COMMONEXP/bin" "$TARGET/bc"
fi

# Make a "relink" script
if [[ ! -x "$TARGET/link.again.sh" ]]; then
  rm -fv "$TARGET/link.again.sh"
  PATHBASH="$(which bash)"
  cat > "$TARGET/link.again.sh" <<EOF
#!$PATHBASH -v
set -euo pipefail

EOF
  printf "'%s'" "$(readlink -f "$0")" >> "$TARGET/link.again.sh"
  printf " '%s'" "$(readlink -f "$1")" >> "$TARGET/link.again.sh"
  chmod 755 "$TARGET/link.again.sh"
fi

# Make "requirements.txt" for python scripts
(
if [[ -f "$TARGET/uc/requirements.txt" ]]; then
  echo "-r uc/requirements.txt"
fi
if [[ -f "$TARGET/us/requirements.txt" ]]; then
  echo "-r us/requirements.txt"
fi
) > "$TARGET/requirements.txt"

# By default, use a local directory as tmp and log
echo "export TMPDIR=tmp" > "$TARGET/.env"
echo "export HF_HOME=tmp" >> "$TARGET/.env"
echo "export MORDIO_LOGDIR=log" >> "$TARGET/.env"
echo "export TOKENIZERS_PARALLELISM=false" >> "$TARGET/.env"
