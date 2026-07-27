import os
import sys
import urllib.request
import pandas as pd

# Dataset configuration for OGLE-III survey files
DATASETS = {
    "Cepheid": {
        "url": "https://ftp.astrouw.edu.pl/ogle/ogle3/OIII-CVS/lmc/cep/cepF.dat",
        "filename": "cepF.dat",
        "amp_col": 6
    },
    "RR Lyrae": {
        "url": "https://ftp.astrouw.edu.pl/ogle/ogle3/OIII-CVS/lmc/rrlyr/RRab.dat",
        "filename": "RRab.dat",
        "amp_col": 6
    },
    "Mira": {
        "url": "https://ftp.astrouw.edu.pl/ogle/ogle3/OIII-CVS/lmc/lpv/Miras.dat",
        "filename": "Miras.dat",
        "amp_col": 6
    },
    "Eclipsing Binary": {
        "url": "https://ftp.astrouw.edu.pl/ogle/ogle3/OIII-CVS/lmc/ecl/ecl.dat",
        "filename": "ecl.dat",
        "amp_col": 5
    }
}

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "stars_dataset.csv")

def main():
    print("Loading raw OGLE-III datasets...")
    download_raw_data()

    cleaned_dfs = []
    for star_type, config in DATASETS.items():
        print(f"Cleaning {star_type} data...")
        df = clean_file(star_type, config)
        cleaned_dfs.append(df)

    print("Merging and balancing dataset...")
    master_df = balance_and_merge(cleaned_dfs, samples_per_class=1500)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    master_df.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 60)
    print(f"Data cleaning complete! Saved to {OUTPUT_FILE}")
    print(f"Total rows: {len(master_df)}")
    print("Class distribution:")
    print(master_df["star_type"].value_counts().to_string())
    print("=" * 60)


def download_raw_data():
    """
    Downloads raw .dat catalog files from OGLE-III FTP server
    if they do not already exist locally in data/raw/.
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    for star_type, config in DATASETS.items():
        filepath = os.path.join(RAW_DIR, config["filename"])
        if not os.path.exists(filepath):
            print(f"  Downloading {config['filename']}...")
            urllib.request.urlretrieve(config["url"], filepath)


def clean_file(star_type, config):
    """
    Reads space-delimited text file for a given star category, extracts 
    relevant physical features, converts columns to numeric types, calculates 
    V_minus_I_color (V - I), drops missing values, and returns a clean DataFrame.
    """
    filepath = os.path.join(RAW_DIR, config["filename"])

    df = pd.read_csv(filepath, sep=r'\s+', header=None, comment='#')

    i_mag = pd.to_numeric(df[1], errors='coerce')
    v_mag = pd.to_numeric(df[2], errors='coerce')
    period = pd.to_numeric(df[3], errors='coerce')
    amp = pd.to_numeric(df[config["amp_col"]], errors='coerce')

    clean_df = pd.DataFrame({
        "I_magnitude": i_mag,
        "period_days": period,
        "I_band_amplitude": amp,
        "V_minus_I_color": v_mag - i_mag,
        "star_type": star_type
    })

    return clean_df.dropna()


def balance_and_merge(dataframes, samples_per_class=1500):
    """
    Subsamples each DataFrame in dataframes to at most samples_per_class 
    rows (using random_state=42) and concatenates them into a single 
    master DataFrame.
    """
    balanced_dfs = []

    for df in dataframes:
        if len(df) > samples_per_class:
            df = df.sample(n=samples_per_class, random_state=42)

        balanced_dfs.append(df)

    return pd.concat(balanced_dfs, ignore_index=True)


if __name__ == "__main__":
    main()
