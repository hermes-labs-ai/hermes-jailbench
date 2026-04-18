#!/usr/bin/env bash
# Set jailbreak-bench GitHub repo metadata. Run ONCE after the repo is public.
# DO NOT run while the repo is still private - description and topics set now
# get indexed immediately after public flip.

gh repo edit roli-lpci/jailbreak-bench \
  --description "Regression test suite for LLM safety: 45 patterns, 8 categories, 251 tests. Commit-to-git refusal rate per model release. Hermes Labs." \
  --homepage "https://hermes-labs.ai" \
  --add-topic llm \
  --add-topic llm-safety \
  --add-topic ai-audit \
  --add-topic red-team \
  --add-topic regression-testing \
  --add-topic anthropic \
  --add-topic claude \
  --add-topic hermes-labs \
  --add-topic python-cli \
  --add-topic eu-ai-act
