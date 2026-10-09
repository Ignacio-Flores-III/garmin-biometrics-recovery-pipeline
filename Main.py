import pandas as pd
import numpy as np
import re

def parse_duration_to_minutes(val):
    if pd.isna(val) or str(val).strip() == '--':
        return np.nan
    hours = re.search(r'(\d+)\s*h', str(val))
    mins = re.search(r'(\d+)\s*min', str(val))
    h = int(hours.group(1)) if hours else 0
    m = int(mins.group(1)) if mins else 0
    return h * 60 + m

# 1. Load Datasets
df_act = pd.read_excel('GARMIN ACTVITIES .xlsx', sheet_name='Activities')
df_sleep = pd.read_excel('SlEEP.xlsx', sheet_name='Sleep')
df_stress = pd.read_excel('STRESS.xlsx')

# 2. Process Sleep Data
df_sleep.rename(columns={'Sleep Score 4 Weeks': 'Date'}, inplace=True)
df_sleep['Date'] = pd.to_datetime(df_sleep['Date']).dt.date
df_sleep['Sleep_Duration_Min'] = df_sleep['Duration'].apply(parse_duration_to_minutes)
df_sleep['Sleep_Need_Min'] = df_sleep['Sleep Need'].apply(parse_duration_to_minutes)
df_sleep['Sleep_Debt_Min'] = df_sleep['Sleep_Need_Min'] - df_sleep['Sleep_Duration_Min']

# Clean numeric columns containing '--'
for col in ['Score', 'Resting Heart Rate', 'Body Battery', 'HRV Status']:
    df_sleep[col] = pd.to_numeric(df_sleep[col].replace('--', np.nan), errors='coerce')

sleep_clean = df_sleep[['Date', 'Score', 'Resting Heart Rate', 'Body Battery', 
                        'HRV Status', 'Quality', 'Sleep_Duration_Min', 'Sleep_Debt_Min']].copy()
sleep_clean.columns = ['date', 'sleep_score', 'resting_hr', 'body_battery_charge', 
                       'hrv_status', 'sleep_quality', 'sleep_duration_min', 'sleep_debt_min']

# 3. Process Stress Data
df_stress.rename(columns={'Unnamed: 0': 'Date', 'Stress': 'daily_avg_stress'}, inplace=True)
df_stress['date'] = pd.to_datetime(df_stress['Date']).dt.date
stress_clean = df_stress[['date', 'daily_avg_stress']].copy()

# 4. Process & Aggregate Activity Data
df_act['date'] = pd.to_datetime(df_act['Date']).dt.date
df_act['Distance'] = pd.to_numeric(df_act['Distance'], errors='coerce').fillna(0)
df_act['Calories'] = pd.to_numeric(df_act['Calories'], errors='coerce').fillna(0)
df_act['Aerobic TE'] = pd.to_numeric(df_act['Aerobic TE'], errors='coerce').fillna(0)

act_agg = df_act.groupby('date').agg(
    total_distance_mi=('Distance', 'sum'),
    total_active_calories=('Calories', 'sum'),
    max_aerobic_training_effect=('Aerobic TE', 'max'),
    avg_workout_hr=('Avg HR', 'mean'),
    workout_count=('Activity Type', 'count'),
    primary_activity=('Activity Type', lambda x: x.mode()[0] if not x.empty else 'Rest')
).reset_index()

# 5. Join Datasets
master_df = pd.merge(stress_clean, sleep_clean, on='date', how='outer')
master_df = pd.merge(master_df, act_agg, on='date', how='outer')
master_df['total_distance_mi'] = master_df['total_distance_mi'].fillna(0)
master_df['workout_count'] = master_df['workout_count'].fillna(0)
master_df.sort_values(by='date', ascending=True, inplace=True)

# 6. Export Unified File for Tableau
master_df.to_csv('garmin_unified_master.csv', index=False)
print("Pipeline complete. Saved garmin_unified_master.csv")