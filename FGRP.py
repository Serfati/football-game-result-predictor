# coding: utf-8

# About the Dataset:

# The ultimate Soccer database for data analysis and machine learning The dataset comes in the form of an SQL
# database and contains statistics of about 25,000 football matches. from the top football league of 11 European
# Countries. It covers seasons from 2008 to 2016 and contains match statistics (i.e: scores, corners, fouls etc...)
# as well as the team formations, with player names and a pair of coordinates to
# Players and Teams' attributes* sourced from EA Sports' FIFA video game series, including the weekly updates Team
# line up with squad formation (X, Y coordinates) Betting odds from up to 10 providers Detailed match events (goal
# types, possession, corner, cross, fouls, cards etc...) for +10,000 matches The dataset also has a set of about 35
# statistics for each player, derived from EA Sports' FIFA video games. It is not just the stats that come with a new

## STEPS: Data Wrangling, Business Understanding,
# ## Data Understanding, Data Cleaning, Data Preparation
# ## Create new variables, Exploratory Data Analysis, Conclusions
# ## Modelling, Evaluation, Deployment

# Importing libraries to the environment
import sqlite3
from math import sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sklearn as sk
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split, KFold, StratifiedKFold
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import mean_squared_error
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC

##################################################################################
############################### Data Wrangling ###################################
##################################################################################

match = pd.DataFrame()
cnx = sqlite3.connect('database.sqlite')


def wrangling():
    global match, cnx
    # Plot styling and sizing
    plt.style.use('seaborn-darkgrid')
    pd.set_option('display.max_columns', None)
    sns.set(style='darkgrid', context='notebook', rc={'figure.figsize': (12, 6)})

    # create a connection object for sql db

    # database.sqlite IS SQLITE file downloaded from KAGGLE.COM used for importing the dataset

    # match = pd.read_sql_query("SELECT * FROM Match", cnx)

    match = pd.read_sql("""SELECT Match.id,
                                    Country.name AS country_name,
                                    League.name AS league_name,
                                    season,
                                    stage,
                                    date,
                                    HT.team_long_name AS home_team,
                                    HT.team_api_id AS home_id,
                                    AT.team_long_name AS away_team,
                                    AT.team_api_id AS away_id,
                                    B365H,  BWH,
                                    B365D,  BWD,
                                    B365A,  BWA,
                                    home_team_goal,
                                    away_team_goal
                                    FROM Match
                                    JOIN Country on Country.id = Match.country_id
                                    JOIN League on League.id = Match.league_id
                                    LEFT JOIN Team AS HT on HT.team_api_id = Match.home_team_api_id
                                    LEFT JOIN Team AS AT on AT.team_api_id = Match.away_team_api_id
                                    WHERE country_name in ('Spain', 'Germany', 'France', 'Italy', 'England')
    
                                    ORDER by date
                                    LIMIT 100000;""", cnx)


##################################################################################
############################# Data Understanding #################################
##################################################################################
def understanding():
    print(match.head())

    # ## Exploratory data analysis
    print(match.info())

    # to check data types of the all the columns
    print(match.dtypes)

    # for numeric variable to get stats
    print(match.describe())

    # nrows and ncols
    print(match.shape)

    # missing values in the data frame
    print(match.isnull().sum())

    percent_of_missing = (match.isnull().sum() / match.isnull().count()) * 100

    # is showing percent of the nulls present in every columns
    print(percent_of_missing)

    # is showing duplicates in every columns
    print(sum(match.duplicated()))

    # Print summary statistics of home_team_goal.
    match[['home_team_goal', 'away_team_goal']].describe()


##################################################################################
# *********************** Data Cleaning + Preparation ************************   #
#### Create new variables ########################################################
def cleaning():
    global match
    selected_col = ["home_team", "home_id", "away_team", "away_id", "season", "home_team_goal", "away_team_goal",
                    "league_name", 'date', 'B365H', 'B365D', 'B365A', 'BWH', 'BWD', 'BWA']

    match = match[selected_col]

    match.dropna(subset=selected_col, inplace=True)

    match = pd.DataFrame(
        {"League": match.league_name, "season": match.season, "HomeTeam": match.home_team, "HomeID": match.home_id,
         "AwayTeam": match.away_team, "AwayID": match.away_id,
         "HTG": match.home_team_goal, "ATG": match.away_team_goal, "B365H": match.B365H, "B365D": match.B365D,
         "B365A": match.B365A, "BWH": match.BWH, "BWD": match.BWD, "BWA": match.BWA})

    # GOAL_DIFF for each match
    match['GOAL_DIFF'] = match['HTG'] - match['ATG']

    print(match.head())


