# Export Management
from organize_paths import myDirectories
data_directories = myDirectories
print_clusters = True
print_slots = True
save_clusters = False
save_PoLs = False
debug = False

# Search Parameters
study_start_date = None         # "YYYY-MM-DD"
study_stop_date = None          # "YYYY-MM-DD"
phase_dr_max = 0.3           # degrees/day
mean_dr_max = 0.1            # degrees/day
min_mode = 5                    # days
max_SK_band = 1.2               # degrees
lookback_period = 30            # days
max_band_separation = 0.08      # degrees
max_geo_alt = 35900000.0   # meters
