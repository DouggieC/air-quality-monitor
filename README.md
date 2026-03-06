
# air-quality-monitor

This app will download data from the IQAir API, particularly regular air quality data concerning the specified city.

## Setup

1. Clone the repository from Github
2. Create and activate a virtual environment:
   ```bash
      cd your_project_root
      python -m venv .venv
      source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
      pip install -r requirements.txt
      pip install -e .
   ```
4. Go to [text](https://dashboard.iqair.com/auth/sign-in?redirectURL=%2Fpersonal%2Fapi-keys) to register for a Community API key
5. Copy `.env.example` to `.env` and customise as required. As a minimum, you will need to add your API key and set the correct BASE_DIR value
   
## Running the app

The app can be run either directly from the command line or as a cronjob.  
To run from the command line:
```bash
   /your/project/root/.venv/bin/python -m air_quality_monitor.main
```  
And as a cronjob:
```cron
   5 * * * * * /your/project/root/scripts/run.sh 2>&1 
```

