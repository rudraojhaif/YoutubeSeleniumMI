\# YouTube Multi-Instance Player



A Python script that opens multiple YouTube video instances simultaneously, each with unique browser profiles and fingerprints.



\## Requirements



\- Python 3.12

\- Google Chrome browser installed



\## Installation



Install required packages:

```bash

pip install -r requirements.txt

```



\## Usage



Run the script:

```bash

python youtube\_multiplayer.py

```



The script will ask for:

1\. YouTube URL

2\. Number of instances (1-10)



Note: First time running may take longer as Chrome profiles are created. Subsequent runs will be faster.



\## Features



\- Multiple browser instances with unique fingerprints

\- Isolated Chrome profiles

\- Auto-play video attempts

\- Automatic cleanup of temporary files

\- Real-time instance monitoring



\## How It Works



Each instance creates a temporary Chrome profile with randomized:

\- User agents

\- Window sizes and positions  

\- Debug ports

\- Profile directories



The script uses multi-threading for parallel execution and attempts multiple methods to start video playback automatically.



\## Cleanup



Press Ctrl+C to gracefully close all instances. Profile directories are automatically deleted on exit.

