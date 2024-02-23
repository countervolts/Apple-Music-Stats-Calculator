# Stat Calculator
## How to request your Apple Music Data
1. Go to https://privacy.apple.com/
2. Login to your AppleID
3. Click “Obtain a copy of your data”
4. Only select “Apple Media services”
5. Scroll down and click the blue “continue” button

## How to use the code
1. run ```git clone https://github.com/countervolts/Apple-Music-Stats-Calculator```
2. make sure that your "Apple Music - Play History Daily Tracks.csv" is in same folder as the stat calculator (should be ```C:\Users\<username>\Apple-Music-Stats-Calculator```)
3. run ```cd Apple-Music-Stats-Calculator```
4. run ```pip install -r requirements.txt```
5. run ```python reader.py```
6. when ran it should print "Pick a CSV: " if it says that and the Play History csv is in the folder press 1
7. allow it to process the streams (this should take a couple seconds)
8. when done it will print your top 10 artists as well as you top 10 songs, if you type "y" to writing a stats.txt file it will contain more information and save in the same directory

## Examples
1. [command prompt output](https://github.com/countervolts/Apple-Music-Stats-Calculator/blob/main/examples/top10.txt)
2. [full stats.txt output](https://github.com/countervolts/Apple-Music-Stats-Calculator/blob/main/examples/Stats.txt)

## Support
my discord is [._ayo](https://discord.com/users/488368000055902228) <--- or just click the link

## **DISCLAIMER**
this isnt the perfect stats calculator here is by about how much each thing MIGHT be off by
```
Total Streams: ~20.61%
Minutes Streamed: ~16.25%
Hours Streamed: ~16.22%
Different Artists: ~36.88%
Different Songs: ~30.86%
```
