import pandas as pd
import logging
import plotly.express as px
import string
import numpy as np

logging.basicConfig(level=10)

import sort_dataframeby_monthorweek as sd
import mysql.connector
import requests
from xgboost import XGBClassifier
import re
from sklearn.feature_selection import SelectKBest, f_classif
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.ensemble import RandomForestClassifier


def sort_month(df, column_name):
    return sd.Sort_Dataframeby_Month(df, column_name)


def main(show=False) -> None:
    df: pd.DataFrame = pd.read_csv("hotel_bookings.csv")
    logging.info(df.info())
    null = pd.DataFrame(
        {
            "Null Values": df.isna().sum(),
            "Percentage Null Values": (df.isna().sum()) / (df.shape[0]) * (100),
        }
    )
    logging.info(null)
    df.fillna(0, inplace=True)

    df = df[~((df["children"] == 0) & (df["adults"] == 0) & (df["babies"] == 0))]

    logging.info(df.head())
    df["guest_count"] = (df["adults"] + df["children"] + df["babies"]).astype(int)

    df["total_nights"] = (
        df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    ).astype(int)

    df_country_count: pd.DataFrame = (
        df[df["is_canceled"] == 0]
        .groupby("country")
        .size()
        .sort_values()
        .reset_index(name="country_count")
    )

    df_resort_avg_price_room_type: pd.DataFrame = (
        df[(df["is_canceled"] == 0) & (df["hotel"] == "Resort Hotel")]
        .groupby("assigned_room_type")["adr"]
        .mean()
        .reset_index()
        .sort_values(by="assigned_room_type")
    )
    df_resort_avg_price_month: pd.DataFrame = sort_month(
        (
            df[(df["is_canceled"] == 0) & (df["hotel"] == "Resort Hotel")]
            .groupby("arrival_date_month")["adr"]
            .mean()
            .reset_index()
        ),
        "arrival_date_month",
    )

    df_city_avg_price_room_type: pd.DataFrame = (
        df[(df["is_canceled"] == 0) & (df["hotel"] == "City Hotel")]
        .groupby("assigned_room_type")["adr"]
        .mean()
        .reset_index()
        .sort_values(by="assigned_room_type")
    )

    df_city_avg_price_month: pd.DataFrame = sort_month(
        (
            df[(df["is_canceled"] == 0) & (df["hotel"] == "City Hotel")]
            .groupby("arrival_date_month")["adr"]
            .mean()
            .reset_index()
        ),
        "arrival_date_month",
    )

    df_city_guest_count_month: pd.DataFrame = sort_month(
        (
            df[(df["is_canceled"] == 0) & (df["hotel"] == "City Hotel")]
            .groupby("arrival_date_month")["guest_count"]
            .sum()
            .sort_values()
            .reset_index()
            .rename(columns={"guest_count": "guest_count_city"})
        ),
        "arrival_date_month",
    )

    df_resort_guest_count_month: pd.DataFrame = sort_month(
        (
            df[(df["is_canceled"] == 0) & (df["hotel"] == "Resort Hotel")]
            .groupby("arrival_date_month")["guest_count"]
            .sum()
            .sort_values()
            .reset_index()
            .rename(columns={"guest_count": "guest_count_resort"})
        ),
        "arrival_date_month",
    )

    df_guest_count_month = df_city_guest_count_month.merge(
        df_resort_guest_count_month, how="inner", on="arrival_date_month"
    )

    logging.info(df_guest_count_month)

    df_stay_count = (
        df[(df["is_canceled"] == 0)]
        .groupby(["hotel", "total_nights"])
        .size()
        .reset_index(name="stay_count")
    )
    logging.info(df_stay_count)

    df_correlation: pd.DataFrame = (
        df.corr(numeric_only=True)["is_canceled"].abs().sort_values(ascending=False)
    )
    logging.info(df_correlation)

    if show:
        guests_map = px.choropleth(
            df_country_count,
            locations=df_country_count["country"],
            color=df_country_count["country_count"],
            hover_name=df_country_count["country"],
        )
        guests_map.show()
        guest_per_month = px.line(
            df_guest_count_month,
            x="arrival_date_month",
            y=["guest_count_resort", "guest_count_city"],
            title="Total no of guests per Months",
            template="plotly_dark",
        )
        guest_per_month.show()


def sql_test():
    mydb = mysql.connector.connect(
        host="localhost",  # port erbij indien mac
        user="root",
        password="",
        database="project_yc2401",
    )

    mycursor = mydb.cursor()

    myresult = mycursor.fetchall()
    print(myresult)


# def datafinity_api():

