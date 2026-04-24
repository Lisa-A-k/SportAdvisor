# SportAdvisor

SportAdvisor is a Streamlit application that helps a user:

- fill in a personal sports profile;
- Take a psychological test to choose the right sport;
- Assess your physical profile;
- Receive more personalized recommendations based on your health, training conditions, and equipment;
- Maintain a training calendar and brief monthly statistics.

## Stack

- Python
- Streamlit
- Pandas
- Matplotlib
- NumPy

## Project structure

`main/app.py` - Streamlit UI

`main/data.py` - dictionaries and static app data

`main/logic.py` - recommendation engine, physical scoring, monthly planning

`main/storage.py` - session state initialization, import/export helpers

## What's improved

- recommendation logic now uses health group, training environment, equipment and physical profile;
- adult health groups `IIIa` and `IIIb` are normalized correctly;
- monthly statistics are shown consistently and no longer disappear after progress history appears;
- the original monolithic file is split into smaller modules for easier maintenance.

## Run locally

```bash
pip install -r requirements.txt
streamlit run main/app.py
```
