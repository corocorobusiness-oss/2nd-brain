#!/bin/bash
# Claude再起動スクリプト
# Discord経由で呼ばれる。KeepAlive=trueのlaunchdが自動で再起動する。

sleep 2
pkill -f "claude --channels"