#     # Set your API parameters here.
#     API_token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ6ZDI5Ym9kdW11MXZqcjd5eGRhdzlrb3p6YmUzbnJwYyIsImlzcyI6ImRhdGFmaW5pdGkuY28ifQ.HCv7XTnOOBghpXj2aIeZLl4UyyeOArSp_grbQlD1WfmXCdcdK-BLWdCkBjahNg76mXrQTr4MUdu3gTQQYRfCnTGAmSuq4FGm6a1sxjWyjzGCaYc1y3sG07QUmcA-DfYRWFWYjfMheLaLv2MqIjBsXyD16HazDY4ISZmFGN-J9wx80oFiQOUFVYqGTEeLAJ_AmH8fTyQ8NC4dCWu9APRl6ZHugegxMqkIWpav_rykTUFH7B8--FeFsTeRdfGCsxTtALPeBG29oUSsN5Ggxd_V0BQlv04aKyBj2aDWwfY7v6wMFqXqf8U-D1jZOHY8CCeHKV2X55RmVZbS75avKrdywEbob9LMpo9CGq7YaH6dmcxA0g0iyefHNDhdQz7of9oS9sI0tx1Lkg775SQYE2eyrmp03ZDzUUpj7KxombbHrPw2i95jRzprnPvsOWZbp8uXFpsbwwqfw4FR8FUar40zojYloYrnvIBWZXsp5cukvfv5El1JmqNDzR6Aa1VbzMZ4hwsnEV1PoVueAXMd8BhjqqdF8waKt9VO1ZQ8vtl862-eUAKLlQTJBl5JBIpf94w4oBJJeLXSkPDf9oPMZJ34WuTFyaXkvQyL5EmOKVwwnWTAb2ynM5upM5lsDtz_LNUOGhc3AY5zN5S1xjZFq_ktkmUm5irg7Fa0kEoO_eq5fr0'
#     format = 'JSON'
#     query = 'categories:hotels'
#     num_records = 300
#     download = False

#     request_headers = {
#         'Authorization': 'Bearer ' + API_token,
#         'Content-Type': 'application/json',
#     }
#     request_data = {
#         'query': query,
#         'format': format,
#         'num_records':num_records
#     }

#     # Make the API call.
#     r = requests.post('https://api.datafiniti.co/v4/businesses/search',json=request_data,headers=request_headers);


#     # Do something with the response.
#     if r.status_code == 200:
#         req:dict = r.json().get("records")
#         print(len(req))
#         # df:pd.DataFrame = pd.DataFrame(req)
#         # df.to_csv("hotel_records.csv", header=True, index=False, sep=";")
#     else:
#         print('Request failed')
def test():
    url = "https://tourist-attraction.p.rapidapi.com/currencies"

    headers = {
        "X-RapidAPI-Key": "5744310ef3mshbd60ec185d882d9p19e561jsne06bad0614ac",
        "X-RapidAPI-Host": "tourist-attraction.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers)

    print(response.json())


def extract_integers_with_letter(s):
    # Regular expression to match integers followed by an optional letter
    pattern = r"\b\d+[a-zA-Z]?\b"

    # Find all matches
    if len(re.findall(pattern, s)) == 0:
        return ""
    return re.findall(pattern, s)[0]


# Example usage
def extract_house_number(address):
    match = re.search(r"\b\d+[a-zA-Z]?\b", address)
    return match.group(0) if match else None


# Function to extract street name
def extract_street_name(address):
    return re.sub(r"\b\d+[a-zA-Z]?\b", "", address).strip()


def remove_text_after_comma(s):
    # Regular expression to match a comma and everything after it
    pattern = r",.*$"

    # Replace the matched pattern with an empty string
    return re.sub(pattern, "", s)


def read_file():
    df = pd.read_csv("238320_1.csv")
    df.dropna(axis="columns", how="all", inplace=True)
    df.drop(
        [
            "rooms",
            "cuisines",
            "emails",
            "productsOrServices",
            "priceRangeCurrency",
            "priceRangeMin",
            "priceRangeMax",
        ],
        axis=1,
        inplace=True,
    )
    hotel_df = df[["address", "city", "country", "name", "latitude", "longitude"]]
    hotel_df["house_number"] = hotel_df["address"].apply(extract_house_number)
    hotel_df["street"] = (
        hotel_df["address"].apply(extract_street_name).apply(remove_text_after_comma)
    )

    print(hotel_df["house_number"])
    print(hotel_df["street"])


def format_date(date_str):
    if "-" in date_str:
        new_str = date_str.split("-")
        new_lst = []
        new_lst.insert(0, new_str[1])
        new_lst.insert(1, new_str[2])
        new_lst.insert(2, new_str[0])
        return "/".join(new_lst)
    return date_str

def find_day(date_str):
    return int(date_str.split("/")[1])

def find_month(date_str):
    return int(date_str.split("/")[0])

def find_year(date_str):
    return int(date_str.split("/")[2])

alphabet_dict = {letter: index for index, letter in enumerate(string.ascii_uppercase, start=1)}
months = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]

