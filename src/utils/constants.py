"""Contains constants used throughout the program."""

NUM_EXPECTED_ARGS = 2 # Expected number of command line arguments
NUM_DAYS = 6 # Number of days in the meet
NUM_LINEUPS = 1 # Number of lineups to generate for the single day solver

CREDITS = 800
ADDITIONAL_CREDITS = 150
SWITCH_COST = 1
SWITCHES = (CREDITS + ADDITIONAL_CREDITS) // SWITCH_COST

SCHEDULE_URLS = {
    "2014 SCM Worlds": "https://www.worldaquatics.com/competitions/341/12th-fina-world-swimming-championships-25m-2014/schedule?phase=All",
    "2015 LCM Worlds": "https://www.worldaquatics.com/competitions/312/16th-fina-world-championships-2015/schedule?phase=All&disciplines=SW",
    "2016 SCM Worlds": "https://www.worldaquatics.com/competitions/239/13th-fina-world-swimming-championships-25m-2016/schedule?phase=All",
    "2017 LCM Worlds": "https://www.worldaquatics.com/competitions/213/17th-fina-world-championships-2017/schedule?phase=All&disciplines=SW",
    "2018 SCM Worlds": "https://www.worldaquatics.com/competitions/132/14th-fina-world-swimming-championships-25m-2018/schedule?phase=All",
    "2019 LCM Worlds": "https://www.worldaquatics.com/competitions/95/18th-fina-world-championships-2019/schedule?phase=All&disciplines=SW",
    "2021 SCM Worlds": "https://www.worldaquatics.com/competitions/2/15th-fina-world-swimming-championships-25m-2021/schedule?phase=All",
    "2022 SCM Worlds": "https://www.worldaquatics.com/competitions/2894/16th-fina-world-swimming-championships-25m-2022/schedule?phase=All",
    "2022 LCM Worlds": "https://www.worldaquatics.com/competitions/2902/19th-fina-world-championships-budapest-2022/schedule?phase=All&disciplines=SW",
    "2023 LCM Worlds": "https://www.worldaquatics.com/competitions/1/world-aquatics-championships-fukuoka-2023/schedule?phase=All&disciplines=SW",
    "2024 LCM Worlds": "https://www.worldaquatics.com/competitions/2969/world-aquatics-championships-doha-2024/schedule?phase=All&disciplines=SW",
    "2024 SCM Worlds": "https://www.worldaquatics.com/competitions/3433/world-aquatics-swimming-championships-25m-2024/schedule?phase=All",
}
