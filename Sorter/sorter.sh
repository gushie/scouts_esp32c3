#!/bin/bash
chromium --user-data-dir="/tmp/chrome-dev-disable-security" --disable-web-security --disable-site-isolation-trials --disable-features=BlockInsecurePrivateNetworkRequests,BlockInsecureRequests --allow-running-insecure-content https://editor.p5js.org/j-lying/full/Cz2QZ48Iv
