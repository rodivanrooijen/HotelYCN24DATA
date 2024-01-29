import pandas as pd

def main():
    df = pd.read_csv("Hotel_Reviews.csv")
    print(df.info())
    print(df.head())
    
if __name__ == "__main__":
    main()