# Create a dictionary where each month name is mapped to its position in the year
months_dict = {month: index for index, month in enumerate(months, start=1)}


def assign_room_type(room_letter):
    new_str = alphabet_dict[room_letter]
    return f"Room_Type {new_str}"
def assign_month_number(month_str):
    return months_dict[month_str]

def hotel_bookings():
    df: pd.DataFrame = pd.read_csv("hotel_bookings.csv")

    df.fillna(0, inplace=True)

    df = df[~((df["children"] == 0) & (df["adults"] == 0) & (df["babies"] == 0))]

    logging.info(df.head())
    df["children"] = (df["children"] + df["babies"]).astype(int)

    df.drop(
        [
            "hotel",
            "babies",
            "country",
            "assigned_room_type",
            "booking_changes",
            "deposit_type",
            "agent",
            "company",
            "days_in_waiting_list",
            "customer_type",
            "reservation_status",
            "reservation_status_date",
            "distribution_channel"
        ],
        axis=1,
        inplace=True,
    )
    df = df.rename(
        columns={
            "arrival_date_year": "year",
            "arrival_date_month": "month",
            "arrival_date_day_of_month": "day",
            "is_canceled": "booking status",
            "adr": "average price",
            "market_segment": "market segment type",
            "is_repeated_guest": "repeated",
            "previous_cancellations": "P-C",
            "previous_bookings_not_canceled": "P-not-C",
            "required_car_parking_spaces": "car parking space",
            "meal": "type of meal",
            "reserved_room_type": "room type",
            "lead_time": "lead time",
            "total_of_special_requests":"special requests",
            "adults":"number of adults",
            "children":"number of children",
            "stays_in_weekend_nights": "number of weekend nights",
            "stays_in_week_nights": "number of week nights",
        }
    )
    df = df[['number of adults', 'number of children', 'number of weekend nights',
       'number of week nights', 'type of meal', 'car parking space',
       'room type', 'lead time', 'market segment type', 'repeated', 'P-C',
       'P-not-C', 'average price', 'special requests', 'booking status', 'day',
       'month', 'year']]
    df["month"] = df["month"].apply(assign_month_number)
    df["market segment type"] = df["market segment type"].apply(lambda x: x.split(" ")[0])
    
    df["room type"] = df["room type"].apply(assign_room_type)
    df["type of meal"] = df["type of meal"].replace("BB", "Meal Plan 1")
    df["type of meal"] = df["type of meal"].replace("Undefined", "Not Selected")
    df["type of meal"] = df["type of meal"].replace("SC", "Not Selected")
    df["type of meal"] = df["type of meal"].replace("HB", "Meal Plan 2")
    df["type of meal"] = df["type of meal"].replace("FB", "Meal Plan 3")
    print(df.columns)
    print(df["room type"])
    print(df["type of meal"])
    return df


def bookings():
    df = pd.read_csv("booking.csv")
    df["date of reservation"] = df["date of reservation"].apply(format_date)

    df["day"] = df["date of reservation"].apply(find_day)
    df["month"] = df["date of reservation"].apply(find_month)
    df["year"] = df["date of reservation"].apply(find_year)

    df.drop(["Booking_ID", "date of reservation"], axis=1, inplace=True)
    df["booking status"] = df["booking status"].replace("Canceled", 1)
    df["booking status"] = df["booking status"].replace("Not_Canceled", 0)

    print(df.columns)
    return df

