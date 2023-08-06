from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect,
    send_file,
    session as fsession,
)
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    logout_user,
    current_user,
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from cassandra.query import SimpleStatement
from flask_login import login_required
from flask_session import Session
from cassandra import ConsistencyLevel
from cassandra.policies import DCAwareRoundRobinPolicy
from io import BytesIO

import base64
import uuid
import hashlib
import json


app = Flask(__name__)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'
app.config[
    "SESSION_TYPE"
] = "filesystem"  # You can change the session type based on your requirements
Session(app)
cloud_config = {"secure_connect_bundle": "C:\secure-connect-fyp-ica.zip"}
auth_provider = PlainTextAuthProvider(
    "RxnkOimyTprpDRaWZyEfWZTz",
    "5ydlP0.DQvbKjBv-GTt7tWxQnpBk5A+Kg84d3MZojxSNo8wciB+i0RnzYL_MIQgKgpCZEp9PH5Cdhf,s-1mJdEweY9N2vClPu+EqSlfmG1vHuAuw,9eS7k.UzrDOwT8W",
)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()

row = session.execute("select release_version from system.local").one()
if row:
    print(row[0])
else:
    print("An error occurred.")


@app.route("/sockets")
def pose_sockets():
    return render_template("pose_sockets.html")


@app.route("/tfjs")
def pose_tfjs():
    return render_template("pose_tfjs.html")


@app.route("/push_up")
def count_push_ups():
    if "sessID" in fsession:
        sessionID = fsession["sessID"]
        return render_template("count_push_ups.html", sessionID=sessionID)
    else:
        return render_template("login.html")


@app.route("/sit_up")
def count_sit_ups():
    if "sessID" in fsession:
        sessionID = fsession["sessID"]
        return render_template("count_sit_ups.html", sessionID=sessionID)
    else:
        return render_template("login.html")


@app.route("/")
def home():
    if "sessID" in fsession:
        sessionID = fsession["sessID"]
        return render_template("home.html", sessionID=sessionID)
    else:
        return render_template("home.html")


