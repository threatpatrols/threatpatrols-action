#!/bin/bash

# Top User Agents
# https://github.com/microlinkhq/top-user-agents

curl -O https://raw.githubusercontent.com/microlinkhq/top-user-agents/refs/heads/master/src/mobile.json && \
  curl -O https://raw.githubusercontent.com/microlinkhq/top-user-agents/refs/heads/master/src/desktop.json && \
  date > update-timestamp