def model():
    df1 = bookings()
    df2 = hotel_bookings()
    df3 = pd.concat([df2])
    df3.drop_duplicates(inplace=True, ignore_index=True)
    df3["average price"] = df3["average price"].round().astype(int)
    object_columns = df3.select_dtypes(include=["object"]).columns
    df3 = pd.get_dummies(df3, columns=object_columns)
    df3 = df3.replace({True: 1, False: 0})
    print(df3.info())

    # plt.figure(figsize=(12, 8))
    # sns.heatmap(df3.corr(), cmap="icefire", linewidths=0.5)
    # plt.title("Correlation Heatmap")
    # plt.show()
    
    
    scores = {}

    features = df3.drop(["booking status"], axis=1)
    target = df3["booking status"]

    k_best = SelectKBest(score_func=f_classif, k=10)

    X = k_best.fit_transform(features, target)
    y = target

    # Get the indices of the selected features
    selected_features_indices = k_best.get_support(indices=True)

    # Get the scores associated with each feature
    feature_scores = k_best.scores_

    # Create a list of tuples containing feature names and scores
    feature_info = list(zip(features.columns, feature_scores))

    # Sort the feature info in descending order based on scores
    sorted_feature_info = sorted(feature_info, key=lambda x: x[1], reverse=True)

    for feature_name, feature_score in sorted_feature_info[:10]:
        print(f"{feature_name}: {feature_score:.2f}")
    feature_names, feature_scores = zip(*sorted_feature_info[:])

    # Create a bar chart
    # plt.figure(figsize=(10, 6))
    # plt.barh(feature_names, feature_scores, color="skyblue")
    # plt.xlabel("Feature Importance Score")
    # plt.title("Features Importance Scores")
    # plt.show()
    
    selected_features_df = features.iloc[:, selected_features_indices]
    
    X_train, X_test, y_train, y_test = train_test_split(
    X, target, test_size=0.2, random_state=5
    )
    dt = DecisionTreeClassifier()

    params = {"max_depth": np.arange(0, 30, 5), "criterion": ["gini", "entropy"]}

    grid_search = GridSearchCV(dt, param_grid=params, cv=5)
    grid_search.fit(X_train, y_train)
    print(f"Best Parameters: {grid_search.best_params_}")
    print(f"Best Score: {grid_search.best_score_}")

    best_dt = grid_search.best_estimator_

    y_pred = best_dt.predict(X_test)

    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    scores["Decision Tree"] = accuracy_score(y_test, y_pred)
    print("---------------------------------------------------------")
    print(f"Confusion Matrix: \n{confusion_matrix(y_test, y_pred)}")
    # sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, cmap="Blues", fmt=".0f")
    print("---------------------------------------------------------")
    print(f"Classification Report: \n{classification_report(y_test, y_pred)}")
    
    rf = RandomForestClassifier(max_depth=20, n_estimators=20)

    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)

    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    scores["Random Forest"] = accuracy_score(y_test, y_pred)
    print("---------------------------------------------------------")
    print(f"Confusion Matrix: \n{confusion_matrix(y_test, y_pred)}")
    # sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, cmap="Blues", fmt=".0f")
    print("---------------------------------------------------------")
    print(f"Classification Report: \n{classification_report(y_test, y_pred)}")
    xgb = XGBClassifier(booster = 'gbtree', learning_rate = 0.1, max_depth = 5, n_estimators = 180)
    xgb.fit(X_train, y_train)

    y_pred_xgb = xgb.predict(X_test)

    acc_xgb = accuracy_score(y_test, y_pred_xgb)
    conf = confusion_matrix(y_test, y_pred_xgb)
    clf_report = classification_report(y_test, y_pred_xgb)

    print(f"Accuracy Score of Ada Boost Classifier is : {acc_xgb}")
    print(f"Confusion Matrix : \n{conf}")
    print(f"Classification Report : \n{clf_report}")
    return scores

if __name__ == "__main__":
    model()

# key = addres
# key = categories
# key = city
# key = claimed
# key = country
# key = cuisines
# key = dateAdded
# key = dateUpdated
# key = descriptions
# key = domains
# key = facebookPageURL
# key = features
# key = geoLocation
# key = hours
# key = imageURLs
# key = isClosed
# key = keys
# key = languagesSpoken
# key = latitude
# key = longitude
# key = name
# key = neighborhoods
# key = paymentTypes
# key = phones
# key = postalCode
# key = priceRangeCurrency
# key = priceRangeMin
# key = priceRangeMax
# key = primaryCategories
# key = province
# key = reviews
# key = sourceURLs
# key = websites
# key = id

# key = address
# key = categories
# key = city
# key = claimed
# key = country
# key = cuisines
# key = dateAdded
# key = dateUpdated
# key = descriptions
# key = domains
# key = facebookPageURL
# key = features
# key = geoLocation
# key = hours
# key = imageURLs
# key = isClosed
# key = keys
# key = languagesSpoken
# key = latitude
# key = longitude
# key = name
# key = neighborhoods
# key = paymentTypes
# key = phones
# key = postalCode
# key = priceRangeCurrency
# key = priceRangeMin
# key = priceRangeMax
# key = primaryCategories
# key = province
# key = reviews
# key = sourceURLs
# key = websites
# key = id

# key = address
# key = categories
# key = city
# key = country
# key = dateAdded
# key = dateUpdated
# key = descriptions
# key = domains
# key = features
# key = geoLocation
# key = hours
# key = isClosed
# key = keys
# key = latitude
# key = longitude
# key = name
# key = paymentTypes
# key = people
# key = phones
# key = postalCode
# key = primaryCategories
# key = province
# key = sourceURLs
# key = websites
# key = yearIncorporated
# key = yearOpened
# key = id