@app.route("/profile")
def profile():
    sessionID = fsession["sessID"]

    # Query user data
    user_query = "SELECT * FROM fyp.users WHERE id = %s ALLOW FILTERING"
    user_result = session.execute(user_query, (sessionID,))
    user_row = user_result.one()

    # Extract user data
    age = user_row.age
    name = user_row.name
    yob = user_row.yob
    gender = user_row.gender

    # Query best scores for different exercises
    score_query_push_up = "SELECT * FROM fyp.basicscores WHERE user_id = %s AND exercise = 'Push Ups' ALLOW FILTERING"
    score_query_sit_up = "SELECT * FROM fyp.basicscores WHERE user_id = %s AND exercise = 'Sit Ups' ALLOW FILTERING"
    score_query_squats_with_ball = "SELECT * FROM fyp.basicscores WHERE user_id = %s AND exercise = 'Squats with Ball' ALLOW FILTERING"
    score_query_grip_strength = (
        "SELECT * FROM fyp.gripscore WHERE user_id = %s ALLOW FILTERING"
    )
    score_query_standing_broad_jump = (
        "SELECT * FROM fyp.jumpscore WHERE user_id = %s ALLOW FILTERING"
    )
    score_query_2_4km_run = (
        "SELECT * FROM fyp.runscore WHERE user_id = %s ALLOW FILTERING"
    )

    # Execute the queries for each exercise
    score_result_push_up = session.execute(score_query_push_up, (sessionID,))
    score_result_sit_up = session.execute(score_query_sit_up, (sessionID,))
    score_result_squats_with_ball = session.execute(
        score_query_squats_with_ball, (sessionID,)
    )
    score_result_grip_strength = session.execute(
        score_query_grip_strength, (sessionID,)
    )
    score_result_standing_broad_jump = session.execute(
        score_query_standing_broad_jump, (sessionID,)
    )
    score_result_2_4km_run = session.execute(score_query_2_4km_run, (sessionID,))

    # Get the best (maximum) goodcount for each exercise
    best_push_up = max(score_result_push_up, key=lambda x: x.goodcount, default=0)
    best_sit_up = max(score_result_sit_up, key=lambda x: x.goodcount, default=0)
    best_squats_with_ball = max(
        score_result_squats_with_ball, key=lambda x: x.goodcount, default=0
    )
    best_grip_strength = max(
        score_result_grip_strength, key=lambda x: x.weight, default=0
    )
    best_standing_broad_jump = max(
        score_result_standing_broad_jump, key=lambda x: x.totaldist, default=0
    )
    best_2_4km_run = min(score_result_2_4km_run, key=lambda x: x.seconds, default=0)

    # Prepare the data for rendering in the template
    best_scores = [
        {
            "exercise": "Push Up",
            "goodcount": best_push_up.goodcount if best_push_up else 0,
        },
        {
            "exercise": "Sit Up",
            "goodcount": best_sit_up.goodcount if best_sit_up else 0,
        },
        {
            "exercise": "Squats with Ball",
            "goodcount": best_squats_with_ball.goodcount
            if best_squats_with_ball
            else 0,
        },
        {
            "exercise": "Grip Strength",
            "goodcount": best_grip_strength.weight if best_grip_strength else 0,
        },
        {
            "exercise": "Standing Broad Jump",
            "goodcount": best_standing_broad_jump.totaldist
            if best_standing_broad_jump
            else 0,
        },
        {
            "exercise": "2.4km run",
            "goodcount": best_2_4km_run.seconds if best_2_4km_run else 0,
        },
    ]

    # Accessing "goodcount" value for the exercise "Push Up"
    best_push_up_score = best_scores[0]["goodcount"]

    # Accessing "goodcount" value for the exercise "Sit Up"
    best_sit_up_score = best_scores[1]["goodcount"]

    # Accessing "goodcount" value for the exercise "Squats with Ball"
    best_squats_with_ball_score = best_scores[2]["goodcount"]

    # Accessing "goodcount" value for the exercise "Grip Strength"
    best_grip_strength_score = best_scores[3]["goodcount"]

    # Accessing "goodcount" value for the exercise "Standing Broad Jump"
    best_standing_broad_jump_score = best_scores[4]["goodcount"]

    # Accessing "goodcount" value for the exercise "2.4km run"
    best_2_4km_run_score = best_scores[5]["goodcount"]

    fitness_levels = {
        (13, 24): {
            (25, 30): "Very Fit",
            (19, 24): "Fit",
            (13, 18): "Average",
            (7, 12): "Below Average",
            (1, 6): "Unfit",
        },
        # Add more age range mappings here if needed
    }

    def get_situp_score(age, good_count):
        male_situp_score_age_mapping = {
            13: {1: 25, 2: 29, 3: 34, 4: 38, 5: 43},
            14: {1: 31, 2: 34, 3: 37, 4: 40, 5: 43},
            15: {1: 31, 2: 34, 3: 37, 4: 40, 5: 43},
            16: {1: 31, 2: 34, 3: 37, 4: 40, 5: 43},
            17: {1: 31, 2: 34, 3: 37, 4: 40, 5: 43},
            18: {1: 31, 2: 34, 3: 37, 4: 40, 5: 43},
            19: {1: 31, 2: 34, 3: 37, 4: 40, 5: 43},
            20: {1: 28, 2: 31, 3: 34, 4: 37, 5: 40},
            # Add more mappings as needed for different ages and scores
        }
        female_situp_score_age_mapping = {
            13: {1: 14, 2: 18, 3: 22, 4: 26, 5: 31},
            14: {1: 16, 2: 20, 3: 24, 4: 28, 5: 31},
            15: {1: 17, 2: 21, 3: 25, 4: 29, 5: 31},
            16: {1: 18, 2: 22, 3: 26, 4: 29, 5: 31},
            17: {1: 19, 2: 23, 3: 27, 4: 29, 5: 31},
            18: {1: 20, 2: 24, 3: 27, 4: 29, 5: 31},
            19: {1: 21, 2: 24, 3: 27, 4: 29, 5: 31},
            20: {1: 21, 2: 23, 3: 25, 4: 27, 5: 29},
            # Add more mappings as needed for different ages and scores
        }
        if gender == "Male":
            acceptable_age = max(male_situp_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in male_situp_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(male_situp_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1, count + 1):
                            if male_situp_score_age_mapping[age][i] <= good_count and male_situp_score_age_mapping[age][i + 1] > good_count:
                                point += i
                                break
                            elif male_situp_score_age_mapping[age][count] <= good_count:
                                point += 5
                                break

                        return point
            else:
                count = len(male_situp_score_age_mapping[20].values())
                point = 0
                for i in range(1, count + 1):
                    if male_situp_score_age_mapping[20][i] <= good_count and male_situp_score_age_mapping[20][i + 1] > good_count:
                        point += i
                        break
                    elif male_situp_score_age_mapping[20][count] <= good_count:
                        point += 5
                        break

                return point

            return 0
        else:
            acceptable_age = max(female_situp_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in female_situp_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(female_situp_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1, count + 1):
                            if female_situp_score_age_mapping[age][i] <= good_count and female_situp_score_age_mapping[age][i + 1] > good_count:
                                point += i
                                break
                            elif female_situp_score_age_mapping[age][count] <= good_count:
                                point += 5
                                break

                        return point
            else:
                count = len(female_situp_score_age_mapping[20].values())
                point = 0
                for i in range(1, count + 1):
                    if female_situp_score_age_mapping[20][i] <= good_count and female_situp_score_age_mapping[20][i + 1] > good_count:
                        point += i
                        break
                    elif female_situp_score_age_mapping[20][count] <= good_count:
                        point += 5
                        break

                return point

            return 0

    # Assuming best_sit_up_score holds the number of sit-ups performed by the person
    situp_score = get_situp_score(age, best_sit_up_score)


    def get_pushup_score(age, good_count):
        male_pushup_score_age_mapping = {
            13: {1: 12, 2: 18, 3: 23, 4: 28, 5: 35},
            14: {1: 12, 2: 18, 3: 23, 4: 28, 5: 35},
            15: {1: 15, 2: 19, 3: 25, 4: 30, 5: 38},
            16: {1: 15, 2: 19, 3: 25, 4: 30, 5: 38},
            17: {1: 17, 2: 21, 3: 27, 4: 32, 5: 40},
            18: {1: 17, 2: 21, 3: 27, 4: 32, 5: 40},
            19: {1: 17, 2: 21, 3: 27, 4: 32, 5: 40},
            20: {1: 16, 2: 18, 3: 22, 4: 29, 5: 37}
        }
        female_pushup_score_age_mapping = {
            13: {1: 8, 2: 12, 3: 18, 4: 25, 5: 30},
            14: {1: 8, 2: 12, 3: 18, 4: 25, 5: 30},
            15: {1: 10, 2: 13, 3: 19, 4: 26, 5: 32},
            16: {1: 10, 2: 13, 3: 19, 4: 26, 5: 32},
            17: {1: 11, 2: 15, 3: 20, 4: 27, 5: 34},
            18: {1: 11, 2: 15, 3: 20, 4: 27, 5: 34},
            19: {1: 11, 2: 15, 3: 20, 4: 27, 5: 34},
            20: {1: 9, 2: 11, 3: 15, 4: 21, 5: 31}
        }
        if gender == "Male":  
            acceptable_age = max(male_pushup_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in male_pushup_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(male_pushup_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1,count+1):
                                
                            if male_pushup_score_age_mapping[age][i] <= good_count and male_pushup_score_age_mapping[age][i+1] > good_count:
                                point += i
                                
                                break
                            
                            elif male_pushup_score_age_mapping[age][count] <= good_count :
                                point += 5
                                
                                break
                        
                        return point
            else:            
                count = len(male_pushup_score_age_mapping[20].values())
                point = 0
                for i in range(1,count+1):                    
                    if male_pushup_score_age_mapping[20][i] <= good_count and male_pushup_score_age_mapping[20][i+1] > good_count:
                        point += i
                            
                        break
                    elif male_pushup_score_age_mapping[20][count] <= good_count:
                        point += 5
                            
                        break
                    
                return point
        else:
            acceptable_age = max(female_pushup_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in female_pushup_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(female_pushup_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1,count+1):
                                
                            if female_pushup_score_age_mapping[age][i] <= good_count and female_pushup_score_age_mapping[age][i+1] > good_count:
                                point += i
                                
                                break
                            
                            elif female_pushup_score_age_mapping[age][count] <= good_count :
                                point += 5
                                
                                break
                        
                        return point
            else:            
                count = len(female_pushup_score_age_mapping[20].values())
                point = 0
                for i in range(1,count+1):                    
                    if female_pushup_score_age_mapping[20][i] <= good_count and female_pushup_score_age_mapping[20][i+1] > good_count:
                        point += i
                            
                        break
                    elif female_pushup_score_age_mapping[20][count] <= good_count:
                        point += 5
                            
                        break
                    
                return point

    pushup_score = get_pushup_score(age, best_push_up_score)

    def get_squat_score(age, good_count):
        male_squat_score_age_mapping = {
            13: {1: 10, 2: 15, 3: 20, 4: 25, 5: 35},
            14: {1: 10, 2: 15, 3: 20, 4: 25, 5: 35},
            15: {1: 12, 2: 17, 3: 21, 4: 26, 5: 36},
            16: {1: 12, 2: 17, 3: 21, 4: 26, 5: 36},
            17: {1: 12, 2: 17, 3: 21, 4: 27, 5: 36},
            18: {1: 12, 2: 17, 3: 21, 4: 27, 5: 38},
            19: {1: 14, 2: 19, 3: 24, 4: 30, 5: 40},
            20: {1: 12, 2: 17, 3: 22, 4: 28, 5: 39},
            # Add more mappings as needed for different ages and scores
        }
        female_squat_score_age_mapping = {
            13: {1: 6, 2: 10, 3: 15, 4: 20, 5: 25},
            14: {1: 6, 2: 10, 3: 15, 4: 20, 5: 26},
            15: {1: 7, 2: 11, 3: 16, 4: 21, 5: 26},
            16: {1: 7, 2: 11, 3: 16, 4: 21, 5: 28},
            17: {1: 8, 2: 17, 3: 17, 4: 22, 5: 28},
            18: {1: 8, 2: 17, 3: 18, 4: 23, 5: 30},
            19: {1: 9, 2: 19, 3: 20, 4: 25, 5: 32},
            20: {1: 8, 2: 17, 3: 19, 4: 24, 5: 31},
            # Add more mappings as needed for different ages and scores
        }
        if gender == "Male":
            acceptable_age = max(male_squat_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in male_squat_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(male_squat_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1, count + 1):
                            if male_squat_score_age_mapping[age][i] <= good_count and male_squat_score_age_mapping[age][i + 1] > good_count:
                                point += i
                                break
                            elif male_squat_score_age_mapping[age][count] <= good_count:
                                point += 5
                                break

                        return point
            else:
                count = len(male_squat_score_age_mapping[20].values())
                point = 0
                for i in range(1, count + 1):
                    if male_squat_score_age_mapping[20][i] <= good_count and male_squat_score_age_mapping[20][i + 1] > good_count:
                        point += i
                        break
                    elif male_squat_score_age_mapping[20][count] <= good_count:
                        point += 5
                        break

                return point

            return 0
        else:
            acceptable_age = max(female_squat_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in female_squat_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(female_squat_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1, count + 1):
                            if female_squat_score_age_mapping[age][i] <= good_count and female_squat_score_age_mapping[age][i + 1] > good_count:
                                point += i
                                break
                            elif female_squat_score_age_mapping[age][count] <= good_count:
                                point += 5
                                break

                        return point
            else:
                count = len(female_squat_score_age_mapping[20].values())
                point = 0
                for i in range(1, count + 1):
                    if female_squat_score_age_mapping[20][i] <= good_count and female_squat_score_age_mapping[20][i + 1] > good_count:
                        point += i
                        break
                    elif female_squat_score_age_mapping[20][count] <= good_count:
                        point += 5
                        break

                return point

            return 0

    # Assuming best_squats_with_ball_score holds the number of squats performed by the person
    squat_score = get_squat_score(age, best_squats_with_ball_score)


    def get_jump_score(age, good_count):
        male_jump_score_age_mapping = {
            13: {1: 164, 2: 176, 3: 189, 4: 202, 5: 215},
            14: {1: 186, 2: 196, 3: 206, 4: 216, 5: 226},
            15: {1: 198, 2: 208, 3: 218, 4: 228, 5: 238},
            16: {1: 206, 2: 216, 3: 226, 4: 236, 5: 246},
            17: {1: 210, 2: 220, 3: 230, 4: 240, 5: 250},
            18: {1: 212, 2: 222, 3: 232, 4: 242, 5: 252},
            19: {1: 212, 2: 222, 3: 232, 4: 242, 5: 252},
            20: {1: 207, 2: 216, 3: 225, 4: 234, 5: 243},
            # Add more mappings as needed for different ages and scores
        }
        female_jump_score_age_mapping = {
            13: {1: 135, 2: 144, 3: 153, 4: 162, 5: 171},
            14: {1: 142, 2: 151, 3: 160, 4: 169, 5: 178},
            15: {1: 147, 2: 156, 3: 165, 4: 174, 5: 183},
            16: {1: 151, 2: 160, 3: 169, 4: 178, 5: 187},
            17: {1: 154, 2: 163, 3: 172, 4: 181, 5: 190},
            18: {1: 156, 2: 165, 3: 174, 4: 183, 5: 192},
            19: {1: 156, 2: 165, 3: 174, 4: 185, 5: 196},
            20: {1: 150, 2: 162, 3: 174, 4: 186, 5: 198},
            # Add more mappings as needed for different ages and scores
        }
        if gender == "Male":
            acceptable_age = max(male_jump_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in male_jump_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(male_jump_score_age_mapping[agegroup])
                        point = 0
                        for i in range(1, count + 1):
                            if male_jump_score_age_mapping[age][i] <= good_count and male_jump_score_age_mapping[age].get(i + 1, float('inf')) > good_count:
                                point += i
                                break
                            elif male_jump_score_age_mapping[age][count] <= good_count:
                                point += 5
                                break

                        return point
            else:
                count = len(male_jump_score_age_mapping[20])
                point = 0
                for i in range(1, count + 1):
                    if male_jump_score_age_mapping[20][i] <= good_count and male_jump_score_age_mapping[20].get(i + 1, float('inf')) > good_count:
                        point += i
                        break
                    elif male_jump_score_age_mapping[20][count] <= good_count:
                        point += 5
                        break

                return point

            return 0
        else:
            acceptable_age = max(female_jump_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in female_jump_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(female_jump_score_age_mapping[agegroup])
                        point = 0
                        for i in range(1, count + 1):
                            if female_jump_score_age_mapping[age][i] <= good_count and female_jump_score_age_mapping[age].get(i + 1, float('inf')) > good_count:
                                point += i
                                break
                            elif female_jump_score_age_mapping[age][count] <= good_count:
                                point += 5
                                break

                        return point
            else:
                count = len(female_jump_score_age_mapping[20])
                point = 0
                for i in range(1, count + 1):
                    if female_jump_score_age_mapping[20][i] <= good_count and female_jump_score_age_mapping[20].get(i + 1, float('inf')) > good_count:
                        point += i
                        break
                    elif female_jump_score_age_mapping[20][count] <= good_count:
                        point += 5
                        break

                return point

            return 0

    # Assuming best_standing_broad_jump_score holds the best standing broad jump score
    jump_score = get_jump_score(age, best_standing_broad_jump_score)


    def get_grip_score(age, good_count):
        male_grip_score_age_mapping = {
            13: {1: 19, 2: 23, 3: 26, 4: 28, 5: 30},
            14: {1: 28, 2: 30, 3: 32, 4: 36, 5: 40},
            15: {1: 28, 2: 30, 3: 32, 4: 36, 5: 40},
            16: {1: 32, 2: 36, 3: 42, 4: 45, 5: 50},
            17: {1: 32, 2: 36, 3: 42, 4: 45, 5: 50},
            18: {1: 35, 2: 40, 3: 45, 4: 48, 5: 52},
            19: {1: 35, 2: 40, 3: 45, 4: 48, 5: 52},
            20: {1: 36, 2: 42, 3: 46, 4: 50, 5: 55}
        }
        female_grip_score_age_mapping = {
            13: {1: 14, 2: 16, 3: 19, 4: 22, 5: 24},
            14: {1: 15, 2: 18, 3: 21, 4: 24, 5: 27},
            15: {1: 15, 2: 18, 3: 21, 4: 24, 5: 27},
            16: {1: 17, 2: 20, 3: 23, 4: 25, 5: 29},
            17: {1: 17, 2: 20, 3: 23, 4: 25, 5: 29},
            18: {1: 19, 2: 22, 3: 25, 4: 28, 5: 30},
            19: {1: 19, 2: 22, 3: 25, 4: 28, 5: 30},
            20: {1: 21, 2: 25, 3: 28, 4: 31, 5: 35}
        }  
        if gender == "Male":
            acceptable_age = max(male_grip_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in male_grip_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(male_grip_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1,count+1):
                                
                            if male_grip_score_age_mapping[age][i] <= good_count and male_grip_score_age_mapping[age][i+1] > good_count:
                                point += i
                                
                                break
                            elif male_grip_score_age_mapping[age][count] <= good_count:
                                point += 5
                                
                                break
                        
                        return point
            else:            
                count = len(male_grip_score_age_mapping[20].values())
                point = 0
                for i in range(1,count+1):                    
                    if male_grip_score_age_mapping[20][i] <= good_count and male_grip_score_age_mapping[20][i+1] > good_count:
                        point += i
                            
                        break
                    elif male_grip_score_age_mapping[20][count] <= good_count:
                        point += 5
                            
                        break
                    
                return point
        else:
            acceptable_age = max(female_grip_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in female_grip_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(female_grip_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1,count+1):
                                
                            if female_grip_score_age_mapping[age][i] <= good_count and female_grip_score_age_mapping[age][i+1] > good_count:
                                point += i
                                
                                break
                            elif female_grip_score_age_mapping[age][count] <= good_count:
                                point += 5
                                
                                break
                        
                        return point
            else:            
                count = len(female_grip_score_age_mapping[20].values())
                point = 0
                for i in range(1,count+1):                    
                    if female_grip_score_age_mapping[20][i] <= good_count and female_grip_score_age_mapping[20][i+1] > good_count:
                        point += i
                            
                        break
                    elif female_grip_score_age_mapping[20][count] <= good_count:
                        point += 5
                            
                        break
                    
                return point

    grip_score = get_grip_score(age, best_grip_strength_score)

    def get_run_score(age, good_count):
        male_run_score_age_mapping = {
            13: {1: 960, 2: 890, 3: 820, 4: 750, 5: 690},
            14: {1: 920, 2: 850, 3: 780, 4: 720, 5: 660},
            15: {1: 880, 2: 820, 3: 760, 4: 700, 5: 640},
            16: {1: 850, 2: 800, 3: 740, 4: 690, 5: 630},
            17: {1: 820, 2: 770, 3: 720, 4: 670, 5: 620},
            18: {1: 810, 2: 760, 3: 710, 4: 670, 5: 620},
            19: {1: 800, 2: 750, 3: 700, 4: 660, 5: 620},
            20: {1: 780, 2: 740, 3: 700, 4: 660, 5: 620}
        }
        female_run_score_age_mapping = {
            13: {1: 1110, 2: 1050, 3: 990, 4: 930, 5: 870},
            14: {1: 1100, 2: 1040, 3: 980, 4: 920, 5: 860},
            15: {1: 1090, 2: 1030, 3: 970, 4: 910, 5: 850},
            16: {1: 1080, 2: 1020, 3: 960, 4: 900, 5: 840},
            17: {1: 1050, 2: 1000, 3: 950, 4: 890, 5: 840},
            18: {1: 1040, 2: 990, 3: 940, 4: 890, 5: 840},
            19: {1: 1030, 2: 980, 3: 930, 4: 890, 5: 860},
            20: {1: 1020, 2: 990, 3: 960, 4: 930, 5: 900}
        } 
        if gender == "Male":
            acceptable_age = max(male_run_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in male_run_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(male_run_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1,count+1):
                                
                            if male_run_score_age_mapping[age][i] >= good_count and male_run_score_age_mapping[age][i+1] < good_count:
                                point += i
                                
                                break
                            elif male_run_score_age_mapping[age][count] >= good_count and good_count != 0:
                                point += 5
                                
                                break
                            elif good_count == 0:
                                point = 0

                                break
                        
                        return point
            else:            
                count = len(male_run_score_age_mapping[20].values())
                point = 0
                for i in range(1,count+1):                    
                    if male_run_score_age_mapping[20][i] >= good_count and male_run_score_age_mapping[20][i+1] < good_count:
                        point += i
                            
                        break
                    elif male_run_score_age_mapping[20][count] >= good_count and good_count != 0:
                        point += 5
                            
                        break
                    elif good_count == 0:
                        point = 0

                        break
                    
                return point
        else:
            acceptable_age = max(female_run_score_age_mapping.keys())
            if age < acceptable_age:
                for agegroup in female_run_score_age_mapping.keys():
                    if age == agegroup:
                        count = len(female_run_score_age_mapping[agegroup].values())
                        point = 0
                        for i in range(1,count+1):
                                
                            if female_run_score_age_mapping[age][i] >= good_count and female_run_score_age_mapping[age][i+1] < good_count:
                                point += i
                                
                                break
                            elif female_run_score_age_mapping[age][count] >= good_count and good_count != 0:
                                point += 5
                                
                                break
                            elif good_count == 0:
                                point = 0

                                break
                        
                        return point
            else:            
                count = len(female_run_score_age_mapping[20].values())
                point = 0
                for i in range(1,count+1):                    
                    if female_run_score_age_mapping[20][i] >= good_count and female_run_score_age_mapping[20][i+1] < good_count:
                        point += i
                            
                        break
                    elif female_run_score_age_mapping[20][count] >= good_count and good_count != 0:
                        point += 5
                            
                        break
                    elif good_count == 0:
                        point = 0

                        break
                    
                return point

    run_score = get_run_score(age, best_2_4km_run_score)

    # Total score:
    total_score = (
        grip_score + jump_score + squat_score + pushup_score + situp_score + run_score
    )

    def get_fitness_level(age, total_score):
        # Get the fitness level mappings for the given age range
        age_range_mapping = fitness_levels.get((13, 24), {})

        # Find the appropriate fitness level for the given total_score
        fitness_level = "Fitness Level may not be available for your age."
        for score_range, level in age_range_mapping.items():
            if score_range[0] <= total_score <= score_range[1]:
                fitness_level = level
                break
        

        return fitness_level

    fitness_level = get_fitness_level(age, total_score)

    exercise_score = {
        "Push Ups": best_push_up_score,
        "Sit Ups": best_sit_up_score,
        "Squats with Ball": best_squats_with_ball_score,
        "Grip Strength": best_grip_strength_score,
        "2.4Km Run": best_2_4km_run_score,
        "Standing Broad Jump": best_standing_broad_jump_score,
    }
    lowest_score = min(exercise_score.values())

    # Find exercises with the lowest score (in case of ties)
    exercises_with_lowest_score = [exercise for exercise, score in exercise_score.items() if score == lowest_score and score != 0]
    return render_template(
        "profile.html",
        age=age,
        name=name,
        yob=yob,
        best_scores=best_scores,
        fitness_level=fitness_level,
        total_score=total_score,
        exercises_with_lowest_score=exercises_with_lowest_score
    )


@app.route("/generate", methods=["POST"])
def generate_chart():
    exercise = request.form["exercise"]

    # Query the database to retrieve the data for the specified exercise
    query = "SELECT goodcount, badcount, exercise, poseresult, chart FROM fyp.basicscores WHERE poseresult = %s ALLOW FILTERING"
    result = session.execute(query, (exercise,))

    data = result.one()

    if data:
        exercise = data.exercise
        good_count = data.goodcount
        bad_count = data.badcount
        poseresult = data.poseresult
        image_blob = data.chart
        image_base64 = base64.b64encode(image_blob).decode("utf-8")
        # Render the generate.html template with exercise data
        return render_template(
            "generate.html",
            exercise=exercise,
            good_count=good_count,
            bad_count=bad_count,
            poseresult=poseresult,
            image_base64=image_base64,
        )

    # Handle the case when the data for the exercise is not found
    return "Data not found for exercise: {}".format(exercise)


@app.route("/filter", methods=["POST"])
def filter_profile():
    sessionID = fsession["sessID"]
    exercise = request.form.get("exercise")

    # Query user data
    user_query = "SELECT * FROM fyp.users WHERE id = %s ALLOW FILTERING"
    user_result = session.execute(user_query, (sessionID,))

    user_row = user_result.one()

    # Extract user data
    age = user_row.age
    name = user_row.name
    yob = user_row.yob

    score_history = "SELECT * FROM fyp.basicscores WHERE user_id = %s AND exercise = %s ALLOW FILTERING"
    g_score_history = "SELECT * FROM fyp.gripscore WHERE user_id = %s AND exercise = %s ALLOW FILTERING"
    r_score_history = "SELECT * FROM fyp.runscore WHERE user_id = %s AND exercise = %s ALLOW FILTERING"
    j_score_history = "SELECT * FROM fyp.jumpscore WHERE user_id = %s AND exercise = %s ALLOW FILTERING"

    score_result = session.execute(score_history, (sessionID, exercise))
    g_score_result = session.execute(g_score_history, (sessionID, exercise))
    r_score_result = session.execute(r_score_history, (sessionID, exercise))
    j_score_result = session.execute(j_score_history, (sessionID, exercise))

    histscores = []

    for score_row in score_result:
        histscores.append(score_row)
    for score_row in g_score_result:
        histscores.append(score_row)
    for score_row in r_score_result:
        histscores.append(score_row)
    for score_row in j_score_result:
        histscores.append(score_row)
    # Retrieve the selected exercise from the form data

    # Query scores for the user and the selected exercise
    score_query = "SELECT * FROM fyp.basicscores WHERE user_id = %s AND exercise = %s ALLOW FILTERING"
    g_score_query = "SELECT * FROM fyp.gripscore WHERE user_id = %s AND exercise = %s ALLOW FILTERING"
    r_score_query = "SELECT * FROM fyp.runscore WHERE user_id = %s AND exercise = %s ALLOW FILTERING"
    j_score_query = "SELECT * FROM fyp.jumpscore WHERE user_id = %s AND exercise = %s ALLOW FILTERING"

    score_result = session.execute(score_query, (sessionID, exercise))
    g_score_result = session.execute(g_score_query, (sessionID, exercise))
    r_score_result = session.execute(r_score_query, (sessionID, exercise))
    j_score_result = session.execute(j_score_query, (sessionID, exercise))

    scores = []
    for score_row in score_result:
        scores.append(
            {
                "exercise": score_row.exercise,
                "timestamp": score_row.date,
                "goodcount": score_row.goodcount,
            }
        )
    for score_row in g_score_result:
        scores.append(
            {
                "exercise": score_row.exercise,
                "timestamp": score_row.date,
                "goodcount": score_row.weight,
            }
        )
    for score_row in r_score_result:
        scores.append(
            {
                "exercise": score_row.exercise,
                "timestamp": score_row.date,
                "goodcount": score_row.seconds,
            }
        )
    for score_row in j_score_result:
        scores.append(
            {
                "exercise": score_row.exercise,
                "timestamp": score_row.date,
                "goodcount": score_row.totaldist,
            }
        )

    return render_template(
        "profilefilter.html",
        age=age,
        name=name,
        yob=yob,
        scores=scores,
        histscores=histscores,
        exercise=exercise,
    )


@app.route("/vidmaster")
def vid_master():
    return render_template("video_master.html")


@app.route("/vidminion")
def vid_minion():
    gFaceMode = request.args.get("face")
    gCamPosition = request.args.get("camerapos")
    return render_template(
        "video_minion.html", gFaceMode=gFaceMode, gCamPosition=gCamPosition
    )


@app.route("/vidsample")
def vid_sample():
    return render_template("video_sample.html")


@app.route("/vidsampleios")
def vid_sample_ios():
    return render_template("video_sample_ios.html")


# end master-minion simultaneous video capturing


# Team Member pages
@app.route("/member")
def member():
    if "sessID" in fsession:
        sessionID = fsession["sessID"]
        return render_template("project_member.html", sessionID=sessionID)
    else:
        return render_template("project_member.html")


# About Page
@app.route("/about")
def about():
    if "sessID" in fsession:
        sessionID = fsession["sessID"]
        return render_template("about.html", sessionID=sessionID)
    else:
        return render_template("about.html")


# Contact Page
@app.route("/contact")
def contact():
    if "sessID" in fsession:
        sessionID = fsession["sessID"]
        return render_template("contact.html", sessionID=sessionID)
    else:
        return render_template("contact.html")


# Login Page
@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


# Validating of credentials
@app.route("/login", methods=["POST"])
def login_post():
    fname = request.form["username"]
    password = request.form["password"]
    login_hash = hashlib.sha1(password.encode()).hexdigest()
    # Perform Cassandra query to validate the credentials
    query = "SELECT * FROM fyp.users WHERE name = %s AND password = %s ALLOW FILTERING"
    result = session.execute(query, (fname, login_hash))

    if result.one():
        row = result.one()
        fsession["username"] = fname
        name = fsession["username"]
        fsession["sessID"] = row.id
        sessionID = fsession["sessID"]
        # Valid credentials, perform login logic

        return f"Login successful<br><a href='/'>Welcome {name}, Go to the Home Page</a><br><a href='/logout'>Logout</a>"

    else:
        # Invalid credentials, show error message
        return "Invalid username or password"


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    # Render the dashboard template with the username
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    fsession.pop("sessID", 0)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_post():
    # checks for duplicate uuid
    new_uuid = uuid.uuid4()
    uuidCheck = "SELECT * FROM fyp.users WHERE id = %s ALLOW FILTERING"
    result = session.execute(uuidCheck, (new_uuid,))
    if result.one():
        new_uuid = uuid.uuid4()
    else:
        # initialization of details
        user_id = new_uuid
        username = request.form["username"]
        password = request.form["password"]

        yob = request.form["yob"]
        age = int(request.form["age"])
        gender = request.form['gender']

        password_hash = hashlib.sha1(password.encode()).hexdigest()
        # Perform Cassandra query to check if the username already exists
        query = "SELECT * FROM fyp.users WHERE name = %s ALLOW FILTERING"
        result = session.execute(query, (username,))

        if result.one():
            return "Username already exists<br><a href='/register'>Please Try Again</a>"
        else:
            # Perform Cassandra query to insert the new user into the users table
            query = "INSERT INTO fyp.users (id, age,gender, name, password, yob) VALUES (%s, %s, %s, %s, %s, %s)"
            session.execute(query, (user_id, age, gender, username, password_hash, yob))
            return "Registration successful<br><a href='/login'>Log In Now</a>"


@app.route("/record")
def record():
    sessionID = fsession["sessID"]
    return render_template("record.html")



@app.route("/insert", methods=["POST"])
def insert_record():
    sessionID = fsession["sessID"]
    new_rid = uuid.uuid4()
    ridCheck = "SELECT * FROM fyp.basicscores WHERE rid = %s ALLOW FILTERING"
    result = session.execute(ridCheck, (new_rid,))
    if result.one():
        new_rid = uuid.uuid4()
    else:
        exercise = request.form["exercise"]

        if exercise in ["Push Ups", "Sit Ups", "Squats with Ball"]:
            rid = new_rid
            badc = int(request.form["badcount"])
            totalc = int(request.form["excount"])
            goodc = int(request.form["goodcount"])
            poseresult = f"{badc} Bad,{goodc} Good"

            # Get the uploaded file
            image_file = request.files["file"]

            # Convert the file to a binary large object (BLOB)
            if image_file:
                image_data = BytesIO(image_file.read()).getvalue()
            else:
                image_data = None

            query = "INSERT INTO fyp.basicscores (rid, badcount, chart, date, excount, exercise, goodcount, poseresult, user_id, video) VALUES (%s, %s, %s, toTimestamp(now()), %s, %s, %s, %s, %s, NULL);"

            # Include the image_data (BLOB) in the session.execute call
            session.execute(
                query,
                (rid, badc, image_data, totalc, exercise, goodc, poseresult, sessionID),
            )
            return "Record uploaded successfully. <br><a href='/record'>Go Back</a>"

        elif exercise == "Standing Broad Jump":
            rid = new_rid
            tdist = int(request.form["totalDist"])
            query = "insert into fyp.jumpscore (rid, totaldist, exercise, user_id, date) VALUES (%s, %s, %s, %s, toTimestamp(now()));"
            session.execute(query, (rid, tdist, exercise, sessionID))
            return "Record uploaded successfully. <br><a href='/record'>Go Back</a>"
        elif exercise == "Grip Strength":
            rid = new_rid
            weight = int(request.form["weight"])
            query = "insert into fyp.gripscore (rid, weight, exercise, user_id, date) VALUES (%s, %s, %s, %s, toTimestamp(now()));"
            session.execute(query, (rid, weight, exercise, sessionID))
            return "Record uploaded successfully. <br><a href='/record'>Go Back</a>"
        elif exercise == "2.4km run":
            rid = new_rid
            dur = int(request.form["duration"])
            query = "insert into fyp.runscore (rid, seconds, exercise, user_id, date) VALUES (%s, %s, %s, %s, toTimestamp(now()));"
            session.execute(query, (rid, dur, exercise, sessionID))
            return "Record uploaded successfully. <br><a href='/record'>Go Back</a>"

@app.route("/export", methods=["POST"])
def insert_exercise_record():
    sessionID = fsession["sessID"]
    new_rid = uuid.uuid4()
    ridCheck = "SELECT * FROM fyp.basicscores WHERE rid = %s ALLOW FILTERING"
    result = session.execute(ridCheck, (new_rid,))
    if result.one():
        new_rid = uuid.uuid4()
    else:
        # Get the JSON data from the request
        json_data = request.json

        # Extract values from the JSON data
        totalc = json_data["Total"]
        goodc = json_data["Good"]
        badc = json_data["Bad"]
        exercise = json_data["Exercise"]
        chart_data = json_data["Chart"]
        poseresult = f"{badc} Bad,{goodc} Good"
        rid = new_rid

        query = "INSERT INTO fyp.basicscores (rid, badcount, chart, date, excount, exercise, goodcount, poseresult, user_id, video) VALUES (%s, %s, %s, toTimestamp(now()), %s, %s, %s, %s, %s, NULL);"

        # Include the chart_binary_data (BLOB) and other extracted values in the session.execute call
        session.execute(
            query,
            (rid, badc, chart_data, totalc, exercise, goodc, poseresult, sessionID),
        )
        return "Record uploaded successfully. <br><a href='/record'>Go Back</a>"


def display_record():
    image_path = "generated_image.png"
    return render_template("displayRecord.html", image_path=image_path)


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request.")
    return (
        """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(
            e
        ),
        500,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