def match_result(home_goal, away_goal):
    if home_goal > away_goal:
        return 1
    elif home_goal < away_goal:
        return 2
    else:
        return 0


def bets_result(bhome, bdarw, baway):
    if bhome <= bdarw <= baway or bhome <= baway <= bdarw:
        return 1
    elif bhome >= bdarw >= baway or bdarw >= bhome >= baway:
        return 2
    elif bdarw <= bhome <= baway or bdarw <= baway <= bhome:
        return 0


def preparation():
    # Home team Goal Average
    match['HGA'] = match['HTG'].groupby(match['HomeTeam']).transform('mean')
    # Away team Goal Average
    match['AGA'] = match['ATG'].groupby(match['AwayTeam']).transform('mean')
    # B365 Result Bet
    match['B365'] = match.apply(lambda i: bets_result(i['B365H'], i['B365D'], i['B365A']), axis=1)
    # B-Win Result Bet
    match['BW'] = match.apply(lambda i: bets_result(i['BWH'], i['BWD'], i['BWA']), axis=1)
    # Target Variable -  Full Time Result
    match['FTR'] = match.apply(lambda i: match_result(i['HTG'], i['ATG']), axis=1)

    # TODO add 4 new columns
    # HomeWinLastFive
    # AwayWinLastFive
    # HomeWinLastFiveConfrontation
    # AwayWinLastFiveConfrontation


##################################################################################
# ****************************** VISUALIZATION  ******************************   #
##################################################################################
def visualization():
    global cnx
    # Plot the distribution of home_team_goal and its evolution over time.
    f, axes = plt.subplots(2, 1)
    plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.5, hspace=0.5)
    sns.distplot(match['HTG'], kde=False, ax=axes[0]).set_title('Distribution of Home Team Goal')
    sns.distplot(match['ATG'], kde=False, ax=axes[1]).set_title('Distribution of Away Team Goal')

    plt.show()
    match.groupby(by='season')[['HTG', 'ATG']] \
        .mean().plot(ax=axes[1], title='Difference between goals scored at home and goals scored away')
    plt.show()

    results = match.groupby('FTR').count()
    results.HTG.plot(kind='bar')
    plt.title('Distribution of Full Time Results')
    plt.show()

    bet_fit = match.query('FTR==B365').count().HTG / match.shape[0]
    bet_fit_op = 1 - bet_fit
    plt.figure(figsize=(8, 8))
    plt.pie([bet_fit, bet_fit_op], shadow=True, autopct='%1.1f%%', labels=["Fit", "Miss"])
    plt.title('Distribution of BET365')
    plt.show()

    bet_fit = match.query('FTR==BW').count().HTG / match.shape[0]
    bet_fit_op = 1 - bet_fit
    plt.figure(figsize=(8, 8))
    plt.pie([bet_fit, bet_fit_op], shadow=True, autopct='%1.1f%%', labels=["Fit", "Miss"])
    plt.title('Distribution of BET-WIN')
    plt.show()

    total_away_goals = match.ATG.sum()
    total_home_goals = match.HTG.sum()
    plt.figure(figsize=(8, 8))
    plt.bar(x=[1, 2], tick_label=['Away Team', 'Home Team'], height=[total_away_goals, total_home_goals])
    plt.xlabel('Goals scored by')
    plt.ylabel('Number of goals scored')
    plt.title('Goals scored by team')
    plt.show()

    home_percent = results.query('FTR=="1"').HTG / results.shape[0]
    tie_percent = results.query('FTR=="0"').HTG / results.shape[0]
    away_percent = results.query('FTR=="2"').HTG / results.shape[0]

    # plt.figure(figsize=(8, 8))
    # pie_labels = ['Tied', 'Away Team Won', 'Home Team Won']
    # plt.pie([tie_percent, away_percent, home_percent], labels=pie_labels, autopct='%1.1f%%', shadow=True)
    # plt.title('Distribution of match results by winning team')
    # plt.show()

    players_height = pd.read_sql("""SELECT CASE
                                            WHEN ROUND(height)<165 then 165
                                            WHEN ROUND(height)>195 then 195
                                            ELSE ROUND(height)
                                            END AS calc_height,
                                            COUNT(height) AS distribution,
                                            (avg(PA_Grouped.avg_overall_rating)) AS avg_overall_rating,
                                            (avg(PA_Grouped.avg_potential)) AS avg_potential,
                                            AVG(weight) AS avg_weight
                                FROM PLAYER
                                LEFT JOIN (SELECT Player_Attributes.player_api_id,
                                            avg(Player_Attributes.overall_rating) AS avg_overall_rating,
                                            avg(Player_Attributes.potential) AS avg_potential
                                            FROM Player_Attributes
                                            GROUP BY Player_Attributes.player_api_id)
                                            AS PA_Grouped ON PLAYER.player_api_id = PA_Grouped.player_api_id
                                GROUP BY calc_height
                                ORDER BY calc_height
                                    ;""", cnx)

    players_height.plot(x='calc_height', y='avg_overall_rating', figsize=(12, 5), title='Potential vs Height')
    plt.show()

    # Plot the distribution of GOAL_DIFF and its evolution over the considered timeframe.
    plt.figure(figsize=(12, 6))
    figure, axes = plt.subplots(2, 1)
    plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.5, hspace=0.5)
    sns.distplot(match['GOAL_DIFF'], kde=False, ax=axes[0]).set_title('Distribution of goal scored')
    sns.lineplot(x='season', y='GOAL_DIFF', data=match, err_style=None, ax=axes[1]).set_title(
        'How does the variable GOAL_DIFF evolve over time?')
    plt.show()


##################################################################################
# ****************************** Data Splitting  ******************************  #
##################################################################################
def percentage_split(model, data):
    # LogisticRegression - 0.53%
    # LinearRegression - 0.47%
    # KNN - 0.64%
    # NB - 0.44%
    # DecisionTreeClassifier - 00
    # SVM -  0.54%
    global match
    train, test = train_test_split(data, test_size=0.35, random_state=1000)
    df = np.array(match)
    test = np.array(test)

    y = df[:, -1]
    x = df[:, 8:18]
    y1 = test[:, -1]
    x1 = test[:, 8:18]

    model.fit(x, y.astype('int'))
    y_predict = model.predict(x1)
    predictions = [round(value) for value in y_predict]
    evaluation(y_true=y1.astype('int'), y_pred=predictions)


def cross_validation(model, data, predictors, outcome):
    # RandomForestClassifier - 49.4%
    # SVM - 53.040%
    seed = 42
    kf = KFold(n_splits=10, random_state=seed, shuffle=True)
    accuracy = []
    for train, test in kf.split(data):
        train_predictors = (data[predictors].iloc[train, :])
        train_target = data[outcome].iloc[train]
        model.fit(train_predictors, train_target)
        accuracy.append(model.score(data[predictors].iloc[test, :], data[outcome].iloc[test]))
    print("Cross-Validation Score : %s" % "{0:.3%}".format(np.mean(accuracy)))


##################################################################################
# ********************************* Modeling  *********************************  #
##################################################################################
def train_cross_model():
    global match
    model = SVC()
    predictor_var = ['B365H', 'B365D', 'B365A', 'BWH', 'BWD',
                     'BWA', 'HGA', 'AGA', 'B365', 'BW']
    outcome_var = 'FTR'
    cross_validation(model, match, predictor_var, outcome_var)


def train_split_model():
    global match
    model = DecisionTreeClassifier()
    percentage_split(model, match)


##################################################################################
# ********************************* Evaluation  *********************************  #
##################################################################################
def evaluation(y_true, y_pred):
    accuracy = accuracy_score(y_true, y_pred)
    print("Model accuracy: %.2f%% " % accuracy)
    # mse = mean_squared_error(y_true=y_true, y_pred=y_pred)


##################################################################################
# -------------------------------- Main Loop ----------------------------------- #
##################################################################################
def run_main_loop():
    wrangling()
    # understanding()
    cleaning()
    preparation()
    # visualization()
    # train_cross_model()
    train_split_model()


if __name__ == '__main__':
    run_main_loop()